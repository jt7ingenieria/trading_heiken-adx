
import ccxt
import yfinance as yf
import pandas as pd
import time
from typing import Optional
from src.config import Config
from src.logger import logger

class DataHandler:
    """
    Handles the fetching and cleaning of market data from different sources.
    Implements a failover mechanism between ccxt and yfinance.
    """
    def __init__(self, settings_obj: Config):
        self.settings = settings_obj
        self.symbol = self.settings.symbol
        self.timeframe = self.settings.timeframe
        self.exchange_id = self.settings.exchange_id
        self.exchange = getattr(ccxt, self.exchange_id)()

    def _fetch_ccxt(self, retries=3, delay=5) -> Optional[pd.DataFrame]:
        """Fetches OHLCV data from ccxt with retries."""
        for i in range(retries):
            try:
                logger.info(f"[DataHandler] Attempting to fetch data from ccxt (Attempt {i+1}/{retries})...")
                if not self.exchange.has['fetchOHLCV']:
                    logger.warning(f"[DataHandler] Exchange {self.exchange_id} does not support fetchOHLCV.")
                    return None
                
                ohlcv = self.exchange.fetch_ohlcv(self.symbol, self.timeframe)
                if not ohlcv:
                    logger.warning("[DataHandler] No data returned from ccxt.")
                    return None

                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                logger.info("[DataHandler] Successfully fetched data from ccxt.")
                return df
            except Exception as e:
                logger.error(f"[DataHandler] Error fetching from ccxt: {e}")
                if i < retries - 1:
                    logger.info(f"[DataHandler] Retrying in {delay} seconds...")
                    time.sleep(delay)
        return None

    def _fetch_yfinance(self) -> Optional[pd.DataFrame]:
        """Fetches OHLCV data from yfinance."""
        try:
            logger.info("[DataHandler] Attempting to fetch data from yfinance...")
            # yfinance uses a different symbol format (e.g., BTC-USDT)
            yf_symbol = self.symbol.replace('/', '-')
            df = yf.download(tickers=yf_symbol, period='7d', interval=self.timeframe)
            
            if df.empty:
                logger.warning("[DataHandler] No data returned from yfinance.")
                return None

            # Rename columns to be consistent
            df.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'}, inplace=True)
            logger.info("[DataHandler] Successfully fetched data from yfinance.")
            return df
        except Exception as e:
            logger.error(f"[DataHandler] Error fetching from yfinance: {e}")
            return None

    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cleans the DataFrame by handling missing values."""
        logger.info("[DataHandler] Cleaning data...")
        # Forward-fill missing values
        df.ffill(inplace=True)
        # Drop any remaining NaNs (e.g., at the beginning of the dataset)
        df.dropna(inplace=True)
        logger.info("[DataHandler] Data cleaning complete.")
        return df

    def get_data(self) -> Optional[pd.DataFrame]:
        """
        Main method to get data. Tries ccxt first, then yfinance as a fallback.
        Returns a cleaned DataFrame or None if all sources fail.
        """
        logger.info("--- Starting Data Fetching Process ---")
        data = self._fetch_ccxt()

        if data is None:
            logger.warning("[DataHandler] ccxt failed. Trying yfinance as a fallback.")
            data = self._fetch_yfinance()

        if data is not None and not data.empty:
            cleaned_data = self._clean_data(data)
            logger.info("--- Data Fetching Process Finished ---")
            return cleaned_data
        
        logger.error("[DataHandler] All data sources failed. Unable to fetch data.")
        logger.info("--- Data Fetching Process Finished ---")
        return None

if __name__ == '__main__':
    # Example of how to use the DataHandler
    # This part will only run when you execute this file directly
    
    # Load configuration from config.ini (for demonstration)
    import configparser
    config = configparser.ConfigParser()
    # Adjust the path to where the config.ini is located
    config.read('../config.ini') 

    settings = Config()
    handler = DataHandler(settings_obj=settings)
    market_data = handler.get_data()

    if market_data is not None:
        logger.info("\n--- Fetched Market Data ---")
        logger.info(market_data.head())
        logger.info("\nData Info:")
        market_data.info()
