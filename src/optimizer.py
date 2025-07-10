
import os
import pandas as pd
from src.config import Config
from src.data_handler import DataHandler
from src.indicator_calculator import IndicatorCalculator
from src.backtester import Backtester
import numpy as np
from itertools import product
import os
from src.logger import logger

class Optimizer:
    """
    Optimizes strategy parameters by running multiple backtests.
    """
    def __init__(self, settings_obj: Config):
        """
        Initializes the Optimizer with a DataHandler and IndicatorCalculator.
        """
        self.settings = settings_obj
        self.data_handler = DataHandler(
            settings_obj=self.settings,
            mode='backtesting'
        )
        self.indicator_calculator = IndicatorCalculator(settings_obj=self.settings)
        self.output_dir = os.path.join(os.path.dirname(__file__), '..', 'results')
        os.makedirs(self.output_dir, exist_ok=True)

    def optimize_strategy(self) -> tuple[dict, float]:
        """
        Runs the optimization process over a predefined range of parameters.
        """
        logger.info("--- Starting Strategy Optimization ---")

        market_data = self.data_handler.get_data()

        # Define parameter ranges for optimization
        # These ranges should be carefully chosen based on the strategy and asset
        sma_lengths = [40, 50, 60]
        adx_thresholds = [20, 25, 30]
        # Add other parameters you want to optimize

        best_pnl = -np.inf
        best_params = {}
        all_results = []

        # Generate all combinations of parameters
        for sma_len, adx_thresh in itertools.product(sma_lengths, adx_thresholds):
            logger.info(f"Testing params: SMA_Length={sma_len}, ADX_Threshold={adx_thresh}")

            # Temporarily update settings for the current backtest
            self.settings.sma_length = sma_len
            self.settings.adx_threshold = adx_thresh
            # Update other settings as needed for optimization

            # Recalculate indicators with new settings
            data_with_indicators = self.indicator_calculator.add_all_indicators(market_data.copy())
            
            if data_with_indicators.empty:
                logger.warning(f"Skipping params (SMA_Length={sma_len}, ADX_Threshold={adx_thresh}) due to insufficient data after indicator calculation.")
                continue

            # Run backtest with current parameters
            backtester = Backtester(initial_equity=10000.0, settings_obj=self.settings)
            results = backtester.run_backtest(data_with_indicators)

            current_pnl = results.get('total_pnl', 0.0)
            
            param_results = {
                'sma_length': sma_len,
                'adx_threshold': adx_thresh,
                'total_pnl': current_pnl,
                'final_equity': results.get('final_equity', 10000.0),
                'num_trades': results.get('num_trades', 0),
                'win_rate': results.get('win_rate', 0.0),
                'profit_factor': results.get('profit_factor', 0.0),
                'max_drawdown': results.get('max_drawdown', 0.0),
                'sharpe_ratio': results.get('sharpe_ratio', 0.0),
                'sortino_ratio': results.get('sortino_ratio', 0.0),
                'calmar_ratio': results.get('calmar_ratio', 0.0)
            }
            all_results.append(param_results)

            if current_pnl > best_pnl:
                best_pnl = current_pnl
                best_params = {'sma_length': sma_len, 'adx_threshold': adx_thresh}
        
        # Save all optimization results to a CSV file
        if all_results:
            results_df = pd.DataFrame(all_results)
            output_file = os.path.join(self.output_dir, 'optimization_results.csv')
            results_df.to_csv(output_file, index=False)
            logger.info(f"Optimization results saved to {output_file}")

        logger.info("--- Strategy Optimization Complete ---")
        return best_params, best_pnl

if __name__ == '__main__':
    """
    Example usage of the Optimizer.
    """
    import sys
    import os

    # Add the project root to the Python path
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.insert(0, project_root)

    optimizer = Optimizer(settings_obj=settings)

    # Define ranges for parameters to optimize
    param_ranges = {
        'sma_length': [20, 50, 100],
        'adx_threshold': [20, 25, 30]
    }

    best_params_df = optimizer.optimize(param_ranges)

    if not best_params_df.empty:
        logger.info("\nBest Parameters Found:")
        logger.info(best_params_df.iloc[0])
