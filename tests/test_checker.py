import pytest
from unittest.mock import MagicMock
from src.models import Product
from src.config import Config
from src.storage import StorageManager
from src.notifier.telegram import TelegramNotifier
from src.stores.base import BaseStore, StoreError
from src.checker import StockChecker

@pytest.fixture
def mock_config():
    config = MagicMock(spec=Config)
    config.watchlist = {
        "keywords": ["Skyline", "Porsche"],
        "exclude": []
    }
    return config

@pytest.fixture
def mock_storage():
    storage = MagicMock(spec=StorageManager)
    # By default, allow notifications
    storage.should_notify.return_value = True
    return storage

@pytest.fixture
def mock_notifier():
    notifier = MagicMock(spec=TelegramNotifier)
    notifier.send_alert.return_value = True
    notifier.send_health_report.return_value = True
    return notifier

def test_checker_success_flow(mock_config, mock_storage, mock_notifier):
    # Mock Store
    store1 = MagicMock(spec=BaseStore)
    store1.name = "Blinkit"
    
    # Store returns two products, one matching in stock, one out of stock
    p1 = Product("Nissan Skyline GT-R", 179.0, "url1", "Blinkit", "img1", "In Stock")
    p2 = Product("Porsche 911", 179.0, "url2", "Blinkit", "img2", "Out of Stock")
    store1.search.return_value = [p1, p2]
    
    checker = StockChecker(mock_config, mock_storage, mock_notifier, [store1])
    checker.run_check()
    
    # Verify we searched for 'Hot Wheels'
    store1.search.assert_called_once_with("Hot Wheels")
    
    # Verify should_notify was called on the in-stock matching product, but not the out of stock one
    mock_storage.should_notify.assert_called_once_with(p1)
    
    # Verify alert was sent for p1
    mock_notifier.send_alert.assert_called_once_with(p1)
    
    # Verify notification recorded
    mock_storage.record_notification.assert_called_once()
    
    # Verify updated in stock status
    mock_storage.update_in_stock.assert_called_once_with("Blinkit", [p1])

def test_checker_store_error_handling(mock_config, mock_storage, mock_notifier):
    # Store 1 fails with StoreError
    store1 = MagicMock(spec=BaseStore)
    store1.name = "Blinkit"
    store1.search.side_effect = StoreError("API rate limit")
    
    # Store 2 succeeds
    store2 = MagicMock(spec=BaseStore)
    store2.name = "Zepto"
    p = Product("Nissan Skyline", 179.0, "url", "Zepto", "img", "In Stock")
    store2.search.return_value = [p]
    
    checker = StockChecker(mock_config, mock_storage, mock_notifier, [store1, store2])
    checker.run_check()
    
    # Verify store 1 search was called and error handled
    store1.search.assert_called_once()
    
    # Verify store 2 search was called and succeeded
    store2.search.assert_called_once()
    mock_storage.should_notify.assert_called_once_with(p)
    mock_notifier.send_alert.assert_called_once_with(p)
    
    # Storage should have updated state ONLY for store 2 (Zepto)
    # Storage should NOT update state for store 1 (Blinkit) due to error
    mock_storage.update_in_stock.assert_called_once_with("Zepto", [p])

def test_checker_health_mode(mock_config, mock_storage, mock_notifier):
    store = MagicMock(spec=BaseStore)
    store.name = "Blinkit"
    p = Product("Porsche 911", 179.0, "url", "Blinkit", "img", "In Stock")
    store.search.return_value = [p]
    
    checker = StockChecker(mock_config, mock_storage, mock_notifier, [store])
    checker.run_check(health_mode=True)
    
    # Verify health report was sent
    mock_notifier.send_health_report.assert_called_once_with(1, 1)
