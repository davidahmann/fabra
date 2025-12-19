import os
import traceback
import sys
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock, mock_open, AsyncMock
from fabra.cli import app

runner = CliRunner()


def test_version_command():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "Fabra v" in result.stdout


def test_setup_dry_run():
    result = runner.invoke(app, ["setup", "--dry-run"])
    assert result.exit_code == 0
    assert "Dry Run" in result.stdout
    assert "docker-compose.yml" in result.stdout


def test_setup_create_files():
    with (
        patch("os.makedirs") as mock_makedirs,
        patch("os.path.exists", return_value=False),
        patch("builtins.open", mock_open()) as mock_file,
        patch("os.open") as mock_os_open,
        patch("os.write"),
        patch("os.close"),
    ):
        result = runner.invoke(app, ["setup", "test_proj"])

        if result.exit_code != 0:
            print("Setup output:", result.stdout)
            if result.exception:
                traceback.print_exception(
                    type(result.exception),
                    result.exception,
                    result.exception.__traceback__,
                )

        assert result.exit_code == 0
        assert "Setup Complete" in result.stdout
        mock_makedirs.assert_called_with("test_proj")
        assert mock_file.called
        assert mock_os_open.called


def test_init_dry_run():
    result = runner.invoke(app, ["init", "myproject", "--dry-run"])
    assert result.exit_code == 0
    assert "Would create directory: myproject" in result.stdout


def test_init_interactive_openai():
    # Interactive mode is hard to test with CliRunner due to isatty check.
    with patch("os.makedirs"), patch("builtins.open", mock_open()):
        # Typer prompt reads from stdin.
        result = runner.invoke(app, ["init", "myproject"], input="openai\nsk-123\n")

        if result.exit_code != 0:
            print("Init output:", result.stdout)
            if result.exception:
                traceback.print_exception(
                    type(result.exception),
                    result.exception,
                    result.exception.__traceback__,
                )

        assert result.exit_code == 0
        assert "Created directory" in result.stdout
        # Assert API key logic skipped
        assert "Entered OpenAI API Key" not in result.stdout
        assert "Created .env" not in result.stdout


@patch("fabra.cli.uvicorn.run")
def test_serve_missing_file(mock_uvicorn):
    result = runner.invoke(app, ["serve", "non_existent.py"])
    assert result.exit_code == 1
    assert "Error" in result.stdout
    assert "not found" in result.stdout


@patch("fabra.cli.uvicorn.run")
def test_serve_valid_file(mock_uvicorn):
    # Patch FeatureStore in CLI to be MagicMock class, so isinstance(mock, FeatureStore) works
    with (
        patch("os.path.exists", return_value=True),
        patch("importlib.util.spec_from_file_location") as mock_spec,
        patch("importlib.util.module_from_spec") as mock_module,
        patch("fabra.cli.FeatureStore", new=MagicMock),
    ):
        feature_store_mock = MagicMock()
        feature_store_mock.registry.features = {}
        feature_store_mock.registry.entities = {}
        feature_store_mock.retriever_registry.retrievers = {}

        # Setup mock module
        mock_mod_instance = MagicMock()
        mock_mod_instance.store = feature_store_mock
        # Explicit dir() to include store.
        # Note: MagicMock auto-configures magic methods but sometimes explicit set is safer for __dir__
        mock_mod_instance.__dir__ = MagicMock(return_value=["store"])

        mock_module.return_value = mock_mod_instance
        # Spec loader
        mock_spec.return_value.loader = MagicMock()

        with patch("fabra.cli.create_app") as mock_create_app:
            result = runner.invoke(app, ["serve", "features.py"])

            assert (
                result.exit_code == 0
            ), f"Serve failed. Output:\n{result.stdout}\nException: {result.exception}"
            mock_uvicorn.assert_called_once()
            mock_create_app.assert_called_once()


def test_doctor_command():
    with (
        patch("redis.Redis") as mock_redis_cls,
        patch("urllib.request.urlopen") as mock_urlopen,
        patch.dict("sys.modules", {"asyncpg": MagicMock()}),
    ):
        # AsyncPg setup
        # Doctor code: import asyncpg; conn = await asyncpg.connect(...)
        mock_pg = sys.modules["asyncpg"]
        mock_conn = AsyncMock()  # Connection object
        mock_conn.fetchval.return_value = "PostgreSQL 14.0"
        mock_conn.close = AsyncMock()

        mock_pg.connect = AsyncMock(return_value=mock_conn)

        # Redis setup
        mock_redis_cls.return_value.ping.return_value = True

        # Urllib setup
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"status": "ok"}'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        with patch.dict(
            os.environ,
            {
                "FABRA_REDIS_URL": "redis://localhost:6379",
                "FABRA_POSTGRES_URL": "postgres://user:pass@localhost:5432/db",  # pragma: allowlist secret
            },
        ):
            result = runner.invoke(app, ["doctor"])

            if result.exit_code != 0:
                print("Doctor output:", result.stdout)
                if result.exception:
                    traceback.print_exception(
                        type(result.exception),
                        result.exception,
                        result.exception.__traceback__,
                    )

            assert result.exit_code == 0
            assert "System Information" in result.stdout
            assert "Redis Connection" in result.stdout
            assert "PostgreSQL Connection" in result.stdout
