import os
import json
import logging
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class ConfigError(ValueError):
    """Exception raised for configuration-related errors."""
    pass

class Config:
    """Manages system configuration and environment variables."""

    def __init__(self):
        # Required variables
        self.bot_token: str = self._get_required_env("BOT_TOKEN")
        self.chat_id: str = self._get_required_env("CHAT_ID")
        self.blinkit_location: str = self._get_required_env("BLINKIT_LOCATION")
        self.zepto_location: str = self._get_required_env("ZEPTO_LOCATION")

        # Optional variables
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()
        self.watchlist_path: str = os.getenv("WATCHLIST_PATH", "config/watchlist.json")
        self.alerts_db_path: str = os.getenv("ALERTS_DB_PATH", "alerts.json")

        # Load watchlist
        self.watchlist: List[str] = self._load_watchlist()

    def _get_required_env(self, key: str) -> str:
        """Retrieves a required environment variable or raises a ConfigError."""
        val = os.getenv(key)
        if not val or not val.strip():
            raise ConfigError(f"Missing required environment variable: {key}")
        return val.strip()

    def _load_watchlist(self) -> List[str]:
        """Loads and parses the watchlist JSON file."""
        if not os.path.exists(self.watchlist_path):
            # Fallback/warning if config/watchlist.json is missing, though we package it
            logging.warning(
                f"Watchlist file not found at '{self.watchlist_path}'. Using empty watchlist."
            )
            return []

        try:
            with open(self.watchlist_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, list):
                    raise ConfigError("Watchlist JSON must be a list of strings.")
                return [str(item) for item in data]
        except json.JSONDecodeError as e:
            raise ConfigError(f"Failed to parse watchlist JSON: {e}")
        except Exception as e:
            raise ConfigError(f"Error loading watchlist: {e}")

    def setup_logging(self) -> None:
        """Configures logging for the application."""
        numeric_level = getattr(logging, self.log_level, logging.INFO)
        if not isinstance(numeric_level, int):
            numeric_level = logging.INFO

        logging.basicConfig(
            level=numeric_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler()
            ]
        )
