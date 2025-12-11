"""
Retriever snapshot utilities for replay and drift detection.

Provides functionality to:
- Capture snapshots of retriever results
- Store and retrieve snapshots
- Replay snapshots and detect drift
"""

from typing import List, Optional, Dict, Any, Callable, Awaitable
from datetime import datetime, timezone
import hashlib
import json
import uuid6

from fabra.models import (
    RetrieverSnapshot,
    RetrieverReplayResult,
    DocumentChunkLineage,
)


def create_snapshot(
    retriever_name: str,
    query: str,
    results: List[Dict[str, Any]],
    latency_ms: float = 0.0,
    index_name: Optional[str] = None,
    embedding_model: Optional[str] = None,
    search_params: Optional[Dict[str, Any]] = None,
    context_id: Optional[str] = None,
) -> RetrieverSnapshot:
    """
    Create a snapshot from retriever results.

    Args:
        retriever_name: Name of the retriever.
        query: Query string that was executed.
        results: List of result dictionaries from the retriever.
        latency_ms: Time taken for retrieval.
        index_name: Optional index/collection searched.
        embedding_model: Optional embedding model used.
        search_params: Optional search parameters.
        context_id: Optional context ID this snapshot belongs to.

    Returns:
        RetrieverSnapshot with all data captured.
    """
    snapshot_id = str(uuid6.uuid7())
    now = datetime.now(timezone.utc)

    # Process results into chunk lineages and content map
    chunks: List[DocumentChunkLineage] = []
    chunk_contents: Dict[str, str] = {}

    for i, result in enumerate(results):
        # Extract chunk info from result (assuming common RAG result structure)
        chunk_id = result.get("chunk_id") or result.get("id") or f"chunk_{i}"
        content = result.get("content") or result.get("text") or ""
        document_id = result.get("document_id") or result.get("doc_id") or "unknown"

        # Store content
        chunk_contents[chunk_id] = content

        # Calculate content hash
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        # Parse indexed_at if present
        indexed_at = result.get("indexed_at")
        if isinstance(indexed_at, str):
            indexed_at = datetime.fromisoformat(indexed_at.replace("Z", "+00:00"))
        elif indexed_at is None:
            indexed_at = now

        # Create chunk lineage
        chunk = DocumentChunkLineage(
            chunk_id=chunk_id,
            document_id=document_id,
            content_hash=content_hash,
            source_url=result.get("source_url") or result.get("url"),
            indexed_at=indexed_at,
            document_modified_at=result.get("document_modified_at"),
            freshness_ms=result.get("freshness_ms", 0),
            is_stale=result.get("is_stale", False),
            similarity_score=result.get("similarity_score")
            or result.get("score")
            or 0.0,
            retriever_name=retriever_name,
            position_in_results=i,
        )
        chunks.append(chunk)

    return RetrieverSnapshot(
        snapshot_id=snapshot_id,
        retriever_name=retriever_name,
        query=query,
        timestamp=now,
        results=results,
        results_count=len(results),
        chunks=chunks,
        chunk_contents=chunk_contents,
        latency_ms=latency_ms,
        index_name=index_name,
        embedding_model=embedding_model,
        search_params=search_params or {},
        context_id=context_id,
    )


