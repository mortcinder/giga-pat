"""
Parser pour CrypCool CSV transaction history (2026)
Format transactionnel avec colonnes : Timestamp, Operation type, Base amount, Base currency, etc.
Agrège les transactions pour calculer les holdings actuels avec déduction des frais
"""

import csv
from decimal import Decimal
from datetime import datetime
from typing import Dict, Any, List
from ..base_parser import BaseParser, ParsingError


class CrypCoolTransactionAggregator2026Parser(BaseParser):
    """Parser pour CrypCool transaction history CSV (format 2026 transactionnel)"""

    @property
    def strategy_name(self) -> str:
        return "crypcool.csv.v2026"

    @property
    def supported_formats(self) -> List[str]:
        return ["csv"]

    def can_parse(self, filepath: str, metadata: dict) -> float:
        """Détecte format CrypCool CSV transactionnel (2026)"""
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

                # Vérifier colonnes requises pour format transactionnel 2026
                required_headers = [
                    'Timestamp',
                    'Operation type',
                    'Base amount',
                    'Base currency',
                    'Quote amount',
                    'Quote currency'
                ]
                has_required = all(h in headers for h in required_headers)

                # Vérifier colonnes optionnelles pour frais
                has_fees = 'Fee amount' in headers and 'Fee currency' in headers

                if has_required:
                    # Priorité plus élevée si on a les colonnes de frais
                    return 1.0 if has_fees else 0.9
                else:
                    return 0.0

        except Exception:
            return 0.0

    def parse(self, filepath: str, metadata: dict) -> Dict[str, Any]:
        """Parse le CSV transactionnel et agrège les transactions par crypto"""
        try:
            # Lire toutes les transactions
            transactions = []
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    transactions.append(row)

            # Agréger les transactions par crypto
            holdings = self._aggregate_transactions(transactions)

            # Calculer montant total EUR équivalent (depuis manifest ou 0)
            montant_total = metadata.get("montant", 0.0)

            # Créer les positions pour les cryptos avec balance positive
            positions = []
            for crypto, amount in holdings.items():
                if amount > 0:
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
                    "total_positions": len(positions),
                    "cryptos_detected": list(holdings.keys())
                }
            }

        except Exception as e:
            raise ParsingError(f"Erreur parsing CrypCool CSV v2026 {filepath}: {str(e)}")

    def _aggregate_transactions(self, transactions: List[Dict]) -> Dict[str, Decimal]:
        """
        Agrège les transactions pour calculer les holdings par crypto.

        Logique :
        - trade EUR → Crypto : +Base amount (crypto reçue)
        - trade Crypto → Crypto : +Base amount, -Quote amount (ex: VRO reçu, BTC dépensé)
        - deposit Crypto : +Base amount
        - deposit EUR : ignoré (c'est du fiat)
        - Frais : déduits de la crypto concernée
        """
        holdings: Dict[str, Decimal] = {}

        for tx in transactions:
            op_type = tx.get('Operation type', '').strip().lower()
            base_amount_str = tx.get('Base amount', '').strip()
            base_currency = tx.get('Base currency', '').strip().upper()
            quote_amount_str = tx.get('Quote amount', '').strip()
            quote_currency = tx.get('Quote currency', '').strip().upper()
            fee_amount_str = tx.get('Fee amount', '').strip()
            fee_currency = tx.get('Fee currency', '').strip().upper()

            # Ignorer les dépôts EUR (pas de crypto)
            if base_currency in ['EUR', 'EURO', 'USD']:
                continue

            # Initialiser le holding si nécessaire
            if base_currency and base_currency not in holdings:
                holdings[base_currency] = Decimal('0')

            # Traiter selon le type d'opération
            if op_type == 'trade':
                # Ajouter la crypto reçue
                if base_amount_str:
                    base_amount = self._parse_decimal(base_amount_str)
                    holdings[base_currency] += base_amount

                # Soustraire la crypto dépensée (si trade crypto-to-crypto)
                if quote_currency and quote_currency not in ['EUR', 'EURO', 'USD']:
                    if quote_currency not in holdings:
                        holdings[quote_currency] = Decimal('0')
                    if quote_amount_str:
                        quote_amount = self._parse_decimal(quote_amount_str)
                        holdings[quote_currency] -= quote_amount

            elif op_type == 'deposit':
                # Dépôt de crypto (pas EUR)
                if base_amount_str:
                    base_amount = self._parse_decimal(base_amount_str)
                    holdings[base_currency] += base_amount

            # Déduire les frais
            if fee_amount_str and fee_currency:
                fee_amount = self._parse_decimal(fee_amount_str)
                if fee_currency not in ['EUR', 'EURO', 'USD']:
                    # Frais en crypto
                    if fee_currency not in holdings:
                        holdings[fee_currency] = Decimal('0')
                    holdings[fee_currency] -= fee_amount
                # Note: frais en EUR sont ignorés (pas d'impact sur holdings crypto)

        return holdings

    def _parse_decimal(self, value_str: str) -> Decimal:
        """Parse un montant décimal"""
        if not value_str or value_str.strip() == '':
            return Decimal('0')

        # Nettoyer la chaîne
        value_str = value_str.strip().replace(' ', '')

        # Le format utilise des points (format anglais)
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
