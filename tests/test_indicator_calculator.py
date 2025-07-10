
import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock
from src.indicator_calculator import IndicatorCalculator
from src.config import Config
import warnings

# Suppress FutureWarning messages from pandas
warnings.simplefilter(action='ignore', category=FutureWarning)

# Mock settings for IndicatorCalculator initialization
@pytest.fixture
def mock_settings():
    """Provides a mock configuration object for tests."""
    mock_config = MagicMock(spec=Config)
    mock_config.sma_length = 14
    mock_config.volume_sma_length = 14
    mock_config.adx_length = 14
    mock_config.atr_length = 14
    mock_config.rsi_length = 14
    return mock_config

# Fixture for dummy OHLCV data
@pytest.fixture
def dummy_ohlcv_data():
    """Creates a realistic-looking OHLCV DataFrame for testing."""
    num_rows = 100
    dates = pd.to_datetime(pd.date_range('2023-01-01', periods=num_rows, freq='D'))
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(num_rows) * 0.5)
    volumes = 1000 + np.random.randint(-100, 100, num_rows)

    data = {
        'open': prices,
        'high': prices + np.abs(np.random.randn(num_rows) * 0.5),
        'low': prices - np.abs(np.random.randn(num_rows) * 0.5),
        'close': prices + np.random.randn(num_rows) * 0.1,
        'volume': np.maximum(100, volumes)
    }
    return pd.DataFrame(data, index=dates)

def test_add_all_indicators(mock_settings, dummy_ohlcv_data):
    """Tests that all indicators are added correctly and data is cleaned."""
    calculator = IndicatorCalculator(settings_obj=mock_settings)
    df_with_indicators = calculator.add_all_indicators(dummy_ohlcv_data.copy())

    # Check if all expected columns are present
    expected_columns = [
        'open', 'high', 'low', 'close', 'volume',
        'HA_open', 'HA_high', 'HA_low', 'HA_close',
        f'SMA_{mock_settings.sma_length}',
        f'VOL_SMA_{mock_settings.volume_sma_length}',
        f'RSI_{mock_settings.rsi_length}',
        f'ATRr_{mock_settings.atr_length}',
        f'ADX_{mock_settings.adx_length}'
    ]
    for col in expected_columns:
        assert col in df_with_indicators.columns, f"Missing column: {col}"

    # Check that NaN values have been removed
    assert not df_with_indicators.isnull().values.any(), "NaNs found in the final DataFrame"

    # Basic check for values (e.g., SMA should be present and not all zeros)
    assert df_with_indicators[f'SMA_{mock_settings.sma_length}'].iloc[-1] > 0
    assert df_with_indicators[f'RSI_{mock_settings.rsi_length}'].iloc[-1] > 0
    assert df_with_indicators[f'ADX_{mock_settings.adx_length}'].iloc[-1] > 0

    # Check Heikin-Ashi calculation (simple check)
    assert df_with_indicators['HA_close'].iloc[-1] > 0

    # Ensure some rows were dropped due to NaN removal
    assert 0 < len(df_with_indicators) < len(dummy_ohlcv_data)
