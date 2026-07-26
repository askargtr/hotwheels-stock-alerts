import re
from typing import List, Optional
from src.models import Product

def normalize_text(text: str) -> str:
    """
    Normalizes a string by:
    - Lowercasing
    - Removing spaces, hyphens, and underscores.
    
    Example:
        'Nissan Skyline GT-R R33' -> 'nissanskylinegtrr33'
    """
    if not text:
        return ""
    # Lowercase the string
    normalized = text.lower()
    # Remove space, hyphen, and underscore characters
    normalized = re.sub(r"[\s\-_]+", "", normalized)
    return normalized

def is_watchlist_match(product_name: str, watchlist: List[str]) -> bool:
    """
    Checks if a product name matches any item in the watchlist.
    Matches are case-insensitive, ignore spaces/hyphens/underscores,
    and support partial matching (watchlist item is a substring of product name).
    """
    if not product_name or not watchlist:
        return False
        
    normalized_name = normalize_text(product_name)
    
    for term in watchlist:
        normalized_term = normalize_text(term)
        if not normalized_term:
            continue
        if normalized_term in normalized_name:
            return True
            
    return False

def filter_products(products: List[Product], watchlist: List[str]) -> List[Product]:
    """
    Filters a list of products to keep only those that match the watchlist
    and are currently in stock.
    """
    matched = []
    for product in products:
        # We only care about products that are in stock
        is_in_stock = product.availability.strip().lower() == "in stock"
        if is_in_stock and is_watchlist_match(product.name, watchlist):
            matched.append(product)
    return matched
