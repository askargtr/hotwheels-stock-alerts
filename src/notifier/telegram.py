import html
import logging
from datetime import datetime, timezone, timedelta

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from src.models import Product

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Telegram Bot API notifier using HTML-safe message formatting."""

    def __init__(self, bot_token: str, chat_id: str):
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "HotWheelsStockAlerts/2.0"})
        retries = Retry(total=2, connect=2, read=0, status=0, backoff_factor=0.5)
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

    @staticmethod
    def _time_str() -> str:
        now = datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
        return now.strftime("%I:%M %p IST")

    def _format_message(self, product: Product) -> str:
        name = html.escape(product.name)
        store = html.escape(product.store)
        url = html.escape(product.url, quote=True)
        price = f"{product.price:g}"
        return (
            "🚨 <b>Hot Wheels Restock</b>\n\n"
            f"🏪 <b>Store</b>\n{store}\n\n"
            f"🚗 <b>Die-cast car</b>\n{name}\n\n"
            f"💰 <b>Price</b>\n₹{price}\n\n"
            f"🔗 <b>Buy</b>\n<a href=\"{url}\">Open product</a>\n\n"
            f"🕒 {self._time_str()}"
        )

    def _send(self, text: str) -> bool:
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }
        try:
            response = self.session.post(self.api_url, json=payload, timeout=(5, 12))
            response.raise_for_status()
            result = response.json()
            if not result.get("ok"):
                logger.error("Telegram API error: %s", result.get("description", "unknown error"))
                return False
            return True
        except (requests.RequestException, ValueError) as exc:
            logger.error("Telegram delivery failed: %s", exc)
            return False

    def send_alert(self, product: Product) -> bool:
        logger.info("Sending Telegram alert for %s (%s).", product.name, product.store)
        return self._send(self._format_message(product))

    def send_health_report(self, total_scanned: int, total_matches: int, failures=None) -> bool:
        failures = failures or {}
        if failures:
            failure_text = "\n".join(
                f"• {html.escape(store)}: {html.escape(reason)}"
                for store, reason in failures.items()
            )
            status = f"⚠️ <b>Some stores unavailable</b>\n{failure_text}"
        else:
            status = "✅ <b>All configured stores scanned successfully</b>"
        message = (
            "📊 <b>Hot Wheels Stock Check Report</b>\n\n"
            f"{status}\n\n"
            f"📦 Products scanned: {total_scanned}\n"
            f"🚗 Matching cars in stock: {total_matches}\n"
            f"🕒 {self._time_str()}"
        )
        return self._send(message)
