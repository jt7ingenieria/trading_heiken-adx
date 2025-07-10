
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from src.config import Config
from src.strategy import Strategy
from src.risk_manager import RiskManager
from src.logger import logger
from src.notifier import Notifier

# Suppress FutureWarning messages from pandas
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

class Backtester:
    """
    Simulates the trading strategy on historical data and calculates performance metrics.
    """
    def __init__(self, initial_equity: float = 10000.0, settings_obj: Config = None):
        self.initial_equity = initial_equity
        self.equity_curve = pd.Series(dtype=float)
        self.trades = [] # List of dictionaries, each representing a trade
        self.settings = settings_obj if settings_obj else Config()
        self.strategy = Strategy(settings_obj=self.settings)
        self.risk_manager = RiskManager(equity=initial_equity, settings_obj=self.settings)
        self.current_position = {'type': None, 'entry_price': 0.0, 'quantity': 0.0, 'entry_date': None, 'take_profit_levels': [], 'stop_loss': 0.0}
        self.notifier = Notifier(settings_obj=self.settings)

    def run_backtest(self, data: pd.DataFrame) -> dict:
        """
        Runs the backtest simulation.

        Args:
            data (pd.DataFrame): Historical OHLCV data with all indicators calculated.

        Returns:
            dict: Performance metrics and trade history.
        """
        logger.info("--- Running Backtest Simulation ---")
        self.equity_curve = pd.Series(index=data.index, dtype=float)
        self.equity_curve.iloc[0] = self.initial_equity

        for i in range(1, len(data)):
            current_candle = data.iloc[i]
            prev_candle = data.iloc[i-1]
            current_equity = self.equity_curve.iloc[i-1]

            # Update RiskManager equity for accurate position sizing
            self.risk_manager.equity = current_equity

            # --- Handle existing position ---
            if self.current_position['type'] is not None:
                # Update trailing stop and check for exits
                if self.current_position['type'] == 'long':
                    # Update highest high for trailing stop
                    self.current_position['highest_high'] = max(self.current_position.get('highest_high', -np.inf), current_candle['high'])
                    self.current_position['stop_loss'] = self.current_position['highest_high'] - 2 * current_candle[f'ATRr_{self.settings.atr_length}']

                    # Check exit conditions
                    if current_candle['low'] <= self.current_position['stop_loss']:
                        exit_price = self.current_position['stop_loss']
                        pnl = (exit_price - self.current_position['entry_price']) * self.current_position['quantity']
                        self.trades.append({'entry_date': self.current_position['entry_date'], 'exit_date': current_candle.name, 
                                            'type': 'long', 'entry_price': self.current_position['entry_price'], 
                                            'exit_price': exit_price, 'pnl': pnl, 'reason': 'SL'})
                        self.notifier.send_telegram_message(f"Long position closed by SL at {exit_price:.2f}. PnL: {pnl:.2f}")
                        self.current_position = {'type': None, 'entry_price': 0.0, 'quantity': 0.0, 'entry_date': None, 'take_profit': 0.0, 'stop_loss': 0.0}
                    elif self.current_position['take_profit_levels']:
                        # Iterate through take profit levels
                        for tp_level_idx, tp_price in enumerate(self.current_position['take_profit_levels']):
                            if current_candle['high'] >= tp_price:
                                # Close a portion of the position (e.g., 50%)
                                partial_quantity = self.current_position['quantity'] * 0.5
                                pnl = (tp_price - self.current_position['entry_price']) * partial_quantity
                                self.trades.append({'entry_date': self.current_position['entry_date'], 'exit_date': current_candle.name,
                                                    'type': 'long', 'entry_price': self.current_position['entry_price'],
                                                    'exit_price': tp_price, 'pnl': pnl, 'reason': f'TP{tp_level_idx + 1}'})
                                self.notifier.send_telegram_message(f"Long position partial TP{tp_level_idx + 1} hit at {tp_price:.2f}. PnL: {pnl:.2f}")
                                
                                # Adjust remaining quantity
                                self.current_position['quantity'] -= partial_quantity
                                
                                # Remove the hit TP level
                                self.current_position['take_profit_levels'].pop(tp_level_idx)
                                
                                # If no quantity left, close the position
                                if self.current_position['quantity'] <= 0.000001: # Use a small epsilon for float comparison
                                    self.current_position = {'type': None, 'entry_price': 0.0, 'quantity': 0.0, 'entry_date': None, 'take_profit_levels': [], 'stop_loss': 0.0}
                                    break # Exit TP loop if position is fully closed

                elif self.current_position['type'] == 'short':
                    # Update lowest low for trailing stop
                    self.current_position['lowest_low'] = min(self.current_position.get('lowest_low', np.inf), current_candle['low'])
                    self.current_position['stop_loss'] = self.current_position['lowest_low'] + 2 * current_candle[f'ATRr_{self.settings.atr_length}']

                    # Check exit conditions
                    if current_candle['high'] >= self.current_position['stop_loss']:
                        exit_price = self.current_position['stop_loss']
                        pnl = (self.current_position['entry_price'] - exit_price) * self.current_position['quantity']
                        self.trades.append({'entry_date': self.current_position['entry_date'], 'exit_date': current_candle.name, 
                                            'type': 'short', 'entry_price': self.current_position['entry_price'], 
                                            'exit_price': exit_price, 'pnl': pnl, 'reason': 'SL'})
                        self.notifier.send_telegram_message(f"Short position closed by SL at {exit_price:.2f}. PnL: {pnl:.2f}")
                        self.current_position = {'type': None, 'entry_price': 0.0, 'quantity': 0.0, 'entry_date': None, 'take_profit': 0.0, 'stop_loss': 0.0}
                    elif self.current_position['take_profit_levels']:
                        # Iterate through take profit levels
                        for tp_level_idx, tp_price in enumerate(self.current_position['take_profit_levels']):
                            if current_candle['low'] <= tp_price:
                                # Close a portion of the position (e.g., 50%)
                                partial_quantity = self.current_position['quantity'] * 0.5
                                pnl = (self.current_position['entry_price'] - tp_price) * partial_quantity
                                self.trades.append({'entry_date': self.current_position['entry_date'], 'exit_date': current_candle.name, 
                                                    'type': 'short', 'entry_price': self.current_position['entry_price'], 
                                                    'exit_price': tp_price, 'pnl': pnl, 'reason': f'TP{tp_level_idx + 1}'})
                                self.notifier.send_telegram_message(f"Short position partial TP{tp_level_idx + 1} hit at {tp_price:.2f}. PnL: {pnl:.2f}")
                                
                                # Adjust remaining quantity
                                self.current_position['quantity'] -= partial_quantity
                                
                                # Remove the hit TP level
                                self.current_position['take_profit_levels'].pop(tp_level_idx)
                                
                                # If no quantity left, close the position
                                if self.current_position['quantity'] <= 0.000001: # Use a small epsilon for float comparison
                                    self.current_position = {'type': None, 'entry_price': 0.0, 'quantity': 0.0, 'entry_date': None, 'take_profit_levels': [], 'stop_loss': 0.0}
                                    break # Exit TP loop if position is fully closed

            # --- Check for new entry signals ---
            if self.current_position['type'] is None:
                trade_params = self.strategy.get_trade_parameters(data.iloc[:i+1]) # Pass data up to current candle

                if trade_params['signal_type']:
                    # Calculate position size based on current equity and ATR
                    current_atr = current_candle[f'ATRr_{self.settings.atr_length}']
                    if current_atr > 0:
                        quantity = self.risk_manager.calculate_position_size(atr=current_atr)
                        if quantity > 0:
                            self.current_position = {
                                'type': trade_params['signal_type'],
                                'entry_price': trade_params['entry_price'],
                                'quantity': quantity,
                                'entry_date': current_candle.name,
                                'take_profit_levels': trade_params['take_profit_levels'],
                                'stop_loss': trade_params['stop_loss'],
                                'highest_high': current_candle['high'] if trade_params['signal_type'] == 'long' else -np.inf,
                                'lowest_low': current_candle['low'] if trade_params['signal_type'] == 'short' else np.inf
                            }
                            logger.info(f"[Backtester] Entered {self.current_position['type']} at {self.current_position['entry_price']:.2f} with qty {self.current_position['quantity']:.6f}")
                            self.notifier.send_telegram_message(f"Entered {self.current_position['type']} at {self.current_position['entry_price']:.2f} with qty {self.current_position['quantity']:.6f}")

            # Update equity curve
            self.equity_curve.iloc[i] = current_equity + (self.trades[-1]['pnl'] if self.trades and self.trades[-1]['exit_date'] == current_candle.name else 0)

        # If still in position at the end, close it at the last candle's close price
        if self.current_position['type'] is not None:
            exit_price = data.iloc[-1]['close']
            pnl = (exit_price - self.current_position['entry_price']) * self.current_position['quantity'] if self.current_position['type'] == 'long' else (self.current_position['entry_price'] - exit_price) * self.current_position['quantity']
            self.trades.append({'entry_date': self.current_position['entry_date'], 'exit_date': data.iloc[-1].name, 
                                'type': self.current_position['type'], 'entry_price': self.current_position['entry_price'], 
                                'exit_price': exit_price, 'pnl': pnl, 'reason': 'EOD'})
            self.equity_curve.iloc[-1] = self.equity_curve.iloc[-1] + pnl
            self.notifier.send_telegram_message(f"Position closed at EOD. Type: {self.current_position['type']}, PnL: {pnl:.2f}")

        metrics = self._calculate_metrics()
        metrics['equity_curve'] = self.equity_curve.to_json()
        return metrics

    def _calculate_metrics(self) -> dict:
        """
        Calculates various performance metrics from the backtest results.
        """
        metrics = {}
        total_pnl = sum(trade['pnl'] for trade in self.trades)
        metrics['total_pnl'] = total_pnl
        metrics['final_equity'] = self.initial_equity + total_pnl
        metrics['num_trades'] = len(self.trades)

        if len(self.trades) > 0:
            winning_trades = [t for t in self.trades if t['pnl'] > 0]
            losing_trades = [t for t in self.trades if t['pnl'] <= 0]
            
            metrics['win_rate'] = len(winning_trades) / len(self.trades) * 100
            metrics['avg_win'] = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
            metrics['avg_loss'] = np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0
            metrics['profit_factor'] = abs(sum(t['pnl'] for t in winning_trades) / sum(t['pnl'] for t in losing_trades)) if losing_trades and sum(t['pnl'] for t in losing_trades) != 0 else np.inf

        # Calculate drawdown
        if not self.equity_curve.empty:
            roll_max = self.equity_curve.expanding(min_periods=1).max()
            daily_drawdown = self.equity_curve / roll_max - 1.0
            max_drawdown = daily_drawdown.min()
            metrics['max_drawdown'] = max_drawdown

            # Calculate Sharpe Ratio
            returns = self.equity_curve.pct_change().dropna()
            if not returns.empty:
                # Assuming a risk-free rate of 0 for simplicity, or it can be a parameter
                # Annualized Sharpe Ratio = (Mean Daily Return - Risk-Free Rate) / Std Dev of Daily Returns * sqrt(Trading Days)
                # For daily data, trading days = 252
                annualized_returns = returns.mean() * 252
                annualized_std = returns.std() * np.sqrt(252)
                metrics['sharpe_ratio'] = annualized_returns / annualized_std if annualized_std != 0 else 0

                # Calculate Sortino Ratio
                # Downside deviation: standard deviation of negative returns
                downside_returns = returns[returns < 0]
                if not downside_returns.empty:
                    downside_std = downside_returns.std() * np.sqrt(252)
                    metrics['sortino_ratio'] = annualized_returns / downside_std if downside_std != 0 else 0
                else:
                    metrics['sortino_ratio'] = np.inf # No downside risk

            # Calculate Calmar Ratio
            # Calmar Ratio = Annualized Return / Max Drawdown (absolute value)
            if metrics['max_drawdown'] != 0:
                metrics['calmar_ratio'] = annualized_returns / abs(metrics['max_drawdown']) if 'annualized_returns' in locals() else 0
            else:
                metrics['calmar_ratio'] = np.inf # No drawdown

        logger.info("--- Backtest Metrics Calculated ---")
        return metrics

    def plot_results(self, data: pd.DataFrame):
        """
        Plots the equity curve and trade entries/exits.
        """
        if self.equity_curve.empty:
            logger.warning("[Backtester] No equity curve to plot. Run backtest first.")
            return

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

        # Plot price and SMA
        ax1.plot(data.index, data['close'], label='Close Price', color='blue')
        ax1.plot(data.index, data[f'SMA_{self.settings.sma_length}'], label=f'SMA {self.settings.sma_length}', color='orange')
        ax1.set_ylabel('Price')
        ax1.legend()
        ax1.set_title(f'{self.settings.symbol} Trading Strategy Backtest')

        # Plot equity curve
        ax2.plot(self.equity_curve.index, self.equity_curve, label='Equity Curve', color='green')
        ax2.set_xlabel('Date')
        ax2.set_ylabel('Equity')
        ax2.legend()

        # Mark trades on the price plot
        for trade in self.trades:
            entry_date = trade['entry_date']
            exit_date = trade['exit_date']
            entry_price = trade['entry_price']
            exit_price = trade['exit_price']
            trade_type = trade['type']

            color = 'green' if trade_type == 'long' else 'red'
            marker = '^' if trade_type == 'long' else 'v'

            ax1.plot(entry_date, entry_price, marker=marker, color=color, markersize=10, label=f'{trade_type} Entry')
            ax1.plot(exit_date, exit_price, marker='o', color='black', markersize=8, label=f'{trade_type} Exit')

        plt.tight_layout()
        plt.show()

