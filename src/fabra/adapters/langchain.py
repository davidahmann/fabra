from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Optional, cast

from fabra.exporters.logging import emit_context_id_json
from fabra.exporters.otel import attach_context_id_to_current_span
from fabra.receipts import ReceiptRecorder


@dataclass
class _PendingRun:
    started_at_s: float
    prompts: list[str]
    serialized: dict[str, Any]
    metadata: dict[str, Any]
    tags: list[str]


class FabraLangChainCallbackHandler:
    """
    A thin LangChain-style callback handler that creates a durable CRS-001 receipt.

    This does not require LangChain at import time. If you're using LangChain,
    you can pass this instance as a callback handler.
    """

    def __init__(
        self,
        *,
        recorder: ReceiptRecorder,
        emit_logs: bool = True,
        emit_otel: bool = True,
        max_capture_chars: int = 50_000,
    ) -> None:
        self._recorder = recorder
        self._emit_logs = emit_logs
        self._emit_otel = emit_otel
        self._max_capture_chars = max_capture_chars
        self._pending: dict[str, _PendingRun] = {}
        self._context_ids: dict[str, str] = {}

    def get_context_id(self, run_id: str) -> Optional[str]:
        return self._context_ids.get(run_id)

    def on_llm_start(  # LangChain signature-compatible (best effort)
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: str,
        parent_run_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        **_: Any,
    ) -> None:
        md = dict(metadata or {})
        if parent_run_id:
            md["parent_run_id"] = parent_run_id

        self._pending[run_id] = _PendingRun(
            started_at_s=time.time(),
            prompts=list(prompts),
            serialized=dict(serialized or {}),
            metadata=md,
            tags=list(tags or []),
        )

    def on_llm_end(self, response: Any, *, run_id: str, **_: Any) -> None:
        pending = self._pending.pop(run_id, None)
        if not pending:
            return

        output_text = _extract_langchain_output_text(response)
        elapsed_ms = max(0, int((time.time() - pending.started_at_s) * 1000))

        prompt_text = "\n\n".join(pending.prompts)
        inputs = {
            "adapter": "langchain",
            "run_id": run_id,
            "tags": pending.tags,
            "metadata": pending.metadata,
            "serialized": _truncate_json(pending.serialized, self._max_capture_chars),
            "output_text": _truncate_str(output_text, self._max_capture_chars),
            "elapsed_ms": elapsed_ms,
        }

        receipt = self._recorder.record_sync(
            context_function="langchain.llm",
            content=_truncate_str(prompt_text, self._max_capture_chars),
            inputs=inputs,
        )

        self._context_ids[run_id] = receipt.context_id

        if self._emit_logs:
            emit_context_id_json(
                receipt.context_id,
                source="langchain",
                run_id=run_id,
            )
        if self._emit_otel:
            attach_context_id_to_current_span(
                receipt.context_id,
                attributes={"fabra.source": "langchain", "fabra.run_id": run_id},
            )

    def on_llm_error(self, error: BaseException, *, run_id: str, **_: Any) -> None:
        pending = self._pending.pop(run_id, None)
        prompts = pending.prompts if pending else []
        prompt_text = "\n\n".join(prompts)
        inputs = {
            "adapter": "langchain",
            "run_id": run_id,
            "error": {"type": type(error).__name__, "message": str(error)},
        }
        receipt = self._recorder.record_sync(
            context_function="langchain.llm.error",
            content=_truncate_str(prompt_text, self._max_capture_chars),
            inputs=inputs,
        )
        self._context_ids[run_id] = receipt.context_id

        if self._emit_logs:
            emit_context_id_json(
                receipt.context_id,
                source="langchain",
                run_id=run_id,
                error_type=type(error).__name__,
            )
        if self._emit_otel:
            attach_context_id_to_current_span(
                receipt.context_id,
                attributes={
                    "fabra.source": "langchain",
                    "fabra.run_id": run_id,
                    "fabra.error_type": type(error).__name__,
                },
            )


def _extract_langchain_output_text(response: Any) -> str:
    generations = getattr(response, "generations", None)
    if isinstance(generations, list) and generations:
        first = generations[0]
        if isinstance(first, list) and first:
            gen0 = first[0]
            if isinstance(gen0, dict) and isinstance(gen0.get("text"), str):
                return cast(str, gen0["text"])
            text = getattr(gen0, "text", None)
            if isinstance(text, str):
                return text

    if isinstance(response, dict):
        for key in ("output_text", "text", "content"):
            if isinstance(response.get(key), str):
                return cast(str, response[key])
    return ""


def _truncate_str(value: str, max_chars: int) -> str:
    if len(value) <= max_chars:
        return value
    return value[:max_chars] + "…"


def _truncate_json(value: Any, max_chars: int) -> Any:
    try:
        text = json.dumps(value, default=str, ensure_ascii=False)
    except Exception:
        return {"_unserializable": True, "repr": _truncate_str(repr(value), max_chars)}
    if len(text) <= max_chars:
        return value
    return {"_truncated_json": True, "json": text[:max_chars] + "…"}
