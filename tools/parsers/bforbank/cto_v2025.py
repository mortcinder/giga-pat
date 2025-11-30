"""
Parser pour CTO BforBank format PDF (2025)
Extrait positions, espèces et valorisation totale
"""

import re
import pdfplumber
from datetime import datetime
from typing import Dict, Any, List
from ..base_parser import BaseParser, ParsingError


class BforBankCTO2025Parser(BaseParser):
    """Parser pour CTO BforBank format PDF (2025+)"""

    @property
    def strategy_name(self) -> str:
        return "bforbank.cto.v2025"

    @property
    def supported_formats(self) -> List[str]:
        return ["pdf"]

    def can_parse(self, filepath: str, metadata: dict) -> float:
        """Détecte format BforBank CTO"""
        try:
            # Vérifier établissement
            custodian = metadata.get("custodian", "").lower()
            if custodian not in ["bforbank", "bfb"]:
                return 0.0

            # Vérifier type de compte
            type_compte = metadata.get("type_compte", "").upper()
            if type_compte != "CTO":
                return 0.0

            # Analyser le PDF
            with pdfplumber.open(filepath) as pdf:
                if not pdf.pages:
                    return 0.0

                text = pdf.pages[0].extract_text()
                if not text:
                    return 0.0

                text_lower = text.lower()

                # Heuristiques de détection BforBank CTO
                has_bforbank = "bforbank" in text_lower or "bfb" in text_lower
                has_designation = "désignation" in text_lower and "code de la valeur" in text_lower
                has_valorisation = "valorisation" in text_lower
                has_quantite = "quantité" in text_lower or "quantite" in text_lower

                # Score de confiance
                score = 0.0
                if has_bforbank:
                    score += 0.4
                if has_designation:
                    score += 0.3
                if has_valorisation:
                    score += 0.2
                if has_quantite:
                    score += 0.1

                return min(score, 1.0)

        except Exception:
            return 0.0

    def parse(self, filepath: str, metadata: dict) -> Dict[str, Any]:
        """Parse le PDF CTO BforBank"""
        try:
            with pdfplumber.open(filepath) as pdf:
                # Extraire toutes les tables de toutes les pages
                all_rows = []
                especes = 0.0
                total_valorisation = 0.0

                for page_num, page in enumerate(pdf.pages):
                    tables = page.extract_tables()
                    for table in tables:
                        if table:
                            # Trouver l'index de la ligne d'en-tête
                            header_row_idx = None
                            for i, row in enumerate(table):
                                if row and any("Désignation" in str(cell) or "Valorisation" in str(cell) for cell in row if cell):
                                    header_row_idx = i
                                    break

                            if header_row_idx is not None:
                                # Parser les lignes de données
                                for row in table[header_row_idx + 1:]:
                                    if not row:
                                        continue

                                    designation = row[0] if row[0] else ""

                                    # Vérifier si c'est la ligne ESPECES
                                    if "ESPECES" in str(designation).upper():
                                        # Extraire montant espèces (2ème colonne pour page 2)
                                        especes_str = row[1] if len(row) > 1 and row[1] else "0"
                                        especes = self._parse_amount(especes_str)
                                        continue

                                    # Vérifier si c'est une ligne de total, section, ou titre
                                    if any(keyword in str(designation).upper() for keyword in ["TOTAL", "TITRES", "ACTIONS", "OBLIGATIONS", "ETF"]):
                                        # Ignorer les lignes de section/total sauf si elles contiennent un ISIN
                                        if "\n" in designation and any(char.isdigit() for char in designation):
                                            # C'est peut-être une position valide avec ISIN
                                            all_rows.append(row)
                                        continue

                                    # Si la ligne contient un ISIN (format: texte avec retour chariot et code ISIN)
                                    if designation and "\n" in designation:
                                        # Format attendu: "NOM\nISIN"
                                        parts = designation.split("\n")
                                        if len(parts) >= 2 and len(parts[1]) == 12:  # ISIN = 12 caractères
                                            all_rows.append(row)

                # Parser les positions
                positions = self._parse_positions(all_rows)

                # Calculer montant total
                total_positions = sum(p["valeur"] for p in positions)
                montant_total = total_positions + especes

                return {
                    "type": "CTO",
                    "montant": montant_total,
                    "positions": positions,
                    "solde_especes": especes,
                    "metadata_parsing": {
                        "parser_used": self.strategy_name,
                        "parsed_at": datetime.now().isoformat(),
                        "warnings": [],
                        "total_positions": len(positions),
                        "total_valorisation": montant_total
                    }
                }

        except Exception as e:
            raise ParsingError(f"Erreur parsing BforBank CTO {filepath}: {str(e)}")

    def _parse_positions(self, rows: List[List[str]]) -> List[Dict[str, Any]]:
        """Parse les lignes de positions"""
        positions = []

        for row in rows:
            try:
                if not row or len(row) < 6:
                    continue

                designation = row[0] if row[0] else ""
                quantite_str = row[2] if len(row) > 2 and row[2] else "0"
                cours_str = row[3] if len(row) > 3 and row[3] else "0"
                valorisation_str = row[5] if len(row) > 5 and row[5] else "0"

                # Extraire nom et ISIN de la désignation
                # Format: "NOM\nISIN" (avec retour chariot)
                if "\n" in designation:
                    parts = designation.split("\n")
                    nom = parts[0].strip()
                    isin = parts[1].strip() if len(parts) > 1 else ""
                else:
                    # Fallback: format "NOM (ISIN)" (parenthèses)
                    match = re.search(r"^(.+?)\s*\(([A-Z]{2}[A-Z0-9]{10})\)", designation)
                    if match:
                        nom = match.group(1).strip()
                        isin = match.group(2).strip()
                    else:
                        nom = designation.strip()
                        isin = ""

                # Parser les montants
                quantite = self._parse_amount(quantite_str)
                cours = self._parse_amount(cours_str)
                valorisation = self._parse_amount(valorisation_str)

                # Valider que ce n'est pas une ligne vide
                if quantite == 0 and valorisation == 0:
                    continue

                positions.append({
                    "nom": nom,
                    "ticker": isin,
                    "quantite": quantite,
                    "prix": cours,
                    "valeur": valorisation,
                    "type": "Action"  # Par défaut, peut être ETF aussi
                })

            except Exception as e:
                # Logger l'erreur mais continuer
                print(f"Warning: Erreur parsing ligne {row}: {e}")
                continue

        return positions

    def validate(self, parsed_data: dict) -> List[str]:
        """Valide les données parsées"""
        anomalies = []

        # Vérifier structure de base
        if "montant" not in parsed_data:
            anomalies.append("Montant total manquant")
        if "positions" not in parsed_data:
            anomalies.append("Positions manquantes")

        # Vérifier cohérence montant
        if "positions" in parsed_data and "solde_especes" in parsed_data:
            total_calc = sum(p["valeur"] for p in parsed_data["positions"]) + parsed_data["solde_especes"]
            montant_declare = parsed_data.get("montant", 0)

            # Tolérance de 0.01 € pour erreurs d'arrondi
            if abs(total_calc - montant_declare) > 0.01:
                anomalies.append(
                    f"Incohérence montant: calculé {total_calc:.2f} € vs déclaré {montant_declare:.2f} €"
                )

        # Vérifier nombre de positions
        if "positions" in parsed_data and len(parsed_data["positions"]) == 0:
            anomalies.append("Aucune position trouvée")

        # Vérifier ISINs
        for pos in parsed_data.get("positions", []):
            if "ticker" in pos and pos["ticker"]:
                if not self._is_valid_isin(pos["ticker"]):
                    anomalies.append(f"ISIN invalide: {pos['ticker']}")

        return anomalies
