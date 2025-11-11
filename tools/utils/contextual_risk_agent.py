"""
Agent autonome de détection de risques contextuels
Conçu pour exécution parallèle via threading

Ce module encapsule la logique d'analyse contextuelle (veille économique,
réglementaire, fiscale) pour permettre une exécution indépendante et parallèle
de l'analyse structurelle du patrimoine.

Architecture multi-agents (v2.1):
- Agent principal: Analyse risques structurels
- Agent contextuel: Détection risques émergents (ce module)
"""

import logging
import yaml
import os
from typing import Dict, List, Any, Optional
from datetime import datetime


class ContextualRiskAgent:
    """
    Agent spécialisé dans la détection de risques contextuels via web research.

    Cet agent est conçu pour s'exécuter en parallèle de l'analyse
    structurelle du patrimoine, permettant un gain de performance global.

    Il surveille l'actualité économique, réglementaire et fiscale française
    pour détecter des risques émergents, en utilisant les recherches web
    configurées dans config/risks.yaml.

    Usage:
        >>> from tools.utils.contextual_risk_agent import ContextualRiskAgent
        >>> agent = ContextualRiskAgent(config, web_researcher)
        >>> result = agent.analyze(patrimoine_data)
        >>> print(result["risks"])  # Liste des risques détectés

    Attributes:
        config (dict): Configuration complète du projet
        web_researcher (WebResearcher): Instance pour recherches Brave API
        contextual_searches (dict): Recherches configurées dans risks.yaml

    See Also:
        - tools/utils/risk_analyzer.py : Analyse risques structurels
        - config/risks.yaml : Configuration des recherches contextuelles
        - CLAUDE.md : Documentation architecture multi-agents
    """

    def __init__(self, config: dict, web_researcher):
        """
        Initialise l'agent contextuel.

        Args:
            config: Configuration complète (chargée depuis config/config.yaml)
            web_researcher: Instance de WebResearcher pour les recherches web
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.web_researcher = web_researcher

        # Charger risks.yaml
        self.risk_definitions = self._load_risk_definitions()
        self.contextual_searches = self.risk_definitions.get("contextual_searches", {})
        self.risk_settings = self.risk_definitions.get("risk_settings", {})

        # Compteur pour IDs uniques (commence à 1000 pour éviter conflits)
        self.risk_id_counter = 1000

        self.logger.info("ContextualRiskAgent initialisé")

    def analyze(self, patrimoine_data: dict) -> dict:
        """
        Point d'entrée principal - Détecte les risques contextuels.

        Args:
            patrimoine_data: Données normalisées du patrimoine

        Returns:
            {
                "risks": [
                    {
                        "id": "RISK_1001",
                        "titre": "Évolution réglementaire économique France",
                        "description": "...",
                        "niveau": "Moyen",
                        "categorie": "Réglementaire - Contexte",
                        "sources_web": [...]
                    },
                    ...
                ],
                "meta": {
                    "searches_executed": 6,
                    "duration_seconds": 14.2,
                    "risks_detected": 2,
                    "timestamp": "2025-11-11T14:23:10"
                }
            }
        """
        start_time = datetime.now()
        self.logger.info("Début analyse risques contextuels (agent parallèle)...")

        risks = []
        searches_executed = 0

        if not self.contextual_searches:
            self.logger.info("    Aucune recherche contextuelle configurée")
            return self._build_result(risks, searches_executed, start_time)

        # Parcourir les recherches contextuelles configurées
        for search_id, search_config in self.contextual_searches.items():
            if not search_config.get("enabled", False):
                continue

            priority = search_config.get("priority", "medium")
            queries = search_config.get("queries", [])
            context = search_config.get("analysis_context", "")

            self.logger.info(f"    → Recherche contextuelle: {search_id} (priorité: {priority})")

            # Exécuter recherche web
            search_results = self.web_researcher.search(
                sujet=f"Contexte: {search_id}",
                queries=queries,
                context=context
            )

            searches_executed += 1

            if not search_results:
                self.logger.info(f"      Aucun résultat pertinent pour {search_id}")
                continue

            # Analyser résultats et générer risques
            detected_risks = self._analyze_search_results(
                search_id=search_id,
                search_config=search_config,
                search_results=search_results,
                patrimoine_data=patrimoine_data
            )

            risks.extend(detected_risks)
            self.logger.info(f"      ✓ {len(detected_risks)} risques détectés")

        duration = (datetime.now() - start_time).total_seconds()
        self.logger.info(f"✓ Analyse contextuelle terminée : "
                        f"{len(risks)} risques en {duration:.1f}s")

        return self._build_result(risks, searches_executed, start_time)

    def _build_result(self, risks: List[Dict], searches_executed: int, start_time: datetime) -> dict:
        """Construit le résultat final de l'agent"""
        duration = (datetime.now() - start_time).total_seconds()

        return {
            "risks": risks,
            "meta": {
                "searches_executed": searches_executed,
                "duration_seconds": round(duration, 1),
                "risks_detected": len(risks),
                "timestamp": datetime.now().isoformat()
            }
        }

    def _load_risk_definitions(self) -> dict:
        """
        Charge les définitions de risques depuis config/risks.yaml
        Retourne un dictionnaire avec les règles structurelles et contextuelles
        """
        risks_config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "config",
            "risks.yaml"
        )

        try:
            if os.path.exists(risks_config_path):
                with open(risks_config_path, "r", encoding="utf-8") as f:
                    risk_defs = yaml.safe_load(f)
                    self.logger.info(f"✓ Définitions de risques chargées depuis {risks_config_path}")
                    return risk_defs
            else:
                self.logger.warning(f"Fichier {risks_config_path} introuvable")
                return {}
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement de {risks_config_path}: {e}")
            return {}

    def _analyze_search_results(
        self,
        search_id: str,
        search_config: dict,
        search_results: List[Dict],
        patrimoine_data: dict
    ) -> List[Dict[str, Any]]:
        """
        Génère des risques depuis les résultats de recherche.

        Args:
            search_id: ID de la recherche (ex: "actualite_economique_france")
            search_config: Configuration de la recherche
            search_results: Résultats web
            patrimoine_data: Données patrimoine pour calcul exposition

        Returns:
            Liste de risques détectés
        """
        risks = []
        max_risks = self.risk_settings.get("max_contextual_risks_per_search", 3)

        # Mapper search_id vers catégorie et niveau de risque appropriés
        risk_mapping = self._get_contextual_risk_mapping(search_id, patrimoine_data)

        if not risk_mapping:
            return risks

        # Générer un risque contextuel basé sur les résultats web
        # On regroupe les sources pour créer un risque synthétique
        if len(search_results) >= 2:  # Minimum 2 sources pour confirmer un risque
            risk = {
                "id": self._get_risk_id(),
                "titre": risk_mapping["titre"],
                "description": risk_mapping["description"],
                "exposition_montant": risk_mapping.get("exposition_montant", 0),
                "exposition_pct": risk_mapping.get("exposition_pct", 0),
                "probabilite": risk_mapping["probabilite"],
                "impact": risk_mapping["impact"],
                "niveau": risk_mapping["niveau"],
                "categorie": risk_mapping["categorie"],
                "sources_web": search_results[:max_risks]  # Limiter les sources
            }
            risks.append(risk)

        return risks

    def _get_contextual_risk_mapping(
        self,
        search_id: str,
        patrimoine_data: dict
    ) -> Optional[Dict[str, Any]]:
        """
        Mappe un search_id vers les propriétés du risque contextuel

        Cette méthode analyse le patrimoine pour déterminer si le risque
        contextuel est pertinent et génère les métadonnées appropriées.

        Args:
            search_id: Identifiant de la recherche contextuelle
            patrimoine_data: Données du patrimoine

        Returns:
            Dictionnaire avec propriétés du risque ou None si non pertinent
        """
        total_patrimoine = (
            patrimoine_data.get("patrimoine", {}).get("financier", {}).get("total", 0) +
            patrimoine_data.get("patrimoine", {}).get("crypto", {}).get("total", 0) +
            patrimoine_data.get("patrimoine", {}).get("immobilier", {}).get("total", 0)
        )

        # Mapping des recherches contextuelles vers risques
        mappings = {
            "actualite_economique_france": {
                "titre": "Évolution réglementaire économique France",
                "description": "Des évolutions réglementaires ou économiques récentes en France "
                              "peuvent impacter l'épargne et les investissements. "
                              "Consulter les sources web pour plus de détails.",
                "probabilite": "Moyenne",
                "impact": "Moyen",
                "niveau": "Moyen",
                "categorie": "Réglementaire - Contexte",
                "exposition_montant": patrimoine_data.get("patrimoine", {}).get("financier", {}).get("total", 0),
                "exposition_pct": 0
            },
            "risques_bancaires": {
                "titre": "Risques système bancaire français",
                "description": "Des signaux d'alerte concernant la stabilité du système bancaire "
                              "ont été identifiés dans l'actualité récente. "
                              "Une vigilance accrue est recommandée.",
                "probabilite": "Faible",
                "impact": "Élevé",
                "niveau": "Élevé",
                "categorie": "Concentration - Contexte",
                "exposition_montant": patrimoine_data.get("patrimoine", {}).get("financier", {}).get("total", 0),
                "exposition_pct": 0
            },
            "evolution_fiscalite": {
                "titre": "Évolutions fiscales en cours",
                "description": "Des modifications fiscales récentes ou en projet peuvent affecter "
                              "l'épargne et les investissements. Voir sources pour détails.",
                "probabilite": "Moyenne",
                "impact": "Moyen",
                "niveau": "Moyen",
                "categorie": "Fiscal - Contexte",
                "exposition_montant": total_patrimoine,
                "exposition_pct": 100
            },
            "risques_geopolitiques": {
                "titre": "Risques géopolitiques actuels",
                "description": "Des tensions géopolitiques actuelles peuvent impacter les marchés "
                              "financiers et la valorisation du patrimoine.",
                "probabilite": "Moyenne",
                "impact": "Moyen",
                "niveau": "Faible",
                "categorie": "Marché - Contexte",
                "exposition_montant": total_patrimoine,
                "exposition_pct": 0
            },
            "volatilite_marches": {
                "titre": "Volatilité accrue des marchés",
                "description": "Des signaux de volatilité accrue ou de risque de correction "
                              "ont été identifiés sur les marchés financiers.",
                "probabilite": "Moyenne",
                "impact": "Moyen",
                "niveau": "Moyen",
                "categorie": "Marché - Contexte",
                "exposition_montant": self._calculate_equity_exposure(patrimoine_data),
                "exposition_pct": 0
            },
            "regulation_crypto": {
                "titre": "Évolution réglementation crypto",
                "description": "Des évolutions réglementaires concernant les cryptomonnaies "
                              "peuvent impacter les détenteurs d'actifs numériques.",
                "probabilite": "Moyenne",
                "impact": "Moyen",
                "niveau": "Faible",
                "categorie": "Réglementaire - Crypto",
                "exposition_montant": patrimoine_data.get("patrimoine", {}).get("crypto", {}).get("total", 0),
                "exposition_pct": 0
            }
        }

        risk_data = mappings.get(search_id)
        if not risk_data:
            return None

        # Filtrer les risques non pertinents (exposition = 0)
        if risk_data.get("exposition_montant", 0) == 0 and search_id in ["regulation_crypto"]:
            return None  # Pas de crypto, pas de risque crypto

        return risk_data

    def _calculate_equity_exposure(self, data: dict) -> float:
        """
        Calcule l'exposition totale aux actions du patrimoine

        Args:
            data: Données du patrimoine

        Returns:
            Montant total investi en actions (€)
        """
        exposition_actions = 0

        for etab in data.get("patrimoine", {}).get("financier", {}).get("etablissements", []):
            for compte in etab.get("comptes", []):
                if compte.get("type") in ["PEA", "PEA-PME", "CTO"]:
                    exposition_actions += compte.get("montant", 0)
                elif compte.get("type") == "Assurance-vie":
                    # UC sauf fonds euro
                    for fond in compte.get("fonds", []):
                        if "euro" not in fond.get("nom", "").lower():
                            exposition_actions += fond.get("montant", 0)

        return exposition_actions

    def _get_risk_id(self) -> str:
        """Génère un ID unique pour risque"""
        risk_id = f"RISK_{self.risk_id_counter:04d}"
        self.risk_id_counter += 1
        return risk_id
