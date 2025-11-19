"""
Factory pour créer les providers de recherche web avec support fallback
"""

import os
import logging
from typing import List, Dict, Type

from .base import BaseSearchProvider
from .models import ProviderConfig
from .brave_provider import BraveSearchProvider
from .serper_provider import SerperSearchProvider
from .tavily_provider import TavilySearchProvider
from .ddgs_provider import DDGSSearchProvider


class SearchProviderFactory:
    """Factory pour créer et configurer les providers de recherche"""

    # Registre des providers disponibles
    PROVIDERS: Dict[str, Type[BaseSearchProvider]] = {
        "brave": BraveSearchProvider,
        "serper": SerperSearchProvider,
        "tavily": TavilySearchProvider,
        "ddgs": DDGSSearchProvider,
    }

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def create_provider(
        self, provider_name: str, config: dict
    ) -> BaseSearchProvider:
        """
        Crée un provider depuis la configuration

        Args:
            provider_name: Nom du provider (brave, serper, tavily, ddgs)
            config: Configuration complète (config.yaml)

        Returns:
            Instance du provider configuré

        Raises:
            ValueError: Si le provider est inconnu
            RuntimeError: Si le provider n'est pas disponible
        """
        if provider_name not in self.PROVIDERS:
            raise ValueError(
                f"Provider inconnu: {provider_name}. "
                f"Providers disponibles: {list(self.PROVIDERS.keys())}"
            )

        # Construire la ProviderConfig depuis config.yaml
        provider_config = self._build_provider_config(provider_name, config)

        # Instancier le provider
        provider_class = self.PROVIDERS[provider_name]
        provider = provider_class(provider_config)

        self.logger.debug(
            f"Provider {provider_name} créé: "
            f"enabled={provider_config.enabled}, "
            f"rate_limit={provider_config.rate_limit}s"
        )

        return provider

    def create_fallback_chain(self, config: dict) -> List[BaseSearchProvider]:
        """
        Crée une chaîne de providers avec fallback automatique

        L'ordre est défini par config.yaml → fallback_providers
        Seuls les providers disponibles sont inclus dans la chaîne.

        Args:
            config: Configuration complète (config.yaml)

        Returns:
            Liste de providers triés par priorité (disponibles uniquement)

        Raises:
            RuntimeError: Si aucun provider n'est disponible
        """
        web_config = config.get("analyzer", {}).get("web_research", {})
        fallback_order = web_config.get("fallback_providers", ["brave"])

        providers = []
        unavailable_providers = []

        for provider_name in fallback_order:
            try:
                provider = self.create_provider(provider_name, config)

                if provider.is_available():
                    providers.append(provider)
                    self.logger.info(
                        f"✓ Provider {provider_name} disponible "
                        f"(priorité {len(providers)})"
                    )
                else:
                    unavailable_providers.append(provider_name)
                    reason = self._get_unavailability_reason(provider)
                    self.logger.warning(
                        f"✗ Provider {provider_name} non disponible: {reason}"
                    )

            except Exception as e:
                unavailable_providers.append(provider_name)
                self.logger.warning(
                    f"✗ Provider {provider_name} échec création: {e}"
                )

        if not providers:
            raise RuntimeError(
                f"Aucun provider de recherche disponible. "
                f"Providers tentés: {fallback_order}. "
                f"Non disponibles: {unavailable_providers}"
            )

        self.logger.info(
            f"Chaîne de fallback créée: {[p.provider_name for p in providers]}"
        )
        return providers

    def _build_provider_config(
        self, provider_name: str, config: dict
    ) -> ProviderConfig:
        """
        Construit une ProviderConfig depuis config.yaml

        Args:
            provider_name: Nom du provider
            config: Configuration complète

        Returns:
            ProviderConfig avec tous les paramètres
        """
        web_config = config.get("analyzer", {}).get("web_research", {})
        providers_config = web_config.get("providers", {})
        provider_specific = providers_config.get(provider_name, {})

        # Charger l'API key depuis les variables d'environnement
        api_key_env_var = f"{provider_name.upper()}_API_KEY"
        api_key = os.getenv(api_key_env_var)

        # Construire la config avec fallback sur defaults
        provider_config = ProviderConfig(
            name=provider_name,
            enabled=provider_specific.get("enabled", True),
            api_key=api_key,
            rate_limit=provider_specific.get(
                "rate_limit", web_config.get("default_rate_limit", 1.3)
            ),
            timeout=provider_specific.get(
                "timeout", web_config.get("default_timeout", 30)
            ),
            retry_count=provider_specific.get(
                "retry_count", web_config.get("default_retry_count", 3)
            ),
            max_results=provider_specific.get(
                "max_results", web_config.get("default_max_results", 10)
            ),
            priority=provider_specific.get("priority", 99),
        )

        # Validation et warnings
        self._validate_config(provider_name, provider_config)

        return provider_config

    def _validate_config(self, provider_name: str, config: ProviderConfig):
        """
        Valide la configuration et émet des warnings si nécessaire

        Args:
            provider_name: Nom du provider
            config: Configuration à valider
        """
        # Warning si rate_limit trop faible
        if config.rate_limit < 0.5:
            self.logger.warning(
                f"{provider_name}: rate_limit={config.rate_limit}s est très faible, "
                "risque de blocage API"
            )

        # Warning si timeout trop court
        if config.timeout < 10:
            self.logger.warning(
                f"{provider_name}: timeout={config.timeout}s est très court"
            )

        # Warning si retry_count élevé
        if config.retry_count > 5:
            self.logger.warning(
                f"{provider_name}: retry_count={config.retry_count} est élevé, "
                "temps d'attente potentiellement long"
            )

        # Warning si clé API manquante pour providers qui en ont besoin
        if provider_name in ["brave", "serper", "tavily"] and not config.api_key:
            self.logger.warning(
                f"{provider_name}: Clé API manquante "
                f"({provider_name.upper()}_API_KEY non définie). "
                f"Provider sera non disponible."
            )

    def _get_unavailability_reason(self, provider: BaseSearchProvider) -> str:
        """
        Détermine la raison pour laquelle un provider n'est pas disponible

        Args:
            provider: Provider à analyser

        Returns:
            Raison d'indisponibilité
        """
        if not provider.config.enabled:
            return "désactivé dans config.yaml"

        if provider.provider_name in ["brave", "serper", "tavily"]:
            if not provider.config.api_key:
                return f"clé API manquante ({provider.provider_name.upper()}_API_KEY)"

        if provider.provider_name == "ddgs":
            try:
                from duckduckgo_search import DDGS
                return "raison inconnue"
            except ImportError:
                return "module duckduckgo-search non installé"

        return "raison inconnue"
