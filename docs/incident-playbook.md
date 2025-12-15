---
title: "Incident Playbook: From Context ID to Fix"
description: "How to use Fabra under incident pressure: paste a context_id into a ticket, reproduce what the AI saw, diff drift, verify integrity, and export evidence."
keywords: incident playbook, context_id, ai incident, ai audit trail, reproducible ai, context records
---

# Incident Playbook: From Context ID to Fix

Fabra is built for one moment: an AI incident where everyone is guessing.

Your goal is to turn “the AI was wrong” into **a reproducible ticket** in minutes.

## Step 0 — Ask for the receipt

In every incident, ask one question:

> “What’s the `context_id`?”

That ID is the atomic unit of evidence.

## Step 1 — Show what the AI saw

```bash
fabra context show <context_id>
```

Use this to answer:
- what data was included
- what got dropped (token budget)
- what features/retrievers were used (lineage)

## Step 2 — Verify integrity (audits / disputes)

```bash
fabra context verify <context_id>
```

This checks cryptographic hashes so you can tell if the record was modified.

## Step 3 — Diff drift between two incidents

Generate a second Context Record (same user, same request, or after a deploy), then:

```bash
fabra context diff <context_id_A> <context_id_B>
```

This is the fastest way to settle arguments:
- “what changed in features?”
- “what changed in retrieval?”
- “did the assembled context change?”

## Step 4 — Export a ticket attachment

For most incidents, you want a single file you can attach to a ticket or PR:

```bash
fabra context pack <context_id> --output incident.zip
```

If you have a baseline request (before/after a deploy), include a content diff:

```bash
fabra context pack <context_id_B> --baseline <context_id_A> -o incident.zip
```

`incident.zip` contains `context.json`, `summary.md`, and (when `--baseline` is provided) `diff.patch`.

For audit-grade, self-verifiable export bundles, use:

```bash
fabra context export <context_id> --bundle
```

Use this when you need evidence to live outside the running service (support, compliance, chargebacks).

## Storage note (durability by default)

By default, dev installs store Context Records durably in DuckDB:

- `~/.fabra/fabra.duckdb`

Override:

- `FABRA_DUCKDB_PATH=/path/to/file.duckdb`
- `FABRA_DUCKDB_PATH=:memory:` (ephemeral, not recommended for incident workflows)
