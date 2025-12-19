import pytest
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
import json
import os
from fabra.cli import app

runner = CliRunner()


@pytest.fixture
def mock_urlopen():
    with patch("urllib.request.urlopen") as mock:
        yield mock


@pytest.fixture(autouse=True)
def mock_console():
    with patch("fabra.cli.console") as mock:
        yield mock


@pytest.fixture
def mock_env():
    # Ensure no API key set by default
    with patch.dict(os.environ, {}, clear=True):
        yield


def assert_console_printed(mock_console, text):
    """Deep search for text in console.print arguments, including Panels."""
    calls = mock_console.print.call_args_list
    found = False
    debug_args = []

    for call in calls:
        args, _ = call
        debug_args.append(str(args))
        for arg in args:
            # Check string representation of arg
            if text in str(arg):
                found = True
                break
            # Check renderable in Panel
            if hasattr(arg, "renderable"):
                if text in str(arg.renderable):
                    found = True
                    break
            # Check title in Panel
            if hasattr(arg, "title") and arg.title:
                if text in str(arg.title):
                    found = True
                    break
        if found:
            break

    if not found:
        # Fail with helpful message
        pytest.fail(f"Text '{text}' not found in console calls. Calls: {debug_args}")


def test_context_list_success(mock_urlopen, mock_env, mock_console):
    # Mock response
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps(
        [
            {
                "context_id": "ctx_1",
                "name": "test",
                "timestamp": "2023-01-01",
                "token_usage": 100,
                "freshness_status": "guaranteed",
            }
        ]
    ).encode()
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    result = runner.invoke(app, ["context", "list", "--limit", "5"])
    assert result.exit_code == 0
    assert mock_console.print.called


def test_context_show_record_success(mock_urlopen, mock_env, mock_console):
    # Mock response for record
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps(
        {
            "context_id": "ctx_123",
            "content": "Full content",
            "integrity": {"record_hash": "abc"},
        }
    ).encode()
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    result = runner.invoke(app, ["context", "show", "ctx_123"])
    assert result.exit_code == 0
    assert_console_printed(mock_console, "ctx_123")


def test_context_show_fallback(mock_urlopen, mock_env, mock_console):
    from urllib.error import HTTPError

    err_404 = HTTPError(url="http://foo", code=404, msg="Not Found", hdrs={}, fp=None)

    mock_resp_legacy = MagicMock()
    mock_resp_legacy.status = 200
    mock_resp_legacy.read.return_value = json.dumps(
        {"context_id": "ctx_123", "content": "Legacy content"}
    ).encode()

    mock_urlopen.side_effect = [
        err_404,
        MagicMock(__enter__=MagicMock(return_value=mock_resp_legacy)),
    ]

    result = runner.invoke(app, ["context", "show", "ctx_123"])
    assert result.exit_code == 0
    assert_console_printed(mock_console, "Legacy content")
    assert_console_printed(mock_console, "falling back to legacy")


def test_context_verify_success(mock_urlopen, mock_env, mock_console):
    mock_resp = MagicMock()
    mock_resp.status = 200

    with (
        patch("fabra.utils.integrity.verify_content_integrity", return_value=True),
        patch("fabra.utils.integrity.verify_record_integrity", return_value=True),
        patch("fabra.models.ContextRecord.model_validate") as mock_validate,
    ):
        mock_rec = MagicMock()
        mock_rec.integrity.content_hash = "sha256:valid"
        mock_rec.integrity.record_hash = "sha256:valid"
        mock_validate.return_value = mock_rec

        mock_resp.read.return_value = b"{}"
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        result = runner.invoke(app, ["context", "verify", "ctx_123"])
        assert result.exit_code == 0
        assert_console_printed(mock_console, "Integrity verified")


def test_context_export_bundle(mock_urlopen, mock_env, mock_console):
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps(
        {"context_id": "ctx_1", "content": "data"}
    ).encode()
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    with patch("zipfile.ZipFile") as mock_zip:
        result = runner.invoke(
            app, ["context", "export", "ctx_1", "--bundle", "-o", "test.zip"]
        )
        assert result.exit_code == 0
        assert_console_printed(mock_console, "Wrote bundle to test.zip")
        mock_zip.assert_called()


def test_context_replay_pretty(mock_urlopen, mock_env, mock_console):
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps(
        {
            "context_id": "ctx_1",
            "meta": {
                "token_usage": 50,
                "max_tokens": 100,
                "freshness_status": "guaranteed",
            },
            "lineage": {"features_used": [{"feature_name": "f1", "value": 1}]},
            "content": "Replayed content",
        }
    ).encode()
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    result = runner.invoke(app, ["context", "replay", "ctx_1"])
    assert result.exit_code == 0
    assert_console_printed(mock_console, "Context Replay")
    assert_console_printed(mock_console, "Replayed content")
    assert_console_printed(mock_console, "Token Budget")
