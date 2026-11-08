import pytest
from src.stores.base import StoreError
from src.stores.blinkit import BlinkitStore
from src.stores.zepto import ZeptoStore


def test_blinkit_disabled_without_verified_endpoint():
    with pytest.raises(StoreError, match="no verified search endpoint"):
        BlinkitStore("11.0,76.0", endpoint="").search("Hot Wheels")


def test_zepto_disabled_without_verified_endpoint():
    with pytest.raises(StoreError, match="no verified search endpoint"):
        ZeptoStore("11.0,76.0", endpoint="").search("Hot Wheels")


def test_blinkit_parser_does_not_assume_missing_stock_is_available():
    store = BlinkitStore("", endpoint="https://blinkit.com/search")
    products = store._parse_json_response({"products": [
        {"id": "1", "name": "Hot Wheels Car", "price": 179, "url": "https://blinkit.com/prn/a/prid/1"},
        {"id": "2", "name": "Hot Wheels Car 2", "price": 179, "in_stock": True, "url": "https://blinkit.com/prn/b/prid/2"},
        {"id": "3", "name": "Hot Wheels Car 3", "price": 179, "in_stock": False, "url": "https://blinkit.com/prn/c/prid/3"},
    ]})
    assert [p.availability for p in products] == ["Unknown", "In Stock", "Out of Stock"]


def test_unrecognized_blinkit_response_is_error_not_empty_stock():
    store = BlinkitStore("", endpoint="https://blinkit.com/search")
    with pytest.raises(StoreError, match="recognized product list"):
        store._parse_json_response({"message": "temporarily unavailable"})


def test_zepto_parser_uses_explicit_out_of_stock_flag():
    store = ZeptoStore("", endpoint="https://www.zeptonow.com/search")
    products = store._parse_json_response({"products": [
        {"product": {"id": "1", "name": "Hot Wheels Car", "url": "https://www.zeptonow.com/pn/a/p/1", "out_of_stock": False}},
        {"product": {"id": "2", "name": "Hot Wheels Car 2", "url": "https://www.zeptonow.com/pn/b/p/2"}},
    ]})
    assert [p.availability for p in products] == ["In Stock", "Unknown"]
