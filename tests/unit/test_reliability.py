import pytest
from meridian.core import FeatureStore, entity, feature
from meridian.store.online import InMemoryOnlineStore


@pytest.mark.asyncio
async def test_fallback_to_compute() -> None:
    store = FeatureStore(online_store=InMemoryOnlineStore())

    @entity(store)
    class User:
        user_id: str

    @feature(entity=User)
    def computed_feature(user_id: str) -> int:
        return 100

    # Don't set online features, so it should miss cache and hit compute
    result = await store.get_online_features("User", "u1", ["computed_feature"])
    assert result["computed_feature"] == 100


@pytest.mark.asyncio
async def test_fallback_to_default() -> None:
    store = FeatureStore(online_store=InMemoryOnlineStore())

    @entity(store)
    class User:
        user_id: str

    @feature(entity=User, default_value=999)
    def failing_feature(user_id: str) -> int:
        raise ValueError("Compute failed")

    # Cache miss + Compute fail -> Default
    result = await store.get_online_features("User", "u1", ["failing_feature"])
    assert result["failing_feature"] == 999
