from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone


def _wrap_feature_value(value: Any, as_of: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Wrap a feature value with metadata so we can compute freshness and replay.

    This wrapper is internal to online stores; callers should unwrap before returning
    values to application code.
    """
    if isinstance(value, dict) and value.get("__fabra_feature_value__") is True:
        return value

    ts = (as_of or datetime.now(timezone.utc)).isoformat()
    return {"__fabra_feature_value__": True, "value": value, "as_of": ts}


class OnlineStore(ABC):
    @abstractmethod
    async def get_online_features(
        self, entity_name: str, entity_id: str, feature_names: List[str]
    ) -> Dict[str, Any]:
        """
        Retrieves feature values for a single entity from the online store.
        """
        pass

    @abstractmethod
    async def set_online_features(
        self,
        entity_name: str,
        entity_id: str,
        features: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> None:
        """
        Writes feature values for a single entity to the online store.

        Args:
            entity_name: The name of the entity.
            entity_id: The unique identifier for the entity.
            features: A dictionary of feature names to values.
            ttl: Optional time-to-live in seconds.
        """
        pass

    @abstractmethod
    async def set_online_features_bulk(
        self,
        entity_name: str,
        features_df: Any,  # pd.DataFrame
        feature_name: str,
        entity_id_col: str,
        ttl: Optional[int] = None,
    ) -> None:
        """
        Writes feature values for multiple entities to the online store.

        Args:
            entity_name: The name of the entity.
            features_df: DataFrame containing the feature values.
            feature_name: The name of the feature to write.
            entity_id_col: The column name in the DataFrame containing entity IDs.
            ttl: Optional time-to-live in seconds.
        """
        pass

    # --- Cache Primitives ---
    # Optional implementations, but widely used by Context API
    async def get(self, key: str) -> Any:
        pass

    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> Any:
        pass

    async def delete(self, *keys: str) -> Any:
        pass

    async def smembers(self, key: str) -> Any:
        pass

    def pipeline(self) -> Any:
        pass

    # --- Optional Metadata Path ---
    # Used to compute freshness and build lineage without changing the public return values.
    async def get_online_features_with_meta(
        self, entity_name: str, entity_id: str, feature_names: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        raise NotImplementedError


class InMemoryOnlineStore(OnlineStore):
    def __init__(self) -> None:
        # Structure: {entity_name: {entity_id: {feature_name: value}}}
        self._storage: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self._cache_storage: Dict[str, bytes] = {}
        self._set_storage: Dict[str, Any] = {}

    async def get_online_features(
        self, entity_name: str, entity_id: str, feature_names: List[str]
    ) -> Dict[str, Any]:
        entity_storage = self._storage.get(entity_name, {})
        features = entity_storage.get(entity_id, {})
        result: Dict[str, Any] = {}
        for name in feature_names:
            if name not in features:
                continue
            raw = features.get(name)
            if isinstance(raw, dict) and raw.get("__fabra_feature_value__") is True:
                result[name] = raw.get("value")
            else:
                result[name] = raw
        return result

    async def get_online_features_with_meta(
        self, entity_name: str, entity_id: str, feature_names: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        entity_storage = self._storage.get(entity_name, {})
        features = entity_storage.get(entity_id, {})
        result: Dict[str, Dict[str, Any]] = {}
        for name in feature_names:
            if name not in features:
                continue
            raw = features.get(name)
            if isinstance(raw, dict) and raw.get("__fabra_feature_value__") is True:
                result[name] = raw
            else:
                result[name] = _wrap_feature_value(raw)
        return result

    async def set_online_features(
        self,
        entity_name: str,
        entity_id: str,
        features: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> None:
        """Writes features to memory. TTL is currently ignored in-memory."""
        if entity_name not in self._storage:
            self._storage[entity_name] = {}
        if entity_id not in self._storage[entity_name]:
            self._storage[entity_name][entity_id] = {}

        wrapped = {k: _wrap_feature_value(v) for k, v in features.items()}
        self._storage[entity_name][entity_id].update(wrapped)

    async def set_online_features_bulk(
        self,
        entity_name: str,
        features_df: Any,
        feature_name: str,
        entity_id_col: str,
        ttl: Optional[int] = None,
    ) -> None:
        # Iterate over dataframe and set features
        for _, row in features_df.iterrows():
            entity_id = str(row[entity_id_col])
            value = row[feature_name]
            await self.set_online_features(
                entity_name, entity_id, {feature_name: value}
            )

    # --- Cache Primitives for Context API ---
    async def get(self, key: str) -> Optional[bytes]:
        return self._cache_storage.get(key)

    async def set(self, key: str, value: bytes, ex: Optional[int] = None) -> None:
        self._cache_storage[key] = value

    async def delete(self, *keys: str) -> int:
        count = 0
        for k in keys:
            if k in self._cache_storage:
                del self._cache_storage[k]
                count += 1
            if k in self._set_storage:
                del self._set_storage[k]
        return count

    async def smembers(self, key: str) -> Any:
        return self._set_storage.get(key, set())

    def pipeline(self) -> Any:
        # Mock pipeline context manager for in-memory
        class MockPipeline:
            def __init__(self, store: InMemoryOnlineStore):
                self.store = store

            def set(self, k: str, v: bytes, ex: Optional[int] = None) -> None:
                self.store._cache_storage[k] = v

            def sadd(self, k: str, v: Any) -> None:
                if k not in self.store._set_storage:
                    self.store._set_storage[k] = set()
                self.store._set_storage[k].add(v)

            def expire(self, k: str, s: int) -> None:
                pass

            async def execute(self) -> None:
                pass

        return MockPipeline(self)
