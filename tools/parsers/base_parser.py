"""
Interface abstraite pour tous les parsers de documents financiers
Suit le pattern Strategy pour permettre l'ajout de nouveaux établissements sans modifier le code existant
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class ParsingError(Exception):
    """Exception levée en cas d'échec de parsing"""
    pass


class BaseParser(ABC):
    """Interface abstraite pour tous les parsers"""

    @property
    @abstractmethod
    def strategy_name(self) -> str:
        """
        Nom unique du parser (ex: 'credit_agricole.pea.v2025')
        Format recommandé: {etablissement}.{type_compte}.{version}
        """
        pass

    @property
    @abstractmethod
    def supported_formats(self) -> List[str]:
        """
        Formats de fichiers supportés
        Retourne: Liste de ['pdf', 'csv', 'json', 'xlsx', etc.]
        """
        pass

    @abstractmethod
    def can_parse(self, filepath: str, metadata: dict) -> float:
        """
        Score de confiance (0.0-1.0) que ce parser peut traiter le fichier.
        Permet auto-détection et mécanisme de fallback.

        Args:
            filepath: Chemin du fichier à analyser
            metadata: Métadonnées du compte (etablissement, type_compte, etc.)

        Returns:
            Score de 0.0 (impossible) à 1.0 (certitude absolue)

        Example:
            def can_parse(self, filepath, metadata):
                if metadata.get('etablissement') == 'credit_agricole':
                    if metadata.get('type_compte') == 'PEA':
                        # Vérifier format spécifique dans le PDF
                        with pdfplumber.open(filepath) as pdf:
                            text = pdf.pages[0].extract_text().lower()
                            if 'mandat pea' in text:
                                return 0.95
                return 0.0
        """
        pass

    @abstractmethod
    def parse(self, filepath: str, metadata: dict) -> Dict[str, Any]:
        """
        Parse le fichier et retourne structure normalisée.

        Args:
            filepath: Chemin du fichier à parser
            metadata: Métadonnées du compte (pour contexte)

        Returns:
            Dictionnaire avec structure normalisée:
            {
                "type": "PEA",
                "montant": 82186.48,
                "positions": [
                    {"nom": "AIR LIQUIDE", "ticker": "FR0000120073", "quantite": 10, "prix": 150.0, "valeur": 1500.0},
                    ...
                ],
                "solde_especes": 5163.08,  # Optionnel
                "fonds": [...],             # Pour AV
                "metadata_parsing": {       # Informations sur le parsing
                    "parser_used": "credit_agricole.pea.v2025",
                    "parsed_at": "2025-11-09T...",
                    "warnings": []
                }
            }

        Raises:
            ParsingError: Si le parsing échoue
        """
        pass

    @abstractmethod
    def validate(self, parsed_data: dict) -> List[str]:
        """
        Valide les données parsées et retourne liste d'anomalies.

        Args:
            parsed_data: Données retournées par parse()

        Returns:
            Liste d'anomalies détectées (vide si tout OK):
            [
                "Écart valorisation : 10.50€ (calculé: 82186.48€ vs attendu: 82196.98€)",
                "ISIN invalide pour position 'ABC COMPANY'",
                ...
            ]

        Example:
            def validate(self, parsed_data):
                anomalies = []

                # Vérifier cohérence montant total
                total_calc = sum(p['valeur'] for p in parsed_data.get('positions', []))
                total_calc += parsed_data.get('solde_especes', 0)

                if abs(total_calc - parsed_data['montant']) > 1.0:
                    anomalies.append(f"Écart valorisation : {abs(total_calc - parsed_data['montant']):.2f}€")

                # Vérifier ISINs valides
                for pos in parsed_data.get('positions', []):
                    if not self._is_valid_isin(pos.get('ticker')):
                        anomalies.append(f"ISIN invalide : {pos.get('nom')}")

                return anomalies
        """
        pass

    # Méthodes utilitaires communes (peuvent être overridden)

    def _is_valid_isin(self, isin: str) -> bool:
        """
        Valide un code ISIN (format: 2 lettres pays + 10 caractères alphanumériques)

        Example:
            FR0000120073 (Air Liquide) → True
            INVALID → False
        """
        if not isin or len(isin) != 12:
            return False

        # Format: 2 lettres + 9 alphanumériques + 1 chiffre de contrôle
        if not isin[:2].isalpha():
            return False
        if not isin[2:].isalnum():
            return False

        return True

    def _parse_amount(self, amount_str: str) -> float:
        """
        Convertit une chaîne de montant en float (gère format français)

        Examples:
            '12 345,67 €' → 12345.67
            '1.234,56' → 1234.56
            '1,234.56' → 1234.56 (format US)
        """
        if not amount_str:
            return 0.0

        amount_str = str(amount_str)

        # Enlever espaces, symboles monétaires et caractères spéciaux
        amount_str = amount_str.replace(" ", "").replace("\xa0", "")
        amount_str = amount_str.replace("€", "").replace("$", "").replace("USD", "")

        # Détecter format (français: 1.234,56 vs anglais: 1,234.56)
        # Si dernière virgule est suivie de 2 chiffres, c'est le séparateur décimal
        if "," in amount_str and "." in amount_str:
            # Les deux présents: déterminer lequel est le séparateur décimal
            last_comma_idx = amount_str.rfind(",")
            last_dot_idx = amount_str.rfind(".")

            if last_comma_idx > last_dot_idx:
                # Format français: 1.234,56
                amount_str = amount_str.replace(".", "").replace(",", ".")
            else:
                # Format anglais: 1,234.56
                amount_str = amount_str.replace(",", "")
        elif "," in amount_str:
            # Seulement virgule: probablement format français
            amount_str = amount_str.replace(",", ".")

        # Enlever tout ce qui n'est pas chiffre, point ou signe négatif
        amount_str = ''.join(c for c in amount_str if c.isdigit() or c in '.-')

        try:
            return float(amount_str) if amount_str else 0.0
        except ValueError:
            return 0.0

    def __repr__(self):
        return f"<{self.__class__.__name__} strategy='{self.strategy_name}'>"
