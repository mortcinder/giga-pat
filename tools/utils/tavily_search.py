"""
Module de recherche web via Tavily API
Spécialisé pour extraction de consensus et bonnes pratiques

Tavily est optimisé pour les recherches AI avec extraction automatique
de contenu pertinent et filtrage de qualité.
"""

import os
import logging
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime


class TavilySearcher:
    """
    Recherche web optimisée pour extraction de consensus via Tavily
    """

    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.api_key = os.environ.get("TAVILY_API_KEY")
        self.api_url = "https://api.tavily.com/search"
        self.enabled = bool(self.api_key)
        self.timeout = config.get("analyzer", {}).get("web_research", {}).get("timeout_seconds", 30)

        if not self.enabled:
            self.logger.warning("TAVILY_API_KEY non définie - Tavily désactivé")

    def search(
        self,
        query: str,
        search_depth: str = "advanced",
        include_domains: Optional[List[str]] = None,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Effectue une recherche Tavily optimisée pour consensus

        Args:
            query: Requête de recherche
            search_depth: "basic" ou "advanced" (plus de sources)
            include_domains: Liste de domaines à prioriser
            max_results: Nombre de résultats max

        Returns:
            Liste de sources avec extraction AI
        """
        if not self.enabled:
            self.logger.debug("Tavily désactivé, skip recherche")
            return []

        try:
            payload = {
                "api_key": self.api_key,
                "query": query,
                "search_depth": search_depth,
                "max_results": max_results,
                "include_answer": True,  # Tavily génère un résumé
                "include_raw_content": False
            }

            if include_domains:
                payload["include_domains"] = include_domains

            self.logger.debug(f"Appel Tavily API: {query}")

            response = requests.post(
                self.api_url,
                json=payload,
                timeout=self.timeout
            )

            if response.status_code == 401:
                self.logger.error("Clé API Tavily invalide (401 Unauthorized)")
                return []
            elif response.status_code == 429:
                self.logger.warning("Rate limit Tavily atteint (429 Too Many Requests)")
                return []
            elif response.status_code != 200:
                self.logger.error(f"Erreur Tavily API: {response.status_code} - {response.text}")
                return []

            data = response.json()
            return self._parse_tavily_response(data, query)

        except requests.exceptions.Timeout:
            self.logger.warning(f"Timeout Tavily API pour: {query}")
            return []
        except Exception as e:
            self.logger.error(f"Erreur Tavily search: {e}")
            return []

    def _parse_tavily_response(self, data: dict, query: str) -> List[Dict[str, Any]]:
        """Parse réponse Tavily et extrait les sources"""
        sources = []
        date_today = datetime.now().strftime("%Y-%m-%d")

        # Résumé AI (utile pour consensus)
        ai_answer = data.get("answer", "")

        # Résultats de recherche
        for result in data.get("results", []):
            url = result.get("url", "")
            title = result.get("title", "")
            content = result.get("content", "")
            score = result.get("score", 0.0)

            if not url or not title:
                continue

            # Pertinence basée sur le score Tavily
            if score > 0.8:
                pertinence = "Haute"
            elif score > 0.5:
                pertinence = "Moyenne"
            else:
                pertinence = "Faible"

            source = {
                "url": url,
                "titre": title,
                "extrait": content[:300] if content else "",
                "score": score,
                "pertinence": pertinence,
                "date_acces": date_today
            }

            sources.append(source)
            self.logger.debug(f"  Source Tavily: {title[:50]}... (score: {score:.2f})")

        if sources:
            self.logger.info(f"Tavily: {len(sources)} sources pour '{query}'")

        return sources

    def get_answer(self, query: str) -> Optional[str]:
        """
        Obtient uniquement le résumé AI de Tavily (sans sources détaillées)
        Utile pour extraction rapide de consensus
        """
        if not self.enabled:
            return None

        try:
            payload = {
                "api_key": self.api_key,
                "query": query,
                "search_depth": "basic",
                "max_results": 3,
                "include_answer": True,
                "include_raw_content": False
            }

            response = requests.post(
                self.api_url,
                json=payload,
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("answer", "")
            else:
                return None

        except Exception as e:
            self.logger.error(f"Erreur Tavily get_answer: {e}")
            return None
