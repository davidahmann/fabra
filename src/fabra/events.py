from datetime import datetime, timezone
from typing import Any, Dict
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class AxiomEvent(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    event_type: str
    entity_id: str
    payload: Dict[str, Any]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
