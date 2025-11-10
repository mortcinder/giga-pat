"""
Module d'optimisation de portefeuille selon Markowitz
Version simplifiée avec estimations statistiques (sans API externe)
"""

import logging
import os

import matplotlib
import numpy as np
import yaml

matplotlib.use("Agg")  # Backend non-interactif pour génération serveur
import base64
from io import BytesIO
from typing import Any, Dict, List, Tuple

import matplotlib.pyplot as plt
from scipy.optimize import minimize


class PortfolioOptimizer:
    """
    Optimisation de portefeuille selon la théorie moderne de Markowitz
    Utilise des estimations statistiques moyennes par classe d'actifs
    """

    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Charger la configuration de l'optimiseur depuis YAML
        self._load_optimizer_config()

        # Charger le profil actif
        self._load_active_profile()

    def _load_optimizer_config(self):
        """Charge la configuration de l'optimiseur depuis le fichier YAML"""
        try:
            # Déterminer le chemin du fichier de configuration
            analysis_config = self.config.get("analysis", {})
            config_file = analysis_config.get("config_file", "analysis.yaml")

            # Construire le chemin absolu
            config_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "config",
            )
            config_path = os.path.join(config_dir, config_file)

            if not os.path.exists(config_path):
                self.logger.warning(
                    f"Fichier de configuration non trouvé: {config_path}. Utilisation des valeurs par défaut."
                )
                self._load_default_config()
                return

            # Charger le fichier YAML
            with open(config_path, "r", encoding="utf-8") as f:
                self.optimizer_config = yaml.safe_load(f)

            self.logger.info(f"Configuration chargée depuis: {config_path}")

        except Exception as e:
            self.logger.error(f"Erreur lors du chargement de la configuration: {e}")
            self._load_default_config()

    def _load_default_config(self):
        """Charge une configuration par défaut minimale en cas d'erreur"""
        self.optimizer_config = {
            "technical": {
                "optimization": {
                    "num_portfolios": 100,
                    "max_iterations": 1000,
                    "weight_bounds": [0, 1],
                    "min_weight_display": 0.01,
                },
                "charting": {
                    "figure_size": [10, 6],
                    "dpi": 100,
                    "colors": {
                        "efficient_frontier": "#1e3a8a",
                        "current_portfolio": "#b23a3a",
                        "optimal_portfolio": "#b29965",
                    },
                    "marker_size": 133,
                    "line_width": 2.5,
                },
            },
            "interpretation_thresholds": {
                "strong_improvement": 0.5,
                "moderate_improvement": 0.2,
                "near_optimal": -0.1,
            },
            "asset_classification": {"tickers": {}, "keywords": {}},
            "profiles": {
                "default": {
                    "market_parameters": {"risk_free_rate": 0.03},
                    "asset_statistics": {},
                    "correlations": [],
                }
            },
        }

    def _load_active_profile(self):
        """Charge le profil d'investisseur actif"""
        try:
            analysis_config = self.config.get("analysis", {})
            profile_name = analysis_config.get("active_profile", "default")

            profiles = self.optimizer_config.get("profiles", {})
            if profile_name not in profiles:
                self.logger.warning(
                    f"Profil '{profile_name}' non trouvé. Utilisation du profil 'default'."
                )
                profile_name = "default"

            self.active_profile = profiles[profile_name]
            self.profile_name = profile_name

            # Extraire les paramètres du profil
            market_params = self.active_profile.get("market_parameters", {})
            self.risk_free_rate = market_params.get("risk_free_rate", 0.03)

            self.asset_stats = self.active_profile.get("asset_statistics", {})

            # Construire la matrice de corrélation
            self.correlation_defaults = {}
            for corr in self.active_profile.get("correlations", []):
                if len(corr) == 3:
                    class1, class2, value = corr
                    key = tuple(sorted([class1, class2]))
                    self.correlation_defaults[key] = value

            # Stocker la configuration de classification
            self.asset_classification = self.optimizer_config.get(
                "asset_classification", {}
            )

            self.logger.info(
                f"Profil chargé: '{profile_name}' - {self.active_profile.get('description', '')}"
            )

        except Exception as e:
            self.logger.error(f"Erreur lors du chargement du profil: {e}")
            # Valeurs par défaut minimales
            self.risk_free_rate = 0.03
            self.asset_stats = {}
            self.correlation_defaults = {}
            self.asset_classification = {}
            self.profile_name = "default"

    def analyze(self, data: dict) -> Dict[str, Any]:
        """
        Point d'entrée principal
        Retourne les métriques d'optimisation de portefeuille
        """
        self.logger.info(
            "Analyse optimisation de portefeuille (Markowitz simplifié)..."
        )

        try:
            # 1. Extraire et classifier les positions
            positions = self._extract_and_classify_positions(data)

            if len(positions) < 2:
                self.logger.warning("Moins de 2 positions, skip optimisation Markowitz")
                return self._empty_result()

            # 2. Agréger par classe d'actifs
            aggregated = self._aggregate_by_asset_class(positions)

            if len(aggregated) < 2:
                self.logger.warning("Moins de 2 classes d'actifs, skip optimisation")
                return self._empty_result()

            self.logger.info(f"  → {len(aggregated)} classes d'actifs identifiées")

            # 3. Créer vecteurs rendement et matrice de covariance
            asset_classes = list(aggregated.keys())
            mean_returns = np.array(
                [self._get_asset_stats(ac)["rendement"] for ac in asset_classes]
            )
            volatilities = np.array(
                [self._get_asset_stats(ac)["volatilite"] for ac in asset_classes]
            )
            cov_matrix = self._build_covariance_matrix(asset_classes, volatilities)

            # 4. Calculer portefeuille actuel
            current_weights = np.array(
                [aggregated[ac]["poids"] for ac in asset_classes]
            )
            current_perf = self._calculate_portfolio_performance(
                current_weights, mean_returns, cov_matrix
            )

            # 5. Calculer frontière efficiente
            self.logger.info("  → Calcul frontière efficiente...")
            efficient_frontier, inefficient_frontier = (
                self._calculate_efficient_frontier(mean_returns, cov_matrix)
            )

            # 6. Trouver portefeuille optimal (max Sharpe)
            optimal_weights = self._find_optimal_portfolio(mean_returns, cov_matrix)
            optimal_perf = self._calculate_portfolio_performance(
                optimal_weights, mean_returns, cov_matrix
            )

            # 7. Générer graphique
            self.logger.info("  → Génération graphique...")
            chart_base64 = self._generate_chart(
                efficient_frontier,
                inefficient_frontier,
                current_perf,
                optimal_perf,
                asset_classes,
            )

            # 8. Construire résultat
            # Charger le seuil d'affichage depuis la configuration
            min_weight = (
                self.optimizer_config.get("technical", {})
                .get("optimization", {})
                .get("min_weight_display", 0.01)
            )

            result = {
                "portefeuille_actuel": {
                    "rendement_annuel": round(current_perf["return"] * 100, 2),
                    "volatilite_annuelle": round(current_perf["volatility"] * 100, 2),
                    "ratio_sharpe": round(current_perf["sharpe"], 2),
                    "repartition": {
                        ac: round(aggregated[ac]["poids"] * 100, 1)
                        for ac in asset_classes
                    },
                },
                "portefeuille_optimal": {
                    "rendement_annuel": round(optimal_perf["return"] * 100, 2),
                    "volatilite_annuelle": round(optimal_perf["volatility"] * 100, 2),
                    "ratio_sharpe": round(optimal_perf["sharpe"], 2),
                    "repartition": {
                        ac: round(w * 100, 1)
                        for ac, w in zip(asset_classes, optimal_weights)
                        if w > min_weight
                    },
                },
                "frontiere_efficiente": {
                    "points": len(efficient_frontier),
                    "rendement_min": round(
                        min([p["return"] for p in efficient_frontier]) * 100, 2
                    ),
                    "rendement_max": round(
                        max([p["return"] for p in efficient_frontier]) * 100, 2
                    ),
                },
                "graphique_base64": chart_base64,
                "taux_sans_risque": round(self.risk_free_rate * 100, 2),
                "interpretation": self._generate_interpretation(
                    current_perf, optimal_perf
                ),
                "methode": "Estimations statistiques moyennes par classe d'actifs",
            }

            self.logger.info(
                f"✓ Optimisation terminée - Sharpe actuel: {result['portefeuille_actuel']['ratio_sharpe']:.2f}, optimal: {result['portefeuille_optimal']['ratio_sharpe']:.2f}"
            )
            return result

        except Exception as e:
            self.logger.error(f"Erreur optimisation Markowitz: {e}")
            import traceback

            traceback.print_exc()
            return self._empty_result()

    def _extract_and_classify_positions(self, data: dict) -> List[Dict[str, Any]]:
        """Extrait et classifie toutes les positions par classe d'actifs"""
        positions = []

        for etab in (
            data.get("patrimoine", {}).get("financier", {}).get("etablissements", [])
        ):
            for compte in etab.get("comptes", []):
                # Classification par type de compte
                compte_type = compte.get("type", "").lower()

                # 1. Extraire les positions (actions, ETF avec ticker)
                for pos in compte.get("positions", []):
                    if pos.get("valeur", 0) > 0:
                        # Classifier la position
                        asset_class = self._classify_position(pos, compte_type)

                        positions.append(
                            {
                                "ticker": pos.get("ticker", ""),
                                "valeur": pos["valeur"],
                                "classe": asset_class,
                            }
                        )

                # 2. Extraire les fonds d'assurance-vie (SAUF fonds euro et monétaires)
                for fonds in compte.get("fonds", []):
                    montant = fonds.get("montant", 0)
                    if montant > 0:
                        nom_fonds = fonds.get("nom", "").lower()
                        asset_class = self._classify_fonds(nom_fonds)

                        # EXCLUSION: Fonds euro et immobilier (non liquides)
                        if asset_class not in ["fonds_euro", "immobilier"]:
                            positions.append(
                                {
                                    "ticker": fonds.get("nom", "FONDS"),
                                    "valeur": montant,
                                    "classe": asset_class,
                                }
                            )

                # 3. Les livrets, PEL, PER, comptes courants sont EXCLUS (actifs sans risque)
                # L'immobilier est EXCLU (actif non liquide)

        # Ajouter crypto
        crypto_total = data.get("patrimoine", {}).get("crypto", {}).get("total", 0)
        if crypto_total > 0:
            positions.append(
                {"ticker": "CRYPTO", "valeur": crypto_total, "classe": "crypto"}
            )

        # Ajouter or
        or_total = data.get("patrimoine", {}).get("metaux_precieux", {}).get("total", 0)
        if or_total > 0:
            positions.append({"ticker": "OR", "valeur": or_total, "classe": "or"})

        return positions

    def _classify_fonds(self, nom_fonds: str) -> str:
        """Classifie un fonds d'assurance-vie selon son nom"""
        nom = nom_fonds.lower()

        keywords = self.asset_classification.get("keywords", {})

        # Parcourir chaque classe d'actifs et ses mots-clés
        for asset_class, keyword_list in keywords.items():
            if any(keyword in nom for keyword in keyword_list):
                # Cas particulier: "euro" peut être à la fois fonds_euro et actions_europe
                if asset_class == "actions_europe" and "action" not in nom:
                    continue
                return asset_class

        # Par défaut: actions monde (fonds diversifiés)
        return "actions_monde"

    def _classify_position(self, position: dict, compte_type: str) -> str:
        """Classifie une position selon son ticker et le type de compte"""
        ticker = position.get("ticker", "").upper()
        nom = position.get("nom", "").lower()

        # Filtrer les tickers invalides
        if ticker in ["NAN", "NULL", "NONE", ""]:
            ticker = ""

        # Livrets réglementés
        if any(x in compte_type for x in ["livret", "ldds", "pel", "lep"]):
            return "livrets"

        # Fonds euro (AV)
        if "fonds euro" in nom or "fonds en euro" in nom:
            return "fonds_euro"

        # Classification par ticker depuis la configuration
        tickers_config = self.asset_classification.get("tickers", {})
        for asset_class, ticker_list in tickers_config.items():
            if any(t in ticker for t in ticker_list):
                return asset_class

        # Classification par mots-clés dans le nom (obligations)
        if "oblig" in nom:
            if "corp" in nom:
                return "obligations_corp"
            return "obligations_etat"

        # ISINs (12 caractères, format XX0123456789)
        if ticker and len(ticker) == 12 and ticker[:2].isalpha():
            # ISINs actions: USA, France, Luxembourg, Irlande, Allemagne, etc.
            if ticker[:2] in ["US", "FR", "LU", "IE", "DE", "NL", "GB", "CH", "CA"]:
                return "actions_monde"  # Hypothèse: ISINs = actions
            return "autre"

        # Par défaut: actions si c'est un ticker court, sinon autre
        if ticker and len(ticker) <= 10:
            return "actions_monde"  # Hypothèse conservative

        return "autre"

    def _aggregate_by_asset_class(self, positions: List[Dict]) -> Dict[str, Dict]:
        """Agrège les positions par classe d'actifs"""
        total_value = sum(p["valeur"] for p in positions)
        aggregated = {}

        for pos in positions:
            classe = pos["classe"]
            if classe not in aggregated:
                aggregated[classe] = {"valeur": 0, "poids": 0}

            aggregated[classe]["valeur"] += pos["valeur"]

        # Calculer les poids
        for classe in aggregated:
            aggregated[classe]["poids"] = aggregated[classe]["valeur"] / total_value

        return aggregated

    def _get_asset_stats(self, asset_class: str) -> Dict[str, float]:
        """Retourne les stats (rendement, volatilité) pour une classe d'actifs"""
        # Regrouper les variantes
        if asset_class.startswith("actions"):
            if asset_class in self.asset_stats:
                return self.asset_stats[asset_class]
            return self.asset_stats["actions_monde"]

        if asset_class.startswith("obligations"):
            if asset_class in self.asset_stats:
                return self.asset_stats[asset_class]
            return self.asset_stats["obligations_etat"]

        return self.asset_stats.get(asset_class, self.asset_stats["autre"])

    def _build_covariance_matrix(
        self, asset_classes: List[str], volatilities: np.ndarray
    ) -> np.ndarray:
        """Construit la matrice de covariance à partir des volatilités et corrélations"""
        n = len(asset_classes)
        cov_matrix = np.zeros((n, n))

        for i in range(n):
            for j in range(n):
                if i == j:
                    # Variance sur la diagonale
                    cov_matrix[i, j] = volatilities[i] ** 2
                else:
                    # Covariance = corr(i,j) × vol(i) × vol(j)
                    corr = self._get_correlation(asset_classes[i], asset_classes[j])
                    cov_matrix[i, j] = corr * volatilities[i] * volatilities[j]

        return cov_matrix

    def _get_correlation(self, class1: str, class2: str) -> float:
        """Retourne la corrélation entre deux classes d'actifs"""

        # Simplifier les noms pour matching
        def simplify(name):
            if name.startswith("actions"):
                return "actions"
            if name.startswith("obligations"):
                return "obligations"
            return name

        simple1 = simplify(class1)
        simple2 = simplify(class2)

        # Ordre canonique
        key = tuple(sorted([simple1, simple2]))

        return self.correlation_defaults.get(key, 0.3)  # Corrélation par défaut modérée

    def _calculate_portfolio_performance(
        self, weights: np.ndarray, mean_returns: np.ndarray, cov_matrix: np.ndarray
    ) -> Dict[str, float]:
        """Calcule rendement, volatilité et ratio de Sharpe d'un portefeuille"""
        portfolio_return = np.dot(weights, mean_returns)
        portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_volatility

        return {
            "return": portfolio_return,
            "volatility": portfolio_volatility,
            "sharpe": sharpe_ratio,
        }

    def _calculate_efficient_frontier(
        self,
        mean_returns: np.ndarray,
        cov_matrix: np.ndarray,
        num_portfolios: int = None,
    ) -> tuple:
        """
        Calcule la frontière efficiente et inefficiente
        Retourne: (efficient_frontier, inefficient_frontier)
        """
        # Charger le paramètre depuis la configuration
        if num_portfolios is None:
            num_portfolios = (
                self.optimizer_config.get("technical", {})
                .get("optimization", {})
                .get("num_portfolios", 100)
            )

        n_assets = len(mean_returns)

        # 1. Trouver le point de variance minimale
        min_vol_weights = self._find_min_variance_portfolio(mean_returns, cov_matrix)
        min_vol_perf = self._calculate_portfolio_performance(
            min_vol_weights, mean_returns, cov_matrix
        )
        min_efficient_return = min_vol_perf["return"]

        # 2. Calculer la frontière EFFICIENTE (au-dessus du point de variance min)
        max_return = mean_returns.max()
        target_returns_eff = np.linspace(
            min_efficient_return, max_return, num_portfolios
        )

        efficient_frontier = []
        for target in target_returns_eff:
            weights = self._minimize_volatility(mean_returns, cov_matrix, target)
            if weights is not None:
                perf = self._calculate_portfolio_performance(
                    weights, mean_returns, cov_matrix
                )
                efficient_frontier.append(perf)

        # 3. Calculer la frontière INEFFICIENTE (en dessous du point de variance min)
        min_return = mean_returns.min()
        target_returns_ineff = np.linspace(
            min_return, min_efficient_return, num_portfolios // 2
        )

        inefficient_frontier = []
        for target in target_returns_ineff:
            weights = self._minimize_volatility(mean_returns, cov_matrix, target)
            if weights is not None:
                perf = self._calculate_portfolio_performance(
                    weights, mean_returns, cov_matrix
                )
                # Ne garder que si en dessous du point de variance min
                if perf["return"] < min_efficient_return:
                    inefficient_frontier.append(perf)

        return efficient_frontier, inefficient_frontier

    def _find_min_variance_portfolio(
        self, mean_returns: np.ndarray, cov_matrix: np.ndarray
    ) -> np.ndarray:
        """Trouve le portefeuille de variance minimale (point de départ de la frontière)"""
        n_assets = len(mean_returns)

        # Charger les paramètres depuis la configuration
        opt_config = self.optimizer_config.get("technical", {}).get("optimization", {})
        max_iter = opt_config.get("max_iterations", 1000)
        weight_bounds = opt_config.get("weight_bounds", [0, 1])

        def portfolio_variance(weights):
            return np.dot(weights.T, np.dot(cov_matrix, weights))

        constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1}
        bounds = tuple((weight_bounds[0], weight_bounds[1]) for _ in range(n_assets))
        initial_weights = np.array([1 / n_assets] * n_assets)

        result = minimize(
            portfolio_variance,
            initial_weights,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": max_iter},
        )

        return result.x if result.success else initial_weights

    def _minimize_volatility(
        self, mean_returns: np.ndarray, cov_matrix: np.ndarray, target_return: float
    ) -> np.ndarray:
        """Trouve les poids qui minimisent la volatilité pour un rendement cible"""
        n_assets = len(mean_returns)

        # Charger les paramètres depuis la configuration
        opt_config = self.optimizer_config.get("technical", {}).get("optimization", {})
        max_iter = opt_config.get("max_iterations", 1000)
        weight_bounds = opt_config.get("weight_bounds", [0, 1])

        def portfolio_volatility(weights):
            return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

        constraints = [
            {"type": "eq", "fun": lambda w: np.sum(w) - 1},
            {"type": "eq", "fun": lambda w: np.dot(w, mean_returns) - target_return},
        ]

        bounds = tuple((weight_bounds[0], weight_bounds[1]) for _ in range(n_assets))
        initial_weights = np.array([1 / n_assets] * n_assets)

        result = minimize(
            portfolio_volatility,
            initial_weights,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": max_iter},
        )

        return result.x if result.success else None

    def _find_optimal_portfolio(
        self, mean_returns: np.ndarray, cov_matrix: np.ndarray
    ) -> np.ndarray:
        """Trouve le portefeuille avec le ratio de Sharpe maximal"""
        n_assets = len(mean_returns)

        # Charger les paramètres depuis la configuration
        opt_config = self.optimizer_config.get("technical", {}).get("optimization", {})
        max_iter = opt_config.get("max_iterations", 1000)
        weight_bounds = opt_config.get("weight_bounds", [0, 1])

        def negative_sharpe(weights):
            perf = self._calculate_portfolio_performance(
                weights, mean_returns, cov_matrix
            )
            return -perf["sharpe"]

        constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1}
        bounds = tuple((weight_bounds[0], weight_bounds[1]) for _ in range(n_assets))
        initial_weights = np.array([1 / n_assets] * n_assets)

        result = minimize(
            negative_sharpe,
            initial_weights,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": max_iter},
        )

        return result.x if result.success else initial_weights

    def _generate_chart(
        self,
        efficient_frontier: List[Dict],
        inefficient_frontier: List[Dict],
        current: Dict,
        optimal: Dict,
        asset_classes: List[str],
    ) -> str:
        """Génère le graphique de la frontière efficiente"""
        # Charger les paramètres graphiques depuis la configuration
        chart_config = self.optimizer_config.get("technical", {}).get("charting", {})
        colors = chart_config.get("colors", {})
        figsize = tuple(chart_config.get("figure_size", [10, 6]))
        dpi = chart_config.get("dpi", 100)
        marker_size = chart_config.get("marker_size", 133)
        line_width = chart_config.get("line_width", 2.5)
        line_width_inef = chart_config.get("line_width_inefficient", 1.5)

        plt.rcParams["font.family"] = "DejaVu Sans"

        fig, ax = plt.subplots(figsize=figsize, facecolor="white")

        # Frontière efficiente (partie haute)
        ef_vols = [p["volatility"] * 100 for p in efficient_frontier]
        ef_rets = [p["return"] * 100 for p in efficient_frontier]
        ax.plot(
            ef_vols,
            ef_rets,
            color=colors.get("efficient_frontier", "#1e3a8a"),
            linewidth=line_width,
            label="Frontière efficiente",
        )

        # Frontière inefficiente (partie basse, en pointillés)
        if inefficient_frontier and len(inefficient_frontier) > 1:
            # Trier par volatilité DÉCROISSANTE pour descendre vers la gauche
            sorted_inef = sorted(
                inefficient_frontier, key=lambda p: p["volatility"], reverse=True
            )
            inef_vols = [p["volatility"] * 100 for p in sorted_inef]
            inef_rets = [p["return"] * 100 for p in sorted_inef]
            ax.plot(
                inef_vols,
                inef_rets,
                color=colors.get("inefficient_frontier", "#1e3a8a"),
                linestyle="--",
                linewidth=line_width_inef,
                alpha=0.7,
                label="Frontière inefficiente",
            )

        # Portefeuille actuel
        ax.scatter(
            current["volatility"] * 100,
            current["return"] * 100,
            color=colors.get("current_portfolio", "#b23a3a"),
            marker="o",
            s=marker_size,
            label=f"Portefeuille actuel (Sharpe: {current['sharpe']:.2f})",
            zorder=5,
            edgecolors="#7a1e1e",
            linewidths=2,
        )

        # Portefeuille optimal
        ax.scatter(
            optimal["volatility"] * 100,
            optimal["return"] * 100,
            color=colors.get("optimal_portfolio", "#b29965"),
            marker="o",
            s=marker_size,
            label=f"Portefeuille optimal (Sharpe: {optimal['sharpe']:.2f})",
            zorder=5,
            edgecolors="#7f683b",
            linewidths=2,
        )

        # Taux sans risque
        ax.axhline(
            y=self.risk_free_rate * 100,
            color=colors.get("risk_free_line", "gray"),
            linestyle="--",
            alpha=0.5,
            label=f"Taux sans risque ({self.risk_free_rate * 100:.1f}%)",
        )

        ax.set_xlabel("Volatilité annuelle (%)", fontsize=11)
        ax.set_ylabel("Rendement annuel espéré (%)", fontsize=11)
        ax.set_title(
            "Frontière Efficiente de Markowitz\n(Estimations par classe d'actifs)",
            fontsize=13,
            fontweight="bold",
        )
        ax.legend(loc="best", fontsize=9)
        ax.grid(True, alpha=0.3)

        # Sauvegarder en base64
        buffer = BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format="png", dpi=dpi, bbox_inches="tight")
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode("utf-8")
        plt.close(fig)

        return f"data:image/png;base64,{image_base64}"

    def _generate_interpretation(self, current: Dict, optimal: Dict) -> str:
        """Génère une interprétation textuelle des résultats"""
        sharpe_diff = optimal["sharpe"] - current["sharpe"]

        # Charger les seuils depuis la configuration
        thresholds = self.optimizer_config.get("interpretation_thresholds", {})
        strong_improvement = thresholds.get("strong_improvement", 0.5)
        moderate_improvement = thresholds.get("moderate_improvement", 0.2)
        near_optimal = thresholds.get("near_optimal", -0.1)

        if sharpe_diff > strong_improvement:
            return "Forte amélioration possible : le portefeuille actuel est significativement sous-optimal. Une réallocation pourrait améliorer sensiblement le ratio rendement/risque."
        elif sharpe_diff > moderate_improvement:
            return "Amélioration modérée possible : une réallocation vers le portefeuille optimal pourrait améliorer le ratio rendement/risque."
        elif sharpe_diff > near_optimal:
            return "Portefeuille proche de l'optimum : l'allocation actuelle est déjà relativement efficiente selon les estimations statistiques."
        else:
            return "Portefeuille au-dessus de l'optimum calculé : cela peut indiquer des contraintes spécifiques (fiscalité, liquidité) non modélisées."

    def _empty_result(self) -> Dict[str, Any]:
        """Retourne un résultat vide en cas d'échec"""
        return {
            "portefeuille_actuel": None,
            "portefeuille_optimal": None,
            "frontiere_efficiente": None,
            "graphique_base64": None,
            "taux_sans_risque": round(self.risk_free_rate * 100, 2),
            "interpretation": "Analyse non disponible : moins de 2 classes d'actifs identifiées.",
            "methode": "Non applicable",
        }
