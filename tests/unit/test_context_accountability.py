"""Tests for v1.4 Context Accountability features."""

from __future__ import annotations
import pytest
from datetime import datetime, timezone, timedelta

from fabra.models import FeatureLineage, RetrieverLineage, ContextLineage
from fabra.context import (
    context,
    Context,
    AssemblyTracker,
    record_feature_usage,
    record_retriever_usage,
    _assembly_tracker,
)


class TestLineageModels:
    """Test lineage data models."""

    def test_feature_lineage_creation(self) -> None:
        """Test creating a FeatureLineage record."""
        lineage = FeatureLineage(
            feature_name="user_score",
            entity_id="user123",
            value=85.5,
            timestamp=datetime.now(timezone.utc),
            freshness_ms=150,
            source="cache",
        )
        assert lineage.feature_name == "user_score"
        assert lineage.entity_id == "user123"
        assert lineage.value == 85.5
        assert lineage.freshness_ms == 150
        assert lineage.source == "cache"

    def test_retriever_lineage_creation(self) -> None:
        """Test creating a RetrieverLineage record."""
        lineage = RetrieverLineage(
            retriever_name="semantic_search",
            query="What is the product?",
            results_count=5,
            latency_ms=120.5,
            index_name="knowledge_base",
        )
        assert lineage.retriever_name == "semantic_search"
        assert lineage.query == "What is the product?"
        assert lineage.results_count == 5
        assert lineage.latency_ms == 120.5
        assert lineage.index_name == "knowledge_base"

    def test_context_lineage_creation(self) -> None:
        """Test creating a full ContextLineage record."""
        feature = FeatureLineage(
            feature_name="test_feature",
            entity_id="e1",
            value=10,
            timestamp=datetime.now(timezone.utc),
            freshness_ms=50,
            source="compute",
        )
        retriever = RetrieverLineage(
            retriever_name="test_retriever",
            query="test query",
            results_count=3,
            latency_ms=100.0,
        )
        lineage = ContextLineage(
            context_id="ctx-123",
            timestamp=datetime.now(timezone.utc),
            features_used=[feature],
            retrievers_used=[retriever],
            items_provided=5,
            items_included=4,
            items_dropped=1,
            freshness_status="guaranteed",
            stalest_feature_ms=50,
            token_usage=500,
            max_tokens=1000,
        )
        assert lineage.context_id == "ctx-123"
        assert len(lineage.features_used) == 1
        assert len(lineage.retrievers_used) == 1
        assert lineage.items_dropped == 1
        assert lineage.freshness_status == "guaranteed"


class TestAssemblyTracker:
    """Test the AssemblyTracker for lineage collection."""

    def test_tracker_creation(self) -> None:
        """Test creating an AssemblyTracker."""
        tracker = AssemblyTracker(context_id="ctx-abc")
        assert tracker.context_id == "ctx-abc"
        assert len(tracker.features) == 0
        assert len(tracker.retrievers) == 0

    def test_record_feature(self) -> None:
        """Test recording a feature usage."""
        tracker = AssemblyTracker(context_id="ctx-def")
        tracker.record_feature(
            feature_name="engagement_score",
            entity_id="user456",
            value=92.0,
            timestamp=datetime.now(timezone.utc),
            source="cache",
        )
        assert len(tracker.features) == 1
        assert tracker.features[0].feature_name == "engagement_score"
        assert tracker.features[0].entity_id == "user456"
        assert tracker.features[0].value == 92.0
        assert tracker.features[0].source == "cache"
        assert tracker.features[0].freshness_ms >= 0

    def test_record_retriever(self) -> None:
        """Test recording a retriever usage."""
        tracker = AssemblyTracker(context_id="ctx-ghi")
        tracker.record_retriever(
            retriever_name="product_search",
            query="laptop",
            results_count=10,
            latency_ms=45.2,
            index_name="products",
        )
        assert len(tracker.retrievers) == 1
        assert tracker.retrievers[0].retriever_name == "product_search"
        assert tracker.retrievers[0].query == "laptop"
        assert tracker.retrievers[0].results_count == 10
        assert tracker.retrievers[0].latency_ms == 45.2
        assert tracker.retrievers[0].index_name == "products"


