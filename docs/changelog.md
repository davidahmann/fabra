---
title: "Meridian Changelog: Release Notes and History"
description: "Stay up to date with Meridian releases. See what's new in v1.2.0 with Context Store for LLMs, and v1.1.0 with Hybrid Features and Point-in-Time Correctness."
keywords: meridian changelog, release notes, feature store updates, context store, rag updates, software version history
---

# Changelog

All notable changes to this project will be documented in this file.

## [v1.2.0] - 2025-12-07

### 🚀 Major Features: Context Store for LLMs

*   **Context Store:** Full RAG infrastructure for LLM applications.
    *   `@retriever` decorator for semantic search with automatic caching.
    *   `@context` decorator for composing context with token budgets.
    *   Priority-based truncation with `ContextItem(priority=N, required=True/False)`.
*   **Vector Search:**
    *   pgvector integration for Postgres with cosine similarity.
    *   Automatic document chunking via tiktoken.
    *   Multiple embedding providers (OpenAI, Cohere).
*   **Event-Driven Architecture:**
    *   `AxiomEvent` model for structured events.
    *   `RedisEventBus` for publishing to Redis Streams.
    *   `AxiomWorker` for consuming events and triggering feature updates.
    *   Trigger-based features with `@feature(trigger="event_name")`.
*   **DAG Resolution:**
    *   Implicit wiring via `{feature_name}` template syntax.
    *   `DependencyResolver` for automatic dependency graph construction.
*   **Observability:**
    *   `ContextTrace` model for debugging context assembly.
    *   `/context/{id}/explain` API endpoint.
    *   `ContextMetrics` for Prometheus integration.
*   **Time Travel:**
    *   `get_historical_features()` for point-in-time queries.
    *   Debug production issues by querying past state.
*   **Diagnostics:**
    *   `meridian doctor` CLI command for environment diagnostics.
    *   Checks Redis, Postgres, and environment variable configuration.

### 🐛 Bug Fixes

*   Fixed timing-safe API key comparison (now uses `secrets.compare_digest`).
*   Fixed Docker container running as root (now uses non-root user).
*   Fixed environment variable mismatch in docker-compose.yml.
*   Added HEALTHCHECK to Dockerfile.

### 📚 Documentation

*   Added [Context Store Overview](context-store.md) page.
*   Added [Retrievers](retrievers.md) page.
*   Added [Context Assembly](context-assembly.md) page.
*   Added [Event-Driven Features](event-driven-features.md) page.
*   Added [RAG Chatbot Use Case](use-cases/rag-chatbot.md).
*   Updated Architecture page with Context Store diagrams.

---

## [v1.1.0] - 2025-12-05

### 🚀 Major Features

*   **Production Stack (`MERIDIAN_ENV=production`)**: full support for running in production with Postgres (Async) and Redis.
*   **Point-in-Time Correctness**:
    *   Development: Uses DuckDB `ASOF JOIN` logic for zero leakage.
    *   Production: Uses Postgres `LATERAL JOIN` logic for zero leakage.
*   **Async Offline Store**: `PostgresOfflineStore` now uses `asyncpg` for high-throughput I/O.
*   **Hybrid Feature Fixes**: Correctly merges Python (on-the-fly) and SQL (batch) features in retrieval.

### 🐛 Bug Fixes

*   Fixed `AttributeError` in `prod_app.py` regarding `timedelta`.
*   Fixed data loss issue in `PostgresOfflineStore` where Python features were dropped during hybrid retrieval.
*   Fixed type casting issues in `RedisOnlineStore`.

### 📚 Documentation

*   Added [Feast Comparison](feast-alternative.md) page.
*   Added [FAQ](faq.md) page.
*   Added Use Case guides:
    *   [Churn Prediction](use-cases/churn-prediction.md) (PIT Focus)
    *   [Real-Time Recommendations](use-cases/real-time-recommendations.md) (Hybrid Focus)
*   Added Architecture Diagram to README.

## [v1.0.2] - 2025-12-04

### Added
*   Initial support for Hybrid Features (Python + SQL).
