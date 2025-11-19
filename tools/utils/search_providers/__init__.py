"""
Search providers package - Architecture pluggable pour recherche web

Ce package fournit une architecture extensible pour les recherches web
avec support de multiples providers (Brave, Serper, Tavily, DuckDuckGo).
"""

from .base import BaseSearchProvider
from .models import SearchResult, SearchParams, ProviderConfig
from .factory import SearchProviderFactory
from .brave_provider import BraveSearchProvider
from .serper_provider import SerperSearchProvider
from .tavily_provider import TavilySearchProvider
from .ddgs_provider import DDGSSearchProvider

__all__ = [
    "BaseSearchProvider",
    "SearchResult",
    "SearchParams",
    "ProviderConfig",
    "SearchProviderFactory",
    "BraveSearchProvider",
    "SerperSearchProvider",
    "TavilySearchProvider",
    "DDGSSearchProvider",
]
