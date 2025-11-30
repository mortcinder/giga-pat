"""
Module de recherche web via Brave Search API
Suit les spécifications des sections 3.2.5.5 et 14 du PRD

NOTE: Cette implémentation utilise l'API Brave Search pour effectuer
des recherches web réelles et retourner des sources vérifiables.
"""

import os
import logging
import time
import random
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime


class WebResearcher:
    """
    Gère les recherches web avec citation des sources
    Section 3.2.5.5 du PRD
    """

    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.history = []
        self.max_retries = (
            config.get("analyzer", {}).get("web_research", {}).get("retry_count", 3)
        )
        self.timeout = (
            config.get("analyzer", {})
            .get("web_research", {})
            .get("timeout_seconds", 30)
        )
        self.enabled = (
            config.get("analyzer", {}).get("web_research", {}).get("enabled", True)
        )

        # Charger la clé API Brave depuis l'environnement
        self.api_key = os.environ.get("BRAVE_API_KEY")
        if self.enabled and not self.api_key:
            self.logger.error("BRAVE_API_KEY non définie - Recherches web désactivées")
            self.enabled = False

        if not self.enabled:
            self.logger.warning("Recherches web désactivées par configuration")

        # API Brave Search endpoint
        self.api_url = "https://api.search.brave.com/res/v1/web/search"

        # Session HTTP avec pooling de connexions
        self.session = requests.Session()
        self.session.verify = True  # SSL verification explicite

    def search(
        self, sujet: str, queries: List[str], context: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Effectue plusieurs recherches web sur un sujet

        Args:
            sujet: Thème général de recherche
            queries: Liste de requêtes à exécuter
            context: Contexte additionnel pour affiner la recherche

        Returns:
            Liste de sources avec URL, titre, extrait, pertinence
        """
        if not self.enabled:
            self.logger.info(
                f"Recherches web désactivées, skip {len(queries)} requêtes"
            )
            return []

        self.logger.info(f"Recherches sur : {sujet} ({len(queries)} requêtes)")
        all_sources = []

        for i, query in enumerate(queries, 1):
            self.logger.info(f"  [{i}/{len(queries)}] {query}")

            sources = self._search_single(query, context)
            all_sources.extend(sources)

            self.history.append(
                {
                    "sujet": sujet,
                    "query": query,
                    "date": datetime.now().isoformat(),
                    "sources_found": len(sources),
                }
            )

            self.logger.debug(f"    → {len(sources)} sources")

            # Rate limiting Brave API: 1.1-1.5 secondes entre requêtes (section 3.2.5.5)
            if i < len(queries):  # Pas de sleep après la dernière requête
                wait_time = random.uniform(1.1, 1.5)
                time.sleep(wait_time)

        # Dédoublonnage par URL
        unique_sources = []
        seen_urls = set()
        for source in all_sources:
            url = source.get("url", "")
            if url and url not in seen_urls:
                unique_sources.append(source)
                seen_urls.add(url)

        self.logger.info(f"  Total : {len(unique_sources)} sources uniques")
        return unique_sources

    def _search_single(self, query: str, context: str = "") -> List[Dict[str, Any]]:
        """
        Effectue une recherche web unique via Brave Search API avec retry logic
        Section 14.3 du PRD
        """
        for attempt in range(self.max_retries):
            try:
                # Appel API Brave Search
                sources = self._call_brave_api(query, context)
                return sources

            except requests.exceptions.Timeout:
                if attempt == self.max_retries - 1:
                    self.logger.error(
                        f"Timeout après {self.max_retries} tentatives: {query}"
                    )
                    return []

                wait_time = 2**attempt  # Exponential backoff: 1s, 2s, 4s
                self.logger.warning(
                    f"Timeout tentative {attempt + 1}, retry dans {wait_time}s..."
                )
                time.sleep(wait_time)

            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    self.logger.error(
                        f"Échec recherche après {self.max_retries} tentatives: {query} - {e}"
                    )
                    return []

                wait_time = 2**attempt
                self.logger.warning(
                    f"Erreur tentative {attempt + 1}, retry dans {wait_time}s..."
                )
                time.sleep(wait_time)

            except Exception as e:
                self.logger.error(f"Erreur inattendue lors de la recherche: {query} - {e}")
                return []

        return []

    def _call_brave_api(self, query: str, context: str = "") -> List[Dict[str, Any]]:
        """
        Appelle l'API Brave Search et retourne les sources formatées
        Documentation: https://api.search.brave.com/app/documentation/web-search/get-started
        """
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key
        }

        params = {
            "q": query,
            "count": 10,  # Nombre de résultats (max 20)
            "search_lang": "fr",  # Langue de recherche
            "country": "FR",  # Pays
            "text_decorations": False,
            "spellcheck": True
        }

        try:
            self.logger.debug(f"Appel Brave API: {query}")
            response = self.session.get(
                self.api_url,
                headers=headers,
                params=params,
                timeout=self.timeout,
                verify=True  # SSL verification explicite
            )

            # Vérifier le code de réponse
            if response.status_code == 401:
                self.logger.error("Clé API Brave invalide (401 Unauthorized)")
                return []
            elif response.status_code == 429:
                self.logger.warning("Rate limit Brave atteint (429 Too Many Requests)")
                raise requests.exceptions.RequestException("Rate limit exceeded")
            elif response.status_code != 200:
                self.logger.error(f"Erreur API Brave: {response.status_code} - {response.text}")
                return []

            # Parser la réponse JSON
            data = response.json()
            return self._parse_brave_response(data, query)

        except requests.exceptions.Timeout:
            self.logger.warning(f"Timeout API Brave pour: {query}")
            raise
        except requests.exceptions.RequestException as e:
            # Sanitize error message - ne jamais exposer l'API key
            error_msg = str(e)
            if self.api_key and self.api_key in error_msg:
                error_msg = error_msg.replace(self.api_key, "[REDACTED]")

            self.logger.error(f"Erreur requête Brave API: {error_msg}")
            raise
        except Exception as e:
            self.logger.error(f"Erreur parsing réponse Brave: {e}")
            return []

    def _parse_brave_response(self, data: dict, query: str) -> List[Dict[str, Any]]:
        """
        Parse la réponse Brave Search et extrait les sources
        Format Brave: {web: {results: [{url, title, description, ...}]}}
        """
        sources = []
        date_today = datetime.now().strftime("%Y-%m-%d")

        # Extraire les résultats web
        web_results = data.get("web", {}).get("results", [])

        for result in web_results[:5]:  # Limiter à 5 sources par requête
            url = result.get("url", "")
            title = result.get("title", "")
            description = result.get("description", "")

            if not url or not title:
                continue

            # Déterminer la pertinence basée sur la position
            position = len(sources) + 1
            if position <= 2:
                pertinence = "Haute"
            elif position <= 4:
                pertinence = "Moyenne"
            else:
                pertinence = "Faible"

            source = {
                "url": url,
                "titre": title,
                "extrait": description[:300],  # Limiter la longueur
                "pertinence": pertinence,
                "date_acces": date_today
            }

            sources.append(source)
            self.logger.debug(f"  Source: {title[:50]}...")

        return sources

    def _simulate_web_search(
        self, query: str, context: str = ""
    ) -> List[Dict[str, Any]]:
        """
        SIMULATION de recherche web pour tests
        À REMPLACER par une vraie API de recherche (Google, Bing, etc.)

        Cette fonction génère des sources réalistes basées sur les mots-clés
        de la requête pour permettre de tester le système complet.
        """
        sources = []
        query_lower = query.lower()
        date_today = datetime.now().strftime("%Y-%m-%d")

        # Base de données simulée de sources selon les sujets du PRD (section 3.2.5.5)
        if "loi sapin" in query_lower or "sapin 2" in query_lower:
            sources.append(
                {
                    "url": "https://www.economie.gouv.fr/hcsf/loi-sapin-2-article-21",
                    "titre": "HCSF - Article 21 de la Loi Sapin 2",
                    "extrait": "Le Haut Conseil de Stabilité Financière peut, en cas de circonstances exceptionnelles, suspendre temporairement les rachats d'assurance-vie pour préserver la stabilité du système financier.",
                    "pertinence": "Haute",
                    "date_acces": date_today,
                }
            )
            sources.append(
                {
                    "url": "https://www.amf-france.org/fr/reglementation/loi-sapin-2",
                    "titre": "AMF - Dispositifs de la loi Sapin 2",
                    "extrait": "La loi Sapin 2 de 2016 renforce les pouvoirs du HCSF notamment concernant les mesures macroprudentielles et la protection de l'épargne.",
                    "pertinence": "Haute",
                    "date_acces": date_today,
                }
            )

        elif "garantie" in query_lower and "dépôt" in query_lower:
            sources.append(
                {
                    "url": "https://www.garantiedesdepots.fr/",
                    "titre": "Fonds de Garantie des Dépôts et de Résolution",
                    "extrait": "La garantie des dépôts protège les épargnants à hauteur de 100 000 € par déposant et par établissement en cas de défaillance bancaire.",
                    "pertinence": "Haute",
                    "date_acces": date_today,
                }
            )

        elif (
            "pfu" in query_lower
            or "flat tax" in query_lower
            or "fiscalité" in query_lower
        ):
            sources.append(
                {
                    "url": "https://www.service-public.fr/particuliers/vosdroits/F2329",
                    "titre": "Service Public - Prélèvement Forfaitaire Unique",
                    "extrait": "Le PFU (flat tax) s'applique au taux de 30% sur les revenus de capitaux mobiliers : 12,8% d'impôt et 17,2% de prélèvements sociaux.",
                    "pertinence": "Haute",
                    "date_acces": date_today,
                }
            )

        elif "pea" in query_lower:
            sources.append(
                {
                    "url": "https://www.amf-france.org/fr/espace-epargnants/comprendre-les-produits-depargne/supports-dinvestissement/plan-depargne-en-actions-pea",
                    "titre": "AMF - Le Plan d'Épargne en Actions (PEA)",
                    "extrait": "Le PEA permet d'investir en actions européennes avec une exonération d'impôt sur les plus-values après 5 ans de détention. Plafond de versement : 150 000 €.",
                    "pertinence": "Haute",
                    "date_acces": date_today,
                }
            )

        elif "assurance vie" in query_lower or "assurance-vie" in query_lower:
            sources.append(
                {
                    "url": "https://www.service-public.fr/particuliers/vosdroits/F15274",
                    "titre": "Service Public - Fiscalité de l'assurance vie",
                    "extrait": "L'assurance-vie bénéficie d'une fiscalité avantageuse : abattement annuel de 4 600 € (9 200 € pour un couple) sur les rachats après 8 ans.",
                    "pertinence": "Haute",
                    "date_acces": date_today,
                }
            )

        elif (
            "etf" in query_lower or "vwce" in query_lower or "msci world" in query_lower
        ):
            sources.append(
                {
                    "url": "https://www.morningstar.fr/fr/etf/",
                    "titre": "Morningstar - Analyse des ETF",
                    "extrait": "Les ETF (Exchange Traded Funds) permettent une diversification large à faible coût. Les ETF World offrent une exposition à plus de 1500 actions mondiales.",
                    "pertinence": "Haute",
                    "date_acces": date_today,
                }
            )

        elif "inflation" in query_lower or "bce" in query_lower:
            sources.append(
                {
                    "url": "https://www.ecb.europa.eu/",
                    "titre": "BCE - Politique monétaire et inflation",
                    "extrait": "La Banque Centrale Européenne vise un objectif d'inflation de 2% à moyen terme. Les taux directeurs influencent les conditions de crédit et l'épargne.",
                    "pertinence": "Haute",
                    "date_acces": date_today,
                }
            )

        elif "risque" in query_lower or "diversification" in query_lower:
            sources.append(
                {
                    "url": "https://www.amf-france.org/fr/espace-epargnants/comprendre-les-risques",
                    "titre": "AMF - Comprendre les risques financiers",
                    "extrait": "La diversification est un principe clé de gestion : ne pas mettre tous ses œufs dans le même panier. Elle permet de réduire le risque spécifique.",
                    "pertinence": "Haute",
                    "date_acces": date_today,
                }
            )

        # Si aucune correspondance, retourner une source générique
        if not sources:
            sources.append(
                {
                    "url": f"https://www.recherche-exemple.fr/{query.replace(' ', '-')}",
                    "titre": f"Recherche sur : {query}",
                    "extrait": f"Informations concernant {query}. [Source simulée - À remplacer par vraie API de recherche]",
                    "pertinence": "Moyenne",
                    "date_acces": date_today,
                }
            )

        return sources

    def get_history(self) -> List[Dict[str, Any]]:
        """Retourne l'historique des recherches effectuées"""
        return self.history

    def get_search_count(self) -> int:
        """Retourne le nombre total de recherches effectuées"""
        return len(self.history)
