"""
Module de normalisation des fichiers sources (v2.0)
Architecture manifest-driven avec parsers pluggables
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Import du registry de parsers
from tools.parsers.registry import ParserRegistry
from tools.parsers.base_parser import ParsingError

# Import des parsers concrets (pour auto-register)
from tools.parsers.credit_agricole import CreditAgricolePEA2025Parser, CreditAgricoleAV2LignesParser
from tools.parsers.generic import GenericCSVParser


class PatrimoineNormalizer:
    """Normalise les fichiers sources en JSON structuré (v2.0 - manifest-driven)"""

    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialiser le registry et enregistrer les parsers
        self.parser_registry = ParserRegistry()
        self._register_parsers()

    def _register_parsers(self):
        """Enregistre tous les parsers disponibles"""
        self.parser_registry.register(CreditAgricolePEA2025Parser)
        self.parser_registry.register(CreditAgricoleAV2LignesParser)
        self.parser_registry.register(GenericCSVParser)

        self.logger.info(f"Parsers enregistrés : {', '.join(self.parser_registry.list_parsers())}")

    def normalize(self) -> dict:
        """Point d'entrée principal de normalisation (v2.0)"""
        self.logger.info("Début normalisation (v2.0 - manifest-driven)...")

        # 1. Charger manifest.json
        self.logger.info("Lecture manifest.json...")
        manifest = self._load_manifest()

        # 2. Valider manifest
        self.logger.info("Validation manifest...")
        self._validate_manifest(manifest)

        # 3. Extraire profil investisseur
        profil = manifest.get("profil_investisseur", {})

        # 4. Parser chaque compte via stratégie appropriée
        self.logger.info(f"Parsing {len(manifest.get('comptes', []))} comptes...")
        comptes_parsed = self._parse_all_comptes(manifest["comptes"])

        # 5. Enrichir avec métadonnées établissements
        self.logger.info("Enrichissement métadonnées établissements...")
        self._enrich_etablissements_metadata(comptes_parsed)

        # 6. Construire JSON normalisé
        self.logger.info("Construction patrimoine_input.json...")
        data = self._build_normalized_json(profil, comptes_parsed, manifest)

        # 7. Calculer totaux
        self.logger.info("Calcul totaux par catégorie...")
        self._calculate_totals(data)

        # 8. Valider données finales
        self.logger.info("Validation données finales...")
        self._validate_normalized_data(data)

        # 9. Sauvegarder JSON
        output_path = Path(self.config["paths"]["generated"]) / self.config["normalizer"]["output_file"]
        self.logger.info(f"Sauvegarde {output_path}...")
        self._save_json(data, output_path)

        self.logger.info("✓ Normalisation terminée")
        return data

    def _load_manifest(self) -> dict:
        """Charge manifest.json"""
        manifest_path = Path(self.config["paths"]["sources"]) / self.config["normalizer"]["input_file"]

        if not manifest_path.exists():
            raise FileNotFoundError(
                f"Fichier manifest.json introuvable : {manifest_path}\n"
                f"Utilisez 'python tools/generate_manifest.py' pour le générer depuis patrimoine.md"
            )

        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        self.logger.info(f"Manifest chargé : version {manifest.get('version')}")
        return manifest

    def _validate_manifest(self, manifest: dict):
        """Valide la structure du manifest"""
        errors = []

        # Version
        if manifest.get("version") != "2.0.0":
            errors.append(f"Version manifest invalide : {manifest.get('version')} (attendue: 2.0.0)")

        # Profil investisseur requis
        if "profil_investisseur" not in manifest:
            errors.append("Section profil_investisseur manquante")
        else:
            profil = manifest["profil_investisseur"]

            # Sous-sections requises
            required_sections = ["identite", "professionnel", "investissement"]
            for section in required_sections:
                if section not in profil:
                    errors.append(f"Section profil_investisseur.{section} manquante")

            # profil_risque requis
            if "investissement" in profil:
                if "profil_risque" not in profil["investissement"]:
                    errors.append("profil_investisseur.investissement.profil_risque manquant")
                else:
                    profil_risque = profil["investissement"]["profil_risque"]
                    valid_profiles = ["dynamique", "equilibre", "prudent", "default"]
                    if profil_risque not in valid_profiles:
                        errors.append(f"profil_risque '{profil_risque}' invalide. Valeurs: {valid_profiles}")

        # Au moins un compte
        if not manifest.get("comptes"):
            errors.append("Aucun compte défini dans manifest.json")

        # Structure des comptes
        for i, compte in enumerate(manifest.get("comptes", [])):
            required_fields = ["id", "etablissement", "type_compte", "source_file", "parser_strategy"]
            for field in required_fields:
                if field not in compte:
                    errors.append(f"Compte #{i}: champ '{field}' manquant")

        if errors:
            for error in errors:
                self.logger.error(f"  ✗ {error}")
            raise ValueError(f"Validation manifest.json échouée : {len(errors)} erreur(s)")

        self.logger.info("✓ Manifest validé")

    def _parse_all_comptes(self, comptes_manifest: List[dict]) -> List[dict]:
        """Parse tous les comptes définis dans le manifest"""
        comptes_parsed = []
        sources_dir = Path(self.config["paths"]["sources"])

        for compte_def in comptes_manifest:
            compte_id = compte_def["id"]
            self.logger.info(f"  Parsing {compte_id}...")

            try:
                # Construire chemin fichier
                filepath = sources_dir / compte_def["source_file"]

                if not filepath.exists():
                    self.logger.error(f"    ✗ Fichier introuvable : {filepath}")
                    continue

                # Parser avec stratégie définie ou fallback
                parsed = self._parse_compte_with_strategy(compte_def, filepath)

                # Enrichir avec métadonnées du manifest
                parsed["compte_id"] = compte_id
                parsed["etablissement_code"] = compte_def["etablissement"]
                parsed["source_file"] = compte_def["source_file"]

                comptes_parsed.append(parsed)
                self.logger.info(f"    ✓ {len(parsed.get('positions', parsed.get('fonds', [])))} éléments parsés")

            except Exception as e:
                self.logger.error(f"    ✗ Échec parsing {compte_id}: {e}")

        return comptes_parsed

    def _parse_compte_with_strategy(self, compte_def: dict, filepath: Path) -> dict:
        """Parse un compte avec la stratégie définie ou fallback"""
        strategy_name = compte_def["parser_strategy"]
        fallback_strategies = compte_def.get("fallback_parsers", [])
        metadata = compte_def.get("metadata", {})

        # Ajouter métadonnées supplémentaires
        metadata["etablissement"] = compte_def["etablissement"]
        metadata["type_compte"] = compte_def["type_compte"]

        # Essayer stratégie principale + fallbacks
        all_strategies = [strategy_name] + fallback_strategies

        try:
            parsed_data = self.parser_registry.parse_with_fallback(
                str(filepath),
                metadata,
                all_strategies
            )
            return parsed_data

        except ParsingError as e:
            raise Exception(f"Tous les parsers ont échoué : {e}")

    def _enrich_etablissements_metadata(self, comptes_parsed: List[dict]):
        """Enrichit les comptes avec les métadonnées des établissements"""
        # Charger établissements_financiers.json
        metadata_path = Path(self.config["paths"]["sources"]) / "etablissements_financiers.json"

        if not metadata_path.exists():
            self.logger.warning(f"Fichier etablissements_financiers.json introuvable : {metadata_path}")
            return

        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                etablissements_meta = metadata.get("etablissements", {})

            # Enrichir chaque compte
            for compte in comptes_parsed:
                etab_code = compte.get("etablissement_code", "")

                if etab_code in etablissements_meta:
                    meta = etablissements_meta[etab_code]
                    compte["juridiction"] = meta.get("juridiction_principale", "France")
                    compte["juridiction_pays"] = meta.get("pays", "France")
                    compte["type_etablissement"] = meta.get("type", "Banque")
                    compte["garantie_depots"] = meta.get("garantie_depots", "N/A")
                    compte["exposition_sapin_2"] = meta.get("exposition_sapin_2", "NON")
                    compte["exposition_risque_france"] = meta.get("exposition_risque_france", "MOYENNE")

                    self.logger.debug(f"  Enrichi {compte['compte_id']}")

        except Exception as e:
            self.logger.error(f"Erreur lors de l'enrichissement des métadonnées : {e}")

    def _build_normalized_json(self, profil: dict, comptes_parsed: List[dict], manifest: dict) -> dict:
        """Construit le JSON normalisé final"""
        data = {
            "meta": {
                "version": "2.0.0",
                "generated_at": datetime.now().isoformat(),
                "source_manifest": self.config["normalizer"]["input_file"]
            },
            "profil": profil,
            "patrimoine": {
                "financier": {"total": 0, "etablissements": []},
                "crypto": {"total": 0, "plateformes": []},
                "metaux_precieux": {"total": 0},
                "immobilier": {"total": 0, "biens": []}
            },
            "sources_files": []
        }

        # Grouper les comptes par établissement
        etablissements_dict = {}

        for compte in comptes_parsed:
            etab_code = compte.get("etablissement_code", "unknown")

            if etab_code not in etablissements_dict:
                etablissements_dict[etab_code] = {
                    "nom": etab_code,
                    "code": etab_code,
                    "juridiction": compte.get("juridiction", "France"),
                    "juridiction_pays": compte.get("juridiction_pays", "France"),
                    "type_etablissement": compte.get("type_etablissement", "Banque"),
                    "garantie_depots": compte.get("garantie_depots", "N/A"),
                    "exposition_sapin_2": compte.get("exposition_sapin_2", "NON"),
                    "exposition_risque_france": compte.get("exposition_risque_france", "MOYENNE"),
                    "total": 0,
                    "comptes": []
                }

            # Ajouter compte à l'établissement
            compte_entry = {
                "type": compte.get("type", "Compte"),
                "montant": compte.get("montant", 0)
            }

            # Ajouter positions ou fonds si présents
            if "positions" in compte:
                compte_entry["positions"] = compte["positions"]
            if "fonds" in compte:
                compte_entry["fonds"] = compte["fonds"]
            if "solde_especes" in compte:
                compte_entry["solde_especes"] = compte["solde_especes"]
            if "source_file" in compte:
                compte_entry["source_file"] = compte["source_file"]
                if compte["source_file"] not in data["sources_files"]:
                    data["sources_files"].append(compte["source_file"])

            etablissements_dict[etab_code]["comptes"].append(compte_entry)
            etablissements_dict[etab_code]["total"] += compte.get("montant", 0)

        # Ajouter établissements au patrimoine
        data["patrimoine"]["financier"]["etablissements"] = list(etablissements_dict.values())

        return data

    def _calculate_totals(self, data: dict):
        """Calcule les totaux récursifs"""
        # Total financier
        total_financier = sum(e.get("total", 0) for e in data["patrimoine"]["financier"]["etablissements"])
        data["patrimoine"]["financier"]["total"] = total_financier

        # Total crypto
        total_crypto = sum(p.get("total", 0) for p in data["patrimoine"]["crypto"]["plateformes"])
        data["patrimoine"]["crypto"]["total"] = total_crypto

        # Total immobilier
        if "biens" in data["patrimoine"]["immobilier"]:
            total_immo = sum(b.get("valeur_actuelle", 0) for b in data["patrimoine"]["immobilier"]["biens"])
            data["patrimoine"]["immobilier"]["total"] = total_immo

        self.logger.debug(f"Totaux calculés - Financier: {total_financier:,.0f} €, Crypto: {total_crypto:,.0f} €")

    def _validate_normalized_data(self, data: dict):
        """Valide la cohérence des données normalisées"""
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
