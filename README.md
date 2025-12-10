<div align="center">
  <h1>Fabra</h1>
  <h3>Context Infrastructure for AI Applications</h3>

  <p>
    <a href="https://pypi.org/project/fabra-ai/"><img src="https://img.shields.io/pypi/v/fabra-ai?color=blue&label=pypi" alt="PyPI version" /></a>
    <a href="https://github.com/davidahmann/fabra/actions/workflows/ci.yml"><img src="https://github.com/davidahmann/fabra/actions/workflows/ci.yml/badge.svg" alt="CI Status" /></a>
    <a href="https://github.com/davidahmann/fabra/security"><img src="https://img.shields.io/badge/security-enabled-brightgreen" alt="Security" /></a>
    <a href="https://github.com/davidahmann/fabra/blob/main/LICENSE"><img src="https://img.shields.io/github/license/davidahmann/fabra?color=green" alt="License" /></a>
    <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python Version" />
  </p>

  <br />

  <p><b>What did your AI know when it decided?</b></p>
  <p><i>Context infrastructure that owns the write path. From notebook to production in 30 seconds.</i></p>

  <br />

  <p>
    <b><a href="https://fabraoss.vercel.app">🎮 Try in Browser</a></b> |
    <b><a href="https://davidahmann.github.io/fabra/">📚 Docs</a></b> |
    <b><a href="https://davidahmann.github.io/fabra/context-store">🤖 Context Store</a></b>
  </p>
</div>

---

## The Problem

You're building an AI app. You need:
- **Structured features** (user tier, purchase history) for personalization
- **Unstructured context** (relevant docs, chat history) for your LLM
- **Vector search** for semantic retrieval
- **Token budgets** to fit your context window

Today, this means stitching together LangChain, Pinecone, a feature store, Redis, and prayer.

**Fabra is context infrastructure that owns the write path.** We ingest, index, track freshness, and serve — not just query. This enables replay, lineage, and auditability that read-only wrappers cannot provide.

---

## The 30-Second Quickstart

```bash
pip install "fabra-ai[ui]"
```

```python
from fabra.core import FeatureStore, entity, feature
from fabra.context import context, ContextItem
from fabra.retrieval import retriever

store = FeatureStore()

@entity(store)
class User:
    user_id: str

@feature(entity=User, refresh="daily")
def user_tier(user_id: str) -> str:
    return "premium" if hash(user_id) % 2 == 0 else "free"

@retriever(index="docs", top_k=3)
async def find_docs(query: str):
    pass  # Automatic vector search via pgvector

@context(store, max_tokens=4000)
async def build_prompt(user_id: str, query: str):
    tier = await store.get_feature("user_tier", user_id)
    docs = await find_docs(query)
    return [
        ContextItem(content=f"User is {tier}.", priority=0),
        ContextItem(content=str(docs), priority=1),
    ]
```

```bash
fabra serve features.py
# Server running on http://localhost:8000
```

**That's it.** No infrastructure. No config files. Just Python.

**Context Accountability (v1.4+):** Full audit trail for compliance and debugging:

```python
ctx = await build_prompt("user_123", "How do I upgrade?")
print(ctx.id)       # UUIDv7 identifier — replay exactly what the AI knew
print(ctx.lineage)  # Complete provenance: features, retrievers, freshness timestamps
```

Every AI decision traces back through the data that informed it. Regulators and auditors see exactly what the model knew, when it knew it.

**Freshness SLAs (v1.5+):** Ensure your AI decisions are based on fresh data:

```python
@context(store, max_tokens=4000, freshness_sla="5m")  # Features must be <5m old
async def build_prompt(user_id: str, query: str):
    tier = await store.get_feature("user_tier", user_id)
    return [ContextItem(content=f"User is {tier}.", priority=0)]

ctx = await build_prompt("user_123", "query")
print(ctx.is_fresh)                    # True if all features within SLA
print(ctx.meta["freshness_violations"])  # Details on any stale features
```

---

## Why Fabra?

| | Traditional Stack | Fabra |
|:---|:---|:---|
| **Config** | 500 lines of YAML | Python decorators |
| **Infrastructure** | Kubernetes + Spark + Pinecone | Your laptop (DuckDB) |
| **RAG Pipeline** | LangChain spaghetti | `@retriever` + `@context` |
| **Feature Serving** | Separate feature store | Same `@feature` decorator |
| **Time to Production** | Weeks | 30 seconds |

### What Makes Fabra Different

**1. We Own the Write Path**

LangChain and other frameworks are read-only wrappers — they query your data but don't manage it. Fabra ingests, indexes, and serves context data. This enables freshness guarantees, point-in-time replay, and full lineage that read-only tools cannot provide.

