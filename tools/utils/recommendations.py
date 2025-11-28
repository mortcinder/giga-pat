"""
Module de génération de recommandations
Suit les spécifications des sections 3.2.5.3 et 15 du PRD

Version 2.1+ : Intégration recommandations dynamiques basées sur validation web
"""

import logging
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional

from tools.utils.knowledge_validator import KnowledgeValidator


class Recommender:
    """
    Génère des recommandations prioritisées basées sur les risques
    Section 3.2.5.3 et 15 du PRD
    """

    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.reco_id_counter = 1

        # Charger regles metier CGP (v2.1.5+)
        try:
            rules_path = Path("config/recommendations_rules.yaml")
            if rules_path.exists():
                with open(rules_path, 'r', encoding='utf-8') as f:
                    self.rules_config = yaml.safe_load(f)
                self.rules_enabled = True
                self.logger.info("✓ Règles métier CGP chargées")
            else:
                self.logger.warning("recommendations_rules.yaml non trouvé - règles métier désactivées")
                self.rules_config = None
                self.rules_enabled = False
        except Exception as e:
            self.logger.warning(f"Erreur chargement règles métier: {e}")
            self.rules_config = None
            self.rules_enabled = False

        # Charger knowledge config et validator (v2.1+ - validation web)
        try:
            knowledge_path = Path("config/recommendations_knowledge.yaml")
            if knowledge_path.exists():
                with open(knowledge_path, 'r', encoding='utf-8') as f:
                    self.knowledge_config = yaml.safe_load(f)
                self.knowledge_validator = KnowledgeValidator(config, self.knowledge_config)
                self.dynamic_recommendations_enabled = True
                self.logger.info("✓ Recommandations dynamiques activées")
            else:
                self.logger.warning("recommendations_knowledge.yaml non trouvé - recommandations dynamiques désactivées")
                self.knowledge_config = None
                self.knowledge_validator = None
                self.dynamic_recommendations_enabled = False
        except Exception as e:
            self.logger.warning(f"Erreur chargement knowledge config: {e} - recommandations dynamiques désactivées")
            self.knowledge_config = None
            self.knowledge_validator = None
            self.dynamic_recommendations_enabled = False

        # Charger regulatory facts (v2.1+)
        try:
            regulatory_path = Path("config/regulatory_facts.yaml")
            if regulatory_path.exists():
                with open(regulatory_path, 'r', encoding='utf-8') as f:
                    self.regulatory_facts = yaml.safe_load(f)
                self.logger.debug("✓ Regulatory facts chargés")
            else:
                self.logger.warning("regulatory_facts.yaml non trouvé")
                self.regulatory_facts = None
        except Exception as e:
            self.logger.warning(f"Erreur chargement regulatory facts: {e}")
            self.regulatory_facts = None

    def generate(self, data: dict, risques: dict) -> Dict[str, List[Dict]]:
        """
        Génère recommandations prioritisées à partir des risques identifiés
        Formule de score : (criticité × 0.4) + (impact × 0.3) + (facilité × 0.3)

        v2.1+ : Intègre recommandations dynamiques basées sur validation web
        """
        self.logger.info("Génération recommandations...")

        all_recommendations = []

        # PHASE 1: Recommandations dynamiques (v2.1+)
        if self.dynamic_recommendations_enabled:
            try:
                dynamic_recos = self._generate_dynamic_recommendations(data)
                all_recommendations.extend(dynamic_recos)
                self.logger.info(f"✓ {len(dynamic_recos)} recommandations dynamiques générées")
            except Exception as e:
                self.logger.error(f"Erreur génération recommandations dynamiques: {e}")

        # PHASE 2: Recommandations basées sur risques (existant)
        for risque in risques.get("critiques", []) + risques.get("eleves", []):
            recos = self._generate_for_risk(risque, data)
            all_recommendations.extend(recos)

        # Calcul des scores de priorité (section 15.1)
        for reco in all_recommendations:
            reco["priorite"] = self._calculate_priority_score(reco)

        # Tri par score décroissant
        all_recommendations.sort(key=lambda x: x["priorite"], reverse=True)

        # Classification par niveau (section 15.2)
        recommandations = {
            "prioritaires": [r for r in all_recommendations if r["priorite"] >= 8],
            "secondaires": [r for r in all_recommendations if 5 <= r["priorite"] < 8],
            "long_terme": [r for r in all_recommendations if r["priorite"] < 5]
        }

        self.logger.info(f"✓ {len(all_recommendations)} recommandations : "
                        f"{len(recommandations['prioritaires'])} prioritaires, "
                        f"{len(recommandations['secondaires'])} secondaires, "
                        f"{len(recommandations['long_terme'])} long terme")

        return recommandations

    def _generate_for_risk(self, risque: dict, data: dict) -> List[Dict[str, Any]]:
        """Génère recommandations pour un risque spécifique"""
        recommendations = []
        categorie = risque.get("categorie", "")
        titre_risque = risque.get("titre", "")

        # Concentration géographique (check FIRST before general concentration)
        if "Concentration géographique" in titre_risque:
            pays = titre_risque.split(' - ')[-1] if ' - ' in titre_risque else "France"
            montant_diversification = risque["exposition_montant"] * 0.15

            # Analyser les positions internationales existantes
            positions_internationales = self._analyze_international_positions(data)

            # Construire la recommandation selon ce qui existe
            if positions_internationales["etf_world"] or positions_internationales["etf_us"] or positions_internationales["etf_em"]:
                # L'utilisateur a DÉJÀ des ETF internationaux - recommander de renforcer
                etf_existants = []
                if positions_internationales["etf_em"]:
                    etf_existants.append(f"ETF Emerging Markets ({positions_internationales['etf_em_montant']:,.0f}€)")
                if positions_internationales["etf_us"]:
                    etf_existants.append(f"ETF USA ({positions_internationales['etf_us_montant']:,.0f}€)")
                if positions_internationales["actions_us"]:
                    etf_existants.append(f"Actions US ({positions_internationales['actions_us_montant']:,.0f}€)")

                description = f"Exposition internationale actuelle: {positions_internationales['total_international']:,.0f}€ ({positions_internationales['pct_international']:.1f}%). Renforcer la diversification géographique."

                # Identifier ce qui manque
                actions_list = []
                if not positions_internationales["etf_world"]:
                    actions_list.append(f"Ajouter ETF World (CW8 ou VWCE) pour diversification mondiale large: {montant_diversification * 0.5:,.0f}€")
                else:
                    actions_list.append(f"Renforcer ETF World existant: {montant_diversification * 0.5:,.0f}€")

                if positions_internationales["etf_em_montant"] < 3000:
                    actions_list.append(f"Renforcer ETF Emerging Markets (actuellement {positions_internationales['etf_em_montant']:,.0f}€) → cible 5-10% du portefeuille")

                if positions_internationales["etf_asia_montant"] < 2000:
                    actions_list.append(f"Renforcer exposition Asie (Japon/Chine) via ETF JPXNK ou MSCI Asia: {montant_diversification * 0.3:,.0f}€")

                actions_list.append("Programmer versements mensuels de 500-1000€ (DCA)")

                titre = f"Renforcer diversification internationale"
            else:
                # Aucun ETF international - recommander d'en acheter
                description = f"Exposition actuelle: {risque['exposition_pct']:.1f}% en {pays}. Investir {montant_diversification:,.0f}€ sur ETF internationaux."
                titre = f"Diversifier géographiquement hors {pays}"
                actions_list = [
                    f"Ajouter ETF World (CW8 Amundi MSCI World - PEA): exposition mondiale 1600+ entreprises",
                    f"Investir {montant_diversification:,.0f}€ via PEA (frais réduits, fiscalité avantageuse)",
                    "Programmer versements mensuels de 500-1000€ (DCA sur 3-6 mois)",
                    "Rééquilibrer annuellement (objectif: 15-20% international)"
                ]

            recommendations.append({
                "id": self._get_reco_id(),
                "titre": titre,
                "description": description,
                "benefice": f"Réduction exposition {pays} de {risque['exposition_pct']:.1f}% à ~75% (objectif: max 80%)",
                "montant": montant_diversification,
                "delai_jours": 90,
                "difficulte": "Moyenne",
                "actions_concretes": actions_list,
                "risques_mitigues": [risque["id"]],
                "score_criticite": self._niveau_to_score(risque["niveau"]),
                "score_impact": self._pct_to_impact_score(risque["exposition_pct"]),
                "score_facilite": 6
            })

        # Concentration établissement (check AFTER geographic to avoid confusion)
        elif "Concentration" in categorie and "géographique" not in titre_risque.lower():
            custodian_name = titre_risque.split(' - ')[-1] if ' - ' in titre_risque else 'établissement principal'
            montant_a_transferer = risque["exposition_montant"] * 0.3

            # Suggestions d'établissements alternatifs selon le custodian actuel
            etablissements_alternatifs = {
                "Crédit Agricole": ["Boursorama Banque (0€ frais, PEA gratuit)", "Fortuneo (frais réduits)", "BforBank (PEA à 0€)"],
                "BNP Paribas": ["Boursorama Banque", "Trade Republic (frais ultra-bas)", "Degiro (CTO compétitif)"],
                "Société Générale": ["Boursorama Banque", "BforBank", "Fortuneo"],
                "default": ["Boursorama Banque (leader low-cost)", "Trade Republic (ETF gratuits)", "BforBank (diversification)"]
            }
            suggestions = etablissements_alternatifs.get(custodian_name, etablissements_alternatifs["default"])

            recommendations.append({
                "id": self._get_reco_id(),
                "titre": f"Diversifier hors {custodian_name}",
                "description": f"Réduire la concentration chez {custodian_name} ({risque['exposition_pct']:.1f}% du patrimoine) en transférant {montant_a_transferer:,.0f}€ vers un établissement alternatif.",
                "benefice": f"Réduction exposition de {risque['exposition_pct']:.1f}% à ~55% (objectif: max 60%)",
                "montant": montant_a_transferer,
                "delai_jours": 60,
                "difficulte": "Moyenne",
                "actions_concretes": [
                    f"Comparer établissements alternatifs: {', '.join(suggestions[:2])}",
                    f"Ouvrir PEA ou CTO chez l'établissement choisi (délai: 2 semaines)",
                    f"Transférer {montant_a_transferer:,.0f}€ en titres ou liquide (délai: 4-6 semaines)",
                    f"Suivre répartition trimestriellement (objectif: {custodian_name} < 60%)"
                ],
                "risques_mitigues": [risque["id"]],
                "score_criticite": self._niveau_to_score(risque["niveau"]),
                "score_impact": self._pct_to_impact_score(risque["exposition_pct"]),
                "score_facilite": 6  # Moyenne
            })

        # Loi Sapin 2 - Assurance-vie
        elif "Sapin 2" in titre_risque:
            av_total = risque["exposition_montant"]
            montant_a_transferer = min(40000, av_total * 0.4)  # Max 40k€ ou 40%

            recommendations.append({
                "id": self._get_reco_id(),
                "titre": "Réduire exposition Loi Sapin 2 (AV)",
                "description": f"Racheter {montant_a_transferer:,.0f}€ de l'assurance-vie et investir sur PEA/CTO.",
                "benefice": f"Réduction risque blocage AV de {risque['exposition_pct']:.1f}% à {(av_total - montant_a_transferer) / data['patrimoine']['financier']['total'] * 100:.1f}%",
                "montant": montant_a_transferer,
                "delai_jours": 30,
                "difficulte": "Faible",
                "actions_concretes": [
                    f"Racheter {montant_a_transferer:,.0f}€ de l'AV",
                    "Investir sur PEA (enveloppe disponible)",
                    "Maintenir diversification"
                ],
                "risques_mitigues": [risque["id"]],
                "score_criticite": self._niveau_to_score(risque["niveau"]),
                "score_impact": self._pct_to_impact_score(risque["exposition_pct"]),
                "score_facilite": 9  # Faible difficulté
            })

        # Garantie dépôts dépassée
        elif "garantie dépôts" in titre_risque.lower():
            recommendations.append({
                "id": self._get_reco_id(),
                "titre": "Répartir dépôts sous 100k€ par banque",
                "description": f"Transférer {risque['exposition_montant']:,.0f}€ vers autre établissement pour respecter garantie FGDR.",
                "benefice": "Protection intégrale des dépôts en cas de faillite bancaire",
                "montant": risque["exposition_montant"],
                "delai_jours": 30,
                "difficulte": "Faible",
                "actions_concretes": [
                    "Ouvrir compte dans autre banque",
                    f"Transférer {risque['exposition_montant']:,.0f}€",
                    "Vérifier couverture totale"
                ],
                "risques_mitigues": [risque["id"]],
                "score_criticite": self._niveau_to_score(risque["niveau"]),
                "score_impact": 5,
                "score_facilite": 8
            })

        # Liquidité faible/critique
        elif "Liquidité" in categorie:
            montant_cible = 12 * (data.get("profil", {}).get("revenu_mensuel_net", 3000) * 0.7)
            montant_manquant = max(0, montant_cible - risque["exposition_montant"])

            if montant_manquant > 0:
                recommendations.append({
                    "id": self._get_reco_id(),
                    "titre": "Augmenter fonds d'urgence",
                    "description": f"Constituer épargne de précaution : {montant_manquant:,.0f}€ supplémentaires (cible 12 mois).",
                    "benefice": "Sécurisation face perte revenus, urgences",
                    "montant": montant_manquant,
                    "delai_jours": 180,
                    "difficulte": "Moyenne",
                    "actions_concretes": [
                        "Définir budget épargne mensuelle",
                        f"Alimenter Livret A/LDDS jusqu'à {montant_cible:,.0f}€",
                        "Automatiser virements"
                    ],
                    "risques_mitigues": [risque["id"]],
                    "score_criticite": self._niveau_to_score(risque["niveau"]),
                    "score_impact": 7,
                    "score_facilite": 5
                })

        # Forte exposition actions
        elif "exposition au risque actions" in titre_risque.lower():
            recommendations.append({
                "id": self._get_reco_id(),
                "titre": "Diversifier vers obligations/fonds euros",
                "description": f"Réduire exposition actions de {risque['exposition_pct']:.1f}% vers ~60-65%.",
                "benefice": "Réduction volatilité et risque correction",
                "montant": risque["exposition_montant"] * 0.1,
                "delai_jours": 120,
                "difficulte": "Moyenne",
                "actions_concretes": [
                    "Allouer vers fonds euro AV",
                    "Ajouter ETF obligataires",
                    "Maintenir exposition long terme"
                ],
                "risques_mitigues": [risque["id"]],
                "score_criticite": self._niveau_to_score(risque["niveau"]),
                "score_impact": 6,
                "score_facilite": 7
            })

        return recommendations

    def _calculate_priority_score(self, reco: dict) -> float:
        """
        Calcule le score de priorité selon formule PRD section 15.1
        Score = (criticité × 0.4) + (impact × 0.3) + (facilité × 0.3)
        """
        score_criticite = reco.get("score_criticite", 5)
        score_impact = reco.get("score_impact", 5)
        score_facilite = reco.get("score_facilite", 5)

        score_final = (
            score_criticite * 0.4 +
            score_impact * 0.3 +
            score_facilite * 0.3
        )

        return round(score_final, 1)

    def _niveau_to_score(self, niveau: str) -> int:
        """Convertit niveau de risque en score 0-10"""
        mapping = {
            "Critique": 10,
            "Élevé": 7,
            "Moyen": 4,
            "Faible": 2
        }
        return mapping.get(niveau, 5)

    def _analyze_international_positions(self, data: dict) -> dict:
        """
        Analyse les positions internationales existantes dans le patrimoine
        Retourne un dict avec les montants par type d'exposition
        """
        result = {
            "etf_world": False,
            "etf_us": False,
            "etf_em": False,
            "etf_asia": False,
            "actions_us": False,
            "etf_us_montant": 0,
            "etf_em_montant": 0,
            "etf_asia_montant": 0,
            "actions_us_montant": 0,
            "total_international": 0,
            "pct_international": 0
        }

        patrimoine_total = data.get("patrimoine", {}).get("financier", {}).get("total", 0)
        if patrimoine_total == 0:
            return result

        # Patterns pour identifier les ETF/actions internationaux
        world_patterns = ["MSCI WORLD", "FTSE ALL-WORLD", "GLOBAL", "MONDE"]
        us_patterns = ["S&P 500", "NASDAQ", "RUSSEL", "USA", "MSCI USA", "ACTIONS USA", " USA ", "UNITED STATES", "AMERICAN"]
        em_patterns = ["EMERGING", "MSCI EM", "MARCHÉS ÉMERGENTS", "EMERGENT"]
        asia_patterns = ["JAPAN", "JPXNK", "ASIA", "ASIAN", "CHINA", "HONG KONG", "INDIA", "NORDIC", "CHINE", "INDE"]

        # Patterns pour autres régions
        europe_patterns = ["EUROPE", "EURO ", "STOXX"]

        # Parcourir tous les établissements et comptes
        for etab in data.get("patrimoine", {}).get("financier", {}).get("etablissements", []):
            for compte in etab.get("comptes", []):
                # Utiliser structure unifiée "positions" (normalisée par le normalizer)
                items = compte.get("positions", [])

                for item in items:
                    nom = item.get("nom", "").upper()
                    # "valeur" pour positions, "montant" pour fonds AV
                    valeur = item.get("valeur", item.get("montant", 0))

                    # Identifier le type de position
                    is_world = any(pattern in nom for pattern in world_patterns)
                    is_us = any(pattern in nom for pattern in us_patterns)
                    is_em = any(pattern in nom for pattern in em_patterns)
                    is_asia = any(pattern in nom for pattern in asia_patterns)

                    if is_world:
                        result["etf_world"] = True
                        result["total_international"] += valeur
                    elif is_us:
                        result["etf_us"] = True
                        result["etf_us_montant"] += valeur
                        result["total_international"] += valeur
                    elif is_em:
                        result["etf_em"] = True
                        result["etf_em_montant"] += valeur
                        result["total_international"] += valeur
                    elif is_asia:
                        result["etf_asia"] = True
                        result["etf_asia_montant"] += valeur
                        result["total_international"] += valeur

                    # Détecter actions US individuelles (ISIN US...)
                    ticker = item.get("ticker", "")
                    if ticker.startswith("US") and not any([is_world, is_us, is_em, is_asia]):
                        result["actions_us"] = True
                        result["actions_us_montant"] += valeur
                        result["total_international"] += valeur

        # Calculer pourcentage
        if patrimoine_total > 0:
            result["pct_international"] = (result["total_international"] / patrimoine_total) * 100

        return result

    def _pct_to_impact_score(self, pct: float) -> int:
        """Convertit pourcentage exposition en score impact 0-10"""
        if pct >= 50:
            return 10
        elif pct >= 30:
            return 7
        elif pct >= 15:
            return 5
        else:
            return 3

    def _generate_dynamic_recommendations(self, data: dict) -> List[Dict]:
        """
        Génère recommandations dynamiques basées sur analyse des comptes (v2.1+)

        v2.1.5: Approche hybride
        - Règles métier CGP (rapide, fiable)
        - Validation web (pour données volatiles: taux, rendements)
        """
        recommendations = []

        # PHASE 1: Règles métier (v2.1.5+)
        if self.rules_enabled:
            # 1. Comptes inefficaces
            individual_recos = self._analyze_individual_accounts(data)
            recommendations.extend(individual_recos)

            # 2. Liquidités et fonds d'urgence
            liquidity_recos = self._analyze_liquidity_rules(data)
            recommendations.extend(liquidity_recos)

            # 3. Diversification
            diversif_recos = self._analyze_diversification_rules(data)
            recommendations.extend(diversif_recos)

            # 4. Allocation vs benchmark
            allocation_recos = self._analyze_allocation_rules(data)
            recommendations.extend(allocation_recos)

        # PHASE 2: Validation web (optionnel - pour données volatiles)
        # Désactivé pour l'instant car seulement 3 requêtes fonctionnent

        return recommendations

    def _analyze_individual_accounts(self, data: dict) -> List[Dict]:
        """Analyse chaque compte pour détecter inefficacités (règles métier)"""
        recommendations = []

        if not self.rules_config:
            return recommendations

        rules = self.rules_config.get("comptes_inefficaces", {})

        # 1. Livrets en doublon
        livret_recos = self._check_livret_doublon(data, rules.get("livret_doublon"))
        recommendations.extend(livret_recos)

        # 2. Compte courant surdimensionné
        cc_recos = self._check_compte_courant_surdimensionne(data, rules.get("compte_courant_surdimensionne"))
        recommendations.extend(cc_recos)

        # 3. PEA sous-utilisé
        pea_recos = self._check_pea_sous_utilise(data, rules.get("pea_sous_utilise"))
        recommendations.extend(pea_recos)

        return recommendations

    def _detect_low_value_livrets(self, data: dict) -> List[Dict]:
        """Détecte livrets avec montants trop faibles (doublons)"""
        recommendations = []

        # Valider seuil via web
        if not self.knowledge_validator:
            return []

        threshold_data = self.knowledge_validator.validate_threshold("montant_minimum_livret")

        if not threshold_data:
            # Pas assez de sources fiables, skip
            self.logger.debug("Skip détection livrets faibles: pas de consensus web")
            return []

        threshold = threshold_data["valeur"]
        self.logger.debug(f"Seuil validé pour livrets: {threshold}€ (confiance: {threshold_data['confiance']})")

        # Extraire tous les comptes de liquidités depuis patrimoine.financier.etablissements[].comptes[]
        liquidites = []
        for etab in data.get("patrimoine", {}).get("financier", {}).get("etablissements", []):
            for compte in etab.get("comptes", []):
                compte_type = compte.get("type", "")
                if compte_type in ["Livret A", "LDDS", "LDD", "LEP", "PEL", "Compte courant", "Compte"]:
                    liquidites.append(compte)

        # Détecter doublons de livrets A
        livrets_a = [l for l in liquidites if l.get("type") == "Livret A"]

        if len(livrets_a) > 1:
            # Trier par montant croissant
            livrets_a_sorted = sorted(livrets_a, key=lambda x: x.get("montant", 0))
            smallest_livret = livrets_a_sorted[0]

            if smallest_livret.get("montant", 0) < threshold:
                custodian = smallest_livret.get("custodian", "?")
                montant = smallest_livret.get("montant", 0)

                recommendations.append({
                    "id": self._get_reco_id(),
                    "type": "compte_specifique",  # Nouveau type
                    "titre": f"Clôturer le Livret A {custodian} ({montant:,.0f}€)",
                    "description": f"Ce livret A contient seulement {montant:,.0f}€ et fait doublon avec un autre livret A. Montant insuffisant pour justifier un compte séparé.",
                    "benefice": "Simplification administrative",
                    "montant": montant,
                    "delai_jours": 15,
                    "difficulte": "Faible",
                    "actions_concretes": [
                        f"Virer {montant:,.0f}€ vers le livret A principal",
                        f"Clôturer le livret A chez {custodian}",
                        "Confirmer clôture par courrier"
                    ],
                    "risques_mitigues": [],  # Pas lié à un risque spécifique
                    "sources": threshold_data.get("sources", []),  # Sources web
                    "confiance": threshold_data.get("confiance", "medium"),
                    "score_criticite": 3,  # Faible urgence
                    "score_impact": 3,  # Faible impact financier
                    "score_facilite": 10  # Très facile
                })

                self.logger.info(f"✓ Recommandation: Clôturer Livret A {custodian} ({montant:,.0f}€)")

        return recommendations

    def _get_reco_id(self) -> str:
        """Génère un ID unique pour une recommandation"""
        reco_id = f"REC_{self.reco_id_counter:03d}"
        self.reco_id_counter += 1
        return reco_id

    # =========================================================================
    # RÈGLES MÉTIER CGP (v2.1.5+)
    # =========================================================================

    def _check_livret_doublon(self, data: dict, rule: dict) -> List[Dict]:
        """Détecte livrets réglementés en doublon avec montant faible"""
        recommendations = []

        if not rule:
            return recommendations

        # Extraire tous les comptes de liquidités depuis patrimoine.financier.etablissements[].comptes[]
        liquidites = []
        for etab in data.get("patrimoine", {}).get("financier", {}).get("etablissements", []):
            for compte in etab.get("comptes", []):
                compte_type = compte.get("type", "")
                if compte_type in ["Livret A", "LDDS", "LDD", "LEP", "PEL", "Compte courant", "Compte"]:
                    liquidites.append(compte)

        # Vérifier livrets A
        livrets_a = [l for l in liquidites if l.get("type") == "Livret A"]

        if len(livrets_a) > 1:
            livrets_a_sorted = sorted(livrets_a, key=lambda x: x.get("montant", 0))
            smallest = livrets_a_sorted[0]

            if smallest.get("montant", 0) < 1000:  # Seuil de la règle
                custodian = smallest.get("custodian", "?")
                montant = smallest.get("montant", 0)
                total = sum(l.get("montant", 0) for l in livrets_a)

                recommendations.append({
                    "id": self._get_reco_id(),
                    "type": "compte_inefficace",
                    "titre": f"Consolider les livrets A",
                    "description": f"Vous détenez {len(livrets_a)} livrets A pour un total de {total:,.0f}€. Le plus petit ({custodian}) contient seulement {montant:,.0f}€.",
                    "benefice": "Simplification administrative",
                    "montant": montant,
                    "delai_jours": rule.get("recommandation", {}).get("delai_jours", 15),
                    "difficulte": "Faible",
                    "actions_concretes": [
                        f"Virer {montant:,.0f}€ vers le livret A principal",
                        f"Clôturer le livret A chez {custodian}",
                        "Confirmer clôture par courrier"
                    ],
                    "risques_mitigues": [],
                    "score_criticite": rule.get("recommandation", {}).get("criticite", 3),
                    "score_impact": rule.get("recommandation", {}).get("impact", 3),
                    "score_facilite": rule.get("recommandation", {}).get("facilite", 10)
                })

                self.logger.info(f"✓ Recommandation: Consolider livrets A ({montant:,.0f}€)")

        return recommendations

    def _check_compte_courant_surdimensionne(self, data: dict, rule: dict) -> List[Dict]:
        """Détecte compte courant avec montant excessif non rémunéré"""
        recommendations = []

        if not rule:
            return recommendations

        # Récupérer dépenses mensuelles du profil
        depenses_mensuelles = data.get("profil", {}).get("professionnel", {}).get("revenu_mensuel_net", 0) * 0.70

        if depenses_mensuelles == 0:
            return recommendations

        # Extraire tous les comptes courants depuis patrimoine.financier.etablissements[].comptes[]
        for etab in data.get("patrimoine", {}).get("financier", {}).get("etablissements", []):
            for compte in etab.get("comptes", []):
                compte_type = compte.get("type", "")
                if compte_type.lower() in ["compte courant", "compte", "depot"]:
                    montant = compte.get("montant", 0)
                    nb_mois = montant / depenses_mensuelles if depenses_mensuelles > 0 else 0

                    if nb_mois > 2:  # Seuil de la règle
                        montant_ideal = depenses_mensuelles * 2
                        montant_a_transferer = montant - montant_ideal

                        recommendations.append({
                            "id": self._get_reco_id(),
                            "type": "compte_inefficace",
                            "titre": "Réduire le montant sur compte courant",
                            "description": f"{montant:,.0f}€ sur compte courant non rémunéré ({nb_mois:.1f} mois de dépenses). Montant recommandé: {montant_ideal:,.0f}€ (2 mois).",
                            "benefice": f"Rendement potentiel: {montant_a_transferer * 0.025:.0f}€/an (Livret A 2.5%)",
                            "montant": montant_a_transferer,
                            "delai_jours": 7,
                            "difficulte": "Très faible",
                            "actions_concretes": [
                                f"Transférer {montant_a_transferer:,.0f}€ vers Livret A ou LDDS",
                                f"Conserver {montant_ideal:,.0f}€ sur compte courant"
                            ],
                            "risques_mitigues": [],
                            "score_criticite": rule.get("recommandation", {}).get("criticite", 4),
                            "score_impact": rule.get("recommandation", {}).get("impact", 5),
                            "score_facilite": rule.get("recommandation", {}).get("facilite", 9)
                        })

                        self.logger.info(f"✓ Recommandation: Réduire compte courant ({montant_a_transferer:,.0f}€ à transférer)")

        return recommendations

    def _check_pea_sous_utilise(self, data: dict, rule: dict) -> List[Dict]:
        """Détecte PEA sous-utilisé (<5000€ et <5 ans)"""
        recommendations = []

        if not rule:
            return recommendations

        # Chercher PEA dans comptes titres
        for etablissement in data.get("patrimoine", {}).get("etablissements", []):
            for compte in etablissement.get("comptes", []):
                compte_type = compte.get("type", "").upper()

                if "PEA" in compte_type and "PME" not in compte_type:
                    montant = compte.get("montant", 0)
                    # Ancienneté : à calculer si date_ouverture disponible (simplification)
                    anciennete = 3  # Supposons <5 ans pour simplifier

                    if montant < 5000 and anciennete < 5:
                        recommendations.append({
                            "id": self._get_reco_id(),
                            "type": "compte_inefficace",
                            "titre": "Alimenter le PEA avant les 5 ans",
                            "description": f"PEA de {montant:,.0f}€ (ancienneté estimée: {anciennete} ans). Avantage fiscal acquis à 5 ans de détention.",
                            "benefice": "Exonération d'impôts sur plus-values après 5 ans (hors PS 17.2%)",
                            "montant": 10000 - montant,
                            "delai_jours": 365,
                            "difficulte": "Moyenne",
                            "actions_concretes": [
                                f"Verser progressivement pour atteindre 10,000€ avant les 5 ans",
                                "Investir sur ETF diversifiés (World, Europe)"
                            ],
                            "risques_mitigues": [],
                            "score_criticite": rule.get("recommandation", {}).get("criticite", 5),
                            "score_impact": rule.get("recommandation", {}).get("impact", 7),
                            "score_facilite": rule.get("recommandation", {}).get("facilite", 8)
                        })

                        self.logger.info(f"✓ Recommandation: Alimenter PEA ({montant:,.0f}€)")

        return recommendations

    def _analyze_liquidity_rules(self, data: dict) -> List[Dict]:
        """Analyse règles de liquidités et fonds d'urgence"""
        recommendations = []

        if not self.rules_config:
            return recommendations

        rules = self.rules_config.get("liquidites_et_urgence", {})

        # Fonds d'urgence insuffisant
        urgence_rule = rules.get("fonds_urgence_insuffisant")
        if urgence_rule:
            urgence_recos = self._check_fonds_urgence(data, urgence_rule)
            recommendations.extend(urgence_recos)

        return recommendations

    def _check_fonds_urgence(self, data: dict, rule: dict) -> List[Dict]:
        """Vérifie fonds d'urgence (règle: 3-6 mois de dépenses)"""
        recommendations = []

        if not rule:
            return recommendations

        # Récupérer dépenses mensuelles
        depenses_mensuelles = data.get("profil", {}).get("professionnel", {}).get("revenu_mensuel_net", 0) * 0.70

        if depenses_mensuelles == 0:
            return recommendations

        # Calculer liquidités immédiates (depuis patrimoine.financier.etablissements[].comptes[])
        liquidites_immediates = 0
        for etab in data.get("patrimoine", {}).get("financier", {}).get("etablissements", []):
            for compte in etab.get("comptes", []):
                compte_type = compte.get("type", "")
                if compte_type in ["Livret A", "LDDS", "LDD", "Compte courant", "Compte", "LEP", "PEL"]:
                    liquidites_immediates += compte.get("montant", 0)

        nb_mois = liquidites_immediates / depenses_mensuelles if depenses_mensuelles > 0 else 0
        cible_mois = 6  # Règle CGP

        if nb_mois < 3:  # Seuil d'alerte
            montant_cible = depenses_mensuelles * cible_mois
            montant_manquant = montant_cible - liquidites_immediates
            montant_mensuel = montant_manquant / 12  # Sur 1 an

            recommendations.append({
                "id": self._get_reco_id(),
                "type": "liquidites",
                "titre": "Constituer un fonds d'urgence",
                "description": f"Fonds d'urgence actuel: {nb_mois:.1f} mois de dépenses ({liquidites_immediates:,.0f}€). Cible recommandée: {cible_mois} mois ({montant_cible:,.0f}€).",
                "benefice": "Sécurité financière en cas de coup dur (perte emploi, urgence)",
                "montant": montant_manquant,
                "delai_jours": 365,
                "difficulte": "Moyenne",
                "actions_concretes": [
                    f"Épargner {montant_mensuel:,.0f}€/mois pendant 12 mois",
                    f"Placer sur Livret A ou LDDS (disponibilité immédiate)",
                    f"Objectif: {montant_cible:,.0f}€ ({cible_mois} mois × {depenses_mensuelles:,.0f}€)"
                ],
                "risques_mitigues": ["Risque liquidité", "Perte d'emploi"],
                "score_criticite": rule.get("recommandation", {}).get("criticite", 8),
                "score_impact": rule.get("recommandation", {}).get("impact", 9),
                "score_facilite": rule.get("recommandation", {}).get("facilite", 7)
            })

            self.logger.info(f"✓ Recommandation: Constituer fonds d'urgence ({nb_mois:.1f} mois actuels)")

        return recommendations

    def _analyze_diversification_rules(self, data: dict) -> List[Dict]:
        """Analyse règles de diversification"""
        recommendations = []

        if not self.rules_config:
            return recommendations

        rules = self.rules_config.get("diversification", {})

        # Concentration custodian
        concentration_rule = rules.get("concentration_custodian")
        if concentration_rule:
            concentration_recos = self._check_concentration_custodian(data, concentration_rule)
            recommendations.extend(concentration_recos)

        return recommendations

    def _check_concentration_custodian(self, data: dict, rule: dict) -> List[Dict]:
        """Vérifie concentration chez un établissement (>60%)"""
        recommendations = []

        if not rule:
            return recommendations

        patrimoine_total = data.get("patrimoine", {}).get("patrimoine_total", 0)

        if patrimoine_total == 0:
            return recommendations

        # Analyser répartition par custodian
        for etablissement in data.get("patrimoine", {}).get("etablissements", []):
            montant = etablissement.get("total", 0)
            pct = (montant / patrimoine_total) * 100
            custodian = etablissement.get("nom", "?")

            if pct > 60:  # Seuil d'alerte
                recommendations.append({
                    "id": self._get_reco_id(),
                    "type": "diversification",
                    "titre": "Diversifier entre établissements",
                    "description": f"{pct:.1f}% du patrimoine ({montant:,.0f}€) concentré chez {custodian}. Risque: garantie dépôts limitée à 100,000€ par personne.",
                    "benefice": "Réduction du risque de défaillance bancaire",
                    "montant": montant - (patrimoine_total * 0.50),  # Excès au-dessus de 50%
                    "delai_jours": 90,
                    "difficulte": "Moyenne",
                    "actions_concretes": [
                        "Ouvrir compte chez 1-2 autres établissements",
                        "Transférer progressivement pour atteindre max 50% par établissement"
                    ],
                    "risques_mitigues": ["Concentration bancaire", "Risque défaillance"],
                    "score_criticite": rule.get("recommandation", {}).get("criticite", 7),
                    "score_impact": rule.get("recommandation", {}).get("impact", 8),
                    "score_facilite": rule.get("recommandation", {}).get("facilite", 6)
                })

                self.logger.info(f"✓ Recommandation: Diversifier établissements ({pct:.1f}% chez {custodian})")

        return recommendations

    def _analyze_allocation_rules(self, data: dict) -> List[Dict]:
        """Analyse allocation vs benchmarks du profil"""
        recommendations = []

        # Récupérer le profil actif
        profil = self.config.get("analysis", {}).get("active_profile", "equilibre")

        # Récupérer benchmarks
        benchmarks = data.get("config", {}).get("benchmarks", {}).get(profil, {})

        if not benchmarks:
            return recommendations

        # Récupérer allocation actuelle
        allocation = data.get("repartition", {}).get("par_classe", {})

        # Vérifier écarts significatifs
        for classe, bench in benchmarks.items():
            if classe not in allocation:
                continue

            pct_actuel = allocation[classe].get("pourcentage", 0)
            target = bench.get("target", 0)
            min_bench = bench.get("min", 0)
            max_bench = bench.get("max", 0)

            # Sous-pondération forte (>5% sous minimum)
            if pct_actuel < min_bench - 5:
                recommendations.append({
                    "id": self._get_reco_id(),
                    "type": "allocation",
                    "titre": f"Augmenter allocation {classe}",
                    "description": f"Allocation actuelle: {pct_actuel:.1f}%. Cible profil {profil}: {target}% (minimum: {min_bench}%).",
                    "benefice": "Alignement avec profil de risque",
                    "delai_jours": 30,
                    "difficulte": "Moyenne",
                    "actions_concretes": [
                        f"Renforcer {classe} pour atteindre {target}%"
                    ],
                    "risques_mitigues": ["Écart allocation"],
                    "score_criticite": 6,
                    "score_impact": 7,
                    "score_facilite": 7
                })

            # Sur-pondération forte (>5% au-dessus maximum)
            elif pct_actuel > max_bench + 5:
                recommendations.append({
                    "id": self._get_reco_id(),
                    "type": "allocation",
                    "titre": f"Réduire allocation {classe}",
                    "description": f"Allocation actuelle: {pct_actuel:.1f}%. Cible profil {profil}: {target}% (maximum: {max_bench}%).",
                    "benefice": "Réduction de la concentration",
                    "delai_jours": 30,
                    "difficulte": "Moyenne",
                    "actions_concretes": [
                        f"Réduire {classe} pour atteindre {target}%"
                    ],
                    "risques_mitigues": ["Concentration classe d'actifs"],
                    "score_criticite": 5,
                    "score_impact": 6,
                    "score_facilite": 6
                })

        return recommendations
