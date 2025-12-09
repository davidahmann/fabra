import pytest
from unittest.mock import AsyncMock, patch
from fabra.store.postgres import PostgresOfflineStore


@pytest.mark.asyncio
async def test_index_dedup_logic() -> None:
    # Patch create_async_engine to prevent real connection
    with patch("fabra.store.postgres.create_async_engine") as MockEngine:
        mock_conn = AsyncMock()
        mock_conn.__aenter__.return_value = mock_conn
        mock_conn.__aexit__.return_value = None
        MockEngine.return_value.begin.return_value = mock_conn

        store = PostgresOfflineStore("postgresql+asyncpg://mock")

        # Call add_documents with mock data
        await store.add_documents("test_idx", "e1", ["content"], [[0.1]])

        # Verify SQL contains ON CONFLICT ... DO NOTHING
        # execute called with (text(query), values)
        # args[0] is the SQL text object. str(args[0])
        assert mock_conn.execute.called
        call_args = mock_conn.execute.call_args
        # call_args[0][0] is the first positional arg (text object)
        sql_text = str(call_args[0][0])

        assert "INSERT INTO fabra_index_test_idx" in sql_text
        assert "ON CONFLICT (entity_id, content_hash) DO NOTHING" in sql_text
