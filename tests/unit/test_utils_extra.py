from unittest.mock import MagicMock, patch
import sys
from fabra.utils.integrity import (
    compute_content_hash,
    compute_record_hash,
    verify_record_integrity,
    verify_content_integrity,
    compute_hashes_for_record,
)
from fabra.models import IntegrityMetadata
from fabra.utils.tokens import OpenAITokenCounter, AnthropicTokenCounter
import fabra.store as store_pkg


# --- Integrity Tests ---
def test_integrity_hashes():
    content = "Hello world"
    # Expected sha256 for "Hello world"
    # echo -n "Hello world" | shasum -a 256
    # 64ec88ca00b268e5ba1a35678a1b5316d212f4f366b2477232534a8aeca37f3c
    expected_content_hash = (
        "sha256:64ec88ca00b268e5ba1a35678a1b5316d212f4f366b2477232534a8aeca37f3c"
    )

    assert compute_content_hash(content) == expected_content_hash


def test_record_hashing():
    _ = IntegrityMetadata(
        record_hash="",
        content_hash="sha256:123",
        previous_context_id="ctx_old",
        signed_at=None,
        signature=None,
    )
    record = MagicMock()
    record.model_dump.return_value = {
        "context_id": "ctx_1",
        "created_at": "2023-01-01T00:00:00Z",
        "environment": "test",
        "integrity": {"record_hash": "", "content_hash": "sha256:123"},
    }

    # Mock property access for integrity check
    mock_integrity = MagicMock()
    mock_integrity.record_hash = (
        ""  # Will verify matching logic manually or just hash computation
    )
    record.integrity = mock_integrity
    record.content = "test"

    # Compute
    rec_hash = compute_record_hash(record)
    assert rec_hash.startswith("sha256:")

    # Verify
    # We can't set property on MagicMock nicely if not configured, but we can check if hash matches expected
    # verify_record_integrity accesses record.integrity.record_hash
    # We want it to match expected.
    record.integrity.record_hash = rec_hash
    assert verify_record_integrity(record)

    # Verify content integrity failure
    # content has "test", hash is "sha256:123" (from mocking)
    # verify_content_integrity accesses record.integrity.content_hash and record.content
    record.integrity.content_hash = "sha256:123"
    assert not verify_content_integrity(
        record
    )  # Content "test" hashes to something else


def test_compute_hashes_for_record():
    rec_dict = {"content": "Hello world", "integrity": {"record_hash": "old"}}
    hashes = compute_hashes_for_record(rec_dict)

    assert (
        hashes["content_hash"]
        == "sha256:64ec88ca00b268e5ba1a35678a1b5316d212f4f366b2477232534a8aeca37f3c"
    )
    assert hashes["record_hash"].startswith("sha256:")
    assert rec_dict["integrity"]["record_hash"] == ""  # Side effect check


# --- Token Tests ---
def test_openai_token_counter_fallback():
    # Force ImportError for tiktoken
    with patch.dict(sys.modules, {"tiktoken": None}):
        counter = OpenAITokenCounter()
        assert counter.encoder is None
        # Fallback chars/4
        assert counter.count("1234") == 1
        assert counter.count("12345678") == 2


def test_openai_token_counter_success():
    mock_tiktoken = MagicMock()
    mock_enc = MagicMock()
    mock_enc.encode.return_value = [1, 2, 3]
    mock_tiktoken.encoding_for_model.return_value = mock_enc

    with patch.dict(sys.modules, {"tiktoken": mock_tiktoken}):
        counter = OpenAITokenCounter()
        assert counter.count("foo") == 3
        mock_tiktoken.encoding_for_model.assert_called_with("gpt-4o")


def test_anthropic_token_counter_fallback():
    # Force ImportError
    with patch.dict(sys.modules, {"anthropic": None}):
        counter = AnthropicTokenCounter()
        assert counter.client is None
        assert counter.count("1234") == 1


def test_anthropic_token_counter_success():
    mock_anthropic = MagicMock()
    mock_client = MagicMock()
    mock_client.beta.messages.count_tokens.return_value.input_tokens = 5
    mock_anthropic.Anthropic.return_value = mock_client

    with patch.dict(sys.modules, {"anthropic": mock_anthropic}):
        counter = AnthropicTokenCounter()
        # count() function instantiates local client
        count = counter.count("foo")
        assert count == 5


# --- Store Init Test ---
def test_store_init_exports():
    assert hasattr(store_pkg, "OfflineStore")
    assert hasattr(store_pkg, "OnlineStore")
    # Postgres/Redis heavily mocked or present
    # This essentially covers the import lines
