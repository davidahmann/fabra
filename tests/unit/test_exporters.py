import sys
from unittest.mock import MagicMock, patch
from fabra.exporters.otel import attach_context_id_to_current_span


def test_otel_missing():
    # Simulate opentelemetry not installed
    with patch.dict(sys.modules, {"opentelemetry": None}):
        # Should not raise
        attach_context_id_to_current_span("ctx-123")


def test_otel_installed_no_span():
    # Mock opentelemetry modules structure
    mock_trace_module = MagicMock()
    # mock_span = MagicMock() # Unused
    mock_trace_module.get_current_span.return_value = None

    # We need to mock both the package and the sub-module for "from opentelemetry import trace"
    mock_pkg = MagicMock()
    mock_pkg.trace = mock_trace_module

    with patch.dict(
        sys.modules,
        {"opentelemetry": mock_pkg, "opentelemetry.trace": mock_trace_module},
    ):
        # Force reload? No, it's a local import inside the function, so it runs every time.
        # But if "from opentelemetry import trace" fails, it returns.
        # Ensure the import doesn't raise.

        attach_context_id_to_current_span("ctx-123")
        mock_trace_module.get_current_span.assert_called_once()


def test_otel_installed_with_span():
    mock_span = MagicMock()
    mock_trace_module = MagicMock()
    mock_trace_module.get_current_span.return_value = mock_span

    mock_pkg = MagicMock()
    mock_pkg.trace = mock_trace_module

    with patch.dict(
        sys.modules,
        {"opentelemetry": mock_pkg, "opentelemetry.trace": mock_trace_module},
    ):
        attach_context_id_to_current_span("ctx-123", attributes={"foo": "bar"})

        mock_trace_module.get_current_span.assert_called_once()
        mock_span.set_attribute.assert_any_call("fabra.context_id", "ctx-123")
        mock_span.set_attribute.assert_any_call("foo", "bar")

        # Check for add_event call if callable
        # The code checks `callable(add_event)`.
        # MagicMock is callable by default.
        mock_span.add_event.assert_called_with("fabra.context_id")


def test_otel_exception_safe():
    # Ensure exceptions inside OTEL logic (e.g. span closed) don't crash app
    mock_span = MagicMock()
    mock_span.set_attribute.side_effect = RuntimeError("Span closed")
    mock_trace = MagicMock()
    mock_trace.get_current_span.return_value = mock_span

    with patch.dict(
        sys.modules, {"opentelemetry": MagicMock(), "opentelemetry.trace": mock_trace}
    ):
        # Should catch RuntimeError and return gracefully
        attach_context_id_to_current_span("ctx-123")
