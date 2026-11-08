import json
import logging
import os
from dotenv import load_dotenv

load_dotenv()


class ConfigError(ValueError):
    pass


class Config:
    def __init__(self):
        self.bot_token = self._required("BOT_TOKEN")
        self.chat_id = self._required("CHAT_ID")
        self.blinkit_location = os.getenv("BLINKIT_LOCATION", "").strip()
        self.zepto_location = os.getenv("ZEPTO_LOCATION", "").strip()
        self.blinkit_search_url = os.getenv("BLINKIT_SEARCH_URL", "").strip()
        self.zepto_search_url = os.getenv("ZEPTO_SEARCH_URL", "").strip()
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.watchlist_path = os.getenv("WATCHLIST_PATH", "config/watchlist.json")
        self.alerts_db_path = os.getenv("ALERTS_DB_PATH", "alerts.json")
        self.watchlist = self._load_watchlist()

    @staticmethod
    def _required(key: str) -> str:
        value = os.getenv(key, "").strip()
        if not value:
            raise ConfigError(f"Missing required environment variable: {key}")
        return value

    def _load_watchlist(self) -> dict:
        if not os.path.exists(self.watchlist_path):
            raise ConfigError(f"Watchlist file not found: {self.watchlist_path}")
        try:
            with open(self.watchlist_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise ConfigError(f"Unable to read watchlist: {exc}") from exc

        if not isinstance(data, dict):
            raise ConfigError("Watchlist must be a JSON object.")
        for key in ("keywords", "exclude", "require_any"):
            value = data.get(key, [])
            if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                raise ConfigError(f"Watchlist '{key}' must be a list of strings.")
        if not data.get("require_any"):
            raise ConfigError("Watchlist must define require_any to avoid matching unrelated products.")
        return data

    def setup_logging(self) -> None:
        level = getattr(logging, self.log_level, logging.INFO)
        logging.basicConfig(level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
