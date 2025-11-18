"""
Modèles de données pour les providers de recherche web
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SearchResult:
    """Résultat de recherche normalisé (commun à tous les providers)"""

    url: str
    title: str
    snippet: str
    relevance: str  # "Haute", "Moyenne", "Faible"
    accessed_date: str
    provider: str  # "brave", "serper", "tavily", "ddgs"

    def to_dict(self) -> dict:
        """Convertit en dict pour compatibilité avec code legacy"""
        return {
            "url": self.url,
            "titre": self.title,
            "extrait": self.snippet,
            "pertinence": self.relevance,
            "date_acces": self.accessed_date,
        }


@dataclass
class ProviderConfig:
    """Configuration d'un provider de recherche"""

    name: str
    enabled: bool
    api_key: Optional[str]
    rate_limit: float  # Secondes entre requêtes
    timeout: int  # Timeout en secondes
    max_results: int  # Nombre max de résultats par requête
    retry_count: int  # Nombre de tentatives en cas d'échec
    priority: int  # Priorité pour fallback (1 = highest)


@dataclass
class SearchParams:
    """Paramètres de recherche standardisés"""

    query: str
    lang: str = "fr"
    country: str = "FR"
    max_results: int = 10
    context: str = ""
