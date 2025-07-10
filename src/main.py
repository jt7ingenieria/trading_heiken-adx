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

def run_backtest_pipeline(settings_obj: Config):
    """
    Runs the full backtesting pipeline: data fetching, indicator calculation,
    and backtesting.
    """
    logger.info("--- Starting Backtest Pipeline ---")
    notifier = Notifier(settings_obj=settings_obj)
    notifier.send_telegram_message("Backtest pipeline started.")

    try:
        # 1. Get data
        data_handler = DataHandler(
            settings_obj=settings_obj,
            mode='backtesting'
        )
        market_data = data_handler.get_data()

        if market_data is None or market_data.empty:
            logger.error("Failed to retrieve data. Exiting backtest pipeline.")
            notifier.send_telegram_message("Backtest pipeline failed: Could not retrieve data.")
            return

        # 2. Calculate indicators
        indicator_calculator = IndicatorCalculator(settings_obj=settings_obj)
        data_with_indicators = indicator_calculator.add_all_indicators(market_data)

        if data_with_indicators.empty:
            logger.error("No data after indicator calculation. Exiting backtest pipeline.")
            notifier.send_telegram_message("Backtest pipeline failed: No data after indicator calculation.")
            return

        # 3. Run backtest
        backtester = Backtester(initial_equity=10000.0, settings_obj=settings_obj)
        results = backtester.run_backtest(data_with_indicators)

        logger.info("\n--- Backtest Results ---")
        for key, value in results.items():
            if isinstance(value, (int, float)):
                logger.info(f"{key.replace('_', ' ').title()}: {value:.2f}")
            else:
                logger.info(f"{key.replace('_', ' ').title()}: {value}")
        
        notifier.send_telegram_message(f"Backtest pipeline finished. Total PnL: {results['total_pnl']:.2f}, Final Equity: {results['final_equity']:.2f}")

        # 4. Save backtest results to JSON for dashboard
        import json
        results_dir = os.path.join(project_root, 'results')
        os.makedirs(results_dir, exist_ok=True)
        backtest_results_path = os.path.join(results_dir, 'backtest_results.json')
        with open(backtest_results_path, 'w') as f:
            json.dump(results, f, indent=4)
        logger.info(f"Backtest results saved to {backtest_results_path}")

        # 5. Plot results (optional, for local execution)
        # backtester.plot_results(data_with_indicators)

    except Exception as e:
        logger.error(f"An error occurred during the backtest pipeline: {e}")
        notifier.send_telegram_message(f"Backtest pipeline encountered an error: {e}")

def run_optimization_pipeline(settings_obj: Config):
    """
    Runs the optimization pipeline to find the best strategy parameters.
    """
    logger.info("--- Starting Optimizer Pipeline ---")
    notifier = Notifier(settings_obj=settings_obj)
    notifier.send_telegram_message("Optimizer pipeline started.")

    try:
        optimizer = Optimizer(settings_obj=settings_obj)
        best_params, best_pnl = optimizer.optimize_strategy()

        if best_params:
            logger.info("\n--- Optimization Results ---")
            logger.info(f"Best Parameters: {best_params}")
            logger.info(f"Best PnL: {best_pnl:.2f}")
            notifier.send_telegram_message(f"Optimizer pipeline finished. Best PnL: {best_pnl:.2f} with parameters: {best_params}")
        else:
            logger.warning("Optimizer could not find best parameters.")
            notifier.send_telegram_message("Optimizer pipeline finished: Could not find best parameters.")

    except Exception as e:
        logger.error(f"An error occurred during the optimizer pipeline: {e}")
        notifier.send_telegram_message(f"Optimizer pipeline encountered an error: {e}")

if __name__ == '__main__':
    # Initialize logging
    logger.info("--- Application Started ---")

    # Create a single instance of Config
    settings = Config()

    # Example of running the backtest pipeline
    run_backtest_pipeline(settings)

    # Example of running the optimizer pipeline
    run_optimization_pipeline(settings)

    logger.info("--- Application Finished ---")