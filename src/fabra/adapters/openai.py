from __future__ import annotations

import json
from typing import Any, Callable, Literal, TypeVar, overload, cast

from fabra.exporters.logging import emit_context_id_json
from fabra.exporters.otel import attach_context_id_to_current_span
from fabra.receipts import ReceiptRecorder


T = TypeVar("T")


@overload
def wrap_openai_call(
    func: Callable[..., T],
    *,
    recorder: ReceiptRecorder,
    context_function: str = "openai.call",
    emit_logs: bool = True,
    emit_otel: bool = True,
    return_context_id: Literal[False] = False,
    max_capture_chars: int = 50_000,
) -> Callable[..., T]:
    ...


@overload
def wrap_openai_call(
    func: Callable[..., T],
    *,
    recorder: ReceiptRecorder,
    context_function: str = "openai.call",
    emit_logs: bool = True,
    emit_otel: bool = True,
    return_context_id: Literal[True],
    max_capture_chars: int = 50_000,
) -> Callable[..., tuple[T, str]]:
    ...


def wrap_openai_call(
    func: Callable[..., T],
    *,
    recorder: ReceiptRecorder,
    context_function: str = "openai.call",
    emit_logs: bool = True,
    emit_otel: bool = True,
    return_context_id: bool = False,
    max_capture_chars: int = 50_000,
) -> Callable[..., Any]:
    """
    Wrap an OpenAI SDK call site and emit a durable CRS-001 receipt.

    This wrapper is SDK-agnostic: it works with any callable (OpenAI Responses,
    Chat Completions, etc.) by best-effort extracting prompt/response fields.
    """

    def wrapped(*args: Any, **kwargs: Any) -> Any:
        prompt = _extract_prompt(args, kwargs)
        try:
            result = func(*args, **kwargs)
        except BaseException as e:
            receipt = recorder.record_sync(
                context_function=f"{context_function}.error",
                content=_truncate(prompt, max_capture_chars),
                inputs={
                    "adapter": "openai",
                    "error": {"type": type(e).__name__, "message": str(e)},
                    "kwargs": _truncate_json(kwargs, max_capture_chars),
                },
            )
            _emit(
                receipt.context_id,
                emit_logs=emit_logs,
                emit_otel=emit_otel,
                source="openai",
            )
            raise

        response_text = _extract_response_text(result)
        receipt = recorder.record_sync(
            context_function=context_function,
            content=_truncate(prompt, max_capture_chars),
            inputs={
                "adapter": "openai",
                "kwargs": _truncate_json(kwargs, max_capture_chars),
                "response_text": _truncate(response_text, max_capture_chars),
            },
        )

        _emit(
            receipt.context_id,
            emit_logs=emit_logs,
            emit_otel=emit_otel,
            source="openai",
        )
        if return_context_id:
            return result, receipt.context_id
        return result

    return wrapped


def _emit(context_id: str, *, emit_logs: bool, emit_otel: bool, source: str) -> None:
    if emit_logs:
        emit_context_id_json(context_id, source=source)
    if emit_otel:
        attach_context_id_to_current_span(
            context_id, attributes={"fabra.source": source}
        )


def _extract_prompt(args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
    for key in ("input", "prompt", "messages"):
        if key in kwargs:
            return _safe_str(kwargs[key])
    if args:
        return _safe_str(args[0])
    return ""


def _extract_response_text(result: Any) -> str:
    if isinstance(result, dict):
        for key in ("output_text", "text", "content"):
            if isinstance(result.get(key), str):
                return cast(str, result.get(key))
        choices = result.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                msg = first.get("message")
                if isinstance(msg, dict) and isinstance(msg.get("content"), str):
                    return cast(str, msg["content"])
                if isinstance(first.get("text"), str):
                    return cast(str, first["text"])
    # OpenAI SDK objects often expose .output_text or .choices[0].message.content
    for attr in ("output_text", "text", "content"):
        v = getattr(result, attr, None)
        if isinstance(v, str):
            return v
    choices = getattr(result, "choices", None)
    if isinstance(choices, list) and choices:
        c0 = choices[0]
        msg = getattr(c0, "message", None)
        content = getattr(msg, "content", None)
        if isinstance(content, str):
            return content
    return ""


def _safe_str(value: Any) -> str:
    try:
        return json.dumps(value, default=str, ensure_ascii=False)
    except Exception:
        return str(value)


def _truncate(value: str, max_chars: int) -> str:
    if len(value) <= max_chars:
        return value
    return value[:max_chars] + "…"


def _truncate_json(value: Any, max_chars: int) -> Any:
    try:
        text = json.dumps(value, default=str, ensure_ascii=False)
    except Exception:
        return {"_unserializable": True, "repr": _truncate(repr(value), max_chars)}
    if len(text) <= max_chars:
        return value
    return {"_truncated_json": True, "json": text[:max_chars] + "…"}
