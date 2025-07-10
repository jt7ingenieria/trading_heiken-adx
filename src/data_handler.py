
import os
import datetime
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
    def __init__(self, settings_obj: Config, mode: str = 'backtesting'):
        self.settings = settings_obj
        self.symbol = self.settings.symbol
        self.timeframe = self.settings.timeframe
        self.exchange_id = self.settings.exchange_id
        self.mode = mode
        self.exchange = getattr(ccxt, self.exchange_id)()

    def _fetch_yfinance(self) -> Optional[pd.DataFrame]:
        """Fetches OHLCV data from yfinance."""
        logger.info("[DataHandler] Attempting to fetch data from yfinance...")
        try:
            # yfinance uses a different symbol format (e.g., BTC-USDT)
            yf_symbol = self.symbol.replace('/', '-')
            # For a year of data, yfinance 'period' can be '1y'
            df = yf.download(tickers=yf_symbol, period='1y', interval=self.timeframe)
            
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

    def get_data(self, since_days: int = 365) -> Optional[pd.DataFrame]:
        """
        Main method to get data. Dispatches based on mode and saves historical data to CSV.
        """
        logger.info("--- Starting Data Fetching Process ---")
        data = None

        if self.mode == 'backtesting':
            data = self._fetch_ccxt(since_days=since_days)
        elif self.mode == 'realtime':
            data = self._fetch_realtime()
        else:
            logger.error(f"[DataHandler] Invalid mode specified: {self.mode}")
            return None

        if data is None:
            logger.warning("[DataHandler] Primary data source failed. Trying fallback (yfinance).")
            data = self._fetch_yfinance()

        if data is not None and not data.empty:
            cleaned_data = self._clean_data(data)
            logger.info("--- Data Fetching Process Finished ---")
            
            # Save to CSV for backtesting mode
            if self.mode == 'backtesting':
                results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results')
                os.makedirs(results_dir, exist_ok=True)
                filename = f"{self.symbol.replace('/', '_')}_{self.timeframe}_historical.csv"
                filepath = os.path.join(results_dir, filename)
                cleaned_data.to_csv(filepath)
                logger.info(f"[DataHandler] Historical data saved to {filepath}")

            return cleaned_data
        
        logger.error("[DataHandler] All data sources failed. Unable to fetch data.")
        logger.info("--- Data Fetching Process Finished ---")
        return None

    def _fetch_ccxt(self, retries=3, delay=5, since_days: int = 365) -> Optional[pd.DataFrame]:
        """Fetches OHLCV data from ccxt with retries."""
        # Calculate timestamp for one year ago
        since_date = datetime.datetime.now() - datetime.timedelta(days=365)
        since_timestamp = self.exchange.parse8601(since_date.isoformat() + 'Z')

        all_ohlcv = []
        while True:
            try:
                logger.info(f"[DataHandler] Attempting to fetch data from ccxt (Attempt {len(all_ohlcv) + 1}/{retries})...")
                if not self.exchange.has['fetchOHLCV']:
                    logger.warning(f"[DataHandler] Exchange {self.exchange_id} does not support fetchOHLCV.")
                    return None
                
                # Fetch data in chunks
                ohlcv = self.exchange.fetch_ohlcv(self.symbol, self.timeframe, since=since_timestamp)
                if not ohlcv:
                    break # No more data

                all_ohlcv.extend(ohlcv)
                # Update since_timestamp to the timestamp of the last fetched candle + 1
                since_timestamp = ohlcv[-1][0] + 1

                # Break if we have enough data (e.g., more than a year's worth)
                # This is a rough estimate, adjust as needed
                if (all_ohlcv[-1][0] - all_ohlcv[0][0]) / (1000 * 60 * 60 * 24) > 365:
                    break

                time.sleep(self.exchange.rateLimit / 1000) # Respect rate limits

            except Exception as e:
                logger.error(f"[DataHandler] Error fetching from ccxt: {e}")
                if len(all_ohlcv) == 0 and retries > 0: # Only retry if no data fetched yet
                    retries -= 1
                    logger.info(f"[DataHandler] Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    break # Stop if retries exhausted or some data already fetched

        if not all_ohlcv:
            logger.warning("[DataHandler] No data returned from ccxt after all attempts.")
            return None

        df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        df.drop_duplicates(inplace=True) # Remove potential duplicates from multiple fetches
        df.sort_index(inplace=True) # Ensure chronological order
        logger.info("[DataHandler] Successfully fetched data from ccxt.")
        return df
