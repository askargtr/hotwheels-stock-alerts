import os
import json
import pytest
from src.models import Product
from src.storage import StorageManager

@pytest.fixture
def temp_db_path(tmp_path):
    """Fixture to provide a clean temporary storage file path."""
    return str(tmp_path / "test_alerts.json")

def test_storage_initialization(temp_db_path):
    storage = StorageManager(temp_db_path)
    assert storage.state["in_stock_last_seen"] == {}
    assert storage.state["alert_history"] == {}

def test_should_notify_new_product(temp_db_path):
    storage = StorageManager(temp_db_path)
    product = Product("Nissan Skyline", 179.0, "http://link", "Blinkit", "img", "In Stock")
    
    # Brand new product should notify
    assert storage.should_notify(product) is True

def test_should_notify_duplicate_prevention(temp_db_path):
    storage = StorageManager(temp_db_path)
    product = Product("Nissan Skyline", 179.0, "http://link", "Blinkit", "img", "In Stock")
    
    # 1. First check - returns True
    assert storage.should_notify(product) is True
    
    # Simulate marking as notified and updating in-stock
    storage.record_notification(product, "2026-07-26T09:35:00Z")
    storage.update_in_stock(product.store, [product.name])
    
    # 2. Second check - same product remains in stock, should return False (no duplicate notification)
    assert storage.should_notify(product) is False

def test_should_notify_restock(temp_db_path):
    storage = StorageManager(temp_db_path)
    product = Product("Nissan Skyline", 179.0, "http://link", "Blinkit", "img", "In Stock")
    
    # 1. Notify initially
    assert storage.should_notify(product) is True
    storage.record_notification(product, "2026-07-26T09:35:00Z")
    storage.update_in_stock(product.store, [product.name])
    
    # 2. Product goes out of stock (removed from active list)
    storage.update_in_stock(product.store, [])
    
    # 3. Product comes back in stock - should return True (restock notification)
    assert storage.should_notify(product) is True
