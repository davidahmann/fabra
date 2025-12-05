from typer.testing import CliRunner
from meridian.cli import app
from unittest.mock import patch

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
from meridian.core import FeatureStore, entity, feature
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


def test_ui_command(tmp_path: Path) -> None:
    d = tmp_path / "features.py"
    d.write_text("pass")

    # Mock sys.exit to prevent crashing the test runner, and stcli.main
    with patch("streamlit.web.cli.main") as mock_st_main:
        with patch("sys.exit"):
            result = runner.invoke(app, ["ui", str(d)])
            assert result.exit_code == 0
            # Relax assertion to handle wrapping
            assert "Launching Meridian UI" in result.stdout
            assert str(d.name) in result.stdout
            mock_st_main.assert_called_once()
