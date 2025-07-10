import configparser
import os
from dotenv import load_dotenv

# Build absolute paths from the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
env_path = os.path.join(project_root, '.env')
config_path = os.path.join(project_root, 'config.ini')

load_dotenv(dotenv_path=env_path)

class Config:
    """
    Handles loading and providing access to all configuration parameters
    from config.ini and environment variables.
    """
    def __init__(self, config_file=config_path):
        self.config = configparser.ConfigParser()
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        self.config.read(config_file)

    # --- Trading Parameters ---
    @property
    def symbol(self) -> str:
        """
        Returns the trading symbol (e.g., 'BTC/USDT').
        """
        return self.config.get('TRADING', 'symbol')

    @property
    def timeframe(self) -> str:
        """
        Returns the trading timeframe (e.g., '1h').
        """
        return self.config.get('TRADING', 'timeframe')

    @property
    def exchange_id(self) -> str:
        """
        Returns the exchange ID (e.g., 'binance').
        """
        return self.config.get('TRADING', 'exchange')

    @property
    def risk_per_trade(self) -> float:
        """
        Returns the percentage of equity to risk per trade.
        """
        return self.config.getfloat('TRADING', 'risk_per_trade')

    # --- Strategy Parameters ---
    @property
    def sma_length(self) -> int:
        """
        Returns the length for the Simple Moving Average (SMA) indicator.
        """
        return self.config.getint('STRATEGY', 'sma_length')

    @sma_length.setter
    def sma_length(self, value: int):
        self.config.set('STRATEGY', 'sma_length', str(value))

    @property
    def volume_sma_length(self) -> int:
        """
        Returns the length for the Volume Simple Moving Average (SMA) indicator.
        """
        return self.config.getint('STRATEGY', 'volume_sma_length')

    @volume_sma_length.setter
    def volume_sma_length(self, value: int):
        self.config.set('STRATEGY', 'volume_sma_length', str(value))

    @property
    def volume_multiplier(self) -> float:
        """
        Returns the multiplier for volume threshold calculation.
        """
        return self.config.getfloat('STRATEGY', 'volume_multiplier')

    @volume_multiplier.setter
    def volume_multiplier(self, value: float):
        self.config.set('STRATEGY', 'volume_multiplier', str(value))

    @property
    def adx_length(self) -> int:
        """
        Returns the length for the Average Directional Index (ADX) indicator.
        """
        return self.config.getint('STRATEGY', 'adx_length')

    @adx_length.setter
    def adx_length(self, value: int):
        self.config.set('STRATEGY', 'adx_length', str(value))

    @property
    def adx_threshold(self) -> int:
        """
        Returns the threshold for the ADX indicator to confirm trend strength.
        """
        return self.config.getint('STRATEGY', 'adx_threshold')

    @adx_threshold.setter
    def adx_threshold(self, value: int):
        self.config.set('STRATEGY', 'adx_threshold', str(value))

    @property
    def atr_length(self) -> int:
        """
        Returns the length for the Average True Range (ATR) indicator.
        """
        return self.config.getint('STRATEGY', 'atr_length')

    @atr_length.setter
    def atr_length(self, value: int):
        self.config.set('STRATEGY', 'atr_length', str(value))

    @property
    def rsi_length(self) -> int:
        """
        Returns the length for the Relative Strength Index (RSI) indicator.
        """
        return self.config.getint('STRATEGY', 'rsi_length')

    @rsi_length.setter
    def rsi_length(self, value: int):
        self.config.set('STRATEGY', 'rsi_length', str(value))

    @property
    def take_profit_levels(self) -> list[float]:
        """
        Returns a list of multipliers for calculating multiple take profit levels.
        """
        tp_levels_str = self.config.get('STRATEGY', 'take_profit_levels', fallback="").strip()
        if tp_levels_str:
            return [float(x.strip()) for x in tp_levels_str.split(',')]
        return []

    # --- API Keys ---
    @property
    def api_key(self) -> str:
        """
        Returns the API key for the selected exchange.
        """
        return os.getenv(f"{self.exchange_id.upper()}_API_KEY")

    @property
    def api_secret(self) -> str:
        """
        Returns the API secret for the selected exchange.
        """
        return os.getenv(f"{self.exchange_id.upper()}_API_SECRET")

    # --- Telegram Notifications ---
    @property
    def telegram_bot_token(self) -> str:
        """
        Returns the Telegram bot token for notifications.
        """
        return os.getenv("TELEGRAM_BOT_TOKEN")

    @property
    def telegram_chat_id(self) -> str:
        """
        Returns the Telegram chat ID for notifications.
        """
        return os.getenv("TELEGRAM_CHAT_ID")

if __name__ == '__main__':
    # Create a single, globally accessible instance of the configuration
    # Any part of the bot can import `settings` to get the configuration.
    settings = Config()

    # Example of how to use the Config object
    from src.logger import logger
    logger.info("--- Configuration Loaded ---")
    logger.info(f"Symbol: {settings.symbol}")
    logger.info(f"Timeframe: {settings.timeframe}")
    logger.info(f"Risk per Trade: {settings.risk_per_trade}%")
    logger.info(f"SMA Length: {settings.sma_length}")
    logger.info(f"ADX Threshold: {settings.adx_threshold}")
    logger.info(f"Take Profit Levels: {settings.take_profit_levels}")
    logger.info(f"API Key Loaded: {'Yes' if settings.api_key else 'No'}")
    logger.info(f"Telegram Bot Token Loaded: {'Yes' if settings.telegram_bot_token else 'No'}")
    logger.info(f"Telegram Chat ID Loaded: {'Yes' if settings.telegram_chat_id else 'No'}")