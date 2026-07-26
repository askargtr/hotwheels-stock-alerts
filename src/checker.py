import logging
from datetime import datetime, timezone
from typing import List
from src.config import Config
from src.storage import StorageManager
from src.notifier.telegram import TelegramNotifier
from src.stores.base import BaseStore, StoreError
from src.filters import filter_products

logger = logging.getLogger(__name__)

class StockChecker:
    """Orchestrates the process of checking stores, filtering products, and triggering notifications."""

    def __init__(
        self,
        config: Config,
        storage: StorageManager,
        notifier: TelegramNotifier,
        stores: List[BaseStore]
    ):
        self.config = config
        self.storage = storage
        self.notifier = notifier
        self.stores = stores

    def run_check(self, health_mode: bool = False) -> None:
        """Executes stock check flow for all configured stores."""
        logger.info(f"Starting stock check run (health_mode={health_mode})...")
        
        total_scanned = 0
        total_matches = 0
        
        for store in self.stores:
            try:
                # Query the store
                # We search for 'Hot Wheels' since we are monitoring Hot Wheels castings
                all_products = store.search("Hot Wheels")
                total_scanned += len(all_products)
                logger.info(f"Retrieved {len(all_products)} products from {store.name}.")
                
                # Filter for in-stock products matching the watchlist
                matching_in_stock = filter_products(all_products, self.config.watchlist)
                total_matches += len(matching_in_stock)
                logger.info(f"Found {len(matching_in_stock)} watchlist matches in stock for {store.name}.")
                
                # Check alerts and notify
                for product in matching_in_stock:
                    if self.storage.should_notify(product):
                        success = self.notifier.send_alert(product)
                        if success:
                            timestamp = datetime.now(timezone.utc).isoformat()
                            self.storage.record_notification(product, timestamp)
                
                # Update the store's list of currently in-stock watchlist items.
                # This lets us detect when items go out of stock and come back later.
                self.storage.update_in_stock(store.name, matching_in_stock)
                
            except StoreError as e:
                # Log the error, but continue with the other stores. Do not update state for this store.
                logger.error(f"Error querying store {store.name}: {e}. Skipping state update for this run.")
            except Exception as e:
                # Catch-all to prevent application crash on unexpected exceptions
                logger.error(f"Unexpected error checking store {store.name}: {e}", exc_info=True)
                
        if health_mode:
            self.notifier.send_health_report(total_scanned, total_matches)
            
        logger.info("Stock check run completed.")
