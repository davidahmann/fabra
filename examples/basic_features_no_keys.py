"""
No-keys, no-setup variant of `basic_features.py`.

Run:
  fabra serve examples/basic_features_no_keys.py

Test:
  curl 'http://127.0.0.1:8000/features/user_click_count?entity_id=u1'
"""

from datetime import timedelta

from fabra.core import FeatureStore, entity, feature
from fabra.store import DuckDBOfflineStore, InMemoryOnlineStore

store = FeatureStore(
    offline_store=DuckDBOfflineStore(),
    online_store=InMemoryOnlineStore(),
)


@entity(store)
class User:
    user_id: str


@feature(entity=User, refresh=timedelta(minutes=5), materialize=True)
def user_click_count(user_id: str) -> int:
    return abs(hash(user_id + "clicks")) % 101


@feature(entity=User)
def user_is_active(user_id: str) -> bool:
    return hash(user_id) % 3 != 0


async def _seed_demo_data() -> None:
    await store.online_store.set_online_features(
        "User",
        "u1",
        {
            "user_click_count": user_click_count("u1"),
            "user_is_active": user_is_active("u1"),
        },
    )


def _run_seed() -> None:
    import asyncio

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_seed_demo_data())
    except RuntimeError:
        asyncio.run(_seed_demo_data())


_run_seed()
