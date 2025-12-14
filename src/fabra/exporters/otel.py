from __future__ import annotations

from typing import Any, Optional


def attach_context_id_to_current_span(
    context_id: str, *, attributes: Optional[dict[str, Any]] = None
) -> None:
    """
    Attach `context_id` to the current OpenTelemetry span (if OTEL is available).
    """
    try:
        from opentelemetry import trace  # type: ignore[import-not-found]
    except Exception:
        return

    span = trace.get_current_span()
    if span is None:
        return

    try:
        span.set_attribute("fabra.context_id", context_id)
        for k, v in (attributes or {}).items():
            span.set_attribute(k, v)
        add_event = getattr(span, "add_event", None)
        if callable(add_event):
            add_event("fabra.context_id")
    except Exception:
        # Never fail app code if tracing isn't configured.
        return
