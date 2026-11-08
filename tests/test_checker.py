from unittest.mock import MagicMock
from src.models import Product
from src.config import Config
from src.storage import StorageManager
from src.notifier.telegram import TelegramNotifier
from src.stores.base import BaseStore, StoreError
from src.checker import StockChecker


def make_config():
    config = MagicMock(spec=Config)
    config.watchlist = {"require_any": ["Hot Wheels"], "keywords": [], "exclude": ["track"]}
    return config


def test_checker_success_flow():
    config, storage, notifier = make_config(), MagicMock(spec=StorageManager), MagicMock(spec=TelegramNotifier)
    storage.should_notify.return_value = True
    notifier.send_alert.return_value = True
    store = MagicMock(spec=BaseStore)
    store.name = "Blinkit"
    car = Product("Hot Wheels Nissan Skyline", 179, "https://shop/1", "Blinkit", availability="In Stock")
    store.search.return_value = [car]
    checker = StockChecker(config, storage, notifier, [store])
    assert checker.run_check() is True
    store.search.assert_called_once_with("Hot Wheels")
    notifier.send_alert.assert_called_once_with(car)
    storage.record_notification.assert_called_once()
    storage.update_in_stock.assert_called_once_with("Blinkit", [car])


def test_failed_store_does_not_update_state_and_scan_fails():
    config, storage, notifier = make_config(), MagicMock(spec=StorageManager), MagicMock(spec=TelegramNotifier)
    store = MagicMock(spec=BaseStore)
    store.name = "Blinkit"
    store.search.side_effect = StoreError("HTTP 403")
    checker = StockChecker(config, storage, notifier, [store])
    assert checker.run_check() is False
    storage.update_in_stock.assert_not_called()


def test_one_failed_store_preserves_other_store_success():
    config, storage, notifier = make_config(), MagicMock(spec=StorageManager), MagicMock(spec=TelegramNotifier)
    storage.should_notify.return_value = True
    notifier.send_alert.return_value = True
    bad = MagicMock(spec=BaseStore)
    bad.name = "Blinkit"
    bad.search.side_effect = StoreError("HTTP 403")
    good = MagicMock(spec=BaseStore)
    good.name = "Zepto"
    car = Product("Hot Wheels Porsche 911", 179, "https://shop/2", "Zepto", availability="In Stock")
    good.search.return_value = [car]
    checker = StockChecker(config, storage, notifier, [bad, good])
    assert checker.run_check() is False
    storage.update_in_stock.assert_called_once_with("Zepto", [car])


def test_health_report_includes_store_failures():
    config, storage, notifier = make_config(), MagicMock(spec=StorageManager), MagicMock(spec=TelegramNotifier)
    store = MagicMock(spec=BaseStore)
    store.name = "Blinkit"
    store.search.side_effect = StoreError("not configured")
    checker = StockChecker(config, storage, notifier, [store])
    checker.run_check(health_mode=True)
    notifier.send_health_report.assert_called_once_with(0, 0, {"Blinkit": "not configured"})


def test_unknown_stock_status_preserves_state_and_sends_no_alert():
    config, storage, notifier = make_config(), MagicMock(spec=StorageManager), MagicMock(spec=TelegramNotifier)
    store = MagicMock(spec=BaseStore)
    store.name = "Blinkit"
    unknown_car = Product("Hot Wheels Nissan Skyline", 179, "https://shop/1", "Blinkit", availability="Unknown")
    store.search.return_value = [unknown_car]
    checker = StockChecker(config, storage, notifier, [store])
    assert checker.run_check() is False
    notifier.send_alert.assert_not_called()
    storage.update_in_stock.assert_not_called()
