"""
Parser CSV générique avec mapping flexible des colonnes
Adapté du code existant de file_parser.py
"""

import pandas as pd
from datetime import datetime
from typing import Dict, Any, List
from ..base_parser import BaseParser, ParsingError


class GenericCSVParser(BaseParser):
    """Parser CSV générique pour comptes titres (CTO, PEA, etc.)"""

    # Mapping des colonnes CSV (section 12.1 du PRD)
    COLUMN_MAPPINGS = {
        'ticker': ['ticker', 'symbole', 'code', 'isin', 'ticker/isin'],
        'quantite': ['quantite', 'quantity', 'qté', 'nombre', 'quantité'],
        'prix': ['prix', 'price', 'cours', 'valeur_unitaire', 'prix_unitaire', 'prix unitaire', 'clôture'],
        'valeur': ['valeur', 'value', 'montant', 'total', 'valeur_totale', 'valeur totale', 'montant en eur'],
        'nom': ['nom', 'name', 'libelle', 'libellé', 'description', 'designation', 'désignation', 'produit']
    }

    @property
    def strategy_name(self) -> str:
        return "generic.csv.flexible"

    @property
    def supported_formats(self) -> List[str]:
        return ["csv"]

    def can_parse(self, filepath: str, metadata: dict) -> float:
        """Vérifie que c'est un CSV valide"""
        try:
            if not filepath.lower().endswith('.csv'):
                return 0.0

            # Essayer de lire le CSV
            df = pd.read_csv(filepath, encoding='utf-8-sig', sep=None, engine='python', nrows=5)

            if df.empty:
                return 0.0

            # Vérifier présence de colonnes attendues
            columns_lower = [col.lower().strip() for col in df.columns]

            # Au moins une colonne valeur ou montant
            has_valeur = any(alias in columns_lower for alias in self.COLUMN_MAPPINGS['valeur'])
            # Au moins une colonne ticker ou nom
            has_identifier = (
                any(alias in columns_lower for alias in self.COLUMN_MAPPINGS['ticker']) or
                any(alias in columns_lower for alias in self.COLUMN_MAPPINGS['nom'])
            )

            if has_valeur and has_identifier:
                return 0.7  # Confiance modérée (générique)

            return 0.3  # Confiance faible mais possible

        except Exception:
            return 0.0

    def parse(self, filepath: str, metadata: dict) -> Dict[str, Any]:
        """Parse le fichier CSV avec normalisation des colonnes"""
        try:
            # Lire CSV
            df = pd.read_csv(
                filepath,
                encoding='utf-8-sig',
                sep=None,
                engine='python'
            )

            # Nettoyage colonnes
            df.columns = df.columns.str.strip().str.lower()

            # Mapping vers noms standards
            for target_col, aliases in self.COLUMN_MAPPINGS.items():
                for alias in aliases:
                    if alias in df.columns:
                        df.rename(columns={alias: target_col}, inplace=True)
                        break

            # Conversion types numériques (format français)
            if 'quantite' in df.columns:
                df['quantite'] = df['quantite'].apply(self._convert_french_number)
            if 'prix' in df.columns:
                df['prix'] = df['prix'].apply(self._convert_french_number)
            if 'valeur' in df.columns:
                df['valeur'] = df['valeur'].apply(self._convert_french_number)

            # Construire positions
            positions = []
            for _, row in df.iterrows():
                position = {}

                if 'nom' in row and pd.notna(row['nom']):
                    position['nom'] = str(row['nom'])
                if 'ticker' in row and pd.notna(row['ticker']):
                    position['ticker'] = str(row['ticker'])
                if 'quantite' in row and pd.notna(row['quantite']):
                    position['quantite'] = float(row['quantite'])
                if 'prix' in row and pd.notna(row['prix']):
                    position['prix'] = float(row['prix'])
                if 'valeur' in row and pd.notna(row['valeur']):
                    position['valeur'] = float(row['valeur'])

                # Si valeur manquante mais on a quantité et prix, calculer
                if 'valeur' not in position and 'quantite' in position and 'prix' in position:
                    position['valeur'] = position['quantite'] * position['prix']

                if position:  # Au moins un champ
                    positions.append(position)

            # Calculer montant total
            montant_total = sum(p.get('valeur', 0) for p in positions)

            return {
                "type": metadata.get("type_compte", "CTO"),
                "montant": montant_total,
                "positions": positions,
                "metadata_parsing": {
                    "parser_used": self.strategy_name,
                    "parsed_at": datetime.now().isoformat(),
                    "nb_positions": len(positions),
                    "warnings": []
                }
            }

        except Exception as e:
            raise ParsingError(f"Erreur parsing CSV générique: {e}")

    def validate(self, parsed_data: dict) -> List[str]:
        """Valide les données parsées"""
        anomalies = []

        # Vérifier au moins une position
        if not parsed_data.get("positions"):
            anomalies.append("Aucune position détectée dans le CSV")

        # Vérifier cohérence montant
        total_calc = sum(p.get("valeur", 0) for p in parsed_data.get("positions", []))
        montant_declare = parsed_data.get("montant", 0)

        if abs(total_calc - montant_declare) > 0.01:  # Tolérance arrondi
            anomalies.append(
                f"Écart valorisation : {abs(total_calc - montant_declare):.2f}€"
            )

        # Vérifier valeurs positives
        for pos in parsed_data.get("positions", []):
            if pos.get("valeur", 0) < 0:
                nom = pos.get("nom", pos.get("ticker", "inconnu"))
                anomalies.append(f"Valeur négative pour position : {nom}")

        return anomalies

    def _convert_french_number(self, value):
        """Convertit un nombre au format français (virgule) en float"""
        if pd.isna(value) or value is None:
            return None

        if not isinstance(value, str):
            return value

        # Nettoyer
        value = value.strip().strip('"').strip("'")

        # Remplacer virgule par point
        value = value.replace(',', '.')

        # Enlever les espaces (séparateurs de milliers)
        value = value.replace(' ', '')

        try:
            return float(value)
        except (ValueError, AttributeError):
            return None
