
import pytest
import os
from unittest.mock import patch
from src.config import Config

# Define the path to a dummy config.ini for testing
@pytest.fixture
def dummy_config_file(tmp_path):
    content = """
[TRADING]
symbol = TEST/USDT
timeframe = 1h
exchange = test_exchange
risk_per_trade = 0.5

[STRATEGY]
sma_length = 20
volume_sma_length = 10
volume_multiplier = 2.0
adx_length = 10
adx_threshold = 30
atr_length = 10
rsi_length = 10
take_profit_levels = 2.0,3.0
"""
    f = tmp_path / "config.ini"
    f.write_text(content)
    return str(f)

# Test case for Config class with mocked environment variables
@patch.dict(os.environ, {
    "TEST_EXCHANGE_API_KEY": "test_api_key",
    "TEST_EXCHANGE_API_SECRET": "test_api_secret",
    "TELEGRAM_BOT_TOKEN": "test_telegram_bot_token",
    "TELEGRAM_CHAT_ID": "test_telegram_chat_id"
})
def test_config_loading(dummy_config_file):
    """
    Tests that the Config class correctly loads settings from a config file
    and environment variables.
    """
    config_instance = Config(config_file=dummy_config_file)

    # Test TRADING section
    assert config_instance.symbol == "TEST/USDT"
    assert config_instance.timeframe == "1h"
    assert config_instance.exchange_id == "test_exchange"
    assert config_instance.risk_per_trade == 0.5

    # Test STRATEGY section
    assert config_instance.sma_length == 20
    assert config_instance.volume_sma_length == 10
    assert config_instance.volume_multiplier == 2.0
    assert config_instance.adx_length == 10
    assert config_instance.adx_threshold == 30
    assert config_instance.atr_length == 10
    assert config_instance.rsi_length == 10
    assert config_instance.take_profit_levels == [2.0, 3.0]

    # Test API keys from mocked .env
    assert config_instance.api_key == "test_api_key"
    assert config_instance.api_secret == "test_api_secret"
    

def test_config_file_not_found():
    """
    Tests that a FileNotFoundError is raised if the config file does not exist.
    """
    with pytest.raises(FileNotFoundError):
        Config(config_file="/nonexistent/path/config.ini")
