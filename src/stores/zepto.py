import logging
import os
from typing import Any, Dict, List

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from src.models import Product
from src.stores.base import BaseStore, StoreError
from src.stores._json_store import find_items, to_product, validate_endpoint

logger = logging.getLogger(__name__)


class ZeptoStore(BaseStore):
    """Zepto adapter; disabled until a verified official endpoint is configured."""

    def __init__(self, location: str, endpoint: str = ""):
        self.location = location
        self.endpoint = endpoint or os.getenv("ZEPTO_SEARCH_URL", "").strip()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "HotWheelsStockAlerts/2.0",
            "Accept": "application/json",
            "Content-Type": "application/json",
        })
        retries = Retry(total=2, connect=2, read=0, status=0, backoff_factor=0.5)
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

    @property
    def name(self) -> str:
        return "Zepto"

    def _build_request(self, query: str) -> Dict[str, Any]:
        endpoint = validate_endpoint(self.endpoint, self.name, ("zeptonow.com",))
        payload: Dict[str, Any] = {"query": query}
        if self.location:
            payload["location"] = self.location
        return {"url": endpoint, "json": payload, "headers": dict(self.session.headers)}


    def _parse_json_response(self, data: Dict[str, Any]) -> List[Product]:
        items = find_items(data, (("products",), ("data", "items"), ("data", "products"), ("results",)))
        if items is None:
            raise StoreError("Zepto response did not contain a recognized product list.")
        products = []
        for item in items:
            details = item.get("product") if isinstance(item.get("product"), dict) else item
            product = to_product(details, self.name, "zeptonow.com", out_of_stock_key="out_of_stock")
            if product:
                products.append(product)
            elif (details.get("name") or details.get("title") or "").lower().find("hot wheels") >= 0:
                raise StoreError("Zepto returned a Hot Wheels listing without a valid official product URL.")
        if items and not products:
            raise StoreError("Zepto product response could not be parsed; preserving previous stock state.")
        return products

    def search(self, query: str) -> List[Product]:
        request_config = self._build_request(query)
        try:
            response = self.session.post(
                request_config["url"], json=request_config["json"],
                headers=request_config["headers"], timeout=(5, 12)
            )
            if response.status_code in (401, 403):
                raise StoreError(f"Zepto refused the configured request (HTTP {response.status_code}).")
            response.raise_for_status()
            data = response.json()
        except StoreError:
            raise
        except (requests.RequestException, ValueError) as exc:
            raise StoreError(f"Zepto search failed: {exc}") from exc

        products = self._parse_json_response(data)
        return products
