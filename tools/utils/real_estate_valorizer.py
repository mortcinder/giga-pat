"""
Extracteur de prix immobilier au m² depuis résultats de recherches web.

Utilise les résultats des recherches Brave API pour extraire le prix moyen au m²
et calculer la valorisation actuelle d'un bien immobilier.
"""

import re
import logging
from typing import Dict, Any, Optional, List


class RealEstateValorizer:
    """Extrait les prix immobiliers depuis les résultats de recherches web"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Données de fallback par ville (prix au m² moyen 2025)
        # Source : données moyennes du marché immobilier français
        self.fallback_prices = {
            "nanterre": 5300,      # Hauts-de-Seine, proche Paris
            "paris": 10500,
            "lyon": 5800,
            "marseille": 4200,
            "toulouse": 4000,
            "bordeaux": 4500,
            "nice": 5500,
            "strasbourg": 3800,
            "lille": 3600,
            "rennes": 4100,
            "default": 3500  # Prix moyen national
        }

    def extract_price_per_m2(self, city: str, web_sources: List[Dict[str, str]]) -> Optional[float]:
        """
        Extrait le prix au m² depuis les résultats de recherches web.

        Args:
            city: Nom de la ville
            web_sources: Liste des sources web retournées par Brave API
                         Format: [{"titre": "...", "url": "...", "snippet": "..."}]

        Returns:
            Prix au m² moyen (float) ou None si extraction échoue
        """
        if not web_sources:
            self.logger.warning(f"Aucune source web disponible pour {city}, utilisation fallback")
            return self._get_fallback_price(city)

        # Patterns de détection de prix au m²
        patterns = [
            r"(\d[\d\s]*)\s*€\s*/\s*m[²2]",           # "5 300 €/m²" ou "5300 €/m2"
            r"(\d[\d\s]*)\s*euros?\s*/\s*m[²2]",      # "5 300 euros/m²"
            r"prix\s+(?:moyen|médian)\s*:\s*(\d[\d\s]*)\s*€",  # "prix moyen : 5 300 €"
            r"(\d[\d\s]*)\s*€.*m[²2]",                # "5 300 € le m²"
        ]

        extracted_prices = []

        # Parcourir toutes les sources web
        for source in web_sources:
            snippet = source.get("snippet", "") + " " + source.get("titre", "")

            for pattern in patterns:
                matches = re.findall(pattern, snippet, re.IGNORECASE)
                for match in matches:
                    try:
                        # Nettoyer et convertir
                        price_str = match.replace(" ", "").replace("\u00a0", "")
                        price = float(price_str)

                        # Filtrer les valeurs aberrantes (entre 1000 et 20000 €/m²)
                        if 1000 <= price <= 20000:
                            extracted_prices.append(price)
                            self.logger.debug(f"Prix extrait depuis '{source.get('titre', 'source')}': {price} €/m²")
                    except (ValueError, AttributeError) as e:
                        self.logger.debug(f"Erreur parsing prix '{match}': {e}")
                        continue

        if extracted_prices:
            # Retourner la médiane des prix extraits (plus robuste que la moyenne)
            sorted_prices = sorted(extracted_prices)
            median_price = sorted_prices[len(sorted_prices) // 2]
            self.logger.info(f"Prix extrait web pour {city}: {median_price} €/m² (sur {len(extracted_prices)} valeurs)")
            return median_price
        else:
            self.logger.warning(f"Aucun prix extractible depuis web pour {city}, utilisation fallback")
            return self._get_fallback_price(city)

    def _get_fallback_price(self, city: str) -> float:
        """Retourne un prix de fallback basé sur la ville"""
        city_normalized = city.lower().strip()

        # Chercher correspondance exacte
        if city_normalized in self.fallback_prices:
            price = self.fallback_prices[city_normalized]
            self.logger.info(f"Prix fallback pour {city}: {price} €/m²")
            return price

        # Chercher correspondance partielle
        for known_city, price in self.fallback_prices.items():
            if known_city in city_normalized or city_normalized in known_city:
                self.logger.info(f"Prix fallback pour {city} (match partiel '{known_city}'): {price} €/m²")
                return price

        # Fallback par défaut
        default_price = self.fallback_prices["default"]
        self.logger.info(f"Prix fallback par défaut pour {city}: {default_price} €/m²")
        return default_price

    def calculate_property_value(
        self,
        surface_m2: float,
        city: str,
        web_sources: List[Dict[str, str]],
        acquisition_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calcule la valorisation actuelle d'un bien immobilier.

        Args:
            surface_m2: Surface en m²
            city: Nom de la ville
            web_sources: Sources web de l'API Brave
            acquisition_price: Prix d'acquisition (optionnel, pour comparaison)

        Returns:
            Dict avec: valeur_actuelle, prix_m2, source (web/fallback), plus_value_pct
        """
        prix_m2 = self.extract_price_per_m2(city, web_sources)
        valeur_actuelle = round(surface_m2 * prix_m2, 2)

        result = {
            "valeur_actuelle": valeur_actuelle,
            "prix_m2": prix_m2,
            "source": "web" if web_sources and len(web_sources) > 0 else "fallback",
            "nb_sources_web": len(web_sources) if web_sources else 0
        }

        # Calculer la plus-value si prix d'acquisition fourni
        if acquisition_price and acquisition_price > 0:
            plus_value = valeur_actuelle - acquisition_price
            plus_value_pct = (plus_value / acquisition_price) * 100
            result["plus_value"] = round(plus_value, 2)
            result["plus_value_pct"] = round(plus_value_pct, 1)

        self.logger.info(
            f"Valorisation calculée : {surface_m2}m² × {prix_m2}€/m² = {valeur_actuelle}€ "
            f"(source: {result['source']})"
        )

        return result
