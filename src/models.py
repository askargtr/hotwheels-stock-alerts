from dataclasses import dataclass


@dataclass
class Product:
    """A product returned by a store integration.

    Availability is deliberately explicit: only the exact value "In Stock"
    is eligible for an alert. Unknown or missing stock data fails closed.
    """

    name: str
    price: float
    url: str
    store: str
    image: str = ""
    availability: str = "Unknown"
