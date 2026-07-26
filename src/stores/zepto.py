import os
import logging
import requests
import uuid
from typing import List, Dict, Any
from urllib3.util import Retry
from requests.adapters import HTTPAdapter
from src.stores.base import BaseStore, StoreError
from src.models import Product

logger = logging.getLogger(__name__)

class ZeptoStore(BaseStore):
    """Store adapter for Zepto."""

    def __init__(self, location: str):
        self.location = location
        self.session = requests.Session()
        
        # Configure headers matching Zepto's mobile app client requests
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "Origin": "https://www.zeptonow.com",
            "Referer": "https://www.zeptonow.com/",
            "platform": "web",
            "app_version": "12.0.0",
            "tenant_id": "1",
            "request_id": str(uuid.uuid4()),
            "session_id": str(uuid.uuid4())
        })
        
        # Configure retries
        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            raise_on_status=False
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

    @property
    def name(self) -> str:
        return "Zepto"

    def _parse_location(self) -> Dict[str, str]:
        """Parses latitude and longitude from location string."""
        headers = {}
        if "," in self.location:
            try:
                lat, lon = self.location.split(",")
                headers["lat"] = lat.strip()
                headers["lon"] = lon.strip()
                headers["latitude"] = lat.strip()
                headers["longitude"] = lon.strip()
            except ValueError:
                logger.warning(f"Could not parse latitude/longitude from '{self.location}'")
        else:
            # Fallback or placeholder pincode/address handling
            headers["x-pincode"] = self.location.strip()
        return headers

    def _build_request(self, query: str) -> Dict[str, Any]:
        """Builds URL, headers, and JSON payload for the Zepto search request."""
        loc_headers = self._parse_location()
        search_url = "https://api.zeptonow.com/api/v1/product/search/"
        headers = {**self.session.headers, **loc_headers}
        payload = {
            "query": query,
            "pageNumber": 0,
            "pageSize": 30
        }
        return {
            "url": search_url,
            "json": payload,
            "headers": headers
        }

    def search(self, query: str) -> List[Product]:
        """Searches Zepto for products matching the query."""
        req_config = self._build_request(query)
        
        try:
            logger.info(f"Searching {self.name} for '{query}'...")
            # Use 8 seconds connection/read timeout
            response = self.session.post(
                req_config["url"],
                json=req_config["json"],
                headers=req_config["headers"],
                timeout=8
            )
            
            if response.status_code == 200:
                data = response.json()
                products = self._parse_json_response(data)
                if products:
                    return products
                else:
                    logger.warning(f"{self.name} returned 200 OK but no products parsed from JSON structure.")
            else:
                logger.warning(f"{self.name} API returned status code {response.status_code}.")
                if os.getenv("SIMULATE_STORES", "true").lower() != "true":
                    raise StoreError(f"Zepto API returned status code {response.status_code}")
                
        except StoreError:
            raise
        except Exception as e:
            logger.warning(f"Network error or anti-bot block on {self.name}: {e}")
            if os.getenv("SIMULATE_STORES", "true").lower() != "true":
                raise StoreError(f"Network error or anti-bot block on {self.name}: {e}") from e

        # Check if simulation mode is enabled as fallback
        if os.getenv("SIMULATE_STORES", "true").lower() == "true":
            logger.info(f"Falling back to simulated results for {self.name}.")
            return self._generate_simulated_products(query)

        return []

    def _parse_json_response(self, data: Dict[str, Any]) -> List[Product]:
        """Parses Zepto search JSON response into Product dataclasses."""
        products = []
        try:
            # Traversal for typical Zepto schema layouts
            items = data.get("products", []) or data.get("data", {}).get("items", [])
            for item in items:
                # Zepto products can contain a nested 'product' object or flat details
                prod_details = item.get("product", item)
                
                name = prod_details.get("name") or prod_details.get("title", "")
                if not name:
                    continue
                    
                # Parse price (convert price in paise/cents if necessary, but typically standard rupees)
                price_val = prod_details.get("price") or prod_details.get("mrp") or 0.0
                # Zepto internal price is sometimes in paise (e.g. 17900), check and divide
                if price_val > 1000:
                    price = price_val / 100.0
                else:
                    price = price_val

                product_id = prod_details.get("id") or prod_details.get("product_id", "")
                url = f"https://www.zeptonow.com/pn/{name.lower().replace(' ', '-')}/p/{product_id}" if product_id else "https://www.zeptonow.com"
                
                image = prod_details.get("image_url") or prod_details.get("image", "")
                
                # Check availability status
                out_of_stock = prod_details.get("out_of_stock", False)
                availability = "Out of Stock" if out_of_stock else "In Stock"
                
                products.append(Product(
                    name=name,
                    price=float(price),
                    url=url,
                    store=self.name,
                    image=image,
                    availability=availability
                ))
        except Exception as e:
            logger.error(f"Error parsing {self.name} JSON response: {e}")
            
        return products

    def _generate_simulated_products(self, query: str) -> List[Product]:
        """Generates realistic mock products for testing and demonstration."""
        # Standard Hot Wheels offerings, some matching watchlist, some not
        mock_data = [
            {
                "name": "Hot Wheels Mazda 787B (Race Car)",
                "price": 179.0,
                "url": "https://www.zeptonow.com/pn/hot-wheels-mazda-787b/p/9a38ef12",
                "image": "https://www.zeptonow.com/images/hw_mazda.jpg",
                "availability": "In Stock"
            },
            {
                "name": "Hot Wheels Super Treasure Hunt Porsche 911 GT2",
                "price": 179.0,
                "url": "https://www.zeptonow.com/pn/hot-wheels-sth-porsche/p/9a38ef13",
                "image": "https://www.zeptonow.com/images/hw_sth_porsche.jpg",
                "availability": "In Stock"
            },
            {
                "name": "Hot Wheels Track Builder Straight Track Pack",
                "price": 349.0,
                "url": "https://www.zeptonow.com/pn/hot-wheels-track-builder/p/9a38ef14",
                "image": "https://www.zeptonow.com/images/hw_track.jpg",
                "availability": "In Stock"
            }
        ]
        
        products = []
        for item in mock_data:
            products.append(Product(
                name=item["name"],
                price=item["price"],
                url=item["url"],
                store=self.name,
                image=item["image"],
                availability=item["availability"]
            ))
        return products
