"""
Module de génération du rapport HTML
Suit les spécifications de la section 3.3 du PRD
"""

import html
import json
import logging
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
from bs4 import BeautifulSoup


class ReportGenerator:
    """
    Génère le rapport HTML depuis l'analyse
    Section 3.3 du PRD
    """

    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)

    def generate(self, analysis_data: dict, timestamp: str) -> str:
        """Génère le rapport HTML"""
        self.logger.info("Début génération HTML...")

        # 1. Load template
        self.logger.info("Chargement template...")
        template_path = (
            Path(self.config["paths"]["templates"])
            / self.config["generator"]["template_file"]
        )

        if not template_path.exists():
            raise FileNotFoundError(f"Template introuvable : {template_path}")

        template_html = template_path.read_text(encoding="utf-8")
        soup = BeautifulSoup(template_html, "lxml")

        # 1.5. Inline CSS
        self.logger.info("Incorporation du CSS...")
        self._inline_css(soup)

        # 2. Inject simple fields
        self.logger.info("Injection données...")
        self._inject_simple_fields(soup, analysis_data)

        # 3. Inject repeated rows
        self._inject_repeated_rows(soup, analysis_data)

        # 4. Inject chart data
        self._inject_chart_data(soup, analysis_data)

        # 5. Save with timestamp
        output_filename = f"{self.config['generator']['output_prefix']}{timestamp}.html"
        output_path = Path(self.config["paths"]["generated"]) / output_filename

        self.logger.info(f"Sauvegarde {output_path}...")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(str(soup), encoding="utf-8")

        self.logger.info("✓ Génération terminée")
        return str(output_path)

    def _inject_simple_fields(self, soup: BeautifulSoup, data: dict):
        """
        Injecte les champs simples [data-field]
        Section 16.1 du PRD
        """
        # Mapping des champs selon section 3.3.5
        mappings = {
            # Dates
            "date_rapport": (lambda d: datetime.now().strftime("%d %B %Y"), None),
            "report_date": (lambda d: datetime.now().strftime("%d %B %Y"), None),
            "date_generation": (
                lambda d: datetime.now().strftime("%d %B %Y à %H:%M"),
                None,
            ),
            # Profil investisseur (subtitle_profile)
            "subtitle_profile": (self._synthesize_investor_profile, None),
            # Synthèse - Montants
            "patrimoine_total": ("synthese.patrimoine_total", self._format_currency),
            "actifs_financiers": (
                "synthese.patrimoine_financier",
                self._format_currency,
            ),
            "immobilier": ("synthese.patrimoine_immobilier", self._format_currency),
            # Synthèse - Scores
            "score_global": ("synthese.score_global", lambda x: f"{x}/10"),
            "risque_principal": ("synthese.risque_principal", str),
            "priorites": ("synthese.priorites", str),
            "synthese_commentaire": (self._generate_synthese_commentaire, None),
            # Détails score diversification
            "div_score_final": ("synthese.diversification_details.score", lambda x: f"{x:.1f}"),
            "div_label": ("synthese.diversification_details.label", str),
            "div_score_institutional": ("synthese.diversification_details.details.score_institutional", lambda x: f"{x:.1f}"),
            "div_score_jurisdictional": ("synthese.diversification_details.details.score_jurisdictional", lambda x: f"{x:.1f}"),
            "div_score_weighted": ("synthese.diversification_details.details.score_weighted", lambda x: f"{x:.1f}"),
            "div_bonus_total": ("synthese.diversification_details.details.bonus_total", lambda x: f"{x:.1f}"),
            "div_nb_classes": ("synthese.diversification_details.details.nb_classes_actifs", str),
            "div_nb_positions": ("synthese.diversification_details.details.nb_positions", str),
            "div_pct_international": ("synthese.diversification_details.details.pct_international", lambda x: f"{x:.1f}"),
            "div_bonus_details": (self._format_diversification_bonus_details, None),
            # Détails score résilience
            "res_score_final": ("synthese.resilience_details.score", lambda x: f"{x:.1f}"),
            "res_label": ("synthese.resilience_details.label", str),
            # Détails score liquidité
            "liq_score_final": ("synthese.liquidity_details.score", lambda x: f"{x:.1f}"),
            "liq_label": ("synthese.liquidity_details.label", str),
            "liq_liquidite_actuelle": ("synthese.liquidity_details.details.liquidite_actuelle", lambda x: f"{x:,.0f} €".replace(",", " ")),
            "liq_liquidite_cible": ("synthese.liquidity_details.details.liquidite_cible", lambda x: f"{x:,.0f} €".replace(",", " ")),
            "liq_ratio": ("synthese.liquidity_details.details.ratio", lambda x: f"{x:.2f}"),
            "liq_target_months": ("synthese.liquidity_details.details.target_months", str),
            "liq_depenses_mensuelles": ("synthese.liquidity_details.details.depenses_mensuelles", lambda x: f"{x:,.0f} €".replace(",", " ")),
            "liq_overliquid_message": (self._format_overliquidity_message, None),
            # Détails score fiscal
            "fisc_score_final": ("synthese.fiscal_details.score", lambda x: f"{x:.1f}"),
            "fisc_label": ("synthese.fiscal_details.label", str),
            "fisc_pea_total": ("synthese.fiscal_details.details.pea_total", lambda x: f"{x:,.0f} €".replace(",", " ")),
            "fisc_cto_total": ("synthese.fiscal_details.details.cto_total", lambda x: f"{x:,.0f} €".replace(",", " ")),
            "fisc_av_total": ("synthese.fiscal_details.details.av_total", lambda x: f"{x:,.0f} €".replace(",", " ")),
            "fisc_per_total": ("synthese.fiscal_details.details.per_total", lambda x: f"{x:,.0f} €".replace(",", " ")),
            "fisc_crypto_total": ("synthese.fiscal_details.details.crypto_total", lambda x: f"{x:,.0f} €".replace(",", " ")),
            "fisc_crypto_percentage": ("synthese.fiscal_details.details.crypto_percentage", lambda x: f"{x:.1f}%"),
            "fisc_pea_over_cto": ("synthese.fiscal_details.details.pea_over_cto", lambda x: "Oui" if x else "Non"),
            "fisc_has_per": ("synthese.fiscal_details.details.has_per", lambda x: "Oui" if x else "Non"),
            "fisc_bonuses": (self._format_fiscal_bonuses, None),
            "fisc_penalties": (self._format_fiscal_penalties, None),
            # Détails score croissance
            "growth_score_final": ("synthese.growth_details.score", lambda x: f"{x:.1f}"),
            "growth_label": ("synthese.growth_details.label", str),
            "growth_exposition_actions": ("synthese.growth_details.details.exposition_actions", lambda x: f"{x:,.0f} €".replace(",", " ")),
            "growth_patrimoine_financier": ("synthese.growth_details.details.patrimoine_financier", lambda x: f"{x:,.0f} €".replace(",", " ")),
            "growth_pct_actions": ("synthese.growth_details.details.pct_actions", lambda x: f"{x:.1f}%"),
            "growth_profil_actif": ("synthese.growth_details.details.profil_actif", str),
            "growth_optimal_range": (self._format_growth_optimal_range, None),
            "growth_interpretation": ("synthese.growth_details.details.interpretation", str),
            # Alerte de concentration (conditionnel)
            "concentration_alert_content": (self._analyze_concentration_alert, None),
            # Optimisation Markowitz - Graphique
            "markowitz_chart": ("optimisation_portefeuille.graphique_base64", str),
            # Optimisation Markowitz - Portefeuille actuel
            "markowitz_current_return": (
                "optimisation_portefeuille.portefeuille_actuel.rendement_annuel",
                lambda x: f"{x}%",
            ),
            "markowitz_current_volatility": (
                "optimisation_portefeuille.portefeuille_actuel.volatilite_annuelle",
                lambda x: f"{x}%",
            ),
            "markowitz_current_sharpe": (
                "optimisation_portefeuille.portefeuille_actuel.ratio_sharpe",
                lambda x: f"{x:.2f}",
            ),
            # Optimisation Markowitz - Portefeuille optimal
            "markowitz_optimal_return": (
                "optimisation_portefeuille.portefeuille_optimal.rendement_annuel",
                lambda x: f"{x}%",
            ),
            "markowitz_optimal_volatility": (
                "optimisation_portefeuille.portefeuille_optimal.volatilite_annuelle",
                lambda x: f"{x}%",
            ),
            "markowitz_optimal_sharpe": (
                "optimisation_portefeuille.portefeuille_optimal.ratio_sharpe",
                lambda x: f"{x:.2f}",
            ),
            # Optimisation Markowitz - Métadonnées
            "markowitz_risk_free_rate": (
                "optimisation_portefeuille.taux_sans_risque",
                lambda x: f"{x}".replace(".", ","),
            ),
            "markowitz_interpretation": (
                "optimisation_portefeuille.interpretation",
                str,
            ),
        }

        for field_name, (json_path_or_func, formatter) in mappings.items():
            # Traiter fonction lambda ou chemin JSON
            if callable(json_path_or_func):
                value = json_path_or_func(data)
            else:
                value = self._get_nested_value(data, json_path_or_func)

            # Appliquer formateur si présent (UNE SEULE FOIS avant la boucle)
            if value is not None and formatter:
                value = formatter(value)

            # Trouver tous les éléments avec ce data-field
            elements = soup.find_all(attrs={"data-field": field_name})

            for el in elements:
                if value is None:
                    # Si la valeur est None et que l'élément a un parent avec data-conditional,
                    # supprimer tout le parent conditionnel
                    parent = el.find_parent(attrs={"data-conditional": True})
                    if parent:
                        parent.decompose()
                        self.logger.debug(
                            f"  → Alerte conditionnelle '{field_name}' supprimée (aucune alerte)"
                        )
                else:
                    # Si c'est une balise img, injecter dans src
                    if el.name == "img":
                        el["src"] = str(value)
                    else:
                        # Injecter du HTML si le contenu contient des balises
                        if isinstance(value, str) and ("<" in value and ">" in value):
                            el.clear()
                            el.append(BeautifulSoup(value, "html.parser"))
                        else:
                            el.string = str(value)

        # Post-traitement : Appliquer la classe CSS au badge div_label
        div_label_elements = soup.find_all(attrs={"data-field": "div_label"})
        for badge_el in div_label_elements:
            label_text = badge_el.string if badge_el.string else ""
            badge_class = self._get_diversification_badge_class(label_text)

            if badge_el.has_attr("class"):
                badge_classes = [c for c in badge_el["class"] if c not in ["high", "mid", "low", "crit"]]
                badge_classes.append(badge_class)
                badge_el["class"] = badge_classes
            else:
                badge_el["class"] = ["badge", badge_class]

        # Post-traitement : Appliquer la classe CSS au badge res_label
        res_label_elements = soup.find_all(attrs={"data-field": "res_label"})
        for badge_el in res_label_elements:
            label_text = badge_el.string if badge_el.string else ""
            badge_class = self._get_resilience_badge_class(label_text)

            if badge_el.has_attr("class"):
                badge_classes = [c for c in badge_el["class"] if c not in ["high", "mid", "low", "crit"]]
                badge_classes.append(badge_class)
                badge_el["class"] = badge_classes
            else:
                badge_el["class"] = ["badge", badge_class]

        # Post-traitement : Appliquer la classe CSS au badge liq_label
        liq_label_elements = soup.find_all(attrs={"data-field": "liq_label"})
        for badge_el in liq_label_elements:
            label_text = badge_el.string if badge_el.string else ""
            badge_class = self._get_liquidity_badge_class(label_text)

            if badge_el.has_attr("class"):
                badge_classes = [c for c in badge_el["class"] if c not in ["high", "mid", "low", "crit"]]
                badge_classes.append(badge_class)
                badge_el["class"] = badge_classes
            else:
                badge_el["class"] = ["badge", badge_class]

        # Post-traitement : Appliquer la classe CSS au badge fisc_label
        fisc_label_elements = soup.find_all(attrs={"data-field": "fisc_label"})
        for badge_el in fisc_label_elements:
            label_text = badge_el.string if badge_el.string else ""
            badge_class = self._get_fiscal_badge_class(label_text)

            if badge_el.has_attr("class"):
                badge_classes = [c for c in badge_el["class"] if c not in ["high", "mid", "low", "crit"]]
                badge_classes.append(badge_class)
                badge_el["class"] = badge_classes
            else:
                badge_el["class"] = ["badge", badge_class]

        # Post-traitement : Appliquer la classe CSS au badge growth_label
        growth_label_elements = soup.find_all(attrs={"data-field": "growth_label"})
        for badge_el in growth_label_elements:
            label_text = badge_el.string if badge_el.string else ""
            badge_class = self._get_growth_badge_class(label_text)

            if badge_el.has_attr("class"):
                badge_classes = [c for c in badge_el["class"] if c not in ["high", "mid", "low", "crit"]]
                badge_classes.append(badge_class)
                badge_el["class"] = badge_classes
            else:
                badge_el["class"] = ["badge", badge_class]

        self.logger.debug(f"  → {len(mappings)} champs simples injectés")

    def _inject_repeated_rows(self, soup: BeautifulSoup, data: dict):
        """
        Duplique et remplit les lignes répétées [data-repeat]
        Section 16.2 du PRD
        """
        # 1. Établissements
        self._inject_etablissements(soup, data)

        # 2. Classes d'actifs
        self._inject_classes_actifs(soup, data)

        # 3. Risques
        self._inject_risques(soup, data)

        # 4. Recommandations
        self._inject_recommandations(soup, data)

        # 5. Stress tests
        self._inject_stress_tests(soup, data)

    def _inject_etablissements(self, soup: BeautifulSoup, data: dict):
        """Injecte les lignes d'établissements"""
        template_row = soup.find("tr", attrs={"data-repeat": "etablissement"})
        if not template_row:
            return

        tbody = template_row.find_parent("tbody")
        if not tbody:
            return

        # Retirer le template
        template_row.extract()

        # Créer une ligne par établissement
        for etab in data.get("repartition", {}).get("par_etablissement", []):
            new_row = BeautifulSoup(str(template_row), "html.parser").find("tr")

            # Remplir les champs
            self._set_field(new_row, "etablissement_name", etab.get("nom", ""))
            self._set_field(
                new_row, "etablissement_juridiction", etab.get("juridiction", "")
            )
            self._set_field(
                new_row,
                "etablissement_montant",
                self._format_currency(etab.get("montant", 0)),
            )
            self._set_field(
                new_row, "etablissement_pct", f"{etab.get('pourcentage', 0)} %"
            )

            # Badge risque - logique dynamique identique aux stress tests
            niveau_risque = etab.get("niveau_risque", "Normal")
            badge = new_row.find(attrs={"data-field": "etablissement_risk"})
            if badge:
                badge.string = niveau_risque
                # Calculer la classe CSS appropriée
                risk_class = self._get_badge_class(niveau_risque)

                # Appliquer la classe dynamiquement
                if badge.has_attr("class"):
                    # Supprimer les anciennes classes de sévérité
                    badge_classes = [
                        c
                        for c in badge["class"]
                        if c not in ["high", "mid", "low", "crit"]
                    ]
                    badge_classes.append(risk_class)
                    badge["class"] = badge_classes
                else:
                    badge["class"] = ["badge", risk_class]

            tbody.append(new_row)

        self.logger.debug(
            f"  → {len(data.get('repartition', {}).get('par_etablissement', []))} établissements injectés"
        )

    def _inject_classes_actifs(self, soup: BeautifulSoup, data: dict):
        """Injecte les lignes de classes d'actifs avec séparation établissement/détail"""
        # Le template utilise data-repeat="classes" sur tbody
        tbody = soup.find("tbody", attrs={"data-repeat": "classes"})
        if not tbody:
            self.logger.warning("tbody[data-repeat='classes'] introuvable")
            return

        # Extraire le tr template du tbody
        template_row = tbody.find("tr")
        if not template_row:
            self.logger.warning("Aucun <tr> template dans tbody classes")
            return

        # Cloner le template
        template_html = str(template_row)

        # Vider le tbody
        tbody.clear()

        # Créer une ligne par classe d'actif
        for actif in data.get("repartition", {}).get("par_classe_actifs", []):
            new_row = BeautifulSoup(template_html, "html.parser").find("tr")

            type_actif = actif.get("type_actif", "")
            etablissement_raw = actif.get("etablissement", "")

            # Parser l'établissement pour séparer "Établissement (Détail)"
            # Pattern: "Crédit Agricole (AV - Fonds Euro)" → etab="Crédit Agricole", detail="AV - Fonds Euro"
            match = re.match(r"^(.+?)\s*\((.+)\)$", etablissement_raw)

            if match:
                # Format: "Établissement (Détail)"
                etablissement_name = match.group(1).strip()
                detail_compte = match.group(2).strip()
            else:
                # Pas de parenthèses: c'est juste un détail sans établissement
                etablissement_name = ""
                detail_compte = etablissement_raw

            # Colonne "Classe d'actifs" : ligne 1 = type, ligne 2 = détail
            self._set_field(new_row, "class_name_primary", type_actif)
            self._set_field(new_row, "class_name_secondary", detail_compte)

            # Colonne "Établissement"
            self._set_field(new_row, "class_etablissement", etablissement_name)

            # Colonnes montant et pourcentage
            self._set_field(
                new_row, "class_amount", self._format_currency(actif.get("montant", 0))
            )
            self._set_field(new_row, "class_pct", f"{actif.get('pourcentage', 0)} %")

            # Colonne écart benchmark
            benchmark_gap = actif.get("benchmark_gap", {})
            gap_message = benchmark_gap.get("message", "N/A")
            gap_niveau = benchmark_gap.get("niveau", "normal")
            gap_status = benchmark_gap.get("status", "pas_de_benchmark")

            # Message textuel
            self._set_field(new_row, "class_gap_message", gap_message)

            # Badge (uniquement si niveau attention ou alerte)
            badge_span = new_row.find("span", attrs={"data-field": "class_gap_badge"})
            if badge_span:
                if gap_niveau in ["attention", "alerte"]:
                    # Déterminer la classe CSS du badge selon le status
                    if "fort" in gap_status:
                        badge_class = "crit"  # Rouge foncé
                        badge_text = "Alerte"
                    elif gap_niveau == "alerte":
                        badge_class = "high"  # Rouge clair
                        badge_text = "Attention"
                    else:
                        badge_class = "mid"  # Orange
                        badge_text = "À surveiller"

                    badge_span["class"] = ["badge", badge_class]
                    badge_span.string = badge_text
                else:
                    # Pas de badge si niveau normal
                    badge_span.decompose()

            tbody.append(new_row)

        self.logger.debug(
            f"  → {len(data.get('repartition', {}).get('par_classe_actifs', []))} classes d'actifs injectées"
        )

    def _inject_risques(self, soup: BeautifulSoup, data: dict):
        """Injecte les risques critiques et élevés"""
        template_div = soup.find("div", attrs={"data-repeat": "risque"})
        if not template_div:
            return

        parent = template_div.find_parent()
        if not parent:
            return

        template_div.extract()

        # Afficher tous les risques (critiques, élevés, moyens, faibles)
        all_risques = (
            data.get("risques", {}).get("critiques", [])
            + data.get("risques", {}).get("eleves", [])
            + data.get("risques", {}).get("moyens", [])
            + data.get("risques", {}).get("faibles", [])
        )

        for idx, risque in enumerate(all_risques[:10], start=1):  # Max 10 risques
            new_div = BeautifulSoup(str(template_div), "html.parser").find("div")

            # Numéro du risque (01, 02, 03, etc.)
            self._set_field(new_div, "risque_num", f"{idx:02d}")

            self._set_field(new_div, "risque_titre", risque.get("titre", ""))
            self._set_field(
                new_div, "risque_description", risque.get("description", "")
            )
            self._set_field(
                new_div,
                "risque_montant",
                self._format_currency(risque.get("exposition_montant", 0)),
            )
            self._set_field(
                new_div, "risque_pct", f"{risque.get('exposition_pct', 0)}%"
            )

            # Injecter les sources web
            sources_web = risque.get("sources_web", [])
            self._set_field(new_div, "sources_count", str(len(sources_web)))

            # Créer la liste des sources
            sources_list_el = new_div.find(attrs={"data-field": "sources_list"})
            if sources_list_el and sources_web:
                sources_list_el.clear()
                for source in sources_web:
                    li = soup.new_tag("li")
                    a = soup.new_tag(
                        "a",
                        href=source.get("url", "#"),
                        target="_blank",
                        rel="noopener",
                    )
                    a.string = source.get("titre", "Source")
                    li.append(a)

                    # Ajouter extrait si disponible
                    if source.get("extrait"):
                        br = soup.new_tag("br")
                        li.append(br)
                        small = soup.new_tag("small", style="color: #666;")
                        # Décoder les entités HTML (&#x27; → ', etc.)
                        extrait_text = (
                            html.unescape(source.get("extrait", ""))[:150] + "..."
                        )
                        small.string = extrait_text
                        li.append(small)

                    sources_list_el.append(li)

            parent.append(new_div)

        self.logger.debug(f"  → {min(5, len(all_risques))} risques injectés")

    def _inject_recommandations(self, soup: BeautifulSoup, data: dict):
        """Injecte les recommandations prioritaires"""
        template_div = soup.find("div", attrs={"data-repeat": "recommandation"})
        if not template_div:
            return

        parent = template_div.find_parent()
        if not parent:
            return

        template_div.extract()

        recos = data.get("recommandations", {}).get("prioritaires", [])

        for idx, reco in enumerate(recos[:5], start=1):  # Max 5 recommandations
            new_div = BeautifulSoup(str(template_div), "html.parser").find("div")

            # Numéro de la recommandation (01, 02, 03, etc.)
            self._set_field(new_div, "reco_num", f"{idx:02d}")

            self._set_field(new_div, "reco_titre", reco.get("titre", ""))
            self._set_field(new_div, "reco_description", reco.get("description", ""))
            self._set_field(new_div, "reco_benefice", reco.get("benefice", ""))

            # Délai estimé
            delai_jours = reco.get("delai_jours", 30)
            self._set_field(new_div, "reco_delai", f"{delai_jours} jours")

            # Actions concrètes
            actions_ul = new_div.find(attrs={"data-field": "reco_actions"})
            if actions_ul and "actions_concretes" in reco:
                actions_ul.clear()
                for action in reco["actions_concretes"]:
                    li = soup.new_tag("li")
                    li.string = action
                    actions_ul.append(li)

            parent.append(new_div)

        self.logger.debug(f"  → {min(5, len(recos))} recommandations injectées")

    def _inject_stress_tests(self, soup: BeautifulSoup, data: dict):
        """Injecte les stress tests"""
        template_div = soup.find("div", attrs={"data-repeat": "stress_test"})
        if not template_div:
            return

        parent = template_div.find_parent()
        if not parent:
            return

        template_div.extract()

        for test in data.get("stress_tests", []):
            new_div = BeautifulSoup(str(template_div), "html.parser").find("div")

            # Scénario
            self._set_field(new_div, "test_scenario", test.get("scenario", ""))

            # Impact - Nouvelle structure : valeur et pourcentage séparés
            impact_montant = test.get("impact_montant", 0)
            impact_pct = test.get("impact_pct", 0)

            # Injecter la valeur monétaire (dans span.price)
            self._set_field(
                new_div, "test_impact_valeur", self._format_currency(impact_montant)
            )

            # Injecter le pourcentage (dans span.pct)
            self._set_field(new_div, "test_impact_pct", f"{impact_pct:+.1f} %")

            # Détails - Description seule (sans sévérité)
            description = test.get("description", "")
            severite = test.get("severite", "Moyenne")
            self._set_field(new_div, "test_details", description)

            # Classe CSS dynamique selon sévérité
            severite_class = self._get_stress_severity_class(severite)
            if new_div.has_attr("class"):
                # Remplacer la classe de sévérité (high, mid, low)
                classes = [
                    c
                    for c in new_div["class"]
                    if c not in ["high", "mid", "low", "crit"]
                ]
                classes.append(severite_class)
                new_div["class"] = classes
            else:
                new_div["class"] = ["stress", severite_class]

            # Badge de sévérité
            badge_el = new_div.find("div", class_="badge")
            if badge_el:
                badge_el.string = severite.upper()
                # Ajouter la classe de sévérité au badge aussi
                if badge_el.has_attr("class"):
                    badge_classes = [
                        c
                        for c in badge_el["class"]
                        if c not in ["high", "mid", "low", "crit"]
                    ]
                    badge_classes.append(severite_class)
                    badge_el["class"] = badge_classes
                else:
                    badge_el["class"] = ["badge", severite_class]

            parent.append(new_div)

        self.logger.debug(
            f"  → {len(data.get('stress_tests', []))} stress tests injectés"
        )

    def _inject_chart_data(self, soup: BeautifulSoup, data: dict):
        """
        Injecte les données dans le graphique Chart.js
        Section 16.3 du PRD
        """
        # Trouver le script contenant le radar chart
        script_tag = soup.find("script", string=re.compile("radarChart"))
        if not script_tag:
            self.logger.warning(
                "Script radarChart introuvable, skip injection graphique"
            )
            return

        # Extraire les scores depuis JSON
        scores_details = data.get("synthese", {}).get("scores_details", {})
        scores_array = [
            scores_details.get("diversification", 5),
            scores_details.get("resilience", 5),
            scores_details.get("liquidite", 5),
            scores_details.get("fiscalite", 5),
            scores_details.get("croissance", 5),
        ]

        # Remplacer les données dans le script
        old_script = script_tag.string
        # Pattern pour trouver: data: [8, 7.5, 6.5, 7, 8.5]
        new_script = re.sub(r"data:\s*\[[^\]]+\]", f"data: {scores_array}", old_script)

        script_tag.string = new_script
        self.logger.debug(f"  → Données graphique radar injectées: {scores_array}")

    def _inline_css(self, soup: BeautifulSoup):
        """
        Incorpore le CSS externe directement dans le HTML
        Remplace <link rel="stylesheet" href="rapport.css" /> par <style>...</style>
        """
        # Trouver la balise link vers rapport.css
        link_tag = soup.find("link", attrs={"rel": "stylesheet", "href": "rapport.css"})

        if not link_tag:
            self.logger.warning("Balise <link> vers rapport.css introuvable")
            return

        # Construire le chemin vers le fichier CSS
        css_path = Path(self.config["paths"]["templates"]) / "rapport.css"

        if not css_path.exists():
            self.logger.warning(f"Fichier CSS introuvable : {css_path}")
            return

        # Lire le contenu du CSS
        css_content = css_path.read_text(encoding="utf-8")

        # Créer une nouvelle balise <style>
        style_tag = soup.new_tag("style")
        style_tag.string = css_content

        # Remplacer la balise <link> par <style>
        link_tag.replace_with(style_tag)

        self.logger.debug(f"  → CSS incorporé ({len(css_content)} caractères)")

    def _format_currency(self, value: float) -> str:
        """
        Formate un montant en euros
        Section 16.1 du PRD : 470354 → '470 354 €'
        """
        return f"{value:,.0f} €".replace(",", " ")

    def _format_diversification_bonus_details(self, data: dict) -> str:
        """
        Formate les détails des bonus de diversification
        Retourne un HTML structuré avec <p> et <ul>
        """
        try:
            bonus_details = data.get("synthese", {}).get("diversification_details", {}).get("details", {}).get("bonus_details", {})

            if not bonus_details:
                return ""

            html_parts = [
                '<p style="margin-top: 0.75rem; margin-bottom: 0.5rem">',
                '<strong>Bonus obtenus :</strong>',
                '</p>',
                '<ul>'
            ]

            # Bonus classes d'actifs
            if "classes_actifs" in bonus_details:
                count = bonus_details["classes_actifs"].get("count", 0)
                bonus = bonus_details["classes_actifs"].get("bonus", 0)
                html_parts.append(f'<li>{count} classes d\'actifs : +{bonus:.1f} point(s)</li>')

            # Bonus positions
            if "positions" in bonus_details:
                count = bonus_details["positions"].get("count", 0)
                bonus = bonus_details["positions"].get("bonus", 0)
                html_parts.append(f'<li>{count} positions/comptes : +{bonus:.1f} point(s)</li>')

            # Bonus international
            if "international" in bonus_details:
                pct = bonus_details["international"].get("pct", 0)
                bonus = bonus_details["international"].get("bonus", 0)
                html_parts.append(f'<li>Exposition internationale {pct:.1f}% : +{bonus:.1f} point(s)</li>')

            html_parts.append('</ul>')

            return "".join(html_parts)
        except Exception as e:
            self.logger.warning(f"Erreur formatage bonus diversification: {e}")
            return ""

    def _get_nested_value(self, data: dict, path: str) -> Any:
        """
        Récupère valeur dans dict imbriqué via chemin type 'synthese.patrimoine_total'
        Section 16.1 du PRD
        """
        keys = path.split(".")
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
            if value is None:
                return None
        return value

    def _set_field(self, element, field_name: str, value: str):
        """Définit la valeur d'un champ data-field dans un élément"""
        field_el = element.find(attrs={"data-field": field_name})
        if field_el:
            field_el.string = str(value)

    def _get_badge_class(self, niveau: str) -> str:
        """
        Retourne classe CSS selon niveau risque
        Section 16.2 du PRD
        """
        mapping = {
            "Critique": "crit",
            "Élevé": "mid",
            "Moyen": "mid",
            "Faible": "low",
            "Normal": "low",
        }
        return mapping.get(niveau, "mid")

    def _get_stress_severity_class(self, severite: str) -> str:
        """
        Retourne classe CSS selon sévérité du stress test
        Mapping: Critique/Élevée -> high, Moyenne/Modérée -> mid, Faible -> low
        """
        severite_lower = severite.lower()
        if severite_lower in ["critique", "élevée", "élevé", "high"]:
            return "high"
        elif severite_lower in ["moyenne", "modérée", "modéré", "medium", "mid"]:
            return "mid"
        elif severite_lower in ["faible", "basse", "low"]:
            return "low"
        else:
            # Par défaut: moyenne
            return "mid"

    def _get_diversification_badge_class(self, label: str) -> str:
        """
        Retourne classe CSS selon le label de qualité de diversification
        Mapping des labels vers les classes CSS
        """
        label_lower = label.lower()
        if "excellente" in label_lower or "très bien" in label_lower:
            return "low"  # Vert = bon
        elif "bonne" in label_lower or "bon équilibre" in label_lower:
            return "low"  # Vert = bon
        elif "modérée" in label_lower or "concentration modérée" in label_lower:
            return "mid"  # Orange = attention
        elif "forte" in label_lower or "concentration élevée" in label_lower:
            return "high"  # Rouge clair = alerte
        elif "critique" in label_lower or "concentration critique" in label_lower:
            return "crit"  # Rouge foncé = critique
        else:
            # Par défaut: mid
            return "mid"

    def _get_resilience_badge_class(self, label: str) -> str:
        """
        Retourne classe CSS selon le label de qualité de résilience
        Mapping des labels vers les classes CSS
        """
        label_lower = label.lower()
        if "résilient" in label_lower:
            return "low"  # Vert = bon
        elif "solide" in label_lower:
            return "low"  # Vert = bon
        elif "vulnérable" in label_lower:
            return "mid"  # Orange = attention
        elif "fragile" in label_lower:
            return "high"  # Rouge clair = alerte
        elif "critique" in label_lower:
            return "crit"  # Rouge foncé = critique
        else:
            # Par défaut: mid
            return "mid"

    def _get_fiscal_badge_class(self, label: str) -> str:
        """
        Retourne classe CSS selon le label de qualité fiscal
        Mapping des labels vers les classes CSS
        """
        label_lower = label.lower()

        if "excellente" in label_lower:
            return "low"  # Vert = bon
        elif "bonne" in label_lower:
            return "low"  # Vert = bon
        elif "moyenne" in label_lower:
            return "mid"  # Orange = attention
        elif "sous-optimisée" in label_lower or "sous-optimisé" in label_lower:
            return "high"  # Rouge clair = alerte
        elif "défavorable" in label_lower:
            return "crit"  # Rouge foncé = critique
        else:
            # Par défaut: mid
            return "mid"

    def _format_fiscal_bonuses(self, data: dict) -> str:
        """
        Formate les bonus fiscaux appliqués
        Retourne une liste HTML des bonus
        """
        try:
            fiscal_details = data.get("synthese", {}).get("fiscal_details", {}).get("details", {})
            if not fiscal_details:
                return ""

            bonuses_applied = fiscal_details.get("bonuses_applied", {})
            if not bonuses_applied:
                return "<p style='font-style: italic; color: var(--text-secondary);'>Aucun bonus appliqué</p>"

            html_parts = []

            # Bonus PEA > CTO
            if "pea_over_cto" in bonuses_applied:
                bonus = bonuses_applied["pea_over_cto"]
                html_parts.append(f"<li>PEA > CTO (fiscalement avantageux) : +{bonus:.1f} point(s)</li>")

            # Bonus AV succession
            if "av_succession" in bonuses_applied:
                bonus = bonuses_applied["av_succession"]
                html_parts.append(f"<li>Assurance-vie (succession optimisée) : +{bonus:.1f} point(s)</li>")

            # Bonus PER
            if "per_present" in bonuses_applied:
                bonus = bonuses_applied["per_present"]
                html_parts.append(f"<li>PER présent (avantage fiscal à l'entrée) : +{bonus:.1f} point(s)</li>")

            if html_parts:
                return "<ul>" + "".join(html_parts) + "</ul>"
            else:
                return "<p style='font-style: italic; color: var(--text-secondary);'>Aucun bonus appliqué</p>"

        except Exception as e:
            self.logger.error(f"Erreur formatage bonus fiscaux: {e}")
            return ""

    def _format_fiscal_penalties(self, data: dict) -> str:
        """
        Formate les pénalités fiscales appliquées
        Retourne une liste HTML des pénalités
        """
        try:
            fiscal_details = data.get("synthese", {}).get("fiscal_details", {}).get("details", {})
            if not fiscal_details:
                return ""

            penalties_applied = fiscal_details.get("penalties_applied", {})
            if not penalties_applied:
                return "<p style='font-style: italic; color: var(--text-secondary);'>Aucune pénalité appliquée</p>"

            html_parts = []

            # Pénalité cryptos élevés
            if "crypto_high" in penalties_applied:
                penalty = penalties_applied["crypto_high"]
                crypto_pct = fiscal_details.get("crypto_percentage", 0)
                html_parts.append(f"<li>Cryptomonnaies élevées ({crypto_pct:.1f}% du patrimoine) : {penalty:.1f} point(s)</li>")

            if html_parts:
                return "<ul>" + "".join(html_parts) + "</ul>"
            else:
                return "<p style='font-style: italic; color: var(--text-secondary);'>Aucune pénalité appliquée</p>"

        except Exception as e:
            self.logger.error(f"Erreur formatage pénalités fiscales: {e}")
            return ""

    def _get_growth_badge_class(self, label: str) -> str:
        """
        Retourne classe CSS selon le label de qualité croissance
        Mapping des labels vers les classes CSS
        """
        label_lower = label.lower()

        if "excellent" in label_lower:
            return "low"  # Vert = bon
        elif "bon" in label_lower:
            return "low"  # Vert = bon
        elif "modéré" in label_lower:
            return "mid"  # Orange = attention
        elif "limité" in label_lower:
            return "high"  # Rouge clair = alerte
        elif "très faible" in label_lower or "faible" in label_lower:
            return "crit"  # Rouge foncé = critique
        else:
            # Par défaut: mid
            return "mid"

    def _format_growth_optimal_range(self, data: dict) -> str:
        """
        Formate la plage optimale du profil de croissance
        Retourne une chaîne formatée "X-Y%"
        """
        try:
            growth_details = data.get("synthese", {}).get("growth_details", {}).get("details", {})
            if not growth_details:
                return "N/A"

            optimal_range = growth_details.get("optimal_range", [60, 70])
            return f"{optimal_range[0]}-{optimal_range[1]}%"

        except Exception as e:
            self.logger.error(f"Erreur formatage plage optimale croissance: {e}")
            return "N/A"

    def _format_overliquidity_message(self, data: dict) -> str:
        """
        Formate le message de sur-liquidité
        Retourne un message d'alerte si sur-liquidité détectée
        """
        try:
            liquidity_details = data.get("synthese", {}).get("liquidity_details", {}).get("details", {})
            if not liquidity_details:
                return ""

            is_overliquid = liquidity_details.get("is_overliquid", False)
            if not is_overliquid:
                return ""

            ratio = liquidity_details.get("ratio", 0)
            threshold = liquidity_details.get("overliquidity_threshold", 1.5)

            return (
                f"⚠️ Sur-liquidité détectée (ratio {ratio:.2f} > {threshold:.2f}). "
                f"Une partie importante de votre patrimoine est en liquidités non investies, "
                f"ce qui peut limiter le potentiel de croissance à long terme."
            )
        except Exception as e:
            self.logger.error(f"Erreur formatage message sur-liquidité: {e}")
            return ""

    def _get_liquidity_badge_class(self, label: str) -> str:
        """
        Retourne classe CSS selon le label de qualité de liquidité
        Mapping des labels vers les classes CSS
        """
        label_lower = label.lower()

        if "excellente" in label_lower:
            return "low"  # Vert = bon
        elif "bonne" in label_lower:
            return "low"  # Vert = bon
        elif "acceptable" in label_lower:
            return "mid"  # Orange = attention
        elif "fragile" in label_lower:
            return "high"  # Rouge clair = alerte
        elif "critique" in label_lower:
            return "crit"  # Rouge foncé = critique
        else:
            # Par défaut: mid
            return "mid"

    def _synthesize_investor_profile(self, data: dict) -> str:
        """
        Synthétise le profil investisseur pour le subtitle du rapport
        Section 3.3.8 du PRD
        """
        profil = data.get("profil", {})

        # Extraire les informations clés
        prenom = profil.get("prénom", "")
        nom = profil.get("nom", "")
        age = profil.get("age", "")
        situation = profil.get("situation_familiale", "")
        enfants = profil.get("enfants", 0)
        type_inv = profil.get("type_investissement", "")
        statut = profil.get("statut", "")
        profession = profil.get("profession", "")
        revenu = profil.get("revenu_mensuel_net", 0)

        # Construire la synthèse
        parts = []

        # Prénom NOM + âge
        if prenom and nom:
            full_name = f"{prenom} {nom.upper()}"
            if age:
                parts.append(f"{full_name} • {age} ans")
            else:
                parts.append(full_name)
        elif age:
            parts.append(f"{age} ans")

        # Situation familiale
        if situation:
            situation_text = situation
            if enfants > 0:
                situation_text += f", {enfants} enfant" + ("s" if enfants > 1 else "")
            parts.append(situation_text)

        # Type d'investisseur
        if type_inv:
            parts.append(f"Profil {type_inv}")

        # Profession/statut
        if profession and statut:
            parts.append(f"{profession} ({statut})")
        elif profession:
            parts.append(profession)
        elif statut:
            parts.append(statut)

        # Revenu (optionnel, seulement si présent et significatif)
        if revenu > 0:
            parts.append(f"{self._format_currency(revenu)}/mois")

        # Joindre avec des séparateurs
        if len(parts) > 0:
            return " • ".join(parts)
        else:
            return "Analyse approfondie • Recommandations • Synthèse"

    def _get_concentration_france_pct(self, data: dict) -> float:
        """
        Récupère le pourcentage du patrimoine exposé au système bancaire français
        """
        concentration = data.get("repartition", {}).get("concentration", {})
        france = concentration.get("france", {})
        return france.get("pourcentage", 0)

    def _get_concentration_top_etablissement(self, data: dict) -> float:
        """
        Récupère le pourcentage du premier établissement (le plus concentré)
        """
        etablissements = data.get("repartition", {}).get("par_etablissement", [])
        if etablissements:
            return etablissements[0].get("pourcentage", 0)
        return 0

    def _generate_synthese_commentaire(self, data: dict) -> str:
        """
        Génère le commentaire de synthèse finale basé sur l'analyse
        """
        # Récupérer les informations clés
        score = data.get("synthese", {}).get("score_global", 0)
        risques_critiques = data.get("risques", {}).get("critiques", [])
        risques_eleves = data.get("risques", {}).get("eleves", [])

        # Déterminer l'état général du patrimoine
        if score >= 7:
            etat = "présente une structure globalement saine"
        elif score >= 5:
            etat = "présente une structure correcte"
        else:
            etat = "nécessite des ajustements importants"

        # Identifier les principaux risques
        principaux_risques = []
        for risque in risques_critiques + risques_eleves[:2]:  # Max 3 risques
            categorie = risque.get("categorie", "")
            if "Concentration" in categorie:
                principaux_risques.append("concentration institutionnelle")
            elif "Sapin" in risque.get("titre", ""):
                principaux_risques.append("exposition aux produits d'assurance-vie")
            elif "géographique" in categorie.lower():
                principaux_risques.append("concentration géographique")
            elif "Réglementaire" in categorie:
                principaux_risques.append("risques réglementaires")
            elif "Fiscale" in categorie or "fiscal" in categorie.lower():
                principaux_risques.append("optimisation fiscale")

        # Enlever les doublons et limiter à 2-3 risques
        principaux_risques = list(dict.fromkeys(principaux_risques))[:3]

        # Construire le commentaire
        if principaux_risques:
            if len(principaux_risques) == 1:
                risques_text = f"une {principaux_risques[0]}"
            elif len(principaux_risques) == 2:
                risques_text = f"une {principaux_risques[0]} et {principaux_risques[1]}"
            else:
                risques_text = f"une {principaux_risques[0]}, {principaux_risques[1]} et {principaux_risques[2]}"

            commentaire = f"Le patrimoine {etat}, mais présente {risques_text}. "
        else:
            commentaire = f"Le patrimoine {etat}. "

        commentaire += "Les mesures proposées visent à renforcer la diversification, à réduire les risques systémiques et à améliorer la résilience globale."

        return commentaire

    def _analyze_concentration_alert(self, data: dict) -> str | None:
        """
        Analyse les données de concentration et génère une alerte si nécessaire
        Retourne None si rien d'alarmant n'est détecté

        Seuils d'alerte :
        - Établissement : ≥30% = préoccupant, ≥50% = critique
        - Juridiction : ≥60% = préoccupant, ≥80% = critique
        """
        etablissements = data.get("repartition", {}).get("par_etablissement", [])
        concentration_jur = data.get("repartition", {}).get("concentration", {})

        alerts = []

        # 1. Analyser la concentration par établissement
        for etab in etablissements:
            pct = etab.get("pourcentage", 0)
            nom = etab.get("nom", "Établissement inconnu")
            niveau_risque = etab.get("niveau_risque", "Normal")

            if niveau_risque == "Critique" or pct >= 50:
                alerts.append(
                    {
                        "type": "etablissement_critique",
                        "pct": pct,
                        "nom": nom,
                        "severity": 3,
                    }
                )
            elif niveau_risque == "Élevé" or pct >= 30:
                alerts.append(
                    {
                        "type": "etablissement_eleve",
                        "pct": pct,
                        "nom": nom,
                        "severity": 2,
                    }
                )

        # 2. Analyser la concentration par juridiction
        for juridiction, info in concentration_jur.items():
            pct = info.get("pourcentage", 0)
            niveau_risque = info.get("niveau_risque", "Normal")

            # Nom de juridiction plus lisible
            jur_name = {
                "france": "système français",
                "suisse": "système suisse",
                "luxembourg": "système luxembourgeois",
                "usa": "système américain",
                "royaume-uni": "système britannique",
            }.get(juridiction.lower(), f"système {juridiction}")

            if niveau_risque == "Critique" or pct >= 80:
                alerts.append(
                    {
                        "type": "juridiction_critique",
                        "pct": pct,
                        "nom": jur_name,
                        "severity": 3,
                    }
                )
            elif niveau_risque == "Élevé" or pct >= 60:
                alerts.append(
                    {
                        "type": "juridiction_elevee",
                        "pct": pct,
                        "nom": jur_name,
                        "severity": 2,
                    }
                )

        # Si aucune alerte, retourner None
        if not alerts:
            return None

        # Trier par sévérité décroissante
        alerts.sort(key=lambda x: (-x["severity"], -x["pct"]))

        # Générer le message d'alerte pour les alertes les plus importantes
        alert_messages = []

        for alert in alerts[:2]:  # Max 2 alertes principales
            pct = alert["pct"]
            nom = alert["nom"]
            alert_type = alert["type"]

            if "critique" in alert_type:
                if "etablissement" in alert_type:
                    alert_messages.append(
                        f"<strong>⚠️ Concentration critique :</strong> {pct:.1f}% du patrimoine "
                        f"exposé sur <strong>{nom}</strong>"
                    )
                else:  # juridiction
                    alert_messages.append(
                        f"<strong>⚠️ Concentration géographique critique :</strong> {pct:.1f}% du patrimoine "
                        f"exposé au <strong>{nom}</strong>"
                    )
            else:  # élevé
                if "etablissement" in alert_type:
                    alert_messages.append(
                        f"<strong>⚠️ Concentration élevée :</strong> {pct:.1f}% du patrimoine "
                        f"concentré sur <strong>{nom}</strong>"
                    )
                else:  # juridiction
                    alert_messages.append(
                        f"<strong>⚠️ Concentration géographique élevée :</strong> {pct:.1f}% du patrimoine "
                        f"exposé au <strong>{nom}</strong>"
                    )

        # Joindre les messages - chaque alerte sur une ligne séparée
        if len(alert_messages) == 1:
            return alert_messages[0] + "."
        else:
            # Créer une liste HTML pour séparer visuellement chaque alerte
            alert_items = "".join(
                [
                    f"<div style='margin-bottom: 8px;'>{msg}.</div>"
                    for msg in alert_messages
                ]
            )
            return alert_items
