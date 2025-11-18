r"""
Parser pour PER BoursoBank format PDF (2025)
Avec stratégie de fallback progressive en cas d'échec d'extraction
Gestion des caractères Unicode corrompus (Private Use Area \ue0xx)
"""

import re
import pdfplumber
from datetime import datetime
from typing import Dict, Any, List, Optional
from ..base_parser import BaseParser, ParsingError


def clean_pdf_text(text: Optional[str]) -> str:
    r"""
    Nettoie le texte extrait d'un PDF en remplaçant les caractères Unicode
    corrompus (Private Use Area \ue000-\uf8ff) par des équivalents lisibles.

    Mapping complet basé sur l'analyse du format propriétaire BoursoBank.

    Args:
        text: Texte brut extrait du PDF (peut être None)

    Returns:
        Texte nettoyé et décodé
    """
    if not text:
        return ""

    # Mapping complet des caractères propriétaires BoursoBank
    replacements = {
        # Chiffres (\ue0f1-\ue0fa = 0-9)
        '\ue0f1': '0',
        '\ue0f2': '1',
        '\ue0f3': '2',
        '\ue0f4': '3',
        '\ue0f5': '4',
        '\ue0f6': '5',
        '\ue0f7': '6',
        '\ue0f8': '7',
        '\ue0f9': '8',
        '\ue0fa': '9',

        # Ponctuation et symboles
        '\ue06c': ',',
        '\ue062': '/',
        '\ue061': ' ',
        '\ue04c': '.',
        '\ue04e': '(',
        '\ue05e': ')',
        '\ue052': 'é',
        '\ue07e': "'",
        '\ue07b': ':',
        '\ue072': 'é',
        '\ue113': '€',
        '\ue04f': '-',
        '\ue05d': '%',
        '\ue055': '=',
        '\ue045': '?',
        '\ue053': '!',
        '\ue057': ';',
        '\ue03f': '?',
        '\ue06e': ' ',
        '\ue06d': '~',
        '\ue0b6': '+',
        '\ue112': '£',
        '\ue114': '$',

        # Lettres majuscules (\ue0c0-\ue0ea)
        '\ue0c2': 'A',
        '\ue0c3': 'B',
        '\ue0c4': 'C',
        '\ue0c5': 'D',
        '\ue0c6': 'E',
        '\ue0c7': 'F',
        '\ue0c8': 'G',
        '\ue0c9': 'H',
        '\ue0ca': 'I',
        '\ue0d2': 'J',
        '\ue0d3': 'K',
        '\ue0d4': 'L',
        '\ue0d5': 'M',
        '\ue0d6': 'N',
        '\ue0d7': 'O',
        '\ue0d8': 'P',
        '\ue0d9': 'Q',
        '\ue0da': 'R',
        '\ue0e3': 'S',
        '\ue0e4': 'T',
        '\ue0e5': 'U',
        '\ue0e6': 'V',
        '\ue0e8': 'W',
        '\ue0e9': 'X',
        '\ue0ea': 'Y',

        # Lettres minuscules (\ue082-\ue0aa)
        '\ue082': 'a',
        '\ue083': 'b',
        '\ue084': 'c',
        '\ue085': 'd',
        '\ue086': 'e',
        '\ue087': 'f',
        '\ue088': 'g',
        '\ue089': 'h',
        '\ue08a': 'i',
        '\ue091': 'j',
        '\ue092': 'k',
        '\ue094': 'l',
        '\ue095': 'm',
        '\ue096': 'n',
        '\ue097': 'o',
        '\ue098': 'p',
        '\ue099': 'q',
        '\ue09a': 'r',
        '\ue0a3': 's',
        '\ue0a4': 't',
        '\ue0a5': 'u',
        '\ue0a6': 'v',
        '\ue0a7': 'w',
        '\ue0a8': 'x',
        '\ue0a9': 'y',
        '\ue0aa': 'z',
    }

    # Appliquer tous les remplacements
    cleaned = text
    for old_char, new_char in replacements.items():
        cleaned = cleaned.replace(old_char, new_char)

    # Supprimer les caractères non mappés restants
    cleaned = re.sub(r'[\ue000-\uf8ff]', '', cleaned)

    return cleaned


