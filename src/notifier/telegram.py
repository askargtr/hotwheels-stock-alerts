import logging
import requests
from datetime import datetime, timedelta, timezone
from urllib3.util import Retry
from requests.adapters import HTTPAdapter
from src.models import Product

logger = logging.getLogger(__name__)

class TelegramNotifier:
    """Sends stock alert notifications to a Telegram channel/chat using Telegram Bot API."""

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        
        # Configure a robust requests session with retries, timeout, and user agent
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "HotWheelsStockAlerts/1.0 (GithubActions; Python)"
        })
        
        # Configure retries
        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            raise_on_status=False
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

    def _get_ist_time_str(self, format_str: str = "%I:%M %p") -> str:
        """Helper to get current time in IST timezone (UTC+5:30)."""
        utc_now = datetime.now(timezone.utc)
        ist_now = utc_now + timedelta(hours=5, minutes=30)
        return ist_now.strftime(format_str)

    def _format_message(self, product: Product) -> str:
        """Formats the notification text in Markdown as requested."""
        time_str = self._get_ist_time_str(format_str="%I:%M %p IST")
        
        # Format the price. If price is 179.0, format as 179.
        price_str = str(int(product.price)) if product.price.is_integer() else f"{product.price:.2f}"

        # Build raw markdown string
        message = (
            f"🚨 *Hot Wheels Restock*\n\n"
            f"🏪 *Store*\n"
            f"{product.store}\n\n"
            f"🚗 *Casting*\n"
            f"{product.name}\n\n"
            f"💰 *Price*\n"
            f"₹{price_str}\n\n"
            f"🔗 *Buy*\n"
            f"{product.url}\n\n"
            f"🕒 {time_str}"
        )
        return message

    def send_alert(self, product: Product) -> bool:
        """
        Sends a Markdown-formatted Telegram notification.
        Returns True if successful, False otherwise.
        """
        message = self._format_message(product)
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": False
        }

        try:
            logger.info(f"Sending Telegram notification for {product.name} from {product.store}...")
            # Use a 10-second timeout for the connection and response
            response = self.session.post(self.api_url, json=payload, timeout=10)
            
            # Check for HTTP errors
            response.raise_for_status()
            
            result = response.json()
            if not result.get("ok"):
                logger.error(f"Telegram API returned an error: {result.get('description')}")
                return False
                
            logger.info(f"Telegram notification sent successfully for {product.name}.")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Telegram message for {product.name}: {e}")
            return False

    def send_health_report(self, total_scanned: int, total_matches: int) -> bool:
        """
        Sends a health monitoring report formatted as status update.
        Returns True if successful, False otherwise.
        """
        time_str = self._get_ist_time_str(format_str="%I:%M %p")
        message = (
            f"✅ *Stock monitor running*\n\n"
            f"*Last check:*\n"
            f"{time_str}\n\n"
            f"*Products scanned:*\n"
            f"{total_scanned}\n\n"
            f"*Matches:*\n"
            f"{total_matches}"
        )
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }

        try:
            logger.info("Sending health status Telegram notification...")
            response = self.session.post(self.api_url, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            if not result.get("ok"):
                logger.error(f"Telegram API returned an error: {result.get('description')}")
                return False
            logger.info("Health status notification sent successfully.")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send health status Telegram message: {e}")
            return False
