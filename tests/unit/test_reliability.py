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


@pytest.mark.asyncio
async def test_feature_not_found_suggestion() -> None:
    store = FeatureStore(online_store=InMemoryOnlineStore())

    @entity(store)
    class User:
        user_id: str

    @feature(entity=User)
    def user_score(user_id: str) -> int:
        return 100

    # Test "Did you mean?"
    with pytest.raises(ValueError) as exc:
        await store.get_feature("user_scre", "u1")  # Typo

    assert "Did you mean: user_score?" in str(exc.value)

    # Test get_training_data suggestions
    # Mock dataframe
    import pandas as pd

    df = pd.DataFrame({"user_id": ["u1"]})

    with pytest.raises(ValueError) as exc:
        await store.get_training_data(df, ["user_scre"])

    assert "Did you mean: user_score?" in str(exc.value)
