import hashlib
import json
import logging
import os
from typing import Any, Dict, List

from src.models import Product


def get_product_hash(product: Product) -> str:
    identity = f"{product.store}:{product.url}"
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


class StorageManager:
    """Persistent notification and in-stock state with atomic file replacement."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.state: Dict[str, Any] = self._load_state()

    @staticmethod
    def _default_state() -> Dict[str, Any]:
        return {"in_stock_last_seen": {}, "alert_history": {}}

    def _load_state(self) -> Dict[str, Any]:
        if not os.path.exists(self.db_path):
            return self._default_state()
        try:
            with open(self.db_path, "r", encoding="utf-8") as handle:
                state = json.load(handle)
            if not isinstance(state, dict):
                raise ValueError("root must be an object")
            active = state.get("in_stock_last_seen")
            history = state.get("alert_history")
            if not isinstance(active, dict) or not isinstance(history, dict):
                raise ValueError("required state keys are missing or invalid")
            return {"in_stock_last_seen": active, "alert_history": history}
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            logging.warning("State file could not be loaded (%s); starting with empty state.", exc)
            return self._default_state()

    def save_state(self) -> None:
        directory = os.path.dirname(os.path.abspath(self.db_path))
        os.makedirs(directory, exist_ok=True)
        temp_path = f"{self.db_path}.tmp"
        with open(temp_path, "w", encoding="utf-8") as handle:
            json.dump(self.state, handle, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, self.db_path)

    def should_notify(self, product: Product) -> bool:
        key = get_product_hash(product)
        active = self.state["in_stock_last_seen"].get(product.store, [])
        history = self.state["alert_history"]
        return not (key in history and key in active)

    def record_notification(self, product: Product, timestamp: str) -> None:
        self.state["alert_history"][get_product_hash(product)] = timestamp
        self.save_state()

    def update_in_stock(self, store: str, products: List[Product]) -> None:
        self.state["in_stock_last_seen"][store] = [get_product_hash(item) for item in products]
        self.save_state()
