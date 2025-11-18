"""
DuckDuckGo Search Provider (via duckduckgo-search library)
Documentation: https://pypi.org/project/duckduckgo-search/
"""

from datetime import datetime
from typing import List

try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False

from .base import BaseSearchProvider
from .models import SearchResult, SearchParams


class DDGSSearchProvider(BaseSearchProvider):
    """Provider pour DuckDuckGo Search (scraping gratuit)"""

    def __init__(self, config):
        super().__init__(config)

        if not DDGS_AVAILABLE:
            self.logger.warning(
                "Module duckduckgo-search non installé. "
                "Installer avec: pip install duckduckgo-search"
            )
            self.ddgs = None
        else:
            self.ddgs = DDGS()

    @property
    def provider_name(self) -> str:
        return "ddgs"

    def is_available(self) -> bool:
        """DuckDuckGo ne nécessite pas de clé API, juste le module"""
        return self.config.enabled and DDGS_AVAILABLE and self.ddgs is not None

    def search(self, params: SearchParams) -> List[SearchResult]:
        """
        Effectue une recherche via DuckDuckGo (scraping)

        Args:
            params: Paramètres de recherche

        Returns:
            Liste de SearchResult

        Raises:
            RuntimeError: Si le provider n'est pas disponible
            Exception: En cas d'erreur de recherche
        """
        if not self.is_available():
            if not DDGS_AVAILABLE:
                raise RuntimeError(
                    "DDGS provider non disponible: "
                    "module duckduckgo-search non installé"
                )
            raise RuntimeError("DDGS provider désactivé")

        def _do_search():
            return self._search_ddgs(params)

        return self._retry_with_backoff(_do_search, self.config.retry_count)

    def _search_ddgs(self, params: SearchParams) -> List[SearchResult]:
        """
        Effectue la recherche DuckDuckGo

        Args:
            params: Paramètres de recherche

        Returns:
            Liste de SearchResult normalisés
        """
        try:
            self.logger.debug(f"Recherche DDGS: {params.query}")

            # Construire la région (format: country-lang, ex: fr-fr)
            region = f"{params.country.lower()}-{params.lang}"

            # Effectuer la recherche
            results = self.ddgs.text(
                keywords=params.query,
                region=region,
                max_results=min(params.max_results, self.config.max_results),
                safesearch="moderate",
            )

            # Parser les résultats
            return self._parse_response(results, params.query)

        except Exception as e:
            self.logger.error(f"Erreur recherche DDGS: {e}")
            raise

    def _parse_response(self, results: list, query: str) -> List[SearchResult]:
        """
        Parse les résultats DDGS et extrait les SearchResult

        Format DDGS: [{href, title, body}]

        Args:
            results: Résultats DDGS
            query: Requête de recherche (pour logs)

        Returns:
            Liste de SearchResult normalisés
        """
        search_results = []
        date_today = datetime.now().strftime("%Y-%m-%d")

        if not results:
            self.logger.debug(f"Aucun résultat DDGS pour: {query}")
            return search_results

        for i, result in enumerate(results[: self.config.max_results]):
            url = result.get("href", "")
            title = result.get("title", "")
            body = result.get("body", "")

            if not url or not title:
                continue

            search_result = SearchResult(
                url=url,
                title=title,
                snippet=body[:300],  # Limiter la longueur
                relevance=self._calculate_relevance(i),
                accessed_date=date_today,
                provider="ddgs",
            )

            if self.validate_result(search_result):
                search_results.append(search_result)
                self.logger.debug(f"  Source: {title[:50]}...")

        return search_results
