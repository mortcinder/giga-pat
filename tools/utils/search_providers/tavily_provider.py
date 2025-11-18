"""
Tavily API Provider (AI-native search)
Documentation: https://docs.tavily.com/
"""

import requests
from datetime import datetime
from typing import List

from .base import BaseSearchProvider
from .models import SearchResult, SearchParams


class TavilySearchProvider(BaseSearchProvider):
    """Provider pour Tavily API (AI-native search)"""

    def __init__(self, config):
        super().__init__(config)
        self.api_url = "https://api.tavily.com/search"

    @property
    def provider_name(self) -> str:
        return "tavily"

    def is_available(self) -> bool:
        """Tavily nécessite une clé API valide"""
        return self.config.enabled and bool(self.config.api_key)

    def search(self, params: SearchParams) -> List[SearchResult]:
        """
        Effectue une recherche via Tavily API

        Args:
            params: Paramètres de recherche

        Returns:
            Liste de SearchResult

        Raises:
            requests.exceptions.RequestException: En cas d'erreur API
        """
        if not self.is_available():
            raise RuntimeError("Tavily provider non disponible (clé API manquante)")

        def _do_search():
            return self._call_tavily_api(params)

        return self._retry_with_backoff(_do_search, self.config.retry_count)

    def _call_tavily_api(self, params: SearchParams) -> List[SearchResult]:
        """
        Appelle l'API Tavily

        Args:
            params: Paramètres de recherche

        Returns:
            Liste de SearchResult normalisés
        """
        headers = {
            "Content-Type": "application/json",
        }

        payload = {
            "api_key": self.config.api_key,
            "query": params.query,
            "max_results": min(params.max_results, self.config.max_results),
            "search_depth": "basic",  # "basic" ou "advanced"
            "include_answer": False,  # Pas besoin de la réponse AI
            "include_raw_content": False,  # Pas besoin du contenu brut
        }

        try:
            self.logger.debug(f"Appel Tavily API: {params.query}")
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=self.config.timeout,
            )

            # Gestion des codes HTTP
            if response.status_code == 401:
                self.logger.error("Clé API Tavily invalide (401 Unauthorized)")
                raise requests.exceptions.RequestException("Invalid API key")
            elif response.status_code == 429:
                self.logger.warning("Rate limit Tavily atteint (429 Too Many Requests)")
                raise requests.exceptions.RequestException("Rate limit exceeded")
            elif response.status_code != 200:
                self.logger.error(
                    f"Erreur API Tavily: {response.status_code} - {response.text[:200]}"
                )
                raise requests.exceptions.RequestException(
                    f"HTTP {response.status_code}"
                )

            # Parser la réponse
            data = response.json()
            return self._parse_response(data, params.query)

        except requests.exceptions.Timeout:
            self.logger.warning(f"Timeout API Tavily pour: {params.query}")
            raise
        except requests.exceptions.RequestException as e:
            error_msg = self._sanitize_error(str(e))
            self.logger.error(f"Erreur requête Tavily API: {error_msg}")
            raise
        except Exception as e:
            self.logger.error(f"Erreur parsing réponse Tavily: {e}")
            raise

    def _parse_response(self, data: dict, query: str) -> List[SearchResult]:
        """
        Parse la réponse Tavily et extrait les SearchResult

        Format Tavily: {results: [{url, title, content, score}]}

        Args:
            data: Réponse JSON de Tavily
            query: Requête de recherche (pour logs)

        Returns:
            Liste de SearchResult normalisés
        """
        results = []
        date_today = datetime.now().strftime("%Y-%m-%d")

        # Extraire les résultats
        tavily_results = data.get("results", [])

        for i, result in enumerate(tavily_results[: self.config.max_results]):
            url = result.get("url", "")
            title = result.get("title", "")
            content = result.get("content", "")
            score = result.get("score", 0)  # Score de pertinence 0-1

            if not url or not title:
                continue

            # Mapper le score Tavily à notre échelle de pertinence
            if score >= 0.7:
                relevance = "Haute"
            elif score >= 0.4:
                relevance = "Moyenne"
            else:
                relevance = "Faible"

            search_result = SearchResult(
                url=url,
                title=title,
                snippet=content[:300],  # Limiter la longueur
                relevance=relevance,
                accessed_date=date_today,
                provider="tavily",
            )

            if self.validate_result(search_result):
                results.append(search_result)
                self.logger.debug(f"  Source: {title[:50]}... (score: {score:.2f})")

        return results
