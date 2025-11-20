"""
Extracteur de prix immobilier au m² depuis résultats de recherches web.

Utilise les résultats des recherches web (snippets) puis fallback sur WebFetch
pour extraire le prix moyen au m² et calculer la valorisation actuelle d'un bien.

Architecture hybride (v2.2):
1. Tentative extraction depuis snippets (rapide)
2. Si échec, WebFetch sur URLs prioritaires (MeilleursAgents, Figaro, SeLoger)
3. Si échec, prix fallback par ville
"""

import re
import logging
import requests
import html
from typing import Dict, Any, Optional, List


class RealEstateValorizer:
    """Extrait les prix immobiliers depuis les résultats de recherches web"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Sites de référence pour le scoring (bonus de qualité)
        # Ces sites sont connus pour avoir des données fiables et une structure HTML exploitable
        self.reference_domains = [
            "meilleursagents.com",
            "lefigaro.fr",
            "seloger.com",
            "pap.fr",
            "bien-ici.com",
            "logic-immo.com",
            "orpi.com"
        ]

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
        for idx, source in enumerate(web_sources, 1):
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
            self.logger.info(f"Prix extrait depuis snippets pour {city}: {median_price} €/m² (sur {len(extracted_prices)} valeurs)")
            return median_price
        else:
            self.logger.debug(f"Aucun prix dans les snippets, tentative extraction HTML depuis URLs prioritaires")
            # Fallback : tenter extraction depuis HTML complet
            html_price = self._extract_from_html(city, web_sources)
            if html_price:
                return html_price
            else:
                self.logger.warning(f"Aucun prix extractible depuis web (snippets + HTML) pour {city}, utilisation fallback")
                return self._get_fallback_price(city)

    def _score_url_priority(self, url: str, title: str = "") -> int:
        """
        Score une URL pour déterminer sa priorité d'extraction.

        Critères objectifs:
        - Sites de référence immobiliers (+10)
        - HTTPS (+5)
        - URL principale courte (+3)
        - Titre contenant "prix" ou "m²" (+2)

        Args:
            url: URL de la source
            title: Titre de la page (optionnel)

        Returns:
            Score de priorité (plus élevé = plus prioritaire)
        """
        score = 0

        # 1. Sites de référence connus pour données fiables
        url_lower = url.lower()
        for domain in self.reference_domains:
            if domain in url_lower:
                score += 10
                break

        # 2. Préférer HTTPS (sécurité et sites modernes)
        if url.startswith("https://"):
            score += 5

        # 3. Préférer URLs courtes (page principale vs sous-pages)
        # Exemples:
        #   - https://meilleursagents.com/prix-immobilier/nanterre-92000/ → courte (bon)
        #   - https://site.com/estimation/details/quartier/rue/batiment/... → longue (moins bon)
        if len(url) < 100:
            score += 3
        elif len(url) < 150:
            score += 1

        # 4. Titre pertinent contenant mots-clés prix immobilier
        if title:
            title_lower = title.lower()
            if "prix" in title_lower or "m²" in title_lower or "m2" in title_lower:
                score += 2
            if "estimation" in title_lower or "valorisation" in title_lower:
                score += 1

        return score

    def _extract_domain(self, url: str) -> str:
        """
        Extrait le nom de domaine depuis une URL.

        Args:
            url: URL complète

        Returns:
            Nom de domaine (ex: "meilleursagents.com")
        """
        try:
            # Extraire le domaine entre "://" et le premier "/"
            if "://" in url:
                domain_part = url.split("://")[1].split("/")[0]
                # Retirer www. si présent
                if domain_part.startswith("www."):
                    domain_part = domain_part[4:]
                return domain_part
            return url
        except (IndexError, AttributeError):
            return url

    def _extract_from_html(self, city: str, web_sources: List[Dict[str, str]]) -> Optional[float]:
        """
        Extrait le prix au m² depuis le HTML complet des URLs triées par score de priorité.

        Fallback hybride (v2.2) : si snippets vides, fetch HTML des meilleures sources.

        Tri intelligent basé sur:
        - Sites de référence immobiliers
        - Qualité de l'URL (HTTPS, longueur)
        - Pertinence du titre

        Args:
            city: Nom de la ville
            web_sources: Liste des sources avec URLs

        Returns:
            Prix au m² médian ou None si échec
        """
        if not web_sources:
            return None

        # Scorer et trier toutes les sources par priorité décroissante
        scored_sources = []
        for source in web_sources:
            url = source.get("url", "")
            title = source.get("titre", "")
            score = self._score_url_priority(url, title)
            scored_sources.append({
                "url": url,
                "title": title,
                "score": score,
                "domain": self._extract_domain(url)
            })

        # Trier par score décroissant
        scored_sources.sort(key=lambda x: x["score"], reverse=True)

        # Log des meilleures sources pour transparence (DEBUG)
        top_3 = scored_sources[:3]
        self.logger.debug(
            f"Top 3 sources pour {city}: " +
            ", ".join([f"{s['domain']} (score: {s['score']})" for s in top_3])
        )

        # Patterns HTML plus agressifs (contenu complet de page)
        # Important : capturer TOUS les chiffres contigus, même avec séparateurs
        html_patterns = [
            r'(\d[\d\s,\.]*?)\s*€\s*/\s*m[²2]',                   # "5 300 €/m²", "5,300 €/m²" (non-greedy)
            r'(\d+(?:[\s,\.]\d{3})*)\s*€\s*/\s*m[²2]',            # "5 300 €/m²" (milliers explicites)
            r'(\d[\d\s,\.]*?)\s*euros?\s*/\s*m[²2]',              # "5 300 euros/m²"
            r'prix[^0-9]*?(\d+(?:[\s,\.]\d{3})*)\s*€',            # "prix moyen 5 300 €"
            r'm[²2][^0-9]*?(\d+(?:[\s,\.]\d{3})*)\s*€',           # "m² : 5 300 €"
            r'(\d+(?:[\s,\.]\d{3})*)\s*€[^0-9/]*?m[²2]',          # "5 300 € le m²" ou "5 300 €m²"
            r'prix.*?moyen.*?:?\s*(\d+(?:[\s,\.]\d{3})*)\s*€',    # "Prix moyen: 5300€"
        ]

        extracted_prices = []

        # Essayer jusqu'à 3 URLs avec le meilleur score
        for source in scored_sources[:3]:
            url = source["url"]
            domain = source["domain"]
            try:
                response = requests.get(url, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })

                if response.status_code != 200:
                    self.logger.debug(f"HTTP {response.status_code} pour {domain}")
                    continue

                html_content = response.text

                # Convertir les entités HTML (&nbsp; → espace, &euro; → €, etc.)
                html_content = html.unescape(html_content)

                # Essayer tous les patterns
                for pattern in html_patterns:
                    matches = re.findall(pattern, html_content, re.IGNORECASE)
                    for match in matches:
                        try:
                            # Nettoyer : espaces, virgules, points (sauf décimaux)
                            price_str = match.replace(" ", "").replace("\u00a0", "").replace(",", "")
                            # Gérer les points (5.300 → 5300, mais 5.3 → 5.3)
                            if "." in price_str:
                                parts = price_str.split(".")
                                if len(parts[-1]) == 3:  # milliers : 5.300
                                    price_str = price_str.replace(".", "")

                            price = float(price_str)

                            # Filtrer valeurs aberrantes
                            if 1000 <= price <= 20000:
                                extracted_prices.append(price)
                        except (ValueError, AttributeError, IndexError):
                            continue

                # Si on a trouvé des prix, pas besoin d'essayer d'autres URLs
                if extracted_prices:
                    break

            except requests.RequestException as e:
                self.logger.debug(f"Erreur HTTP pour {domain}: {e}")
                continue

        if extracted_prices:
            # Retourner la médiane
            sorted_prices = sorted(extracted_prices)
            median_price = sorted_prices[len(sorted_prices) // 2]
            self.logger.info(f"Prix extrait HTML pour {city}: {median_price} €/m² (sur {len(extracted_prices)} valeurs)")
            return median_price

        return None

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