class TestRecordFunctions:
    """Test the record_feature_usage and record_retriever_usage helpers."""

    def test_record_feature_usage_with_tracker(self) -> None:
        """Test recording feature usage when tracker is active."""
        tracker = AssemblyTracker(context_id="ctx-jkl")
        token = _assembly_tracker.set(tracker)
        try:
            record_feature_usage(
                feature_name="test_feat",
                entity_id="e1",
                value=100,
                timestamp=datetime.now(timezone.utc),
                source="compute",
            )
            assert len(tracker.features) == 1
            assert tracker.features[0].feature_name == "test_feat"
        finally:
            _assembly_tracker.reset(token)

    def test_record_feature_usage_without_tracker(self) -> None:
        """Test recording feature usage when no tracker is active (no-op)."""
        # Should not raise
        record_feature_usage(
            feature_name="test_feat",
            entity_id="e1",
            value=100,
            timestamp=datetime.now(timezone.utc),
            source="compute",
        )
        # No exception = success

    def test_record_retriever_usage_with_tracker(self) -> None:
        """Test recording retriever usage when tracker is active."""
        tracker = AssemblyTracker(context_id="ctx-mno")
        token = _assembly_tracker.set(tracker)
        try:
            record_retriever_usage(
                retriever_name="doc_search",
                query="help docs",
                results_count=5,
                latency_ms=30.0,
                index_name="docs",
            )
            assert len(tracker.retrievers) == 1
            assert tracker.retrievers[0].retriever_name == "doc_search"
        finally:
            _assembly_tracker.reset(token)

    def test_record_retriever_usage_without_tracker(self) -> None:
        """Test recording retriever usage when no tracker is active (no-op)."""
        # Should not raise
        record_retriever_usage(
            retriever_name="doc_search",
            query="help docs",
            results_count=5,
            latency_ms=30.0,
        )
        # No exception = success


class TestContextWithLineage:
    """Test context assembly with lineage tracking."""

    @pytest.mark.asyncio
    async def test_context_has_lineage_field(self) -> None:
        """Test that Context model has lineage field."""
        ctx = Context(
            id="test-id",
            content="test content",
            meta={"name": "test"},
            version="v1",
        )
        assert ctx.lineage is None  # Default is None

        # With lineage
        lineage = ContextLineage(
            context_id="test-id",
            timestamp=datetime.now(timezone.utc),
        )
        ctx_with_lineage = Context(
            id="test-id",
            content="test content",
            meta={"name": "test"},
            lineage=lineage,
            version="v1",
        )
        assert ctx_with_lineage.lineage is not None
        assert ctx_with_lineage.lineage.context_id == "test-id"

    @pytest.mark.asyncio
    async def test_context_decorator_creates_lineage_with_store(self) -> None:
        """Test that context decorator creates lineage when store with offline_store is provided."""
        from fabra.core import FeatureStore
        from fabra.store.offline import DuckDBOfflineStore

        store = FeatureStore()
        offline = DuckDBOfflineStore(":memory:")
        store.offline_store = offline

        @context(store=store, name="lineage_test")
        async def assemble_with_lineage() -> str:
            return "Test content"

        result = await assemble_with_lineage()
        assert isinstance(result, Context)
        # Lineage should be created by the decorator when store has offline_store
        assert result.lineage is not None
        assert result.lineage.context_id == result.id


