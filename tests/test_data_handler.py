
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from src.data_handler import DataHandler
from src.config import Config

# Mock settings for DataHandler initialization
@pytest.fixture
def mock_settings():
    """Provides a mock configuration object for tests."""
    mock_config = MagicMock(spec=Config)
    mock_config.symbol = 'TEST/USDT'
    mock_config.timeframe = '1h'
    mock_config.exchange_id = 'binance'
    # Add any other attributes from Config that are accessed in DataHandler
    return mock_config

# Mock ccxt and yfinance for data fetching tests
@pytest.fixture
def mock_exchange_apis():
    """Mocks the ccxt and yfinance libraries."""
    with patch('src.data_handler.ccxt') as mock_ccxt_lib, \
         patch('src.data_handler.yf') as mock_yf_lib:
        
        # Configure mock ccxt exchange
        mock_exchange = MagicMock()
        mock_exchange.has = {'fetchOHLCV': True}
        mock_exchange.fetch_ohlcv.return_value = [
            [1678886400000, 100, 105, 98, 102, 1000],
            [1678890000000, 102, 108, 100, 106, 1200],
            [1678893600000, 106, 110, 104, 109, 1500],
        ]
        # Dynamically get the exchange class (e.g., binance) and mock it
        getattr(mock_ccxt_lib, 'binance').return_value = mock_exchange

        # Configure mock yfinance download
        mock_yf_lib.download.return_value = pd.DataFrame({
            'Open': [100, 102, 106],
            'High': [105, 108, 110],
            'Low': [98, 100, 104],
            'Close': [102, 106, 109],
            'Volume': [1000, 1200, 1500]
        }, index=pd.to_datetime(['2023-03-15 00:00:00', '2023-03-15 01:00:00', '2023-03-15 02:00:00']))

        yield mock_ccxt_lib, mock_yf_lib, mock_exchange

# Test successful data fetching from ccxt
def test_get_data_ccxt_success(mock_settings, mock_exchange_apis):
    mock_ccxt, _, mock_exchange = mock_exchange_apis
    data_handler = DataHandler(settings_obj=mock_settings)
    df = data_handler.get_data()

    assert df is not None
    assert not df.empty
    assert list(df.columns) == ['open', 'high', 'low', 'close', 'volume']
    assert len(df) == 3
    mock_exchange.fetch_ohlcv.assert_called_once_with('TEST/USDT', '1h')

# Test ccxt failure and yfinance fallback success
def test_get_data_yfinance_fallback(mock_settings, mock_exchange_apis):
    mock_ccxt, mock_yf, mock_exchange = mock_exchange_apis
    mock_exchange.fetch_ohlcv.side_effect = Exception("CCXT Error")

    data_handler = DataHandler(settings_obj=mock_settings)
    df = data_handler.get_data()

    assert df is not None
    assert not df.empty
    assert 'open' in df.columns
    assert len(df) == 3
    mock_yf.download.assert_called_once_with(tickers='TEST-USDT', period='7d', interval='1h')

# Test both sources fail
def test_get_data_all_fail(mock_settings, mock_exchange_apis):
    mock_ccxt, mock_yf, mock_exchange = mock_exchange_apis
    mock_exchange.fetch_ohlcv.side_effect = Exception("CCXT Error")
    mock_yf.download.return_value = pd.DataFrame() # Simulate empty df

    data_handler = DataHandler(settings_obj=mock_settings)
    df = data_handler.get_data()

    assert df is None

# Test data cleaning (forward fill and dropna)
def test_clean_data(mock_settings):
    data_handler = DataHandler(settings_obj=mock_settings)
    data = {
        'timestamp': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04']),
        'open': [10, 11, None, 13],
        'high': [12, 13, 14, 15],
        'low': [9, 10, 11, 12],
        'close': [11, 12, 13, 14],
        'volume': [100, 110, 120, None]
    }
    df = pd.DataFrame(data).set_index('timestamp')

    cleaned_df = data_handler._clean_data(df.copy())

    assert not cleaned_df.isnull().values.any()
    assert cleaned_df.loc['2023-01-03', 'open'] == 11
    assert cleaned_df.loc['2023-01-04', 'volume'] == 120
    assert len(cleaned_df) == 4
