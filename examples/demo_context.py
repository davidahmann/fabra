"""
Fabra Demo: Context assembly WITHOUT requiring API keys.

This demonstrates:
- Context assembly with full lineage tracking
- Token budgeting and priority-based item dropping
- Freshness SLA enforcement
- Mock retriever (no external API needed)

Run:
    fabra serve examples/demo_context.py

Test:
    curl -X POST localhost:8000/v1/context/chat_context \
      -H "Content-Type: application/json" \
      -d '{"user_id":"user_123","query":"how do features work?"}'

Expected Response:
    {
      "id": "ctx_018f...",
      "content": "You are a helpful assistant...",
      "meta": {
        "freshness_status": "guaranteed",
        "token_usage": 150,
        "dropped_items": 0
      },
      "lineage": {
        "features_used": [...],
        "retrievers_used": [...]
      }
    }
"""

import hashlib
from datetime import timedelta
from typing import List

from fabra.core import FeatureStore, entity, feature
from fabra.context import context, ContextItem
from fabra.retrieval import retriever
from fabra.store import DuckDBOfflineStore, InMemoryOnlineStore

# Initialize the store with in-memory backends
store = FeatureStore(
    offline_store=DuckDBOfflineStore(),
    online_store=InMemoryOnlineStore(),
)


# --- Entity and Features ---


@entity(store)
class User:
    """User entity for personalization."""

    user_id: str


@feature(entity=User, refresh=timedelta(hours=1))
def user_tier(user_id: str) -> str:
    """Premium/free tier based on user ID."""
    return "premium" if hash(user_id) % 2 == 0 else "free"


@feature(entity=User, refresh=timedelta(minutes=5))
def user_engagement_score(user_id: str) -> float:
    """Engagement score (0-100) based on user ID hash."""
    h = int(hashlib.md5(user_id.encode()).hexdigest()[:8], 16)  # nosec
    return round((h % 10000) / 100, 2)


@feature(entity=User)
def support_priority(user_id: str) -> str:
    """Support ticket priority based on tier and engagement."""
    tier = user_tier(user_id)
    score = user_engagement_score(user_id)
    if tier == "premium" and score > 50:
        return "high"
    elif tier == "premium" or score > 70:
        return "medium"
    return "normal"


# --- Mock Retriever (No API Key Required) ---


# Simulated knowledge base
MOCK_DOCS = {
    "features": [
        "Features in Fabra are defined using the @feature decorator. Each feature is a Python function that computes a value for an entity.",
        "Features can be materialized to an online store for low-latency serving, or computed on-demand.",
        "The refresh parameter specifies how often a feature should be recomputed. Use timedelta for precise control.",
    ],
    "context": [
        "Context assembly in Fabra uses the @context decorator to combine features and retrieved data into prompts.",
        "Token budgeting automatically manages prompt length by dropping low-priority items when budget is exceeded.",
        "Every context assembly gets a unique UUID and full lineage tracking for debugging and audit.",
    ],
    "retrieval": [
        "Retrievers in Fabra fetch relevant documents for RAG pipelines. Use @retriever decorator to define them.",
        "Auto-wiring connects retrievers to vector indexes automatically when you specify index=...",
        "Retriever results are tracked in lineage including query, result count, and latency.",
    ],
    "default": [
        "Fabra is a feature store and context store for ML and AI applications.",
        "Use pip install fabra-ai to get started with Fabra.",
        "Check out the examples directory for more usage patterns.",
    ],
}


@retriever(name="demo_docs", cache_ttl=timedelta(seconds=300))
async def search_docs(query: str, top_k: int = 3) -> List[dict]:
    """
    Simulated document search - no API key required.

    In production, this would connect to a vector database.
    For demo purposes, we do keyword matching against mock docs.
    """
    import time

    start = time.time()

    # Simple keyword matching
    query_lower = query.lower()
    results = []

    # Check which topic matches best
    if "feature" in query_lower:
        docs = MOCK_DOCS["features"]
    elif "context" in query_lower:
        docs = MOCK_DOCS["context"]
    elif "retriev" in query_lower or "rag" in query_lower:
        docs = MOCK_DOCS["retrieval"]
    else:
        docs = MOCK_DOCS["default"]

    for i, doc in enumerate(docs[:top_k]):
        results.append(
            {
                "content": doc,
                "score": 0.95 - (i * 0.1),  # Mock similarity scores
                "source": f"docs/fabra/{query_lower.split()[0] if query_lower else 'intro'}.md",
            }
        )

    # Simulate retrieval latency
    latency_ms = (time.time() - start) * 1000

    # Record in lineage (auto-tracked by decorator)
    from fabra.context import record_retriever_usage

    record_retriever_usage(
        retriever_name="demo_docs",
        query=query,
        results_count=len(results),
        latency_ms=latency_ms,
    )

    return results


