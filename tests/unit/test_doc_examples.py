"""
Smoke tests to verify documentation examples are syntactically correct
and match the actual API signatures.
"""

import pytest
from datetime import timedelta


class TestRetrieverAPISignature:
    """Verify @retriever decorator signature matches docs."""

    def test_retriever_with_index_and_top_k(self):
        """Docs show: @retriever(index="docs", top_k=5)"""
        from meridian.retrieval import retriever

        @retriever(index="knowledge_base", top_k=5)
        async def search_docs(query: str):
            return []

        # Should have the decorator metadata
        assert hasattr(search_docs, "_meridian_retriever")
        assert search_docs._meridian_retriever.name == "search_docs"

    def test_retriever_with_cache_ttl(self):
        """Docs show: @retriever(index="docs", cache_ttl=timedelta(...))"""
        from meridian.retrieval import retriever

        @retriever(index="docs", top_k=3, cache_ttl=timedelta(seconds=300))
        async def cached_search(query: str):
            return []

        assert cached_search._meridian_retriever.name == "cached_search"

    def test_retriever_with_name_override(self):
        """Docs show: @retriever(name="custom_name")"""
        from meridian.retrieval import retriever

        @retriever(name="my_custom_retriever")
        async def search_func(query: str):
            return []

        assert search_func._meridian_retriever.name == "my_custom_retriever"


class TestContextAPISignature:
    """Verify @context decorator signature matches docs."""

    def test_context_with_store_and_max_tokens(self):
        """Docs show: @context(store, max_tokens=4000)"""
        from meridian.core import FeatureStore
        from meridian.context import context, ContextItem

        store = FeatureStore()

        @context(store, max_tokens=4000)
        async def chat_context(user_id: str, query: str):
            return [
                ContextItem(content="System prompt", priority=0, required=True),
                ContextItem(content="User data", priority=1),
            ]

        # Should be marked as context
        assert hasattr(chat_context, "_is_context")
        assert chat_context._is_context is True

    def test_context_without_store(self):
        """Context can work without store for simple cases."""
        from meridian.context import context, ContextItem

        @context(max_tokens=1000)
        async def simple_context(query: str):
            return [
                ContextItem(content=f"Query: {query}", priority=0),
            ]

        assert hasattr(simple_context, "_is_context")


class TestContextItemSignature:
    """Verify ContextItem has content= keyword parameter."""

    def test_context_item_with_content_kwarg(self):
        """Docs show: ContextItem(content="...", priority=0)"""
        from meridian.context import ContextItem

        item = ContextItem(content="Hello", priority=0, required=True)
        assert item.content == "Hello"
        assert item.priority == 0
        assert item.required is True

    def test_context_item_optional_fields(self):
        """ContextItem has optional source_id and last_updated."""
        from meridian.context import ContextItem
        from datetime import datetime, timezone

        item = ContextItem(
            content="Test content",
            priority=1,
            required=False,
            source_id="doc_123",
            last_updated=datetime.now(timezone.utc),
        )
        assert item.source_id == "doc_123"
        assert item.last_updated is not None


class TestContextObjectSignature:
    """Verify Context object has expected attributes."""

    def test_context_has_content_and_meta(self):
        """Docs show: ctx.content, ctx.meta, ctx.id"""
        from meridian.context import Context

        ctx = Context(
            id="test-id-123",
            content="Assembled content here",
            meta={
                "timestamp": "2025-01-01T00:00:00Z",
                "dropped_items": 0,
                "freshness_status": "guaranteed",
            },
        )

        assert ctx.id == "test-id-123"
        assert ctx.content == "Assembled content here"
        assert ctx.meta["dropped_items"] == 0
        assert ctx.is_fresh is True

    def test_context_has_no_items_attribute(self):
        """Context should NOT have .items (old API)."""
        from meridian.context import Context

        ctx = Context(id="x", content="y", meta={})

        # items should not exist as an attribute (only as dict method)
        assert not hasattr(ctx, "items") or callable(ctx.items)


class TestFeatureStoreIntegration:
    """Test basic FeatureStore usage as shown in docs."""

    def test_feature_decorator(self):
        """Docs show: @feature(entity=User, refresh=...)"""
        from meridian.core import FeatureStore, entity, feature
        from datetime import timedelta

        store = FeatureStore()

        @entity(store)
        class User:
            user_id: str

        @feature(entity=User, refresh=timedelta(hours=1))
        def user_tier(user_id: str) -> str:
            return "premium"

        # Feature should be registered
        assert "user_tier" in store.registry.features

    @pytest.mark.asyncio
    async def test_get_online_features(self):
        """Docs show: await store.get_online_features(...)"""
        from meridian.core import FeatureStore, entity, feature

        store = FeatureStore()

        @entity(store)
        class User:
            user_id: str

        @feature(entity=User)
        def user_name(user_id: str) -> str:
            return f"User {user_id}"

        result = await store.get_online_features("User", "u1", ["user_name"])
        assert "user_name" in result
        assert result["user_name"] == "User u1"


class TestEndToEndExample:
    """Full example as shown in README/quickstart."""

    @pytest.mark.asyncio
    async def test_readme_example_works(self):
        """The README quickstart example should execute without errors."""
        from meridian.core import FeatureStore, entity, feature
        from meridian.context import context, ContextItem
        from meridian.retrieval import retriever
        from datetime import timedelta

        store = FeatureStore()

        @entity(store)
        class User:
            user_id: str

        @feature(entity=User, refresh=timedelta(hours=1))
        def user_tier(user_id: str) -> str:
            return "premium" if hash(user_id) % 2 == 0 else "free"

        @retriever(index="docs", top_k=3)
        async def find_docs(query: str):
            return [{"content": "Meridian bridges ML features and RAG.", "score": 0.9}]

        @context(store, max_tokens=4000)
        async def build_prompt(user_id: str, query: str):
            tier = await store.get_feature("user_tier", user_id)
            docs = await find_docs(query)

            return [
                ContextItem(
                    content=f"User is {tier}. Adjust tone accordingly.", priority=0
                ),
                ContextItem(content=str(docs), priority=1),
            ]

        # Execute the context assembly
        ctx = await build_prompt(user_id="u1", query="How does Meridian help?")

        # Verify output structure
        assert ctx.id is not None
        assert ctx.content is not None
        assert "User is" in ctx.content
        assert ctx.meta is not None
        assert ctx.meta.get("status") == "assembled"
