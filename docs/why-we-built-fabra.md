---
title: "Why We Built Fabra: Record What Your AI Saw"
description: "The story behind Fabra. Why we built context infrastructure that creates replayable Context Records for every AI decision."
keywords: why fabra, context record, ai audit trail, replay ai decisions, debug ai, context infrastructure
---

# Why We Built Fabra

**What did your AI know when it decided?**

That's the question that started Fabra.

We watched teams deploy AI systems with no way to answer basic questions: What features did the model see? Which documents were retrieved? What got dropped due to token limits? Why did it make *that* decision?

When something went wrong — a bad recommendation, a rejected loan, a hallucinated answer — they couldn't debug it. They couldn't replay it. They couldn't prove what happened.

We built Fabra to fix this.

## The Problem: AI Without a Receipt

Every financial transaction creates a receipt. Every database query creates a log. But AI decisions? They vanish into thin air.

Most AI tooling is **read-only**:

- **LangChain** orchestrates calls but doesn't record what data was used
- **Pinecone** stores vectors but doesn't track what was retrieved when
- **Feature stores** cache values but don't capture the full decision context

When regulators ask "what did your AI know when it made this decision?", these tools have no answer. They never saw the complete picture — they just passed pieces through.

## The Solution: Context Records

Fabra creates a **Context Record** for every AI decision — an immutable snapshot of:

- **What features were used** (with exact values and freshness)
- **What documents were retrieved** (with similarity scores)
- **What got dropped** (due to token limits, with reasons)
- **Cryptographic proof** that the record is authentic

```python
ctx = await chat_context("user_123", "can I get a refund?")

print(ctx.id)        # ctx_018f3a2b-... (your receipt)
print(ctx.lineage)   # Complete data provenance
```

That `ctx.id` is permanent. Weeks later, you can:

```bash
# See exactly what the AI knew
fabra context show ctx_018f3a2b-...

# Verify the record is authentic
fabra context verify ctx_018f3a2b-...

# Compare two decisions side-by-side
fabra context diff ctx_a ctx_b
```

**This is the difference between "we think it worked" and "here's the proof."**

## Why "Own the Write Path"?

The key insight: **you can't record what you don't control.**

Read-only wrappers sit between your app and external databases. They see queries and responses, but they don't manage the data lifecycle. They can't guarantee what was fresh. They can't capture what was dropped. They can't enable replay.

Fabra **owns the write path**:

- **Ingest:** We store your documents and features (not just query them)
- **Index:** We manage embeddings with freshness timestamps
- **Track:** Every context assembly is logged with full lineage
- **Replay:** Reproduce exactly what your AI knew at any point

When you own the data lifecycle, you can create perfect records. When you have perfect records, you can debug anything.

## Who We Built This For

### ML Engineers

You're building fraud detection, recommendations, or risk models. You need:

- Features served without Kubernetes complexity
- Point-in-time correctness for training data
- Proof of what data your model saw for each prediction

**Fabra gives you:** `@feature` decorators that create audit trails automatically.

### AI Engineers

You're building RAG chatbots, AI agents, or LLM applications. You need:

- Vector search with retrieval tracking
- Token budget management that logs what got dropped
- Compliance evidence for regulated industries

**Fabra gives you:** `@context` decorators that create replayable Context Records.

## The Honest Comparison

| Capability | **Fabra** | **LangChain** | **Feast** |
|:-----------|:----------|:--------------|:----------|
| **Records what AI saw** | Full Context Record | No | Partial (features only) |
| **Tracks dropped items** | Yes, with reasons | No | No |
| **Replay decisions** | Built-in CLI | Manual | No |
| **Verify integrity** | Cryptographic hash | No | No |
| **Setup time** | 30 seconds | Minutes | Days/Weeks |
| **Infrastructure** | None required | None required | Kubernetes |

We're not trying to replace everything. LangChain is great for orchestration. Feast is great for enterprises with platform teams.

Fabra is for teams who need to **prove what their AI knew**.

## What We Don't Do

Fabra is focused. We don't do:

- **Agent orchestration** — Use LangChain, CrewAI
- **Workflow scheduling** — Use Airflow, Prefect
- **Model serving** — Use vLLM, TensorRT
- **High-QPS streaming** — Use Tecton, Feathr

We do one thing: **create replayable records of AI decisions**.

## The 30-Second Test

```bash
pip install fabra-ai
fabra demo
```

That's it. No Docker. No Kubernetes. No API keys.

You'll see a Context Record created, stored, and queryable. If that's useful, keep going. If not, no hard feelings.

## Join Us

If you believe AI decisions should be auditable, debuggable, and replayable — we built Fabra for you.

[Get Started →](quickstart.md)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Why We Built Fabra: Record What Your AI Saw",
  "description": "The story behind Fabra. Why we built context infrastructure that creates replayable Context Records for every AI decision.",
  "author": {"@type": "Organization", "name": "Fabra Team"},
  "keywords": "why fabra, context record, ai audit trail, replay ai decisions",
  "articleSection": "About"
}
</script>
