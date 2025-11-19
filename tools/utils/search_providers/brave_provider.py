"""
Brave Search API Provider
Documentation: https://api.search.brave.com/app/documentation/web-search/get-started
"""

import requests
from datetime import datetime
from typing import List

from .base import BaseSearchProvider
from .models import SearchResult, SearchParams


class BraveSearchProvider(BaseSearchProvider):
    """Provider pour Brave Search API"""

    def __init__(self, config):
        super().__init__(config)
        self.api_url = "https://api.search.brave.com/res/v1/web/search"
        self.session = requests.Session()
        self.session.verify = True  # SSL verification explicite

    @property
    def provider_name(self) -> str:
        return "brave"

    def is_available(self) -> bool:
        """Brave nécessite une clé API valide"""
        return self.config.enabled and bool(self.config.api_key)

    def search(self, params: SearchParams) -> List[SearchResult]:
        """
        Effectue une recherche via Brave Search API

        Args:
            params: Paramètres de recherche

        Returns:
            Liste de SearchResult

        Raises:
            requests.exceptions.RequestException: En cas d'erreur API
        """
        if not self.is_available():
            raise RuntimeError("Brave provider non disponible (clé API manquante)")

        def _do_search():
            return self._call_brave_api(params)

        # Utiliser retry avec exponential backoff
        return self._retry_with_backoff(_do_search, self.config.retry_count)

    def _call_brave_api(self, params: SearchParams) -> List[SearchResult]:
        """
        Appelle l'API Brave Search

        Args:
            params: Paramètres de recherche

        Returns:
            Liste de SearchResult normalisés
        """
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.config.api_key,
        }

        api_params = {
            "q": params.query,
            "count": min(params.max_results, self.config.max_results),
            "search_lang": params.lang,
            "country": params.country,
            "text_decorations": False,
            "spellcheck": True,
        }

        try:
            self.logger.debug(f"Appel Brave API: {params.query}")
            response = self.session.get(
                self.api_url,
                headers=headers,
                params=api_params,
                timeout=self.config.timeout,
                verify=True,
            )

            # Gestion des codes HTTP
            if response.status_code == 401:
                self.logger.error("Clé API Brave invalide (401 Unauthorized)")
                raise requests.exceptions.RequestException("Invalid API key")
            elif response.status_code == 429:
                self.logger.warning("Rate limit Brave atteint (429 Too Many Requests)")
                raise requests.exceptions.RequestException("Rate limit exceeded")
            elif response.status_code != 200:
                self.logger.error(
                    f"Erreur API Brave: {response.status_code} - {response.text[:200]}"
                )
                raise requests.exceptions.RequestException(
                    f"HTTP {response.status_code}"
                )

            # Parser la réponse
            data = response.json()
            return self._parse_response(data, params.query)

        except requests.exceptions.Timeout:
            self.logger.warning(f"Timeout API Brave pour: {params.query}")
            raise
        except requests.exceptions.RequestException as e:
            error_msg = self._sanitize_error(str(e))
            self.logger.error(f"Erreur requête Brave API: {error_msg}")
            raise
        except Exception as e:
            self.logger.error(f"Erreur parsing réponse Brave: {e}")
            raise

    def _parse_response(self, data: dict, query: str) -> List[SearchResult]:
        """
        Parse la réponse Brave et extrait les SearchResult

        Format Brave: {web: {results: [{url, title, description}]}}

        Args:
            data: Réponse JSON de Brave
            query: Requête de recherche (pour logs)

        Returns:
            Liste de SearchResult normalisés
        """
        results = []
        date_today = datetime.now().strftime("%Y-%m-%d")

        # Extraire les résultats web
        web_results = data.get("web", {}).get("results", [])

        for i, result in enumerate(web_results[: self.config.max_results]):
            url = result.get("url", "")
            title = result.get("title", "")
            description = result.get("description", "")

            if not url or not title:
                continue

            search_result = SearchResult(
                url=url,
                title=title,
                snippet=description[:300],  # Limiter la longueur
                relevance=self._calculate_relevance(i),
                accessed_date=date_today,
                provider="brave",
            )

            if self.validate_result(search_result):
                results.append(search_result)
                self.logger.debug(f"  Source: {title[:50]}...")

        return results
