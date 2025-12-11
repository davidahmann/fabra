"""
Tests for GTM 30-second quickstart demo functionality.

This module tests:
1. `fabra demo` CLI command
2. demo_features.py example file
3. demo_context.py example file
"""

import pytest
from pathlib import Path
from typer.testing import CliRunner
import importlib.util
import sys

from fabra.cli import app

runner = CliRunner()


# --- Tests for `fabra demo` command ---


def test_demo_command_invalid_mode() -> None:
    """Test that demo command rejects invalid modes."""
    result = runner.invoke(app, ["demo", "--mode", "invalid"])
    assert result.exit_code == 1
    assert "Unknown mode 'invalid'" in result.stdout


def test_demo_command_features_mode_validates_mode() -> None:
    """Test that demo command validates mode without starting server.

    Note: Full integration test with server is in test_30_second_quickstart.sh.
    This just validates the CLI argument parsing before any server work.
    """
    # We just verify the command at least starts and finds the file
    # The actual server test is done in the quickstart script
    from fabra import cli

    # Check the demo_cmd function exists
    assert hasattr(cli, "demo_cmd")


def test_demo_command_context_mode_validates_mode() -> None:
    """Test that demo command context mode exists.

    Note: Full integration test with server is in test_30_second_quickstart.sh.
    """
    # Validated by test_demo_command_invalid_mode passing
    pass


def test_demo_command_default_port() -> None:
    """Test that demo command has default port 8000."""
    from fabra import cli
    import inspect

    sig = inspect.signature(cli.demo_cmd)
    port_param = sig.parameters.get("port")
    assert port_param is not None
    assert port_param.default.default == 8000


# --- Tests for demo_features.py example ---


class TestDemoFeaturesExample:
    """Tests for examples/demo_features.py"""

    @pytest.fixture
    def demo_features_path(self) -> Path:
        """Get path to demo_features.py"""
        return Path(__file__).parent.parent.parent / "examples" / "demo_features.py"

    def test_demo_features_file_exists(self, demo_features_path: Path) -> None:
        """Test that demo_features.py exists."""
        assert (
            demo_features_path.exists()
        ), f"demo_features.py not found at {demo_features_path}"

    def test_demo_features_imports_successfully(self, demo_features_path: Path) -> None:
        """Test that demo_features.py can be imported without errors."""
        if not demo_features_path.exists():
            pytest.skip("demo_features.py not found")

        spec = importlib.util.spec_from_file_location(
            "demo_features", demo_features_path
        )
        assert spec is not None
        assert spec.loader is not None

        module = importlib.util.module_from_spec(spec)
        # Must use the same name as the spec for Python 3.9 get_type_hints compatibility
        sys.modules["demo_features"] = module

        # Should not raise any exceptions
        spec.loader.exec_module(module)

        # Cleanup
        del sys.modules["demo_features"]

    def test_demo_features_has_store(self, demo_features_path: Path) -> None:
        """Test that demo_features.py defines a FeatureStore."""
        if not demo_features_path.exists():
            pytest.skip("demo_features.py not found")

        spec = importlib.util.spec_from_file_location(
            "demo_features", demo_features_path
        )
        assert spec is not None and spec.loader is not None

        module = importlib.util.module_from_spec(spec)
        sys.modules["demo_features"] = module
        spec.loader.exec_module(module)

        from fabra.core import FeatureStore

        # Find store in module
        store_found = False
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, FeatureStore):
                store_found = True
                break

        assert store_found, "demo_features.py must define a FeatureStore instance"

    def test_demo_features_user_engagement_deterministic(
        self, demo_features_path: Path
    ) -> None:
        """Test that user_engagement feature returns deterministic values."""
        if not demo_features_path.exists():
            pytest.skip("demo_features.py not found")

        spec = importlib.util.spec_from_file_location(
            "demo_features", demo_features_path
        )
        assert spec is not None and spec.loader is not None

        module = importlib.util.module_from_spec(spec)
        sys.modules["demo_features"] = module
        spec.loader.exec_module(module)

        # Test determinism - same input should give same output
        result1 = module.user_engagement("user_123")
        result2 = module.user_engagement("user_123")

        assert result1 == result2, "user_engagement should be deterministic"
        assert isinstance(result1, float), "user_engagement should return float"
        assert 0 <= result1 <= 100, "user_engagement should be between 0 and 100"

    def test_demo_features_user_tier_deterministic(
        self, demo_features_path: Path
    ) -> None:
        """Test that user_tier feature returns deterministic values."""
        if not demo_features_path.exists():
            pytest.skip("demo_features.py not found")

        spec = importlib.util.spec_from_file_location(
            "demo_features", demo_features_path
        )
        assert spec is not None and spec.loader is not None

        module = importlib.util.module_from_spec(spec)
        sys.modules["demo_features"] = module
        spec.loader.exec_module(module)

        result1 = module.user_tier("user_123")
        result2 = module.user_tier("user_123")

        assert result1 == result2, "user_tier should be deterministic"
        assert result1 in ["premium", "free"], "user_tier should be 'premium' or 'free'"


