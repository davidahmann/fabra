from fastapi.testclient import TestClient
from meridian.server import create_app
from meridian.core import FeatureStore


def test_api_metrics() -> None:
    store = FeatureStore()
    app = create_app(store)
    client = TestClient(app)

    # Make a request to trigger metrics
    client.get("/health")

    # Fetch metrics
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "meridian_request_count" in response.text
    assert "meridian_request_latency_seconds" in response.text
