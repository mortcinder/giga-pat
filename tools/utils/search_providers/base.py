"""
Classe abstraite de base pour les providers de recherche web
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import List

from .models import SearchResult, SearchParams, ProviderConfig


class BaseSearchProvider(ABC):
    """
    Interface commune pour tous les providers de recherche web

    Tous les providers (Brave, Serper, Tavily, DDGS) doivent implémenter
    cette interface pour assurer l'interopérabilité.
    """

    def __init__(self, config: ProviderConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def search(self, params: SearchParams) -> List[SearchResult]:
        """
        Effectue une recherche et retourne des résultats normalisés

        Args:
            params: Paramètres de recherche (query, lang, country, etc.)

        Returns:
            Liste de SearchResult normalisés

        Raises:
            Exception: En cas d'erreur (timeout, API error, etc.)
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Vérifie si le provider est disponible

        Returns:
            True si le provider est utilisable (clé API valide, enabled, etc.)
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Nom du provider

        Returns:
            Nom du provider (brave, serper, tavily, ddgs)
        """
        pass

    @property
    def rate_limit(self) -> float:
        """
        Délai minimum entre requêtes (secondes)

        Returns:
            Secondes à attendre entre deux requêtes
        """
        return self.config.rate_limit

    def validate_result(self, result: SearchResult) -> bool:
        """
        Valide qu'un résultat a tous les champs requis

        Args:
            result: Résultat à valider

        Returns:
            True si le résultat est valide
        """
        return bool(result.url and result.title)

    def _calculate_relevance(self, position: int) -> str:
        """
        Calcule la pertinence basée sur la position dans les résultats

        Args:
            position: Position dans les résultats (0-indexed)

        Returns:
            "Haute", "Moyenne", ou "Faible"
        """
        if position <= 1:
            return "Haute"
        elif position <= 3:
            return "Moyenne"
        else:
            return "Faible"

    def _sanitize_error(self, error_msg: str) -> str:
        """
        Masque les clés API dans les messages d'erreur

        Args:
            error_msg: Message d'erreur brut

        Returns:
            Message d'erreur avec clés API masquées
        """
        if self.config.api_key and self.config.api_key in error_msg:
            return error_msg.replace(self.config.api_key, "[REDACTED]")
        return error_msg

    def _retry_with_backoff(self, func, max_retries: int = None):
        """
        Exécute une fonction avec retry et exponential backoff

        Args:
            func: Fonction à exécuter
            max_retries: Nombre max de tentatives (None = utiliser config)

        Returns:
            Résultat de la fonction

        Raises:
            Exception: Si toutes les tentatives échouent
        """
        retries = max_retries or self.config.retry_count
        last_exception = None

        for attempt in range(retries):
            try:
                return func()
            except Exception as e:
                last_exception = e
                if attempt == retries - 1:
                    # Dernière tentative échouée
                    break

                # Exponential backoff: 1s, 2s, 4s, 8s...
                wait_time = 2**attempt
                self.logger.warning(
                    f"Tentative {attempt + 1}/{retries} échouée, "
                    f"retry dans {wait_time}s... ({self._sanitize_error(str(e))})"
                )
                time.sleep(wait_time)

        # Toutes les tentatives ont échoué
        raise last_exception
