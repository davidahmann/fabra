"""Tests for time travel context replay functionality."""

from __future__ import annotations
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from fabra.context import (
    context,
    Context,
    set_time_travel_context,
    clear_time_travel_context,
    get_time_travel_timestamp,
)
from fabra.core import FeatureRegistry, FeatureStore
from fabra.models import ContextLineage


class TestTimeTravelContextFunctions:
    """Tests for time travel context variable functions."""

    def test_get_time_travel_timestamp_default_none(self) -> None:
        """Time travel timestamp should be None by default."""
        # Ensure clean state
        clear_time_travel_context()
        assert get_time_travel_timestamp() is None

    def test_set_and_get_time_travel_timestamp(self) -> None:
        """Setting timestamp should be retrievable."""
        test_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        try:
            set_time_travel_context(test_time)
            assert get_time_travel_timestamp() == test_time
        finally:
            clear_time_travel_context()

    def test_clear_time_travel_context(self) -> None:
        """Clearing should reset timestamp to None."""
        test_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        set_time_travel_context(test_time)
        clear_time_travel_context()
        assert get_time_travel_timestamp() is None

    def test_multiple_set_calls_override(self) -> None:
        """Multiple set calls should override previous value."""
        time1 = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        time2 = datetime(2024, 6, 20, 18, 30, 0, tzinfo=timezone.utc)
        try:
            set_time_travel_context(time1)
            assert get_time_travel_timestamp() == time1
            set_time_travel_context(time2)
            assert get_time_travel_timestamp() == time2
        finally:
            clear_time_travel_context()


class TestFeatureRegistryContextRegistration:
    """Tests for FeatureRegistry context function registration."""

    def test_registry_has_contexts_dict(self) -> None:
        """Registry should have a contexts dict."""
        registry = FeatureRegistry()
        assert hasattr(registry, "contexts")
        assert isinstance(registry.contexts, dict)
        assert len(registry.contexts) == 0

    def test_register_context(self) -> None:
        """Should be able to register a context function."""
        registry = FeatureRegistry()

        async def my_context_func(user_id: str) -> str:
            return f"Context for {user_id}"

        registry.register_context("my_context", my_context_func)
        assert "my_context" in registry.contexts
        assert registry.contexts["my_context"] is my_context_func

    def test_register_multiple_contexts(self) -> None:
        """Should be able to register multiple context functions."""
        registry = FeatureRegistry()

        async def context_a() -> str:
            return "A"

        async def context_b() -> str:
            return "B"

        registry.register_context("a", context_a)
        registry.register_context("b", context_b)
        assert len(registry.contexts) == 2
        assert registry.contexts["a"] is context_a
        assert registry.contexts["b"] is context_b

    def test_register_context_overwrites(self) -> None:
        """Registering same name should overwrite."""
        registry = FeatureRegistry()

        async def old_func() -> str:
            return "old"

        async def new_func() -> str:
            return "new"

        registry.register_context("test", old_func)
        registry.register_context("test", new_func)
        assert registry.contexts["test"] is new_func


class TestContextDecoratorRegistration:
    """Tests for @context decorator auto-registration."""

    @pytest.mark.asyncio
    async def test_context_decorator_registers_with_store(self) -> None:
        """@context decorator should register with store's registry."""
        # Create mock store with registry
        mock_store = MagicMock()
        mock_store.registry = FeatureRegistry()
        mock_store.online_store = None

        @context(store=mock_store, name="test_registered_context")
        async def my_context(user_id: str) -> str:
            return f"Hello {user_id}"

        # Check registration
        assert "test_registered_context" in mock_store.registry.contexts
        # The registered function is the wrapper
        assert (
            mock_store.registry.contexts["test_registered_context"]._is_context is True
        )

    @pytest.mark.asyncio
    async def test_context_decorator_without_store_no_registration(self) -> None:
        """@context decorator without store should not fail."""

        @context(name="no_store_context")
        async def my_context(user_id: str) -> str:
            return f"Hello {user_id}"

        # Should still work
        result = await my_context(user_id="test")
        assert isinstance(result, Context)
        assert result.content == "Hello test"


