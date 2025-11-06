"""
Module de parsing de fichiers sources
"""

import pandas as pd
import pdfplumber
import json
import logging
from typing import Dict, Any


class FileParser:
    """Parser générique pour CSV, PDF, JSON"""

    # Mapping des colonnes CSV selon section 12.1 du PRD
    COLUMN_MAPPINGS = {
        'ticker': ['ticker', 'symbole', 'code', 'isin', 'ticker/isin'],
        'quantite': ['quantite', 'quantity', 'qté', 'nombre', 'quantité'],
        'prix': ['prix', 'price', 'cours', 'valeur_unitaire', 'prix_unitaire', 'prix unitaire'],
        'valeur': ['valeur', 'value', 'montant', 'total', 'valeur_totale', 'valeur totale', 'montant en eur']
    }

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def _convert_french_number(self, value):
        """Convertit un nombre au format français (virgule) en float"""
        if pd.isna(value) or value is None:
            return None

        # Convertir en string si ce n'est pas déjà le cas
        if not isinstance(value, str):
            return value

        # Nettoyer: enlever espaces et guillemets
        value = value.strip().strip('"').strip("'")

        # Remplacer virgule par point pour le format décimal
        value = value.replace(',', '.')

        # Enlever les espaces (utilisés comme séparateurs de milliers)
        value = value.replace(' ', '')

        try:
            return float(value)
        except (ValueError, AttributeError):
            return None

    def parse_csv(self, filepath: str) -> pd.DataFrame:
        """
        Parse un fichier CSV avec normalisation des colonnes
        Suit les spécifications de la section 12 du PRD
        """
        try:
            df = pd.read_csv(
                filepath,
                encoding='utf-8-sig',
                sep=None,
                engine='python'
            )

            # Nettoyage colonnes
            df.columns = df.columns.str.strip().str.lower()

            # Mapping vers noms standards (section 12.2)
            for target_col, aliases in self.COLUMN_MAPPINGS.items():
                for alias in aliases:
                    if alias in df.columns:
                        df.rename(columns={alias: target_col}, inplace=True)
                        break

            # Conversion types numériques (section 12.2)
            # Utiliser la conversion française pour gérer les virgules comme séparateurs décimaux
            if 'quantite' in df.columns:
                df['quantite'] = df['quantite'].apply(self._convert_french_number)
            if 'prix' in df.columns:
                df['prix'] = df['prix'].apply(self._convert_french_number)
            if 'valeur' in df.columns:
                df['valeur'] = df['valeur'].apply(self._convert_french_number)

            self.logger.info(f"CSV parsé : {filepath} ({len(df)} lignes)")
            return df

        except Exception as e:
            self.logger.error(f"Erreur parsing CSV {filepath}: {e}")
            raise
            
    def parse_pdf(self, filepath: str) -> Dict[str, Any]:
        """
        Parse un fichier PDF avec détection de type de document
        Suit les spécifications de la section 13 du PRD
        """
        try:
            result = {
                "metadata": {},
                "tables": [],
                "text": "",
                "detected_type": None
            }

            with pdfplumber.open(filepath) as pdf:
                result["metadata"]["pages"] = len(pdf.pages)

                for i, page in enumerate(pdf.pages):
                    tables = page.extract_tables()
                    for table in tables:
                        if table:
                            result["tables"].append({
                                "page": i + 1,
                                "data": table
                            })

                    result["text"] += page.extract_text() or ""

            # Heuristiques pour identifier type de document (section 13.2)
            text_lower = result["text"].lower()
            text_original = result["text"]

            # Détecter PEA et PEA-PME en premier (plus spécifique que PER)
            if "pea pme" in text_lower or "pea-pme" in text_lower or "PEA PME" in text_original:
                result["detected_type"] = "PEA-PME"
            elif ("mandat pea" in text_lower or "compte pea" in text_lower) and "portefeuille" in text_lower:
                result["detected_type"] = "PEA"
            elif any(keyword in text_lower for keyword in ["assurance-vie", "assurance vie", "unités de compte", "fonds euro", "actif euro", "répartition des supports"]):
                result["detected_type"] = "Assurance-vie"
            elif any(keyword in text_lower for keyword in ["plan épargne retraite", "plan d'épargne retraite"]):
                result["detected_type"] = "PER"
            elif any(keyword in text_lower for keyword in ["compte-titres", "compte titres"]):
                result["detected_type"] = "CTO"

            self.logger.info(f"PDF parsé : {filepath} ({result['metadata']['pages']} pages, type: {result['detected_type']})")
            return result

        except Exception as e:
            self.logger.error(f"Erreur parsing PDF {filepath}: {e}")
            raise
            
    def parse_json(self, filepath: str) -> Dict[str, Any]:
        """Parse un fichier JSON"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.logger.info(f"JSON parsé : {filepath}")
            return data
            
        except Exception as e:
            self.logger.error(f"Erreur parsing JSON {filepath}: {e}")
            raise
