---
title: "Fabra Philosophy: Record What Your AI Saw"
description: "Why we built Fabra around Context Records. The philosophy behind making AI decisions replayable, debuggable, and auditable."
keywords: fabra philosophy, context record, ai audit trail, replay ai decisions, debug ai, context infrastructure, write path ownership
---

# Philosophy

We built Fabra because we believe every AI decision should produce an artifact you can replay and debug.

Not a log. Not a trace. A **Context Record** — an immutable snapshot of exactly what data your AI used, where it came from, what got dropped, and why.

## The Problem We Saw

When an AI makes a bad decision, teams scramble to answer basic questions:

- What features did the model see?
- Which documents were retrieved?
- Were any of them stale?
- What got dropped due to token limits?
- Can we reproduce this exact decision?

Most AI tooling can't answer these questions because they don't own the data. LangChain queries your vector DB. Orchestration frameworks call your APIs. They pass data through — they don't record it.

**You can't debug what you didn't capture. You can't audit what you don't own.**

## The Context Record Principle

Fabra is built around a single principle: **every context assembly produces an immutable record**.

```python
ctx = await chat_context("user_123", "how do I get a refund?")

print(ctx.id)        # ctx_018f3a2b-... (stable ID)
print(ctx.lineage)   # Exactly what data was used
```

That `ctx.id` is your receipt. Days, weeks, or months later, you can:

```bash
# See exactly what the AI knew
fabra context show ctx_018f3a2b-...

# Verify the record hasn't been tampered with
fabra context verify ctx_018f3a2b-...

# Compare two decisions
fabra context diff ctx_a ctx_b
```

This is the difference between "we think it saw these documents" and "here is cryptographic proof of exactly what it saw."

## Why "Own the Write Path"?

Most AI tools are read-only wrappers. They query databases but don't manage the data lifecycle.

Fabra **owns the write path**:

| Capability | Read-Only Tools | Fabra |
|:-----------|:----------------|:------|
| Ingest documents | Pass-through | Stores with timestamps |
| Track freshness | No visibility | SLAs with violations logged |
| Log what was retrieved | Maybe, inconsistently | Every item, every time |
| Record what was dropped | Never | Full list with reasons |
| Replay decisions | Impossible | Built-in |

When you own the write path, you control the data lifecycle. When you control the lifecycle, you can record everything. When you record everything, you can replay and debug.

## Trade-offs We Made

### Simplicity Over Scale

Fabra runs on your laptop with `pip install`. No Kubernetes. No Spark. No Docker required for development.

This means we're not optimized for Google-scale problems. If you need sub-millisecond streaming at millions of QPS, use Tecton. If you need to serve features without infrastructure complexity and want full audit trails, use Fabra.

### Records Over Performance

We prioritize complete Context Records over micro-optimizations. Every context assembly logs:

- All features accessed (with freshness)
- All documents retrieved (with similarity scores)
- All items dropped (with reasons)
- Assembly latency and token usage

This adds overhead. We think it's worth it. The first time you debug a production AI issue by replaying the exact context, you'll agree.

### Explicit Over Magic

No auto-caching. No query optimization. No hidden materialization.

You write `@feature`, we compute and cache it. You write `@context`, we assemble and record it. What you see is what happens.

Predictability matters more than cleverness when you're debugging at 2am.

## Who Fabra Is For

**You should use Fabra if:**

- You need to prove what your AI knew when it decided
- You want to replay and debug AI decisions
- You're in a regulated industry (fintech, healthcare, legal)
- You value "works on my laptop" over "scales to exabytes"
- You want features and RAG from one system, not five

**You should NOT use Fabra if:**

- You need sub-millisecond streaming inference
- You have a dedicated platform team for Kubernetes
- You don't care about audit trails
- You're optimizing for maximum QPS, not debuggability

## The Honest Truth

We didn't start by building Fabra. We spent weeks trying to use existing tools. We fought with Kubernetes manifests, registry sync issues, and infrastructure complexity.

Then we asked: "What if we just recorded everything the AI saw?"

That question led to Context Records. Context Records led to Fabra.

**Once context is a ledger, everything else follows.**

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "TechArticle",
  "headline": "Fabra Philosophy: Record What Your AI Saw",
  "description": "Why we built Fabra around Context Records. The philosophy behind making AI decisions replayable, debuggable, and auditable.",
  "author": {"@type": "Organization", "name": "Fabra Team"},
  "keywords": "fabra philosophy, context record, ai audit trail, replay ai decisions",
  "articleSection": "Philosophy"
}
</script>
