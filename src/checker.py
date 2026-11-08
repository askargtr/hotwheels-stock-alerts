import logging
from datetime import datetime, timezone
from typing import Dict, List

from src.config import Config
from src.storage import StorageManager
from src.notifier.telegram import TelegramNotifier
from src.stores.base import BaseStore, StoreError
from src.filters import filter_products, is_watchlist_match

logger = logging.getLogger(__name__)


class StockChecker:
    """Runs each store independently and never treats failed scans as sold-out."""

    def __init__(self, config: Config, storage: StorageManager,
                 notifier: TelegramNotifier, stores: List[BaseStore]):
        self.config = config
        self.storage = storage
        self.notifier = notifier
        self.stores = stores

    def run_check(self, health_mode: bool = False) -> bool:
        total_scanned = 0
        total_matches = 0
        failures: Dict[str, str] = {}
        successes = 0

        logger.info("Starting stock check (health_mode=%s).", health_mode)
        for store in self.stores:
            try:
                products = store.search("Hot Wheels")
                if not isinstance(products, list):
                    raise StoreError("Store adapter returned an invalid result type.")
                total_scanned += len(products)
                # If a relevant Hot Wheels car has unknown stock status, the scan is
                # incomplete. Do not alert or clear last-known state based on guesswork.
                unknown_candidates = [
                    product for product in products
                    if is_watchlist_match(product.name, self.config.watchlist)
                    and (product.availability or "").strip().casefold() not in {"in stock", "out of stock"}
                ]
                if unknown_candidates:
                    raise StoreError(
                        f"{len(unknown_candidates)} matching Hot Wheels listing(s) had unknown stock status."
                    )
                successes += 1
                matches = filter_products(products, self.config.watchlist)
                total_matches += len(matches)

                for product in matches:
                    if self.storage.should_notify(product):
                        if self.notifier.send_alert(product):
                            self.storage.record_notification(
                                product, datetime.now(timezone.utc).isoformat()
                            )
                # Only a successful response may update the store's active state.
                self.storage.update_in_stock(store.name, matches)
                logger.info("%s: scanned %d products; %d matching cars in stock.",
                            store.name, len(products), len(matches))
            except StoreError as exc:
                failures[store.name] = str(exc)
                logger.error("%s scan failed; existing stock state was preserved: %s", store.name, exc)
            except Exception as exc:
                failures[store.name] = f"Unexpected error: {exc}"
                logger.exception("Unexpected error checking %s; state was preserved.", store.name)

        if health_mode:
            self.notifier.send_health_report(total_scanned, total_matches, failures)

        if successes == 0 or failures:
            logger.error("Stock check incomplete: %d/%d stores succeeded.", successes, len(self.stores))
            return False

        logger.info("Stock check completed successfully.")
        return True
