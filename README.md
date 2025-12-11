<div align="center">
  <h1>Fabra</h1>
  <p><strong>The feature store that runs on your laptop.<br/>The context store that knows what your AI knew.</strong></p>

  <p>
    <a href="https://pypi.org/project/fabra-ai/"><img src="https://img.shields.io/pypi/v/fabra-ai?color=blue&label=pypi" alt="PyPI version" /></a>
    <a href="https://github.com/davidahmann/fabra/blob/main/LICENSE"><img src="https://img.shields.io/github/license/davidahmann/fabra?color=green" alt="License" /></a>
    <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python Version" />
  </p>
</div>

---

## The Problem

**ML Engineers:** Feast needs Kubernetes and Spark. You have a 4-person team and a deadline.

**AI Engineers:** Legal asked what data your AI used for a decision last Tuesday. You had no answer.

Both problems have the same root cause: **you don't own your data pipeline**.

---

## 30 Seconds to Proof

```bash
pip install fabra-ai && fabra demo
```

That's it. Server starts, makes a test request, shows you the result. No Docker. No config files. No API keys.

<details>
<summary><strong>What you'll see</strong></summary>

```
  Fabra Demo Server

  Testing feature retrieval...
  curl localhost:8000/features/user_engagement?entity_id=user_123

  Response:
  {
    "value": 87.5,
    "freshness_ms": 0,
    "served_from": "online"
  }

  Press Ctrl+C to stop, or visit http://localhost:8000/docs
```

</details>

---

## Two Entry Points, One Infrastructure

<table>
<tr>
<td width="50%" valign="top">

### For ML Engineers

**"I need features in production, not a platform team."**

```python
from fabra import FeatureStore, entity, feature
from datetime import timedelta

store = FeatureStore()

@entity(store)
class User:
    user_id: str

@feature(entity=User, refresh=timedelta(hours=1))
def purchase_count(user_id: str) -> int:
    return db.query(
        "SELECT COUNT(*) FROM purchases WHERE user_id = ?",
        user_id
    )
```

```bash
fabra serve features.py
curl localhost:8000/features/purchase_count?entity_id=u123
# {"value": 47, "freshness_ms": 0, "served_from": "online"}
```

**Python decorators. Not YAML.**

</td>
<td width="50%" valign="top">

### For AI Engineers

**"Compliance asked what the AI knew. I need an answer."**

```python
from fabra import FeatureStore
from fabra.context import context, ContextItem

store = FeatureStore()

@context(store, max_tokens=4000, freshness_sla="5m")
async def build_prompt(user_id: str, query: str):
    tier = await store.get_feature("user_tier", user_id)
    docs = await search_docs(query)
    return [
        ContextItem(content=f"User tier: {tier}", priority=1),
        ContextItem(content=docs, priority=2),
    ]

ctx = await build_prompt("user_123", "question")
print(ctx.id)       # ctx_018f3a2b-... (replay this anytime)
print(ctx.lineage)  # exactly what data was used
```

**Full audit trail. Not a black box.**

</td>
</tr>
</table>

---

## Why It Works

### 1. You Own Your Data

LangChain queries your vector DB. Fabra *is* your vector DB. We ingest, index, track freshness, and serve. When someone asks "what did the AI know?", we have the answer because we never lost sight of the data.

```bash
# Replay any historical context
fabra context show ctx_018f3a2b-7def-7abc-8901-234567890abc

# Compare what changed between two decisions
fabra context diff ctx_abc123 ctx_def456
```

### 2. Same Code Everywhere

Development uses DuckDB (zero setup). Production uses Postgres + Redis (just add env vars). Your feature definitions don't change.

```bash
# Development (right now, on your laptop)
fabra serve features.py

# Production (same code, different backends)
FABRA_ENV=production \
FABRA_POSTGRES_URL=postgresql://... \
FABRA_REDIS_URL=redis://... \
fabra serve features.py
```

### 3. Point-in-Time Correctness

Training ML models? We use `ASOF JOIN` to ensure your training data reflects exactly what the model would have seen at prediction time. No data leakage. No training-serving skew.

### 4. Token Budgets That Work

No more prompt length errors in production. Set a budget, assign priorities, and low-priority items get dropped automatically.

