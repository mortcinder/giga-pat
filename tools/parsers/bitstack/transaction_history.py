"""
Parser pour les fichiers de transaction Bitstack (CSV).

Ce parser supporte:
- Format CSV d'historique de transactions Bitstack
- Calcul automatique du solde BTC (achats - retraits)
- Support multi-années avec système de cache

Structure CSV:
Type,Date,Fuseau horaire,Montant reçu,Monnaie ou jeton reçu,Montant envoyé,
Monnaie ou jeton envoyé,Frais,Monnaie ou jeton des frais,Description,...

Types de transactions:
- Échange: Achat de BTC avec EUR
- Retrait: Envoi de BTC vers wallet externe
- Dépôt: Réception de BTC (cadeau, transfert)

Version: v2025
Auteur: Claude Code
PRD: Section 2.1.2 (Parsers pluggables)
"""

import csv
import re
from decimal import Decimal, InvalidOperation
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from tools.parsers.base_parser import BaseParser
import logging


class BitstackTransactionHistoryParser(BaseParser):
    """Parser pour fichiers CSV d'historique Bitstack."""

    strategy_name = "bitstack.transaction_history.v2025"

    def __init__(self):
        super().__init__()
        self.btc_balance = Decimal('0')
        self.transactions = []
        self.logger = logging.getLogger(__name__)

    @property
    def supported_formats(self) -> List[str]:
        """Formats supportés par ce parser."""
        return ['csv']

    def can_parse(self, file_path: str, metadata: Dict[str, Any]) -> bool:
        """
        Vérifie si le fichier peut être parsé par ce parser.

        Critères:
        - Fichier CSV
        - Pattern [BIT] - *.csv
        - Contient les colonnes attendues
        """
        path = Path(file_path)

        # Vérification du pattern de nom
        if not path.name.startswith('[BIT]') or path.suffix.lower() != '.csv':
            return False

        # Vérification des colonnes
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames or []
                required = ['Type', 'Date', 'Montant reçu', 'Monnaie ou jeton reçu']
                return all(col in headers for col in required)
        except Exception as e:
            self.logger.warning(f"Impossible de vérifier les colonnes: {e}")
            return False

    def parse(self, file_path: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse le fichier CSV et calcule le solde BTC.

        Args:
            file_path: Chemin vers le fichier CSV
            metadata: Métadonnées du compte (custodian, type, etc.)

        Returns:
            Liste avec une seule entrée contenant le solde BTC cumulé
        """
        self.btc_balance = Decimal('0')
        self.transactions = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    self._process_transaction(row)

            # Extraire l'année du nom de fichier
            year_match = re.search(r'(\d{4})', Path(file_path).name)
            year = year_match.group(1) if year_match else "unknown"

            # Retourner un résumé du solde pour cette période
            position = {
                'nom': f"Bitcoin {year}",
                'type': 'BTC',
                'quantite': float(self.btc_balance),
                'valeur_unitaire': 0,  # Sera enrichi par le normalizer avec prix actuel
                'valeur_totale': 0,    # Sera calculé par le normalizer
                'devise': 'BTC',
                'metadata': {
                    'year': year,
                    'transaction_count': len(self.transactions),
                    'btc_balance': str(self.btc_balance)
                }
            }

            # Retourner au format attendu par le normalizer
            return {
                'type_compte': 'Crypto',
                'positions': [position]
            }

        except Exception as e:
            self.logger.error(f"Erreur lors du parsing de {file_path}: {e}")
            raise

    def _process_transaction(self, row: Dict[str, str]) -> None:
        """
        Traite une transaction et met à jour le solde BTC.

        Types:
        - Échange: Achat de BTC (montant reçu en BTC)
        - Retrait: Envoi de BTC (montant envoyé en BTC)
        - Dépôt: Réception de BTC (montant reçu en BTC)
        """
        tx_type = row.get('Type', '').strip()

        if tx_type == 'Échange' or tx_type == 'Dépôt':
            # Achat ou dépôt: ajout au solde
            btc_received = self._parse_decimal(row.get('Montant reçu', '0'))
            currency = row.get('Monnaie ou jeton reçu', '').strip()

            if currency == 'BTC' and btc_received > 0:
                self.btc_balance += btc_received
                self.transactions.append({
                    'type': tx_type,
                    'date': row.get('Date', ''),
                    'btc': float(btc_received),
                    'direction': 'in'
                })

        elif tx_type == 'Retrait':
            # Retrait: déduction du solde
            btc_sent = self._parse_decimal(row.get('Montant envoyé', '0'))
            currency = row.get('Monnaie ou jeton envoyé', '').strip()

            if currency == 'BTC' and btc_sent > 0:
                self.btc_balance -= btc_sent
                self.transactions.append({
                    'type': tx_type,
                    'date': row.get('Date', ''),
                    'btc': float(btc_sent),
                    'direction': 'out'
                })

    def _parse_decimal(self, value: str) -> Decimal:
        """Parse une valeur décimale depuis une string."""
        try:
            cleaned = value.strip().replace(',', '.').replace(' ', '')
            return Decimal(cleaned) if cleaned else Decimal('0')
        except (InvalidOperation, ValueError):
            return Decimal('0')

    def validate(self, parsed_data: Dict[str, Any]) -> bool:
        """
        Valide les données parsées.

        Critères:
        - Structure correcte (dict avec 'positions')
        - Au moins une position
        - Solde BTC >= 0 (cohérence des transactions)
        """
        if not parsed_data:
            self.logger.error("Aucune donnée parsée")
            return False

        # Check for dict structure
        if not isinstance(parsed_data, dict):
            self.logger.error(f"Format incorrect: attendu dict, obtenu {type(parsed_data)}")
            return False

        positions = parsed_data.get('positions', [])
        if not positions:
            self.logger.error("Aucune position trouvée")
            return False

        if len(positions) != 1:
            self.logger.error(f"Attendu 1 position résumée, obtenu {len(positions)}")
            return False

        btc_qty = positions[0].get('quantite', 0)
        if btc_qty < 0:
            self.logger.error(f"Solde BTC négatif: {btc_qty}")
            return False

        return True
