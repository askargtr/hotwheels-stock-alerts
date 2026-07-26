import os
import logging
import requests
from typing import List, Dict, Any
from urllib3.util import Retry
from requests.adapters import HTTPAdapter
from src.stores.base import BaseStore, StoreError
from src.models import Product

logger = logging.getLogger(__name__)

class BlinkitStore(BaseStore):
    """Store adapter for Blinkit (formerly Grofers)."""

    def __init__(self, location: str):
        self.location = location
        self.session = requests.Session()
        
        # Configure a realistic User-Agent and headers
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://blinkit.com",
            "Referer": "https://blinkit.com/"
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
        return "Blinkit"

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
            # If it's a code/pincode, pass it in headers or query params
            headers["x-location-id"] = self.location.strip()
        return headers

    def _build_request(self, query: str) -> Dict[str, Any]:
        """Builds URL, headers, and parameters for the Blinkit search request."""
        loc_headers = self._parse_location()
        search_url = "https://grofers.com/v4/search/"
        params = {
            "q": query,
            "start": 0,
            "size": 30
        }
        headers = {**self.session.headers, **loc_headers}
        return {
            "url": search_url,
            "params": params,
            "headers": headers
        }

    def search(self, query: str) -> List[Product]:
        """Searches Blinkit for products matching the query."""
        req_config = self._build_request(query)
        
        try:
            logger.info(f"Searching {self.name} for '{query}'...")
            # Use 8 seconds connection/read timeout
            response = self.session.get(
                req_config["url"],
                params=req_config["params"],
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
                    raise StoreError(f"Blinkit API returned status code {response.status_code}")
                
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
        """Parses Blinkit search JSON response into Product dataclasses."""
        products = []
        try:
            # Internal schema traversal
            items = data.get("products", []) or data.get("data", {}).get("products", [])
            if not items and "results" in data:
                items = data["results"]
                
            for item in items:
                name = item.get("name") or item.get("title", "")
                price = item.get("price") or item.get("mrp") or 0.0
                
                # Normalize unit or pack details
                if not name:
                    continue
                    
                product_id = item.get("id") or item.get("product_id", "")
                slug = item.get("slug") or f"product-{product_id}"
                url = f"https://blinkit.com/prn/{slug}/prid/{product_id}" if product_id else "https://blinkit.com"
                
                image = item.get("image_url") or item.get("image", "")
                
                # Check stock status
                in_stock = item.get("in_stock", True)
                availability = "In Stock" if in_stock else "Out of Stock"
                
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
                "name": "Hot Wheels Nissan Skyline GT-R (R33) Diecast Car",
                "price": 179.0,
                "url": "https://blinkit.com/prn/hot-wheels-nissan-skyline-gt-r-r33/prid/482910",
                "image": "https://blinkit.com/images/hw_skyline.jpg",
                "availability": "In Stock"
            },
            {
                "name": "Hot Wheels Porsche 911 GT3 RS",
                "price": 179.0,
                "url": "https://blinkit.com/prn/hot-wheels-porsche-911-gt3/prid/482911",
                "image": "https://blinkit.com/images/hw_porsche.jpg",
                "availability": "In Stock"
            },
            {
                "name": "Hot Wheels HW Metro Bus (Red)",
                "price": 179.0,
                "url": "https://blinkit.com/prn/hot-wheels-hw-metro-bus/prid/482912",
                "image": "https://blinkit.com/images/hw_bus.jpg",
                "availability": "In Stock"
            },
            {
                "name": "Hot Wheels Toyota Supra Mk4 Black",
                "price": 179.0,
                "url": "https://blinkit.com/prn/hot-wheels-toyota-supra/prid/482913",
                "image": "https://blinkit.com/images/hw_supra.jpg",
                "availability": "Out of Stock"  # Should be ignored by the checker because it is out of stock
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