class BoursoBankPER2025Parser(BaseParser):
    """Parser pour PER BoursoBank avec fallback manuel (2025+)"""

    @property
    def strategy_name(self) -> str:
        return "boursobank.per.v2025"

    @property
    def supported_formats(self) -> List[str]:
        return ["pdf"]

    def can_parse(self, filepath: str, metadata: dict) -> float:
        """Détecte format BoursoBank PER"""
        try:
            # Vérifier établissement
            custodian = metadata.get("custodian", "").lower()
            if custodian not in ["boursobank", "bob", "bourse bank"]:
                return 0.0

            # Vérifier type de compte
            type_compte = metadata.get("type_compte", "").upper()
            if type_compte != "PER":
                return 0.0

            # Si metadata correspondent exactement, haute confiance
            # (permet de gérer les PDFs corrompus avec fallback manuel)
            if custodian in ["boursobank", "bob"] and type_compte == "PER":
                # Vérifier que le fichier est bien un PDF
                if filepath.lower().endswith('.pdf'):
                    # Tenter de lire le PDF
                    try:
                        with pdfplumber.open(filepath) as pdf:
                            if not pdf.pages:
                                return 0.0

                            raw_text = pdf.pages[0].extract_text()
                            text = clean_pdf_text(raw_text)

                            # Si le texte est lisible, vérifier les mots-clés
                            if text and len(text.strip()) > 50:
                                text_lower = text.lower()
                                has_boursobank = "boursobank" in text_lower or "bourse bank" in text_lower
                                has_per = "per" in text_lower or "plan épargne retraite" in text_lower or "épargne retraite" in text_lower
                                has_retraite = "retraite" in text_lower

                                score = 0.0
                                if has_boursobank:
                                    score += 0.4
                                if has_per:
                                    score += 0.4
                                if has_retraite:
                                    score += 0.2

                                return min(score, 1.0)
                            else:
                                # PDF corrompu ou vide, mais metadata correspondent
                                # → On peut gérer avec fallback manuel
                                return 0.9

                    except Exception:
                        # Erreur de lecture PDF, mais metadata correspondent
                        return 0.8

            return 0.0

        except Exception:
            return 0.0

    def parse(self, filepath: str, metadata: dict) -> Dict[str, Any]:
        """Parse le PDF PER BoursoBank avec stratégie de fallback"""
        warnings = []

        # Stratégie 1 : Tentative d'extraction depuis le PDF
        try:
            result = self._parse_pdf_standard(filepath, metadata)
            if result:
                return result
        except Exception as e:
            warnings.append(f"Extraction PDF échouée: {str(e)}")

        # Stratégie 2 : Fallback manuel depuis metadata
        try:
            result = self._fallback_manual(metadata)
            result["metadata_parsing"]["warnings"] = warnings
            result["metadata_parsing"]["fallback_used"] = True
            return result
        except Exception as e:
            raise ParsingError(f"Toutes les stratégies d'extraction ont échoué pour {filepath}: {str(e)}")

    def _parse_pdf_standard(self, filepath: str, metadata: dict) -> Dict[str, Any]:
        """Tentative d'extraction standard depuis le PDF"""
        with pdfplumber.open(filepath) as pdf:
            # Extraire texte complet avec nettoyage
            text = "\n".join(clean_pdf_text(page.extract_text()) for page in pdf.pages)

            if not text or len(text.strip()) < 50:
                raise ParsingError("PDF vide ou corrompu")

            # Extraire toutes les tables avec nettoyage
            all_tables = []
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    if table:
                        # Nettoyer chaque cellule du tableau
                        cleaned_table = [
                            [clean_pdf_text(str(cell)) if cell else '' for cell in row]
                            for row in table
                        ]
                        all_tables.append(cleaned_table)

            if not all_tables:
                raise ParsingError("Aucune table détectable dans le PDF")

            # Parser les tables
            positions = self._parse_per_tables(all_tables)

            # Calculer montant total
            total_positions = sum(p["valeur"] for p in positions)

            # Si on a réussi à extraire des positions valides
            if total_positions > 0:
                return {
                    "type": "PER",
                    "montant": total_positions,
                    "positions": positions,
                    "metadata_parsing": {
                        "parser_used": self.strategy_name,
                        "parsed_at": datetime.now().isoformat(),
                        "warnings": [],
                        "extraction_method": "pdf_standard"
                    }
                }
            else:
                raise ParsingError("Aucune position valide extraite")

    def _parse_per_tables(self, tables: List[List[List[str]]]) -> List[Dict[str, Any]]:
        """
        Parse les tables PER (format BoursoBank).

        Format observé dans les relevés BoursoBank PER :
        - Colonne 0 : Nom du support (ex: "PD ISHARES MSCI USA...")
        - Colonne 1 : Valeur en euros (ex: "€\n1 190,76" ou "€ 1 190,76")
        - Colonnes suivantes : Performance, nombre d'UC, etc.
        """
        positions = []

        for table in tables:
            if not table or len(table) < 2:
                continue

            # Analyser chaque ligne du tableau
            for row in table:
                if not row or len(row) < 2:
                    continue

                try:
                    # Colonne 0 = nom du support
                    nom = row[0].strip() if row[0] else ""

                    # Ignorer les lignes de header ou vides
                    if not nom:
                        continue

                    # Ignorer les en-têtes de colonnes
                    if any(keyword in nom.upper() for keyword in [
                        "SUPPORT", "VALORISATION", "VALEUR", "PERFORMANCE",
                        "CODE ISIN", "FRAIS", "UC ", "TABLEAU"
                    ]):
                        continue

                    # Ignorer les lignes de total
                    if "TOTAL" in nom.upper() or "SOUS-TOTAL" in nom.upper():
                        continue

                    # Chercher les montants en euros dans la colonne 1
                    # IMPORTANT : certaines lignes peuvent contenir plusieurs supports fusionnés
                    # avec plusieurs montants séparés par des retours à la ligne
                    cell_val = row[1] if len(row) > 1 else ""

                    if cell_val and ('€' in cell_val or 'EUR' in cell_val.upper()):
                        # Extraire TOUS les montants de la cellule (il peut y en avoir plusieurs)
                        montants = re.findall(r'€?\s*(\d[\d\s]*,\d+)', cell_val)

                        if not montants:
                            continue

                        # Séparer les noms s'ils sont fusionnés (détectés par "PD " répété)
                        noms_parts = nom.split('\nPD ')
                        if len(noms_parts) == 1:
                            noms_parts = [nom]
                        else:
                            # Reconstituer "PD " au début du 2ème support
                            noms_parts = [noms_parts[0]] + ['PD ' + p for p in noms_parts[1:]]

                        # Associer chaque nom avec son montant
                        for idx, montant_str in enumerate(montants):
                            valorisation = self._parse_amount(montant_str)

                            if valorisation <= 0:
                                continue

                            # Utiliser le nom correspondant (ou le premier si fusion incomplète)
                            nom_support = noms_parts[idx] if idx < len(noms_parts) else noms_parts[0]

                            # Nettoyer le nom
                            nom_clean = ' '.join(nom_support.split())

                            # Ignorer les noms trop courts
                            if len(nom_clean) < 5:
                                continue

                            # Vérifier que ce n'est pas un doublon
                            is_duplicate = any(
                                p['nom'] == nom_clean and abs(p['valeur'] - valorisation) < 0.01
                                for p in positions
                            )

                            if not is_duplicate:
                                positions.append({
                                    "nom": nom_clean,
                                    "ticker": "",
                                    "quantite": 1,
                                    "prix": valorisation,
                                    "valeur": valorisation,
                                    "type": "PER"
                                })

                except Exception as e:
                    # Ignorer silencieusement les erreurs de parsing de lignes individuelles
                    continue

        return positions

    def _fallback_manual(self, metadata: dict) -> Dict[str, Any]:
        """Fallback : utilise le montant manuel du metadata"""
        # Chercher montant dans différents endroits du metadata
        montant = None

        # Option 1 : montant_manuel dans metadata
        if "montant_manuel" in metadata:
            montant = float(metadata["montant_manuel"])

        # Option 2 : montant direct dans metadata
        elif "montant" in metadata:
            montant = float(metadata["montant"])

        # Option 3 : chercher dans les sections manuelles du manifest
        # (sera géré par le normalizer directement)

        if montant is None or montant == 0:
            raise ParsingError("Aucun montant manuel trouvé dans metadata")

        return {
            "type": "PER",
            "montant": montant,
            "positions": [],  # Pas de détail de positions avec fallback manuel
            "metadata_parsing": {
                "parser_used": self.strategy_name,
                "parsed_at": datetime.now().isoformat(),
                "warnings": ["Fallback manuel : extraction PDF impossible (encodage corrompu)"],
                "extraction_method": "manual_fallback",
                "fallback_used": True
            }
        }

    def validate(self, parsed_data: dict) -> List[str]:
        """Valide les données parsées"""
        anomalies = []

        # Vérifier structure de base
        if "montant" not in parsed_data:
            anomalies.append("Montant total manquant")

        # Vérifier montant cohérent
        if "montant" in parsed_data and parsed_data["montant"] <= 0:
            anomalies.append(f"Montant invalide: {parsed_data['montant']}")

        # Si fallback utilisé, c'est normal de ne pas avoir de positions
        is_fallback = parsed_data.get("metadata_parsing", {}).get("fallback_used", False)

        if not is_fallback:
            # Mode extraction normale : vérifier positions
            if "positions" not in parsed_data or len(parsed_data["positions"]) == 0:
                anomalies.append("Aucune position trouvée (mode extraction)")

        return anomalies
