"""
Module de recherche web multi-provider (v2.0)
Suit les spécifications des sections 3.2.5.5 et 14 du PRD

Architecture v2.0:
- Support multi-provider (Brave, Serper, Tavily, DuckDuckGo)
- Fallback automatique en cas d'échec
- Configuration centralisée dans config.yaml

IMPORTANT: L'API publique reste inchangée pour compatibilité avec analyzer.py
"""

import logging
import time
import random
from typing import List, Dict, Any
from datetime import datetime

from .search_providers import (
    SearchProviderFactory,
    SearchParams,
    BaseSearchProvider,
)


class WebResearcher:
    """
    Gère les recherches web avec support multi-provider
    Section 3.2.5.5 du PRD

    API publique (inchangée pour compatibilité):
    - search(sujet, queries, context) -> List[Dict[str, Any]]
    - get_history() -> List[Dict[str, Any]]
    - get_search_count() -> int
    """

    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.history = []

        web_config = config.get("analyzer", {}).get("web_research", {})
        self.enabled = web_config.get("enabled", True)

        if not self.enabled:
            self.logger.warning("Recherches web désactivées par configuration")
            self.providers = []
            return

        # Initialiser les providers via la Factory
        try:
            factory = SearchProviderFactory()
            enable_fallback = web_config.get("enable_fallback", True)

            if enable_fallback:
                # Mode fallback: chaîne de providers
                self.providers = factory.create_fallback_chain(config)
                self.logger.info(
                    f"WebResearcher v2.0 initialisé avec fallback: "
                    f"{[p.provider_name for p in self.providers]}"
                )
            else:
                # Mode single provider
                primary_provider = web_config.get("provider", "brave")
                provider = factory.create_provider(primary_provider, config)

                if not provider.is_available():
                    self.logger.error(
                        f"Provider {primary_provider} non disponible - "
                        "Recherches web désactivées"
                    )
                    self.enabled = False
                    self.providers = []
                    return

                self.providers = [provider]
                self.logger.info(
                    f"WebResearcher v2.0 initialisé (provider unique: "
                    f"{primary_provider})"
                )

            if not self.providers:
                self.logger.error(
                    "Aucun provider disponible - Recherches web désactivées"
                )
                self.enabled = False

        except Exception as e:
            self.logger.error(f"Erreur initialisation WebResearcher: {e}")
            self.enabled = False
            self.providers = []

    def search(
        self, sujet: str, queries: List[str], context: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Effectue plusieurs recherches web sur un sujet

        API PUBLIQUE - Compatible avec analyzer.py

        Args:
            sujet: Thème général de recherche
            queries: Liste de requêtes à exécuter
            context: Contexte additionnel pour affiner la recherche

        Returns:
            Liste de sources avec URL, titre, extrait, pertinence
            Format: [{"url": str, "titre": str, "extrait": str,
                     "pertinence": str, "date_acces": str}, ...]
        """
        if not self.enabled:
            self.logger.info(
                f"Recherches web désactivées, skip {len(queries)} requêtes"
            )
            return []

        if not self.providers:
            self.logger.warning("Aucun provider disponible")
            return []

        self.logger.info(f"Recherches sur : {sujet} ({len(queries)} requêtes)")
        all_sources = []

        for i, query in enumerate(queries, 1):
            self.logger.info(f"  [{i}/{len(queries)}] {query}")

            # Créer les paramètres de recherche
            search_params = SearchParams(
                query=query, lang="fr", country="FR", max_results=10, context=context
            )

            # Rechercher avec fallback
            results = self._search_with_fallback(search_params)

            # Convertir SearchResult -> dict (format legacy pour compatibilité)
            sources = [result.to_dict() for result in results]
            all_sources.extend(sources)

            # Enregistrer dans l'historique
            self.history.append(
                {
                    "sujet": sujet,
                    "query": query,
                    "date": datetime.now().isoformat(),
                    "sources_found": len(sources),
                    "provider_used": results[0].provider if results else None,
                }
            )

            self.logger.debug(f"    → {len(sources)} sources")

            # Rate limiting (utiliser le rate_limit du premier provider)
            if i < len(queries):  # Pas de sleep après la dernière requête
                wait_time = self._get_rate_limit()
                time.sleep(wait_time)

        # Dédoublonnage par URL
        unique_sources = self._deduplicate_sources(all_sources)

        self.logger.info(f"  Total : {len(unique_sources)} sources uniques")
        return unique_sources

    def _search_with_fallback(self, params: SearchParams) -> List:
        """
        Tente la recherche avec fallback automatique

        Args:
            params: Paramètres de recherche

        Returns:
            Liste de SearchResult (peut être vide si tous les providers échouent)
        """
        for i, provider in enumerate(self.providers, 1):
            try:
                self.logger.debug(
                    f"Tentative {i}/{len(self.providers)}: "
                    f"{provider.provider_name}"
                )

                results = provider.search(params)

                if results:
                    self.logger.info(
                        f"✓ {len(results)} résultats via {provider.provider_name}"
                    )
                    return results
                else:
                    self.logger.debug(
                        f"Aucun résultat via {provider.provider_name}, "
                        "tentative provider suivant..."
                    )

            except Exception as e:
                self.logger.warning(
                    f"✗ Échec {provider.provider_name}: {str(e)[:100]}"
                )

                # Si ce n'est pas le dernier provider, essayer le suivant
                if i < len(self.providers):
                    next_provider = self.providers[i].provider_name
                    self.logger.info(f"→ Fallback vers {next_provider}...")
                    continue

        # Tous les providers ont échoué
        self.logger.error(
            f"Tous les providers ont échoué pour: {params.query[:50]}"
        )
        return []

    def _deduplicate_sources(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Dédoublonne les sources par URL

        Args:
            sources: Liste de sources brutes

        Returns:
            Liste de sources uniques
        """
        unique_sources = []
        seen_urls = set()

        for source in sources:
            url = source.get("url", "")
            if url and url not in seen_urls:
                unique_sources.append(source)
                seen_urls.add(url)

        return unique_sources

    def _get_rate_limit(self) -> float:
        """
        Retourne le rate limit à utiliser entre requêtes

        Utilise le rate_limit du premier provider avec randomisation
        (pour éviter patterns de requêtes prévisibles)

        Returns:
            Secondes à attendre entre requêtes
        """
        if not self.providers:
            return 1.3  # Default

        base_rate = self.providers[0].rate_limit

        # Ajouter randomisation ±10% pour éviter patterns
        min_rate = base_rate * 0.9
        max_rate = base_rate * 1.1

        return random.uniform(min_rate, max_rate)

    def get_history(self) -> List[Dict[str, Any]]:
        """
        Retourne l'historique des recherches effectuées

        Returns:
            Liste des recherches avec métadonnées
        """
        return self.history

    def get_search_count(self) -> int:
        """
        Retourne le nombre total de recherches effectuées

        Returns:
            Nombre de recherches
        """
        return len(self.history)
