from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class ContextTrace(BaseModel):
    """
    Metadata-only trace object for debugging context assembly.
    Does NOT contain the full text content to preserve privacy/log-size.
    """

    context_id: str = Field(
        ..., description="The unique UUIDv7 of the context assembly"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp",
    )
    latency_ms: float = Field(..., description="Total assembly time in milliseconds")

    # Costs
    token_usage: int = Field(..., description="Total tokens used in the final context")
    cost_usd: Optional[float] = Field(None, description="Estimated cost in USD")

    # Freshness
    freshness_status: str = Field(..., description="'guaranteed' or 'degraded'")
    stale_sources: List[str] = Field(
        default_factory=list, description="List of source IDs that violated SLA"
    )

    # Lineage
    source_ids: List[str] = Field(
        default_factory=list, description="IDs of source items used"
    )
    cache_hit: bool = Field(False, description="Whether this was served from cache")

    # Missing Data (for debugging)
    missing_features: List[str] = Field(
        default_factory=list, description="Features that were requested but not found"
    )

    meta: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
