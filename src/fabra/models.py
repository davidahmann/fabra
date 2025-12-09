from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class FeatureLineage(BaseModel):
    """Record of a feature used in context assembly."""

    feature_name: str = Field(..., description="Name of the feature")
    entity_id: str = Field(..., description="Entity ID for which feature was retrieved")
    value: Any = Field(..., description="The feature value used")
    timestamp: datetime = Field(
        ..., description="When this feature value was computed/retrieved"
    )
    freshness_ms: int = Field(
        ..., description="Age of the feature in milliseconds at assembly time"
    )
    source: Literal["cache", "compute", "fallback"] = Field(
        ..., description="Where the value came from"
    )


class RetrieverLineage(BaseModel):
    """Record of a retriever call in context assembly."""

    retriever_name: str = Field(..., description="Name of the retriever")
    query: str = Field(..., description="Query string passed to retriever")
    results_count: int = Field(..., description="Number of results returned")
    latency_ms: float = Field(..., description="Time taken for retrieval in ms")
    index_name: Optional[str] = Field(None, description="Index/collection searched")


class ContextLineage(BaseModel):
    """Full lineage for a context assembly - tracks exactly what data was used."""

    context_id: str = Field(..., description="The UUIDv7 of the parent context")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When assembly occurred",
    )

    # What data sources were used
    features_used: List[FeatureLineage] = Field(
        default_factory=list, description="All features retrieved during assembly"
    )
    retrievers_used: List[RetrieverLineage] = Field(
        default_factory=list, description="All retriever calls made during assembly"
    )

    # Assembly statistics
    items_provided: int = Field(
        0, description="Total items returned by context function"
    )
    items_included: int = Field(0, description="Items that fit within token budget")
    items_dropped: int = Field(0, description="Items dropped due to budget constraints")

    # Freshness tracking
    freshness_status: Literal["guaranteed", "degraded", "unknown"] = Field(
        "unknown", description="Overall freshness of the context"
    )
    stalest_feature_ms: int = Field(
        0, description="Age in ms of the oldest feature used"
    )
    freshness_violations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Features that violated freshness SLA",
    )

    # Token economics
    token_usage: int = Field(0, description="Total tokens in final context")
    max_tokens: Optional[int] = Field(None, description="Token budget limit")
    estimated_cost_usd: float = Field(0.0, description="Estimated cost in USD")


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
