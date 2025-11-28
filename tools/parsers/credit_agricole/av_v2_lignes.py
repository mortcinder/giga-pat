"""
Parser pour Assurance-vie Crédit Agricole format 2 lignes par fonds
Extrait du code existant de normalizer.py (lignes 738-798)
"""

import re
import pdfplumber
from datetime import datetime
from typing import Dict, Any, List
from ..base_parser import BaseParser, ParsingError


class CreditAgricoleAV2LignesParser(BaseParser):
    """Parser pour Assurance-vie CA format 2 lignes par fonds"""

    @property
    def strategy_name(self) -> str:
        return "credit_agricole.av.v2_lignes"

    @property
    def supported_formats(self) -> List[str]:
        return ["pdf"]

    def can_parse(self, filepath: str, metadata: dict) -> float:
        """Détecte format AV CA avec tables 2 lignes"""
        try:
            # Vérifier établissement
            if metadata.get("etablissement", "").lower() not in ["credit_agricole", "ca"]:
                return 0.0

            # Vérifier type de compte
            type_compte = metadata.get("type_compte", "").upper()
            if "ASSURANCE" not in type_compte and "AV" not in type_compte:
                return 0.0

            # Analyser le PDF
            with pdfplumber.open(filepath) as pdf:
                if not pdf.pages:
                    return 0.0

                text = pdf.pages[0].extract_text()
                if not text:
                    return 0.0

                text_lower = text.lower()

                # Heuristiques de détection AV
                has_assurance_vie = "assurance-vie" in text_lower or "assurance vie" in text_lower
                has_unites_compte = "unités de compte" in text_lower or "unites de compte" in text_lower
                has_fonds_euro = "fonds euro" in text_lower or "actif euro" in text_lower
                has_repartition = "répartition" in text_lower

                # Vérifier présence de tables avec "Valorisation"
                has_valorisation = False
                tables = pdf.pages[0].extract_tables()
                for table in tables:
                    if table and len(table) >= 2:
                        for row in table:
                            if any("Valorisation" in str(cell) for cell in row if cell):
                                has_valorisation = True
                                break

                # Score de confiance
                score = 0.0
                if has_assurance_vie:
                    score += 0.4
                if has_unites_compte or has_fonds_euro:
                    score += 0.2
                if has_repartition:
                    score += 0.1
                if has_valorisation:
                    score += 0.3

                return min(score, 1.0)

        except Exception:
            return 0.0

    def parse(self, filepath: str, metadata: dict) -> Dict[str, Any]:
        """Parse le PDF Assurance-vie format 2 lignes"""
        try:
            with pdfplumber.open(filepath) as pdf:
                # Extraire toutes les tables
                all_tables = []
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        if table:
                            all_tables.append(table)

                # Parser les fonds (positions dans l'AV)
                positions = self._parse_av_tables(all_tables)

                # Calculer montant total
                montant_total = sum(f["montant"] for f in positions)

                return {
                    "type": "Assurance-vie",
                    "montant": montant_total,
                    "positions": positions,  # Utiliser "positions" pour homogénéité
                    "metadata_parsing": {
                        "parser_used": self.strategy_name,
                        "parsed_at": datetime.now().isoformat(),
                        "nb_positions": len(positions),
                        "warnings": []
                    }
                }

        except Exception as e:
            raise ParsingError(f"Erreur parsing AV CA v2_lignes: {e}")

    def validate(self, parsed_data: dict) -> List[str]:
        """Valide les données parsées"""
        anomalies = []

        # Vérifier cohérence montant
        total_calc = sum(f["montant"] for f in parsed_data.get("positions", []))
        montant_declare = parsed_data.get("montant", 0)

        if abs(total_calc - montant_declare) > 1.0:  # Tolérance 1€
            anomalies.append(
                f"Écart valorisation : {abs(total_calc - montant_declare):.2f}€ "
                f"(calculé: {total_calc:.2f}€ vs déclaré: {montant_declare:.2f}€)"
            )

        # Vérifier au moins une position
        if not parsed_data.get("positions"):
            anomalies.append("Aucune position détectée dans le PDF")

        # Vérifier valeurs positives
        if montant_declare < 0:
            anomalies.append(f"Montant total négatif : {montant_declare:.2f}€")

        for position in parsed_data.get("positions", []):
            if position.get("montant", 0) < 0:
                anomalies.append(f"Valeur négative pour position : {position.get('nom')}")

        return anomalies

    def _parse_av_tables(self, tables: list) -> List[Dict[str, Any]]:
        """
        Parse les tables d'une assurance-vie
        Format attendu : chaque fonds est une table de 2 lignes
        - Ligne 0 : [Nom du fonds, "Valorisation : XXX €"]
        - Ligne 1 : [Répartition, Plus-values]
        """
        fonds_list = []

        for table in tables:
            # Format moderne : table de 2 lignes par fonds
            if table and len(table) == 2 and len(table[0]) >= 2:
                # Ligne 0 contient nom + valorisation
                nom_fonds = str(table[0][0]).strip() if table[0][0] else ""
                valeur_str = str(table[0][1]).strip() if len(table[0]) > 1 and table[0][1] else ""

                # Ignorer les tables vides ou sans nom de fonds
                if not nom_fonds or not valeur_str:
                    continue

                # Extraire la valorisation (format: "Valorisation : 58 100,39 €")
                valeur_match = re.search(r"Valorisation\s*:\s*([\d\s,]+)\s*€", valeur_str, re.IGNORECASE)
                if valeur_match:
                    valeur = self._parse_amount(valeur_match.group(1))
                    if valeur > 0:
                        fonds_list.append({
                            "nom": nom_fonds,
                            "montant": valeur
                        })

            # Format classique : table avec headers et plusieurs lignes
            elif table and len(table) > 2:
                # Chercher colonnes Support/Fonds et Valeur
                headers = [str(h).lower() if h else "" for h in table[0]]

                for row in table[1:]:
                    if not row or len(row) < 2:
                        continue

                    # Extraction nom du fonds et valeur
                    nom_fonds = str(row[0]).strip() if row[0] else ""
                    valeur_str = ""

                    for cell in row[1:]:
                        if cell and re.search(r"\d", str(cell)):
                            valeur_str = str(cell)
                            break

                    if nom_fonds and valeur_str:
                        valeur = self._parse_amount(valeur_str)
                        if valeur > 0:
                            fonds_list.append({
                                "nom": nom_fonds,
                                "montant": valeur
                            })

        return fonds_list
