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

def is_watchlist_match(product_name: str, watchlist: dict) -> bool:
    """
    Checks if a product name matches the watchlist rules.
    - If any term in the 'exclude' list matches the product name, returns False.
    - If any term in the 'keywords' list matches, returns True.
    Matches are case-insensitive, ignoring spaces, hyphens, and underscores.
    """
    if not product_name or not watchlist:
        return False
        
    normalized_name = normalize_text(product_name)
    
    keywords = watchlist.get("keywords", [])
    exclude = watchlist.get("exclude", [])
    
    # 1. Check exclusions first
    for term in exclude:
        normalized_term = normalize_text(term)
        if normalized_term and normalized_term in normalized_name:
            return False
            
    # 2. Check inclusions
    for term in keywords:
        normalized_term = normalize_text(term)
        if normalized_term and normalized_term in normalized_name:
            return True
            
    return False

def filter_products(products: List[Product], watchlist: dict) -> List[Product]:
    """
    Filters a list of products to keep only those that match the watchlist rules
    and are currently in stock.
    """
    matched = []
    for product in products:
        # We only care about products that are in stock
        is_in_stock = product.availability.strip().lower() == "in stock"
        if is_in_stock and is_watchlist_match(product.name, watchlist):
            matched.append(product)
    return matched
