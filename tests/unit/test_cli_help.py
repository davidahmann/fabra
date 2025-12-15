import re

from typer.testing import CliRunner

from fabra.cli import app


runner = CliRunner()

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


def test_root_help_lists_core_commands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    stdout = _strip_ansi(result.stdout)
    # Core workflow commands should be discoverable from the top-level help.
    assert "demo" in stdout
    assert "context" in stdout
    assert "doctor" in stdout


def test_context_help_lists_subcommands() -> None:
    result = runner.invoke(app, ["context", "--help"])
    assert result.exit_code == 0
    stdout = _strip_ansi(result.stdout)
    for subcommand in ("show", "list", "export", "pack", "diff", "verify"):
        assert subcommand in stdout


def test_context_export_help_mentions_bundle() -> None:
    result = runner.invoke(app, ["context", "export", "--help"])
    assert result.exit_code == 0
    assert "--bundle" in _strip_ansi(result.stdout)


def test_context_verify_help_mentions_crs() -> None:
    result = runner.invoke(app, ["context", "verify", "--help"])
    assert result.exit_code == 0
    assert "CRS-001" in _strip_ansi(result.stdout)
