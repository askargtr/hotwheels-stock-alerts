import os
import json
import logging
from typing import Dict, List, Any
from src.models import Product

class StorageManager:
    """
    Manages the local state of active listings and notification history 
    to prevent duplicate alerts and handle restocks.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.state: Dict[str, Any] = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        """Loads state from the JSON file, or initializes it if not found/corrupted."""
        if not os.path.exists(self.db_path):
            return self._get_default_state()

        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                state = json.load(f)
                # Validation of root keys
                if "in_stock_last_seen" not in state or "alert_history" not in state:
                    logging.warning("State file format was invalid. Resetting to default.")
                    return self._get_default_state()
                return state
        except json.JSONDecodeError:
            logging.warning("State file was corrupted. Resetting to default.")
            return self._get_default_state()
        except Exception as e:
            logging.error(f"Failed to read state file: {e}. Using empty state.")
            return self._get_default_state()

    def _get_default_state(self) -> Dict[str, Any]:
        """Returns default empty state structure."""
        return {
            "in_stock_last_seen": {},  # Maps store name (str) -> list of product names (List[str])
            "alert_history": {}        # Maps "store:product_name" -> ISO timestamp of last alert (str)
        }

    def save_state(self) -> None:
        """Saves current state to the local JSON file."""
        try:
            # Write to a temporary file first, then rename it to avoid corruption
            temp_path = f"{self.db_path}.tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2)
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
            os.rename(temp_path, self.db_path)
        except Exception as e:
            logging.error(f"Failed to save state file: {e}")

    def should_notify(self, product: Product) -> bool:
        """
        Determines whether a notification should be sent for a product.
        - Returns True if the product is new or has come back in stock after being sold out.
        - Returns False if the product was already in stock during the last run and alerted.
        """
        store = product.store
        name = product.name
        key = f"{store}:{name}"

        in_stock_last_run = self.state["in_stock_last_seen"].get(store, [])
        alert_history = self.state["alert_history"]

        # If product was in stock last run and we have already notified about it,
        # do not duplicate the notification.
        if key in alert_history and name in in_stock_last_run:
            logging.debug(f"Skipping duplicate alert: {key} is still in stock.")
            return False

        # Otherwise, this is a new stock or a restock
        logging.info(f"New stock/restock detected for: {key}")
        return True

    def record_notification(self, product: Product, timestamp: str) -> None:
        """Records a sent notification timestamp to the history."""
        key = f"{product.store}:{product.name}"
        self.state["alert_history"][key] = timestamp
        self.save_state()

    def update_in_stock(self, store: str, current_in_stock_names: List[str]) -> None:
        """
        Updates the list of products that were in stock during this run.
        This allows detecting when a product goes out of stock and comes back later.
        """
        self.state["in_stock_last_seen"][store] = current_in_stock_names
        self.save_state()
