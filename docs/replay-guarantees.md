---
title: "Replay Guarantees"
description: "What Fabra replay guarantees (and what is best-effort): historical feature values, retriever evidence, and how to interpret replay results."
keywords: context replay, time travel, point in time, replay guarantees, ai reproducibility
---

# Replay Guarantees

Fabra uses “replay” in an incident sense: **make a decision reconstructable**.

This page defines what is guaranteed vs best-effort so you can rely on it under pressure.

## Two concepts: show vs replay

### Show (guaranteed if the record exists)
`fabra context show <id>` returns the stored artifact for audit/debugging.

This answers: “what did the system record at decision time?”

### Replay (best-effort execution)
`POST /v1/context/{id}/replay?timestamp=...` re-executes the context function when possible.

This answers: “if we re-run the assembly, what happens?”

## Guarantees

### Feature time-travel (guaranteed when supported)
When you replay with a timestamp, Fabra will retrieve feature values **as of that timestamp** (requires an offline store that supports historical reads).

### Lineage + budgeting
Dropped items and budget decisions are recorded as part of lineage/record metadata and can be inspected later.

## Best-effort (explicitly not guaranteed)

### Retriever determinism
External retrievers (vector DBs, web, SaaS) can change.

Fabra can provide:
- **Evidence replay:** the recorded retrieved items/metadata (what the system recorded)
- **Re-query replay:** re-running the retriever against a changing index (not deterministic by default)

If you need strict reproducibility for retrieval, treat retrieval content as part of the durable artifact (and store it intentionally).

### Code drift
Replay re-executes *current code* unless you pin code version.
If you deploy new context logic, replay may differ even for the same inputs.

## Practical incident guidance

- Use `show` + `diff` to settle “what changed?” quickly.
- Use `verify` when audits/disputes demand tamper-evidence.
- Use replay for confirming hypotheses, not as the only source of truth.
