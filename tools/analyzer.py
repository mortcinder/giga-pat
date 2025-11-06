"""
Module d'analyse du patrimoine
Suit les spécifications de la section 3.2 du PRD
"""

import json
import logging
import yaml
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
from tools.utils.web_research import WebResearcher
from tools.utils.risk_analyzer import RiskAnalyzer
from tools.utils.recommendations import Recommender
from tools.utils.stress_tester import StressTester
from tools.utils.portfolio_optimizer import PortfolioOptimizer
from tools.utils.benchmark_gap import BenchmarkGapCalculator


class PatrimoineAnalyzer:
    """
    Analyse approfondie du patrimoine avec recherches web
    Section 3.2 du PRD
    """

    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Charger la configuration d'analyse depuis YAML
        self._load_analysis_config()

        # Initialiser les outils d'analyse
        self.web_researcher = WebResearcher(config)
        self.risk_analyzer = RiskAnalyzer(config, self.web_researcher)
        self.recommender = Recommender(config)
        self.stress_tester = StressTester(config)
        self.portfolio_optimizer = PortfolioOptimizer(config)
        # benchmark_calculator déjà initialisé dans _load_analysis_config()

    def _load_analysis_config(self):
        """Charge la configuration d'analyse depuis le fichier YAML"""
        try:
            # Déterminer le chemin du fichier de configuration
            analysis_config = self.config.get("analysis", {})
            config_file = analysis_config.get("config_file", "analysis.yaml")

            # Construire le chemin absolu
            config_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "config",
            )
            config_path = os.path.join(config_dir, config_file)

            if not os.path.exists(config_path):
                self.logger.warning(
                    f"Fichier de configuration non trouvé: {config_path}. Utilisation des valeurs par défaut."
                )
                self._load_default_analysis_config()
                return

            # Charger le fichier YAML
            with open(config_path, "r", encoding="utf-8") as f:
                self.analysis_config = yaml.safe_load(f)

            # Extraire le profil actif
            self.active_profile = analysis_config.get("active_profile", "default")

            self.logger.info(f"Configuration d'analyse chargée depuis: {config_path}")
            self.logger.info(f"Profil actif: {self.active_profile}")

            # Initialiser le calculateur d'écart benchmark
            self.benchmark_calculator = BenchmarkGapCalculator(self.analysis_config, self.active_profile)

        except Exception as e:
            self.logger.error(f"Erreur lors du chargement de la configuration: {e}")
            self._load_default_analysis_config()

    def _load_default_analysis_config(self):
        """Charge une configuration par défaut minimale en cas d'erreur"""
        self.analysis_config = {
            "account_classification": {"keywords": {}, "mapping": {}, "special_institutions": {}, "fonds_euro_keywords": []},
            "risk_justifications": {},
            "benchmarks": {"default": {}},
            "scores": {}
        }
        self.active_profile = "default"
        # Initialiser le calculateur avec config par défaut
        self.benchmark_calculator = BenchmarkGapCalculator(self.analysis_config, self.active_profile)

    def analyze(self, input_data: dict) -> dict:
        """Point d'entrée principal d'analyse"""
        self.logger.info("Début analyse...")
        
        start_time = datetime.now()
        
        analysis = {
            "meta": {
                "version": "1.0.0",
                "generated_at": datetime.now().isoformat(),
                "analysis_duration_seconds": 0,
                "web_searches_count": 0
            },
            "profil": input_data.get("profil", {}),  # Inclure le profil investisseur
            "synthese": {},
            "repartition": {},
            "risques": {},
            "recommandations": {},
            "stress_tests": [],
            "optimisation_portefeuille": {},
            "recherches_web": []
        }
        
        # 1. Calcul répartitions
        self.logger.info("Analyse répartition...")
        analysis["repartition"] = self._analyze_repartition(input_data)

        # 2. Identification risques (avec web research)
        self.logger.info("Identification risques...")
        analysis["risques"] = self.risk_analyzer.analyze(input_data)
        
        # 3. Génération recommandations
        self.logger.info("Génération recommandations...")
        analysis["recommandations"] = self.recommender.generate(input_data, analysis["risques"])
        
        # 4. Stress tests
        self.logger.info("Exécution stress tests...")
        analysis["stress_tests"] = self.stress_tester.run_all_tests(input_data)

        # 5. Optimisation de portefeuille (Markowitz + Sharpe)
        self.logger.info("Optimisation portefeuille...")
        analysis["optimisation_portefeuille"] = self.portfolio_optimizer.analyze(input_data)

        # 6. Synthèse
        self.logger.info("Génération synthèse globale...")
        analysis["synthese"] = self._generate_synthese(analysis, input_data)

        # 7. Métadonnées
        analysis["recherches_web"] = self.web_researcher.get_history()
        analysis["meta"]["web_searches_count"] = len(analysis["recherches_web"])
        analysis["meta"]["analysis_duration_seconds"] = int((datetime.now() - start_time).total_seconds())
        
        # Sauvegarde
        output_path = Path(self.config["paths"]["generated"]) / self.config["analyzer"]["output_file"]
        self.logger.info(f"Sauvegarde {output_path}...")
        self._save_json(analysis, output_path)
        
        self.logger.info("✓ Analyse terminée")
        return analysis
    
    def _analyze_repartition(self, data: dict) -> Dict[str, Any]:
        """
        Analyse la répartition du patrimoine
        Section 3.2.5.1 du PRD
        """
        total_financier = data["patrimoine"]["financier"]["total"]
        total_global = (
            total_financier +
            data["patrimoine"].get("crypto", {}).get("total", 0) +
            data["patrimoine"].get("metaux_precieux", {}).get("total", 0) +
            data["patrimoine"].get("immobilier", {}).get("total", 0)
        )

        repartition = {
            "par_etablissement": [],
            "par_classe_actifs": [],
            "concentration": {}
        }

        # Répartition par établissement (financier)
        for etab in data["patrimoine"]["financier"]["etablissements"]:
            if total_global > 0:
                pct = (etab["total"] / total_global) * 100

                # Déterminer niveau de risque concentration
                seuils = self.config.get("analyzer", {}).get("risk_thresholds", {})
                justifications = self.analysis_config.get("risk_justifications", {})

                if pct >= seuils.get("concentration_etablissement_critique", 50):
                    niveau_risque = "Critique"
                    justification = justifications.get("concentration_critical", "Concentration excessive")
                elif pct >= seuils.get("concentration_etablissement_eleve", 30):
                    niveau_risque = "Élevé"
                    justification = justifications.get("concentration_high", "Concentration importante")
                else:
                    niveau_risque = "Normal"
                    justification = justifications.get("concentration_normal", "Bien diversifié")

                repartition["par_etablissement"].append({
                    "nom": etab["nom"],
                    "juridiction": etab.get("juridiction", "Inconnue"),
                    "montant": etab["total"],
                    "pourcentage": round(pct, 1),
                    "niveau_risque": niveau_risque,
                    "justification": justification
                })

        # Ajouter plateformes crypto
        justifications = self.analysis_config.get("risk_justifications", {})
        for plat in data["patrimoine"].get("crypto", {}).get("plateformes", []):
            if total_global > 0 and plat.get("total", 0) > 0:
                pct = (plat["total"] / total_global) * 100

                repartition["par_etablissement"].append({
                    "nom": plat["nom"],
                    "juridiction": plat.get("juridiction", "Inconnue"),
                    "montant": plat["total"],
                    "pourcentage": round(pct, 1),
                    "niveau_risque": "Normal",
                    "justification": justifications.get("crypto_platform", "Plateforme crypto")
                })

        # Ajouter Veracash (métaux précieux)
        metaux = data["patrimoine"].get("metaux_precieux", {})
        if total_global > 0 and metaux.get("total", 0) > 0:
            pct = (metaux["total"] / total_global) * 100

            repartition["par_etablissement"].append({
                "nom": metaux.get("plateforme", "Métaux précieux"),
                "juridiction": metaux.get("juridiction", "Suisse"),
                "montant": metaux["total"],
                "pourcentage": round(pct, 1),
                "niveau_risque": "Normal",
                "justification": justifications.get("precious_metals", "Métaux précieux")
            })

        # Répartition par classe d'actifs - RESTRUCTURÉE
        # Format: type_actif | etablissement | montant | pourcentage

        actifs_detailles = []

        # Actifs financiers
        for etab in data["patrimoine"]["financier"]["etablissements"]:
            etab_nom = etab.get("nom", "")

            for compte in etab.get("comptes", []):
                montant = compte.get("montant", 0)
                if montant > 0:
                    type_compte = compte.get("type", "").lower()

                    # Classification selon le type de compte
                    if "pea" in type_compte and "pme" not in type_compte:
                        type_actif = "Actions"
                        detail = f"{etab_nom} (PEA)"
                    elif "pea-pme" in type_compte:
                        type_actif = "Actions"
                        detail = f"{etab_nom} (PEA-PME)"
                    elif "cto" in type_compte:
                        type_actif = "Actions"
                        detail = f"{etab_nom} (CTO)"
                    elif "assurance" in type_compte and "vie" in type_compte:
                        # Assurance-vie: diviser entre UC (actions) et fonds euro (obligations)
                        fonds = compte.get("fonds", [])
                        if fonds:
                            # AV avec détail des fonds
                            for fond in fonds:
                                fond_montant = fond.get("montant", 0)
                                fond_nom = fond.get("nom", "").lower()
                                if "euro" in fond_nom:
                                    actifs_detailles.append({
                                        "type_actif": "Obligations",
                                        "etablissement": f"{etab_nom} (AV - Fonds Euro)",
                                        "montant": fond_montant
                                    })
                                else:
                                    actifs_detailles.append({
                                        "type_actif": "Actions",
                                        "etablissement": f"{etab_nom} (AV - UC)",
                                        "montant": fond_montant
                                    })
                            continue  # Skip l'ajout global de l'AV
                        else:
                            # AV sans détail des fonds: considérer comme mixte (50% UC / 50% Fonds Euro)
                            # ou simplement comme Actions si pas d'info
                            type_actif = "Actions"
                            detail = f"{etab_nom} (Assurance-vie)"
                    elif any(x in type_compte for x in ["livret", "ldd", "pel"]):
                        type_actif = "Liquidités"
                        # Déterminer le label spécifique
                        if "pel" in type_compte:
                            detail = f"{etab_nom} (PEL)"
                        else:
                            detail = f"{etab_nom} ({compte.get('type', '')})"
                    elif "per" in type_compte:
                        type_actif = "Actions"
                        detail = f"{etab_nom} (PER)"
                    elif "parts sociales" in type_compte:
                        type_actif = "Actions"
                        detail = f"{etab_nom} (Parts Sociales)"
                    elif "compte" in type_compte or "dépôt" in type_compte:
                        # Vérifier si c'est Spiko (T-Bonds)
                        if "spiko" in etab_nom.lower():
                            type_actif = "Obligations d'État"
                            detail = f"{etab_nom} (T-Bonds)"
                        else:
                            type_actif = "Liquidités"
                            detail = f"{etab_nom} (Compte)"
                    else:
                        type_actif = "Autres"
                        detail = f"{etab_nom} ({compte.get('type', '')})"

                    actifs_detailles.append({
                        "type_actif": type_actif,
                        "etablissement": detail,
                        "montant": montant
                    })

        # Cryptomonnaies
        for plat in data["patrimoine"].get("crypto", {}).get("plateformes", []):
            plat_nom = plat.get("nom", "")
            for actif in plat.get("actifs", []):
                montant = actif.get("valeur", 0)
                if montant > 0:
                    symbole = actif.get("symbole", "")

                    actifs_detailles.append({
                        "type_actif": "Cryptomonnaies",
                        "etablissement": f"{plat_nom} ({symbole})",
                        "montant": montant
                    })

        # Métaux précieux
        plateforme_metaux = data["patrimoine"].get("metaux_precieux", {}).get("plateforme", "Veracash")
        for metal in data["patrimoine"].get("metaux_precieux", {}).get("metaux", []):
            montant = metal.get("valeur", 0)
            if montant > 0:
                type_metal = metal.get("type", "Métal")

                actifs_detailles.append({
                    "type_actif": "Métaux précieux",
                    "etablissement": f"{plateforme_metaux} ({type_metal})",
                    "montant": montant
                })

        # Immobilier
        for bien in data["patrimoine"].get("immobilier", {}).get("biens", []):
            montant = bien.get("valeur_actuelle", 0)
            if montant > 0:
                type_bien = bien.get("type", "Bien")
                adresse = bien.get("adresse", "")

                # Extraire ville
                ville = ""
                if adresse:
                    import re
                    match = re.search(r"\d{5}\s+([A-Za-zÀ-ÿ\s-]+)", adresse)
                    if match:
                        ville = match.group(1).strip().split()[0]

                detail = f"{type_bien} {ville}" if ville else type_bien

                actifs_detailles.append({
                    "type_actif": "Immobilier",
                    "etablissement": detail,
                    "montant": montant
                })

        # Agréger les actifs par (type_actif, etablissement)
        # Ceci permet de fusionner les multiples fonds UC de l'AV en une seule ligne
        actifs_agreges = {}
        for actif in actifs_detailles:
            key = (actif["type_actif"], actif["etablissement"])
            if key in actifs_agreges:
                actifs_agreges[key]["montant"] += actif["montant"]
            else:
                actifs_agreges[key] = {
                    "type_actif": actif["type_actif"],
                    "etablissement": actif["etablissement"],
                    "montant": actif["montant"]
                }

        # Convertir en liste
        actifs_detailles = list(actifs_agreges.values())

        # Calculer les pourcentages (sur total_global pour totaliser 100%)
        for actif in actifs_detailles:
            pct = (actif["montant"] / total_global * 100) if total_global > 0 else 0
            actif["pourcentage"] = round(pct, 1)

        # Trier par montant décroissant
        actifs_detailles.sort(key=lambda x: x["montant"], reverse=True)

        # Enrichir avec les données d'écart benchmark
        if self.benchmark_calculator:
            actifs_detailles = self.benchmark_calculator.calculate_all_gaps(actifs_detailles)

        repartition["par_classe_actifs"] = actifs_detailles

        # Concentration juridictionnelle
        juridictions = {}
        for etab in data["patrimoine"]["financier"]["etablissements"]:
            jur = etab.get("juridiction", "Inconnue")
            juridictions[jur] = juridictions.get(jur, 0) + etab["total"]

        # Ajouter la répartition par juridiction à la structure
        repartition["par_juridiction"] = []

        for jur, montant in juridictions.items():
            if total_global > 0:
                pct = (montant / total_global) * 100
                seuils = self.config.get("analyzer", {}).get("risk_thresholds", {})

                if pct >= seuils.get("concentration_juridiction_critique", 80):
                    niveau_risque = "Critique"
                elif pct >= seuils.get("concentration_juridiction_eleve", 60):
                    niveau_risque = "Élevé"
                else:
                    niveau_risque = "Normal"

                repartition["concentration"][jur.lower()] = {
                    "montant": montant,
                    "pourcentage": round(pct, 1),
                    "niveau_risque": niveau_risque
                }

                # Ajouter à par_juridiction
                repartition["par_juridiction"].append({
                    "nom": jur,
                    "montant": montant,
                    "pourcentage": round(pct, 1),
                    "niveau_risque": niveau_risque
                })

        # Trier par montant décroissant
        repartition["par_juridiction"].sort(key=lambda x: x["montant"], reverse=True)

        return repartition

    def _generate_synthese(self, analysis: dict, input_data: dict) -> Dict[str, Any]:
        """
        Génère la synthèse globale avec scores
        Section 3.2.4 du PRD
        """
        # Calcul patrimoine total
        patrimoine_financier = input_data["patrimoine"]["financier"]["total"]
        patrimoine_crypto = input_data["patrimoine"].get("crypto", {}).get("total", 0)
        patrimoine_metaux = input_data["patrimoine"].get("metaux_precieux", {}).get("total", 0)
        patrimoine_immobilier = input_data["patrimoine"].get("immobilier", {}).get("total", 0)
        patrimoine_total = patrimoine_financier + patrimoine_crypto + patrimoine_metaux + patrimoine_immobilier

        # Calcul des scores (0-10)
        diversification_data = self._calculate_diversification_score(input_data, analysis)
        score_diversification = diversification_data.get("score", 0)

        resilience_data = self._calculate_resilience_score(analysis)
        score_resilience = resilience_data.get("score", 0)

        liquidite_data = self._calculate_liquidity_score(input_data)
        score_liquidite = liquidite_data.get("score", 0)

        fiscal_data = self._calculate_fiscal_score(input_data)
        score_fiscalite = fiscal_data.get("score", 0)

        growth_data = self._calculate_growth_score(input_data)
        score_croissance = growth_data.get("score", 0)

        score_global = round(
            (score_diversification + score_resilience + score_liquidite + score_fiscalite + score_croissance) / 5,
            1
        )

        # Identifier risque principal
        risques_critiques = analysis["risques"].get("critiques", [])
        if risques_critiques:
            risque_principal = risques_critiques[0].get("titre", "Non identifié")
        else:
            risques_eleves = analysis["risques"].get("eleves", [])
            risque_principal = risques_eleves[0].get("titre", "Aucun") if risques_eleves else "Aucun"

        # Identifier priorités
        recos_prioritaires = analysis["recommandations"].get("prioritaires", [])
        if recos_prioritaires:
            priorites = recos_prioritaires[0].get("titre", "Non défini")
        else:
            priorites = "Maintenir allocation actuelle"

        synthese = {
            "patrimoine_total": patrimoine_total,
            "patrimoine_financier": patrimoine_financier,
            "patrimoine_immobilier": patrimoine_immobilier,
            "score_global": score_global,
            "scores_details": {
                "diversification": score_diversification,
                "resilience": score_resilience,
                "liquidite": score_liquidite,
                "fiscalite": score_fiscalite,
                "croissance": score_croissance
            },
            "diversification_details": diversification_data,  # Ajout des détails enrichis
            "resilience_details": resilience_data,  # Ajout des détails enrichis
            "liquidity_details": liquidite_data,  # Ajout des détails enrichis
            "fiscal_details": fiscal_data,  # Ajout des détails enrichis
            "growth_details": growth_data,  # Ajout des détails enrichis
            "risque_principal": risque_principal,
            "priorites": priorites
        }

        return synthese

    def _calculate_diversification_score(self, data: dict, analysis: dict) -> dict:
        """
        Score diversification (0-10) basé sur concentration et dispersion
        Retourne un dict avec score, label, et détails des composantes
        """
        # Charger les paramètres depuis la configuration
        div_config = self.analysis_config.get("scores", {}).get("diversification", {})
        base_score = div_config.get("base_score", 10.0)
        weights = div_config.get("weights", {"institutional": 0.6, "jurisdictional": 0.4})
        bonuses_config = div_config.get("bonuses", {})

        # --- COMPOSANTE 1 : Score institutionnel ---
        score_institutional = base_score
        etab_penalties = div_config.get("penalties", {}).get("establishment_concentration", {})

        for etab_info in analysis["repartition"].get("par_etablissement", []):
            pct = etab_info.get("pourcentage", 0)
            if pct > 70:
                score_institutional += etab_penalties.get("threshold_70", -3.0)
            elif pct > 50:
                score_institutional += etab_penalties.get("threshold_50", -2.0)
            elif pct > 30:
                score_institutional += etab_penalties.get("threshold_30", -0.5)

        score_institutional = max(0, min(10, score_institutional))

        # --- COMPOSANTE 2 : Score juridictionnel ---
        score_jurisdictional = base_score
        jur_penalties = div_config.get("penalties", {}).get("jurisdiction_concentration", {})

        for jur_info in analysis["repartition"]["concentration"].values():
            pct = jur_info.get("pourcentage", 0)
            if pct > 85:
                score_jurisdictional += jur_penalties.get("threshold_85", -2.0)

        score_jurisdictional = max(0, min(10, score_jurisdictional))

        # --- BONUS INTRA-PORTEFEUILLE ---
        bonus_total = 0.0
        bonus_details = {}

        # Bonus 1 : Nombre de classes d'actifs distinctes
        classes_actifs = set()
        for actif in analysis["repartition"].get("par_classe_actifs", []):
            type_actif = actif.get("type_actif", "")
            if type_actif:
                classes_actifs.add(type_actif)

        nb_classes = len(classes_actifs)
        if nb_classes >= 5:
            bonus = bonuses_config.get("asset_classes_5plus", 1.0)
            bonus_total += bonus
            bonus_details["classes_actifs"] = {"count": nb_classes, "bonus": bonus}

        # Bonus 2 : Nombre de positions/comptes individuels
        nb_positions = 0
        for etab in data["patrimoine"]["financier"]["etablissements"]:
            nb_positions += len(etab.get("comptes", []))

        # Ajouter crypto et métaux
        for plat in data["patrimoine"].get("crypto", {}).get("plateformes", []):
            nb_positions += len(plat.get("actifs", []))
        nb_positions += len(data["patrimoine"].get("metaux_precieux", {}).get("metaux", []))
        nb_positions += len(data["patrimoine"].get("immobilier", {}).get("biens", []))

        if nb_positions >= 10:
            bonus = bonuses_config.get("positions_10plus", 0.5)
            bonus_total += bonus
            bonus_details["positions"] = {"count": nb_positions, "bonus": bonus}

        # Bonus 3 : Exposition internationale
        # Calculer le patrimoine total depuis data (input_data)
        patrimoine_financier = data["patrimoine"]["financier"]["total"]
        patrimoine_crypto = data["patrimoine"].get("crypto", {}).get("total", 0)
        patrimoine_metaux = data["patrimoine"].get("metaux_precieux", {}).get("total", 0)
        patrimoine_immobilier = data["patrimoine"].get("immobilier", {}).get("total", 0)
        total_patrimoine = patrimoine_financier + patrimoine_crypto + patrimoine_metaux + patrimoine_immobilier
        exposition_internationale = 0

        for jur, jur_info in analysis["repartition"]["concentration"].items():
            if jur.lower() != "france":
                exposition_internationale += jur_info.get("montant", 0)

        pct_international = (exposition_internationale / total_patrimoine * 100) if total_patrimoine > 0 else 0

        if pct_international > 15:
            bonus = bonuses_config.get("international_15plus", 0.5)
            bonus_total += bonus
            bonus_details["international"] = {"pct": round(pct_international, 1), "bonus": bonus}

        # --- SCORE FINAL PONDÉRÉ ---
        score_weighted = (
            score_institutional * weights.get("institutional", 0.6) +
            score_jurisdictional * weights.get("jurisdictional", 0.4)
        )

        score_final = score_weighted + bonus_total
        score_final = max(0, min(10, round(score_final, 1)))

        # --- LABEL DE QUALITÉ ---
        quality_label = "Score non défini"
        quality_labels = div_config.get("quality_labels", [])

        for label_range in quality_labels:
            min_score, max_score, label = label_range
            if min_score <= score_final < max_score or (score_final == 10 and max_score == 10):
                quality_label = label
                break

        # --- RETOUR ENRICHI ---
        return {
            "score": score_final,
            "label": quality_label,
            "details": {
                "score_institutional": round(score_institutional, 1),
                "score_jurisdictional": round(score_jurisdictional, 1),
                "score_weighted": round(score_weighted, 1),
                "bonus_total": round(bonus_total, 1),
                "bonus_details": bonus_details,
                "nb_classes_actifs": nb_classes,
                "nb_positions": nb_positions,
                "pct_international": round(pct_international, 1)
            }
        }

    def _calculate_resilience_score(self, analysis: dict) -> dict:
        """
        Score résilience (0-10) basé sur stress tests
        Retourne un dict avec score et label de qualité
        """
        # Charger les paramètres depuis la configuration
        res_config = self.analysis_config.get("scores", {}).get("resilience", {})
        score = res_config.get("base_score", 8.0)

        # Pénaliser sévérités élevées dans stress tests
        stress_penalties = res_config.get("stress_test_penalties", {})
        for test in analysis.get("stress_tests", []):
            severite = test.get("severite")
            if severite in stress_penalties:
                score += stress_penalties[severite]

        # Bonus/malus selon nombre de risques critiques
        nb_critiques = len(analysis["risques"].get("critiques", []))
        bonuses = res_config.get("critical_risks_bonus", {})
        if nb_critiques == 0:
            score += bonuses.get("zero_risks", 1.0)
        elif nb_critiques >= 3:
            score += bonuses.get("three_or_more", -1.5)

        score = max(0, min(10, round(score, 1)))

        # Déterminer le label de qualité
        quality_label = "Score non défini"
        quality_labels = res_config.get("quality_labels", [])

        for label_range in quality_labels:
            min_score, max_score, label = label_range
            if min_score <= score < max_score or (score == 10 and max_score == 10):
                quality_label = label
                break

        return {
            "score": score,
            "label": quality_label
        }

    def _calculate_liquidity_score(self, data: dict) -> dict:
        """
        Score liquidité (0-10) basé sur liquidités disponibles
        Version 2.0 : Retourne un dict avec score, label, et détails
        Adapté au profil investisseur et pénalise la sur-liquidité
        """
        # Charger les paramètres depuis la configuration
        liq_config = self.analysis_config.get("scores", {}).get("liquidity", {})
        keywords = liq_config.get("liquid_account_keywords", ["livret", "dépôt", "compte"])

        # Calculer liquidités
        liquidite = 0
        for etab in data["patrimoine"]["financier"]["etablissements"]:
            for compte in etab.get("comptes", []):
                type_compte = compte.get("type", "").lower()
                if any(x in type_compte for x in keywords):
                    liquidite += compte.get("montant", 0)

        # Cible : X mois de dépenses selon le profil actif
        revenu_mensuel = data.get("profil", {}).get("revenu_mensuel_net", 3000)
        expenses_ratio = liq_config.get("expenses_to_income_ratio", 0.7)
        depenses_mensuelles = revenu_mensuel * expenses_ratio

        # Récupérer la cible en mois selon le profil
        target_months_by_profile = liq_config.get("target_months_by_profile", {})
        target_months = target_months_by_profile.get(self.active_profile, 12)

        liquidite_cible = depenses_mensuelles * target_months

        # Calcul du ratio et du score
        if liquidite_cible > 0:
            ratio = liquidite / liquidite_cible

            # Détection de sur-liquidité
            overliquidity_threshold = liq_config.get("overliquidity_threshold", 1.5)
            is_overliquid = ratio > overliquidity_threshold

            # Appliquer les seuils depuis la configuration
            thresholds = liq_config.get("thresholds", [])
            score = liq_config.get("default_score", 5)

            # Parcourir les seuils dans l'ordre décroissant
            for threshold_min, threshold_score in sorted(thresholds, reverse=True):
                if ratio >= threshold_min:
                    score = threshold_score
                    break
        else:
            ratio = 0
            score = liq_config.get("default_score", 5)
            is_overliquid = False

        # Déterminer le label de qualité
        quality_label = "Score non défini"
        quality_labels = liq_config.get("quality_labels", [])

        for label_range in quality_labels:
            min_score, max_score, label = label_range
            if min_score <= score < max_score or (score == 10 and max_score == 10):
                quality_label = label
                break

        # Retour enrichi
        return {
            "score": round(score, 1),
            "label": quality_label,
            "details": {
                "liquidite_actuelle": round(liquidite, 2),
                "liquidite_cible": round(liquidite_cible, 2),
                "ratio": round(ratio, 2),
                "target_months": target_months,
                "depenses_mensuelles": round(depenses_mensuelles, 2),
                "is_overliquid": is_overliquid,
                "overliquidity_threshold": overliquidity_threshold
            }
        }

    def _calculate_fiscal_score(self, data: dict) -> dict:
        """
        Score fiscalité (0-10) basé sur optimisation fiscale
        Version 2.0 : Retourne un dict avec score, label, et détails
        Prend en compte PEA, CTO, AV, PER et cryptos
        """
        # Charger les paramètres depuis la configuration
        fiscal_config = self.analysis_config.get("scores", {}).get("fiscal", {})
        score = fiscal_config.get("base_score", 7.0)

        # Calculer les montants par enveloppe
        pea_total = 0
        cto_total = 0
        av_total = 0
        per_total = 0

        for etab in data["patrimoine"]["financier"]["etablissements"]:
            for compte in etab.get("comptes", []):
                type_compte = compte.get("type", "")
                montant = compte.get("montant", 0)

                if "PEA" in type_compte:
                    pea_total += montant
                elif type_compte == "CTO":
                    cto_total += montant
                elif "Assurance" in type_compte:
                    av_total += montant
                elif "PER" in type_compte:
                    per_total += montant

        # Calculer patrimoine crypto
        crypto_total = data.get("patrimoine", {}).get("crypto", {}).get("total", 0)

        # Calculer patrimoine total pour les pourcentages
        patrimoine_financier = data["patrimoine"]["financier"]["total"]
        patrimoine_immobilier = data["patrimoine"].get("immobilier", {}).get("total", 0)
        patrimoine_metaux = data["patrimoine"].get("metaux_precieux", {}).get("total", 0)
        patrimoine_total = patrimoine_financier + crypto_total + patrimoine_metaux + patrimoine_immobilier

        crypto_percentage = (crypto_total / patrimoine_total * 100) if patrimoine_total > 0 else 0

        # Appliquer les bonus
        bonuses = fiscal_config.get("bonuses", {})
        bonuses_applied = {}

        # Bonus PEA > CTO
        pea_over_cto = pea_total > cto_total
        if pea_over_cto:
            bonus_value = bonuses.get("pea_over_cto", 1.5)
            score += bonus_value
            bonuses_applied["pea_over_cto"] = bonus_value

        # Bonus AV succession
        av_threshold = bonuses.get("av_threshold", 50000)
        if av_total > av_threshold:
            bonus_value = bonuses.get("av_bonus", 0.5)
            score += bonus_value
            bonuses_applied["av_succession"] = bonus_value

        # Bonus PER présent
        per_threshold = bonuses.get("per_threshold", 5000)
        has_per = per_total > per_threshold
        if has_per:
            bonus_value = bonuses.get("per_present", 1.0)
            score += bonus_value
            bonuses_applied["per_present"] = bonus_value

        # Appliquer les pénalités
        penalties_config = fiscal_config.get("penalties", {})
        penalties_applied = {}

        # Pénalité cryptos élevés
        crypto_high_threshold = penalties_config.get("crypto_high_threshold", 15)
        if crypto_percentage > crypto_high_threshold:
            penalty_value = penalties_config.get("crypto_high_penalty", -0.5)
            score += penalty_value
            penalties_applied["crypto_high"] = penalty_value

        # Borner le score
        score = max(0, min(10, score))

        # Déterminer le label de qualité
        quality_label = "Score non défini"
        quality_labels = fiscal_config.get("quality_labels", [])

        for label_range in quality_labels:
            min_score, max_score, label = label_range
            if min_score <= score < max_score or (score == 10 and max_score == 10):
                quality_label = label
                break

        # Retour enrichi
        return {
            "score": round(score, 1),
            "label": quality_label,
            "details": {
                "pea_total": round(pea_total, 2),
                "cto_total": round(cto_total, 2),
                "av_total": round(av_total, 2),
                "per_total": round(per_total, 2),
                "crypto_total": round(crypto_total, 2),
                "crypto_percentage": round(crypto_percentage, 1),
                "pea_over_cto": pea_over_cto,
                "has_per": has_per,
                "bonuses_applied": bonuses_applied,
                "penalties_applied": penalties_applied
            }
        }

    def _calculate_growth_score(self, data: dict) -> dict:
        """
        Score croissance (0-10) basé sur exposition actions
        Version 2.0 : Retourne un dict avec score, label, et détails
        Adapté au profil investisseur (prudent, équilibré, dynamique)
        """
        # Calculer exposition actions
        exposition_actions = 0
        total = data["patrimoine"]["financier"]["total"]

        for etab in data["patrimoine"]["financier"]["etablissements"]:
            for compte in etab.get("comptes", []):
                type_compte = compte.get("type", "")
                montant = compte.get("montant", 0)

                if type_compte in ["PEA", "PEA-PME", "CTO"]:
                    exposition_actions += montant
                elif type_compte == "Assurance-vie":
                    # Compter UC comme actions
                    for fond in compte.get("fonds", []):
                        if "euro" not in fond.get("nom", "").lower():
                            exposition_actions += fond.get("montant", 0)

        if total > 0:
            pct_actions = (exposition_actions / total) * 100

            # Charger les paramètres du profil actif
            growth_config = self.analysis_config.get("scores", {}).get("growth", {}).get(self.active_profile, {})

            # Plages optimales/bonnes/moyennes selon le profil
            optimal_range = growth_config.get("optimal_range", [60, 70])
            good_ranges = growth_config.get("good_ranges", [[50, 60], [70, 80]])
            medium_ranges = growth_config.get("medium_ranges", [[40, 50], [80, 90]])
            fallback_score = growth_config.get("fallback_score", 4)

            # Déterminer le score et l'interprétation
            interpretation = ""
            if optimal_range[0] <= pct_actions <= optimal_range[1]:
                score = 10
                interpretation = f"Exposition optimale pour votre profil ({optimal_range[0]}-{optimal_range[1]}%)"
            else:
                # Vérifier si dans une plage "good"
                in_good = any(r[0] <= pct_actions <= r[1] for r in good_ranges)
                if in_good:
                    score = 8
                    if pct_actions < optimal_range[0]:
                        interpretation = f"Légèrement sous-exposé (optimal : {optimal_range[0]}-{optimal_range[1]}%)"
                    else:
                        interpretation = f"Légèrement sur-exposé (optimal : {optimal_range[0]}-{optimal_range[1]}%)"
                else:
                    # Vérifier si dans une plage "medium"
                    in_medium = any(r[0] <= pct_actions <= r[1] for r in medium_ranges)
                    if in_medium:
                        score = 6
                        if pct_actions < optimal_range[0]:
                            interpretation = f"Nettement sous-exposé (optimal : {optimal_range[0]}-{optimal_range[1]}%)"
                        else:
                            interpretation = f"Nettement sur-exposé (optimal : {optimal_range[0]}-{optimal_range[1]}%)"
                    else:
                        score = fallback_score
                        if pct_actions < optimal_range[0]:
                            interpretation = f"Fortement sous-exposé (optimal : {optimal_range[0]}-{optimal_range[1]}%)"
                        else:
                            interpretation = f"Fortement sur-exposé (optimal : {optimal_range[0]}-{optimal_range[1]}%)"
        else:
            score = 5
            pct_actions = 0
            optimal_range = [60, 70]
            interpretation = "Patrimoine financier vide ou non renseigné"

        # Déterminer le label de qualité
        quality_label = "Score non défini"
        quality_labels = self.analysis_config.get("scores", {}).get("growth", {}).get("quality_labels", [])

        for label_range in quality_labels:
            min_score, max_score, label = label_range
            if min_score <= score < max_score or (score == 10 and max_score == 10):
                quality_label = label
                break

        # Retour enrichi
        return {
            "score": round(score, 1),
            "label": quality_label,
            "details": {
                "exposition_actions": round(exposition_actions, 2),
                "patrimoine_financier": round(total, 2),
                "pct_actions": round(pct_actions, 1),
                "profil_actif": self.active_profile,
                "optimal_range": optimal_range,
                "interpretation": interpretation
            }
        }
    
    def _save_json(self, data: dict, output_path: Path):
        """Sauvegarde le JSON d'analyse"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
