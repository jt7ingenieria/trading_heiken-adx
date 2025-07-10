import pytest
from unittest.mock import MagicMock
from src.risk_manager import RiskManager
from src.config import Config

# Mock settings for RiskManager initialization
@pytest.fixture
def mock_settings():
    """Provides a mock configuration object for tests."""
    mock_config = MagicMock(spec=Config)
    # Set a default risk_per_trade, which can be overridden in tests
    mock_config.risk_per_trade = 1.0
    return mock_config

@pytest.mark.parametrize("equity, risk_per_trade, atr, expected_size", [
    (10000.0, 1.0, 100.0, 0.5),   # Normal case: (10000 * 0.01) / (2 * 100) = 0.5
    (10000.0, 2.0, 100.0, 1.0),   # Higher risk: (10000 * 0.02) / (2 * 100) = 1.0
    (5000.0, 1.5, 50.0, 0.75),    # Different equity/risk: (5000 * 0.015) / (2 * 50) = 0.75
    (10000.0, 1.0, 0.0, 0.0),     # Zero ATR should result in zero size
    (10000.0, 1.0, -50.0, 0.0),   # Negative ATR should result in zero size
])
def test_calculate_position_size(mock_settings, equity, risk_per_trade, atr, expected_size):
    """Tests the position size calculation with various inputs."""
    mock_settings.risk_per_trade = risk_per_trade  # Set risk for the specific test case
    risk_manager = RiskManager(equity=equity, settings_obj=mock_settings)
    calculated_size = risk_manager.calculate_position_size(atr=atr)
    assert calculated_size == pytest.approx(expected_size)

def test_initial_equity_zero_or_negative(mock_settings):
    """Tests that a ValueError is raised for non-positive initial equity."""
    with pytest.raises(ValueError, match="Initial equity must be positive."):
        RiskManager(equity=0.0, settings_obj=mock_settings)
    with pytest.raises(ValueError, match="Initial equity must be positive."):
        RiskManager(equity=-100.0, settings_obj=mock_settings)
