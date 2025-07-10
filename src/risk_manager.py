from src.config import Config
from src.logger import logger

class RiskManager:
    """
    Handles position sizing and other risk management tasks.
    """
    def __init__(self, equity: float, settings_obj=None):
        if settings_obj is None:
            settings_obj = Config()
        if equity <= 0:
            raise ValueError("Initial equity must be positive.")
        self.equity = equity
        self.risk_per_trade_percentage = settings_obj.risk_per_trade

    def calculate_position_size(self, atr: float) -> float:
        """
        Calculates the position size based on the account equity, 
        risk percentage, and the current ATR.

        Args:
            atr (float): The current Average True Range value.

        Returns:
            float: The calculated quantity to trade.
        """
        if atr <= 0:
            logger.warning("[RiskManager] ATR is zero or negative. Cannot calculate position size.")
            return 0.0

        # Amount to risk in currency (e.g., USD)
        risk_amount = self.equity * (self.risk_per_trade_percentage / 100.0)

        # The stop loss distance is defined as 2 * ATR in the original strategy
        stop_loss_distance = 2 * atr

        # Calculate position size
        position_size = risk_amount / stop_loss_distance

        logger.info(f"[RiskManager] Equity: ${self.equity:.2f}, Risk Amount: ${risk_amount:.2f}, ATR: {atr:.4f}, Position Size: {position_size:.6f}")
        return position_size

if __name__ == '__main__':
    # Example of how to use the RiskManager
    import sys
    import os

    # Add the project root to the Python path
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.insert(0, project_root)

    from src.config import Config

    logger.info("--- Risk Manager Test ---")

    # Assume we have an account with $10,000 and the current ATR is 150.5
    initial_equity = 10000
    current_atr = 150.5

    settings_instance = Config()

    logger.info(f"Initial Equity: ${initial_equity}")
    logger.info(f"Risk per trade: {settings_instance.risk_per_trade}%")
    logger.info(f"Current ATR: {current_atr}")

    risk_manager = RiskManager(equity=initial_equity, settings_obj=settings_instance)
    size = risk_manager.calculate_position_size(atr=current_atr)

    logger.info(f"\nCalculated Position Size: {size}")