
import pandas as pd
from src.config import Config
from src.data_handler import DataHandler
from src.indicator_calculator import IndicatorCalculator
from src.backtester import Backtester
import itertools
import os
from src.logger import logger

class Optimizer:
    """
    Optimizes strategy parameters by running multiple backtests.
    """
    def __init__(self):
        """
        Initializes the Optimizer with a DataHandler and IndicatorCalculator.
        """
        self.settings = Config()
        self.data_handler = DataHandler(
            symbol=self.settings.symbol,
            timeframe=self.settings.timeframe,
            exchange_id=self.settings.exchange_id
        )
        self.indicator_calculator = IndicatorCalculator()

    def optimize(self, param_ranges: dict) -> pd.DataFrame:
        """
        Runs backtests for all combinations of parameters and returns the best ones.

        Args:
            param_ranges (dict): A dictionary where keys are parameter names
                                 and values are lists of possible values for that parameter.
                                 Example: {'sma_length': [10, 20, 30], 'adx_threshold': [20, 25]}

        Returns:
            pd.DataFrame: A DataFrame with results for each parameter combination,
                          sorted by a chosen metric (e.g., total_pnl).
        """
        logger.info("--- Starting Optimization Process ---")
        
        # Get historical data once
        market_data = self.data_handler.get_data()
        if market_data is None or market_data.empty:
            logger.error("[Optimizer] Failed to retrieve data for optimization. Exiting.")
            return pd.DataFrame()

        # Generate all combinations of parameters
        keys = param_ranges.keys()
        values = param_ranges.values()
        parameter_combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]

        results = []
        for i, params in enumerate(parameter_combinations):
            logger.info(f"[Optimizer] Running backtest for combination {i+1}/{len(parameter_combinations)}: {params}")
            
            # Temporarily override settings for this backtest
            original_settings = {attr: getattr(self.settings, attr) for attr in params.keys()}
            for param, value in params.items():
                setattr(self.settings, param, value)

            # Recalculate indicators with new parameters
            data_with_indicators = self.indicator_calculator.add_all_indicators(market_data.copy())
            
            # Run backtest
            backtester = Backtester(initial_equity=10000.0)
            backtest_results = backtester.run_backtest(data_with_indicators.copy())
            
            # Store results
            combined_results = {**params, **backtest_results}
            results.append(combined_results)

            # Restore original settings
            for param, value in original_settings.items():
                setattr(self.settings, param, value)

        results_df = pd.DataFrame(results)
        if not results_df.empty:
            results_df.sort_values(by='total_pnl', ascending=False, inplace=True)
            
            # Save results to CSV
            results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results')
            if not os.path.exists(results_dir):
                os.makedirs(results_dir)
            results_path = os.path.join(results_dir, 'optimization_results.csv')
            results_df.to_csv(results_path, index=False)
            logger.info(f"Optimization results saved to {results_path}")

            logger.info("--- Optimization Process Complete ---")
            logger.info("\n--- Top Optimization Results ---")
            logger.info(results_df.head())
        else:
            logger.warning("No optimization results generated.")

        return results_df

if __name__ == '__main__':
    """
    Example usage of the Optimizer.
    """
    import sys
    import os

    # Add the project root to the Python path
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.insert(0, project_root)

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
