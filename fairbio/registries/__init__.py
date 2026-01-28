"""GA4GH clients for service discovery"""

from .ga4gh_registry import GA4GHServiceRegistry
from .trs_registry import ToolRegistryService

__all__ = [
    "GA4GHServiceRegistry",
    "ToolRegistryService"
]
