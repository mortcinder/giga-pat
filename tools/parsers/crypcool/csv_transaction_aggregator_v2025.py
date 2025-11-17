"""
Parser pour CrypCool CSV transaction history (2025)
Agrège les transactions pour calculer les holdings actuels
"""

import csv
import re
from decimal import Decimal
from datetime import datetime
from typing import Dict, Any, List
from ..base_parser import BaseParser, ParsingError


class CrypCoolTransactionAggregator2025Parser(BaseParser):
    """Parser pour CrypCool transaction history CSV (2025+)"""

    @property
    def strategy_name(self) -> str:
        return "crypcool.csv.v2025"

    @property
    def supported_formats(self) -> List[str]:
        return ["csv"]

    def can_parse(self, filepath: str, metadata: dict) -> float:
        """Détecte format CrypCool CSV"""
        try:
            # Vérifier custodian
            custodian = metadata.get("custodian", "").lower()
            if custodian not in ["crypcool", "cryp"]:
                return 0.0

            # Vérifier que c'est un CSV
            if not filepath.lower().endswith('.csv'):
                return 0.0

            # Analyser le CSV
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames

                if not headers:
                    return 0.0

                # Vérifier colonnes requises
                required_headers = ['DATE', 'REFERENCE', 'TYPE', 'EURO', 'ETAT']
                has_required = all(h in headers for h in required_headers)

                # Vérifier au moins une colonne crypto (BTC, ETH, etc.)
                has_crypto = any(h in headers for h in ['BTC', 'ETH', 'VRO', 'XRP', 'LTC'])

                if has_required and has_crypto:
                    return 1.0
                else:
                    return 0.0

        except Exception:
            return 0.0

    def parse(self, filepath: str, metadata: dict) -> Dict[str, Any]:
        """Parse le CSV et agrège les transactions"""
        try:
            # Lire le CSV
            transactions = []
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                headers = list(reader.fieldnames)

                # Identifier les colonnes crypto dynamiquement
                crypto_columns = [h for h in headers if h not in ['DATE', 'REFERENCE', 'TYPE', 'EURO', 'ETAT']]

                for row in reader:
                    # Ne traiter que les transactions valides
                    if row.get('ETAT', '').upper() == 'VALIDE':
                        transactions.append(row)

            # Agréger les transactions par crypto
            holdings = self._aggregate_transactions(transactions, crypto_columns)

            # Calculer montant total EUR équivalent
            montant_total = metadata.get("montant", 0.0)  # Depuis manifest

            # Créer les positions
            positions = []
            for crypto, amount in holdings.items():
                if amount > 0:  # Ne garder que les holdings positifs
                    positions.append({
                        "nom": f"{crypto.upper()}",
                        "ticker": crypto.upper(),
                        "quantite": float(amount),
                        "devise": crypto.upper(),
                        "type": "Crypto",
                        "metadata": {
                            "custodian": metadata.get("custodian", "crypcool")
                        }
                    })

            return {
                "type_compte": "Crypto",
                "montant": montant_total,
                "positions": positions,
                "metadata_parsing": {
                    "parser_used": self.strategy_name,
                    "parsed_at": datetime.now().isoformat(),
                    "warnings": [],
                    "total_transactions": len(transactions),
                    "total_positions": len(positions)
                }
            }

        except Exception as e:
            raise ParsingError(f"Erreur parsing CrypCool CSV {filepath}: {str(e)}")

    def _aggregate_transactions(self, transactions: List[Dict], crypto_columns: List[str]) -> Dict[str, Decimal]:
        """Agrège les transactions pour calculer les holdings"""
        holdings = {}

        # Initialiser les holdings à zéro pour chaque crypto
        for crypto in crypto_columns:
            holdings[crypto] = Decimal('0')

        # Traiter toutes les transactions dans l'ordre chronologique
        for tx in transactions:
            tx_type = tx.get('TYPE', '').upper()

            # Traiter chaque colonne crypto
            for crypto in crypto_columns:
                amount_str = tx.get(crypto, '').strip()
                if amount_str:
                    # Parser le montant (format français : virgule pour décimale)
                    amount = self._parse_decimal(amount_str)

                    # Ajouter au holding (positif ou négatif selon la transaction)
                    holdings[crypto] += amount

        return holdings

    def _parse_decimal(self, value_str: str) -> Decimal:
        """Parse un montant en format français (virgule = décimale)"""
        if not value_str or value_str.strip() == '':
            return Decimal('0')

        # Nettoyer la chaîne
        value_str = value_str.strip().replace(' ', '')

        # Remplacer virgule par point pour Decimal
        value_str = value_str.replace(',', '.')

        try:
            return Decimal(value_str)
        except Exception:
            return Decimal('0')

    def validate(self, parsed_data: dict) -> List[str]:
        """Valide les données parsées"""
        anomalies = []

        # Vérifier structure de base
        if "montant" not in parsed_data:
            anomalies.append("Montant total manquant")
        if "positions" not in parsed_data:
            anomalies.append("Positions manquantes")

        # Vérifier qu'il y a au moins une position
        if "positions" in parsed_data and len(parsed_data["positions"]) == 0:
            anomalies.append("Aucune position trouvée après agrégation")

        # Vérifier que toutes les quantités sont positives
        for pos in parsed_data.get("positions", []):
            if pos.get("quantite", 0) < 0:
                anomalies.append(f"Holding négatif détecté: {pos.get('nom')} = {pos.get('quantite')}")

            if pos.get("quantite", 0) == 0:
                anomalies.append(f"Holding nul: {pos.get('nom')}")

        return anomalies
