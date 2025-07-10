import pytest
from unittest.mock import MagicMock, patch
from src.execution_handler import ExecutionHandler
from src.config import Config
import ccxt

# Mock settings for ExecutionHandler initialization
@pytest.fixture
def mock_settings():
    """Provides a mock configuration object for tests."""
    mock_config = MagicMock(spec=Config)
    mock_config.exchange_id = 'binance'
    mock_config.symbol = 'BTC/USDT'
    mock_config.api_key = 'test_api_key'
    mock_config.api_secret = 'test_api_secret'
    # These are not used by ExecutionHandler but are part of the Config spec
    mock_config.telegram_token = 'test_telegram_token'
    mock_config.telegram_chat_id = 'test_telegram_chat_id'
    return mock_config

# Mock ccxt exchange for ExecutionHandler tests
@pytest.fixture
def mock_exchange_api():
    """Mocks the ccxt library and returns a mock exchange object."""
    with patch('src.execution_handler.ccxt') as mock_ccxt_lib:
        mock_exchange = MagicMock()
        mock_exchange.set_sandbox_mode.return_value = None
        mock_exchange.load_markets.return_value = None
        mock_exchange.urls = {'test': 'https://testnet.binance.com'}
        mock_exchange.create_market_buy_order.return_value = {'id': '123', 'status': 'open'}
        mock_exchange.create_limit_sell_order.return_value = {'id': '456', 'status': 'open'}
        mock_exchange.create_market_order.return_value = {'id': '789', 'status': 'open'}
        mock_exchange.create_limit_order.return_value = {'id': '101', 'status': 'open'}
        # The class name (e.g., binance) is dynamically fetched from settings
        getattr(mock_ccxt_lib, 'binance').return_value = mock_exchange
        yield mock_exchange

def test_execution_handler_connection(mock_settings, mock_exchange_api):
    """Tests successful connection and initialization of the handler."""
    handler = ExecutionHandler(settings_obj=mock_settings, sandbox=True)
    assert handler.exchange is not None
    mock_exchange_api.set_sandbox_mode.assert_called_once_with(True)
    mock_exchange_api.load_markets.assert_called_once()

def test_place_market_order_buy(mock_settings, mock_exchange_api):
    """Tests placing a market buy order."""
    handler = ExecutionHandler(settings_obj=mock_settings, sandbox=True)
    mock_exchange_api.create_market_order.return_value = {'id': '123', 'status': 'open'}
    
    order_result = handler.place_order(symbol='BTC/USDT', order_type='market', side='buy', amount=0.001)
    
    mock_exchange_api.create_market_order.assert_called_once_with('BTC/USDT', 'buy', 0.001)
    assert order_result['status'] == 'open'

def test_place_limit_order_sell(mock_settings, mock_exchange_api):
    """Tests placing a limit sell order."""
    handler = ExecutionHandler(settings_obj=mock_settings, sandbox=True)
    mock_exchange_api.create_limit_order.return_value = {'id': '456', 'status': 'open'}
    
    order_result = handler.place_order(symbol='BTC/USDT', order_type='limit', side='sell', amount=0.001, price=30000)
    
    mock_exchange_api.create_limit_order.assert_called_once_with('BTC/USDT', 'sell', 0.001, 30000)
    assert order_result['status'] == 'open'

def test_get_balance(mock_settings, mock_exchange_api):
    """Tests fetching account balance."""
    handler = ExecutionHandler(settings_obj=mock_settings, sandbox=True)
    mock_exchange_api.fetch_balance.return_value = {'free': {'USDT': 1000, 'BTC': 0.5}}
    
    usdt_balance = handler.get_balance('USDT')
    btc_balance = handler.get_balance('BTC')

    assert mock_exchange_api.fetch_balance.call_count == 2
    assert usdt_balance == 1000
    assert btc_balance == 0.5

@patch('src.execution_handler.ccxt.binance', side_effect=ccxt.ExchangeError("Connection Failed"))
def test_connection_failure(mock_binance_class, mock_settings):
    """Tests that handler.exchange is None if connection fails."""
    handler = ExecutionHandler(settings_obj=mock_settings)
    assert handler.exchange is None

@patch('src.execution_handler.ccxt.binance', side_effect=ccxt.ExchangeError("Connection Failed"))
def test_place_order_not_connected(mock_binance_class, mock_settings):
    """Tests that placing an order fails if not connected."""
    handler = ExecutionHandler(settings_obj=mock_settings)
    order_result = handler.place_order(symbol='BTC/USDT', order_type='market', side='buy', amount=0.001)
    assert order_result == {'status': 'failed', 'info': 'Not connected'}

@patch('src.execution_handler.ccxt.binance', side_effect=ccxt.ExchangeError("Connection Failed"))
def test_get_balance_not_connected(mock_binance_class, mock_settings):
    """Tests that getting balance fails if not connected."""
    handler = ExecutionHandler(settings_obj=mock_settings)
    balance = handler.get_balance('USDT')
    assert balance is None
