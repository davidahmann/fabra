import os
import json
import tempfile
from unittest.mock import patch

from fabra.utils import pricing


def test_estimate_cost_default():
    # Test valid model
    cost = pricing.estimate_cost("gpt-4o", 1_000_000, 1_000_000)
    # Input 2.50, Output 10.00 -> 12.50
    assert cost == 12.50


def test_estimate_cost_fallback():
    # Test unknown model uses default
    cost = pricing.estimate_cost("unknown-model-xyz", 1_000_000, 0)
    # Default input is 5.00
    assert cost == 5.00


def test_custom_pricing_file():
    # Create temp file
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        json.dump({"custom-model": {"input": 100.0, "output": 200.0}}, f)
        temp_path = f.name

    try:
        # Reset internal state
        pricing._merged_pricing = None
        pricing._checked_freshness = False

        with patch.dict(os.environ, {"FABRA_CUSTOM_PRICING_FILE": temp_path}):
            cost = pricing.estimate_cost("custom-model", 1_000_000, 0)
            assert cost == 100.0

            # Verify overrides work but defaults remain
            default_cost = pricing.estimate_cost("gpt-4o", 1_000_000, 0)
            assert default_cost == 2.50
    finally:
        os.unlink(temp_path)
        # Reset execution state
        pricing._merged_pricing = None


def test_stale_pricing_warning():
    # Mock logger
    with patch("fabra.utils.pricing.logger") as mock_logger:
        with patch("fabra.utils.pricing.PRICING_VERSION", "2020-01"):
            pricing._checked_freshness = False
            pricing._merged_pricing = None

            pricing._check_pricing_freshness()

            mock_logger.warning.assert_called_once()
            args, kwargs = mock_logger.warning.call_args
            assert args[0] == "pricing_data_stale"
