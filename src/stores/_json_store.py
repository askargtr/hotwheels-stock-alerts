"""Shared safe parsing helpers for JSON-backed store adapters."""
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse

from src.models import Product
from src.stores.base import StoreError


def validate_endpoint(endpoint: Optional[str], store_name: str, allowed_hosts: Iterable[str]) -> str:
    if not endpoint:
        raise StoreError(
            f"{store_name} is not connected: no verified search endpoint is configured. "
            "The previous unofficial endpoint is not being used."
        )
    parsed = urlparse(endpoint)
    host = (parsed.hostname or "").lower()
    allowed = tuple(allowed_hosts)
    if parsed.scheme != "https" or not any(host == item or host.endswith("." + item) for item in allowed):
        raise StoreError(f"{store_name} endpoint must be HTTPS on an official {store_name} domain.")
    return endpoint


def find_items(data: Any, candidate_paths: Iterable[tuple]):
    for path in candidate_paths:
        current = data
        try:
            for key in path:
                current = current[key]
            if isinstance(current, list):
                return [item for item in current if isinstance(item, dict)]
        except (KeyError, TypeError):
            continue
    return None


def explicit_availability(item: Dict[str, Any], *, out_of_stock_key: Optional[str] = None) -> str:
    """Never infer availability from a missing field."""
    if out_of_stock_key and isinstance(item.get(out_of_stock_key), bool):
        return "Out of Stock" if item[out_of_stock_key] else "In Stock"

    for key in ("in_stock", "available", "is_available"):
        if isinstance(item.get(key), bool):
            return "In Stock" if item[key] else "Out of Stock"

    for key in ("availability", "stock_status", "status"):
        value = item.get(key)
        if isinstance(value, str):
            normalized = value.strip().casefold().replace("_", " ").replace("-", " ")
            if normalized in {"in stock", "available", "instock"}:
                return "In Stock"
            if normalized in {"out of stock", "unavailable", "sold out", "outofstock"}:
                return "Out of Stock"

    return "Unknown"


def to_product(item: Dict[str, Any], store_name: str, allowed_host: str, *, out_of_stock_key=None) -> Optional[Product]:
    name = item.get("name") or item.get("title")
    if not isinstance(name, str) or not name.strip():
        return None

    raw_price = item.get("selling_price", item.get("price", item.get("mrp", 0)))
    try:
        price = float(raw_price or 0)
        if price < 0:
            price = 0.0
    except (TypeError, ValueError):
        price = 0.0

    product_url = item.get("url") or item.get("product_url")
    if not isinstance(product_url, str) or not product_url.startswith("https://"):
        return None
    parsed_url = urlparse(product_url)
    host = (parsed_url.hostname or "").lower()
    if not (host == allowed_host or host.endswith("." + allowed_host)):
        return None

    image = item.get("image_url") or item.get("image") or ""
    if isinstance(image, dict):
        image = image.get("url") or image.get("src") or ""
    if not isinstance(image, str):
        image = ""

    return Product(
        name=name.strip(),
        price=price,
        url=product_url,
        store=store_name,
        image=image,
        availability=explicit_availability(item, out_of_stock_key=out_of_stock_key),
    )