class TestContextLogging:
    """Test context logging to offline store."""

    @pytest.mark.asyncio
    async def test_duckdb_log_context(self) -> None:
        """Test logging context to DuckDB offline store."""
        from fabra.store.offline import DuckDBOfflineStore

        store = DuckDBOfflineStore(":memory:")

        context_id = "test-ctx-001"
        timestamp = datetime.now(timezone.utc)
        content = "Test context content"
        lineage = {
            "context_id": context_id,
            "timestamp": timestamp.isoformat(),
            "features_used": [],
            "retrievers_used": [],
        }
        meta = {"name": "test", "key": "value"}

        await store.log_context(
            context_id=context_id,
            timestamp=timestamp,
            content=content,
            lineage=lineage,
            meta=meta,
            version="v1",
        )

        # Retrieve and verify
        result = await store.get_context(context_id)
        assert result is not None
        assert result["context_id"] == context_id
        assert result["content"] == content
        assert result["version"] == "v1"
        assert result["lineage"]["context_id"] == context_id

    @pytest.mark.asyncio
    async def test_duckdb_list_contexts(self) -> None:
        """Test listing contexts from DuckDB with time filtering."""
        from fabra.store.offline import DuckDBOfflineStore

        store = DuckDBOfflineStore(":memory:")

        now = datetime.now(timezone.utc)

        # Log multiple contexts
        for i in range(5):
            await store.log_context(
                context_id=f"ctx-{i:03d}",
                timestamp=now - timedelta(hours=i),
                content=f"Content {i}",
                lineage={"context_id": f"ctx-{i:03d}"},
                meta={"index": i},
                version="v1",
            )

        # List all (limit 10)
        results = await store.list_contexts(limit=10)
        assert len(results) == 5

        # List with time filter (last 2 hours)
        start = now - timedelta(hours=2)
        results = await store.list_contexts(start=start, limit=10)
        assert len(results) >= 2  # Should include ctx-000, ctx-001, ctx-002

        # List with limit
        results = await store.list_contexts(limit=2)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_duckdb_get_nonexistent_context(self) -> None:
        """Test getting a context that doesn't exist."""
        from fabra.store.offline import DuckDBOfflineStore

        store = DuckDBOfflineStore(":memory:")

        result = await store.get_context("nonexistent-id")
        assert result is None


class TestFeatureStoreReplayAPI:
    """Test FeatureStore context replay methods."""

    @pytest.mark.asyncio
    async def test_get_context_at(self) -> None:
        """Test retrieving a historical context by ID."""
        from fabra.core import FeatureStore
        from fabra.store.offline import DuckDBOfflineStore

        store = FeatureStore()
        offline = DuckDBOfflineStore(":memory:")
        store.offline_store = offline

        # Log a context
        context_id = "replay-test-001"
        timestamp = datetime.now(timezone.utc)
        await offline.log_context(
            context_id=context_id,
            timestamp=timestamp,
            content="Historical content",
            lineage={"context_id": context_id, "timestamp": timestamp.isoformat()},
            meta={"name": "replay_test"},
            version="v1",
        )

        # Retrieve via FeatureStore
        result = await store.get_context_at(context_id)
        assert result is not None
        assert result.id == context_id
        assert result.content == "Historical content"

    @pytest.mark.asyncio
    async def test_get_context_at_not_found(self) -> None:
        """Test retrieving a non-existent context returns None."""
        from fabra.core import FeatureStore
        from fabra.store.offline import DuckDBOfflineStore

        store = FeatureStore()
        offline = DuckDBOfflineStore(":memory:")
        store.offline_store = offline

        result = await store.get_context_at("does-not-exist")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_contexts(self) -> None:
        """Test listing contexts via FeatureStore."""
        from fabra.core import FeatureStore
        from fabra.store.offline import DuckDBOfflineStore

        store = FeatureStore()
        offline = DuckDBOfflineStore(":memory:")
        store.offline_store = offline

        now = datetime.now(timezone.utc)

        # Log contexts
        for i in range(3):
            await offline.log_context(
                context_id=f"list-ctx-{i}",
                timestamp=now - timedelta(minutes=i),
                content=f"List content {i}",
                lineage={"context_id": f"list-ctx-{i}"},
                meta={},
                version="v1",
            )

        results = await store.list_contexts(limit=10)
        assert len(results) == 3


