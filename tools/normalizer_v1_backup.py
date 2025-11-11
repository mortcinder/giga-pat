"""
Module de normalisation des fichiers sources
Suit les spécifications de la section 3.1 du PRD
"""

import json
import logging
import re
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from tools.utils.file_parser import FileParser


class PatrimoineNormalizer:
    """Normalise les fichiers sources en JSON structuré"""
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.file_parser = FileParser()
        
    def normalize(self) -> dict:
        """Point d'entrée principal de normalisation"""
        self.logger.info("Début normalisation...")

        # 1. Parse patrimoine.md
        self.logger.info("Lecture patrimoine.md...")
        patrimoine_data = self._parse_patrimoine_md()

        # 2. Enrich with etablissements metadata
        self.logger.info("Enrichissement métadonnées établissements...")
        self._enrich_etablissements_metadata(patrimoine_data)

        # 3. Load referenced files
        self.logger.info(f"Parsing {len(patrimoine_data.get('sources_files', []))} fichiers sources...")
        self._load_source_files(patrimoine_data)

        # 4. Calculate totals
        self.logger.info("Calcul totaux par catégorie...")
        self._calculate_totals(patrimoine_data)

        # 5. Validate
        self.logger.info("Validation données...")
        self._validate(patrimoine_data)

        # 6. Save JSON
        output_path = Path(self.config["paths"]["generated"]) / self.config["normalizer"]["output_file"]
        self.logger.info(f"Sauvegarde {output_path}...")
        self._save_json(patrimoine_data, output_path)

        self.logger.info("✓ Normalisation terminée")
        return patrimoine_data
    
    def _parse_patrimoine_md(self) -> dict:
        """
        Parse le fichier patrimoine.md et extrait les données structurées
        Suit les spécifications de la section 3.1.5 du PRD
        """
        md_path = Path(self.config["paths"]["sources"]) / self.config["normalizer"]["input_file"]

        if not md_path.exists():
            raise FileNotFoundError(f"Fichier patrimoine.md introuvable : {md_path}")

        content = md_path.read_text(encoding='utf-8')
        lines = content.splitlines()

        # Structure de base conforme à la section 3.1.4
        data = {
            "meta": {
                "version": "1.0.0",
                "generated_at": datetime.now().isoformat(),
                "source_file": str(md_path)
            },
            "profil": {},
            "patrimoine": {
                "financier": {"total": 0, "etablissements": []},
                "crypto": {"total": 0, "plateformes": []},
                "metaux_precieux": {"total": 0},
                "immobilier": {"total": 0, "biens": []}
            },
            "sources_files": []
        }

        # Parsing ligne par ligne
        current_section = None
        current_etablissement = None
        current_plateforme = None
        current_subsection = None  # Track subsections like "#### Métaux"

        for line_idx, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # Détection sections principales
            if line.startswith("## Profil"):
                current_section = "profil"
                current_subsection = None
                continue
            elif line.startswith("## Epargne") or line.startswith("## Épargne"):
                current_section = "epargne"
                current_subsection = None
                continue
            elif line.startswith("## Crypto") or line.startswith("## Cryptomonnaie"):
                current_section = "crypto"
                current_subsection = None
                continue
            elif line.startswith("## Métaux") or line.startswith("## Metaux"):
                current_section = "metaux"
                current_subsection = None
                continue
            elif line.startswith("## Immobilier"):
                current_section = "immobilier"
                current_subsection = None
                continue

            # Détection subsections (#### Métaux, #### Actifs, etc.)
            if line.startswith("#### "):
                subsection_match = re.match(r"####\s+(.+)", line)
                if subsection_match:
                    current_subsection = subsection_match.group(1).strip().lower()
                    continue

            # Section Profil
            if current_section == "profil" and line.startswith("- "):
                self._parse_profil_line(line, data["profil"])

            # Section Epargne (établissements financiers)
            elif current_section == "epargne":
                if line.startswith("### "):
                    # Nouveau établissement
                    etab_match = re.match(r"###\s+(\w+)(?:\s+\((.+?)\))?$", line)
                    if etab_match:
                        code_or_nom = etab_match.group(1)
                        nom = etab_match.group(2) if etab_match.group(2) else code_or_nom

                        # Check if this is "Veracash" (metals platform) or similar without code
                        if etab_match.group(2):
                            code = code_or_nom
                        else:
                            code = code_or_nom
                            nom = code_or_nom

                        current_etablissement = {
                            "nom": nom,
                            "code": code,
                            "juridiction": "France",  # Par défaut
                            "total": 0,
                            "comptes": []
                        }
                        data["patrimoine"]["financier"]["etablissements"].append(current_etablissement)
                        current_subsection = None  # Reset subsection for new establishment
                elif line.startswith("- ") and current_etablissement is not None:
                    # Check if we're in a "métaux" subsection
                    if current_subsection and ("métaux" in current_subsection or "metaux" in current_subsection):
                        # Parse as metals, not as compte
                        self._parse_metaux_line(line, data["patrimoine"]["metaux_precieux"], current_etablissement.get("nom"))
                    else:
                        self._parse_compte_line(line, current_etablissement, data["sources_files"])

            # Section Crypto
            elif current_section == "crypto":
                if line.startswith("### "):
                    # Nouvelle plateforme crypto
                    plat_match = re.match(r"###\s+(.+?)(?:\s+\((.+?)\))?$", line)
                    if plat_match:
                        nom = plat_match.group(1)
                        current_plateforme = {
                            "nom": nom,
                            "juridiction": "France",  # Par défaut
                            "total": 0,
                            "actifs": []
                        }
                        data["patrimoine"]["crypto"]["plateformes"].append(current_plateforme)
                elif line.startswith("- ") and current_plateforme is not None:
                    self._parse_crypto_line(line, current_plateforme, data["sources_files"])

            # Section Métaux précieux (standalone section, not subsection)
            elif current_section == "metaux" and line.startswith("- "):
                self._parse_metaux_line(line, data["patrimoine"]["metaux_precieux"], None)

            # Section Immobilier
            elif current_section == "immobilier" and line.startswith("### "):
                self._parse_immobilier_line(line_idx, lines, data["patrimoine"]["immobilier"])

        # Nettoyer les établissements financiers vides (ex: Veracash dont les comptes sont dans metaux_precieux)
        data["patrimoine"]["financier"]["etablissements"] = [
            etab for etab in data["patrimoine"]["financier"]["etablissements"]
            if etab.get("total", 0) > 0 or len(etab.get("comptes", [])) > 0
        ]

        self.logger.info(f"patrimoine.md parsé : {len(content.splitlines())} lignes, {len(data['sources_files'])} fichiers référencés")
        return data

    def _enrich_etablissements_metadata(self, data: dict):
        """
        Enrichit les établissements avec les métadonnées de etablissements_financiers.json
        Ajoute juridiction, exposition Sapin 2, garantie dépôts, etc.
        """
        # Charger le fichier etablissements_financiers.json
        metadata_path = Path(self.config["paths"]["sources"]) / "etablissements_financiers.json"

        if not metadata_path.exists():
            self.logger.warning(f"Fichier etablissements_financiers.json introuvable : {metadata_path}")
            return

        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                etablissements_meta = metadata.get("etablissements", {})

            self.logger.debug(f"Chargé etablissements_financiers.json : {len(etablissements_meta)} établissements")

            # Mapping code -> clé JSON
            code_mapping = {
                "CA": "credit_agricole",
                "BFB": "bforbank",
                "SG": "societe_generale",
                "BOB": "boursobank",
                "DGO": "degiro",
                "Spiko": "spiko",
                "Veracash": "veracash",
                "Ledger": "ledger",
                "Bitstack": "bitstack",
                "CrypCool": "crypcool",
                "Aave": "aave"
            }

            # Enrichir les établissements financiers
            for etab in data.get("patrimoine", {}).get("financier", {}).get("etablissements", []):
                code = etab.get("code", "")
                nom = etab.get("nom", "")

                # Trouver la clé correspondante
                meta_key = code_mapping.get(code) or code_mapping.get(nom)

                if meta_key and meta_key in etablissements_meta:
                    meta = etablissements_meta[meta_key]

                    # Enrichir avec les métadonnées
                    etab["juridiction"] = meta.get("juridiction_principale", "France")
                    etab["juridiction_pays"] = meta.get("pays", "France")
                    etab["type_etablissement"] = meta.get("type", "Banque")
                    etab["garantie_depots"] = meta.get("garantie_depots", "N/A")
                    etab["exposition_sapin_2"] = meta.get("exposition_sapin_2", "NON")
                    etab["exposition_risque_france"] = meta.get("exposition_risque_france", "MOYENNE")
                    etab["regulation"] = meta.get("regulation", [])

                    self.logger.debug(f"  Enrichi {nom} ({code}) : juridiction={etab['juridiction']}, Sapin2={etab['exposition_sapin_2']}")
                else:
                    self.logger.warning(f"  Métadonnées introuvables pour {nom} ({code})")

            # Enrichir les plateformes crypto
            for plat in data.get("patrimoine", {}).get("crypto", {}).get("plateformes", []):
                nom = plat.get("nom", "")
                meta_key = code_mapping.get(nom)

                if meta_key and meta_key in etablissements_meta:
                    meta = etablissements_meta[meta_key]

                    plat["juridiction"] = meta.get("juridiction_principale", "France")
                    plat["juridiction_pays"] = meta.get("pays", "France")
                    plat["type_plateforme"] = meta.get("type", "Plateforme crypto")
                    plat["exposition_risque_france"] = meta.get("exposition_risque_france", "MOYENNE")
                    plat["custody_type"] = meta.get("custody_type", "Custodial")

                    self.logger.debug(f"  Enrichi plateforme crypto {nom} : juridiction={plat['juridiction']}")

            # Enrichir métaux précieux
            metaux = data.get("patrimoine", {}).get("metaux_precieux", {})
            plateforme_metaux = metaux.get("plateforme", "")

            if plateforme_metaux:
                meta_key = code_mapping.get(plateforme_metaux)

                if meta_key and meta_key in etablissements_meta:
                    meta = etablissements_meta[meta_key]

                    metaux["juridiction"] = meta.get("juridiction_principale", "France")
                    metaux["juridiction_pays"] = meta.get("pays", "France")
                    metaux["stockage"] = meta.get("stockage", "N/A")
                    metaux["exposition_risque_france"] = meta.get("exposition_risque_france", "FAIBLE")

                    self.logger.debug(f"  Enrichi métaux précieux {plateforme_metaux} : juridiction={metaux['juridiction']}")

            self.logger.info(f"✓ Enrichissement terminé : {len(data.get('patrimoine', {}).get('financier', {}).get('etablissements', []))} établissements")

        except Exception as e:
            self.logger.error(f"Erreur lors de l'enrichissement des métadonnées : {e}")

    def _parse_profil_line(self, line: str, profil: dict):
        """Parse une ligne de profil (ex: '- Genre : Homme')"""
        match = re.match(r"-\s*(.+?)\s*:\s*(.+)", line)
        if match:
            key = match.group(1).strip().lower().replace(" ", "_").replace("'", "")
            value = match.group(2).strip()

            # Normalisation des clés
            key_mapping = {
                "genre": "genre",
                "date_de_naissance": "date_naissance",
                "situation_familiale": "situation_familiale",
                "enfants": "enfants",
                "nombre_denfants": "enfants",  # Support "Nombre d'enfants"
                "type_dinvestissement": "type_investissement",
                "type_investissement": "type_investissement",
                "statut": "statut",
                "profession": "profession",
                "revenu": "revenu_mensuel_net"
            }

            normalized_key = key_mapping.get(key, key)

            # Conversion des valeurs
            if "date" in normalized_key and "/" in value:
                # Format DD/MM/YYYY -> YYYY-MM-DD
                parts = value.split("/")
                if len(parts) == 3:
                    value = f"{parts[2]}-{parts[1]}-{parts[0]}"
                    # Calcul de l'âge si date de naissance
                    if normalized_key == "date_naissance":
                        birth_year = int(parts[2])
                        current_year = datetime.now().year
                        profil["age"] = current_year - birth_year

            # Extraction des montants
            amount_match = re.search(r"([\d\s,]+)\s*€", value)
            if amount_match:
                value = self._parse_amount(amount_match.group(1))

            # Conversion nombre d'enfants
            if normalized_key == "enfants" and value.isdigit():
                value = int(value)

            profil[normalized_key] = value

    def _parse_compte_line(self, line: str, etablissement: dict, sources_files: list):
        """
        Parse une ligne de compte
        Formats supportés:
        - '- PEA : 82 186,48 €' (montant en EUR)
        - '- Compte en $ : 8076,20 $' (montant en USD, converti en EUR)
        """
        # Détection fichier référencé
        file_ref = re.search(r'"(.+?\.(?:csv|pdf|json))"', line, re.IGNORECASE)
        if file_ref:
            filename = file_ref.group(1)
            if filename not in sources_files:
                sources_files.append(filename)
            return

        # Parsing compte avec montant (€ ou $)
        match = re.match(r"-\s*(.+?)\s*(?:\((\w+)\))?\s*:\s*([\d\s,.]+)\s*([€$])", line)
        if match:
            type_compte = match.group(1).strip()
            montant_str = match.group(3)
            devise = match.group(4)

            montant = self._parse_amount(montant_str)

            # Conversion USD → EUR si nécessaire
            if devise == "$":
                montant = montant * 0.92  # Taux USD → EUR approximatif
                self.logger.debug(f"Converti {montant_str} $ → {montant:.2f} €")

            compte = {
                "type": type_compte,
                "montant": montant
            }

            # Ajout du compte
            etablissement["comptes"].append(compte)
            etablissement["total"] += montant

    def _parse_crypto_line(self, line: str, plateforme: dict, sources_files: list):
        """
        Parse une ligne crypto
        Formats supportés:
        - '- BTC : 0.01 (800 €)' - avec quantité et valeur
        - '- ETH : 0.5 (980.95 €)' - avec quantité et valeur décimale
        - '- Nano : 8253,10 €' - valeur directe sans quantité
        """
        # Détection fichier référencé
        file_ref = re.search(r'"(.+?\.(?:csv|pdf|json))"', line, re.IGNORECASE)
        if file_ref:
            filename = file_ref.group(1)
            if filename not in sources_files:
                sources_files.append(filename)
            return

        # Format 1: Symbole : quantité (valeur €)
        match_with_qty = re.match(r"-\s*(\w+)\s*:\s*([\d.]+)\s*\(([\d\s,.]+)\s*€\)", line)
        if match_with_qty:
            symbole = match_with_qty.group(1)
            quantite = float(match_with_qty.group(2))
            valeur = self._parse_amount(match_with_qty.group(3))

            actif = {
                "symbole": symbole,
                "quantite": quantite,
                "valeur": valeur
            }

            plateforme["actifs"].append(actif)
            plateforme["total"] += valeur
            return

        # Format 2: Symboles avec valeur € ou $ (ex: "BTC + ETH + VRO : 1780,95 €" ou "Pool : 1166,41 $")
        match_multi = re.match(r"-\s*([\w\s+()\-]+?)\s*:\s*([\d\s,.]+)\s*([€$])", line)
        if match_multi:
            symboles_str = match_multi.group(1).strip()
            valeur_str = match_multi.group(2)
            devise = match_multi.group(3)

            # Convertir $ en € (taux approximatif, devrait être dans config)
            valeur = self._parse_amount(valeur_str)
            if devise == "$":
                # Taux USD → EUR approximatif : 1 USD = 0.92 EUR (configurable)
                valeur = valeur * 0.92

            # Si contient "+", c'est un agrégat de plusieurs actifs
            if "+" in symboles_str:
                # Parser les symboles séparés par "+"
                symboles = [s.strip() for s in symboles_str.split("+")]
                # Créer un actif unique pour l'agrégat
                actif = {
                    "symbole": " + ".join(symboles),  # "BTC + ETH + VRO"
                    "quantite": valeur,
                    "valeur": valeur
                }
            else:
                # Un seul symbole (peut contenir parenthèses)
                actif = {
                    "symbole": symboles_str,
                    "quantite": valeur,
                    "valeur": valeur
                }

            plateforme["actifs"].append(actif)
            plateforme["total"] += valeur

    def _parse_metaux_line(self, line: str, metaux_data: dict, plateforme: str = None):
        """
        Parse une ligne métaux précieux
        Args:
            line: La ligne à parser (ex: "- Or : 3 355,69 €")
            metaux_data: Le dictionnaire métaux_precieux
            plateforme: Nom de la plateforme (ex: "Veracash")
        """
        # Ex: "- Or : 3 355,69 €"
        match = re.match(r"-\s*(.+?)\s*:\s*([\d\s,.]+)\s*€", line)
        if match:
            type_metal = match.group(1).strip()
            valeur = self._parse_amount(match.group(2))

            # Initialiser la structure si nécessaire
            if "metaux" not in metaux_data:
                metaux_data["metaux"] = []

            # Set plateforme if provided
            if plateforme and "plateforme" not in metaux_data:
                metaux_data["plateforme"] = plateforme

            metaux_data["metaux"].append({
                "type": type_metal,
                "valeur": valeur
            })
            metaux_data["total"] += valeur

            self.logger.debug(f"Métal ajouté: {type_metal} - {valeur:,.2f} € (plateforme: {plateforme})")

        # Détection plateforme explicite dans la ligne
        if "plateforme" in line.lower():
            match = re.search(r"plateforme\s*:\s*(.+)", line, re.IGNORECASE)
            if match:
                metaux_data["plateforme"] = match.group(1).strip()

    def _parse_immobilier_line(self, line_idx: int, lines: list, immobilier_data: dict):
        """
        Parse une section immobilier (section 3.1.4 du PRD)
        Format attendu:
        ### Détails
        - Studio :
          + Prix d'aquisition : 110 000 € (hors frais de notaire)
          + Lieu : 34, rue Salvador Allende 92000 Nanterre France
          + Surface : 25 m²
          + Prix m² : 5254 € (En octobre 2025)
        """
        # Charger le fichier immobilier_valorisation.json pour enrichissement
        valorisation_path = Path(self.config["paths"]["sources"]) / "immobilier_valorisation.json"
        valorisation_data = None

        if valorisation_path.exists():
            try:
                with open(valorisation_path, 'r', encoding='utf-8') as f:
                    valorisation_data = json.load(f)
                    self.logger.debug(f"Chargé immobilier_valorisation.json : {len(valorisation_data.get('biens', []))} biens")
            except Exception as e:
                self.logger.warning(f"Erreur chargement immobilier_valorisation.json: {e}")

        # Initialiser la liste biens si nécessaire
        if "biens" not in immobilier_data:
            immobilier_data["biens"] = []

        # Parser les lignes suivantes pour extraire les détails
        bien = {}
        i = line_idx + 1
        current_type = None

        while i < len(lines):
            next_line = lines[i].strip()

            # Arrêter si on atteint une nouvelle section
            if next_line.startswith("##") or next_line.startswith("###"):
                break

            # Détecter le type de bien (ex: "- Studio :")
            type_match = re.match(r"- (.+?)\s*:", next_line)
            if type_match:
                current_type = type_match.group(1).strip()
                bien["type"] = current_type
                i += 1
                continue

            # Parser les sous-détails (lignes commençant par +)
            if next_line.startswith("+ ") or next_line.startswith("  + "):
                # Prix d'acquisition
                prix_match = re.search(r"Prix d[''`]aquisition\s*:\s*([\d\s,.]+)\s*€", next_line, re.IGNORECASE)
                if prix_match:
                    bien["prix_acquisition"] = self._parse_amount(prix_match.group(1))

                # Lieu/Adresse
                lieu_match = re.search(r"Lieu\s*:\s*(.+?)(?:\(|$)", next_line, re.IGNORECASE)
                if lieu_match:
                    bien["adresse"] = lieu_match.group(1).strip()

                # Surface
                surface_match = re.search(r"Surface\s*:\s*([\d\s,.]+)\s*m", next_line, re.IGNORECASE)
                if surface_match:
                    bien["surface_m2"] = self._parse_amount(surface_match.group(1))

                # Prix au m²
                prix_m2_match = re.search(r"Prix m²\s*:\s*([\d\s,.]+)\s*€", next_line, re.IGNORECASE)
                if prix_m2_match:
                    prix_m2 = self._parse_amount(prix_m2_match.group(1))
                    # Calculer la valeur actuelle si on a surface et prix au m²
                    if "surface_m2" in bien:
                        bien["valeur_actuelle"] = round(bien["surface_m2"] * prix_m2, 2)

            i += 1

        # Enrichir avec les données de valorisation si disponibles
        if valorisation_data and bien:
            for valorisation_bien in valorisation_data.get("biens", []):
                # Matcher par type et adresse
                if (valorisation_bien.get("type", "").lower() == bien.get("type", "").lower() or
                    (bien.get("adresse", "") and valorisation_bien.get("adresse", "") and
                     "nanterre" in bien.get("adresse", "").lower() and
                     "nanterre" in valorisation_bien.get("adresse", "").lower())):

                    # Enrichir avec les données de valorisation
                    if "valeur_actuelle" not in bien and "valorisation_actuelle" in valorisation_bien:
                        valeur_estimee = valorisation_bien["valorisation_actuelle"].get("valeur_estimee_moyenne")
                        if valeur_estimee:
                            bien["valeur_actuelle"] = valeur_estimee

                    # Ajouter les sources de valorisation
                    if "valorisation_actuelle" in valorisation_bien:
                        bien["valorisation_sources"] = valorisation_bien["valorisation_actuelle"].get("sources", [])

                    self.logger.debug(f"Enrichissement bien immobilier avec valorisation_json")
                    break

        # Si on a collecté des données, ajouter le bien
        if bien and "type" in bien:
            # Calculer valeur actuelle si manquante mais qu'on a prix acquisition
            if "valeur_actuelle" not in bien and "prix_acquisition" in bien:
                bien["valeur_actuelle"] = bien["prix_acquisition"]
                self.logger.warning(f"Pas de valorisation actuelle pour {bien['type']}, utilisation prix acquisition")

            immobilier_data["biens"].append(bien)
            self.logger.debug(f"Bien immobilier ajouté: {bien.get('type')} - {bien.get('valeur_actuelle', 0):,.0f} €")

    def _parse_amount(self, amount_str: str) -> float:
        """
        Convertit une chaîne de montant en float
        Ex: '12 345,67 €' -> 12345.67
        """
        if not amount_str:
            return 0.0

        # Convertir en string au cas où
        amount_str = str(amount_str)

        # Enlever espaces et symboles monétaires
        amount_str = amount_str.replace(" ", "").replace("\xa0", "").replace("€", "").replace("$", "")
        # Remplacer virgule par point
        amount_str = amount_str.replace(",", ".")

        # Enlever tout ce qui n'est pas un chiffre, un point ou un signe négatif
        amount_str = ''.join(c for c in amount_str if c.isdigit() or c in '.-')

        try:
            return float(amount_str) if amount_str else 0.0
        except ValueError:
            self.logger.warning(f"Impossible de parser le montant : {amount_str}")
            return 0.0

    def _load_source_files(self, data: dict):
        """
        Charge les fichiers sources référencés (CSV, PDF, JSON)
        Enrichit les données avec le contenu des fichiers
        """
        sources_dir = Path(self.config["paths"]["sources"])

        for filename in data["sources_files"]:
            filepath = sources_dir / filename

            if not filepath.exists():
                self.logger.warning(f"Fichier source introuvable : {filepath}")
                continue

            self.logger.info(f"Chargement {filename}...")

            try:
                # Déterminer le type de fichier
                if filename.lower().endswith(".csv"):
                    self._load_csv_file(filepath, filename, data)
                elif filename.lower().endswith(".pdf"):
                    self._load_pdf_file(filepath, filename, data)
                elif filename.lower().endswith(".json"):
                    self._load_json_file(filepath, filename, data)
                else:
                    self.logger.warning(f"Type de fichier non supporté : {filename}")

            except Exception as e:
                self.logger.error(f"Erreur chargement {filename}: {e}")

    def _load_csv_file(self, filepath: Path, filename: str, data: dict):
        """Charge un fichier CSV et enrichit les données"""
        df = self.file_parser.parse_csv(str(filepath))

        # Trouver le compte correspondant
        compte = self._find_compte_by_source(data, filename)
        if compte is None:
            self.logger.warning(f"Aucun compte trouvé pour {filename}")
            return

        # Ajouter les positions
        if "positions" not in compte:
            compte["positions"] = []

        for _, row in df.iterrows():
            position = {}
            if "ticker" in row:
                position["ticker"] = str(row["ticker"])
            if "quantite" in row and pd.notna(row["quantite"]):
                position["quantite"] = float(row["quantite"])
            if "prix" in row and pd.notna(row["prix"]):
                position["prix"] = float(row["prix"])
            if "valeur" in row and pd.notna(row["valeur"]):
                position["valeur"] = float(row["valeur"])

            if position:
                compte["positions"].append(position)

        compte["source_file"] = filename
        self.logger.debug(f"  → {len(df)} positions chargées")

    def _load_pdf_file(self, filepath: Path, filename: str, data: dict):
        """Charge un fichier PDF et enrichit les données"""
        pdf_data = self.file_parser.parse_pdf(str(filepath))

        # Trouver le compte correspondant
        compte = self._find_compte_by_source(data, filename)
        if compte is None:
            self.logger.warning(f"Aucun compte trouvé pour {filename}")
            return

        compte["source_file"] = filename
        compte["pdf_type"] = pdf_data.get("detected_type")

        # Traiter les tables selon le type détecté
        if pdf_data["detected_type"] == "Assurance-vie":
            self._parse_av_tables(pdf_data["tables"], compte)
        elif pdf_data["detected_type"] == "CTO":
            self._parse_cto_tables(pdf_data["tables"], compte)
        elif pdf_data["detected_type"] in ["PEA", "PEA-PME"]:
            self._parse_pea_tables(pdf_data["tables"], pdf_data["text"], compte)

        self.logger.debug(f"  → PDF traité (type: {pdf_data.get('detected_type')})")

    def _load_json_file(self, filepath: Path, filename: str, data: dict):
        """Charge un fichier JSON"""
        json_data = self.file_parser.parse_json(str(filepath))
        # TODO: Traiter selon la structure JSON
        self.logger.debug(f"  → JSON chargé")

    def _find_compte_by_source(self, data: dict, filename: str) -> dict:
        """Trouve un compte par son fichier source"""
        # Chercher dans les établissements financiers
        for etab in data["patrimoine"]["financier"]["etablissements"]:
            if etab["code"] not in filename:
                continue

            # Chercher le meilleur match (le plus spécifique)
            # Important: tester les patterns les plus spécifiques en premier
            for compte in etab.get("comptes", []):
                compte_type = compte.get("type", "")

                # PEA-PME (plus spécifique, tester en premier)
                if "PEA-PME" in filename and "PEA-PME" in compte_type:
                    return compte

            # Si aucun match spécifique, tester les patterns génériques
            for compte in etab.get("comptes", []):
                compte_type = compte.get("type", "")

                # PEA (générique, mais exclure PEA-PME)
                if "PEA" in filename and "PEA" in compte_type and "PEA-PME" not in compte_type and "PEA-PME" not in filename:
                    return compte
                elif "AV" in filename and "Assurance" in compte_type:
                    return compte
                elif "CTO" in filename and "CTO" in compte_type:
                    return compte
                elif "PER" in filename and "PER" in compte_type:
                    return compte

        # Chercher dans les plateformes crypto
        for plat in data["patrimoine"]["crypto"]["plateformes"]:
            if plat["nom"].upper() in filename.upper():
                return plat

        return None

    def _parse_av_tables(self, tables: list, compte: dict):
        """
        Parse les tables d'une assurance-vie
        Format attendu : chaque fonds est une table de 2 lignes
        - Ligne 0 : [Nom du fonds, "Valorisation : XXX €"]
        - Ligne 1 : [Répartition, Plus-values]
        """
        if "fonds" not in compte:
            compte["fonds"] = []

        for table_info in tables:
            table = table_info["data"]

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
                        compte["fonds"].append({
                            "nom": nom_fonds,
                            "montant": valeur
                        })
                        self.logger.debug(f"    Fonds AV: {nom_fonds} = {valeur:,.2f} €")

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
                            compte["fonds"].append({
                                "nom": nom_fonds,
                                "montant": valeur
                            })
                            self.logger.debug(f"    Fonds AV: {nom_fonds} = {valeur:,.2f} €")

    def _parse_cto_tables(self, tables: list, compte: dict):
        """Parse les tables d'un CTO"""
        if "positions" not in compte:
            compte["positions"] = []

        # Logique similaire à parse_av_tables mais pour positions
        # TODO: Implémenter selon structure réelle des PDFs CTO

    def _extract_solde_especes(self, text: str) -> float:
        """
        Extrait le solde espèces depuis le texte du PDF PEA/PEA-PME

        Le solde espèces est extrait depuis la ligne de valorisation totale:
        Format: "X € = Y € + Z € = ..." où Z est le solde espèces
        Ex: "6 133,22 € = 970,14 € + 5 163,08 € = 0,00 % + 11,51 €"
            -> solde espèces = 5 163,08 €

        Note: Le "Solde disponible" affiché séparément peut être différent
        (opérations en cours), c'est pourquoi on utilise la ligne de valorisation.
        """
        if not text:
            return 0.0

        # Chercher la ligne avec "Ma valorisation totale" suivie de la formule
        # Format: montant1 € = montant2 € + montant3 € = ...
        # Le montant3 est le solde espèces
        lines = text.split('\n')
        for i, line in enumerate(lines):
            # Si on trouve "Ma valorisation totale", regarder la ligne suivante
            if 'ma valorisation' in line.lower():
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

    def _parse_pea_tables(self, tables: list, text: str, compte: dict):
        """
        Parse les tables d'un PEA ou PEA-PME
        Format Crédit Agricole web :
        - Ligne d'en-tête : [Valeur, Quantité, Cours, Variation (1J), Prix de revient, Valorisation, +/- Value latente, Variation (1er Janv)]
        - Lignes de données :
          - Colonne 2 : "NOM ACTION\nISIN CODE"
          - Colonne 3 : Quantité
          - Colonne 4 : Cours
          - Colonne 7 : Valorisation

        Note: Les tables multi-pages ne répètent pas l'en-tête sur chaque page.

        Extrait aussi le solde espèces depuis le texte du PDF.
        """
        if "positions" not in compte:
            compte["positions"] = []

        # Extraire le solde espèces du texte
        solde_especes = self._extract_solde_especes(text)
        if solde_especes > 0:
            compte["solde_especes"] = solde_especes
            self.logger.debug(f"    Solde espèces: {solde_especes:,.2f} €")

        # Variable pour savoir si on a déjà trouvé l'en-tête
        header_found = False

        for table_info in tables:
            table = table_info["data"]

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
                # Page 1 (offset=2) : [None, None, Valeur, Quantité, Cours, Variation, Prix_rev, Valorisation, ...]
                #                      [0,    1,    2,      3,        4,     5,         6,         7]
                # Page 2 (offset=0) : [Valeur, Quantité, Cours, Variation, Prix_rev, None, Valorisation, ...]
                #                      [0,      1,        2,     3,         4,         5,    6]
                valeur_cell = str(row[offset + 0]) if len(row) > offset and row[offset] else ""
                quantite_cell = str(row[offset + 1]) if len(row) > offset + 1 and row[offset + 1] else ""
                cours_cell = str(row[offset + 2]) if len(row) > offset + 2 and row[offset + 2] else ""
                prix_revient_cell = str(row[offset + 4]) if len(row) > offset + 4 and row[offset + 4] else ""
                # Valorisation: colonne 7 avec offset=2 (page 1), colonne 6 avec offset=0 (page 2)
                valorisation_idx = 7 if offset == 2 else 6
                valorisation_cell = str(row[valorisation_idx]) if len(row) > valorisation_idx and row[valorisation_idx] else ""

                # Ignorer les lignes vides
                if not valeur_cell or len(valeur_cell) < 5:
                    continue

                # Extraire nom et ISIN (format: "NOM\nISIN CODE")
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
                    compte["positions"].append(position)
                    self.logger.debug(f"    Position PEA: {nom} ({isin}) = {valorisation:,.2f} €")

    def _calculate_totals(self, data: dict):
        """
        Calcule les totaux récursifs pour toutes les catégories
        Section 3.1.5 - point 3 du PRD
        """
        # Totaux par établissement
        for etab in data["patrimoine"]["financier"]["etablissements"]:
            total_etab = 0
            for compte in etab.get("comptes", []):
                # Recalculer montant si positions détaillées
                if "positions" in compte and compte["positions"]:
                    total_positions = sum(p.get("valeur", 0) for p in compte["positions"])
                    # Ajouter le solde espèces (PEA/PEA-PME)
                    solde_especes = compte.get("solde_especes", 0)
                    if total_positions > 0 or solde_especes > 0:
                        compte["montant"] = total_positions + solde_especes

                total_etab += compte.get("montant", 0)

            etab["total"] = total_etab

        # Total financier
        total_financier = sum(e.get("total", 0) for e in data["patrimoine"]["financier"]["etablissements"])
        data["patrimoine"]["financier"]["total"] = total_financier

        # Totaux crypto
        for plat in data["patrimoine"]["crypto"]["plateformes"]:
            total_plat = sum(a.get("valeur", 0) for a in plat.get("actifs", []))
            plat["total"] = total_plat

        total_crypto = sum(p.get("total", 0) for p in data["patrimoine"]["crypto"]["plateformes"])
        data["patrimoine"]["crypto"]["total"] = total_crypto

        # Total métaux précieux (déjà calculé dans le parsing)
        # Total immobilier
        if "biens" in data["patrimoine"]["immobilier"]:
            total_immo = sum(b.get("valeur_actuelle", 0) for b in data["patrimoine"]["immobilier"]["biens"])
            data["patrimoine"]["immobilier"]["total"] = total_immo

        self.logger.debug(f"Totaux calculés - Financier: {total_financier:,.0f} €, Crypto: {total_crypto:,.0f} €")
    
    def _validate(self, data: dict):
        """
        Valide la cohérence des données
        Section 3.1.5 - point 4 du PRD
        """
        errors = []
        warnings = []

        # Validation profil
        if not data.get("profil"):
            warnings.append("Profil vide ou incomplet")

        # Validation fichiers sources
        sources_dir = Path(self.config["paths"]["sources"])
        for filename in data.get("sources_files", []):
            filepath = sources_dir / filename
            if not filepath.exists():
                errors.append(f"Fichier source manquant : {filename}")

        # Validation totaux
        financier_total = data["patrimoine"]["financier"]["total"]
        sum_etab = sum(e.get("total", 0) for e in data["patrimoine"]["financier"]["etablissements"])

        if abs(financier_total - sum_etab) > 0.01:  # Tolérance pour erreurs d'arrondi
            warnings.append(f"Incohérence total financier : {financier_total} vs {sum_etab}")

        # Validation montants positifs
        if financier_total < 0:
            errors.append("Total financier négatif")

        # Affichage résultats
        if errors:
            for error in errors:
                self.logger.error(f"  ✗ {error}")
            raise ValueError(f"Validation échouée : {len(errors)} erreur(s)")

        if warnings:
            for warning in warnings:
                self.logger.warning(f"  ⚠ {warning}")

        self.logger.info(f"✓ Validation OK ({len(warnings)} avertissement(s))")
    
    def _save_json(self, data: dict, output_path: Path):
        """Sauvegarde le JSON normalisé"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
