from typer.testing import CliRunner

from fabra.cli import app


runner = CliRunner()


def test_root_help_lists_core_commands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    # Core workflow commands should be discoverable from the top-level help.
    assert "demo" in result.stdout
    assert "context" in result.stdout
    assert "doctor" in result.stdout


def test_context_help_lists_subcommands() -> None:
    result = runner.invoke(app, ["context", "--help"])
    assert result.exit_code == 0
    for subcommand in ("show", "list", "export", "diff", "verify"):
        assert subcommand in result.stdout


def test_context_export_help_mentions_bundle() -> None:
    result = runner.invoke(app, ["context", "export", "--help"])
    assert result.exit_code == 0
    assert "--bundle" in result.stdout


def test_context_verify_help_mentions_crs() -> None:
    result = runner.invoke(app, ["context", "verify", "--help"])
    assert result.exit_code == 0
    assert "CRS-001" in result.stdout
