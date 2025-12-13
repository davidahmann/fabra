"""
No-keys, serve-able RAG demo (context assembly + retriever).

Run:
  fabra serve examples/rag_chatbot_no_keys.py

Test:
  curl -X POST http://127.0.0.1:8000/v1/context/chat_context \\
    -H 'Content-Type: application/json' \\
    -d '{\"user_id\":\"user_123\",\"query\":\"How does context work?\"}'
"""

import asyncio
from datetime import timedelta

from fabra.context import Context, ContextItem, context
from fabra.core import FeatureStore, entity, feature
from fabra.retrieval import retriever
from fabra.store import DuckDBOfflineStore, InMemoryOnlineStore

store = FeatureStore(
    offline_store=DuckDBOfflineStore(),
    online_store=InMemoryOnlineStore(),
)


@entity(store)
class User:
    user_id: str


@feature(entity=User, refresh=timedelta(hours=1))
def user_tier(user_id: str) -> str:
    return "premium" if hash(user_id) % 2 == 0 else "free"


@feature(entity=User)
def support_history(user_id: str) -> list[str]:
    return [
        "Issue #101: Login failure",
        "Issue #98: Billing question",
        "Issue #45: Feature request",
    ]


@retriever(name="knowledge_base", cache_ttl=timedelta(seconds=300))  # type: ignore[untyped-decorator]
async def search_docs(query: str, top_k: int = 3) -> list[str]:
    return [
        "Fabra creates Context Records for every assembly.",
        "Use @context to define prompt assembly with token budgets.",
        "Use @retriever to define retrieval without YAML.",
    ][:top_k]


@context(store, name="chat_context", max_tokens=400)
async def chat_context(user_id: str, query: str) -> Context:
    features = await store.get_online_features(
        "User", user_id, ["user_tier", "support_history"]
    )
    tier = features.get("user_tier", "free")
    history = features.get("support_history", [])
    docs = await search_docs(query)

    items = [
        ContextItem(content="You are a helpful assistant.", priority=0, required=True),
        ContextItem(content=f"User Tier: {tier}", priority=1, required=True),
        ContextItem(content="Context:\n" + "\n".join(docs), priority=2, required=True),
        ContextItem(
            content="History:\n" + "\n".join(str(h) for h in history),
            priority=3,
            required=False,
        ),
    ]
    return items  # type: ignore[return-value]


async def _seed_demo_data() -> None:
    await store.online_store.set_online_features(
        "User",
        "user_123",
        {
            "user_tier": user_tier("user_123"),
            "support_history": support_history("user_123"),
        },
    )


def _run_seed() -> None:
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_seed_demo_data())
    except RuntimeError:
        asyncio.run(_seed_demo_data())


_run_seed()
