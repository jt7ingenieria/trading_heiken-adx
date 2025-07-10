"""Main module to run the trading bot's backtesting and optimization pipelines."""

import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.config import Config
from src.data_handler import DataHandler
from src.indicator_calculator import IndicatorCalculator
from src.backtester import Backtester
from src.optimizer import Optimizer
from src.notifier import Notifier
from src.logger import logger

def run_backtest_pipeline():
    """
    Runs the full backtesting pipeline with improved error handling.
    """
    logger.info("--- Starting Bot: Backtesting Pipeline ---")
    settings_instance = Config()
    notifier = Notifier(settings_instance)
    
    try:
        # 1. Data Handling
                settings_instance = Config()
    logger.info(f"Loading data for {settings_instance.symbol} on {settings_instance.exchange_id} with timeframe {settings_instance.timeframe}")
        notifier.send_telegram_message(f"Starting backtest for {settings_instance.symbol} on {settings_instance.exchange_id} with timeframe {settings_instance.timeframe}")
        data_handler = DataHandler(
            symbol=settings_instance.symbol,
            timeframe=settings_instance.timeframe,
            exchange_id=settings_instance.exchange_id
        )
        market_data = data_handler.get_data()

                if market_data is None or market_data.empty:
            logger.error("[Main] Failed to retrieve data for backtesting. Exiting.")
            return

        logger.info("[Main] Successfully retrieved data.")

        # 2. Indicator Calculation
        indicator_calculator = IndicatorCalculator()
        data_with_indicators = indicator_calculator.add_all_indicators(market_data)

        logger.info("[Main] Successfully calculated indicators.")

        # 3. Run Backtest
        backtester = Backtester(initial_equity=10000.0)
        results = backtester.run_backtest(data_with_indicators.copy())

                logger.info("--- Backtest Results ---")
        for key, value in results.items():
            if isinstance(value, (int, float)):
                logger.info(f"{key.replace('_', ' ').title()}: {value:.2f}")
            else:
                logger.info(f"{key.replace('_', ' ').title()}: {value}")

        # 4. Plot results
        backtester.plot_results(data_with_indicators)

        except Exception as e:
        logger.error(f"
[Main] An unexpected error occurred during the backtest pipeline: {e}")
        # Here you could add more specific error handling for ccxt or other libraries
    
    finally:
        logger.info("--- Backtesting Pipeline Complete ---")

def run_optimization_pipeline():
    """
    Runs the optimization pipeline.
    """
        logger.info("--- Starting Bot: Optimization Pipeline ---")
    settings_instance = Config()
    notifier = Notifier(settings_instance)
    notifier.send_telegram_message("Starting optimization pipeline.")

    settings_instance = Config()
    optimizer = Optimizer()

    # Define ranges for parameters to optimize
    param_ranges = {
        'sma_length': [20, 50, 100],
        'adx_threshold': [20, 25, 30]
    }

    best_params_df = optimizer.optimize(param_ranges)

        if not best_params_df.empty:
        logger.info("\nBest Parameters Found:")
        logger.info(best_params_df.iloc[0])
    else:
        logger.warning("\nNo optimization results generated.")

    logger.info("--- Optimization Pipeline Complete ---")

if __name__ == "__main__":
    # You can choose which pipeline to run here
    # run_backtest_pipeline()
    run_optimization_pipeline()