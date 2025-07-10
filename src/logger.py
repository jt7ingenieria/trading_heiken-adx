"""Configures and provides a centralized logging mechanism for the trading bot."""

import logging
import os
from logging.handlers import RotatingFileHandler

# Define the logs directory and ensure it exists
log_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

# Path for the log file
log_file_path = os.path.join(log_directory, 'trading_bot.log')

def setup_logger():
    """
    Configures and returns a logger for the application.
    """
    logger = logging.getLogger('TradingBotLogger')
    logger.setLevel(logging.INFO)

    # Prevent adding multiple handlers to the same logger instance
    if logger.hasHandlers():
        return logger

    # Create a rotating file handler
    handler = RotatingFileHandler(
        log_file_path, 
        maxBytes=1024*1024*5, # 5 MB
        backupCount=5
    )
    
    # Create a formatter and set it for the handler
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    # Add the handler to the logger
    logger.addHandler(handler)
    
    # Also log to console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

# Initialize the logger
logger = setup_logger()
