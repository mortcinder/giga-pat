"""
Module de génération de recommandations
Suit les spécifications des sections 3.2.5.3 et 15 du PRD
"""

import logging
from typing import Dict, List, Any


class Recommender:
    """
    Génère des recommandations prioritisées basées sur les risques
    Section 3.2.5.3 et 15 du PRD
    """

    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.reco_id_counter = 1

    def generate(self, data: dict, risques: dict) -> Dict[str, List[Dict]]:
        """
        Génère recommandations prioritisées à partir des risques identifiés
        Formule de score : (criticité × 0.4) + (impact × 0.3) + (facilité × 0.3)
        """
        self.logger.info("Génération recommandations...")

        all_recommendations = []

        # Générer recommandations pour risques critiques et élevés
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

        # Concentration établissement
        if "Concentration" in categorie and "établissement" not in categorie.lower():
            recommendations.append({
                "id": self._get_reco_id(),
                "titre": f"Diversifier hors {titre_risque.split(' - ')[-1] if ' - ' in titre_risque else 'établissement principal'}",
                "description": f"Transférer une partie des actifs vers d'autres établissements pour réduire le risque de concentration.",
                "benefice": f"Réduction exposition de {risque['exposition_pct']:.1f}% à ~40%",
                "montant": risque["exposition_montant"] * 0.3,  # Suggérer transfert 30%
                "delai_jours": 60,
                "difficulte": "Moyenne",
                "actions_concretes": [
                    "Ouvrir compte chez nouvel établissement",
                    f"Transférer {risque['exposition_montant'] * 0.3:,.0f}€",
                    "Suivre évolution répartition"
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

        # Concentration géographique
        elif "Concentration géographique" in titre_risque:
            recommendations.append({
                "id": self._get_reco_id(),
                "titre": "Diversifier géographiquement",
                "description": f"Investir hors {titre_risque.split(' - ')[-1]} via ETF World/internationaux.",
                "benefice": f"Réduction risque pays de {risque['exposition_pct']:.1f}%",
                "montant": risque["exposition_montant"] * 0.15,
                "delai_jours": 90,
                "difficulte": "Moyenne",
                "actions_concretes": [
                    "Sélectionner ETF World/USA/Émergents",
                    "Investir progressivement",
                    "Rééquilibrer annuellement"
                ],
                "risques_mitigues": [risque["id"]],
                "score_criticite": self._niveau_to_score(risque["niveau"]),
                "score_impact": self._pct_to_impact_score(risque["exposition_pct"]),
                "score_facilite": 6
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

    def _get_reco_id(self) -> str:
        """Génère un ID unique pour une recommandation"""
        reco_id = f"REC_{self.reco_id_counter:03d}"
        self.reco_id_counter += 1
        return reco_id
