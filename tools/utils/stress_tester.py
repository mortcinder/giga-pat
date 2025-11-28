"""
Module de simulation de stress tests
Suit les spécifications des sections 3.2.5.4 et 17 du PRD
"""

import logging
from typing import Dict, List, Any


class StressTester:
    """
    Simule l'impact de scénarios de crise sur le patrimoine
    Section 3.2.5.4 du PRD - 5 scénarios
    """

    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)

    def run_all_tests(self, data: dict) -> List[Dict]:
        """
        Exécute tous les stress tests
        Retourne une liste de scénarios avec impacts
        """
        self.logger.info("Exécution stress tests...")

        tests = []

        # Scénario 1: Crise bancaire + Sapin 2 (section 17.1)
        self.logger.info("  → Crise bancaire + Sapin 2")
        tests.append(self._test_banking_crisis(data))

        # Scénario 2: Krach actions -30% (section 17.2)
        self.logger.info("  → Krach actions -30%")
        tests.append(self._test_market_crash(data))

        # Scénario 3: Perte d'emploi (section 17.3)
        self.logger.info("  → Perte d'emploi 12-24 mois")
        tests.append(self._test_job_loss(data))

        # Scénario 4: Hausse fiscalité
        self.logger.info("  → Hausse fiscalité PFU")
        tests.append(self._test_tax_increase(data))

        # Scénario 5: Crise immobilière -20%
        self.logger.info("  → Crise immobilière -20%")
        tests.append(self._test_real_estate_crisis(data))

        self.logger.info(f"✓ {len(tests)} scénarios simulés")

        return tests

    def _test_banking_crisis(self, data: dict) -> Dict[str, Any]:
        """
        Scénario : Crise bancaire + activation Loi Sapin 2
        Section 17.1 du PRD
        """
        patrimoine_financier = data["patrimoine"]["financier"]["total"]

        # Actifs gelés
        av_gele = 0
        depots_geles = 0

        for etab in data["patrimoine"]["financier"]["etablissements"]:
            if etab.get("juridiction") == "France":
                for compte in etab.get("comptes", []):
                    compte_type = compte.get("type", "").lower()

                    # Blocage Assurance-vie (Loi Sapin 2)
                    if "assurance" in compte_type and "vie" in compte_type:
                        av_gele += compte.get("montant", 0)

                    # Hypothèse : 50% des dépôts gelés temporairement
                    elif any(x in compte_type for x in ["compte", "dépôt", "livret"]):
                        depots_geles += compte.get("montant", 0) * 0.5

        total_gele = av_gele + depots_geles
        patrimoine_accessible = patrimoine_financier - total_gele

        if patrimoine_financier > 0:
            pct_accessible = (patrimoine_accessible / patrimoine_financier) * 100
            impact_pct = -round((total_gele / patrimoine_financier) * 100, 1)
        else:
            pct_accessible = 0
            impact_pct = 0

        return {
            "scenario": "Crise bancaire + Sapin 2",
            "description": "Blocage AV + gel partiel dépôts bancaires",
            "impact_montant": -total_gele,
            "impact_pct": impact_pct,
            "patrimoine_accessible": patrimoine_accessible,
            "pct_accessible": round(pct_accessible, 1),
            "severite": "Haute" if pct_accessible < 50 else "Moyenne",
            "details": {
                "av_gele": av_gele,
                "depots_geles": depots_geles
            },
            "duree_estimee": "3-12 mois",
            "precedents": ["Crise Chypre 2013", "Crise Grèce 2015"]
        }

    def _test_market_crash(self, data: dict) -> Dict[str, Any]:
        """
        Scénario : Krach boursier -30%
        Section 17.2 du PRD
        """
        patrimoine_total = (
            data["patrimoine"]["financier"]["total"] +
            data["patrimoine"].get("crypto", {}).get("total", 0) +
            data["patrimoine"].get("immobilier", {}).get("total", 0)
        )

        # Exposition actions (PEA, CTO, UC AV)
        exposition_actions = 0

        for etab in data["patrimoine"]["financier"]["etablissements"]:
            for compte in etab.get("comptes", []):
                compte_type = compte.get("type", "")

                if compte_type in ["PEA", "PEA-PME", "CTO"]:
                    exposition_actions += compte.get("montant", 0)

                elif compte_type == "Assurance-vie":
                    # Extraction UC (hors fonds euro)
                    for position in compte.get("positions", []):
                        if "euro" not in position.get("nom", "").lower():
                            exposition_actions += position.get("montant", 0)

        # Impact -30% sur actions
        perte = exposition_actions * 0.30
        patrimoine_final = patrimoine_total - perte

        if patrimoine_total > 0:
            pct_impact = (perte / patrimoine_total) * 100
        else:
            pct_impact = 0

        return {
            "scenario": "Krach actions -30%",
            "description": "Correction majeure type 2008 ou 2020",
            "impact_montant": -perte,
            "impact_pct": -round(pct_impact, 1),
            "patrimoine_final": patrimoine_final,
            "severite": "Haute" if pct_impact > 20 else "Moyenne",
            "details": {
                "exposition_actions": exposition_actions,
                "perte_actions": perte
            },
            "duree_estimee": "6-24 mois pour récupération",
            "precedents": ["Crise 2008 : -40%", "COVID 2020 : -35%"]
        }

    def _test_job_loss(self, data: dict) -> Dict[str, Any]:
        """
        Scénario : Perte d'emploi prolongée
        Section 17.3 du PRD
        """
        profil = data.get("profil", {})
        revenu_mensuel = profil.get("professionnel", {}).get("revenu_mensuel_net", 0)

        # Hypothèse dépenses : 70% du revenu
        depenses_mensuelles = revenu_mensuel * 0.70

        # Liquidité disponible
        liquidite = 0
        for etab in data["patrimoine"]["financier"]["etablissements"]:
            for compte in etab.get("comptes", []):
                compte_type = compte.get("type", "").lower()
                # Types de comptes liquides : livrets, comptes de dépôt, épargne réglementée
                if any(x in compte_type for x in ["compte", "dépôt", "livret", "ldd", "pel", "lea", "ldds"]):
                    liquidite += compte.get("montant", 0)

        # Durée tenable
        if depenses_mensuelles > 0:
            duree_mois = int(liquidite / depenses_mensuelles)
        else:
            duree_mois = 999

        severite = "Faible" if duree_mois >= 12 else ("Moyenne" if duree_mois >= 6 else "Haute")

        return {
            "scenario": "Perte d'emploi 12-24 mois",
            "description": f"Capacité maintien niveau de vie ({depenses_mensuelles:,.0f}€/mois)",
            "duree_mois": duree_mois,
            "severite": severite,
            "details": {
                "liquidite_disponible": liquidite,
                "depenses_mensuelles": depenses_mensuelles,
                "revenu_mensuel": revenu_mensuel
            },
            "recommandation": f"Cible : 12 mois ({depenses_mensuelles * 12:,.0f}€)",
            "impact_montant": 0,  # Pour compatibilité structure
            "impact_pct": 0
        }

    def _test_tax_increase(self, data: dict) -> Dict[str, Any]:
        """
        Scénario : Hausse fiscalité PFU 30% → 35%
        """
        # Actifs soumis au PFU (CTO principalement)
        actifs_pfu = 0

        for etab in data["patrimoine"]["financier"]["etablissements"]:
            for compte in etab.get("comptes", []):
                if compte.get("type") == "CTO":
                    actifs_pfu += compte.get("montant", 0)

        # Hypothèse : plus-value moyenne de 20%
        plus_value_estimee = actifs_pfu * 0.20

        # Impact fiscal +5% sur plus-values
        surcout_fiscal = plus_value_estimee * 0.05

        patrimoine_total = (
            data["patrimoine"]["financier"]["total"] +
            data["patrimoine"].get("crypto", {}).get("total", 0) +
            data["patrimoine"].get("immobilier", {}).get("total", 0)
        )

        if patrimoine_total > 0:
            impact_pct = (surcout_fiscal / patrimoine_total) * 100
        else:
            impact_pct = 0

        return {
            "scenario": "Hausse fiscalité PFU 30% → 35%",
            "description": "Impact d'une hausse du PFU de 5 points",
            "impact_montant": -surcout_fiscal,
            "impact_pct": -round(impact_pct, 1),
            "severite": "Faible" if impact_pct < 1 else "Moyenne",
            "details": {
                "actifs_concernes": actifs_pfu,
                "plus_value_estimee": plus_value_estimee,
                "surcout_fiscal_annuel": surcout_fiscal
            },
            "duree_estimee": "Impact annuel récurrent",
            "probabilite": "Moyenne"
        }

    def _test_real_estate_crisis(self, data: dict) -> Dict[str, Any]:
        """
        Scénario : Crise immobilière -20%
        """
        valeur_immo = data["patrimoine"].get("immobilier", {}).get("total", 0)

        # Impact -20% sur l'immobilier
        perte_immo = valeur_immo * 0.20

        patrimoine_total = (
            data["patrimoine"]["financier"]["total"] +
            data["patrimoine"].get("crypto", {}).get("total", 0) +
            valeur_immo
        )

        if patrimoine_total > 0:
            impact_pct = (perte_immo / patrimoine_total) * 100
        else:
            impact_pct = 0

        return {
            "scenario": "Crise immobilière -20%",
            "description": "Correction marché immobilier local",
            "impact_montant": -perte_immo,
            "impact_pct": -round(impact_pct, 1),
            "patrimoine_final": patrimoine_total - perte_immo,
            "severite": "Moyenne" if impact_pct > 5 else "Faible",
            "details": {
                "valeur_actuelle": valeur_immo,
                "valeur_apres_crise": valeur_immo - perte_immo
            },
            "duree_estimee": "3-10 ans pour récupération",
            "precedents": ["Crise subprimes 2008", "Bulle immobilière 1990"]
        }
