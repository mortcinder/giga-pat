"""
Module d'analyse des risques patrimoniaux
Suit les spécifications de la section 3.2.5.2 du PRD
"""

import logging
import re
from typing import Dict, List, Any, Optional


class RiskAnalyzer:
    """
    Analyse tous types de risques patrimoniaux
    Section 3.2.5.2 du PRD - 6 catégories de risques
    """

    def __init__(self, config: dict, web_researcher):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.web_researcher = web_researcher

        # Seuils de risque depuis config
        self.seuils = config.get("analyzer", {}).get("risk_thresholds", {
            "concentration_etablissement_critique": 50,
            "concentration_etablissement_eleve": 30,
            "concentration_juridiction_critique": 80,
            "concentration_juridiction_eleve": 60,
            "liquidite_critique": 5000,
            "liquidite_faible": 15000
        })

        self.risk_id_counter = 1

    def analyze(self, data: dict) -> Dict[str, List[Dict]]:
        """
        Analyse complète de tous les risques
        Retourne un dictionnaire catégorisé par niveau
        """
        self.logger.info("Analyse des risques patrimoniaux...")

        all_risks = []

        # 1. Risques de concentration (section 3.2.5.2.1)
        self.logger.info("  → Risques de concentration")
        all_risks.extend(self._analyze_concentration_risks(data))

        # 2. Risques réglementaires (section 3.2.5.2.2)
        self.logger.info("  → Risques réglementaires")
        all_risks.extend(self._analyze_regulatory_risks(data))

        # 3. Risques fiscaux (section 3.2.5.2.3)
        self.logger.info("  → Risques fiscaux")
        all_risks.extend(self._analyze_fiscal_risks(data))

        # 4. Risques de marché (section 3.2.5.2.4)
        self.logger.info("  → Risques de marché")
        all_risks.extend(self._analyze_market_risks(data))

        # 5. Risques de liquidité (section 3.2.5.2.5)
        self.logger.info("  → Risques de liquidité")
        all_risks.extend(self._analyze_liquidity_risks(data))

        # 6. Risques politiques (section 3.2.5.2.6)
        self.logger.info("  → Risques politiques")
        all_risks.extend(self._analyze_political_risks(data))

        # 7. Risques de changes (section 3.2.5.2.7)
        self.logger.info("  → Risques de changes")
        all_risks.extend(self._analyze_currency_risks(data))

        # Catégorisation par niveau
        risques = {
            "critiques": [r for r in all_risks if r["niveau"] == "Critique"],
            "eleves": [r for r in all_risks if r["niveau"] == "Élevé"],
            "moyens": [r for r in all_risks if r["niveau"] == "Moyen"],
            "faibles": [r for r in all_risks if r["niveau"] == "Faible"]
        }

        self.logger.info(f"✓ {len(all_risks)} risques identifiés : {len(risques['critiques'])} critiques, "
                        f"{len(risques['eleves'])} élevés, {len(risques['moyens'])} moyens, {len(risques['faibles'])} faibles")

        return risques

    def _analyze_concentration_risks(self, data: dict) -> List[Dict[str, Any]]:
        """Analyse risques de concentration (établissement, juridiction, classe)"""
        risks = []
        total_financier = data["patrimoine"]["financier"]["total"]

        if total_financier == 0:
            return risks

        # Concentration par établissement
        for etab in data["patrimoine"]["financier"]["etablissements"]:
            pct = (etab["total"] / total_financier) * 100

            if pct >= self.seuils.get("concentration_etablissement_critique", 50):
                # Recherche web sur risques concentration
                sources = self.web_researcher.search(
                    "Concentration bancaire",
                    [f"risques concentration bancaire {etab['nom']}",
                     "diversification établissements bancaires France"],
                    context=f"Exposition {pct:.1f}% chez {etab['nom']}"
                )

                risks.append({
                    "id": self._get_risk_id(),
                    "titre": f"Concentration excessive - {etab['nom']}",
                    "description": f"L'établissement {etab['nom']} représente {pct:.1f}% du patrimoine financier, "
                                  f"créant un risque de concentration critique.",
                    "exposition_montant": etab["total"],
                    "exposition_pct": round(pct, 1),
                    "probabilite": "Faible",
                    "impact": "Élevé",
                    "niveau": "Critique",
                    "categorie": "Concentration",
                    "sources_web": sources[:2] if sources else []
                })

            elif pct >= self.seuils.get("concentration_etablissement_eleve", 30):
                risks.append({
                    "id": self._get_risk_id(),
                    "titre": f"Concentration élevée - {etab['nom']}",
                    "description": f"L'établissement {etab['nom']} représente {pct:.1f}% du patrimoine financier.",
                    "exposition_montant": etab["total"],
                    "exposition_pct": round(pct, 1),
                    "probabilite": "Faible",
                    "impact": "Moyen",
                    "niveau": "Élevé",
                    "categorie": "Concentration",
                    "sources_web": []
                })

        # Concentration par juridiction
        juridictions = {}
        for etab in data["patrimoine"]["financier"]["etablissements"]:
            jur = etab.get("juridiction", "Inconnue")
            juridictions[jur] = juridictions.get(jur, 0) + etab["total"]

        for crypto_plat in data["patrimoine"].get("crypto", {}).get("plateformes", []):
            jur = crypto_plat.get("juridiction", "Inconnue")
            juridictions[jur] = juridictions.get(jur, 0) + crypto_plat.get("total", 0)

        total_global = total_financier + data["patrimoine"].get("crypto", {}).get("total", 0)

        for jur, montant in juridictions.items():
            if total_global > 0:
                pct = (montant / total_global) * 100

                if pct >= self.seuils.get("concentration_juridiction_critique", 80):
                    sources = self.web_researcher.search(
                        "Risque pays",
                        [f"risque pays {jur}",
                         f"diversification géographique patrimoine"],
                        context=f"Exposition {pct:.1f}% en {jur}"
                    )

                    risks.append({
                        "id": self._get_risk_id(),
                        "titre": f"Concentration géographique critique - {jur}",
                        "description": f"La juridiction {jur} représente {pct:.1f}% du patrimoine total, "
                                      f"créant un risque pays important.",
                        "exposition_montant": montant,
                        "exposition_pct": round(pct, 1),
                        "probabilite": "Moyenne",
                        "impact": "Élevé",
                        "niveau": "Critique",
                        "categorie": "Concentration géographique",
                        "sources_web": sources[:2] if sources else []
                    })

        return risks

    def _analyze_regulatory_risks(self, data: dict) -> List[Dict[str, Any]]:
        """Analyse risques réglementaires (Loi Sapin 2, garantie dépôts, plafonds)"""
        risks = []
        total_financier = data["patrimoine"]["financier"]["total"]

        # Risque Loi Sapin 2 (Assurance-vie)
        av_total = 0
        for etab in data["patrimoine"]["financier"]["etablissements"]:
            for compte in etab.get("comptes", []):
                if "assurance" in compte.get("type", "").lower() and "vie" in compte.get("type", "").lower():
                    av_total += compte.get("montant", 0)

        if av_total > 0 and total_financier > 0:
            pct_av = (av_total / total_financier) * 100

            # Recherche web sur Loi Sapin 2
            sources = self.web_researcher.search(
                "Loi Sapin 2",
                ["Loi Sapin 2 blocage assurance-vie 2025",
                 "HCSF article 21 Loi Sapin 2",
                 "risques assurance-vie gel rachats"],
                context=f"Exposition AV: {av_total:,.0f}€ ({pct_av:.1f}%)"
            )

            niveau = "Critique" if pct_av >= 25 else "Élevé" if pct_av >= 15 else "Moyen"

            risks.append({
                "id": self._get_risk_id(),
                "titre": "Loi Sapin 2 - Blocage assurance-vie",
                "description": f"Risque de gel temporaire de l'assurance-vie en cas de crise bancaire. "
                              f"Exposition actuelle : {av_total:,.0f}€ ({pct_av:.1f}% du patrimoine financier).",
                "exposition_montant": av_total,
                "exposition_pct": round(pct_av, 1),
                "probabilite": "Faible",
                "impact": "Élevé",
                "niveau": niveau,
                "categorie": "Réglementaire",
                "sources_web": sources[:3] if sources else []
            })

        # Garantie des dépôts (100k€ par établissement)
        sources_garantie = self.web_researcher.search(
            "Garantie dépôts",
            ["garantie dépôts bancaires France 100000 euros",
             "FGDR fonds garantie dépôts résolution"],
            context="Vérification couverture dépôts"
        )

        for etab in data["patrimoine"]["financier"]["etablissements"]:
            depots_total = 0
            for compte in etab.get("comptes", []):
                type_compte = compte.get("type", "").lower()
                if any(x in type_compte for x in ["livret", "dépôt", "compte courant"]):
                    depots_total += compte.get("montant", 0)

            if depots_total > 100000:
                excedent = depots_total - 100000
                pct_non_garanti = (excedent / depots_total) * 100

                risks.append({
                    "id": self._get_risk_id(),
                    "titre": f"Dépassement garantie dépôts - {etab['nom']}",
                    "description": f"Les dépôts chez {etab['nom']} dépassent de {excedent:,.0f}€ "
                                  f"le plafond de garantie de 100 000€.",
                    "exposition_montant": excedent,
                    "exposition_pct": round(pct_non_garanti, 1),
                    "probabilite": "Très faible",
                    "impact": "Élevé",
                    "niveau": "Moyen",
                    "categorie": "Réglementaire",
                    "sources_web": sources_garantie[:1] if sources_garantie else []
                })

        # Plafonds PEA/PEA-PME
        for etab in data["patrimoine"]["financier"]["etablissements"]:
            for compte in etab.get("comptes", []):
                if compte.get("type") == "PEA" and compte.get("montant", 0) > 150000:
                    risks.append({
                        "id": self._get_risk_id(),
                        "titre": "Plafond PEA dépassé",
                        "description": f"Le PEA dépasse le plafond de 150 000€. Nouveaux versements impossibles.",
                        "exposition_montant": compte["montant"] - 150000,
                        "exposition_pct": 0,
                        "probabilite": "N/A",
                        "impact": "Faible",
                        "niveau": "Faible",
                        "categorie": "Réglementaire",
                        "sources_web": []
                    })

        return risks

    def _analyze_fiscal_risks(self, data: dict) -> List[Dict[str, Any]]:
        """Analyse risques fiscaux (PFU, fiscalité AV, IFI)"""
        risks = []

        # Recherche sur évolution fiscalité
        sources_fiscal = self.web_researcher.search(
            "Fiscalité épargne",
            ["PFU prélèvement forfaitaire unique évolution 2025",
             "fiscalité assurance-vie France",
             "flat tax 30% réforme fiscale"],
            context="Anticipation évolutions fiscales"
        )

        # Risque évolution PFU
        total_cto = 0
        for etab in data["patrimoine"]["financier"]["etablissements"]:
            for compte in etab.get("comptes", []):
                if compte.get("type") == "CTO":
                    total_cto += compte.get("montant", 0)

        if total_cto > 50000:
            risks.append({
                "id": self._get_risk_id(),
                "titre": "Risque hausse fiscalité PFU",
                "description": f"Le CTO ({total_cto:,.0f}€) est soumis au PFU de 30%. "
                              f"Risque de hausse fiscale future (ex: 35%).",
                "exposition_montant": total_cto,
                "exposition_pct": 0,
                "probabilite": "Moyenne",
                "impact": "Moyen",
                "niveau": "Moyen",
                "categorie": "Fiscal",
                "sources_web": sources_fiscal[:2] if sources_fiscal else []
            })

        return risks

    def _analyze_market_risks(self, data: dict) -> List[Dict[str, Any]]:
        """Analyse risques de marché (volatilité, change, corrélation, immobilier)"""
        risks = []

        # Exposition actions
        exposition_actions = 0
        for etab in data["patrimoine"]["financier"]["etablissements"]:
            for compte in etab.get("comptes", []):
                if compte.get("type") in ["PEA", "PEA-PME", "CTO"]:
                    exposition_actions += compte.get("montant", 0)
                elif compte.get("type") == "Assurance-vie":
                    # UC sauf fonds euro
                    for fond in compte.get("fonds", []):
                        if "euro" not in fond.get("nom", "").lower():
                            exposition_actions += fond.get("montant", 0)

        total_patrimoine = data["patrimoine"]["financier"]["total"]
        if total_patrimoine > 0:
            pct_actions = (exposition_actions / total_patrimoine) * 100

            if pct_actions > 70:
                sources_marche = self.web_researcher.search(
                    "Risque actions",
                    ["volatilité marchés actions risques",
                     "diversification actions obligations"],
                    context=f"Exposition actions {pct_actions:.1f}%"
                )

                risks.append({
                    "id": self._get_risk_id(),
                    "titre": "Forte exposition au risque actions",
                    "description": f"L'exposition aux actions ({pct_actions:.1f}%) est élevée. "
                                  f"Volatilité et risque de correction important.",
                    "exposition_montant": exposition_actions,
                    "exposition_pct": round(pct_actions, 1),
                    "probabilite": "Moyenne",
                    "impact": "Élevé",
                    "niveau": "Moyen",
                    "categorie": "Marché",
                    "sources_web": sources_marche[:1] if sources_marche else []
                })

        # Risque immobilier - Recherche web sur valorisation actuelle
        immobilier_total = data.get("patrimoine", {}).get("immobilier", {}).get("total", 0)
        biens_immobiliers = data.get("patrimoine", {}).get("immobilier", {}).get("biens", [])

        if immobilier_total > 0 and biens_immobiliers:
            for bien in biens_immobiliers:
                bien_type = bien.get("type", "bien")
                adresse = bien.get("adresse", "")
                valeur = bien.get("valeur_actuelle", 0)

                # Extraire la ville de l'adresse pour la recherche
                ville = ""
                if adresse:
                    # Chercher le code postal (5 chiffres) suivi de la ville
                    match = re.search(r"\d{5}\s+([A-Za-zÀ-ÿ\s-]+)", adresse)
                    if match:
                        ville = match.group(1).strip()

                # Recherche web sur la valorisation immobilière
                if ville:
                    sources_immo = self.web_researcher.search(
                        f"Valorisation immobilière {ville}",
                        [
                            f"prix immobilier m² {ville} 2025",
                            f"marché immobilier {ville} évolution",
                            f"valorisation {bien_type.lower()} {ville}"
                        ],
                        context=f"Bien: {bien_type}, {adresse}, valeur actuelle: {valeur:,.0f}€"
                    )

                    self.logger.info(f"Recherche valorisation immobilière {ville}: {len(sources_immo)} sources")

                    # Ajouter un risque informatif sur le bien immobilier
                    risks.append({
                        "id": self._get_risk_id(),
                        "titre": f"Valorisation {bien_type} - {ville}",
                        "description": f"{bien_type} situé à {adresse}. "
                                      f"Valeur estimée actuelle: {valeur:,.0f}€. "
                                      f"Consulter les sources web pour l'évolution du marché local.",
                        "exposition_montant": valeur,
                        "exposition_pct": round((valeur / (total_patrimoine + immobilier_total)) * 100, 1) if (total_patrimoine + immobilier_total) > 0 else 0,
                        "probabilite": "Faible",
                        "impact": "Moyen",
                        "niveau": "Faible",
                        "categorie": "Marché - Immobilier",
                        "sources_web": sources_immo[:3] if sources_immo else []
                    })

        return risks

    def _analyze_liquidity_risks(self, data: dict) -> List[Dict[str, Any]]:
        """Analyse risques de liquidité (actifs bloqués, immobilier)"""
        risks = []

        # Liquidité disponible
        liquidite = 0
        for etab in data["patrimoine"]["financier"]["etablissements"]:
            for compte in etab.get("comptes", []):
                type_compte = compte.get("type", "").lower()
                if any(x in type_compte for x in ["livret", "dépôt", "compte courant"]):
                    liquidite += compte.get("montant", 0)

        if liquidite < self.seuils.get("liquidite_critique", 5000):
            risks.append({
                "id": self._get_risk_id(),
                "titre": "Liquidité critique",
                "description": f"Liquidité disponible très faible : {liquidite:,.0f}€. "
                              f"Recommandé : minimum 3-6 mois de dépenses.",
                "exposition_montant": liquidite,
                "exposition_pct": 0,
                "probabilite": "N/A",
                "impact": "Élevé",
                "niveau": "Critique",
                "categorie": "Liquidité",
                "sources_web": []
            })
        elif liquidite < self.seuils.get("liquidite_faible", 15000):
            risks.append({
                "id": self._get_risk_id(),
                "titre": "Liquidité faible",
                "description": f"Liquidité disponible limitée : {liquidite:,.0f}€.",
                "exposition_montant": liquidite,
                "exposition_pct": 0,
                "probabilite": "N/A",
                "impact": "Moyen",
                "niveau": "Moyen",
                "categorie": "Liquidité",
                "sources_web": []
            })

        return risks

    def _analyze_political_risks(self, data: dict) -> List[Dict[str, Any]]:
        """Analyse risques politiques (instabilité, nationalisation)"""
        risks = []

        # Risque politique France (si très forte concentration)
        juridictions = {}
        total = data["patrimoine"]["financier"]["total"]

        for etab in data["patrimoine"]["financier"]["etablissements"]:
            jur = etab.get("juridiction", "Inconnue")
            juridictions[jur] = juridictions.get(jur, 0) + etab["total"]

        for jur, montant in juridictions.items():
            if total > 0:
                pct = (montant / total) * 100
                if pct > 90 and jur == "France":
                    # Recherche web sur risque politique France
                    sources = self.web_researcher.search(
                        "Risque politique France",
                        [
                            "risque politique France investissements",
                            "concentration géographique patrimoine France",
                            "diversification internationale patrimoine"
                        ],
                        context=f"Concentration {pct:.1f}% en France"
                    )

                    risks.append({
                        "id": self._get_risk_id(),
                        "titre": "Risque politique concentration France",
                        "description": f"Très forte concentration en France ({pct:.1f}%). "
                                      f"Exposition aux décisions politiques françaises.",
                        "exposition_montant": montant,
                        "exposition_pct": round(pct, 1),
                        "probabilite": "Faible",
                        "impact": "Moyen",
                        "niveau": "Faible",
                        "categorie": "Politique",
                        "sources_web": sources[:3] if sources else []
                    })

        return risks

    def _analyze_currency_risks(self, data: dict) -> List[Dict[str, Any]]:
        """
        Analyse risques de changes (Section 3.2.5.2 du PRD)
        - Risque de transaction
        - Risque de volatilité des devises
        - Risque économique
        """
        risks = []

        # Identifier actifs en devises étrangères
        # 1. Comptes USD (Spiko T-Bonds)
        montant_usd = 0
        for etab in data["patrimoine"]["financier"]["etablissements"]:
            if "spiko" in etab.get("nom", "").lower():
                for compte in etab.get("comptes", []):
                    if "$" in compte.get("type", "").lower() or "usd" in compte.get("type", "").lower():
                        montant_usd += compte.get("montant", 0)

        # 2. Actifs crypto (volatilité devise)
        montant_crypto = data.get("patrimoine", {}).get("crypto", {}).get("total", 0)

        # 3. Immobilier étranger
        montant_immo_etranger = 0
        for bien in data.get("patrimoine", {}).get("immobilier", {}).get("biens", []):
            adresse = bien.get("adresse", "").lower()
            if "france" not in adresse and bien.get("valeur_actuelle", 0) > 0:
                montant_immo_etranger += bien.get("valeur_actuelle", 0)

        total_exposition = montant_usd + montant_crypto + montant_immo_etranger
        total_patrimoine = (
            data.get("patrimoine", {}).get("financier", {}).get("total", 0) +
            data.get("patrimoine", {}).get("crypto", {}).get("total", 0) +
            data.get("patrimoine", {}).get("metaux_precieux", {}).get("total", 0) +
            data.get("patrimoine", {}).get("immobilier", {}).get("total", 0)
        )

        if total_patrimoine > 0:
            pct_exposition = (total_exposition / total_patrimoine) * 100

            # Recherche web sur volatilité EUR/USD et crypto
            if pct_exposition > 3:  # Seuil 3%
                sources = self.web_researcher.search(
                    "Risque de change EUR/USD",
                    [
                        "volatilité EUR USD 2025",
                        "risque de change investissement",
                        "couverture risque devise"
                    ],
                    context=f"Exposition {pct_exposition:.1f}% du patrimoine en devises étrangères"
                )

                # Déterminer niveau de risque
                if pct_exposition >= 20:
                    niveau = "Élevé"
                    probabilite = "Moyenne"
                    impact = "Élevé"
                elif pct_exposition >= 10:
                    niveau = "Moyen"
                    probabilite = "Moyenne"
                    impact = "Moyen"
                else:
                    niveau = "Faible"
                    probabilite = "Faible"
                    impact = "Faible"

                risks.append({
                    "id": self._get_risk_id(),
                    "titre": "Risque de change (EUR/USD et crypto)",
                    "description": f"Exposition à {pct_exposition:.1f}% en devises étrangères "
                                  f"(USD: {montant_usd:,.0f}€, Crypto: {montant_crypto:,.0f}€, "
                                  f"Immobilier étranger: {montant_immo_etranger:,.0f}€). "
                                  f"Risque de perte en cas de dépréciation EUR.",
                    "exposition_montant": total_exposition,
                    "exposition_pct": round(pct_exposition, 1),
                    "probabilite": probabilite,
                    "impact": impact,
                    "niveau": niveau,
                    "categorie": "Change",
                    "sources_web": sources[:2] if sources else []
                })

        return risks

    def _get_risk_id(self) -> str:
        """Génère un ID unique pour un risque"""
        risk_id = f"RISK_{self.risk_id_counter:03d}"
        self.risk_id_counter += 1
        return risk_id