# --- Context Assembly ---


@context(
    store,
    name="chat_context",
    max_tokens=500,
    freshness_sla="5m",  # Features must be < 5 minutes old
)
async def chat_context(user_id: str, query: str) -> List[ContextItem]:
    """
    Assemble context for a chat response.

    This demonstrates:
    1. Feature retrieval with lineage tracking
    2. Mock retriever (no API key needed)
    3. Priority-based context items
    4. Token budget management
    """
    # Get user features (tracked in lineage)
    tier = user_tier(user_id)
    score = user_engagement_score(user_id)
    priority = support_priority(user_id)

    # Record feature usage for lineage
    from fabra.context import record_feature_usage
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    record_feature_usage("user_tier", user_id, tier, now, "compute")
    record_feature_usage("user_engagement_score", user_id, score, now, "compute")
    record_feature_usage("support_priority", user_id, priority, now, "compute")

    # Retrieve relevant docs
    docs = await search_docs(query, top_k=3)

    # Build context items with priorities
    items = [
        # System prompt (highest priority, required)
        ContextItem(
            content="You are a helpful AI assistant for Fabra users. "
            "Be concise and accurate. Reference documentation when helpful.",
            priority=100,
            required=True,
            source_id="system_prompt",
        ),
        # User context (high priority)
        ContextItem(
            content=f"User Profile:\n"
            f"- Tier: {tier}\n"
            f"- Engagement Score: {score}\n"
            f"- Support Priority: {priority}",
            priority=90,
            required=False,
            source_id="user_features",
        ),
        # Retrieved documents (medium priority)
        ContextItem(
            content="Relevant Documentation:\n"
            + "\n".join(f"- {d['content']}" for d in docs),
            priority=50,
            required=False,
            source_id="retrieved_docs",
        ),
        # User query (required)
        ContextItem(
            content=f"User Query: {query}",
            priority=100,
            required=True,
            source_id="user_query",
        ),
    ]

    return items


# --- Additional Demo Context ---


@context(store, name="support_context", max_tokens=300)
async def support_context(user_id: str, issue: str) -> List[ContextItem]:
    """
    Context for support ticket routing.

    Demonstrates minimal context assembly with just features.
    """
    tier = user_tier(user_id)
    priority = support_priority(user_id)

    # Record feature usage
    from fabra.context import record_feature_usage
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    record_feature_usage("user_tier", user_id, tier, now, "compute")
    record_feature_usage("support_priority", user_id, priority, now, "compute")

    return [
        ContextItem(
            content="Route this support ticket appropriately.",
            priority=100,
            required=True,
        ),
        ContextItem(
            content=f"User: {user_id} | Tier: {tier} | Priority: {priority}",
            priority=90,
            required=True,
        ),
        ContextItem(
            content=f"Issue: {issue}",
            priority=80,
            required=True,
        ),
    ]


# --- Pre-seed Demo Data ---


async def _seed_demo_data() -> None:
    """Pre-seed the online store with demo data."""
    demo_users = ["user_123", "user_456", "alice", "bob"]

    for uid in demo_users:
        features = {
            "user_tier": user_tier(uid),
            "user_engagement_score": user_engagement_score(uid),
            "support_priority": support_priority(uid),
        }
        await store.online_store.set_online_features("User", uid, features)


def _run_seed() -> None:
    """Run the seeding synchronously on module load."""
    import asyncio

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_seed_demo_data())
    except RuntimeError:
        asyncio.run(_seed_demo_data())


# Seed on import
_run_seed()

if __name__ == "__main__":
    import asyncio

    async def demo() -> None:
        await _seed_demo_data()

        # Test the context assembly
        ctx = await chat_context("user_123", "how do features work?")
        print(f"Context ID: {ctx.id}")
        print(f"Freshness: {ctx.meta.get('freshness_status')}")
        print(f"Token Usage: {ctx.meta.get('token_usage')}")
        print(f"\nContent Preview:\n{ctx.content[:300]}...")

        if ctx.lineage:
            print(f"\nFeatures Used: {len(ctx.lineage.features_used)}")
            print(f"Retrievers Used: {len(ctx.lineage.retrievers_used)}")

    asyncio.run(demo())
    print("\nDemo data seeded! Test with:")
    print(
        '  curl -X POST localhost:8000/v1/context/chat_context -H "Content-Type: application/json" -d \'{"user_id":"user_123","query":"how do features work?"}\''
    )
