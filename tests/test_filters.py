import pytest
from src.models import Product
from src.filters import normalize_text, is_watchlist_match, filter_products

def test_normalize_text():
    assert normalize_text("Skyline") == "skyline"
    assert normalize_text("skyline") == "skyline"
    assert normalize_text("SKYLINE") == "skyline"
    assert normalize_text("Sky Line") == "skyline"
    assert normalize_text("GT-R") == "gtr"
    assert normalize_text("GT_R") == "gtr"
    assert normalize_text("  Nissan-Skyline_GT-R   ") == "nissanskylinegtr"
    assert normalize_text("") == ""
    assert normalize_text(None) == ""

def test_is_watchlist_match():
    watchlist = {
        "keywords": ["Skyline", "Supra", "Mazda 787B", "Porsche", "GT-R"],
        "exclude": ["Keychain", "Sticker"]
    }
    
    # Positive matches
    assert is_watchlist_match("Nissan Skyline GT-R R33", watchlist) is True
    assert is_watchlist_match("Toyota Supra Mk4", watchlist) is True
    assert is_watchlist_match("Mazda-787B Le Mans", watchlist) is True
    assert is_watchlist_match("Porsche 911 GT3", watchlist) is True
    assert is_watchlist_match("skyline", watchlist) is True
    assert is_watchlist_match("gtr", watchlist) is True
    
    # Negative matches
    assert is_watchlist_match("Honda Civic Type R", watchlist) is False
    assert is_watchlist_match("Hot Wheels HW Bus", watchlist) is False
    assert is_watchlist_match("", watchlist) is False
    assert is_watchlist_match("Porsche", {}) is False

    # Exclusions
    assert is_watchlist_match("Porsche 911 Keychain", watchlist) is False
    assert is_watchlist_match("Skyline Sticker", watchlist) is False

def test_filter_products():
    watchlist = {
        "keywords": ["Skyline", "Porsche"],
        "exclude": ["Keychain"]
    }
    products = [
        Product("Nissan Skyline GT-R", 179.0, "http://link1", "Blinkit", "img1", "In Stock"),
        Product("Porsche 911", 179.0, "http://link2", "Blinkit", "img2", "Out of Stock"), # Out of stock, ignore!
        Product("Honda Civic", 179.0, "http://link3", "Blinkit", "img3", "In Stock"),     # Not on watchlist, ignore!
        Product("Porsche Cayman", 179.0, "http://link4", "Zepto", "img4", "In Stock"),    # In stock and matches watchlist
        Product("Skyline Keychain", 179.0, "http://link5", "Blinkit", "img5", "In Stock") # Excluded, ignore!
    ]
    
    filtered = filter_products(products, watchlist)
    assert len(filtered) == 2
    assert filtered[0].name == "Nissan Skyline GT-R"
    assert filtered[1].name == "Porsche Cayman"