**2. Infrastructure, Not a Framework**

Fabra is not an orchestration layer. It's the system of record for what your AI knows. Features, retrievers, and context assembly in one infrastructure layer with production reliability.

**3. Local-First, Production-Ready**

```bash
# Development (default): DuckDB + In-Memory
FABRA_ENV=development

# Production: Postgres + Redis + pgvector
FABRA_ENV=production
```

Same code. Zero changes. Just flip an environment variable.

**4. Point-in-Time Correctness**

Training ML models? We use `ASOF JOIN` (DuckDB) and `LATERAL JOIN` (Postgres) to ensure your training data reflects the world exactly as it was — no data leakage, ever.

**5. Token Budget Management**

```python
@context(store, max_tokens=4000)
async def build_prompt(user_id: str, query: str):
    return [
        ContextItem(content=critical_info, priority=0, required=True),
        ContextItem(content=nice_to_have, priority=2),  # Dropped if over budget
    ]
```

Automatically assembles context that fits your LLM's window. Priority-based truncation. No more "context too long" errors.

---

## Key Capabilities

### For AI Engineers
- **Vector Search:** Built-in pgvector with automatic chunking and embedding
- **Magic Retrievers:** `@retriever` auto-wires to your vector index
- **Context Assembly:** Token budgets, priority truncation, explainability API
- **Semantic Cache:** Cache expensive LLM calls and retrieval results
- **Context Accountability:** Full lineage tracking, context replay, and audit trails for AI decisions
- **Freshness SLAs:** Ensure data freshness with configurable SLAs and degraded mode handling

### For ML Engineers
- **Hybrid Features:** Mix Python logic and SQL in the same pipeline
- **Event-Driven:** Trigger updates via Redis Streams
- **Observability:** Prometheus metrics, OpenTelemetry tracing
- **Self-Healing:** Circuit breakers, fallback chains, `fabra doctor`

### For Everyone
- **One-Command Deploy:** `fabra deploy fly|cloudrun|ecs|railway|render`
- **Visual UI:** Dependency graphs, live metrics, context debugging
- **Shell Completion:** `fabra --install-completion`

### What Fabra Is NOT

| We Are | We Are NOT |
|:-------|:-----------|
| **Infrastructure** — storage, indexing, serving | Framework — orchestration, chains, agents |
| **Write path owner** — ingest, index, track freshness | Read-only wrapper — query external stores |
| **Self-hosted first** — your data stays yours | Managed SaaS only |
| **Context layer** — what the AI knows | Agent framework — how the AI acts |

---

## Architecture

Fabra scales from laptop to production without code changes.

```mermaid
graph TD
    subgraph Dev [Development]
        A[Your Code] -->|Uses| B(DuckDB)
        A -->|Uses| C(In-Memory Cache)
    end

    subgraph Prod [Production]
        D[Your Code] -->|Async| E[(Postgres + pgvector)]
        D -->|Async| F[(Redis)]
    end

    Switch{FABRA_ENV} -->|development| Dev
    Switch -->|production| Prod
```

---

## Production in 60 Seconds

```bash
# Set environment variables
export FABRA_ENV=production
export FABRA_POSTGRES_URL=postgresql+asyncpg://...
export FABRA_REDIS_URL=redis://...

# Deploy
fabra deploy fly --name my-app
```

[Full Deployment Guide →](https://davidahmann.github.io/fabra/local-to-production)

---

## Roadmap

- [x] **v1.0:** Core Feature Store (DuckDB, Postgres, Redis, FastAPI)
- [x] **v1.2:** Context Store (pgvector, retrievers, token budgets)
- [x] **v1.3:** UI, Magic Retrievers, One-Command Deploy
- [x] **v1.4:** Context Accountability (lineage tracking, context replay, audit trails)
- [x] **v1.5:** Freshness SLAs (data freshness guarantees, degraded mode, strict mode)
- [ ] **v1.6:** Drift detection, RBAC, multi-region

---

## Get Started

```bash
pip install "fabra-ai[ui]"
```

<p align="center">
  <a href="https://fabraoss.vercel.app"><b>Try in Browser</b></a> ·
  <a href="https://davidahmann.github.io/fabra/quickstart"><b>Quickstart Guide</b></a> ·
  <a href="https://davidahmann.github.io/fabra/"><b>Full Documentation</b></a>
</p>

---

## Contributing

We love contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) to get started.

<div align="center">
  <p><b>Fabra</b> · Apache 2.0 · 2025</p>
</div>