class TestServerEndpoints:
    """Test REST API endpoints for context accountability."""

    @pytest.mark.asyncio
    async def test_list_contexts_endpoint(self) -> None:
        """Test GET /v1/contexts endpoint."""
        from httpx import AsyncClient, ASGITransport
        from fabra.server import create_app
        from fabra.core import FeatureStore
        from fabra.store.offline import DuckDBOfflineStore

        store = FeatureStore()
        offline = DuckDBOfflineStore(":memory:")
        store.offline_store = offline

        now = datetime.now(timezone.utc)
        await offline.log_context(
            context_id="api-ctx-001",
            timestamp=now,
            content="API test content",
            lineage={"context_id": "api-ctx-001"},
            meta={},
            version="v1",
        )

        app = create_app(store)
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/v1/contexts", params={"limit": 10})
            assert resp.status_code == 200
            data = resp.json()
            # Endpoint returns a list directly
            assert isinstance(data, list)
            assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_get_context_by_id_endpoint(self) -> None:
        """Test GET /v1/context/{context_id} endpoint."""
        from httpx import AsyncClient, ASGITransport
        from fabra.server import create_app
        from fabra.core import FeatureStore
        from fabra.store.offline import DuckDBOfflineStore

        store = FeatureStore()
        offline = DuckDBOfflineStore(":memory:")
        store.offline_store = offline

        now = datetime.now(timezone.utc)
        await offline.log_context(
            context_id="api-ctx-002",
            timestamp=now,
            content="Get by ID content",
            lineage={"context_id": "api-ctx-002", "timestamp": now.isoformat()},
            meta={"name": "test"},
            version="v1",
        )

        app = create_app(store)
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/v1/context/api-ctx-002")
            assert resp.status_code == 200
            data = resp.json()
            assert data["context_id"] == "api-ctx-002"
            assert data["content"] == "Get by ID content"

    @pytest.mark.asyncio
    async def test_get_context_not_found_endpoint(self) -> None:
        """Test GET /v1/context/{context_id} returns 404 for missing context."""
        from httpx import AsyncClient, ASGITransport
        from fabra.server import create_app
        from fabra.core import FeatureStore
        from fabra.store.offline import DuckDBOfflineStore

        store = FeatureStore()
        offline = DuckDBOfflineStore(":memory:")
        store.offline_store = offline

        app = create_app(store)
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/v1/context/nonexistent-ctx")
            assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_context_lineage_endpoint(self) -> None:
        """Test GET /v1/context/{context_id}/lineage endpoint."""
        from httpx import AsyncClient, ASGITransport
        from fabra.server import create_app
        from fabra.core import FeatureStore
        from fabra.store.offline import DuckDBOfflineStore

        store = FeatureStore()
        offline = DuckDBOfflineStore(":memory:")
        store.offline_store = offline

        now = datetime.now(timezone.utc)
        lineage_data = {
            "context_id": "api-ctx-003",
            "timestamp": now.isoformat(),
            "features_used": [
                {
                    "feature_name": "test_feature",
                    "entity_id": "e1",
                    "value": 100,
                    "timestamp": now.isoformat(),
                    "freshness_ms": 50,
                    "source": "cache",
                }
            ],
            "retrievers_used": [],
        }
        await offline.log_context(
            context_id="api-ctx-003",
            timestamp=now,
            content="Lineage test content",
            lineage=lineage_data,
            meta={},
            version="v1",
        )

        app = create_app(store)
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/v1/context/api-ctx-003/lineage")
            assert resp.status_code == 200
            data = resp.json()
            assert data["context_id"] == "api-ctx-003"
            # Lineage is wrapped in a "lineage" key
            assert "lineage" in data
            lineage = data["lineage"]
            assert "features_used" in lineage
            assert len(lineage["features_used"]) == 1
            assert lineage["features_used"][0]["feature_name"] == "test_feature"
