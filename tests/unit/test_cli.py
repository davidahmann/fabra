from typer.testing import CliRunner
from fabra.cli import app
import os

from pathlib import Path

runner = CliRunner()


def test_serve_file_not_found() -> None:
    result = runner.invoke(app, ["serve", "non_existent_file.py"])
    assert result.exit_code == 1
    assert "Error: File 'non_existent_file.py' not found" in result.stdout


def test_serve_no_feature_store(tmp_path: Path) -> None:
    # Create a dummy python file without a FeatureStore
    d = tmp_path / "empty_features.py"
    d.write_text("print('hello')")

    result = runner.invoke(app, ["serve", str(d)])
    assert result.exit_code == 1
    assert "Error: No FeatureStore instance found in file" in result.stdout


def test_serve_success(tmp_path: Path) -> None:
    # Create a valid feature definitions file
    d = tmp_path / "valid_features.py"
    content = """
from fabra.core import FeatureStore, entity, feature
from datetime import timedelta

store = FeatureStore()

@entity(store)
class User:
    user_id: str

@feature(entity=User, refresh=timedelta(minutes=5))
def user_click_count(user_id: str) -> int:
    return 42
"""
    d.write_text(content)

    # We mock uvicorn.run because we don't want to actually start the server blocking
    import uvicorn
    from unittest.mock import patch

    with patch.object(uvicorn, "run") as mock_run:
        result = runner.invoke(app, ["serve", str(d)])

        assert result.exit_code == 0
        # Relax assertion to handle rich formatting/wrapping
        assert "Successfully loaded features" in result.stdout
        mock_run.assert_called_once()


def test_ui_command_file_not_found() -> None:
    """Test that ui command fails gracefully for non-existent file."""
    result = runner.invoke(app, ["ui", "non_existent_file.py"])
    assert result.exit_code == 1
    assert "not found" in result.stdout


def test_ui_command_no_feature_store(tmp_path: Path) -> None:
    """Test that ui command fails gracefully for file without FeatureStore."""
    d = tmp_path / "features.py"
    d.write_text("pass")

    result = runner.invoke(app, ["ui", str(d)])
    # Should fail because file has no FeatureStore
    assert result.exit_code == 1
    assert "No FeatureStore instance found" in result.stdout


def test_init_dry_run(tmp_path: Path) -> None:
    # Use tmp_path as CWD for this test to avoid polluting project root
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            app, ["init", "my_new_project", "--dry-run", "--no-interactive"]
        )

        assert result.exit_code == 0
        assert "Would create directory: my_new_project" in result.stdout
        assert "Would create file: my_new_project/.gitignore" in result.stdout

        # Verify nothing was created
        assert not os.path.exists("my_new_project")


def test_verbose_flag() -> None:
    # Use 'version' command as it's simple
    result = runner.invoke(app, ["--verbose", "version"])

    assert result.exit_code == 0
    assert "Fabra v" in result.stdout
    assert "Verbose output enabled" in result.stdout
