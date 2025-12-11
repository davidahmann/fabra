"""
Context comparison utilities for differential analysis.

Provides functionality to compare two context assemblies and identify
what features, retrievers, and content changed between them.
"""

from typing import List, Optional, Dict
from datetime import datetime, timezone
import difflib

from fabra.models import (
    ContextLineage,
    ContextDiff,
    FeatureDiff,
    RetrieverDiff,
    ContentDiff,
    FeatureLineage,
    RetrieverLineage,
)


def compare_features(
    base_features: List[FeatureLineage],
    comparison_features: List[FeatureLineage],
) -> tuple[List[FeatureDiff], int, int, int]:
    """
    Compare features between two contexts.

    Returns:
        Tuple of (feature_diffs, added_count, removed_count, modified_count)
    """
    diffs: List[FeatureDiff] = []
    added = 0
    removed = 0
    modified = 0

    # Create lookup maps by (feature_name, entity_id)
    base_map: Dict[tuple[str, str], FeatureLineage] = {
        (f.feature_name, f.entity_id): f for f in base_features
    }
    comparison_map: Dict[tuple[str, str], FeatureLineage] = {
        (f.feature_name, f.entity_id): f for f in comparison_features
    }

    all_keys = set(base_map.keys()) | set(comparison_map.keys())

    for key in all_keys:
        feature_name, entity_id = key
        base_feature = base_map.get(key)
        comp_feature = comparison_map.get(key)

        if base_feature is None and comp_feature is not None:
            # Added
            diffs.append(
                FeatureDiff(
                    feature_name=feature_name,
                    entity_id=entity_id,
                    old_value=None,
                    new_value=comp_feature.value,
                    change_type="added",
                    old_freshness_ms=None,
                    new_freshness_ms=comp_feature.freshness_ms,
                )
            )
            added += 1
        elif base_feature is not None and comp_feature is None:
            # Removed
            diffs.append(
                FeatureDiff(
                    feature_name=feature_name,
                    entity_id=entity_id,
                    old_value=base_feature.value,
                    new_value=None,
                    change_type="removed",
                    old_freshness_ms=base_feature.freshness_ms,
                    new_freshness_ms=None,
                )
            )
            removed += 1
        elif base_feature is not None and comp_feature is not None:
            # Check if modified
            if base_feature.value != comp_feature.value:
                diffs.append(
                    FeatureDiff(
                        feature_name=feature_name,
                        entity_id=entity_id,
                        old_value=base_feature.value,
                        new_value=comp_feature.value,
                        change_type="modified",
                        old_freshness_ms=base_feature.freshness_ms,
                        new_freshness_ms=comp_feature.freshness_ms,
                    )
                )
                modified += 1
            else:
                # Unchanged but include for completeness if values same
                diffs.append(
                    FeatureDiff(
                        feature_name=feature_name,
                        entity_id=entity_id,
                        old_value=base_feature.value,
                        new_value=comp_feature.value,
                        change_type="unchanged",
                        old_freshness_ms=base_feature.freshness_ms,
                        new_freshness_ms=comp_feature.freshness_ms,
                    )
                )

    return diffs, added, removed, modified


def compare_retrievers(
    base_retrievers: List[RetrieverLineage],
    comparison_retrievers: List[RetrieverLineage],
) -> tuple[List[RetrieverDiff], int, int, int]:
    """
    Compare retrievers between two contexts.

    Returns:
        Tuple of (retriever_diffs, added_count, removed_count, modified_count)
    """
    diffs: List[RetrieverDiff] = []
    added = 0
    removed = 0
    modified = 0

    # Create lookup maps by retriever_name
    base_map: Dict[str, RetrieverLineage] = {
        r.retriever_name: r for r in base_retrievers
    }
    comparison_map: Dict[str, RetrieverLineage] = {
        r.retriever_name: r for r in comparison_retrievers
    }

    all_names = set(base_map.keys()) | set(comparison_map.keys())

    for name in all_names:
        base_ret = base_map.get(name)
        comp_ret = comparison_map.get(name)

        if base_ret is None and comp_ret is not None:
            # Added
            diffs.append(
                RetrieverDiff(
                    retriever_name=name,
                    query_changed=True,
                    old_query=None,
                    new_query=comp_ret.query,
                    old_results_count=0,
                    new_results_count=comp_ret.results_count,
                    chunks_added=[c.chunk_id for c in comp_ret.chunks_returned],
                    chunks_removed=[],
                    change_type="added",
                )
            )
            added += 1
        elif base_ret is not None and comp_ret is None:
            # Removed
            diffs.append(
                RetrieverDiff(
                    retriever_name=name,
                    query_changed=True,
                    old_query=base_ret.query,
                    new_query=None,
                    old_results_count=base_ret.results_count,
                    new_results_count=0,
                    chunks_added=[],
                    chunks_removed=[c.chunk_id for c in base_ret.chunks_returned],
                    change_type="removed",
                )
            )
            removed += 1
        elif base_ret is not None and comp_ret is not None:
            # Compare chunks
            base_chunk_ids = {c.chunk_id for c in base_ret.chunks_returned}
            comp_chunk_ids = {c.chunk_id for c in comp_ret.chunks_returned}

            chunks_added = list(comp_chunk_ids - base_chunk_ids)
            chunks_removed = list(base_chunk_ids - comp_chunk_ids)
            query_changed = base_ret.query != comp_ret.query

            if query_changed or chunks_added or chunks_removed:
                diffs.append(
                    RetrieverDiff(
                        retriever_name=name,
                        query_changed=query_changed,
                        old_query=base_ret.query,
                        new_query=comp_ret.query,
                        old_results_count=base_ret.results_count,
                        new_results_count=comp_ret.results_count,
                        chunks_added=chunks_added,
                        chunks_removed=chunks_removed,
                        change_type="modified",
                    )
                )
                modified += 1
            else:
                diffs.append(
                    RetrieverDiff(
                        retriever_name=name,
                        query_changed=False,
                        old_query=base_ret.query,
                        new_query=comp_ret.query,
                        old_results_count=base_ret.results_count,
                        new_results_count=comp_ret.results_count,
                        chunks_added=[],
                        chunks_removed=[],
                        change_type="unchanged",
                    )
                )

    return diffs, added, removed, modified