if __name__ == '__main__':
    # Example of how to use the Backtester
    import sys
    import os

    # Add the project root to the Python path
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.insert(0, project_root)

    from src.data_handler import DataHandler
    from src.indicator_calculator import IndicatorCalculator

    logger.info("--- Backtester Module Test ---")

    # 1. Get data
    data_handler = DataHandler(symbol=self.settings.symbol, timeframe=self.settings.timeframe, exchange_id=self.settings.exchange_id)
    market_data = data_handler.get_data()

    if market_data is None or market_data.empty:
        logger.error("Failed to retrieve data for backtesting. Exiting.")
    else:
        # 2. Calculate indicators
        indicator_calculator = IndicatorCalculator()
        data_with_indicators = indicator_calculator.add_all_indicators(market_data)

        # 3. Run backtest
        backtester = Backtester(initial_equity=10000.0, settings_obj=settings)
        results = backtester.run_backtest(data_with_indicators)

        logger.info("\n--- Backtest Results ---")
        for key, value in results.items():
            if isinstance(value, (int, float)):
                logger.info(f"{key.replace('_', ' ').title()}: {value:.2f}")
            else:
                logger.info(f"{key.replace('_', ' ').title()}: {value}")

        # 4. Plot results
        backtester.plot_results(data_with_indicators)
