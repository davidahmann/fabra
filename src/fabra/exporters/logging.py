from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any


def emit_context_id_json(context_id: str, **fields: Any) -> str:
    """
    Emit a single JSON log line containing `context_id`.

    Returns the JSON string (useful for tests or custom sinks).
    """
    payload: dict[str, Any] = {
        "event": "fabra.context_id",
        "context_id": context_id,
        "ts": datetime.now(timezone.utc).isoformat(),
        **fields,
    }
    text = json.dumps(payload, ensure_ascii=False, default=str)
    logging.getLogger("fabra").info(text)
    return text


def emit_structured(
    logger: logging.Logger, context_id: str, **fields: Any
) -> dict[str, Any]:
    """
    Emit via standard `logging` using an easy-to-index `extra` payload.
    """
    payload = {"context_id": context_id, **fields}
    logger.info("fabra.context_id", extra={"fabra": payload})
    return payload