async def replay_snapshot(
    snapshot: RetrieverSnapshot,
    retriever_fn: Callable[[str], Awaitable[List[Dict[str, Any]]]],
) -> RetrieverReplayResult:
    """
    Replay a snapshot by re-executing the query and comparing results.

    Args:
        snapshot: The snapshot to replay.
        retriever_fn: Async function that takes a query and returns results.

    Returns:
        RetrieverReplayResult with drift analysis.
    """
    # Execute live retrieval
    live_results = await retriever_fn(snapshot.query)

    # Build maps for comparison
    snapshot_chunks = {c.chunk_id: c for c in snapshot.chunks}
    snapshot_contents = snapshot.chunk_contents

    # Process live results
    live_chunk_ids = set()
    live_scores: Dict[str, float] = {}
    live_contents: Dict[str, str] = {}

    for i, result in enumerate(live_results):
        chunk_id = result.get("chunk_id") or result.get("id") or f"chunk_{i}"
        live_chunk_ids.add(chunk_id)
        live_scores[chunk_id] = (
            result.get("similarity_score") or result.get("score") or 0.0
        )
        live_contents[chunk_id] = result.get("content") or result.get("text") or ""

    snapshot_chunk_ids = set(snapshot_chunks.keys())

    # Compute diffs
    chunks_added = list(live_chunk_ids - snapshot_chunk_ids)
    chunks_removed = list(snapshot_chunk_ids - live_chunk_ids)

    # Check for modified content (chunks present in both)
    common_chunks = live_chunk_ids & snapshot_chunk_ids
    chunks_modified = []
    for chunk_id in common_chunks:
        snapshot_content = snapshot_contents.get(chunk_id, "")
        live_content = live_contents.get(chunk_id, "")
        if snapshot_content != live_content:
            chunks_modified.append(chunk_id)

    # Compute score drift for common chunks
    score_drift: Dict[str, float] = {}
    for chunk_id in common_chunks:
        snapshot_score = snapshot_chunks[chunk_id].similarity_score
        live_score = live_scores.get(chunk_id, 0.0)
        drift = live_score - snapshot_score
        if abs(drift) > 0.001:  # Only track meaningful drift
            score_drift[chunk_id] = drift

    # Calculate drift statistics
    max_score_drift = max(abs(d) for d in score_drift.values()) if score_drift else 0.0
    avg_score_drift = (
        sum(score_drift.values()) / len(score_drift) if score_drift else 0.0
    )

    # Determine if there's meaningful drift
    has_drift = bool(
        chunks_added or chunks_removed or chunks_modified or max_score_drift > 0.05
    )

    # Generate summary
    summary_parts = []
    if chunks_added:
        summary_parts.append(f"+{len(chunks_added)} chunks")
    if chunks_removed:
        summary_parts.append(f"-{len(chunks_removed)} chunks")
    if chunks_modified:
        summary_parts.append(f"~{len(chunks_modified)} modified")
    if max_score_drift > 0.05:
        summary_parts.append(f"score drift: {max_score_drift:.3f}")

    drift_summary = "; ".join(summary_parts) if summary_parts else "No drift detected"

    return RetrieverReplayResult(
        snapshot_id=snapshot.snapshot_id,
        replayed_at=datetime.now(timezone.utc),
        live_results_count=len(live_results),
        snapshot_results_count=snapshot.results_count,
        chunks_added=chunks_added,
        chunks_removed=chunks_removed,
        chunks_modified=chunks_modified,
        score_drift=score_drift,
        max_score_drift=max_score_drift,
        avg_score_drift=avg_score_drift,
        has_drift=has_drift,
        drift_summary=drift_summary,
    )


def serialize_snapshot(snapshot: RetrieverSnapshot) -> str:
    """Serialize a snapshot to JSON string for storage."""
    return snapshot.model_dump_json()


def deserialize_snapshot(data: str) -> RetrieverSnapshot:
    """Deserialize a snapshot from JSON string."""
    return RetrieverSnapshot.model_validate_json(data)


async def store_snapshot(
    snapshot: RetrieverSnapshot,
    backend: Any,
    ttl_seconds: int = 86400 * 7,  # 7 days default
) -> None:
    """
    Store a snapshot in the online store.

    Args:
        snapshot: The snapshot to store.
        backend: Redis-like backend with set method.
        ttl_seconds: Time-to-live in seconds.
    """
    key = f"retriever_snapshot:{snapshot.snapshot_id}"
    await backend.set(key, serialize_snapshot(snapshot), ex=ttl_seconds)

    # Also index by context_id if present
    if snapshot.context_id:
        context_key = f"context_snapshots:{snapshot.context_id}"
        # Add snapshot_id to a set for this context
        if hasattr(backend, "sadd"):
            await backend.sadd(context_key, snapshot.snapshot_id)
            await backend.expire(context_key, ttl_seconds)


