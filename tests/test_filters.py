from src.models import Product
from src.filters import normalize_text, is_watchlist_match, filter_products


def test_normalize_text():
    assert normalize_text("Nissan Skyline GT-R R33") == "nissanskylinegtrr33"
    assert normalize_text(None) == ""


def test_diecast_car_watchlist_and_accessory_exclusions():
    watchlist = {
        "require_any": ["Hot Wheels", "Hotwheels"],
        "keywords": [],
        "exclude": ["track", "playset", "keychain", "sticker", "accessory"],
    }
    assert is_watchlist_match("Hot Wheels Nissan Skyline GT-R R33", watchlist)
    assert is_watchlist_match("HOTWHEELS Porsche 911", watchlist)
    assert not is_watchlist_match("Hot Wheels Track Builder", watchlist)
    assert not is_watchlist_match("Hot Wheels Porsche Keychain", watchlist)
    assert not is_watchlist_match("Porsche 911 diecast", watchlist)


def test_filter_only_confirmed_stock_and_https_products():
    watchlist = {"require_any": ["Hot Wheels"], "keywords": [], "exclude": ["track", "keychain"]}
    products = [
        Product("Hot Wheels Nissan Skyline", 179, "https://shop/item/1", "Blinkit", availability="In Stock"),
        Product("Hot Wheels Porsche", 179, "https://shop/item/2", "Blinkit", availability="Unknown"),
        Product("Hot Wheels Track Builder", 349, "https://shop/item/3", "Blinkit", availability="In Stock"),
        Product("Hot Wheels Supra", 179, "http://insecure/item/4", "Blinkit", availability="In Stock"),
        Product("Hot Wheels Mazda", 179, "https://shop/item/5", "Blinkit", availability="Out of Stock"),
    ]
    assert [p.name for p in filter_products(products, watchlist)] == ["Hot Wheels Nissan Skyline"]
