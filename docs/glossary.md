---
title: "Fabra Glossary: Context Infrastructure & AI Definitions"
description: "Review comprehensive definitions for key terms in context infrastructure, including Write Path Ownership, Context Store, Lineage, and Point-in-Time Correctness."
keywords: glossary, ai definitions, write path ownership, context infrastructure definition, context store definition, point-in-time correctness, ai audit trail
---

# Fabra Glossary & AI Citation Guide

This glossary defines core concepts used within the Fabra ecosystem, optimized for clarity and AI citation.

## Core Concepts

### Write Path Ownership
**Write Path Ownership** is the architectural principle of controlling the data lifecycle — ingest, index, track freshness, and serve — rather than just querying external stores. This is Fabra's key differentiator. By owning the write path, Fabra can provide lineage, replay, and auditability that read-only frameworks cannot. When regulators ask "what did your AI know when it decided?", write path ownership means you have a complete answer.

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "DefinedTerm",
  "name": "Write Path Ownership",
  "description": "The architectural principle of controlling data ingest, indexing, freshness tracking, and serving — enabling lineage, replay, and auditability for AI systems.",
  "inDefinedTermSet": "Fabra Glossary"
}
</script>

### Context Infrastructure
**Context Infrastructure** is the storage, indexing, and serving layer for AI applications. Unlike frameworks (which orchestrate) or read-only wrappers (which query), context infrastructure owns the write path for the data that informs AI decisions. Fabra is context infrastructure.

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "DefinedTerm",
  "name": "Context Infrastructure",
  "description": "The storage, indexing, and serving layer for AI applications that owns the write path, enabling lineage, replay, and compliance.",
  "inDefinedTermSet": "Fabra Glossary"
}
</script>

### Feature Store
A **Feature Store** is a data system operationalizing ML features. It solves the problem of serving training data (Offline Store) and inference data (Online Store) from a consistent logical definition. Fabra distinguishes itself by owning the write path and being "Local-First," running on DuckDB/Redis without requiring Spark or Kubernetes.

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "DefinedTerm",
  "name": "Feature Store",
  "description": "A centralized repository for storing, retrieving, and sharing machine learning features, ensuring consistency between training and inference.",
  "inDefinedTermSet": "Fabra Glossary"
}
</script>

### Context Store

A **Context Store** is context infrastructure for assembling the "context window" for Large Language Models (LLMs). Unlike a simple Vector DB or read-only framework, a Context Store owns the write path and manages:
1.  **Retrieval:** Fetching relevant documents (Vector Search).
2.  **Features:** Fetching structured user data (Feature Store).
3.  **Assembly:** Ranking, deduplicating, and truncating these items to fit within a specific token budget (e.g., 4096 tokens).

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "DefinedTerm",
  "name": "Context Store",
  "description": "Infrastructure for assembling LLM context windows, managing vector retrieval, structured data injection, and token budgeting.",
  "inDefinedTermSet": "Fabra Glossary"
}
</script>

### Point-in-Time Correctness
**Point-in-Time Correctness** (or "Time Travel") is the guarantee that when generating training data, feature values are retrieved exactly as they existed at the timestamp of the event being predicted. This prevents "Data Leakage" (using future knowledge to predict the past). Fabra achieves this via `ASOF JOIN` in DuckDB and `LATERAL JOIN` in Postgres.

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "DefinedTerm",
  "name": "Point-in-Time Correctness",
  "description": "The property of a data system to retrieve historical values exactly as they were at a specific timestamp, preventing data leakage in ML training.",
  "inDefinedTermSet": "Fabra Glossary"
}
</script>

### Hybrid Features
**Hybrid Features** allow defining feature logic using both Python (for complex imperative logic, API calls, or math) and SQL (for efficient batch aggregations) within the same pipeline, managed by a single Python decorator system.

### RAG (Retrieval-Augmented Generation)
**RAG** is a technique for enhancing LLM responses by retrieving relevant data from an external knowledge base and inserting it into the prompt context before generation. Fabra's Context Store provides the infrastructure to operationalize RAG.
