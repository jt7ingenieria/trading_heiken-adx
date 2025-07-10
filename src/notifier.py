import requests
from src.config import Config
from src.logger import logger

class Notifier:
    """
    Handles sending notifications, e.g., to Telegram.
    """
    def __init__(self, settings_obj: Config):
        self.settings = settings_obj
        self.telegram_token = getattr(self.settings, 'telegram_bot_token', None)
        self.telegram_chat_id = getattr(self.settings, 'telegram_chat_id', None)
        self.telegram_api_url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"

        if not self.telegram_token or not self.telegram_chat_id:
            logger.warning("Telegram bot token or chat ID not configured. Notifications will be disabled.")
            self.enabled = False
        else:
            self.enabled = True

    def send_telegram_message(self, message: str):
        """
        Sends a message to the configured Telegram chat.
        """
        if not self.enabled:
            return

        try:
            payload = {
                'chat_id': self.telegram_chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(self.telegram_api_url, data=payload)
            response.raise_for_status() # Raise an exception for HTTP errors
            logger.info(f"Telegram message sent: {message}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending Telegram message: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while sending Telegram message: {e}")