class TestReplayContext:
    """Tests for FeatureStore.replay_context method."""

    @pytest.fixture
    def mock_store(self) -> MagicMock:
        """Create a mock FeatureStore with required components."""
        store = MagicMock(spec=FeatureStore)
        store.registry = FeatureRegistry()
        store.offline_store = AsyncMock()
        return store

    @pytest.mark.asyncio
    async def test_replay_context_not_found(self, mock_store: MagicMock) -> None:
        """Should return None when context not found."""
        mock_store.offline_store.get_context = AsyncMock(return_value=None)

        # Call the actual method
        store = FeatureStore.__new__(FeatureStore)
        store.registry = mock_store.registry
        store.offline_store = mock_store.offline_store

        result = await store.replay_context("nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_replay_context_no_timestamp_returns_stored(
        self, mock_store: MagicMock
    ) -> None:
        """Should return stored context when no timestamp provided."""
        stored_data = {
            "context_id": "test-id",
            "content": "Original content",
            "lineage": None,
            "meta": {"name": "test"},
            "version": "v1",
        }
        mock_store.offline_store.get_context = AsyncMock(return_value=stored_data)

        store = FeatureStore.__new__(FeatureStore)
        store.registry = mock_store.registry
        store.offline_store = mock_store.offline_store

        result = await store.replay_context("test-id")
        assert result is not None
        assert result.id == "test-id"
        assert result.content == "Original content"

    @pytest.mark.asyncio
    async def test_replay_context_no_lineage_returns_stored(
        self, mock_store: MagicMock
    ) -> None:
        """Should return stored context when no lineage available."""
        stored_data = {
            "context_id": "test-id",
            "content": "Original content",
            "lineage": None,
            "meta": {},
            "version": "v1",
        }
        mock_store.offline_store.get_context = AsyncMock(return_value=stored_data)

        store = FeatureStore.__new__(FeatureStore)
        store.registry = mock_store.registry
        store.offline_store = mock_store.offline_store

        timestamp = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        result = await store.replay_context("test-id", timestamp=timestamp)
        assert result is not None
        assert result.content == "Original content"

    @pytest.mark.asyncio
    async def test_replay_context_missing_context_name(
        self, mock_store: MagicMock
    ) -> None:
        """Should return stored context when context_name not in lineage."""
        stored_data = {
            "context_id": "test-id",
            "content": "Original content",
            "lineage": {
                "context_id": "test-id",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "context_name": None,  # Missing
                "context_args": {"user": "test"},
            },
            "meta": {},
            "version": "v1",
        }
        mock_store.offline_store.get_context = AsyncMock(return_value=stored_data)

        store = FeatureStore.__new__(FeatureStore)
        store.registry = mock_store.registry
        store.offline_store = mock_store.offline_store

        timestamp = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        result = await store.replay_context("test-id", timestamp=timestamp)
        assert result is not None
        assert result.content == "Original content"

    @pytest.mark.asyncio
    async def test_replay_context_function_not_registered(
        self, mock_store: MagicMock
    ) -> None:
        """Should return stored context when function not registered."""
        stored_data = {
            "context_id": "test-id",
            "content": "Original content",
            "lineage": {
                "context_id": "test-id",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "context_name": "unregistered_func",
                "context_args": {"user": "test"},
            },
            "meta": {},
            "version": "v1",
        }
        mock_store.offline_store.get_context = AsyncMock(return_value=stored_data)

        store = FeatureStore.__new__(FeatureStore)
        store.registry = mock_store.registry  # Empty registry
        store.offline_store = mock_store.offline_store

        timestamp = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        result = await store.replay_context("test-id", timestamp=timestamp)
        assert result is not None
        assert result.content == "Original content"

    @pytest.mark.asyncio
    async def test_replay_context_success(self, mock_store: MagicMock) -> None:
        """Should replay context with time travel when all info available."""
        # Setup stored context with lineage
        stored_data = {
            "context_id": "original-id",
            "content": "Original content",
            "lineage": {
                "context_id": "original-id",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "context_name": "replay_test_context",
                "context_args": {"user_id": "user123"},
            },
            "meta": {"name": "replay_test_context"},
            "version": "v1",
        }
        mock_store.offline_store.get_context = AsyncMock(return_value=stored_data)

        # Create and register a context function
        call_count = 0

        @context(name="replay_test_context")
        async def replay_test_context(user_id: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"Replayed for {user_id}"

        mock_store.registry.register_context("replay_test_context", replay_test_context)

        store = FeatureStore.__new__(FeatureStore)
        store.registry = mock_store.registry
        store.offline_store = mock_store.offline_store

        # Replay with timestamp
        timestamp = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        result = await store.replay_context("original-id", timestamp=timestamp)

        assert result is not None
        assert "Replayed for user123" in result.content
        assert result.meta.get("replayed_from") == "original-id"
        assert result.meta.get("replay_timestamp") == timestamp.isoformat()
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_replay_context_sets_time_travel(self, mock_store: MagicMock) -> None:
        """Time travel context should be set during replay."""
        stored_data = {
            "context_id": "original-id",
            "content": "Original content",
            "lineage": {
                "context_id": "original-id",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "context_name": "time_check_context",
                # Must have non-empty context_args (empty dict is falsy in Python)
                "context_args": {"_placeholder": True},
            },
            "meta": {},
            "version": "v1",
        }
        mock_store.offline_store.get_context = AsyncMock(return_value=stored_data)

        captured_timestamp = None

        @context(name="time_check_context")
        async def time_check_context(_placeholder: bool = True) -> str:
            nonlocal captured_timestamp
            captured_timestamp = get_time_travel_timestamp()
            return "Done"

        mock_store.registry.register_context("time_check_context", time_check_context)

        store = FeatureStore.__new__(FeatureStore)
        store.registry = mock_store.registry
        store.offline_store = mock_store.offline_store

        replay_time = datetime(2024, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
        await store.replay_context("original-id", timestamp=replay_time)

        assert captured_timestamp == replay_time

    @pytest.mark.asyncio
    async def test_replay_context_clears_time_travel_on_success(
        self, mock_store: MagicMock
    ) -> None:
        """Time travel context should be cleared after successful replay."""
        stored_data = {
            "context_id": "original-id",
            "content": "Original content",
            "lineage": {
                "context_id": "original-id",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "context_name": "cleanup_test",
                "context_args": {},
            },
            "meta": {},
            "version": "v1",
        }
        mock_store.offline_store.get_context = AsyncMock(return_value=stored_data)

        @context(name="cleanup_test")
        async def cleanup_test() -> str:
            return "Done"

        mock_store.registry.register_context("cleanup_test", cleanup_test)

        store = FeatureStore.__new__(FeatureStore)
        store.registry = mock_store.registry
        store.offline_store = mock_store.offline_store

        replay_time = datetime(2024, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
        await store.replay_context("original-id", timestamp=replay_time)

        # Should be cleared after replay
        assert get_time_travel_timestamp() is None

    @pytest.mark.asyncio
    async def test_replay_context_clears_time_travel_on_error(
        self, mock_store: MagicMock
    ) -> None:
        """Time travel context should be cleared even if replay fails."""
        stored_data = {
            "context_id": "original-id",
            "content": "Original content",
            "lineage": {
                "context_id": "original-id",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "context_name": "error_test",
                "context_args": {},
            },
            "meta": {},
            "version": "v1",
        }
        mock_store.offline_store.get_context = AsyncMock(return_value=stored_data)

        @context(name="error_test")
        async def error_test() -> str:
            raise ValueError("Test error")

        mock_store.registry.register_context("error_test", error_test)

        store = FeatureStore.__new__(FeatureStore)
        store.registry = mock_store.registry
        store.offline_store = mock_store.offline_store

        replay_time = datetime(2024, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
        # Should not raise, returns stored context on error
        result = await store.replay_context("original-id", timestamp=replay_time)

        # Should still return stored content
        assert result is not None
        assert result.content == "Original content"
        # Time travel should be cleared
        assert get_time_travel_timestamp() is None


class TestReplayAPIEndpoint:
    """Tests for the /v1/context/{context_id}/replay API endpoint."""

    @pytest.fixture
    def replay_client(self) -> TestClient:
        """Create a test client with mocked replay_context."""
        from fabra.server import create_app
        from fabra.context import Context

        mock_store = MagicMock(spec=FeatureStore)
        mock_store.online_store = MagicMock()
        mock_store.registry = FeatureRegistry()

        # Mock replay_context to return a Context
        mock_ctx = Context(
            id="replayed-id",
            content="Replayed content",
            meta={"replayed_from": "original-id", "freshness_status": "guaranteed"},
            lineage=None,
            version="v1",
        )
        mock_store.replay_context = AsyncMock(return_value=mock_ctx)

        app = create_app(mock_store)
        return TestClient(app)

    def test_replay_endpoint_success(self, replay_client: TestClient) -> None:
        """Replay endpoint should return replayed context."""
        response = replay_client.post("/v1/context/test-id/replay")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "replayed-id"
        assert data["content"] == "Replayed content"
        assert data["meta"]["replayed_from"] == "original-id"

    def test_replay_endpoint_with_timestamp(self, replay_client: TestClient) -> None:
        """Replay endpoint should accept timestamp parameter."""
        response = replay_client.post(
            "/v1/context/test-id/replay?timestamp=2024-01-15T12:00:00Z"
        )
        assert response.status_code == 200

    def test_replay_endpoint_invalid_timestamp(self) -> None:
        """Replay endpoint should return 400 for invalid timestamp."""
        from fabra.server import create_app

        mock_store = MagicMock(spec=FeatureStore)
        mock_store.online_store = MagicMock()
        mock_store.registry = FeatureRegistry()
        # Make replay_context raise ValueError for bad timestamp parsing
        mock_store.replay_context = AsyncMock(
            side_effect=ValueError("Invalid timestamp")
        )

        app = create_app(mock_store)
        client = TestClient(app)

        response = client.post("/v1/context/test-id/replay?timestamp=not-a-timestamp")
        assert response.status_code == 400
        assert "Invalid timestamp" in response.json()["detail"]

    def test_replay_endpoint_not_found(self) -> None:
        """Replay endpoint should return 404 when context not found."""
        from fabra.server import create_app

        mock_store = MagicMock(spec=FeatureStore)
        mock_store.online_store = MagicMock()
        mock_store.registry = FeatureRegistry()
        mock_store.replay_context = AsyncMock(return_value=None)

        app = create_app(mock_store)
        client = TestClient(app)

        response = client.post("/v1/context/nonexistent/replay")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_replay_endpoint_with_lineage(self) -> None:
        """Replay endpoint should include lineage in response."""
        from fabra.server import create_app
        from fabra.context import Context

        mock_store = MagicMock(spec=FeatureStore)
        mock_store.online_store = MagicMock()
        mock_store.registry = FeatureRegistry()

        lineage = ContextLineage(
            context_id="replayed-id",
            timestamp=datetime.now(timezone.utc),
            context_name="test_context",
            context_args={"user_id": "test"},
        )
        mock_ctx = Context(
            id="replayed-id",
            content="Replayed content",
            meta={},
            lineage=lineage,
            version="v1",
        )
        mock_store.replay_context = AsyncMock(return_value=mock_ctx)

        app = create_app(mock_store)
        client = TestClient(app)

        response = client.post("/v1/context/test-id/replay")
        assert response.status_code == 200
        data = response.json()
        assert "lineage" in data
        assert data["lineage"]["context_name"] == "test_context"


class TestContextLineageForReplay:
    """Tests that context decorator stores replay info in lineage."""

    @pytest.mark.asyncio
    async def test_context_stores_name_in_lineage(self) -> None:
        """Context should store context_name in lineage."""
        mock_offline_store = AsyncMock()
        mock_offline_store.log_context = AsyncMock()

        mock_store = MagicMock()
        mock_store.online_store = None
        mock_store.offline_store = mock_offline_store
        mock_store.registry = FeatureRegistry()

        @context(store=mock_store, name="lineage_name_test")
        async def my_func(user: str) -> str:
            return f"Hello {user}"

        await my_func(user="test")

        # Check log_context was called
        assert mock_offline_store.log_context.called
        call_args = mock_offline_store.log_context.call_args

        # Verify lineage contains context_name
        lineage = call_args.kwargs.get("lineage", {})
        assert lineage.get("context_name") == "lineage_name_test"

    @pytest.mark.asyncio
    async def test_context_stores_args_in_lineage(self) -> None:
        """Context should store serializable context_args in lineage."""
        mock_offline_store = AsyncMock()
        mock_offline_store.log_context = AsyncMock()

        mock_store = MagicMock()
        mock_store.online_store = None
        mock_store.offline_store = mock_offline_store
        mock_store.registry = FeatureRegistry()

        @context(store=mock_store, name="lineage_args_test")
        async def my_func(user_id: str, limit: int) -> str:
            return f"User {user_id}, limit {limit}"

        await my_func(user_id="user123", limit=10)

        # Check log_context was called
        assert mock_offline_store.log_context.called
        call_args = mock_offline_store.log_context.call_args

        # Verify lineage contains context_args
        lineage = call_args.kwargs.get("lineage", {})
        assert lineage.get("context_args") == {"user_id": "user123", "limit": 10}

    @pytest.mark.asyncio
    async def test_context_skips_non_serializable_args(self) -> None:
        """Context should skip non-JSON-serializable args."""
        mock_offline_store = AsyncMock()
        mock_offline_store.log_context = AsyncMock()

        mock_store = MagicMock()
        mock_store.online_store = None
        mock_store.offline_store = mock_offline_store
        mock_store.registry = FeatureRegistry()

        @context(store=mock_store, name="nonserial_test")
        async def my_func(user_id: str, callback: object) -> str:
            return f"User {user_id}"

        # Pass a non-serializable object
        await my_func(user_id="user123", callback=lambda x: x)

        # Check log_context was called
        assert mock_offline_store.log_context.called
        call_args = mock_offline_store.log_context.call_args

        # Verify lineage only contains serializable args
        lineage = call_args.kwargs.get("lineage", {})
        context_args = lineage.get("context_args", {})
        assert "user_id" in context_args
        assert "callback" not in context_args  # Lambda not serializable
