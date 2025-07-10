import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock
from src.strategy import Strategy
from src.config import Config
from src.indicator_calculator import IndicatorCalculator

# Mock settings for Strategy initialization
@pytest.fixture
def mock_settings():
    """Provides a mock configuration object for tests."""
    mock_config = MagicMock(spec=Config)
    mock_config.sma_length = 14
    mock_config.volume_sma_length = 14
    mock_config.volume_multiplier = 1.5
    mock_config.adx_length = 14
    mock_config.adx_threshold = 25
    mock_config.atr_length = 14
    mock_config.rsi_length = 14
    mock_config.rsi_overbought = 70
    mock_config.rsi_oversold = 30
    mock_config.take_profit_levels = [2.0, 3.0]
    return mock_config

# Fixture for dummy OHLCV data with indicators, using the actual calculator
@pytest.fixture
def dummy_data_with_indicators(mock_settings):
    """
    Creates a DataFrame with indicators calculated by the real IndicatorCalculator,
    providing a realistic input for the Strategy tests.
    """
    num_rows = 100 # Need enough data for indicators to be calculated
    dates = pd.to_datetime(pd.date_range('2023-01-01', periods=num_rows, freq='D'))
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(num_rows) * 0.5)
    volumes = 1000 + np.random.randint(-100, 100, num_rows)

    df = pd.DataFrame({
        'open': prices,
        'high': prices + np.abs(np.random.randn(num_rows) * 0.5),
        'low': prices - np.abs(np.random.randn(num_rows) * 0.5),
        'close': prices + np.random.randn(num_rows) * 0.1,
        'volume': np.maximum(100, volumes)
    }, index=dates)

    # Use the actual calculator to add indicators
    calculator = IndicatorCalculator(settings_obj=mock_settings)
    df_with_indicators = calculator.add_all_indicators(df.copy())
    return df_with_indicators

def test_strategy_initialization(mock_settings):
    """Tests that the Strategy class initializes correctly."""
    strategy = Strategy(settings_obj=mock_settings)
    assert strategy.sma_length == mock_settings.sma_length
    assert strategy.adx_threshold == mock_settings.adx_threshold
    assert strategy.take_profit_levels == mock_settings.take_profit_levels

def test_get_trade_parameters_long_signal(mock_settings, dummy_data_with_indicators):
    """Tests the generation of a long trade signal under ideal conditions."""
    strategy = Strategy(settings_obj=mock_settings)
    df = dummy_data_with_indicators.copy()

    # Force conditions for a long signal on the last candle
    last_idx = df.index[-1]
    df.loc[last_idx, f'VOL_SMA_{mock_settings.volume_sma_length}'] = df.loc[last_idx, 'volume'] / 2 # Ensure volume is > multiplier * sma
    df.loc[last_idx, 'HA_close'] = df.loc[last_idx, 'HA_open'] + 0.1 # Bullish HA
    df.loc[last_idx, 'HA_open'] = df.loc[last_idx, 'HA_low'] # No lower wick
    df.loc[last_idx, 'close'] = df.loc[last_idx, f'SMA_{mock_settings.sma_length}'] + 0.1 # Close > SMA
    df.loc[last_idx, f'ADX_{mock_settings.adx_length}'] = mock_settings.adx_threshold + 1 # ADX > threshold
    df.loc[last_idx, f'RSI_{mock_settings.rsi_length}'] = 51 # RSI > 50

    trade_params = strategy.get_trade_parameters(df)

    assert trade_params['signal_type'] == 'long'
    assert 'entry_price' in trade_params
    assert 'take_profit_levels' in trade_params
    assert isinstance(trade_params['take_profit_levels'], list)
    assert len(trade_params['take_profit_levels']) == len(mock_settings.take_profit_levels)
    assert 'stop_loss' in trade_params
    assert 'adx_at_entry' in trade_params

def test_get_trade_parameters_short_signal(mock_settings, dummy_data_with_indicators):
    """Tests the generation of a short trade signal under ideal conditions."""
    strategy = Strategy(settings_obj=mock_settings)
    df = dummy_data_with_indicators.copy()

    # Force conditions for a short signal on the last candle
    last_idx = df.index[-1]
    df.loc[last_idx, f'VOL_SMA_{mock_settings.volume_sma_length}'] = df.loc[last_idx, 'volume'] / 2 # Ensure volume is > multiplier * sma
    df.loc[last_idx, 'HA_close'] = df.loc[last_idx, 'HA_open'] - 0.1 # Bearish HA
    df.loc[last_idx, 'HA_open'] = df.loc[last_idx, 'HA_high'] # No upper wick
    df.loc[last_idx, 'close'] = df.loc[last_idx, f'SMA_{mock_settings.sma_length}'] - 0.1 # Close < SMA
    df.loc[last_idx, f'ADX_{mock_settings.adx_length}'] = mock_settings.adx_threshold + 1 # ADX > threshold
    df.loc[last_idx, f'RSI_{mock_settings.rsi_length}'] = 49 # RSI < 50

    trade_params = strategy.get_trade_parameters(df)

    assert trade_params['signal_type'] == 'short'
    assert 'entry_price' in trade_params
    assert 'take_profit_levels' in trade_params
    assert isinstance(trade_params['take_profit_levels'], list)
    assert len(trade_params['take_profit_levels']) == len(mock_settings.take_profit_levels)
    assert 'stop_loss' in trade_params
    assert 'adx_at_entry' in trade_params

def test_get_trade_parameters_no_signal(mock_settings, dummy_data_with_indicators):
    """Tests that no signal is generated when conditions are not met."""
    strategy = Strategy(settings_obj=mock_settings)
    df = dummy_data_with_indicators.copy()

    # Ensure no signal conditions are met by setting ADX below threshold
    df[f'ADX_{mock_settings.adx_length}'] = mock_settings.adx_threshold - 1

    trade_params = strategy.get_trade_parameters(df)

    assert trade_params['signal_type'] is None
