import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch
from src.backtester import Backtester
from src.config import Config
from src.strategy import Strategy
from src.risk_manager import RiskManager
from src.indicator_calculator import IndicatorCalculator
import warnings

# Suppress FutureWarning messages from pandas
warnings.simplefilter(action='ignore', category=FutureWarning)

# Mock settings for Backtester initialization
@pytest.fixture
def mock_settings():
    """Provides a mock configuration object for tests."""
    mock_config = MagicMock(spec=Config)
    mock_config.sma_length = 14
    mock_config.volume_sma_length = 14
    mock_config.adx_length = 14
    mock_config.atr_length = 14
    mock_config.rsi_length = 14
    mock_config.risk_per_trade = 1.0
    mock_config.take_profit_levels = [2.0, 3.0]
    mock_config.adx_threshold = 25
    mock_config.rsi_overbought = 70
    mock_config.rsi_oversold = 30
    # Add any other attributes from Config that are accessed in the code under test
    mock_config.telegram_token = "test_token"
    mock_config.telegram_chat_id = "test_chat_id"
    return mock_config

# Fixture for dummy OHLCV data with enough length for indicators
@pytest.fixture
def dummy_ohlcv_data_for_backtest(mock_settings):
    num_rows = 500 # Increased significantly for more realistic data and signals
    dates = pd.to_datetime(pd.date_range('2023-01-01', periods=num_rows, freq='D'))
    
    # Create more realistic price movements
    np.random.seed(42) # for reproducibility
    prices = 100 + np.cumsum(np.random.randn(num_rows) * 0.5)
    volumes = 1000 + np.random.randint(-100, 100, num_rows)

    data = {
        'open': prices,
        'high': prices + np.abs(np.random.randn(num_rows) * 0.5),
        'low': prices - np.abs(np.random.randn(num_rows) * 0.5),
        'close': prices + np.random.randn(num_rows) * 0.1,
        'volume': np.maximum(100, volumes) # Ensure volume is not zero or negative
    }
    df = pd.DataFrame(data, index=dates)

    # Process data with the actual IndicatorCalculator
    indicator_calculator = IndicatorCalculator(settings_obj=mock_settings)
    df_with_indicators = indicator_calculator.add_all_indicators(df.copy())

    # Force some signals for testing purposes, ensuring they are within valid index range
    # Ensure these indices are valid after dropna in IndicatorCalculator
    valid_indices = df_with_indicators.index
    if len(valid_indices) > 60:
        df_with_indicators.loc[df_with_indicators.index[20], 'long_signal'] = True # Force a long signal
        df_with_indicators.loc[df_with_indicators.index[40], 'short_signal'] = True # Force a short signal
        df_with_indicators.loc[df_with_indicators.index[60], 'long_signal'] = True # Force another long signal

    return df_with_indicators

def test_backtester_initialization(mock_settings):
    backtester = Backtester(initial_equity=5000.0, settings_obj=mock_settings)
    assert backtester.initial_equity == 5000.0
    assert backtester.equity_curve.empty
    assert not backtester.trades
    assert isinstance(backtester.strategy, Strategy)
    assert isinstance(backtester.risk_manager, RiskManager)

@patch('src.strategy.Strategy.get_trade_parameters')
@patch('src.risk_manager.RiskManager.calculate_position_size')
def test_run_backtest_basic_flow(mock_calculate_position_size, mock_get_trade_parameters, mock_settings, dummy_ohlcv_data_for_backtest):
    # Configure mocks to force a trade
    mock_get_trade_parameters.side_effect = [
        {'signal_type': None}] * 20 + \
        [{'signal_type': 'long', 'entry_price': 100, 'take_profit_levels': [110], 'stop_loss': 95, 'adx_at_entry': 30}] + \
        [{'signal_type': None}] * 19 + \
        [{'signal_type': 'short', 'entry_price': 105, 'take_profit_levels': [95], 'stop_loss': 110, 'adx_at_entry': 35}] + \
        [{'signal_type': None}] * (len(dummy_ohlcv_data_for_backtest) - 41)

    mock_calculate_position_size.return_value = 0.1 # Fixed position size for simplicity

    backtester = Backtester(initial_equity=10000.0, settings_obj=mock_settings)
    results = backtester.run_backtest(dummy_ohlcv_data_for_backtest.copy())

    assert 'total_pnl' in results
    assert 'final_equity' in results
    assert 'num_trades' in results
    assert 'win_rate' in results
    assert 'avg_win' in results
    assert 'avg_loss' in results
    assert 'profit_factor' in results
    assert 'max_drawdown' in results
    assert 'sharpe_ratio' in results
    assert 'sortino_ratio' in results
    assert 'calmar_ratio' in results
    assert 'equity_curve' in results
    assert isinstance(results['equity_curve'], str) # Check if it's a JSON string

    assert backtester.equity_curve is not None
    assert not backtester.equity_curve.empty
    assert len(backtester.trades) > 0 # Expect some trades due to forced signals