async def get_snapshot(
    snapshot_id: str,
    backend: Any,
) -> Optional[RetrieverSnapshot]:
    """
    Retrieve a snapshot from the online store.

    Args:
        snapshot_id: The snapshot ID to retrieve.
        backend: Redis-like backend with get method.

    Returns:
        RetrieverSnapshot or None if not found.
    """
    key = f"retriever_snapshot:{snapshot_id}"
    data = await backend.get(key)
    if data:
        if isinstance(data, bytes):
            data = data.decode()
        return deserialize_snapshot(data)
    return None


async def get_context_snapshots(
    context_id: str,
    backend: Any,
) -> List[RetrieverSnapshot]:
    """
    Get all snapshots for a given context.

    Args:
        context_id: The context ID to find snapshots for.
        backend: Redis-like backend.

    Returns:
        List of RetrieverSnapshots for this context.
    """
    context_key = f"context_snapshots:{context_id}"

    # Get snapshot IDs from set
    snapshot_ids = []
    if hasattr(backend, "smembers"):
        snapshot_ids = await backend.smembers(context_key)
    elif hasattr(backend, "get"):
        # Fallback: might be stored differently
        data = await backend.get(context_key)
        if data:
            snapshot_ids = json.loads(data) if isinstance(data, str) else []

    # Fetch each snapshot
    snapshots = []
    for sid in snapshot_ids:
        if isinstance(sid, bytes):
            sid = sid.decode()
        snapshot = await get_snapshot(sid, backend)
        if snapshot:
            snapshots.append(snapshot)

    return snapshots


def format_replay_report(result: RetrieverReplayResult, verbose: bool = False) -> str:
    """
    Format a replay result as a human-readable report.

    Args:
        result: The replay result to format.
        verbose: If True, include detailed chunk-level info.

    Returns:
        Formatted string report.
    """
    lines = []
    lines.append("=" * 60)
    lines.append("Retriever Replay Report")
    lines.append("=" * 60)
    lines.append(f"Snapshot ID: {result.snapshot_id}")
    lines.append(f"Replayed at: {result.replayed_at.isoformat()}")
    lines.append("")

    # Results comparison
    lines.append("Results Count:")
    lines.append(f"  Snapshot: {result.snapshot_results_count}")
    lines.append(f"  Live:     {result.live_results_count}")
    delta = result.live_results_count - result.snapshot_results_count
    if delta != 0:
        lines.append(f"  Delta:    {'+' if delta > 0 else ''}{delta}")
    lines.append("")

    # Drift summary
    lines.append("Drift Analysis:")
    lines.append(f"  Has drift: {result.has_drift}")
    lines.append(f"  Summary:   {result.drift_summary}")
    lines.append("")

    if result.chunks_added:
        lines.append(f"Chunks Added ({len(result.chunks_added)}):")
        for chunk_id in result.chunks_added[:5]:  # Limit display
            lines.append(f"  + {chunk_id}")
        if len(result.chunks_added) > 5:
            lines.append(f"  ... and {len(result.chunks_added) - 5} more")
        lines.append("")

    if result.chunks_removed:
        lines.append(f"Chunks Removed ({len(result.chunks_removed)}):")
        for chunk_id in result.chunks_removed[:5]:
            lines.append(f"  - {chunk_id}")
        if len(result.chunks_removed) > 5:
            lines.append(f"  ... and {len(result.chunks_removed) - 5} more")
        lines.append("")

    if result.chunks_modified:
        lines.append(f"Chunks Modified ({len(result.chunks_modified)}):")
        for chunk_id in result.chunks_modified[:5]:
            lines.append(f"  ~ {chunk_id}")
        if len(result.chunks_modified) > 5:
            lines.append(f"  ... and {len(result.chunks_modified) - 5} more")
        lines.append("")

    # Score drift
    if result.score_drift:
        lines.append("Score Drift:")
        lines.append(f"  Max drift: {result.max_score_drift:.4f}")
        lines.append(f"  Avg drift: {result.avg_score_drift:.4f}")
        if verbose:
            lines.append("  Per-chunk drift:")
            for chunk_id, drift in sorted(
                result.score_drift.items(), key=lambda x: abs(x[1]), reverse=True
            )[:10]:
                lines.append(f"    {chunk_id}: {'+' if drift > 0 else ''}{drift:.4f}")
        lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)
