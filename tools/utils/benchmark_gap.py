"""
Module de calcul d'écart aux benchmarks d'allocation
Compare la pondération réelle d'une classe d'actifs à son benchmark cible
"""

import logging
from typing import Dict, Any, Optional


class BenchmarkGapCalculator:
    """
    Calcule l'écart entre l'allocation réelle et le benchmark cible
    pour chaque classe d'actifs selon le profil d'investisseur
    """

    def __init__(self, config: dict, active_profile: str):
        """
        Initialise le calculateur avec la configuration des benchmarks

        Args:
            config: Configuration complète depuis analysis.yaml
            active_profile: Profil actif (default/dynamique/equilibre/prudent)
        """
        self.logger = logging.getLogger(__name__)
        self.active_profile = active_profile

        # Charger les benchmarks du profil actif
        all_benchmarks = config.get("benchmarks", {})
        self.benchmarks = all_benchmarks.get(active_profile, all_benchmarks.get("default", {}))

        self.logger.info(f"BenchmarkGapCalculator initialisé avec profil: {active_profile}")

    def calculate_gap(self, classe: str, poids_reel: float) -> Dict[str, Any]:
        """
        Calcule l'écart entre le poids réel et le benchmark cible

        Args:
            classe: Nom de la classe d'actifs (ex: "Actions", "Obligations")
            poids_reel: Poids réel en % du patrimoine total

        Returns:
            Dict avec:
                - ecart_pct: Écart en points de % par rapport à la cible
                - ecart_borne: Écart par rapport aux bornes (0 si dans la fourchette)
                - status: "dans_la_cible", "sous_pondere_modere", "sur_pondere_modere",
                         "sous_pondere_fort", "sur_pondere_fort"
                - niveau: "normal", "attention", "alerte"
                - message: Description textuelle
        """
        benchmark = self.benchmarks.get(classe)

        # Si pas de benchmark pour cette classe, retour neutre
        if not benchmark:
            return {
                "ecart_pct": 0.0,
                "ecart_borne": 0.0,
                "status": "pas_de_benchmark",
                "niveau": "normal",
                "message": "Pas de benchmark défini"
            }

        min_pct = benchmark.get("min", 0)
        target_pct = benchmark.get("target", (min_pct + benchmark.get("max", 100)) / 2)
        max_pct = benchmark.get("max", 100)

        # Calcul de l'écart par rapport à la cible
        ecart_cible = poids_reel - target_pct

        # Calcul de l'écart par rapport aux bornes
        if poids_reel < min_pct:
            ecart_borne = poids_reel - min_pct  # Négatif = sous-pondération
        elif poids_reel > max_pct:
            ecart_borne = poids_reel - max_pct  # Positif = sur-pondération
        else:
            ecart_borne = 0.0  # Dans la fourchette

        # Détermination du status et du niveau
        status, niveau, message = self._determine_status(
            ecart_cible, ecart_borne, min_pct, target_pct, max_pct, classe
        )

        return {
            "ecart_pct": round(ecart_cible, 2),
            "ecart_borne": round(ecart_borne, 2),
            "status": status,
            "niveau": niveau,
            "message": message
        }

    def _determine_status(
        self,
        ecart_cible: float,
        ecart_borne: float,
        min_pct: float,
        target_pct: float,
        max_pct: float,
        classe: str
    ) -> tuple[str, str, str]:
        """
        Détermine le status, niveau et message selon l'écart

        Returns:
            (status, niveau, message)
        """
        # Dans la fourchette acceptable
        if ecart_borne == 0:
            if abs(ecart_cible) <= 2.0:
                return (
                    "dans_la_cible",
                    "normal",
                    f"Dans la cible ({target_pct}%)"
                )
            elif ecart_cible < 0:
                return (
                    "sous_pondere_modere",
                    "normal",
                    f"Légèrement sous-pondéré ({abs(ecart_cible):.1f} pts sous la cible)"
                )
            else:
                return (
                    "sur_pondere_modere",
                    "normal",
                    f"Légèrement sur-pondéré ({ecart_cible:.1f} pts au-dessus de la cible)"
                )

        # Hors de la fourchette
        if ecart_borne < 0:
            # Sous-pondération
            if abs(ecart_borne) >= 10:
                return (
                    "sous_pondere_fort",
                    "alerte",
                    f"Fortement sous-pondéré ({abs(ecart_borne):.1f} pts sous le minimum {min_pct}%)"
                )
            else:
                return (
                    "sous_pondere_modere",
                    "attention",
                    f"Sous-pondéré ({abs(ecart_borne):.1f} pts sous le minimum {min_pct}%)"
                )
        else:
            # Sur-pondération
            if ecart_borne >= 10:
                return (
                    "sur_pondere_fort",
                    "alerte",
                    f"Fortement sur-pondéré ({ecart_borne:.1f} pts au-dessus du maximum {max_pct}%)"
                )
            else:
                return (
                    "sur_pondere_modere",
                    "attention",
                    f"Sur-pondéré ({ecart_borne:.1f} pts au-dessus du maximum {max_pct}%)"
                )

    def calculate_all_gaps(self, repartition_classes: list) -> list:
        """
        Calcule les écarts pour toutes les classes d'actifs

        Args:
            repartition_classes: Liste des classes d'actifs avec leurs poids
                Format: [{"type_actif": "Actions", "pourcentage": 65.2, ...}, ...]

        Returns:
            Liste enrichie avec les données d'écart benchmark
        """
        enriched_classes = []

        for classe_data in repartition_classes:
            classe_name = classe_data.get("type_actif", "")
            poids_reel = classe_data.get("pourcentage", 0.0)

            gap_data = self.calculate_gap(classe_name, poids_reel)

            # Enrichir les données de la classe
            enriched_data = {**classe_data}
            enriched_data["benchmark_gap"] = gap_data

            enriched_classes.append(enriched_data)

        return enriched_classes
