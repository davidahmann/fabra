import pytest
from unittest.mock import AsyncMock, MagicMock
from fabra.core import FeatureStore
from fabra.retrieval import retriever
from fabra.store import OfflineStore, OnlineStore
from typing import Any


@pytest.mark.asyncio
async def test_magic_retriever_wiring() -> None:
    # 1. Mock Stores
    mock_offline = MagicMock(spec=OfflineStore)
    mock_offline.search = AsyncMock(return_value=[{"content": "result", "score": 0.9}])

    mock_online = MagicMock(spec=OnlineStore)

    store = FeatureStore(offline_store=mock_offline, online_store=mock_online)

    # Mock Embedding Provider to avoid API calls
    store.embedding_provider = MagicMock()
    # embed_documents returns list of lists of floats
    store.embedding_provider.embed_documents = AsyncMock(return_value=[[0.1, 0.2, 0.3]])

    # 2. Define Magic Retriever
    # Using 'index' param triggers auto-wiring
    @retriever(index="docs", top_k=3)  # type: ignore
    async def magic_search(query: str) -> list[dict[str, Any]]:
        # This body should be ignored or bypassed by auto-wiring logic
        return []

    # 3. Register Retriever (injects store ref)
    store.register_retriever(magic_search)

    # 4. Execute
    results = await magic_search("test query")

    # 5. Verify
    # Should call store.embedding_provider.embed_documents(["test query"])
    store.embedding_provider.embed_documents.assert_called_once_with(["test query"])

    # Should call offline_store.search with correct params
    mock_offline.search.assert_called_once_with(
        index_name="docs",
        query_embedding=[0.1, 0.2, 0.3],
        top_k=3,
        filter_timestamp=None,
    )

    # Should return results from offline store
    assert len(results) == 1
    assert results[0]["content"] == "result"
    assert results[0]["score"] == 0.9


@pytest.mark.asyncio
async def test_magic_retriever_no_store_ref() -> None:
    # Test that it falls back to function body if not registered

    @retriever(index="docs")  # type: ignore
    async def orphan_search(query: str) -> list[dict[str, Any]]:
        return [{"content": "fallback"}]

    # Not registered with any store, so no store_ref injected
    results = await orphan_search("query")

    assert len(results) == 1
    assert results[0]["content"] == "fallback"
