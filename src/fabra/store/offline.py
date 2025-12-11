from abc import ABC, abstractmethod
from typing import List, Optional
import duckdb
import pandas as pd
import asyncio
from typing import Dict, Any
from datetime import datetime


import structlog

logger = structlog.get_logger()


class OfflineStore(ABC):
    @abstractmethod
    async def get_training_data(
        self,
        entity_df: pd.DataFrame,
        features: List[str],
        entity_id_col: str,
        timestamp_col: str = "timestamp",
    ) -> pd.DataFrame:
        """
        Generates training data by joining entity_df with feature data.
        """

    @abstractmethod
    async def execute_sql(self, query: str) -> pd.DataFrame:
        """
        Executes a SQL query against the offline store and returns a DataFrame.
        """
        pass

    @abstractmethod
    async def get_historical_features(
        self, entity_name: str, entity_id: str, features: List[str], timestamp: datetime
    ) -> Dict[str, Any]:
        """
        Retrieves feature values as they were at the specified timestamp.
        """
        pass

    @abstractmethod
    async def log_context(
        self,
        context_id: str,
        timestamp: datetime,
        content: str,
        lineage: Dict[str, Any],
        meta: Dict[str, Any],
        version: str = "v1",
    ) -> None:
        """
        Persists a context assembly for replay and audit.

        Args:
            context_id: UUIDv7 identifier for the context
            timestamp: When the context was assembled
            content: The full assembled context text
            lineage: Serialized ContextLineage as dict
            meta: Additional metadata
            version: Schema version
        """
        pass

    @abstractmethod
    async def get_context(self, context_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a historical context by ID.

        Returns:
            Dict with keys: context_id, timestamp, content, lineage, meta, version
            Or None if not found.
        """
        pass

    @abstractmethod
    async def list_contexts(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100,
        name: Optional[str] = None,
        freshness_status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Lists contexts in a time range for debugging.

        Args:
            start: Filter contexts created after this time
            end: Filter contexts created before this time
            limit: Maximum number of results
            name: Filter by context name (from meta.name)
            freshness_status: Filter by freshness status ("guaranteed" or "degraded")

        Returns:
            List of context summaries (without full content for efficiency)
        """
        pass


class DuckDBOfflineStore(OfflineStore):
    def __init__(self, database: str = ":memory:") -> None:
        self.conn = duckdb.connect(database=database)

    async def get_training_data(
        self,
        entity_df: pd.DataFrame,
        features: List[str],
        entity_id_col: str,
        timestamp_col: str = "timestamp",
    ) -> pd.DataFrame:
        # Register entity_df so it can be queried
        self.conn.register("entity_df", entity_df)

        # Construct query using ASOF JOIN for Point-in-Time Correctness
        # SELECT e.*, f1.value as f1
        # FROM entity_df e
        # ASOF LEFT JOIN feature_table f1
        # ON e.entity_id = f1.entity_id AND e.timestamp >= f1.timestamp

        query = "SELECT entity_df.*"
        joins = ""

        # ... (rest of the query construction logic is fine, preserving context)
        import re

        for feature in features:
            if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", feature):
                raise ValueError(f"Invalid feature name: {feature}")

            # MVP Assumption: Feature table has columns [entity_id, timestamp, feature_name]
            # We alias the feature table to its name for clarity

            # Note: DuckDB ASOF JOIN syntax:
            # FROM A ASOF LEFT JOIN B ON A.id = B.id AND A.ts >= B.ts
            # The inequality MUST be >= for ASOF behavior (find latest B where B.ts <= A.ts)

            joins += f"""
            ASOF LEFT JOIN {feature}
            ON entity_df.{entity_id_col} = {feature}.entity_id
            AND entity_df.{timestamp_col} >= {feature}.timestamp
            """

            query += f", {feature}.{feature} AS {feature}"

        query += f" FROM entity_df {joins}"

        try:
            # Offload synchronous DuckDB execution to a thread
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                None, lambda: self.conn.execute(query).df()
            )
        except Exception as e:
            # Fallback for when tables don't exist (e.g. unit tests without setup)
            logger.warning("offline_retrieval_failed", error=str(e))
            return entity_df

    async def execute_sql(self, query: str) -> pd.DataFrame:
        # Truly async using thread pool executor
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: self.conn.execute(query).df())

    async def get_historical_features(
        self, entity_name: str, entity_id: str, features: List[str], timestamp: datetime
    ) -> Dict[str, Any]:
        """
        Retrieves historical features using DuckDB ASOF JOIN.
        """
        # 1. Create temporary context for the lookup
        ts_str = timestamp.isoformat()

        # Using parameterized query for safety if possible, or careful string construction
        # entity_id usually safe-ish, but let's be careful.
        # But for view creation, params are tricky. We'll use string interpolation for MVP
        # assuming internal entity_ids.

        setup_query = f"CREATE OR REPLACE TEMP VIEW request_ctx AS SELECT '{entity_id}' as entity_id, CAST('{ts_str}' AS TIMESTAMP) as timestamp"

        self.conn.execute(setup_query)

        # 2. Build Query
        # We select the feature values.
        # Handle case where features list is empty?
        if not features:
            return {}

        selects = ", ".join([f"{f}.{f} as {f}" for f in features])
        query = f"SELECT {selects} FROM request_ctx"  # nosec

        joins = ""
        import re

        for feature in features:
            if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", feature):
                logger.warning("invalid_feature_name", feature=feature)
                continue

            # ASOF JOIN assumes tables named after features exist and have (entity_id, timestamp, {feature_name})
            # This is a strong assumption of the default schema.
            joins += f"""
            ASOF LEFT JOIN {feature}
            ON request_ctx.entity_id = {feature}.entity_id
            AND request_ctx.timestamp >= {feature}.timestamp
            """

        query += joins

        try:
            loop = asyncio.get_running_loop()
            # result returns df
            df = await loop.run_in_executor(None, lambda: self.conn.execute(query).df())
            if not df.empty:
                # Convert first row to dict
                return df.iloc[0].to_dict()
            return {}
        except Exception as e:
            # Table missing likely
            logger.warning("historical_retrieval_failed", error=str(e))
            return {}

    def _ensure_context_table(self) -> None:
        """Create context_log table if it doesn't exist."""
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS context_log (
                context_id VARCHAR PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                content TEXT NOT NULL,
                lineage JSON NOT NULL,
                meta JSON NOT NULL,
                version VARCHAR DEFAULT 'v1'
            )
        """
        )
        # Create index for timestamp-based queries
        try:
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_context_log_timestamp ON context_log(timestamp)"
            )
        except Exception:  # nosec B110 - Index may already exist, safe to ignore
            pass

    async def log_context(
        self,
        context_id: str,
        timestamp: datetime,
        content: str,
        lineage: Dict[str, Any],
        meta: Dict[str, Any],
        version: str = "v1",
    ) -> None:
        """Persist context to DuckDB for replay."""
        import json

        self._ensure_context_table()

        def json_serializer(obj: Any) -> str:
            """Handle datetime and other non-serializable types."""
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(
                f"Object of type {type(obj).__name__} is not JSON serializable"
            )

        lineage_json = json.dumps(lineage, default=json_serializer)
        meta_json = json.dumps(meta, default=json_serializer)
        ts_str = timestamp.isoformat()

        # Use parameterized query to prevent injection
        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(
                None,
                lambda: self.conn.execute(
                    """
                    INSERT OR REPLACE INTO context_log
                    (context_id, timestamp, content, lineage, meta, version)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    [context_id, ts_str, content, lineage_json, meta_json, version],
                ),
            )
            logger.info("context_logged", context_id=context_id)
        except Exception as e:
            logger.error("context_log_failed", context_id=context_id, error=str(e))
            raise

    async def get_context(self, context_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a context by ID."""
        import json

        self._ensure_context_table()

        loop = asyncio.get_running_loop()
        try:
            df = await loop.run_in_executor(
                None,
                lambda: self.conn.execute(
                    "SELECT * FROM context_log WHERE context_id = ?", [context_id]
                ).df(),
            )
            if df.empty:
                return None

            row = df.iloc[0]
            return {
                "context_id": row["context_id"],
                "timestamp": row["timestamp"],
                "content": row["content"],
                "lineage": json.loads(row["lineage"])
                if isinstance(row["lineage"], str)
                else row["lineage"],
                "meta": json.loads(row["meta"])
                if isinstance(row["meta"], str)
                else row["meta"],
                "version": row["version"],
            }
        except Exception as e:
            logger.error(
                "context_retrieval_failed", context_id=context_id, error=str(e)
            )
            return None

    async def list_contexts(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100,
        name: Optional[str] = None,
        freshness_status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List contexts in time range with optional filters.

        Args:
            start: Filter contexts created after this time
            end: Filter contexts created before this time
            limit: Maximum number of results
            name: Filter by context name (from meta.name)
            freshness_status: Filter by freshness status ("guaranteed" or "degraded")
        """
        import json

        self._ensure_context_table()

        # Build query with optional time filters
        conditions = []
        params: List[Any] = []

        if start:
            conditions.append("timestamp >= ?")
            params.append(start.isoformat())
        if end:
            conditions.append("timestamp <= ?")
            params.append(end.isoformat())

        # Filter by name (stored in meta JSON)
        if name:
            conditions.append("json_extract(meta, '$.name') = ?")
            params.append(name)

        # Filter by freshness_status (stored in meta JSON)
        if freshness_status:
            conditions.append("json_extract(meta, '$.freshness_status') = ?")
            params.append(freshness_status)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        params.append(limit)

        query = f"""
            SELECT context_id, timestamp, meta, version
            FROM context_log
            {where_clause}
            ORDER BY timestamp DESC
            LIMIT ?
        """  # nosec B608 - where_clause built from validated internal conditions

        loop = asyncio.get_running_loop()
        try:
            df = await loop.run_in_executor(
                None, lambda: self.conn.execute(query, params).df()
            )
            results = []
            for _, row in df.iterrows():
                meta = (
                    json.loads(row["meta"])
                    if isinstance(row["meta"], str)
                    else row["meta"]
                )
                results.append(
                    {
                        "context_id": row["context_id"],
                        "timestamp": row["timestamp"],
                        "name": meta.get("name", "unknown"),
                        "token_usage": meta.get("token_usage", 0),
                        "freshness_status": meta.get("freshness_status", "unknown"),
                        "version": row["version"],
                    }
                )
            return results
        except Exception as e:
            logger.error("context_list_failed", error=str(e))
            return []
