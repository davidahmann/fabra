from unittest.mock import patch
from typer.testing import CliRunner
from fabra.cli import app

runner = CliRunner()


def test_version() -> None:
    with patch("importlib.metadata.version", return_value="1.2.3"):
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "Fabra v1.2.3" in result.stdout


def test_doctor_cmd() -> None:
    # Doctor command runs diagnostics and exits with 0 (pass) or 1 (fail)
    # It doesn't require mocking since it does actual checks
    result = runner.invoke(app, ["doctor"])
    # Exit code 0 = all checks pass, 1 = some failures (both are valid outcomes)
    assert result.exit_code in (0, 1)
    # Should contain diagnostic output
    assert "Fabra Doctor" in result.stdout or "System Information" in result.stdout


def test_worker_cmd() -> None:
    # Test failure path (file not found)
    with patch("os.path.exists", return_value=False):
        result = runner.invoke(app, ["worker", "missing.py"])
        assert result.exit_code != 0
