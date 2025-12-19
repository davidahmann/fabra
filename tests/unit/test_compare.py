from datetime import datetime, timedelta, timezone

from fabra.models import (
    ContextLineage,
    FeatureLineage,
    RetrieverLineage,
    ContextRecord,
    AssemblyDecisions,
    IntegrityMetadata,
    LineageMetadata,
)
from fabra.utils.compare import (
    compare_contexts,
    compare_records,
    compare_content,
    compare_features,
)


def make_lineage(features=None, retrievers=None, content=""):
    return ContextLineage(
        context_id="ctx_1",
        timestamp=datetime.now(timezone.utc),
        token_usage=100,
        estimated_cost_usd=0.01,
        features_used=features or [],
        retrievers_used=retrievers or [],
        freshness_status="guaranteed",
    )


def make_lineage_meta(features=None):
    return LineageMetadata(
        features_used=features or [],
        retrievers_used=[],
        indexes_used=[],
        fabra_version="1.0.0",
        assembly_latency_ms=10.0,
        estimated_cost_usd=0.01,
    )


def make_feature(name, entity, value="val"):
    return FeatureLineage(
        feature_name=name,
        entity_id=entity,
        value=value,
        timestamp=datetime.now(timezone.utc),
        freshness_ms=0,
        source="compute",
    )


def test_compare_features():
    # Base: f1, f2
    base = [make_feature("f1", "e1", "v1"), make_feature("f2", "e1", "v2")]
    # Comp: f1 (mod), f3 (new) -- f2 removed
    comp = [make_feature("f1", "e1", "v1_mod"), make_feature("f3", "e1", "v3")]

    diffs, added, removed, modified = compare_features(base, comp)

    assert added == 1  # f3
    assert removed == 1  # f2
    assert modified == 1  # f1
    assert len(diffs) == 3


def test_compare_content():
    base = "line1\nline2\nline3\n"
    comp = "line1\nline2_mod\nline4\n"

    diff = compare_content(base, comp)
    # Just check similarity is less than 1.0 (indicating difference)
    assert diff.similarity_score < 1.0
    assert diff.diff_summary != "No changes"


def test_compare_contexts_no_changes():
    # Use fixed TS to avoid execution time delta
    ts = datetime.now(timezone.utc)
    l1 = make_lineage()
    l1.timestamp = ts
    l2 = make_lineage()
    l2.timestamp = ts + timedelta(seconds=1)

    diff = compare_contexts(l1, l2, "abc", "abc")
    assert not diff.has_changes
    assert diff.time_delta_ms == 1000


def test_compare_contexts_changes():
    l1 = make_lineage(features=[make_feature("f1", "e1")])
    l2 = make_lineage(features=[])  # Feature removed

    diff = compare_contexts(l1, l2)
    assert diff.has_changes
    assert diff.features_removed == 1


def test_compare_records():
    # Mocking ContextRecord is heavier, let's just use minimal kwargs
    now = datetime.now(timezone.utc)

    base = ContextRecord(
        context_id="c1",
        context_function="fn",
        content="abc",
        inputs={"a": 1},
        features=[],
        retrieved_items=[],
        assembly=AssemblyDecisions(
            tokens_used=10, dropped_items=[], freshness_status="guaranteed"
        ),
        lineage=make_lineage_meta(),
        integrity=IntegrityMetadata(record_hash="rh1", content_hash="h1"),
        created_at=now,
    )

    comp = ContextRecord(
        context_id="c2",
        context_function="fn",
        content="abc",
        inputs={"a": 2},  # Modified input
        features=[],
        retrieved_items=[],
        assembly=AssemblyDecisions(
            tokens_used=12, dropped_items=[], freshness_status="guaranteed"
        ),
        lineage=make_lineage_meta(),
        integrity=IntegrityMetadata(record_hash="rh1", content_hash="h1"),
        created_at=now + timedelta(seconds=5),
    )

    diff = compare_records(base, comp)
    assert diff.has_changes
    assert diff.inputs_modified == 1
    assert diff.time_delta_ms == 5000
    assert diff.token_delta == 2


def make_retriever(name, query, chunks=None):
    return RetrieverLineage(
        retriever_name=name,
        query=query,
        results_count=len(chunks) if chunks else 0,
        chunks_returned=chunks or [],
        latency_ms=10,
    )


def test_compare_retrievers():
    # Base: r1 (q1, [c1]), r2 (q2, [c2])
    # Comp: r1 (q1_mod, [c1, c3]), r3 (new) -- r2 removed

    from fabra.models import DocumentChunkLineage

    # DocumentChunkLineage fields: chunk_id, document_id, content_hash, indexed_at, retriever_name...
    # We need to provide required fields.
    ts = datetime.now(timezone.utc)

    def make_chunk(cid):
        return DocumentChunkLineage(
            chunk_id=cid,
            document_id="doc1",
            content_hash="h",
            indexed_at=ts,
            retriever_name="r",
        )

    c1 = make_chunk("c1")
    c2 = make_chunk("c2")
    c3 = make_chunk("c3")

    base = [make_retriever("r1", "q1", [c1]), make_retriever("r2", "q2", [c2])]
    comp = [make_retriever("r1", "q1_mod", [c1, c3]), make_retriever("r3", "q3", [])]

    from fabra.utils.compare import compare_retrievers

    diffs, added, removed, modified = compare_retrievers(base, comp)

    assert added == 1  # r3
    assert removed == 1  # r2
    assert modified == 1  # r1

    # Check r1 modification details
    r1_diff = next(d for d in diffs if d.retriever_name == "r1")
    assert r1_diff.query_changed
    assert "c3" in r1_diff.chunks_added
    assert not r1_diff.chunks_removed  # c1 is in both


def test_compare_inputs():
    from fabra.utils.compare import compare_inputs

    base = {"a": 1, "b": "text", "c": [1, 2]}
    comp = {"a": 2, "b": "text", "d": "new"}  # c removed

    diffs, added, removed, modified = compare_inputs(base, comp)

    assert added == 1  # d
    assert removed == 1  # c
    assert modified == 1  # a

    # Check specific diffs
    a_diff = next(d for d in diffs if d.key == "a")
    assert a_diff.old_value == 1
    assert a_diff.new_value == 2

    c_diff = next(d for d in diffs if d.key == "c")
    assert c_diff.change_type == "removed"
