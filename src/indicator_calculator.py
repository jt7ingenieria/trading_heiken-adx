
import pandas as pd
import pandas_ta as ta
from src.config import Config
from src.logger import logger

class IndicatorCalculator:
    """
    Calculates all technical indicators required for the strategy.
    It takes a DataFrame with OHLCV data and returns it with indicators added.
    """
    def __init__(self, settings_obj: Config):
        self.settings = settings_obj
        # Load all strategy parameters from the central config
        self.sma_length = self.settings.sma_length
        self.volume_sma_length = self.settings.volume_sma_length
        self.adx_length = self.settings.adx_length
        self.atr_length = self.settings.atr_length
        self.rsi_length = self.settings.rsi_length

    def add_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Adds all indicators to the given DataFrame.
        """
        logger.info("--- Calculating Indicators ---")
        
        # Calculate Heikin-Ashi candles
        ha_df = df.ta.ha(append=False) # Do not append directly, we'll concatenate later
        df = pd.concat([df, ha_df], axis=1)

        # Add standard indicators using pandas-ta
        df[f'SMA_{self.sma_length}'] = ta.sma(df['close'], length=self.sma_length)
        df[f'VOL_SMA_{self.volume_sma_length}'] = ta.sma(df['volume'], length=self.volume_sma_length)
        df[f'RSI_{self.rsi_length}'] = ta.rsi(df['close'], length=self.rsi_length)
        df[f'ATRr_{self.atr_length}'] = ta.atr(df['high'], df['low'], df['close'], length=self.atr_length)
        
        # Add ADX
        adx_data = ta.adx(df['high'], df['low'], df['close'], length=self.adx_length)
        if adx_data is not None and f"ADX_{self.adx_length}" in adx_data.columns:
            df[f"ADX_{self.adx_length}"] = adx_data[f"ADX_{self.adx_length}"]
        else:
            df[f"ADX_{self.adx_length}"] = pd.NA # Assign NA if ADX cannot be calculated

        # Clean up by dropping rows with NaN values created by the indicators
        df.dropna(inplace=True)
        
        logger.info("--- Indicator Calculation Complete ---")
        return df

if __name__ == '__main__':
    # Example of how to use the IndicatorCalculator
    import sys
    import os

    # Add the project root to the Python path
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.insert(0, project_root)

    from src.data_handler import DataHandler

    # 1. Get data first
    data_handler = DataHandler(symbol=self.settings.symbol, timeframe=self.settings.timeframe, exchange_id=self.settings.exchange_id)
    market_data = data_handler.get_data()

    if market_data is not None:
        # 2. Calculate indicators
        calculator = IndicatorCalculator(settings_obj=settings)
        data_with_indicators = calculator.add_all_indicators(market_data)

        logger.info("\n--- Data with Indicators ---")
        logger.info(data_with_indicators.head())
        logger.info("\nColumns:")
        logger.info(data_with_indicators.columns)