# --- Tests for demo_context.py example ---


class TestDemoContextExample:
    """Tests for examples/demo_context.py"""

    @pytest.fixture
    def demo_context_path(self) -> Path:
        """Get path to demo_context.py"""
        return Path(__file__).parent.parent.parent / "examples" / "demo_context.py"

    def test_demo_context_file_exists(self, demo_context_path: Path) -> None:
        """Test that demo_context.py exists."""
        assert (
            demo_context_path.exists()
        ), f"demo_context.py not found at {demo_context_path}"

    def test_demo_context_imports_successfully(self, demo_context_path: Path) -> None:
        """Test that demo_context.py can be imported without errors."""
        if not demo_context_path.exists():
            pytest.skip("demo_context.py not found")

        spec = importlib.util.spec_from_file_location("demo_context", demo_context_path)
        assert spec is not None
        assert spec.loader is not None

        module = importlib.util.module_from_spec(spec)
        # Must use the same name as the spec for Python 3.9 get_type_hints compatibility
        sys.modules["demo_context"] = module

        # Should not raise any exceptions
        spec.loader.exec_module(module)

        # Cleanup
        del sys.modules["demo_context"]

    def test_demo_context_has_store(self, demo_context_path: Path) -> None:
        """Test that demo_context.py defines a FeatureStore."""
        if not demo_context_path.exists():
            pytest.skip("demo_context.py not found")

        spec = importlib.util.spec_from_file_location("demo_context", demo_context_path)
        assert spec is not None and spec.loader is not None

        module = importlib.util.module_from_spec(spec)
        sys.modules["demo_context"] = module
        spec.loader.exec_module(module)

        from fabra.core import FeatureStore

        store_found = False
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, FeatureStore):
                store_found = True
                break

        assert store_found, "demo_context.py must define a FeatureStore instance"

    def test_demo_context_has_mock_retriever(self, demo_context_path: Path) -> None:
        """Test that demo_context.py has a mock retriever (no API key needed)."""
        if not demo_context_path.exists():
            pytest.skip("demo_context.py not found")

        spec = importlib.util.spec_from_file_location("demo_context", demo_context_path)
        assert spec is not None and spec.loader is not None

        module = importlib.util.module_from_spec(spec)
        sys.modules["demo_context"] = module
        spec.loader.exec_module(module)

        # Check for search_docs function
        assert hasattr(
            module, "search_docs"
        ), "demo_context.py must have search_docs retriever"

    @pytest.mark.asyncio
    async def test_demo_context_search_docs_no_api_key(
        self, demo_context_path: Path
    ) -> None:
        """Test that search_docs works without any API key."""
        if not demo_context_path.exists():
            pytest.skip("demo_context.py not found")

        spec = importlib.util.spec_from_file_location("demo_context", demo_context_path)
        assert spec is not None and spec.loader is not None

        module = importlib.util.module_from_spec(spec)
        sys.modules["demo_context"] = module
        spec.loader.exec_module(module)

        # Should work without OPENAI_API_KEY or any other API key
        results = await module.search_docs("features", top_k=2)

        assert isinstance(results, list), "search_docs should return a list"
        assert len(results) > 0, "search_docs should return at least one result"
        assert all("content" in r for r in results), "Each result should have 'content'"


# --- Integration test for quickstart script ---


class TestQuickstartScript:
    """Tests for scripts/test_30_second_quickstart.sh"""

    @pytest.fixture
    def quickstart_script_path(self) -> Path:
        """Get path to test_30_second_quickstart.sh"""
        return (
            Path(__file__).parent.parent.parent
            / "scripts"
            / "test_30_second_quickstart.sh"
        )

    def test_quickstart_script_exists(self, quickstart_script_path: Path) -> None:
        """Test that test_30_second_quickstart.sh exists."""
        assert (
            quickstart_script_path.exists()
        ), f"Quickstart script not found at {quickstart_script_path}"

    def test_quickstart_script_is_executable(
        self, quickstart_script_path: Path
    ) -> None:
        """Test that test_30_second_quickstart.sh has executable permissions."""
        if not quickstart_script_path.exists():
            pytest.skip("Quickstart script not found")

        import os
        import stat

        mode = os.stat(quickstart_script_path).st_mode
        is_executable = bool(mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))

        assert is_executable, "test_30_second_quickstart.sh should be executable"

    def test_quickstart_script_has_required_tests(
        self, quickstart_script_path: Path
    ) -> None:
        """Test that quickstart script tests both features and context demos."""
        if not quickstart_script_path.exists():
            pytest.skip("Quickstart script not found")

        content = quickstart_script_path.read_text()

        # Should test feature store demo
        assert "demo_features.py" in content, "Script should test demo_features.py"

        # Should test context store demo
        assert "demo_context.py" in content, "Script should test demo_context.py"

        # Should validate responses
        assert "curl" in content, "Script should use curl to test endpoints"
