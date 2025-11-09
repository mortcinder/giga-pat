"""
Registry central de tous les parsers disponibles
Gère l'enregistrement, la sélection et l'auto-détection des parsers
"""

import logging
from typing import Dict, List, Tuple, Type, Optional
from .base_parser import BaseParser, ParsingError


class ParserRegistry:
    """Registry central de tous les parsers disponibles"""

    def __init__(self):
        self._parsers: Dict[str, BaseParser] = {}
        self.logger = logging.getLogger(__name__)

    def register(self, parser_class: Type[BaseParser]):
        """
        Enregistre un parser dans le registry

        Args:
            parser_class: Classe du parser (non instanciée)

        Example:
            registry = ParserRegistry()
            registry.register(CreditAgricolePEA2025Parser)
        """
        try:
            parser = parser_class()
            strategy_name = parser.strategy_name

            if strategy_name in self._parsers:
                self.logger.warning(f"Parser '{strategy_name}' déjà enregistré, écrasement")

            self._parsers[strategy_name] = parser
            self.logger.debug(f"Parser enregistré : {strategy_name} (formats: {parser.supported_formats})")

        except Exception as e:
            self.logger.error(f"Erreur lors de l'enregistrement du parser {parser_class.__name__}: {e}")
            raise

    def get_parser(self, strategy_name: str) -> BaseParser:
        """
        Récupère un parser par son nom de stratégie

        Args:
            strategy_name: Nom de la stratégie (ex: 'credit_agricole.pea.v2025')

        Returns:
            Instance du parser

        Raises:
            ValueError: Si le parser n'existe pas
        """
        if strategy_name not in self._parsers:
            available = list(self._parsers.keys())
            raise ValueError(f"Parser inconnu : '{strategy_name}'. Parsers disponibles : {available}")

        return self._parsers[strategy_name]

    def auto_detect(self, filepath: str, metadata: dict) -> List[Tuple[str, float]]:
        """
        Auto-détecte les parsers compatibles avec un fichier.
        Retourne liste de (strategy_name, confidence_score) triée par score décroissant.

        Args:
            filepath: Chemin du fichier à analyser
            metadata: Métadonnées du compte (etablissement, type_compte, etc.)

        Returns:
            Liste de tuples (strategy_name, score) triée par score DESC
            Exemple: [('credit_agricole.pea.v2025', 0.95), ('generic.pea.pdf', 0.60)]

        Example:
            candidates = registry.auto_detect('/path/to/PEA.pdf', {'etablissement': 'credit_agricole'})
            if candidates:
                best_parser = registry.get_parser(candidates[0][0])
        """
        candidates = []

        for strategy_name, parser in self._parsers.items():
            try:
                score = parser.can_parse(filepath, metadata)

                if score > 0.0:  # Seulement les parsers avec score > 0
                    candidates.append((strategy_name, score))
                    self.logger.debug(f"  {strategy_name}: {score:.2f}")

            except Exception as e:
                self.logger.warning(f"Erreur lors de can_parse() pour {strategy_name}: {e}")

        # Trier par score décroissant
        candidates.sort(key=lambda x: x[1], reverse=True)

        return candidates

    def parse_with_fallback(self, filepath: str, metadata: dict, strategies: List[str]) -> dict:
        """
        Essaye de parser un fichier avec une liste de stratégies (ordre de priorité).
        Retourne dès qu'un parser réussit.

        Args:
            filepath: Chemin du fichier
            metadata: Métadonnées du compte
            strategies: Liste des stratégies à essayer (ordre prioritaire)

        Returns:
            Données parsées par le premier parser qui réussit

        Raises:
            ParsingError: Si tous les parsers échouent

        Example:
            data = registry.parse_with_fallback(
                '/path/to/PEA.pdf',
                {'etablissement': 'credit_agricole'},
                ['credit_agricole.pea.v2025', 'credit_agricole.pea.v2023', 'generic.pea.pdf']
            )
        """
        errors = []

        for strategy_name in strategies:
            try:
                parser = self.get_parser(strategy_name)
                self.logger.info(f"Tentative parsing avec {strategy_name}...")

                # Parse
                parsed_data = parser.parse(filepath, metadata)

                # Validate
                anomalies = parser.validate(parsed_data)
                if anomalies:
                    self.logger.warning(f"Anomalies détectées avec {strategy_name}: {anomalies}")

                # Succès
                self.logger.info(f"✓ Parsing réussi avec {strategy_name}")

                # Ajouter métadonnées de parsing
                if "metadata_parsing" not in parsed_data:
                    parsed_data["metadata_parsing"] = {}

                parsed_data["metadata_parsing"]["parser_used"] = strategy_name
                parsed_data["metadata_parsing"]["warnings"] = anomalies

                return parsed_data

            except Exception as e:
                error_msg = f"{strategy_name}: {str(e)}"
                errors.append(error_msg)
                self.logger.debug(f"Échec parsing avec {strategy_name}: {e}")

        # Tous les parsers ont échoué
        raise ParsingError(
            f"Tous les parsers ont échoué pour {filepath}. "
            f"Stratégies essayées: {strategies}. Erreurs: {errors}"
        )

    def list_parsers(self) -> List[str]:
        """Retourne la liste de tous les parsers enregistrés"""
        return list(self._parsers.keys())

    def get_parsers_by_format(self, file_format: str) -> List[str]:
        """
        Retourne les parsers supportant un format donné

        Args:
            file_format: Extension du fichier ('pdf', 'csv', 'json', etc.)

        Returns:
            Liste des strategy_name supportant ce format
        """
        compatible = []

        for strategy_name, parser in self._parsers.items():
            if file_format.lower() in [fmt.lower() for fmt in parser.supported_formats]:
                compatible.append(strategy_name)

        return compatible

    def __repr__(self):
        return f"<ParserRegistry parsers={len(self._parsers)}>"
