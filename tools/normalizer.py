"""
Module de normalisation des fichiers sources (v2.1)
Architecture manifest-driven avec parsers pluggables et sections manuelles
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import glob
import re
import fnmatch

# Import du registry de parsers
from tools.parsers.registry import ParserRegistry
from tools.parsers.base_parser import ParsingError

# Import du gestionnaire de cache
from tools.cache_manager import CacheManager

# Import de l'API de prix crypto
from tools.crypto_price_api import CryptoPriceAPI

# Import des parsers concrets (pour auto-register)
from tools.parsers.credit_agricole import CreditAgricolePEA2025Parser, CreditAgricoleAV2LignesParser
from tools.parsers.generic import GenericCSVParser
from tools.parsers.bitstack import BitstackTransactionHistoryParser


class PatrimoineNormalizer:
    """Normalise les fichiers sources en JSON structuré (v2.1 - manifest-driven avec sections manuelles)"""

    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialiser le registry et enregistrer les parsers
        self.parser_registry = ParserRegistry()
        self._register_parsers()

        # Initialiser le gestionnaire de cache
        self.cache_manager = CacheManager(
            cache_dir=str(Path(self.config["paths"]["generated"]) / "cache")
        )

        # Initialiser l'API de prix crypto
        self.crypto_api = CryptoPriceAPI()

    def _register_parsers(self):
        """Enregistre tous les parsers disponibles"""
        self.parser_registry.register(CreditAgricolePEA2025Parser)
        self.parser_registry.register(CreditAgricoleAV2LignesParser)
        self.parser_registry.register(GenericCSVParser)
        self.parser_registry.register(BitstackTransactionHistoryParser)

        self.logger.info(f"Parsers enregistrés : {', '.join(self.parser_registry.list_parsers())}")

    def normalize(self) -> dict:
        """Point d'entrée principal de normalisation (v2.1)"""
        self.logger.info("Début normalisation (v2.1 - manifest-driven avec sections manuelles)...")

        # 1. Charger manifest.json
        self.logger.info("Lecture manifest.json...")
        manifest = self._load_manifest()

        # 2. Valider manifest
        self.logger.info("Validation manifest...")
        self._validate_manifest(manifest)

        # 3. Extraire profil investisseur
        profil = manifest.get("profil_investisseur", {})

        # 4. Parser chaque compte titres via stratégie appropriée
        comptes_titres = manifest.get("patrimoine", {}).get("comptes_titres", [])
        self.logger.info(f"Parsing {len(comptes_titres)} comptes titres...")
        comptes_parsed = self._parse_all_comptes(comptes_titres)

        # 5. Enrichir avec métadonnées établissements
        self.logger.info("Enrichissement métadonnées établissements...")
        self._enrich_etablissements_metadata(comptes_parsed)

        # 6. Construire JSON normalisé (intègre sections manuelles)
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
        """Valide la structure du manifest (v2.1)"""
        errors = []

        # Version
        version = manifest.get("version")
        if version not in ["2.1.0", "2.0.0"]:  # Support legacy 2.0.0 temporairement
            errors.append(f"Version manifest invalide : {version} (attendue: 2.1.0)")

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

        # Section patrimoine requise (v2.1)
        if "patrimoine" not in manifest:
            errors.append("Section patrimoine manquante (v2.1)")
        else:
            patrimoine = manifest["patrimoine"]

            # Au moins un type d'actif
            asset_sections = ["comptes_titres", "liquidites", "crypto", "metaux_precieux", "immobilier", "obligations"]
            has_assets = any(patrimoine.get(section) for section in asset_sections)
            if not has_assets:
                errors.append("Aucun actif défini dans patrimoine (au moins une section requise)")

            # Structure des comptes titres (si présents)
            for i, compte in enumerate(patrimoine.get("comptes_titres", [])):
                required_fields = ["id", "custodian", "type_compte", "parser_strategy"]
                for field in required_fields:
                    if field not in compte:
                        errors.append(f"Compte titres #{i}: champ '{field}' manquant")

                # Vérifier qu'il y a soit source_file soit source_pattern
                if "source_file" not in compte and "source_pattern" not in compte:
                    errors.append(f"Compte titres #{i}: 'source_file' ou 'source_pattern' requis")

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
                # Support pour source_pattern (multi-fichiers) ou source_file (fichier unique)
                if "source_pattern" in compte_def:
                    # Mode pattern: parser plusieurs fichiers (ex: [BIT] - *.csv)
                    parsed = self._parse_compte_multi_files(compte_def, sources_dir)
                else:
                    # Mode fichier unique (comportement legacy)
                    filepath = sources_dir / compte_def["source_file"]

                    if not filepath.exists():
                        self.logger.error(f"    ✗ Fichier introuvable : {filepath}")
                        continue

                    parsed = self._parse_compte_with_strategy(compte_def, filepath)

                # Enrichir avec métadonnées du manifest (v2.1: custodian)
                parsed["compte_id"] = compte_id
                parsed["etablissement_code"] = compte_def.get("custodian", compte_def.get("etablissement"))  # Support legacy
                parsed["custodian_name"] = compte_def.get("custodian_name", "")
                parsed["source_file"] = compte_def.get("source_file", compte_def.get("source_pattern", ""))

                comptes_parsed.append(parsed)
                self.logger.info(f"    ✓ {len(parsed.get('positions', parsed.get('fonds', [])))} éléments parsés")

            except Exception as e:
                self.logger.error(f"    ✗ Échec parsing {compte_id}: {e}")

        return comptes_parsed

    def _parse_compte_multi_files(self, compte_def: dict, sources_dir: Path) -> dict:
        """
        Parse un compte depuis plusieurs fichiers (pattern).

        Support du cache pour les années passées.

        Args:
            compte_def: Définition du compte avec 'source_pattern'
            sources_dir: Répertoire des fichiers sources

        Returns:
            Données parsées consolidées
        """
        pattern = compte_def["source_pattern"]
        custodian = compte_def.get("custodian", "")
        use_cache = compte_def.get("cache_historical_years", False)

        # Trouver tous les fichiers correspondant au pattern
        # Support des sous-répertoires (ex: Bitstack/[BIT] - *.csv)
        if "/" in pattern:
            base_dir = sources_dir / Path(pattern).parent
            file_pattern = Path(pattern).name
        else:
            base_dir = sources_dir
            file_pattern = pattern

        # Matcher les fichiers (fnmatch/glob ont des problèmes avec [] littéraux dans les noms)
        all_files = list(base_dir.iterdir()) if base_dir.exists() else []
        matching_files = sorted([f for f in all_files if f.is_file() and self._matches_pattern(f.name, file_pattern)])

        if not matching_files:
            raise FileNotFoundError(f"Aucun fichier trouvé pour le pattern: {pattern}")

        self.logger.info(f"    Trouvé {len(matching_files)} fichier(s) pour {pattern}")

        all_positions = []

        for filepath in matching_files:
            file_name = filepath.name

            # Déterminer si ce fichier doit être caché
            cache_key = None
            if use_cache:
                cache_key = self.cache_manager.get_cache_key(custodian, file_name)

                # Extraire l'année pour vérifier si on doit cacher
                year_match = re.search(r'(\d{4})', file_name)
                if year_match:
                    year = int(year_match.group(1))
                    should_cache = self.cache_manager.should_cache_year(year)

                    if should_cache and self.cache_manager.is_cached(cache_key, str(filepath)):
                        # Charger depuis le cache
                        cached = self.cache_manager.load_from_cache(cache_key)
                        if cached:
                            positions = cached['data']
                            all_positions.extend(positions)
                            self.logger.info(f"      ✓ {file_name} (depuis cache)")
                            continue

            # Parser le fichier
            self.logger.info(f"      Parsing {file_name}...")
            parsed = self._parse_compte_with_strategy(compte_def, filepath)
            positions = parsed.get('positions', parsed.get('fonds', []))
            all_positions.extend(positions)

            # Sauvegarder dans le cache si applicable
            if cache_key and use_cache:
                year_match = re.search(r'(\d{4})', file_name)
                if year_match:
                    year = int(year_match.group(1))
                    if self.cache_manager.should_cache_year(year):
                        self.cache_manager.save_to_cache(
                            cache_key,
                            str(filepath),
                            positions,
                            metadata={'year': year, 'custodian': custodian}
                        )

        # Consolider les résultats
        return {
            'positions': all_positions,
            'type_compte': compte_def.get('type_compte', compte_def.get('type_actif', 'Crypto'))
        }

    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """
        Vérifie si un nom de fichier correspond au pattern.

        Gère les cas particuliers comme [BIT] qui sont des caractères littéraux,
        pas des patterns de matching.

        Args:
            filename: Nom du fichier
            pattern: Pattern (ex: "[BIT] - *.csv")

        Returns:
            True si le fichier match
        """
        # Convertir le pattern en regex-like pour gérer les cas spéciaux
        # Remplacer * par .* mais préserver les [] littéraux
        import re as regex_module

        # Échapper tous les caractères spéciaux sauf *
        escaped = regex_module.escape(pattern)
        # Remplacer \* (échappé) par .* (wildcard regex)
        regex_pattern = escaped.replace(r'\*', '.*')

        # Compiler et matcher
        return regex_module.fullmatch(regex_pattern, filename) is not None

    def _parse_compte_with_strategy(self, compte_def: dict, filepath: Path) -> dict:
        """Parse un compte avec la stratégie définie ou fallback"""
        strategy_name = compte_def["parser_strategy"]
        fallback_strategies = compte_def.get("fallback_parsers", [])
        metadata = compte_def.get("metadata", {})

        # Ajouter métadonnées supplémentaires (v2.1: custodian)
        metadata["etablissement"] = compte_def.get("custodian", compte_def.get("etablissement"))  # Support legacy
        metadata["type_compte"] = compte_def.get("type_compte", compte_def.get("type_actif", "Crypto"))

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
        """Construit le JSON normalisé final (v2.1 avec sections manuelles)"""
        data = {
            "meta": {
                "version": "2.1.0",
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

        # 1. Grouper les comptes titres parsés par établissement
        etablissements_dict = self._group_comptes_titres(comptes_parsed, data)

        # 2. Intégrer les liquidités manuelles dans les établissements existants
        self._integrate_liquidites(manifest, etablissements_dict, data)

        # 3. Intégrer les obligations manuelles
        self._integrate_obligations(manifest, etablissements_dict, data)

        # 4. Intégrer les cryptomonnaies (dans patrimoine.crypto uniquement, pas dans établissements)
        self._integrate_crypto(manifest, data)

        # 5. Intégrer les métaux précieux (dans patrimoine.metaux_precieux uniquement, pas dans établissements)
        self._integrate_metaux_precieux(manifest, data)

        # 6. Intégrer l'immobilier
        self._integrate_immobilier(manifest, data)

        # Finaliser: ajouter établissements au patrimoine
        data["patrimoine"]["financier"]["etablissements"] = list(etablissements_dict.values())

        return data

    def _group_comptes_titres(self, comptes_parsed: List[dict], data: dict) -> dict:
        """Groupe les comptes titres parsés par établissement"""
        etablissements_dict = {}

        for compte in comptes_parsed:
            etab_code = compte.get("etablissement_code", "unknown")

            if etab_code not in etablissements_dict:
                etablissements_dict[etab_code] = {
                    "nom": compte.get("custodian_name", etab_code),
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

        return etablissements_dict

    def _integrate_liquidites(self, manifest: dict, etablissements_dict: dict, data: dict):
        """Intègre les liquidités manuelles du manifest"""
        liquidites = manifest.get("patrimoine", {}).get("liquidites", [])

        for liq in liquidites:
            custodian = liq.get("custodian", "")
            montant = liq.get("montant", 0)
            type_compte = liq.get("type_compte", "Liquidité")

            # Créer ou enrichir l'établissement
            if custodian not in etablissements_dict:
                etablissements_dict[custodian] = self._create_etablissement_entry(liq)

            # Ajouter le compte de liquidité
            etablissements_dict[custodian]["comptes"].append({
                "type": type_compte,
                "montant": montant
            })
            etablissements_dict[custodian]["total"] += montant

    def _integrate_obligations(self, manifest: dict, etablissements_dict: dict, data: dict):
        """Intègre les obligations manuelles du manifest"""
        obligations = manifest.get("patrimoine", {}).get("obligations", [])

        for oblig in obligations:
            custodian = oblig.get("custodian", "")
            type_actif = oblig.get("type_actif", "Obligations")

            # Créer ou enrichir l'établissement
            if custodian not in etablissements_dict:
                etablissements_dict[custodian] = self._create_etablissement_entry(oblig)

            # Traiter chaque compte (multi-devises)
            for compte in oblig.get("comptes", []):
                currency = compte.get("currency", "EUR")
                montant = compte.get("montant_eur_equivalent", compte.get("montant", 0))

                etablissements_dict[custodian]["comptes"].append({
                    "type": f"{type_actif} ({currency})",
                    "montant": montant
                })
                etablissements_dict[custodian]["total"] += montant

    def _integrate_crypto(self, manifest: dict, data: dict):
        """Intègre les cryptomonnaies du manifest (dans patrimoine.crypto uniquement)"""
        cryptos = manifest.get("patrimoine", {}).get("crypto", [])
        sources_dir = Path(self.config["paths"]["sources"])

        for crypto in cryptos:
            metadata = crypto.get("metadata", {})
            montant = 0

            # Si source_pattern ou source_file est présent, parser les fichiers
            if "source_pattern" in crypto or "source_file" in crypto:
                self.logger.info(f"  Parsing crypto {crypto['id']}...")
                try:
                    # Parser le(s) fichier(s)
                    if "source_pattern" in crypto:
                        parsed = self._parse_compte_multi_files(crypto, sources_dir)
                    else:
                        filepath = sources_dir / crypto["source_file"]
                        if not filepath.exists():
                            self.logger.error(f"    ✗ Fichier introuvable : {filepath}")
                            continue
                        parsed = self._parse_compte_with_strategy(crypto, filepath)

                    # Calculer le montant total depuis les positions
                    positions = parsed.get('positions', parsed.get('fonds', []))
                    for pos in positions:
                        # Pour crypto en BTC, on doit convertir en EUR
                        if pos.get('devise') == 'BTC':
                            btc_qty = pos.get('quantite', 0)
                            eur_value = self.crypto_api.convert_btc_to_eur(btc_qty)

                            if eur_value is not None:
                                montant += eur_value
                                self.logger.info(f"    ✓ {btc_qty} BTC converti en {eur_value:.2f} EUR")
                            else:
                                self.logger.warning(f"    ⚠️  Impossible de convertir {btc_qty} BTC en EUR (API indisponible)")
                                montant += 0
                        else:
                            montant += pos.get('valeur_totale', 0)

                    self.logger.info(f"    ✓ {len(positions)} position(s) parsée(s), montant: {montant} EUR")

                except Exception as e:
                    self.logger.error(f"    ✗ Échec parsing {crypto['id']}: {e}")
                    # Fallback sur montant manuel si présent
                    montant = crypto.get("montant_eur_equivalent", crypto.get("montant", 0))
            else:
                # Pas de fichier source, utiliser le montant manuel
                montant = crypto.get("montant_eur_equivalent", crypto.get("montant", 0))

            plateforme_entry = {
                "nom": crypto.get("custodian_name", crypto.get("custodian", "Inconnu")),
                "code": crypto.get("custodian", "unknown"),
                "type": crypto.get("type_actif", "Crypto"),
                "custody_type": crypto.get("custody_type", "custodial_platform"),
                "total": montant,
                "juridiction": metadata.get("juridiction", "Inconnue"),  # Pour l'analyzer
                "juridiction_pays": metadata.get("juridiction_pays", "N/A")
            }

            data["patrimoine"]["crypto"]["plateformes"].append(plateforme_entry)

    def _integrate_metaux_precieux(self, manifest: dict, data: dict):
        """Intègre les métaux précieux du manifest (dans patrimoine.metaux_precieux uniquement)"""
        metaux = manifest.get("patrimoine", {}).get("metaux_precieux", [])

        if not metaux:
            return

        # Regrouper par custodian
        custodians_dict = {}
        for metal in metaux:
            custodian = metal.get("custodian", "unknown")
            if custodian not in custodians_dict:
                metadata = metal.get("metadata", {})
                custodians_dict[custodian] = {
                    "custodian_name": metal.get("custodian_name", custodian),
                    "juridiction": metadata.get("juridiction", "France"),
                    "juridiction_pays": metadata.get("juridiction_pays", "France"),
                    "total": 0,
                    "details": []
                }

            custodians_dict[custodian]["total"] += metal.get("montant", 0)
            custodians_dict[custodian]["details"].append({
                "type": metal.get("type_actif", "Métal"),
                "montant": metal.get("montant", 0)
            })

        # Total général
        total_metaux = sum(c["total"] for c in custodians_dict.values())
        data["patrimoine"]["metaux_precieux"]["total"] = total_metaux

        # Si un seul custodian, utiliser ses infos au niveau racine (pour l'analyzer legacy)
        if len(custodians_dict) == 1:
            custodian_data = list(custodians_dict.values())[0]
            data["patrimoine"]["metaux_precieux"]["plateforme"] = custodian_data["custodian_name"]
            data["patrimoine"]["metaux_precieux"]["juridiction"] = custodian_data["juridiction"]
            data["patrimoine"]["metaux_precieux"]["juridiction_pays"] = custodian_data["juridiction_pays"]

        # Stocker détails par custodian
        data["patrimoine"]["metaux_precieux"]["custodians"] = [
            {
                "custodian": v["custodian_name"],
                "juridiction": v["juridiction"],
                "total": v["total"],
                "details": v["details"]
            }
            for v in custodians_dict.values()
        ]

    def _integrate_immobilier(self, manifest: dict, data: dict):
        """Intègre l'immobilier du manifest"""
        immobilier = manifest.get("patrimoine", {}).get("immobilier", [])

        for bien in immobilier:
            bien_entry = {
                "type": bien.get("type_bien", "Bien"),
                "adresse": bien.get("adresse", ""),
                "valeur_actuelle": bien.get("valeur_actuelle", bien.get("prix_acquisition", 0)),
                "surface": bien.get("surface_m2", 0),
                "metadata": bien.get("metadata", {})
            }
            data["patrimoine"]["immobilier"]["biens"].append(bien_entry)

    def _create_etablissement_entry(self, asset: dict) -> dict:
        """Crée une entrée établissement à partir d'un actif manuel"""
        metadata = asset.get("metadata", {})

        return {
            "nom": asset.get("custodian_name", asset.get("custodian", "Inconnu")),
            "code": asset.get("custodian", "unknown"),
            "juridiction": metadata.get("juridiction", "France"),  # Enrichi depuis metadata
            "juridiction_pays": metadata.get("juridiction_pays", "France"),
            "type_etablissement": asset.get("custody_type", "Plateforme"),
            "garantie_depots": metadata.get("garantie_depots", "N/A"),
            "exposition_sapin_2": metadata.get("exposition_sapin_2", "NON"),
            "exposition_risque_france": metadata.get("exposition_risque_france", "FAIBLE"),
            "total": 0,
            "comptes": []
        }

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
