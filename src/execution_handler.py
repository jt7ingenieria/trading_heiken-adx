
import ccxt
from typing import Optional
from src.config import Config
from src.logger import logger

class ExecutionHandler:
    """
    Handles the execution of trades (placing orders) on an exchange.
    Initially, this will be a simulated execution.
    """
    def __init__(self, settings_obj: Config, sandbox: bool = True):
        self.settings = settings_obj
        self.exchange_id = self.settings.exchange_id
        self.api_key = self.settings.api_key
        self.api_secret = self.settings.api_secret
        self.sandbox = sandbox
        self.exchange = None
        self._connect_exchange()

    def _connect_exchange(self):
        """
        Connects to the specified exchange using CCXT.
        Configures sandbox mode if enabled.
        """
        try:
            exchange_class = getattr(ccxt, self.exchange_id)
            self.exchange = exchange_class({
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'enableRateLimit': True, # Enable built-in rate limiting
            })

            if self.sandbox and 'test' in self.exchange.urls:
                self.exchange.set_sandbox_mode(True)
                logger.info(f"[ExecutionHandler] Connected to {self.exchange_id} in SANDBOX mode.")
            else:
                logger.info(f"[ExecutionHandler] Connected to {self.exchange_id} in LIVE mode (Sandbox not available or disabled).")

            # Load markets to ensure connection is working
            self.exchange.load_markets()
            logger.info(f"[ExecutionHandler] Successfully loaded markets for {self.exchange_id}.")

        except Exception as e:
            logger.error(f"[ExecutionHandler] Error connecting to exchange {self.exchange_id}: {e}")
            self.exchange = None

    def place_order(self, symbol: str, order_type: str, side: str, amount: float, price: Optional[float] = None) -> dict:
        """
        Places an order on the exchange.

        Args:
            symbol (str): Trading pair (e.g., 'BTC/USDT').
            order_type (str): Type of order ('limit', 'market').
            side (str): Order side ('buy', 'sell').
            amount (float): Amount of base currency to trade.
            price (Optional[float]): Price for limit orders. Required for 'limit' orders.

        Returns:
            dict: Order information from the exchange or a simulated response.
        """
        if not self.exchange:
            logger.error("[ExecutionHandler] Not connected to an exchange. Cannot place order.")
            return {'status': 'failed', 'info': 'Not connected'}

        try:
            if order_type == 'limit':
                order = self.exchange.create_limit_order(symbol, side, amount, price)
            elif order_type == 'market':
                order = self.exchange.create_market_order(symbol, side, amount)
            else:
                logger.warning(f"[ExecutionHandler] Unsupported order type: {order_type}")
                return {'status': 'failed', 'info': 'Unsupported order type'}

            logger.info(f"[ExecutionHandler] Order placed: {order}")
            return order
        except ccxt.NetworkError as e:
            logger.error(f"[ExecutionHandler] Network error while placing order: {e}")
            return {'status': 'failed', 'info': f'Network error: {e}'}
        except ccxt.ExchangeError as e:
            logger.error(f"[ExecutionHandler] Exchange error while placing order: {e}")
            return {'status': 'failed', 'info': f'Exchange error: {e}'}
        except Exception as e:
            logger.error(f"[ExecutionHandler] An unexpected error occurred while placing order: {e}")
            return {'status': 'failed', 'info': f'Unexpected error: {e}'}

    def get_balance(self, currency: str) -> Optional[float]:
        """
        Fetches the available balance for a given currency.
        """
        if not self.exchange:
            logger.error("[ExecutionHandler] Not connected to an exchange. Cannot get balance.")
            return None
        try:
            balance = self.exchange.fetch_balance()
            return balance['free'][currency]
        except Exception as e:
            logger.error(f"[ExecutionHandler] Error fetching balance for {currency}: {e}")
            return None

if __name__ == '__main__':
    # Example of how to use the ExecutionHandler
    import sys
    import os

    # Add the project root to the Python path
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.insert(0, project_root)

    from src.config import Config

    logger.info("--- Execution Handler Test ---")

    # IMPORTANT: For real trading, ensure sandbox=False and correct API keys are set in .env
    # For testing, ensure your exchange supports a testnet and your API keys are for the testnet.
    settings = Config()
    # Replace with your actual API Key and Secret from .env for the chosen exchange
    api_key = settings.api_key
    api_secret = settings.api_secret

    if api_key == 'TU_API_KEY_AQUI' or api_secret == 'TU_API_SECRET_AQUI':
        logger.warning("Please update your .env file with actual API keys for testing.")
        logger.warning("Using dummy keys for simulation, but real connection will fail.")
        api_key = 'dummy_key'
        api_secret = 'dummy_secret'

    executor = ExecutionHandler(
        settings_obj=settings,
        sandbox=True # Set to False for live trading
    )

    # Test fetching balance
    base_currency = settings.symbol.split('/')[0] # e.g., BTC from BTC/USDT
    quote_currency = settings.symbol.split('/')[1] # e.g., USDT from BTC/USDT

    # Note: Balance fetching might fail in sandbox if not properly funded or configured on exchange side.
    # This is just a test of the connection.
    base_balance = executor.get_balance(base_currency)
    quote_balance = executor.get_balance(quote_currency)

    if base_balance is not None:
        logger.info(f"Available {base_currency} balance: {base_balance}")
    if quote_balance is not None:
        logger.info(f"Available {quote_currency} balance: {quote_balance}")

    # Test placing a simulated order (will likely fail if sandbox not properly set up on exchange)
    # This is just to show the method call.
    # try:
    #     test_order = executor.place_order(symbol=settings.symbol, order_type='limit', side='buy', amount=0.001, price=20000)
    #     print(f"Test Order Result: {test_order}")
    # except Exception as e:
    #     print(f"Could not place test order: {e}")
