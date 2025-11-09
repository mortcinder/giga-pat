"""
Parser pour PEA/PEA-PME Crédit Agricole format web multipage (2025+)
Extrait du code existant de normalizer.py (lignes 852-953)
"""

import re
import pdfplumber
from datetime import datetime
from typing import Dict, Any, List
from ..base_parser import BaseParser, ParsingError


class CreditAgricolePEA2025Parser(BaseParser):
    """Parser pour PEA Crédit Agricole format web multipage (octobre 2025+)"""

    @property
    def strategy_name(self) -> str:
        return "credit_agricole.pea.v2025"

    @property
    def supported_formats(self) -> List[str]:
        return ["pdf"]

    def can_parse(self, filepath: str, metadata: dict) -> float:
        """Détecte format web CA avec heuristiques spécifiques"""
        try:
            # Vérifier établissement
            if metadata.get("etablissement", "").lower() not in ["credit_agricole", "ca"]:
                return 0.0

            # Vérifier type de compte
            type_compte = metadata.get("type_compte", "").upper()
            if type_compte not in ["PEA", "PEA-PME"]:
                return 0.0

            # Analyser le PDF
            with pdfplumber.open(filepath) as pdf:
                if not pdf.pages:
                    return 0.0

                text = pdf.pages[0].extract_text()
                if not text:
                    return 0.0

                text_lower = text.lower()

                # Heuristiques de détection format web 2025
                has_mandat_pea = "mandat pea" in text_lower
                has_compte_pea = "compte pea" in text_lower
                has_portefeuille = "portefeuille" in text_lower
                has_valorisation_totale = "ma valorisation totale" in text_lower or "valorisation totale" in text_lower
                is_multipage = len(pdf.pages) > 1

                # Exclusion : pas un PER (plus spécifique)
                has_per = "plan épargne retraite" in text_lower or "plan d'épargne retraite" in text_lower
                if has_per:
                    return 0.0

                # Score de confiance
                score = 0.0
                if has_mandat_pea or has_compte_pea:
                    score += 0.4
                if has_portefeuille:
                    score += 0.2
                if has_valorisation_totale:
                    score += 0.3
                if is_multipage:
                    score += 0.1

                return min(score, 1.0)

        except Exception:
            return 0.0

    def parse(self, filepath: str, metadata: dict) -> Dict[str, Any]:
        """Parse le PDF PEA format web multipage"""
        try:
            with pdfplumber.open(filepath) as pdf:
                # Extraire texte complet (pour solde espèces)
                text = "\n".join(page.extract_text() or "" for page in pdf.pages)

                # Extraire toutes les tables
                all_tables = []
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        if table:
                            all_tables.append(table)

                # Parser les tables
                positions = self._parse_pea_tables(all_tables)

                # Extraire solde espèces
                solde_especes = self._extract_solde_especes(text)

                # Calculer montant total
                total_positions = sum(p["valeur"] for p in positions)
                montant_total = total_positions + solde_especes

                return {
                    "type": metadata.get("type_compte", "PEA"),
                    "montant": montant_total,
                    "positions": positions,
                    "solde_especes": solde_especes,
                    "metadata_parsing": {
                        "parser_used": self.strategy_name,
                        "parsed_at": datetime.now().isoformat(),
                        "nb_positions": len(positions),
                        "warnings": []
                    }
                }

        except Exception as e:
            raise ParsingError(f"Erreur parsing PEA CA v2025: {e}")

    def validate(self, parsed_data: dict) -> List[str]:
        """Valide les données parsées"""
        anomalies = []

        # Vérifier cohérence montant
        total_calc = sum(p["valeur"] for p in parsed_data.get("positions", []))
        total_calc += parsed_data.get("solde_especes", 0)
        montant_declare = parsed_data.get("montant", 0)

        if abs(total_calc - montant_declare) > 1.0:  # Tolérance 1€
            anomalies.append(
                f"Écart valorisation : {abs(total_calc - montant_declare):.2f}€ "
                f"(calculé: {total_calc:.2f}€ vs déclaré: {montant_declare:.2f}€)"
            )

        # Vérifier ISINs valides
        for pos in parsed_data.get("positions", []):
            ticker = pos.get("ticker", "")
            if ticker and not self._is_valid_isin(ticker):
                anomalies.append(f"ISIN potentiellement invalide : {pos.get('nom')} ({ticker})")

        # Vérifier valeurs positives
        if montant_declare < 0:
            anomalies.append(f"Montant total négatif : {montant_declare:.2f}€")

        for pos in parsed_data.get("positions", []):
            if pos.get("valeur", 0) < 0:
                anomalies.append(f"Valeur négative pour position : {pos.get('nom')}")

        return anomalies

    def _parse_pea_tables(self, tables: list) -> List[Dict[str, Any]]:
        """
        Parse les tables d'un PEA ou PEA-PME
        Format Crédit Agricole web :
        - Ligne d'en-tête : [Valeur, Quantité, Cours, Variation (1J), Prix de revient, Valorisation, +/- Value latente]
        - Lignes de données :
          - Colonne Valeur : "NOM ACTION\\nISIN CODE"
          - Colonne Quantité, Cours, Valorisation
        """
        positions = []
        header_found = False

        for table in tables:
            if not table or len(table) < 2:
                continue

            # Chercher l'en-tête dans cette table
            header_idx = -1
            for i, row in enumerate(table):
                if row and any("Valeur" in str(cell) for cell in row if cell):
                    header_idx = i
                    header_found = True
                    break

            # Si l'en-tête est trouvé, parser à partir de la ligne suivante
            # Sinon, si header_found est True (trouvé dans une table précédente), parser depuis le début
            start_idx = header_idx + 1 if header_idx >= 0 else (0 if header_found else -1)

            if start_idx < 0:
                continue

            # Parser les lignes de données
            for row in table[start_idx:]:
                if not row or len(row) < 7:
                    continue

                # Détecter le décalage de colonnes (page 1 vs page 2+)
                # Page 1 : colonnes vides en 0-1, données en 2-9
                # Page 2+ : données directement en 0-7
                offset = 2 if (len(row) > 9 and (not row[0] or str(row[0]).strip() == '')) else 0

                # Extraire les données avec offset
                valeur_cell = str(row[offset + 0]) if len(row) > offset and row[offset] else ""
                quantite_cell = str(row[offset + 1]) if len(row) > offset + 1 and row[offset + 1] else ""
                cours_cell = str(row[offset + 2]) if len(row) > offset + 2 and row[offset + 2] else ""

                # Valorisation: colonne 7 avec offset=2 (page 1), colonne 6 avec offset=0 (page 2)
                valorisation_idx = 7 if offset == 2 else 6
                valorisation_cell = str(row[valorisation_idx]) if len(row) > valorisation_idx and row[valorisation_idx] else ""

                # Ignorer les lignes vides
                if not valeur_cell or len(valeur_cell) < 5:
                    continue

                # Extraire nom et ISIN (format: "NOM\\nISIN CODE")
                valeur_parts = valeur_cell.split('\n')
                nom = valeur_parts[0].strip() if len(valeur_parts) > 0 else ""
                isin_code = valeur_parts[1].strip() if len(valeur_parts) > 1 else ""

                # Extraire ISIN (avant le code ticker)
                isin = ""
                if isin_code:
                    # Format: "FR0000120404 AC" -> ISIN = "FR0000120404"
                    isin = isin_code.split()[0] if isin_code else ""

                # Parser les montants
                quantite = self._parse_amount(quantite_cell)
                cours = self._parse_amount(cours_cell)
                valorisation = self._parse_amount(valorisation_cell)

                if nom and valorisation > 0:
                    position = {
                        "nom": nom,
                        "ticker": isin,
                        "quantite": quantite,
                        "prix": cours,
                        "valeur": valorisation
                    }
                    positions.append(position)

        return positions

    def _extract_solde_especes(self, text: str) -> float:
        """
        Extrait le solde espèces depuis le texte du PDF PEA/PEA-PME

        Le solde espèces est extrait depuis la ligne de valorisation totale:
        Format: "X € = Y € + Z € = ..." où Z est le solde espèces
        Ex: "6 133,22 € = 970,14 € + 5 163,08 € = 0,00 % + 11,51 €"
            -> solde espèces = 5 163,08 €
        """
        if not text:
            return 0.0

        # Chercher la ligne avec "Ma valorisation totale" suivie de la formule
        lines = text.split('\n')
        for i, line in enumerate(lines):
            # Si on trouve "Ma valorisation totale", regarder la ligne suivante
            if 'ma valorisation' in line.lower() or 'valorisation totale' in line.lower():
                if i + 1 < len(lines):
                    valorisation_line = lines[i + 1]
                    # Extraire tous les montants de la ligne
                    montants = re.findall(r'([\d\s,\.]+)\s*€', valorisation_line)
                    if len(montants) >= 3:
                        # Le 3ème montant est le solde espèces
                        especes_str = montants[2]
                        # Nettoyer: enlever espaces, remplacer virgule par point
                        especes_str = especes_str.replace(' ', '').replace(',', '.')
                        try:
                            return float(especes_str)
                        except ValueError:
                            pass

        # Fallback: si la méthode ci-dessus échoue, essayer d'extraire depuis "Solde disponible"
        match = re.search(r'Solde[^\n]*?:([^€]+)€', text, re.IGNORECASE)
        if match:
            montant_str = match.group(1)
            montant_str = re.sub(r'[^0-9,\.\s]', '', montant_str)
            return self._parse_amount(montant_str)

        return 0.0
