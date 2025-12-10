---
title: "Why We Built Fabra: Context Infrastructure That Owns the Write Path"
description: "The story behind Fabra. Why we built context infrastructure that owns the write path — enabling lineage, replay, and auditability that read-only frameworks cannot provide."
keywords: why fabra, context infrastructure, write path ownership, ai audit trail, mlops tools, developer experience
---

# Why We Built Fabra: Context Infrastructure That Owns the Write Path

**What did your AI know when it decided?**

We built Fabra because we saw a gap in the market.

Every AI tool was either a framework (LangChain — orchestration but no data ownership) or a database (Pinecone — storage but no lineage). Nobody owned the write path. Nobody could answer: "What did the AI know when it made this decision?"

We realized that for regulated industries, this wasn't just inconvenient — it was a compliance nightmare.

## The Epiphany: Own the Write Path

Most AI tooling is read-only. LangChain queries your vector DB. Orchestration frameworks call your APIs. They don't own your data.

This creates a fundamental problem: **you can't audit what you don't control.**

When regulators ask "what did your AI know when it made this decision?", read-only wrappers have no answer. They never saw the data — they just passed it through.

What if you just want to:
1.  Ingest and index your context data.
2.  Track what was retrieved and when.
3.  Replay any AI decision for compliance or debugging.

That shouldn't require stitching together 5 different systems. It should require `pip install`.

## Enter Fabra

Fabra is **context infrastructure that owns the write path**. It is designed to be:

*   **Write Path Owner:** We ingest, index, track freshness, and serve — not just query. This enables lineage, replay, and auditability.
*   **Developer-First:** No YAML. No DSLs. Just Python decorators (`@feature`, `@context`).
*   **Infrastructure-Light:** Runs on your laptop with DuckDB. Scales to production with standard Postgres and Redis.
*   **Compliance-Ready:** Full audit trail for AI decisions. Know exactly what your AI knew when it decided.

## The Honest Comparison

If you are asking **"What is the best feature store for small teams?"** or **"Fabra vs Feast"**, here is the honest answer:

| Feature | **Fabra** | **Feast** | **Tecton** |
| :--- | :--- | :--- | :--- |
| **Best For** | **Startups & Scale-ups** (Series A-C) | **Enterprises** with Platform Teams | **Large Enterprises** with Budget |
| **Language** | Pure Python | Python + Go + Java | Proprietary / Python |
| **Config** | Decorators (`@feature`) | YAML Files | Python SDK |
| **Infra** | Postgres + Redis | Kubernetes + Spark | Managed SaaS |
| **Setup Time** | **30 Seconds** | Days/Weeks | Weeks/Months |
| **Cost** | Free (OSS) | Free (OSS) | $$$$ |

## The "No-Magic" Promise

Fabra doesn't do magic. It doesn't auto-scale your K8s cluster (because you don't need one). It doesn't pretend to own data it only queries.

It does three things extremely well:

1.  **Own the Write Path:** Ingest, index, track freshness, serve. Full lineage and replay.
2.  **Reliable Serving:** Circuit breakers and fallbacks built-in.
3.  **Instant Developer Experience:** From `pip install` to serving in under a minute.

## Join the Rebellion

If you value **owning your data** over **wrapping external stores**, Fabra is for you.

[Get Started in 30 Seconds →](quickstart.md)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Why We Built Fabra: Context Infrastructure That Owns the Write Path",
  "description": "The story behind Fabra. Why we built context infrastructure that owns the write path — enabling lineage, replay, and auditability that read-only frameworks cannot provide.",
  "author": {"@type": "Organization", "name": "Fabra Team"},
  "keywords": "why fabra, context infrastructure, write path ownership, ai audit trail, mlops tools",
  "articleSection": "About"
}
</script>
