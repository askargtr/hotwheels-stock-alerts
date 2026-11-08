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


class BlinkitStore(BaseStore):
    """Blinkit adapter; disabled until a verified official endpoint is configured."""

    def __init__(self, location: str, endpoint: str = ""):
        self.location = location
        self.endpoint = endpoint or os.getenv("BLINKIT_SEARCH_URL", "").strip()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "HotWheelsStockAlerts/2.0",
            "Accept": "application/json",
        })
        retries = Retry(total=2, connect=2, read=0, status=0, backoff_factor=0.5)
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

    @property
    def name(self) -> str:
        return "Blinkit"

    def _build_request(self, query: str) -> Dict[str, Any]:
        endpoint = validate_endpoint(self.endpoint, self.name, ("blinkit.com",))
        params: Dict[str, Any] = {"q": query}
        # Location is supplied only as configured by the user. The exact parameter
        # name must be confirmed against the provider's authorized API contract.
        if self.location:
            params["location"] = self.location
        return {"url": endpoint, "params": params, "headers": dict(self.session.headers)}


    def _parse_json_response(self, data: Dict[str, Any]) -> List[Product]:
        items = find_items(data, (("products",), ("data", "products"), ("results",)))
        if items is None:
            raise StoreError("Blinkit response did not contain a recognized product list.")
        products = []
        for item in items:
            product = to_product(item, self.name, "blinkit.com")
            if product:
                products.append(product)
            elif (item.get("name") or item.get("title") or "").lower().find("hot wheels") >= 0:
                raise StoreError("Blinkit returned a Hot Wheels listing without a valid official product URL.")
        if items and not products:
            raise StoreError("Blinkit product response could not be parsed; preserving previous stock state.")
        return products

    def search(self, query: str) -> List[Product]:
        request_config = self._build_request(query)
        try:
            response = self.session.get(
                request_config["url"], params=request_config["params"],
                headers=request_config["headers"], timeout=(5, 12)
            )
            if response.status_code in (401, 403):
                raise StoreError(f"Blinkit refused the configured request (HTTP {response.status_code}).")
            response.raise_for_status()
            data = response.json()
        except StoreError:
            raise
        except (requests.RequestException, ValueError) as exc:
            raise StoreError(f"Blinkit search failed: {exc}") from exc

        products = self._parse_json_response(data)
        return products
