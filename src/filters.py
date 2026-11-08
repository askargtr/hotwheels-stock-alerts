import re
from typing import List
from src.models import Product


def normalize_text(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"[^a-z0-9]+", "", str(text).lower())


def is_watchlist_match(product_name: str, watchlist: dict) -> bool:
    """Match Hot Wheels car listings while excluding non-car merchandise."""
    if not product_name or not isinstance(watchlist, dict):
        return False

    normalized_name = normalize_text(product_name)
    if not normalized_name:
        return False

    # Exclusions always take priority.
    for term in watchlist.get("exclude", []):
        normalized_term = normalize_text(term)
        if normalized_term and normalized_term in normalized_name:
            return False

    required_any = watchlist.get("require_any", [])
    if required_any and not any(
        normalize_text(term) in normalized_name
        for term in required_any
        if normalize_text(term)
    ):
        return False

    keywords = watchlist.get("keywords", [])
    return not keywords or any(
        normalize_text(term) in normalized_name
        for term in keywords
        if normalize_text(term)
    )


def filter_products(products: List[Product], watchlist: dict) -> List[Product]:
    """Only return matching products with positively confirmed stock."""
    return [
        product for product in products
        if (product.availability or "").strip().casefold() == "in stock"
        and is_watchlist_match(product.name, watchlist)
        and product.url
        and product.url.startswith("https://")
    ]
