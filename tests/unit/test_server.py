from fastapi.testclient import TestClient
from meridian.server import create_app
from meridian.core import FeatureStore, entity, feature
from meridian.store.online import InMemoryOnlineStore


def test_api_get_features() -> None:
    # 1. Setup Store
    store = FeatureStore(online_store=InMemoryOnlineStore())

    @entity(store)
    class User:
        user_id: str

    @feature(entity=User)
    def user_clicks(user_id: str) -> int:
        return 10

    # Pre-populate online store
    store.online_store.set_online_features(
        entity_name="User", entity_id="u1", features={"user_clicks": 42}
    )

    # 2. Create App & Client
    app = create_app(store)
    client = TestClient(app)

    # 3. Request Features
    response = client.post(
        "/features",
        json={"entity_name": "User", "entity_id": "u1", "features": ["user_clicks"]},
    )

    # 4. Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["user_clicks"] == 42


def test_api_health() -> None:
    store = FeatureStore()
    app = create_app(store)
    client = TestClient(app)

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