def compare_content(
    base_content: str,
    comparison_content: str,
) -> ContentDiff:
    """
    Compare content strings between two contexts using difflib.

    Returns:
        ContentDiff with line-level change counts and similarity score.
    """
    base_lines = base_content.splitlines(keepends=True)
    comp_lines = comparison_content.splitlines(keepends=True)

    # Use SequenceMatcher for similarity
    matcher = difflib.SequenceMatcher(None, base_content, comparison_content)
    similarity = matcher.ratio()

    # Use unified_diff for line-level changes
    diff = list(difflib.unified_diff(base_lines, comp_lines, lineterm=""))

    lines_added = 0
    lines_removed = 0
    lines_changed = 0

    for line in diff:
        if line.startswith("+") and not line.startswith("+++"):
            lines_added += 1
        elif line.startswith("-") and not line.startswith("---"):
            lines_removed += 1

    # Estimate changed lines as min of added/removed (rough heuristic)
    lines_changed = min(lines_added, lines_removed)
    lines_added -= lines_changed
    lines_removed -= lines_changed

    # Generate human-readable summary
    summary_parts = []
    if lines_added > 0:
        summary_parts.append(f"+{lines_added} lines")
    if lines_removed > 0:
        summary_parts.append(f"-{lines_removed} lines")
    if lines_changed > 0:
        summary_parts.append(f"~{lines_changed} lines modified")

    summary = ", ".join(summary_parts) if summary_parts else "No changes"

    return ContentDiff(
        lines_added=lines_added,
        lines_removed=lines_removed,
        lines_changed=lines_changed,
        similarity_score=similarity,
        diff_summary=summary,
    )


def compare_contexts(
    base_lineage: ContextLineage,
    comparison_lineage: ContextLineage,
    base_content: Optional[str] = None,
    comparison_content: Optional[str] = None,
) -> ContextDiff:
    """
    Compare two context assemblies and return a detailed diff.

    Args:
        base_lineage: Lineage of the base (older) context.
        comparison_lineage: Lineage of the comparison (newer) context.
        base_content: Optional content string of the base context.
        comparison_content: Optional content string of the comparison context.

    Returns:
        ContextDiff with all changes between the two contexts.
    """
    # Calculate time delta
    time_delta_ms = int(
        (comparison_lineage.timestamp - base_lineage.timestamp).total_seconds() * 1000
    )

    # Compare features
    (
        feature_diffs,
        features_added,
        features_removed,
        features_modified,
    ) = compare_features(
        base_lineage.features_used,
        comparison_lineage.features_used,
    )

    # Compare retrievers
    (
        retriever_diffs,
        retrievers_added,
        retrievers_removed,
        retrievers_modified,
    ) = compare_retrievers(
        base_lineage.retrievers_used,
        comparison_lineage.retrievers_used,
    )

    # Compare content if provided
    content_diff = None
    if base_content is not None and comparison_content is not None:
        content_diff = compare_content(base_content, comparison_content)

    # Calculate token/cost deltas
    token_delta = comparison_lineage.token_usage - base_lineage.token_usage
    cost_delta = comparison_lineage.estimated_cost_usd - base_lineage.estimated_cost_usd

    # Determine freshness improvement
    freshness_order = {"guaranteed": 0, "degraded": 1, "unknown": 2}
    base_order = freshness_order.get(base_lineage.freshness_status, 2)
    comp_order = freshness_order.get(comparison_lineage.freshness_status, 2)
    freshness_improved = comp_order < base_order

    # Determine if there are meaningful changes
    has_changes = (
        features_added > 0
        or features_removed > 0
        or features_modified > 0
        or retrievers_added > 0
        or retrievers_removed > 0
        or retrievers_modified > 0
        or (content_diff is not None and content_diff.similarity_score < 1.0)
    )

    # Generate change summary
    summary_parts = []
    if features_added > 0:
        summary_parts.append(f"{features_added} features added")
    if features_removed > 0:
        summary_parts.append(f"{features_removed} features removed")
    if features_modified > 0:
        summary_parts.append(f"{features_modified} features modified")
    if retrievers_added > 0:
        summary_parts.append(f"{retrievers_added} retrievers added")
    if retrievers_removed > 0:
        summary_parts.append(f"{retrievers_removed} retrievers removed")
    if retrievers_modified > 0:
        summary_parts.append(f"{retrievers_modified} retrievers modified")
    if content_diff and content_diff.diff_summary != "No changes":
        summary_parts.append(f"content: {content_diff.diff_summary}")
    if token_delta != 0:
        summary_parts.append(f"tokens: {'+' if token_delta > 0 else ''}{token_delta}")

    change_summary = (
        "; ".join(summary_parts) if summary_parts else "No changes detected"
    )

    return ContextDiff(
        base_context_id=base_lineage.context_id,
        comparison_context_id=comparison_lineage.context_id,
        timestamp=datetime.now(timezone.utc),
        time_delta_ms=time_delta_ms,
        feature_diffs=feature_diffs,
        features_added=features_added,
        features_removed=features_removed,
        features_modified=features_modified,
        retriever_diffs=retriever_diffs,
        retrievers_added=retrievers_added,
        retrievers_removed=retrievers_removed,
        retrievers_modified=retrievers_modified,
        content_diff=content_diff,
        token_delta=token_delta,
        cost_delta_usd=cost_delta,
        base_freshness_status=base_lineage.freshness_status,
        comparison_freshness_status=comparison_lineage.freshness_status,
        freshness_improved=freshness_improved,
        has_changes=has_changes,
        change_summary=change_summary,
    )


