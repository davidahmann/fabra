import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from typer.testing import CliRunner
import sys
import os
from fabra.cli import app

runner = CliRunner()


@pytest.fixture
def mock_redis():
    with patch("redis.asyncio.Redis.from_url") as mock:
        # Create an async mock instance
        redis_instance = MagicMock()
        redis_instance.xread = AsyncMock()
        redis_instance.xadd = AsyncMock()
        redis_instance.aclose = AsyncMock()

        mock.return_value = redis_instance
        yield redis_instance


@pytest.fixture
def mock_worker_class():
    # AxiomWorker is imported INSIDE the function: "from .worker import AxiomWorker"
    # standard patch("fabra.cli.AxiomWorker") won't work because fabra.cli doesn't have it at module level.
    # We need to patch "fabra.worker.AxiomWorker" so when cli imports it, it gets the mock.
    # BUT, we must ensure fabra.worker is imported first or mocked in sys.modules

    with patch("fabra.worker.AxiomWorker") as mock_cls:
        worker_inst = MagicMock()
        worker_inst.run = AsyncMock()
        mock_cls.return_value = worker_inst
        yield mock_cls


def test_events_listen_success(mock_redis):
    # Simulate one batch of messages then indefinite block or just one loop iteration
    # The command loop is "while True". To break it, we can raise CancelledError
    # or make xread raise exception after first call.

    mock_redis.xread.side_effect = [
        # First call returns data
        [("stream", [("id1", {"key": "val"})])],
        # Second call raises exception to break loop
        Exception("Stop Loop"),
    ]

    result = runner.invoke(
        app, ["events", "listen", "--stream", "test", "--count", "1"]
    )
    assert "Listening to stream" in result.stdout
    assert "id1" in result.stdout
    assert "Stop Loop" in result.stdout  # It catches generic exception


def test_worker_file_not_found():
    result = runner.invoke(app, ["worker", "non_existent.py"])
    assert result.exit_code == 1
    assert "Error" in result.stdout


def test_worker_success(mock_worker_class):
    # We need a valid python file that defines a FeatureStore
    # We can write a temp file

    content = """
from fabra.core import FeatureStore
store = FeatureStore()
"""
    with open("temp_features.py", "w") as f:
        f.write(content)

    try:
        # We need to ensure fabra.core is importable. It should be in test env.
        # But importlib needs CWD in path
        sys.path.append(os.getcwd())

        result = runner.invoke(app, ["worker", "temp_features.py"])

        assert result.exit_code == 0
        assert "Starting Axiom Worker" in result.stdout
        mock_worker_class.assert_called_once()
        mock_worker_class.return_value.run.assert_called_once()

    finally:
        os.remove("temp_features.py")


def test_worker_with_streams(mock_worker_class):
    content = "from fabra.core import FeatureStore; store=FeatureStore()"
    with open("temp_features_2.py", "w") as f:
        f.write(content)

    try:
        result = runner.invoke(
            app, ["worker", "temp_features_2.py", "--streams", "s1,s2"]
        )
        assert result.exit_code == 0
        # Check args passed to constructor
        _, kwargs = mock_worker_class.call_args
        assert kwargs["streams"] == ["s1", "s2"]

    finally:
        os.remove("temp_features_2.py")


def test_worker_with_event_type(mock_worker_class):
    content = "from fabra.core import FeatureStore; store=FeatureStore()"
    with open("temp_features_3.py", "w") as f:
        f.write(content)

    try:
        result = runner.invoke(
            app, ["worker", "temp_features_3.py", "--event-type", "click"]
        )
        assert result.exit_code == 0
        _, kwargs = mock_worker_class.call_args
        assert kwargs["streams"] == ["fabra:events:click"]

    finally:
        os.remove("temp_features_3.py")
