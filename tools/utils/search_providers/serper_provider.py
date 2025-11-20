"""
Serper API Provider (Google Search Results)
Documentation: https://serper.dev/
"""

import requests
from datetime import datetime
from typing import List

from .base import BaseSearchProvider
from .models import SearchResult, SearchParams


class SerperSearchProvider(BaseSearchProvider):
    """Provider pour Serper API (Google Search)"""

    def __init__(self, config):
        super().__init__(config)
        self.api_url = "https://google.serper.dev/search"

    @property
    def provider_name(self) -> str:
        return "serper"

    def is_available(self) -> bool:
        """Serper nécessite une clé API valide"""
        return self.config.enabled and bool(self.config.api_key)

    def search(self, params: SearchParams) -> List[SearchResult]:
        """
        Effectue une recherche via Serper API

        Args:
            params: Paramètres de recherche

        Returns:
            Liste de SearchResult

        Raises:
            requests.exceptions.RequestException: En cas d'erreur API
        """
        if not self.is_available():
            raise RuntimeError("Serper provider non disponible (clé API manquante)")

        def _do_search():
            return self._call_serper_api(params)

        return self._retry_with_backoff(_do_search, self.config.retry_count)

    def _call_serper_api(self, params: SearchParams) -> List[SearchResult]:
        """
        Appelle l'API Serper

        Args:
            params: Paramètres de recherche

        Returns:
            Liste de SearchResult normalisés
        """
        headers = {
            "X-API-KEY": self.config.api_key,
            "Content-Type": "application/json",
        }

        payload = {
            "q": params.query,
            "num": min(params.max_results, self.config.max_results),
            "gl": params.country.lower(),  # Country code
            "hl": params.lang,  # Language
        }

        try:
            self.logger.debug(f"Appel Serper API: {params.query}")
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=self.config.timeout,
            )

            # Gestion des codes HTTP
            if response.status_code == 401:
                self.logger.error("Clé API Serper invalide (401 Unauthorized)")
                raise requests.exceptions.RequestException("Invalid API key")
            elif response.status_code == 429:
                self.logger.warning("Rate limit Serper atteint (429 Too Many Requests)")
                raise requests.exceptions.RequestException("Rate limit exceeded")
            elif response.status_code != 200:
                self.logger.error(
                    f"Erreur API Serper: {response.status_code} - {response.text[:200]}"
                )
                raise requests.exceptions.RequestException(
                    f"HTTP {response.status_code}"
                )

            # Parser la réponse
            data = response.json()
            return self._parse_response(data, params.query)

        except requests.exceptions.Timeout:
            self.logger.warning(f"Timeout API Serper pour: {params.query}")
            raise
        except requests.exceptions.RequestException as e:
            error_msg = self._sanitize_error(str(e))
            self.logger.error(f"Erreur requête Serper API: {error_msg}")
            raise
        except Exception as e:
            self.logger.error(f"Erreur parsing réponse Serper: {e}")
            raise

    def _parse_response(self, data: dict, query: str) -> List[SearchResult]:
        """
        Parse la réponse Serper et extrait les SearchResult

        Format Serper: {organic: [{link, title, snippet}]}

        Args:
            data: Réponse JSON de Serper
            query: Requête de recherche (pour logs)

        Returns:
            Liste de SearchResult normalisés
        """
        results = []
        date_today = datetime.now().strftime("%Y-%m-%d")

        # Extraire les résultats organiques
        organic_results = data.get("organic", [])

        for i, result in enumerate(organic_results[: self.config.max_results]):
            url = result.get("link", "")
            title = result.get("title", "")
            snippet = result.get("snippet", "")

            if not url or not title:
                continue

            search_result = SearchResult(
                url=url,
                title=title,
                snippet=snippet[:300],  # Limiter la longueur
                relevance=self._calculate_relevance(i),
                accessed_date=date_today,
                provider="serper",
            )

            if self.validate_result(search_result):
                results.append(search_result)
                self.logger.debug(f"  Source: {title[:50]}...")

        return results
