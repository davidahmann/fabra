import pytest
from unittest.mock import patch
from typer.testing import CliRunner
import sys
import os
from fabra.cli import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def mock_console():
    with patch("fabra.cli.console") as mock:
        yield mock


@pytest.fixture
def mock_subprocess():
    with patch("subprocess.run") as mock_run, patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value.poll.return_value = None
        yield mock_run, mock_popen


@pytest.fixture
def mock_ui_server():
    # run_server is imported locally from .ui_server
    # We must patch the SOURCE
    with patch("fabra.ui_server.run_server") as mock:
        yield mock


def create_temp_feature_file(filename="temp_ui_features.py"):
    content = """
from fabra.core import FeatureStore
store = FeatureStore()
"""
    with open(filename, "w") as f:
        f.write(content)
    return filename


def test_ui_file_not_found():
    result = runner.invoke(app, ["ui", "non_existent.py"])
    assert result.exit_code == 1
    # Check console print for error? We mocked console.
    # But checking exit code is simpler for now.


def test_ui_no_store_in_file(mock_console):
    filename = "temp_empty.py"
    with open(filename, "w") as f:
        f.write("x = 1")
    try:
        # We need sys.path to include cwd
        sys.path.append(os.getcwd())
        result = runner.invoke(app, ["ui", filename])
        assert result.exit_code == 1
        assert mock_console.print.called
        # Should assert "No FeatureStore instance found"
        # We can reuse assert_console_printed if we copy logic or import
        # For this test file, let's just check call args string
        calls = [str(call) for call in mock_console.print.call_args_list]
        assert any("No FeatureStore" in c for c in calls)
    finally:
        if os.path.exists(filename):
            os.remove(filename)


def test_ui_success(mock_console, mock_subprocess, mock_ui_server):
    filename = create_temp_feature_file()
    try:
        sys.path.append(os.getcwd())

        # We need to mock "fabra.ui_server.run_server"
        with patch("fabra.ui_server.run_server"):
            # We also need to mock "webbrowser.open"
            with patch("webbrowser.open"):
                # Mock os.path.exists for node_modules check
                # The code checks: os.path.exists(os.path.join(ui_next_dir, "node_modules"))
                # If we want to skip npm install, return True
                # If we want to test npm install, return False

                # Let's test "npm install" path first (return False)
                # But we need to make sure 'file' check passes (it calls exists(file))
                # So side_effect needed

                orig_exists = os.path.exists

                def side_effect(path):
                    if "node_modules" in path:
                        return False  # trigger install
                    if path == filename:
                        return True
                    return orig_exists(path)

                with patch("os.path.exists", side_effect=side_effect):
                    # Mock Thread to avoid background work
                    with patch("threading.Thread"):
                        # subprocess.run blocks, so if mocked, it returns immediately.
                        runner.invoke(
                            app, ["ui", filename, "--port", "3000", "--no-browser"]
                        )

                        mock_run, mock_popen = mock_subprocess
                        # subprocess.run is called for "npm install" AND "npm run dev"
                        # Because "node_modules" check returns False (via side_effect logic logic if applied)
                        # Wait, side_effect for success test returned False for node_modules?
                        # test_ui_success code: if "node_modules" in path: return False

                        # So we expect 2 calls
                        assert mock_run.call_count == 2

                        args1 = mock_run.call_args_list[0][0][0]
                        # First call is install/ci
                        assert "npm" in args1
                        # check for install or ci

                        args2 = mock_run.call_args_list[1][0][0]
                        assert "dev" in args2

    finally:
        if os.path.exists(filename):
            os.remove(filename)


def test_ui_skip_install(mock_console, mock_subprocess):
    # Test case where node_modules exists
    filename = create_temp_feature_file("temp_ui_2.py")
    try:
        sys.path.append(os.getcwd())

        orig_exists = os.path.exists

        def side_effect(path):
            # Check if checking for node_modules
            # path could be absolute .../ui-next/node_modules
            if "node_modules" in str(path):
                return True  # Present -> Skip install
            return orig_exists(path)

        with patch("os.path.exists", side_effect=side_effect):
            # Mock Thread so start_api doesn't run and race with file deletion
            with patch("threading.Thread"):
                # We also mock time.sleep so we don't wait 1s
                with patch("time.sleep"):
                    # Note: Main thread blocks on subprocess.run("npm run dev")
                    # But we mocked subprocess.run.
                    # Wait, line 883 subprocess.run IS blocking.
                    # So it returns immediately (mock).
                    # Then the function ends? No...
                    # Wait, look at code:
                    # subprocess.run(["npm", "run", "dev"...])
                    # It blocks until UI exits.
                    # So we don't need to throw exception from time.sleep!
                    # The CLI only loops if falling back or something?
                    # Let's check code again.
                    # Code: subprocess.run(..., check=True).
                    # It does NOT loop. It just runs the UI process.
                    # When user Ctrl+C, subprocess raises KeyboardInterrupt or returns?
                    # If mocked, it returns immediately!

                    runner.invoke(app, ["ui", filename, "--no-browser"])

                    mock_run, mock_popen = mock_subprocess
                    # npm install should NOT be called
                    # npm run dev SHOULD be called

                    # Check calls
                    # We expect exactly 1 call to subprocess.run for "npm run dev"
                    assert mock_run.call_count == 1
                    args = mock_run.call_args[0][0]
                    assert "dev" in args
                    assert "install" not in args

    finally:
        if os.path.exists(filename):
            os.remove(filename)