def format_diff_report(diff: ContextDiff, verbose: bool = False) -> str:
    """
    Format a ContextDiff as a human-readable report.

    Args:
        diff: The context diff to format.
        verbose: If True, include detailed per-feature/retriever changes.

    Returns:
        Formatted string report.
    """
    lines = []
    lines.append("=" * 60)
    lines.append("Context Diff Report")
    lines.append("=" * 60)
    lines.append(f"Base context:       {diff.base_context_id}")
    lines.append(f"Comparison context: {diff.comparison_context_id}")
    lines.append(f"Time delta:         {diff.time_delta_ms}ms")
    lines.append("")

    # Summary
    lines.append("Summary:")
    lines.append(f"  {diff.change_summary}")
    lines.append("")

    # Features
    lines.append("Features:")
    lines.append(f"  Added:    {diff.features_added}")
    lines.append(f"  Removed:  {diff.features_removed}")
    lines.append(f"  Modified: {diff.features_modified}")

    if verbose and diff.feature_diffs:
        lines.append("")
        for fd in diff.feature_diffs:
            if fd.change_type == "unchanged":
                continue
            lines.append(
                f"    [{fd.change_type.upper()}] {fd.feature_name} ({fd.entity_id})"
            )
            if fd.change_type == "modified":
                lines.append(f"      Old: {fd.old_value}")
                lines.append(f"      New: {fd.new_value}")
            elif fd.change_type == "added":
                lines.append(f"      Value: {fd.new_value}")
            elif fd.change_type == "removed":
                lines.append(f"      Value: {fd.old_value}")

    lines.append("")

    # Retrievers
    lines.append("Retrievers:")
    lines.append(f"  Added:    {diff.retrievers_added}")
    lines.append(f"  Removed:  {diff.retrievers_removed}")
    lines.append(f"  Modified: {diff.retrievers_modified}")

    if verbose and diff.retriever_diffs:
        lines.append("")
        for rd in diff.retriever_diffs:
            if rd.change_type == "unchanged":
                continue
            lines.append(f"    [{rd.change_type.upper()}] {rd.retriever_name}")
            if rd.query_changed:
                lines.append(
                    f"      Query changed: '{rd.old_query}' -> '{rd.new_query}'"
                )
            if rd.chunks_added:
                lines.append(f"      Chunks added: {len(rd.chunks_added)}")
            if rd.chunks_removed:
                lines.append(f"      Chunks removed: {len(rd.chunks_removed)}")

    lines.append("")

    # Content
    if diff.content_diff:
        lines.append("Content:")
        lines.append(f"  Similarity: {diff.content_diff.similarity_score:.2%}")
        lines.append(f"  {diff.content_diff.diff_summary}")
    lines.append("")

    # Token/Cost
    lines.append("Token/Cost Changes:")
    token_sign = "+" if diff.token_delta > 0 else ""
    cost_sign = "+" if diff.cost_delta_usd > 0 else ""
    lines.append(f"  Tokens: {token_sign}{diff.token_delta}")
    lines.append(f"  Cost:   {cost_sign}${diff.cost_delta_usd:.6f}")
    lines.append("")

    # Freshness
    lines.append("Freshness:")
    lines.append(f"  Base:       {diff.base_freshness_status}")
    lines.append(f"  Comparison: {diff.comparison_freshness_status}")
    lines.append(f"  Improved:   {diff.freshness_improved}")

    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)
