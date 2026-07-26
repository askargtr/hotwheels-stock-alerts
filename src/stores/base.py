from abc import ABC, abstractmethod
from typing import List
from src.models import Product

class StoreError(Exception):
    """Exception raised when a store search query fails completely."""
    pass

class BaseStore(ABC):
    """Abstract base class defining the interface for all store adapters."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the name of the store."""
        pass

    @abstractmethod
    def search(self, query: str) -> List[Product]:
        """
        Searches the store for products matching the query.
        
        Args:
            query: The search term (e.g., 'Hot Wheels').
            
        Returns:
            A list of Product objects.
        """
        pass
