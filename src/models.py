from dataclasses import dataclass

@dataclass
class Product:
    """Represents a product casting scraped/queried from a store."""
    name: str
    price: float
    url: str
    store: str
    image: str
    availability: str  # e.g., "In Stock", "Out of Stock"
