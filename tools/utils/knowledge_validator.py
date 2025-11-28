"""
Validateur de bonnes pratiques patrimoniales via recherche web

Ce module valide les seuils et règles de gestion patrimoniale en interrogeant
des sources fiables (AMF, CGP, médias finance) et en extrayant un consensus.
"""

import logging
import re
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

from tools.utils.web_research import WebResearcher
from tools.utils.tavily_search import TavilySearcher
from tools.cache_manager import CacheManager


class KnowledgeValidator:
    """
    Valide les seuils et bonnes pratiques en interrogeant sources web
    et en extrayant un consensus depuis sources fiables
    """

    def __init__(self, config: dict, knowledge_config: dict):
        self.config = config
        self.knowledge_config = knowledge_config
        self.logger = logging.getLogger(__name__)

        # Moteurs de recherche
        self.brave_searcher = WebResearcher(config)
        self.tavily_searcher = TavilySearcher(config)

        # Cache
        self.cache = CacheManager("generated/cache")

        # Paramètres
        parametres = knowledge_config.get("parametres", {})
        self.cache_duree_mois = parametres.get("cache_duree_mois", 3)
        self.min_sources = parametres.get("min_sources", 2)
        self.moteur_par_defaut = parametres.get("moteur_par_defaut", "tavily")

    def validate_threshold(self, threshold_key: str) -> Optional[Dict[str, Any]]:
        """
        Valide un seuil en interrogeant sources web

        Args:
            threshold_key: Clé dans recommendations_knowledge.yaml
                          (ex: "montant_minimum_livret")

        Returns:
            {
                "valeur": float/int,
                "unite": str,
                "confiance": "high"/"medium"/"low",
                "sources": [{url, titre, extrait, domain, institution}],
                "nombre_sources_analysees": int
            }
            ou None si pas assez de sources
        """
        # Vérifier cache d'abord
        cache_key = f"reco_knowledge_{threshold_key}"
        cached = self._check_cache(cache_key, threshold_key)
        if cached:
            self.logger.info(f"✓ Knowledge cache hit: {threshold_key}")
            return cached

        # Récupérer config de la requête
        query_config = self.knowledge_config.get("requetes_validation", {}).get(threshold_key)
        if not query_config:
            self.logger.warning(f"Threshold {threshold_key} non trouvé dans knowledge config")
            return None

        # Recherche web
        self.logger.info(f"Validation web de '{threshold_key}'...")
        sources = self._search_knowledge(query_config)

        if not sources:
            self.logger.warning(f"Aucune source trouvée pour {threshold_key}")
            return None

        # Extraction consensus
        consensus = self._extract_consensus(sources, query_config)

        # Vérifier confiance minimum
        if consensus["confiance"] == "low" or len(consensus["sources"]) < self.min_sources:
            self.logger.warning(
                f"Pas assez de sources fiables pour {threshold_key} "
                f"({len(consensus['sources'])} < {self.min_sources})"
            )
            return None

        # Sauvegarder en cache
        self._save_to_cache(cache_key, consensus, query_config)

        self.logger.info(
            f"✓ Consensus validé pour {threshold_key}: "
            f"{consensus['valeur']}{consensus['unite']} "
            f"(confiance: {consensus['confiance']}, {len(consensus['sources'])} sources)"
        )

        return consensus

    def _search_knowledge(self, query_config: dict) -> List[Dict[str, Any]]:
        """Effectue recherche web selon config"""
        queries = query_config.get("queries", [])
        moteur = query_config.get("moteur", self.moteur_par_defaut)

        all_sources = []

        for query in queries:
            if moteur == "tavily":
                # Utiliser Tavily avec domaines fiables
                trusted_domains = self.knowledge_config.get("sources_fiables", {}).get("institutions", [])
                sources = self.tavily_searcher.search(
                    query,
                    search_depth="advanced",
                    include_domains=trusted_domains if trusted_domains else None,
                    max_results=5
                )
            else:  # brave
                sources = self.brave_searcher.search(
                    "gestion patrimoine",  # sujet
                    [query],
                    context="bonnes pratiques CGP"
                )

            all_sources.extend(sources)

        return all_sources

    def _extract_consensus(self, sources: List[Dict], query_config: dict) -> Dict[str, Any]:
        """
        Extrait consensus des sources

        Stratégie:
        - Parser les extraits pour trouver valeurs (ex: "12 mois", "50%")
        - Compter fréquence de chaque valeur
        - Retourner valeur médiane dans la fourchette attendue
        """
        valeur_attendue = query_config.get("valeur_attendue", {})
        value_type = valeur_attendue.get("type")  # "pourcentage", "entier", "montant", "mois"
        value_range = valeur_attendue.get("fourchette", [0, 999999])

        # Extraire toutes les valeurs mentionnées
        found_values = []

        for source in sources:
            extrait = source.get("extrait", "")

            # Extraction selon type
            if value_type == "pourcentage":
                # Chercher "50%", "50 %", "50 pour cent"
                matches = re.findall(
                    r'(\d+(?:[.,]\d+)?)\s*(?:%|pour\s*cent|pourcent)',
                    extrait,
                    re.IGNORECASE
                )
                for m in matches:
                    try:
                        found_values.append(float(m.replace(',', '.')))
                    except ValueError:
                        pass

            elif value_type in ["entier", "mois"]:
                # Chercher "12 mois", "3 établissements", "5 banques"
                matches = re.findall(
                    r'(\d+)\s*(?:mois|établissement|compte|banque|an|année)',
                    extrait,
                    re.IGNORECASE
                )
                for m in matches:
                    try:
                        found_values.append(int(m))
                    except ValueError:
                        pass

            elif value_type == "montant":
                # Chercher "10000 €", "10 000€", "10k€"
                matches = re.findall(
                    r'(\d+(?:\s?\d{3})*)\s*(?:€|EUR|euros?)',
                    extrait,
                    re.IGNORECASE
                )
                for m in matches:
                    try:
                        found_values.append(int(m.replace(' ', '')))
                    except ValueError:
                        pass

        # Filtrer valeurs dans range attendu
        valid_values = [v for v in found_values if value_range[0] <= v <= value_range[1]]

        if not valid_values:
            return {
                "valeur": None,
                "unite": self._get_unit(value_type),
                "confiance": "low",
                "sources": self._prioritize_sources(sources)[:3],
                "nombre_sources_analysees": len(sources)
            }

        # Calculer valeur consensuelle (médiane)
        valid_values.sort()
        median_value = valid_values[len(valid_values) // 2]

        # Calculer confiance (basé sur nb sources et cohérence)
        num_sources = len(sources)
        value_variance = max(valid_values) - min(valid_values) if len(valid_values) > 1 else 0
        expected_variance = (value_range[1] - value_range[0]) * 0.3

        if num_sources >= 3 and value_variance < expected_variance:
            confiance = "high"
        elif num_sources >= 2:
            confiance = "medium"
        else:
            confiance = "low"

        # Prioriser sources institutionnelles
        prioritized_sources = self._prioritize_sources(sources)

        return {
            "valeur": median_value,
            "unite": self._get_unit(value_type),
            "confiance": confiance,
            "sources": prioritized_sources[:3],  # Max 3 sources
            "nombre_sources_analysees": num_sources
        }

    def _prioritize_sources(self, sources: List[Dict]) -> List[Dict]:
        """Priorise sources institutionnelles et médias finance"""
        trusted_domains_lists = self.knowledge_config.get("sources_fiables", {})
        trusted_domains = (
            trusted_domains_lists.get("institutions", []) +
            trusted_domains_lists.get("media_finance", [])
        )

        prioritized = []
        other = []

        for source in sources:
            url = source.get("url", "")
            domain = self._extract_domain(url)
            is_trusted = any(trusted in domain for trusted in trusted_domains)

            # Enrichir la source
            source["domain"] = domain
            source["institution"] = is_trusted

            if is_trusted:
                prioritized.append(source)
            else:
                other.append(source)

        # Retourner d'abord les sources fiables, puis les autres
        return prioritized + other

    def _get_unit(self, value_type: str) -> str:
        """Retourne l'unité selon le type"""
        units = {
            "pourcentage": "%",
            "montant": "€",
            "mois": " mois",
            "entier": ""
        }
        return units.get(value_type, "")

    def _extract_domain(self, url: str) -> str:
        """Extrait le domaine d'une URL"""
        match = re.search(r'(?:https?://)?(?:www\.)?([^/]+)', url)
        return match.group(1) if match else ""

    def _check_cache(self, cache_key: str, threshold_key: str) -> Optional[Dict]:
        """Vérifie si knowledge est en cache et valide"""
        cached = self.cache.load_from_cache(cache_key)
        if not cached:
            return None

        # Vérifier expiration
        metadata = cached.get("_metadata", {})
        custom_meta = metadata.get("custom_metadata", {})

        expires_at_str = custom_meta.get("expires_at")
        if not expires_at_str:
            # Cache ancien sans expiration, considérer comme expiré
            return None

        try:
            expires_at = datetime.fromisoformat(expires_at_str)
            if datetime.now() > expires_at:
                self.logger.debug(f"Cache expiré pour {cache_key}")
                return None
        except (ValueError, TypeError):
            return None

        # Retourner les données (premier élément de la liste)
        data_list = cached.get("data", [])
        return data_list[0] if data_list else None

    def _save_to_cache(self, cache_key: str, data: Dict, query_config: dict) -> None:
        """Sauvegarde knowledge en cache"""
        # Déterminer durée de cache (spécifique à la query ou global)
        cache_duree_mois = query_config.get("cache_duree_mois", self.cache_duree_mois)
        expires_at = datetime.now() + timedelta(days=cache_duree_mois * 30)

        # CacheManager attend file_path, on simule
        fake_path = f"/cache/{cache_key}.json"

        self.cache.save_to_cache(
            cache_key,
            fake_path,
            [data],  # CacheManager attend une liste
            metadata={
                "type": "knowledge_validation",
                "expires_at": expires_at.isoformat(),
                "cache_duree_mois": cache_duree_mois
            }
        )