```python
@context(store, max_tokens=4000)
async def build_prompt(user_id: str, query: str):
    return [
        ContextItem(content=system_prompt, priority=0, required=True),
        ContextItem(content=user_history, priority=1),  # dropped first if over budget
        ContextItem(content=docs, priority=2),
    ]
```

---

## What's Real

This isn't a framework that wraps other tools. This is infrastructure:

| Capability | What It Does |
|:-----------|:-------------|
| **Feature Store** | `@feature` decorators, online/offline stores, point-in-time joins |
| **Context Store** | `@context` decorators, token budgeting, lineage tracking |
| **Vector Search** | Built-in pgvector, automatic chunking, freshness tracking |
| **Context Replay** | `fabra context show <id>` returns exact historical state |
| **Context Diff** | `fabra context diff <id1> <id2>` shows what changed |
| **Freshness SLAs** | `freshness_sla="5m"` fails if data is stale |
| **Diagnostics** | `fabra doctor` validates your setup |

### CLI

```bash
fabra serve features.py      # Start the server
fabra demo                   # Interactive demo (no setup)
fabra doctor                 # Diagnose configuration issues
fabra context show <id>      # Replay historical context
fabra context diff <a> <b>   # Compare two contexts
fabra context list           # List recent contexts
fabra context export <id>    # Export for audit
fabra deploy fly|railway     # Generate deployment config
fabra ui features.py         # Launch the dashboard (requires [ui] extra)
```

> **Note:** `fabra ui` requires `pip install "fabra-ai[ui]"` for Streamlit dependencies.

---

## Honest Comparison

### vs Feast

| | Feast | Fabra |
|:---|:---|:---|
| Setup | Kubernetes + Spark | `pip install` |
| Config | YAML files | Python decorators |
| Local dev | Docker required | Works immediately |
| Context/RAG | Not supported | Built-in |

**Choose Feast if:** You have a platform team and existing K8s infrastructure.

### vs LangChain

| | LangChain | Fabra |
|:---|:---|:---|
| Architecture | Orchestration framework | Storage + serving infrastructure |
| Data ownership | Queries external stores | Owns the write path |
| Audit trail | None | Full lineage + replay |
| Token management | DIY | Built-in budgets |

**Choose LangChain if:** You need agent chains and don't need compliance.

---

## Production Checklist

- [x] **Observability:** Prometheus metrics at `/metrics`, structured logging
- [x] **Reliability:** Circuit breakers, fallback chains, health checks
- [x] **Security:** Self-hosted, your data stays in your infrastructure
- [x] **Deployment:** One-command deploy to Fly.io, Railway, Cloud Run, Render

---

## Quick Start (Detailed)

### Feature Store

```bash
pip install fabra-ai
fabra serve examples/demo_features.py
```

Test it:
```bash
curl localhost:8000/features/user_engagement?entity_id=user_123
```

Response:
```json
{"value": 87.5, "freshness_ms": 0, "served_from": "online"}
```

### Context Store

```bash
pip install fabra-ai
fabra serve examples/demo_context.py
```

Test it:
```bash
curl -X POST localhost:8000/v1/context/chat_context \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user_123","query":"how do features work?"}'
```

Response:
```json
{
  "id": "ctx_018f3a2b-...",
  "content": "You are a helpful AI assistant...",
  "meta": {
    "freshness_status": "guaranteed",
    "token_usage": 150
  },
  "lineage": {
    "features_used": ["user_tier", "user_engagement_score"],
    "retrievers_used": ["demo_docs"]
  }
}
```

Replay it later:
```bash
fabra context show ctx_018f3a2b-...
```

---

## What We Don't Do

- **100k+ QPS streaming** - Use Tecton
- **Agent orchestration** - Use LangChain
- **50+ SaaS connectors** - Not our focus
- **No-code builders** - This is Python infrastructure

---

<p align="center">
  <a href="https://fabraoss.vercel.app"><strong>Try in Browser</strong></a> ·
  <a href="https://davidahmann.github.io/fabra/docs/quickstart"><strong>Quickstart</strong></a> ·
  <a href="https://davidahmann.github.io/fabra/docs/"><strong>Docs</strong></a>
</p>

---

<div align="center">
  <p><strong>Fabra</strong> · Apache 2.0 · 2025</p>
  <p><em>Context infrastructure that owns the write path.</em></p>
</div>