@patch('src.strategy.Strategy.get_trade_parameters')
@patch('src.risk_manager.RiskManager.calculate_position_size')
def test_backtest_trade_logic(mock_calculate_position_size, mock_get_trade_parameters, mock_settings, dummy_ohlcv_data_for_backtest):
    # Configure mocks to force a trade
    mock_get_trade_parameters.side_effect = [
        {'signal_type': None}] * 20 + \
        [{'signal_type': 'long', 'entry_price': 100, 'take_profit_levels': [110], 'stop_loss': 95, 'adx_at_entry': 30}] + \
        [{'signal_type': None}] * 19 + \
        [{'signal_type': 'short', 'entry_price': 105, 'take_profit_levels': [95], 'stop_loss': 110, 'adx_at_entry': 35}] + \
        [{'signal_type': None}] * (len(dummy_ohlcv_data_for_backtest) - 41)

    mock_calculate_position_size.return_value = 0.1 # Fixed position size for simplicity

    backtester = Backtester(initial_equity=10000.0, settings_obj=mock_settings)
    backtester.run_backtest(dummy_ohlcv_data_for_backtest.copy())

    # Check if trades were recorded correctly
    assert len(backtester.trades) > 0
    for trade in backtester.trades:
        assert 'entry_date' in trade
        assert 'exit_date' in trade
        assert 'type' in trade
        assert 'entry_price' in trade
        assert 'exit_price' in trade
        assert 'pnl' in trade
        assert 'reason' in trade

    # Verify equity curve calculation (simple check)
    # The last PnL might not be added to the last equity if the trade is still open
    # So, we check the final equity against the initial equity plus total PnL
    total_pnl = sum(t['pnl'] for t in backtester.trades)
    assert backtester.equity_curve.iloc[-1] == pytest.approx(backtester.initial_equity + total_pnl)

# Test case for no trades executed
def test_run_backtest_no_trades(mock_settings):
    # Create data with no signals
    num_rows = 50
    dates = pd.to_datetime(pd.date_range('2023-01-01', periods=num_rows, freq='D'))
    prices = 100 + np.cumsum(np.random.randn(num_rows) * 0.1)
    volumes = 1000 + np.random.randint(-10, 10, num_rows)
    df = pd.DataFrame({
        'open': prices,
        'high': prices + 0.1,
        'low': prices - 0.1,
        'close': prices,
        'volume': volumes
    }, index=dates)

    # Process data with the actual IndicatorCalculator
    indicator_calculator = IndicatorCalculator(settings_obj=mock_settings)
    df_with_indicators = indicator_calculator.add_all_indicators(df.copy())

    # Ensure no signals are generated by setting ADX below threshold
    df_with_indicators[f'ADX_{mock_settings.adx_length}'] = 10 # Below default threshold of 25
    df_with_indicators['long_signal'] = False
    df_with_indicators['short_signal'] = False

    backtester = Backtester(initial_equity=10000.0, settings_obj=mock_settings)
    results = backtester.run_backtest(df_with_indicators.copy())

    assert results['num_trades'] == 0
    assert results['total_pnl'] == 0.0
    assert results['final_equity'] == 10000.0

# Test for drawdown calculation
def test_drawdown_calculation(mock_settings):
    backtester = Backtester(initial_equity=100.0, settings_obj=mock_settings)
    # Create a simple equity curve for testing drawdown
    equity_data = [
        100, 110, 105, 120, 115, 130, 125, 140, 135, 150 # Peak at 150
    ]
    dates = pd.to_datetime(pd.date_range('2023-01-01', periods=len(equity_data), freq='D'))
    backtester.equity_curve = pd.Series(equity_data, index=dates)

    metrics = backtester._calculate_metrics()
    # Max drawdown is from 110 to 105: (105 - 110) / 110 = -0.045454545454545414
    assert metrics['max_drawdown'] == pytest.approx(-0.045454545454545414)
