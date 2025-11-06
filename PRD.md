# PRD : Générateur de Rapport Patrimonial Automatisé

**Version** : 1.0.0
**Date** : Octobre 2025
**Auteur** : Spécifications pour Claude Code

---

## Table des matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Architecture du projet](#2-architecture-du-projet)
3. [Spécifications des outils](#3-spécifications-des-outils)
4. [Script principal](#4-script-principal)
5. [Configuration](#5-configuration)
6. [Logs](#6-logs)
7. [Tests et validation](#7-tests-et-validation)
8. [Évolutions futures](#8-évolutions-futures)
9. [Contraintes et limitations](#9-contraintes-et-limitations)
10. [Glossaire](#10-glossaire)

---

## 1. Vue d'ensemble

### 1.1 Objectif

Créer un système automatisé permettant de générer régulièrement des rapports patrimoniaux détaillés et professionnels à partir de fichiers sources (CSV, PDF, Markdown), en passant par une phase d'analyse approfondie avec recherches web.

### 1.2 Workflow global

```
patrimoine.md (+ fichiers CSV/PDF)
    ↓
[1. Normalisation] → patrimoine_input.json (structure normalisée)
    ↓
[2. Analyse approfondie + Web Research] → patrimoine_analysis.json
    ↓
[3. Génération HTML] → rapport_YYYYMMDD_HHMMSS.html
```

### 1.3 Principe directeur

- **Un seul point d'entrée** : `patrimoine.md` (+ références aux fichiers sources)
- **Une seule commande** : `python main.py` - aucune interaction durant l'exécution
- **Séparation stricte** : Les outils ne modifient JAMAIS les fichiers templates ou sources
- **Historisation** : Chaque rapport est daté et conservé

---

## 2. Architecture du projet

### 2.1 Arborescence complète

```
patrimoine-analyzer/
│
├── README.md                          # Documentation principale du projet
├── requirements.txt                   # Dépendances Python
├── .gitignore                         # Ignore logs, generated/, .env
│
├── sources/                           # 📥 INPUTS : Fichiers sources (utilisateur)
│   ├── patrimoine.md                  # Point d'entrée principal
│   ├── [CA] - PEA.pdf
│   ├── [CA] - PEA-PME.pdf
│   ├── [CA] - AV.pdf
│   ├── [DGO] - CTO.csv
│   ├── [BFB] - CTO.pdf
│   ├── [BOB] - PER.pdf
│   ├── [CRYP] - BTC + ETH + VRO.csv
│   ├── [BIT] - BTC.csv
│   └── ... (autres fichiers référencés)
│
├── templates/                         # 📄 TEMPLATES : Modèles HTML
│   ├── rapport_template.html         # Template HTML premium (READONLY)
│   └── rapport.css                    # Feuille de style (incorporée dans HTML final)
│
├── generated/                         # 📤 OUTPUTS : Fichiers générés
│   ├── patrimoine_input.json         # JSON normalisé (étape 1)
│   ├── patrimoine_analysis.json      # JSON analyse complète (étape 2)
│   ├── rapport_20251021_143022.html  # Rapport HTML final (étape 3)
│   └── ... (historique)
│
├── tools/                             # 🛠️ OUTILS : Scripts Python
│   ├── __init__.py
│   ├── normalizer.py                  # [1] Normalisation
│   ├── analyzer.py                    # [2] Analyse + Web Research
│   ├── generator.py                   # [3] Génération HTML
│   └── utils/
│       ├── __init__.py
│       ├── file_parser.py             # Parsing CSV/PDF/JSON
│       ├── web_research.py            # Recherches web (Anthropic)
│       ├── risk_analyzer.py           # Analyse de risques
│       ├── recommendations.py         # Génération recommandations
│       ├── stress_tester.py           # Stress tests
│       ├── portfolio_optimizer.py     # Optimisation Markowitz
│       └── benchmark_gap.py           # Calcul écart aux benchmarks
│
├── logs/                              # 📋 LOGS : Fichiers de logs
│   └── rapport_YYYYMMDD_HHMMSS.log
│
├── config/                            # ⚙️ CONFIG : Configuration
│   ├── config.yaml                    # Configuration globale
│   ├── analysis.yaml                  # Configuration analyse et optimisation
│   └── research_prompts.yaml          # Prompts pour recherches web
│
└── main.py                            # 🚀 POINT D'ENTRÉE
```

### 2.2 Responsabilités des répertoires

| Répertoire | Rôle | Modifiable par utilisateur | Modifiable par scripts |
|------------|------|----------------------------|------------------------|
| `sources/` | Fichiers sources | ✅ Oui | ❌ Non (lecture seule) |
| `templates/` | Templates HTML | ✅ Oui | ❌ Non (lecture seule) |
| `generated/` | Fichiers générés | ❌ Non | ✅ Oui (écriture) |
| `tools/` | Scripts Python | ❌ Non | ❌ Non |
| `logs/` | Logs d'exécution | ❌ Non | ✅ Oui (écriture) |
| `config/` | Configuration | ✅ Oui (rare) | ❌ Non (lecture seule) |

---

## 3. Spécifications des outils

### 3.1 Outil 1 : Normalizer (`tools/normalizer.py`)

#### 3.1.1 Responsabilité

Convertir `patrimoine.md` (+ fichiers sources) en un JSON structuré et normalisé.

#### 3.1.2 Inputs

- `sources/patrimoine.md` (structure patrimoine)
- Fichiers référencés : CSV, PDF, JSON (dans `sources/`)
- `sources/etablissements_financiers.json` (liste des établissements financiers)
- `sources/immobilier_valorisation.json` (liste des biens immobilier avec leur valorisation)

#### 3.1.3 Output

- `generated/patrimoine_input.json`

#### 3.1.4 Structure du JSON de sortie

```json
{
  "meta": {
    "version": "1.0.0",
    "generated_at": "2025-10-21T14:30:22Z",
    "source_file": "sources/patrimoine.md"
  },
  "profil": {
    "genre": "Homme",
    "date_naissance": "1975-11-23",
    "age": 49,
    "situation_familiale": "Marié",
    "enfants": 0,
    "type_investissement": "Dynamique",
    "statut": "Actif",
    "profession": "Développement informatique",
    "revenu_mensuel_net": 3500
  },
  "patrimoine": {
    "financier": {
      "total": 352104.42,
      "etablissements": [
        {
          "nom": "Crédit Agricole",
          "code": "CA",
          "juridiction": "France",
          "total": 283714.00,
          "comptes": [
            {
              "type": "PEA",
              "montant": 85107.13,
              "source_file": "[CA] - PEA.pdf",
              "pdf_type": "PEA",
              "positions": [
                {"ticker": "VWCE", "quantite": 120, "valeur": 12000}
              ]
            },
            {
              "type": "Assurance-vie",
              "montant": 106046.01,
              "source_file": "[CA] - AV.pdf",
              "fonds": [
                {"nom": "Fonds Euro", "montant": 50000},
                {"nom": "MSCI World", "montant": 56046.01}
              ]
            }
          ]
        }
      ]
    },
    "crypto": {
      "total": 12470.47,
      "plateformes": [
        {
          "nom": "CrypCool",
          "juridiction": "France",
          "total": 1780.95,
          "actifs": [
            {"symbole": "BTC", "quantite": 0.01, "valeur": 800}
          ]
        }
      ]
    },
    "metaux_precieux": {
      "total": 4102.30,
      "plateforme": "Veracash",
      "juridiction": "Suisse",
      "metaux": [
        {"type": "Or", "valeur": 3355.69}
      ]
    },
    "immobilier": {
      "total": 131375.00,
      "biens": [
        {
          "type": "Studio",
          "adresse": "34, rue Salvador Allende, 92000 Nanterre",
          "surface_m2": 25,
          "prix_acquisition": 110000,
          "valeur_actuelle": 131375
        }
      ]
    }
  },
  "sources_files": [
    "[CA] - PEA.pdf",
    "[CA] - PEA-PME.pdf",
    "[CA] - AV.pdf",
    "[DGO] - CTO.csv"
  ]
}
```

#### 3.1.5 Fonctionnalités clés

1. **Parsing de `patrimoine.md`**
   - Extraction structure (profil, établissements, comptes)
   - Détection références fichiers sources

2. **Lecture fichiers sources**
   - CSV : parsing avec pandas
   - PDF : extraction texte + tableaux (pdfplumber)
   - JSON : lecture directe

3. **Normalisation**
   - Conversion montants en float
   - Dates en ISO 8601
   - Calcul totaux par catégorie/établissement

4. **Validation**
   - Vérification fichiers référencés existent
   - Cohérence des montants
   - Schéma JSON valide

---

### 3.2 Outil 2 : Analyzer (`tools/analyzer.py`)

#### 3.2.1 Responsabilité

Analyser le patrimoine en profondeur avec recherches web exhaustives et générer des recommandations prioritisées.

#### 3.2.2 Inputs

- `generated/patrimoine_input.json`

#### 3.2.3 Output

- `generated/patrimoine_analysis.json`

#### 3.2.4 Structure du JSON de sortie

```json
{
  "meta": {
    "version": "1.0.0",
    "generated_at": "2025-10-21T14:45:30Z",
    "analysis_duration_seconds": 180,
    "web_searches_count": 47
  },
  "synthese": {
    "patrimoine_total": 470354,
    "patrimoine_financier": 352104,
    "patrimoine_immobilier": 131375,
    "score_global": 7.5,
    "scores_details": {
      "diversification": 8,
      "resilience": 7.5,
      "liquidite": 6.5,
      "fiscalite": 7,
      "croissance": 8.5
    },
    "diversification_details": {
      "score": 8.0,
      "label": "Bonne diversification",
      "details": {
        "score_institutional": 7.5,
        "score_jurisdictional": 8.8,
        "score_weighted": 8.0,
        "bonus_total": 1.0,
        "bonus_details": {
          "classes_actifs": {"count": 6, "bonus": 1.0}
        },
        "nb_classes_actifs": 6,
        "nb_positions": 8,
        "pct_international": 12.5
      }
    },
    "resilience_details": {
      "score": 7.5,
      "label": "Patrimoine solide"
    },
    "liquidity_details": {
      "score": 10.0,
      "label": "Excellente liquidité",
      "details": {
        "liquidite_actuelle": 34727.29,
        "liquidite_cible": 29400.00,
        "ratio": 1.18,
        "target_months": 12,
        "depenses_mensuelles": 2450.00,
        "is_overliquid": false,
        "overliquidity_threshold": 1.5
      }
    },
    "fiscal_details": {
      "score": 9.0,
      "label": "Optimisation fiscale excellente",
      "details": {
        "pea_total": 91814.60,
        "cto_total": 35338.36,
        "av_total": 106046.01,
        "per_total": 4596.76,
        "crypto_total": 11377.16,
        "crypto_percentage": 2.4,
        "pea_over_cto": true,
        "has_per": false,
        "bonuses_applied": {
          "pea_over_cto": 1.5,
          "av_succession": 0.5
        },
        "penalties_applied": {}
      }
    },
    "growth_details": {
      "score": 4.0,
      "label": "Potentiel de croissance limité",
      "details": {
        "exposition_actions": 127153.00,
        "patrimoine_financier": 333119.00,
        "pct_actions": 38.2,
        "profil_actif": "default",
        "optimal_range": [60, 70],
        "interpretation": "Fortement sous-exposé (optimal : 60-70%)"
      }
    },
    "risque_principal": "Concentration institutionnelle",
    "priorites": "Diversification géographique et réduction AV"
  },
  "repartition": {
    "par_etablissement": [
      {
        "nom": "Crédit Agricole",
        "juridiction": "France",
        "montant": 283714,
        "pourcentage": 80.6,
        "niveau_risque": "Critique",
        "justification": "Concentration excessive"
      }
    ],
    "par_classe_actifs": [
      {
        "type_actif": "Actions",
        "etablissement": "Crédit Agricole (PEA)",
        "montant": 82345.00,
        "pourcentage": 17.5,
        "benchmark_gap": {
          "ecart_pct": 5.0,
          "ecart_borne": 0.0,
          "status": "sur_pondere_modere",
          "niveau": "normal",
          "message": "Légèrement sur-pondéré (5.0 pts au-dessus de la cible)"
        }
      },
      {
        "type_actif": "Actions",
        "etablissement": "Crédit Agricole (AV - UC)",
        "montant": 46940.46,
        "pourcentage": 10.0,
        "benchmark_gap": {
          "ecart_pct": 0.0,
          "ecart_borne": 0.0,
          "status": "dans_la_cible",
          "niveau": "normal",
          "message": "Dans la cible (65%)"
        }
      },
      {
        "type_actif": "Obligations",
        "etablissement": "Crédit Agricole (AV - Fonds Euro)",
        "montant": 59105.45,
        "pourcentage": 12.5,
        "benchmark_gap": {
          "ecart_pct": -2.5,
          "ecart_borne": -2.5,
          "status": "sous_pondere_modere",
          "niveau": "attention",
          "message": "Sous-pondéré (2.5 pts sous le minimum 15%)"
        }
      }
    ],
    "concentration": {
      "france": {
        "montant": 307500,
        "pourcentage": 87.4,
        "niveau_risque": "Critique"
      }
    }
  },
  "risques": {
    "critiques": [
      {
        "id": "RISK_001",
        "titre": "Loi Sapin 2 - Blocage assurance-vie",
        "description": "Risque de gel temporaire de l'AV en cas de crise bancaire",
        "exposition_montant": 106046,
        "exposition_pct": 30.1,
        "probabilite": "Moyenne",
        "impact": "Élevé",
        "niveau": "Critique",
        "sources_web": [
          {
            "url": "https://www.economie.gouv.fr/hcsf",
            "titre": "HCSF - Article 21 Loi Sapin 2",
            "date_acces": "2025-10-21",
            "extrait": "Le HCSF peut suspendre..."
          }
        ]
      }
    ],
    "eleves": [],
    "moyens": [],
    "faibles": []
  },
  "recommandations": {
    "prioritaires": [
      {
        "id": "REC_001",
        "priorite": 9.2,
        "titre": "Réduire exposition Loi Sapin 2",
        "description": "Transférer 40 000€ de l'AV vers PEA",
        "benefice": "Réduction exposition de 30.1% à 18.8%",
        "montant": 40000,
        "delai_jours": 30,
        "difficulte": "Faible",
        "actions_concretes": [
          "Racheter 40 000€ de l'AV",
          "Investir dans PEA disponible"
        ],
        "risques_mitigues": ["RISK_001"]
      }
    ],
    "secondaires": [],
    "long_terme": []
  },
  "stress_tests": [
    {
      "scenario": "Crise bancaire + Sapin 2",
      "description": "Blocage AV + gel partiel dépôts",
      "impact_montant": -127972,
      "impact_pct": -36.3,
      "patrimoine_accessible": 224132,
      "severite": "Haute",
      "duree_estimee": "3-12 mois"
    },
    {
      "scenario": "Krach actions -30%",
      "description": "Correction majeure type 2008",
      "impact_montant": -78388,
      "impact_pct": -16.7,
      "patrimoine_final": 391966,
      "severite": "Moyenne"
    }
  ],
  "recherches_web": [
    {
      "sujet": "Loi Sapin 2",
      "query": "Loi Sapin 2 blocage assurance-vie 2025",
      "date": "2025-10-21T14:30:00Z",
      "sources_found": 3
    }
  ]
}
```

#### 3.2.5 Modules d'analyse

##### 3.2.5.1 Analyse de répartition

- Calcul répartition par établissement, classe d'actifs, juridiction
- Détection concentrations excessives
- **Agrégation automatique** : Les actifs multiples d'un même type dans un établissement sont agrégés en une seule ligne (ex: tous les fonds UC de l'AV → une ligne "Actions AV - UC")
- **Calcul d'écart aux benchmarks** : Comparaison de l'allocation réelle avec les benchmarks cibles par profil d'investisseur (`tools/utils/benchmark_gap.py`)
  - **Cibles médianes** : Chaque classe d'actifs a une fourchette `{min, target, max}` selon le profil
  - **Écart calculé** : Différence en points de pourcentage par rapport à la cible médiane
  - **5 niveaux de status** :
    - `dans_la_cible` : Écart ≤ 2 pts de la cible (normal)
    - `sous_pondere_modere` / `sur_pondere_modere` : Hors fourchette < 10 pts (attention)
    - `sous_pondere_fort` / `sur_pondere_fort` : Hors fourchette ≥ 10 pts (alerte)
  - **Affichage** : Message descriptif + badge CSS coloré si écart significatif

**Classification des types de comptes** (ligne 216-245 de `analyzer.py`) :

| Classe d'actifs | Types de comptes inclus |
|----------------|-------------------------|
| **Liquidités** | Livret A, LDD, **PEL** (Plan d'Épargne Logement), Compte de dépôts |
| **Actions** | PEA, PEA-PME, CTO, PER, Parts Sociales, Assurance-vie (UC) |
| **Obligations** | Spiko (T-Bonds), fonds obligataires en AV |
| **Cryptomonnaies** | Plateformes crypto, self-custody wallets |
| **Métaux précieux** | Or physique |
| **Immobilier** | SCPI, biens immobiliers |

**Note importante sur le PEL** : Le Plan d'Épargne Logement est classé comme "Liquidités" (épargne réglementée), et NON comme "Obligations". Le PEL est un produit d'épargne garanti par l'État avec taux fixe réglementé, similaire au Livret A et LDD. Ce n'est pas un titre de dette négociable comme une obligation.

##### 3.2.5.2 Analyse de risques (`tools/utils/risk_analyzer.py`)

**Catégories de risques à analyser** :

1. **Risques de concentration**
   - Par établissement (> 30% : alerte, > 50% : critique)
   - Par juridiction (> 60% : alerte, > 80% : critique)
   - Par classe d'actifs

2. **Risques réglementaires**
   - Loi Sapin 2 (AV)
   - Garantie dépôts (100k€)
   - Plafonds PEA/PEA-PME

3. **Risques fiscaux**
   - Évolution PFU
   - Fiscalité AV
   - IFI (si applicable)

4. **Risques de marché**
   - Volatilité actions
   - Risque de change
   - Corrélation actifs

5. **Risques de liquidité**
   - Actifs bloqués (AV, PER)
   - Immobilier

6. **Risques politiques**
   - Instabilité pays
   - Nationalisation / expropriation

7. **Risques de changes**
   - Risque de transaction
   - Risque de volatilité des devises
   - Risque économique

**Pour chaque risque** :
- Recherche web approfondie (réglementation, actualité)
- Quantification exposition (€ + %)
- Évaluation probabilité × impact
- Sources web citées

**🆕 v2.0 (Novembre 2025) : Système de détection dynamique**

Le système de détection des risques a évolué vers une **architecture hybride à 3 niveaux** pour s'adapter aux évolutions du contexte économique, légal et politique.

**Architecture** :

1. **Niveau 1 : Risques structurels** (toujours actifs)
   - Les 7 catégories ci-dessus détectées par méthodes legacy
   - Règles documentées dans `config/risks.yaml`
   - Rétrocompatibilité totale avec v1.0

2. **Niveau 2 : Risques contextuels** (optionnel, configurable)
   - Détection dynamique via recherches web automatiques
   - 6 catégories de recherches contextuelles :
     * Actualité économique France
     * Risques bancaires systémiques
     * Évolution fiscalité
     * Risques géopolitiques
     * Volatilité marchés
     * Régulation crypto
   - Génère des risques si ≥2 sources confirment
   - Identifiés par suffixe `" - Contexte"` dans la catégorie

3. **Niveau 3 : Analyse LLM** (réservé futur)
   - Classification automatique par IA
   - Génération de descriptions contextualisées

**Configuration** (`config/risks.yaml`) :
- `risk_settings` : Activation/désactivation globale
- `structural_risks` : Définitions des 13 risques structurels
- `contextual_searches` : Configuration des 6 recherches contextuelles
- `metadata` : Versioning et changelog

**Activation/Désactivation** :
```yaml
risk_settings:
  enable_contextual_detection: true  # false pour désactiver
```

**Ajout de nouveaux risques contextuels** :
```yaml
contextual_searches:
  nouvelle_reforme:
    enabled: true
    priority: "high"
    queries: ["requête 1", "requête 2"]
```

Puis ajouter le mapping dans `risk_analyzer.py` → `_get_contextual_risk_mapping()`.

**Impact performance** :
- Désactivé : Aucun impact vs v1.0
- Activé : +6-12 recherches web, +10-20s analyse

**Maintenance** : Mise à jour trimestrielle recommandée des requêtes de recherche.

##### 3.2.5.3 Génération recommandations (`tools/utils/recommendations.py`)

**Critères de priorisation** :
1. Criticité du risque mitigué (40%)
2. Impact financier (30%)
3. Facilité d'exécution (30%)

**Score** = (criticité × 0.4) + (impact × 0.3) + (facilité × 0.3)

**Recommandations types** :
- Rééquilibrage allocation
- Diversification géographique
- Optimisation fiscale
- Protection contre risques spécifiques

##### 3.2.5.4 Stress tests (`tools/utils/stress_tester.py`)

Scénarios à simuler :
1. **Crise bancaire + Sapin 2** : Blocage AV + gel partiel dépôts
2. **Krach actions -30%** : Correction majeure marchés
3. **Perte emploi 12-24 mois** : Capacité maintien niveau de vie
4. **Hausse fiscalité** : PFU 30% → 35%
5. **Crise immobilière -20%** : Correction marché local

##### 3.2.5.5 Recherches web (`tools/utils/web_research.py`)

**Sujets de recherche** :

1. **Réglementation**
   - Loi Sapin 2 dernières évolutions
   - Garantie dépôts 2025
   - Fiscalité épargne (PFU, AV, PEA)

2. **Performance fonds**
   - Fonds AV (si identifiés)
   - ETF positions (VWCE, etc.)
   - Comparaison benchmarks

3. **Taux actuels**
   - Livret A, LDDS
   - Fonds euro
   - T-Bills USD

4. **Actualité économique**
   - Politique monétaire BCE/Fed
   - Risques macro (inflation, récession)
   - Évolutions réglementaires

**Implémentation** :
- Utilisation API Brave Search (L'utilisateur dispose de sa clé API)
- Attendre entre 1,1 et 1,5 secondes entre chaque requête (C'est une limitation Brave)
- 10-15 recherches ciblées
- Toutes sources citées avec URL + date
- Pas d'invention, uniquement sources vérifiables

**Format des sources** :
```json
{
  "url": "https://www.economie.gouv.fr/...",
  "titre": "HCSF - Article 21",
  "extrait": "Le HCSF peut suspendre...",
  "pertinence": "Haute",
  "date_acces": "2025-10-21"
}
```

##### 3.2.5.6 Optimisation de portefeuille (`tools/utils/portfolio_optimizer.py`)

**Objectif** : Analyser le portefeuille selon la théorie moderne de Markowitz et calculer le ratio de Sharpe.

**Configuration** : Tous les paramètres sont externalisés dans `config/analysis.yaml` :
- **Profils d'investisseur** : 4 profils prédéfinis (default, dynamique, equilibre, prudent)
- **Statistiques par classe d'actifs** : rendements et volatilités moyennes
- **Corrélations** : matrice de corrélation entre classes d'actifs
- **Benchmarks d'allocation** : fourchettes cibles par profil avec **cibles médianes**
  - Format : `{min: %, target: %, max: %}` pour chaque classe d'actifs
  - Exemple : Actions (dynamique) → `min: 70, target: 77.5, max: 85`
  - Utilisé pour le calcul d'écart benchmark dans les rapports
- **Calcul des scores** : paramètres pour les 5 scores (diversification, résilience, liquidité, fiscalité, croissance)
- **Classification des comptes** : mots-clés et mapping pour identifier les types de comptes
- **Paramètres techniques** : itérations, contraintes, seuils d'interprétation
- **Paramètres graphiques** : couleurs, tailles, DPI

Le profil actif est sélectionné via `config.yaml` → `analysis.active_profile`.

**Données requises** :
- Positions par classe d'actifs (extraites et classifiées depuis `patrimoine.financier`, `patrimoine.crypto`, `patrimoine.metaux_precieux`)
- Statistiques moyennes par classe d'actifs (rendement, volatilité) - chargées depuis la configuration selon le profil actif
- Matrice de corrélation typique entre classes d'actifs - chargée depuis la configuration
- Méthode : **Estimations statistiques** (pas d'appel API externe pour données de marché)

**Calculs effectués** :

1. **Rendements et volatilités** :
   - Utilise des statistiques chargées depuis le profil actif (exemple profil "default") :
     - Actions monde : 8% rendement, 15% volatilité
     - Actions Europe : 7% rendement, 16% volatilité
     - Crypto : 15% rendement, 60% volatilité
     - Or : 4% rendement, 16% volatilité
     - Obligations : 3.5-4.5% rendement, 5-7% volatilité
   - Classification automatique des positions selon ticker, nom de fonds, type de compte (règles configurables dans `portfolio_optimizer.yaml`)

2. **Matrice de covariance** :
   - Calculée à partir des volatilités et corrélations typiques entre classes d'actifs
   - Corrélations chargées depuis le profil actif (ex: actions-actions 0.75, actions-obligations 0.15, actions-crypto 0.30)
   - Permet de capturer les bénéfices de diversification

3. **Frontière efficiente** :
   - Nombre de portefeuilles configurable (défaut : 100) optimisés par minimisation de la volatilité
   - Pour chaque niveau de rendement cible, trouve l'allocation minimisant le risque
   - Utilise `scipy.optimize.minimize` avec contraintes :
     - Somme des poids = 1
     - Rendement du portefeuille = cible
     - Poids entre 0 et 1 (pas de vente à découvert)

4. **Ratio de Sharpe** :
   - Formule : `(rendement - taux_sans_risque) / volatilité`
   - Taux sans risque : configurable par profil (défaut : 3% pour OAT 10 ans France)
   - Mesure le rendement excédentaire par unité de risque

5. **Portefeuille optimal** :
   - Portefeuille maximisant le ratio de Sharpe
   - Représente la meilleure allocation risque/rendement théorique

**Graphique généré** :
- Frontière efficiente (courbe bleue)
- Frontière inefficiente (courbe bleue en pointillés)
- Portefeuille actuel (point rouge) avec son ratio de Sharpe
- Portefeuille optimal (point jaune) avec son ratio de Sharpe
- Taux sans risque (ligne horizontale grise)
- Couleurs, tailles et DPI configurables dans `portfolio_optimizer.yaml`
- Format : PNG en base64 pour injection directe dans HTML

**Interprétation automatique** (seuils configurables) :
- Sharpe optimal - Sharpe actuel > 0.5 (défaut) : "Forte amélioration possible"
- Différence > 0.2 (défaut) : "Amélioration modérée possible"
- Différence > -0.1 (défaut) : "Portefeuille proche de l'optimum"
- Différence < -0.1 : "Portefeuille au-dessus de l'optimum calculé"

**Gestion des erreurs** :
- Moins de 2 classes d'actifs différentes → analyse sautée
- Montant total insuffisant (< 1000€) → analyse sautée
- Erreur dans l'optimisation scipy → analyse sautée
- Retourne toujours un objet avec `portefeuille_actuel: null` en cas d'échec

**Output JSON** :
```json
{
  "optimisation_portefeuille": {
    "portefeuille_actuel": {
      "rendement_annuel": 8.5,
      "volatilite_annuelle": 14.2,
      "ratio_sharpe": 0.42,
      "poids": {"VWCE": 45.2, "BTC": 5.1, ...}
    },
    "portefeuille_optimal": {
      "rendement_annuel": 10.2,
      "volatilite_annuelle": 12.8,
      "ratio_sharpe": 0.68,
      "poids": {"VWCE": 55.0, "IWDA": 30.0, ...}
    },
    "frontiere_efficiente": {
      "points": 100,
      "rendement_min": 5.2,
      "rendement_max": 15.8
    },
    "graphique_base64": "data:image/png;base64,iVBOR...",
    "taux_sans_risque": 3.0,
    "interpretation": "Amélioration modérée possible..."
  }
}
```

**Profils d'investisseur disponibles** :
- **default** : Statistiques historiques moyennes long terme (20-30 ans), neutres
- **dynamique** : Jeune investisseur (<40 ans), horizon long terme (20+ ans), actions favorisées (+1 à +2%), obligations pénalisées (-1%)
- **equilibre** : Âge moyen (40-55 ans), horizon moyen terme (10-20 ans), mix équilibré
- **prudent** : Proche retraite (>55 ans), horizon court (<10 ans), obligations favorisées (+0.5%), actions pénalisées (-1 à -2%)

**Limites méthodologiques** :
- **Estimations statistiques** : utilise des moyennes historiques long terme (10+ ans) et non des données de marché en temps réel
- **Pas d'API externe** : pas de téléchargement de prix via Yahoo Finance ou autre service
- **Profils simplifiés** : les 4 profils sont des approximations, à personnaliser selon les besoins via `portfolio_optimizer.yaml`
- Performances passées ≠ performances futures
- Suppose rendements normalement distribués (réalité : queues épaisses)
- Ne prend pas en compte : fiscalité, liquidité, contraintes personnelles
- Optimisation purement quantitative à combiner avec analyse qualitative

##### 3.2.5.7 Calcul enrichi du score de diversification (`tools/analyzer.py`)

**Objectif** : Mesurer la robustesse structurelle du patrimoine via un score transparent (0-10) combinant concentration institutionnelle, juridictionnelle et dispersion intra-portefeuille.

**Nouvelle méthodologie (depuis v1.1)** :

La fonction `_calculate_diversification_score()` retourne désormais un **dictionnaire enrichi** au lieu d'un simple score numérique.

**1. Calcul par composantes pondérées**

```
Score final = (Score institutionnel × 60%) + (Score juridictionnel × 40%) + Bonus
```

- **Score institutionnel** (60%) : Mesure la concentration par établissement
  - Base 10/10, pénalités si concentration excessive :
    - `> 70%` sur un établissement : -3.0 points
    - `> 50%` sur un établissement : -2.0 points
    - `> 30%` sur un établissement : -0.5 points

- **Score juridictionnel** (40%) : Mesure la concentration géographique/fiscale
  - Base 10/10, pénalité si concentration excessive :
    - `> 85%` dans une juridiction : -2.0 points

**2. Bonus de diversification intra-portefeuille**

Trois bonus cumulables pour valoriser la dispersion réelle :

| Critère | Seuil | Bonus |
|---------|-------|-------|
| Nombre de classes d'actifs distinctes | ≥ 5 | +1.0 |
| Nombre de positions/comptes individuels | ≥ 10 | +0.5 |
| Exposition internationale | > 15% | +0.5 |

**3. Labels de qualité**

Le score est automatiquement traduit en label descriptif :

| Score | Label | Couleur badge |
|-------|-------|---------------|
| 9-10 | Excellente diversification | Vert (`.low`) |
| 7-9 | Bonne diversification | Vert (`.low`) |
| 5-7 | Concentration modérée | Orange (`.mid`) |
| 3-5 | Forte concentration | Rouge clair (`.high`) |
| 0-3 | Concentration critique | Rouge foncé (`.crit`) |

**4. Structure de retour**

```python
{
  "score": 8.5,                          # Score final (0-10)
  "label": "Bonne diversification",      # Label de qualité
  "details": {
    "score_institutional": 8.0,          # Score concentration établissements
    "score_jurisdictional": 10.0,        # Score concentration juridictionnelle
    "score_weighted": 8.8,               # Score pondéré (60%/40%)
    "bonus_total": 1.5,                  # Bonus cumulés
    "bonus_details": {                   # Détail des bonus obtenus
      "classes_actifs": {"count": 6, "bonus": 1.0},
      "positions": {"count": 12, "bonus": 0.5}
    },
    "nb_classes_actifs": 6,              # Nombre de classes distinctes
    "nb_positions": 12,                  # Nombre de positions/comptes
    "pct_international": 22.5            # % exposition internationale
  }
}
```

**5. Configuration**

Tous les paramètres sont externalisés dans `config/analysis.yaml` → `scores.diversification` :
- `weights` : Pondérations institutionnel/juridictionnel
- `base_score` : Score de départ (10.0)
- `penalties` : Pénalités par seuil de concentration
- `bonuses` : Bonus pour diversification intra-portefeuille
- `quality_labels` : Tranches et labels associés

**6. Affichage dans le rapport**

Le rapport HTML affiche :
- Le score numérique dans le graphique radar
- Un badge coloré avec le label de qualité
- Une section `<details>` collapsible avec la décomposition complète :
  - Scores des deux composantes
  - Score pondéré
  - Liste des bonus obtenus
  - Métriques détaillées (nb classes, positions, % international)

---

##### 3.2.5.8 Calcul enrichi du score de liquidité (`tools/analyzer.py`)

**Objectif** : Mesurer la capacité du ménage à faire face à 12 mois de dépenses sans revenus (matelas de sécurité).

**Méthodologie (v2.0)** :

La fonction `_calculate_liquidity_score()` retourne un **dictionnaire enrichi** au lieu d'un simple score numérique.

**1. Calcul du ratio de liquidité**

```
Ratio = Liquidités disponibles / Liquidité cible
Liquidité cible = Dépenses mensuelles × Nb mois cible
Dépenses mensuelles = Revenu mensuel net × 70%
```

- **Liquidités disponibles** : Comptes contenant "livret", "dépôt", "compte"
- **Nb mois cible** : Adapté au profil investisseur
  - Prudent : 15 mois
  - Équilibré : 12 mois
  - Default : 12 mois
  - Dynamique : 9 mois

**2. Barème de scoring avec pénalisation sur-liquidité**

| Ratio | Score | Interprétation |
|-------|-------|----------------|
| ≥ 1.5 | 9 | Sur-liquidité légère (pénalisé) |
| ≥ 1.0 | 10 | Optimal |
| ≥ 0.75 | 8 | Solide |
| ≥ 0.5 | 6 | Acceptable |
| ≥ 0.25 | 4 | Fragile |
| < 0.25 | 2 | Insuffisant |

**3. Labels de qualité**

| Score | Label |
|-------|-------|
| 9-10 | Excellente liquidité |
| 7-9 | Bonne liquidité |
| 5-7 | Liquidité acceptable |
| 3-5 | Liquidité fragile |
| 0-3 | Liquidité critique |

**4. Structure de retour**

```python
{
  "score": 10.0,
  "label": "Excellente liquidité",
  "details": {
    "liquidite_actuelle": 34727.29,
    "liquidite_cible": 29400.00,
    "ratio": 1.18,
    "target_months": 12,
    "depenses_mensuelles": 2450.00,
    "is_overliquid": false,
    "overliquidity_threshold": 1.5
  }
}
```

**5. Configuration**

Paramètres dans `config/analysis.yaml` → `scores.liquidity` :
- `liquid_account_keywords` : Mots-clés pour identifier les comptes liquides
- `expenses_to_income_ratio` : Ratio dépenses/revenu (0.7)
- `target_months_by_profile` : Cible en mois par profil
- `overliquidity_threshold` : Seuil de sur-liquidité (1.5)
- `thresholds` : Barème ratio → score
- `quality_labels` : Labels par tranche de score

---

##### 3.2.5.9 Calcul enrichi du score fiscal (`tools/analyzer.py`)

**Objectif** : Mesurer le degré d'optimisation fiscale structurelle du patrimoine financier.

**Méthodologie (v2.0)** :

La fonction `_calculate_fiscal_score()` retourne un **dictionnaire enrichi** avec prise en compte de PEA, CTO, AV, PER et cryptos.

**1. Score de base et bonus**

- **Base** : 7.0/10 (patrimoine moyennement optimisé)
- **Bonus PEA > CTO** : +1.5 (fiscalement avantageux)
- **Bonus AV > 50k€** : +0.5 (succession optimisée)
- **Bonus PER présent** : +1.0 si montant > 5000€ (avantage fiscal à l'entrée)

**2. Pénalités**

- **Cryptos élevés** : -0.5 si cryptos > 15% du patrimoine total (fiscalité lourde)

**3. Labels de qualité**

| Score | Label |
|-------|-------|
| 9-10 | Optimisation fiscale excellente |
| 7-9 | Bonne structure fiscale |
| 5-7 | Structure fiscale moyenne |
| 3-5 | Structure sous-optimisée |
| 0-3 | Structure fiscale défavorable |

**4. Structure de retour**

```python
{
  "score": 9.0,
  "label": "Optimisation fiscale excellente",
  "details": {
    "pea_total": 91814.60,
    "cto_total": 35338.36,
    "av_total": 106046.01,
    "per_total": 4596.76,
    "crypto_total": 11377.16,
    "crypto_percentage": 2.4,
    "pea_over_cto": true,
    "has_per": false,
    "bonuses_applied": {
      "pea_over_cto": 1.5,
      "av_succession": 0.5
    },
    "penalties_applied": {}
  }
}
```

**5. Configuration**

Paramètres dans `config/analysis.yaml` → `scores.fiscal` :
- `base_score` : Score de départ (7.0)
- `bonuses` : Montants des bonus (PEA/CTO, AV, PER)
- `penalties` : Seuils et pénalités (cryptos élevés)
- `quality_labels` : Labels par tranche de score

---

##### 3.2.5.10 Calcul enrichi du score de croissance (`tools/analyzer.py`)

**Objectif** : Mesurer le potentiel de croissance à long terme du patrimoine financier via l'exposition aux marchés actions.

**Méthodologie (v2.0)** :

La fonction `_calculate_growth_score()` retourne un **dictionnaire enrichi** avec adaptation au profil investisseur.

**1. Calcul de l'exposition actions**

```
% actions = (Exposition actions / Patrimoine financier total) × 100

Exposition actions = PEA + PEA-PME + CTO + UC dans AV (hors fonds euros)
```

**2. Barème adapté au profil**

Chaque profil a sa plage optimale :

| Profil | Plage optimale | Score 10 | Score 8 | Score 6 |
|--------|---------------|----------|---------|---------|
| Prudent | 30-45% | 30-45% | 20-30%, 45-55% | 10-20%, 55-65% |
| Équilibré | 50-65% | 50-65% | 40-50%, 65-75% | 30-40%, 75-85% |
| Default | 60-70% | 60-70% | 50-60%, 70-80% | 40-50%, 80-90% |
| Dynamique | 70-85% | 70-85% | 60-70%, 85-95% | 50-60% |

**3. Labels de qualité**

| Score | Label |
|-------|-------|
| 9-10 | Excellent potentiel de croissance |
| 7-9 | Bon potentiel de croissance |
| 5-7 | Potentiel de croissance modéré |
| 3-5 | Potentiel de croissance limité |
| 0-3 | Potentiel de croissance très faible |

**4. Interprétation contextuelle**

Le système génère une interprétation personnalisée :
- "Exposition optimale pour votre profil (60-70%)"
- "Légèrement sous-exposé (optimal : 60-70%)"
- "Fortement sur-exposé (optimal : 60-70%)"

**5. Structure de retour**

```python
{
  "score": 4.0,
  "label": "Potentiel de croissance limité",
  "details": {
    "exposition_actions": 127153.00,
    "patrimoine_financier": 333119.00,
    "pct_actions": 38.2,
    "profil_actif": "default",
    "optimal_range": [60, 70],
    "interpretation": "Fortement sous-exposé (optimal : 60-70%)"
  }
}
```

**6. Configuration**

Paramètres dans `config/analysis.yaml` → `scores.growth` :
- `quality_labels` : Labels communs à tous les profils
- Pour chaque profil (`default`, `dynamique`, `equilibre`, `prudent`) :
  - `optimal_range` : Plage pour score 10
  - `good_ranges` : Plages pour score 8
  - `medium_ranges` : Plages pour score 6
  - `fallback_score` : Score par défaut (4)

---

### 3.3 Outil 3 : Generator (`tools/generator.py`)

#### 3.3.1 Responsabilité

Injecter les données de `patrimoine_analysis.json` dans le template HTML pour générer le rapport final.

#### 3.3.2 Inputs

- `generated/patrimoine_analysis.json`
- `templates/rapport_template.html` (READONLY)
- `templates/rapport.css` (READONLY - incorporé dans HTML final)

#### 3.3.3 Output

- `generated/rapport_YYYYMMDD_HHMMSS.html` (fichier autonome avec CSS inline)

#### 3.3.4 Méthode d'injection

Le template utilise des attributs `data-field` :

```html
<div class="value" data-field="patrimoine_total">470 354 €</div>
```

**Stratégie d'injection** :
1. Charger template HTML (BeautifulSoup)
2. **Incorporer CSS** : Remplacer `<link rel="stylesheet" href="rapport.css">` par `<style>...</style>` avec le contenu du fichier CSS
3. Parser `patrimoine_analysis.json`
4. Remplacer valeurs des éléments `[data-field="X"]`
5. Dupliquer lignes `[data-repeat="Y"]` pour tableaux
6. Sauvegarder HTML final avec timestamp

**Note importante** : Le fichier HTML généré est **complètement autonome** et contient le CSS inline. Il peut être déplacé, partagé ou archivé sans dépendances externes (hormis Chart.js chargé depuis CDN).

#### 3.3.5 Mapping JSON → Template

| data-field | Source JSON | Transformation |
|------------|-------------|----------------|
| `patrimoine_total` | `synthese.patrimoine_total` | Format : `470 354 €` |
| `actifs_financiers` | `synthese.patrimoine_financier` | Format : `352 104 €` |
| `immobilier` | `synthese.patrimoine_immobilier` | Format : `131 375 €` |
| `etablissement_name` | `repartition.par_etablissement[].nom` | Texte brut |
| `etablissement_montant` | `repartition.par_etablissement[].montant` | Format : `283 714 €` |
| `etablissement_pct` | `repartition.par_etablissement[].pourcentage` | Format : `80.6 %` |
| `etablissement_risk` | `repartition.par_etablissement[].niveau_risque` | Badge CSS |
| `class_name_primary` | `repartition.par_classe_actifs[].type_actif` | Type d'actif (ligne 1) |
| `class_name_secondary` | `repartition.par_classe_actifs[].etablissement` (détail) | Détail compte (ligne 2) |
| `class_etablissement` | `repartition.par_classe_actifs[].etablissement` (nom) | Nom établissement |
| `class_amount` | `repartition.par_classe_actifs[].montant` | Format : `58 100 €` |
| `class_pct` | `repartition.par_classe_actifs[].pourcentage` | Format : `13.9 %` |
| `class_gap_message` | `repartition.par_classe_actifs[].benchmark_gap.message` | Message écart benchmark |
| `class_gap_badge` | `repartition.par_classe_actifs[].benchmark_gap` | Badge CSS (si niveau ≠ normal) |
| `div_score_final` | `synthese.diversification_details.score` | Format : `8.5` |
| `div_label` | `synthese.diversification_details.label` | Badge coloré avec label qualité |
| `div_score_institutional` | `synthese.diversification_details.details.score_institutional` | Format : `7.5` |
| `div_score_jurisdictional` | `synthese.diversification_details.details.score_jurisdictional` | Format : `8.8` |
| `div_score_weighted` | `synthese.diversification_details.details.score_weighted` | Format : `8.0` |
| `div_bonus_total` | `synthese.diversification_details.details.bonus_total` | Format : `1.5` |
| `div_nb_classes` | `synthese.diversification_details.details.nb_classes_actifs` | Nombre entier |
| `div_nb_positions` | `synthese.diversification_details.details.nb_positions` | Nombre entier |
| `div_pct_international` | `synthese.diversification_details.details.pct_international` | Format : `22.5` |
| `div_bonus_details` | `synthese.diversification_details.details.bonus_details` | HTML formaté (liste bonus) |

**Éléments répétés** :
- `[data-repeat="etablissement"]` : itération sur `repartition.par_etablissement[]`
- `[data-repeat="classes"]` : itération sur `repartition.par_classe_actifs[]`

**Structure spéciale - Tableau classes d'actifs** :
La colonne "Classe d'actifs" utilise une structure à deux lignes :
- `class_name_primary` : Type d'actif (Actions, Obligations, Liquidités, etc.)
- `class_name_secondary` : Détail du compte (PEA, AV - Fonds Euro, etc.)

Le champ `etablissement` dans les données JSON contient le format `"Établissement (Détail)"` (ex: `"Crédit Agricole (AV - Fonds Euro)"`). Le générateur parse cette chaîne pour :
- Extraire le nom de l'établissement → `class_etablissement`
- Extraire le détail du compte → `class_name_secondary`
- Le type d'actif provient directement de `type_actif` → `class_name_primary`

#### 3.3.6 Gestion du graphique radar

Le template contient un graphique Chart.js. Le générateur injecte les données :

```javascript
data: {
  labels: ['Diversification','Résilience','Liquidité','Fiscalité','Croissance'],
  datasets: [{
    data: [8, 7.5, 6.5, 7, 8.5]  // ← injecté depuis synthese.scores_details
  }]
}
```

**Méthode** :
1. Trouver balise `<script>` contenant "radarChart"
2. Extraire scores depuis JSON
3. Remplacer `data: [...]` par nouvelles valeurs
4. Réécrire script dans HTML

#### 3.3.7 Affichage des sources web dans les risques

**Objectif** : Chaque risque affiché dans la section "3. Risques patrimoniaux" doit inclure les sources web qui ont permis son évaluation, avec liens cliquables et extraits.

**Structure HTML du template** :

```html
<div class="alert" data-repeat="risque">
    <strong data-field="risque_titre">Titre du risque</strong>
    <p data-field="risque_description">Description du risque</p>
    <p>
        <strong>Exposition :</strong>
        <span data-field="risque_montant">0 €</span>
        (<span data-field="risque_pct">0%</span>)
    </p>
    <details>
        <summary><strong>📚 Sources web</strong> (<span data-field="sources_count">0</span>)</summary>
        <ul data-field="sources_list" style="margin-top: 10px; font-size: 0.9em;">
            <!-- Sources injectées dynamiquement -->
        </ul>
    </details>
</div>
```

**Données JSON source** : `risques.{critiques|eleves|moyens|faibles}[].sources_web[]`

**Structure d'une source** :
```json
{
  "url": "https://exemple.fr/article",
  "titre": "Titre de l'article",
  "extrait": "Premier paragraphe ou description...",
  "pertinence": "Haute",
  "date_acces": "2025-10-24"
}
```

**Injection dans le générateur** :

1. Pour chaque risque, extraire `sources_web[]`
2. Injecter le compteur : `sources_count` = nombre de sources
3. Pour chaque source, créer un élément `<li>` contenant :
   - Un lien `<a>` avec `href`, `target="_blank"`, `rel="noopener"`
   - Un `<br>` suivi d'un `<small>` avec l'extrait (max 150 caractères)
4. Ajouter tous les `<li>` dans `sources_list`

**Comportement utilisateur** :
- Section pliable par défaut (élément `<details>`)
- L'utilisateur peut cliquer sur "📚 Sources web (X)" pour déplier
- Les liens s'ouvrent dans un nouvel onglet
- Les extraits donnent un aperçu du contenu

**Traçabilité** : Cette fonctionnalité permet de vérifier la provenance des analyses de risques et d'approfondir les recherches si nécessaire.

#### 3.3.8 Structure de la page de couverture (title, subtitle, subtitle-profile)

**Objectif** : La page de couverture présente trois niveaux d'information hiérarchiques pour identifier rapidement le document et le profil de l'investisseur.

**Structure HTML du template** :

```html
<section class="cover" role="banner">
    <h1 class="title" data-field="title">Rapport Patrimonial</h1>
    <div class="subtitle" data-field="subtitle">
        Analyse approfondie • Recommandations • Synthèse —
        <span data-field="report_date">20 octobre 2025</span>
    </div>
    <div class="subtitle-profile" data-field="subtitle_profile">
        Gilles HOFF • 50 ans • Profil Dynamique • Développeur Informatique (Actif) • Revenu: 3 500 €/mois
    </div>
</section>
```

**Hiérarchie des informations** :

1. **Titre (title)** : Titre du document, texte statique "Rapport Patrimonial"
2. **Premier sous-titre (subtitle)** : Nature du rapport + date de génération
   - Texte statique : "Analyse approfondie • Recommandations • Synthèse"
   - Date dynamique : `report_date` (format: "DD mois YYYY")
3. **Second sous-titre (subtitle-profile)** : Synthèse du profil investisseur
   - Contenu complètement dynamique généré depuis le profil JSON

**Données JSON source** : `profil`

**Champs utilisés pour subtitle-profile** :
- `prénom` : Prénom de l'investisseur (depuis `profil` dans patrimoine.md)
- `nom` : Nom de l'investisseur (affiché en MAJUSCULES) (depuis `profil` dans patrimoine.md)
- `age` : Âge calculé depuis la date de naissance (depuis `profil` dans patrimoine.md)
- `situation_familiale` : Situation familiale (Marié, Célibataire, etc.) (depuis `profil` dans patrimoine.md)
- `enfants` : Nombre d'enfants (integer) (depuis `profil` dans patrimoine.md)
- **`profil_actif`** : **Type d'investisseur déterminé par `config/config.yaml → analysis.active_profile`** (Dynamique, Équilibré, Prudent)
  - **IMPORTANT** : Le profil affiché provient de `config/analysis.yaml`, PAS du champ `type_investissement` dans `patrimoine.md`
  - Mapping : `dynamique` → "Dynamique", `equilibre` → "Équilibré", `prudent` → "Prudent", `default` → "Équilibré"
  - Source technique : `data["synthese"]["growth_details"]["details"]["profil_actif"]`
- `statut` : Statut professionnel (Actif, Retraité, etc.) (depuis `profil` dans patrimoine.md)
- `profession` : Profession exercée (depuis `profil` dans patrimoine.md)
- `revenu_mensuel_net` : Revenu mensuel net en euros (depuis `profil` dans patrimoine.md)

**Format de subtitle-profile** :

Le générateur construit dynamiquement une chaîne avec séparateurs " • " incluant :

1. **Prénom NOM • âge** : "Gilles HOFF • 50 ans"
2. **Situation familiale** : "Marié" (avec nombre d'enfants si > 0)
3. **Type d'investisseur** : "Profil Dynamique"
4. **Profession/Statut** : "Développeur informatique (Actif)"
5. **Revenu** : "Revenu: 3 500 €/mois"

**Styles CSS** :

```css
.cover .subtitle {
    color: rgba(255, 245, 210, 0.95);
    font-size: 10.5pt;
}
.cover .subtitle-profile {
    color: rgba(255, 255, 255, 0.85);
    font-size: 9.5pt;
    font-style: italic;
    letter-spacing: 0.3px;
}
```

**Méthode d'injection** :

La méthode `_synthesize_investor_profile()` dans `generator.py` :
1. Extrait les champs du profil depuis le JSON (`data.get("profil", {})`)
2. **Récupère le profil actif depuis `config/analysis.yaml`** via `data["synthese"]["growth_details"]["details"]["profil_actif"]`
3. Mappe le profil technique vers un label français (ex: "dynamique" → "Dynamique")
4. Construit une liste de segments textuels
5. Joint les segments avec " • "
6. Injecte dans `data-field="subtitle_profile"`

**Traçabilité** : Cette structure à trois niveaux permet d'identifier rapidement le type de document, sa date, et le profil du client dès la page de couverture, sans avoir à chercher ces informations dans le reste du document.

#### 3.3.9 Alertes conditionnelles et injection HTML dynamique

**Objectif** : Permettre l'affichage conditionnel d'éléments HTML (comme les alertes) qui ne doivent apparaître que si certaines conditions sont remplies. Si aucune donnée alarmante n'est détectée, l'élément entier est supprimé du DOM.

**Cas d'usage principal** : Alerte de concentration dans la section "Répartition par établissements"

**Structure HTML du template** :

```html
<div class="alert" data-conditional="concentration_alert">
    <span data-field="concentration_alert_content"></span>
</div>
```

**Attributs spéciaux** :
- `data-conditional="identifier"` : Marque un élément comme conditionnel (peut être supprimé)
- `data-field="identifier_content"` : Contient le contenu dynamique à injecter

**Logique d'injection** (dans `_inject_simple_fields()`) :

1. **Si `value` est `None`** :
   - Rechercher le parent avec `data-conditional="true"`
   - Supprimer complètement cet élément parent avec `.decompose()`
   - Logger la suppression

2. **Si `value` est présent** :
   - Injecter le contenu normalement
   - **Si le contenu contient du HTML** (détection: `"<" in value and ">" in value`) :
     - Utiliser BeautifulSoup pour parser et injecter le HTML
   - Sinon : injection texte simple

**Exemple : Alerte de concentration**

La méthode `_analyze_concentration_alert(data: dict) -> str | None` :

**Seuils d'alerte** :
- Établissement : ≥30% = élevé, ≥50% = critique
- Juridiction : ≥60% = élevé, ≥80% = critique

**Retour** :
- `None` : Aucune concentration préoccupante → div supprimée
- `str` : Message HTML formaté → div affichée

**Exemples de messages générés** :

```html
<!-- Cas critique établissement (1 alerte) -->
<strong>⚠️ Concentration critique :</strong> 52.8% du patrimoine exposé sur <strong>Crédit Agricole</strong>.

<!-- Cas critique géographique (1 alerte) -->
<strong>⚠️ Concentration géographique critique :</strong> 84.2% du patrimoine exposé au <strong>système français</strong>.

<!-- Cas mixte (2 alertes - chacune sur une ligne séparée) -->
<div style="margin-bottom: 8px;"><strong>⚠️ Concentration critique :</strong> 52.1% du patrimoine exposé sur <strong>Boursorama</strong>.</div>
<div style="margin-bottom: 8px;"><strong>⚠️ Concentration géographique élevée :</strong> 67.8% du patrimoine exposé au <strong>système français</strong>.</div>
```

**Format d'affichage** :
- **Alerte unique** : Texte simple avec point final
- **Alertes multiples** : Chaque alerte encapsulée dans un `<div style="margin-bottom: 8px;">` pour séparation visuelle claire

**Traçabilité** : Ce système permet de rendre le rapport plus concis et pertinent en n'affichant que les alertes nécessaires, évitant ainsi la présence de messages génériques ou vides qui nuiraient à la lisibilité.

---

## 4. Script principal (`main.py`)

### 4.1 Interface CLI

```bash
$ python main.py
```

**Alternative (Claude Code)** :
```bash
$ /report
```

Cette commande slash, disponible dans Claude Code, exécute automatiquement `python main.py` dans le répertoire `patrimoine-analyzer/`.

**Comportement** :
1. Affiche bannière ASCII art
2. Lance séquentiellement les 3 outils
3. Affiche progression avec emojis
4. Sauvegarde logs
5. Affiche résumé final

**Exemple de sortie** :

```
╔═══════════════════════════════════════════════╗
║     PATRIMOINE ANALYZER v1.0.0                ║
║     Rapport patrimonial automatisé            ║
╚═══════════════════════════════════════════════╝

[2025-10-21 14:30:15] 📥 Étape 1/3 : Normalisation
  ⏱️  Durée : 3.2s

[2025-10-21 14:30:18] 🔍 Étape 2/3 : Analyse approfondie
  ├─ 47 recherches web effectuées
  ├─ 6 risques critiques identifiés
  └─ 5 recommandations prioritaires
  ⏱️  Durée : 3m 12s

[2025-10-21 14:33:30] 📄 Étape 3/3 : Génération HTML
  ⏱️  Durée : 1.8s

╔═══════════════════════════════════════════════╗
║  ✅ RAPPORT GÉNÉRÉ AVEC SUCCÈS                ║
╠═══════════════════════════════════════════════╣
║  📊 Patrimoine total : 470 354 €              ║
║  ⚠️  Risques critiques : 2                    ║
║  💡 Recommandations : 5                       ║
║  📁 Fichier : rapport_20251021_143330.html    ║
║  📋 Log : logs/rapport_20251021_143330.log    ║
╚═══════════════════════════════════════════════╝

⏱️  Durée totale : 3m 17s
```

### 4.2 Gestion des erreurs

Chaque outil gère ses erreurs :
- Fichier manquant → log + arrêt
- Parsing échoué → log détaillé + arrêt
- API web timeout → retry 3× puis log warning
- Template invalide → log + arrêt

Tous les logs sont sauvegardés dans `logs/rapport_YYYYMMDD_HHMMSS.log`.

---

## 5. Configuration

### 5.1 Variables d'environnement (`.env`)

Le projet nécessite un fichier `.env` à la racine contenant les clés API requises :

```bash
# Brave Search API (requise pour les recherches web)
BRAVE_API_KEY=your-api-key-here
```

**Obtenir une clé Brave Search API** :
1. Créer un compte sur https://brave.com/search/api/
2. Tableau de bord : https://api.search.brave.com/app/dashboard
3. Plan gratuit disponible : 2000 requêtes/mois
4. Copier la clé API et l'ajouter au fichier `.env`

**Important** :
- Le fichier `.env` est dans `.gitignore` (ne pas committer les clés)
- Sans `BRAVE_API_KEY`, les recherches web seront désactivées
- L'analyse de risques continuera mais sans sources web

---

### 5.2 Fichier de configuration (`config/config.yaml`)

```yaml
project:
  name: "Patrimoine Analyzer"
  version: "1.0.0"

paths:
  sources: "sources/"
  templates: "templates/"
  generated: "generated/"
  logs: "logs/"

normalizer:
  input_file: "patrimoine.md"
  output_file: "patrimoine_input.json"
  date_format: "ISO8601"

analyzer:
  input_file: "patrimoine_input.json"
  output_file: "patrimoine_analysis.json"
  web_research:
    enabled: true
    max_queries: 50
    timeout_seconds: 30
    retry_count: 3
  risk_thresholds:
    concentration_etablissement_critique: 50
    concentration_etablissement_eleve: 30
    concentration_juridiction_critique: 80
    concentration_juridiction_eleve: 60
    liquidite_critique: 5000
    liquidite_faible: 15000

generator:
  input_file: "patrimoine_analysis.json"
  template_file: "rapport_template.html"
  output_prefix: "rapport_"
  date_format: "%Y%m%d_%H%M%S"

analysis:
  config_file: "analysis.yaml"   # Fichier de configuration pour l'analyse
  active_profile: "default"      # Profil : default, dynamique, equilibre, prudent

logging:
  level: "INFO"
  format: "[%(asctime)s] %(levelname)s: %(message)s"
  date_format: "%Y-%m-%d %H:%M:%S"
```

**Note** : Les paramètres détaillés de l'analyse (optimisation de portefeuille, benchmarks, scores, classification des comptes, profils d'investisseur) sont dans `config/analysis.yaml`. Voir sections 3.2.5.1 et 3.2.5.6 pour plus de détails.

---

## 6. Logs

### 6.1 Format des logs

```
[2025-10-21 14:30:15] INFO: ========================================
[2025-10-21 14:30:15] INFO: Démarrage Patrimoine Analyzer v1.0.0
[2025-10-21 14:30:15] INFO: ========================================
[2025-10-21 14:30:15] INFO: [ÉTAPE 1/3] Normalisation des sources
[2025-10-21 14:30:15] INFO: Lecture sources/patrimoine.md...
[2025-10-21 14:30:15] DEBUG: Profil détecté : Homme, 49 ans
[2025-10-21 14:30:16] INFO: Parsing fichiers sources (9 fichiers)...
[2025-10-21 14:30:18] INFO: ✓ Étape 1 terminée (3.2s)
[2025-10-21 14:30:18] INFO: [ÉTAPE 2/3] Analyse approfondie
[2025-10-21 14:30:20] INFO: [1/47] Recherche : "Loi Sapin 2..."
[2025-10-21 14:33:14] INFO: ✓ Étape 2 terminée (3m 12s)
[2025-10-21 14:33:14] INFO: [ÉTAPE 3/3] Génération rapport HTML
[2025-10-21 14:33:16] INFO: ✓ Étape 3 terminée (1.8s)
[2025-10-21 14:33:16] INFO: ✅ GÉNÉRATION TERMINÉE
```

---

## 7. Tests et validation

### 7.1 Tests unitaires

```python
# tests/test_normalizer.py
def test_parse_patrimoine_md():
    """Test parsing fichier patrimoine.md"""

def test_parse_csv():
    """Test parsing fichier CSV positions"""

def test_calculate_totals():
    """Test calcul totaux récursifs"""

# tests/test_analyzer.py
def test_detect_concentration_risk():
    """Test détection risque concentration"""

def test_generate_recommendations():
    """Test génération recommandations"""

# tests/test_generator.py
def test_inject_simple_fields():
    """Test injection champs simples"""

def test_inject_repeated_rows():
    """Test duplication lignes tableaux"""
```

---

## 8. Évolutions futures (hors scope v1.0)

### 8.1 Fonctionnalités potentielles

- **Comparaison temporelle** : Évolution patrimoine entre 2 rapports
- **Alertes automatiques** : Email si risque critique détecté
- **Export PDF** : Génération PDF via Puppeteer/WeasyPrint
- **Dashboard interactif** : Interface web
- **Connexion API bancaires** : Import automatique positions
- **Optimisation fiscale avancée** : Simulation TMI, IFI
- **Projections** : Simulation évolution sur 10-30 ans

---

## 9. Contraintes et limitations

### 9.1 Limites connues

1. **Parsing PDF** : Extraction imparfaite sur PDF complexes
2. **Recherches web** : Dépend disponibilité API Anthropic
3. **Monnaies** : Support EUR uniquement (USD converti manuellement)
4. **Graphiques** : Chart.js requiert JS activé
5. **Taille fichiers** : Limite 100 MB par fichier source

### 9.2 Hypothèses

- Fichiers sources bien formatés
- Connexion internet pour recherches web
- Clé API Brave Search valide
- Python 3.10+ installé

---

## 10. Glossaire

| Terme | Définition |
|-------|------------|
| **AV** | Assurance-vie |
| **PEA** | Plan d'Épargne en Actions |
| **PEA-PME** | PEA dédié aux PME/ETI |
| **CTO** | Compte-Titres Ordinaire |
| **PER** | Plan d'Épargne Retraite |
| **PEL** | Plan d'Épargne Logement (classé comme Liquidités, épargne réglementée) |
| **PFU** | Prélèvement Forfaitaire Unique (30%) |
| **HCSF** | Haut Conseil de Stabilité Financière |
| **Loi Sapin 2** | Loi permettant gel temporaire AV (article 21) |
| **TMI** | Tranche Marginale d'Imposition |
| **IFI** | Impôt sur la Fortune Immobilière |

---

## 11. Diagramme de flux de données

```
┌─────────────────────────────────────────────────────────────┐
│                     SOURCES (Input Layer)                    │
├─────────────────────────────────────────────────────────────┤
│  patrimoine.md                                               │
│  [CA] - PEA.csv, [CA] - AV.pdf, [DGO] - CTO.csv, etc.      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              NORMALIZER (Processing Layer 1)                 │
├─────────────────────────────────────────────────────────────┤
│  • Parse patrimoine.md (Markdown → Dict)                     │
│  • Read CSV files (Pandas)                                   │
│  • Extract PDF tables (pdfplumber)                           │
│  • Parse JSON files (native)                                 │
│  • Calculate totals (recursive)                              │
│  • Validate schema & coherence                               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
                 patrimoine_input.json
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              ANALYZER (Processing Layer 2)                   │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Repartition Analyzer                                  │   │
│  │  • By etablissement                                   │   │
│  │  • By asset class                                     │   │
│  │  • By jurisdiction                                    │   │
│  └──────────────────────────────────────────────────────┘   │
│                         │                                    │
│  ┌──────────────────────▼──────────────────────────────┐   │
│  │ Risk Analyzer                                         │   │
│  │  ┌─────────────────────────────────────────────┐     │   │
│  │  │ Web Researcher (Anthropic API)              │     │   │
│  │  │  • Search regulatory info                   │     │   │
│  │  │  • Search market data                       │     │   │
│  │  │  • Search economic news                     │     │   │
│  │  │  → Returns cited sources                    │     │   │
│  │  └─────────────────────────────────────────────┘     │   │
│  │  • Concentration risks                                │   │
│  │  • Regulatory risks (Loi Sapin 2, etc.)              │   │
│  │  • Fiscal risks                                       │   │
│  │  • Market risks                                       │   │
│  │  • Liquidity risks                                    │   │
│  │  • Political risks                                    │   │
│  └──────────────────────┬────────────────────────────────┘   │
│                         │                                    │
│  ┌──────────────────────▼──────────────────────────────┐   │
│  │ Recommender                                          │   │
│  │  • Generate recommendations                          │   │
│  │  • Prioritize by score (impact × feasibility)       │   │
│  │  • Link to mitigated risks                          │   │
│  └──────────────────────┬────────────────────────────────┘   │
│                         │                                    │
│  ┌──────────────────────▼──────────────────────────────┐   │
│  │ Stress Tester                                        │   │
│  │  • Banking crisis + Sapin 2                          │   │
│  │  • Market crash -30%                                 │   │
│  │  • Job loss 12-24 months                            │   │
│  │  • Tax increase                                      │   │
│  └──────────────────────┬────────────────────────────────┘   │
│                         │                                    │
│  ┌──────────────────────▼──────────────────────────────┐   │
│  │ Synthesizer                                          │   │
│  │  • Calculate global scores                           │   │
│  │  • Generate executive summary                        │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
              patrimoine_analysis.json
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              GENERATOR (Processing Layer 3)                  │
├─────────────────────────────────────────────────────────────┤
│  • Load HTML template (BeautifulSoup)                        │
│  • Inject simple fields (data-field="X")                     │
│  • Duplicate & fill table rows (data-repeat="Y")             │
│  • Inject chart data (Chart.js script)                       │
│  • Generate timestamp filename                               │
│  • Save HTML file                                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   OUTPUT (Result Layer)                      │
├─────────────────────────────────────────────────────────────┤
│  rapport_20251021_143330.html                                │
│  logs/rapport_20251021_143330.log                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 12. Spécifications détaillées - Parsing CSV

### 12.1 Format CSV attendu pour positions

**Fichier** : `[DGO] - CTO.csv`, etc. (pour les CSV uniquement)

**Note** : Depuis la migration, les fichiers PEA du Crédit Agricole sont maintenant au format PDF (`[CA] - PEA.pdf`, `[CA] - PEA-PME.pdf`) et sont parsés différemment (voir section 13.2).

```csv
Ticker,Quantité,Prix Unitaire,Valeur Totale
VWCE,120,100.50,12060.00
IWDA,50,75.20,3760.00
```

**Colonnes acceptées** (aliases) :
- **Ticker** : ticker, symbole, code, isin
- **Quantité** : quantite, quantity, qté, nombre
- **Prix** : prix, price, cours, valeur_unitaire
- **Valeur** : valeur, value, montant, total

### 12.2 Normalisation CSV

```python
# Conversion colonnes
df.columns = df.columns.str.strip().str.lower()

# Mapping vers noms standards
for target_col, aliases in column_mappings.items():
    for alias in aliases:
        if alias in df.columns:
            df.rename(columns={alias: target_col}, inplace=True)
            break

# Conversion types numériques
df['quantite'] = pd.to_numeric(df['quantite'], errors='coerce')
df['prix'] = pd.to_numeric(df['prix'], errors='coerce')
df['valeur'] = pd.to_numeric(df['valeur'], errors='coerce')
```

---

## 13. Spécifications détaillées - Parsing PDF

### 13.1 Extraction tableaux PDF

**Outil** : pdfplumber

```python
with pdfplumber.open(filepath) as pdf:
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            # table = [
            #   ["En-tête 1", "En-tête 2", "En-tête 3"],
            #   ["Valeur 1", "Valeur 2", "Valeur 3"],
            #   ...
            # ]
```

### 13.2 Heuristiques pour identifier type de document

**Assurance-vie** :
- Mots-clés : "assurance-vie", "unités de compte", "fonds euro"
- Structure : tableau avec colonnes [Support, Valeur, %]

**PER** :
- Mots-clés : "plan épargne retraite", "PER"
- Structure : tableau avec colonnes [Support, Montant]

**PEA / PEA-PME** (format Crédit Agricole web) :
- Mots-clés : "MANDAT PEA", "compte PEA", "PEA PME", "PEA-PME", "portefeuille"
- Priorité : Détecter PEA avant PER (car "PER" peut apparaître dans "Espace PERsonnel")
- **Extraction solde espèces** :
  - Source : ligne "Ma valorisation totale" au format "X € = Y € + Z € = ..."
  - Exemple : "6 133,22 € = 970,14 € + **5 163,08 €**" → solde espèces = 5 163,08 €
  - Le 3ème montant de la formule est le solde espèces (plus fiable que "Solde disponible")
  - Fallback : Extraction depuis "Solde disponible : X €" si formule non trouvée
  - Résultat stocké dans `compte["solde_especes"]`
- **Extraction positions** :
  - Structure multi-pages :
    - **Page 1** : 10 colonnes, colonnes 0-1 vides, données en colonnes 2-9
    - **Page 2+** : 9 colonnes, données directement en colonnes 0-7 (pas de répétition d'en-tête)
  - Format des lignes :
    - Colonne Valeur : "NOM ACTION\nISIN CODE" (sur 2 lignes)
    - Colonnes : [Valeur, Quantité, Cours, Variation(1J), Prix de revient, Valorisation, +/- Value latente, Variation(1er Janv)]
  - Parsing spécifique :
    - Gestion décalage colonnes entre pages (offset=2 pour page 1, offset=0 pour page 2+)
    - Valorisation : colonne 7 (page 1 avec offset) ou colonne 6 (page 2+ sans offset)
    - Extraction ISIN depuis "ISIN CODE" (avant le code ticker)
- **Calcul total compte** : `montant = sum(valorisation positions) + solde_especes`

**CTO** :
- Mots-clés : "compte-titres", "compte titres"
- Structure : tableau avec colonnes [Titre, Quantité, Cours, Valorisation]

---

## 14. Spécifications détaillées - Recherches Web

### 14.1 Prompt type pour recherche

```python
prompt = f"""Effectue une recherche web approfondie sur : "{query}"

{f"Contexte : {context}" if context else ""}

Instructions :
- Recherche des sources officielles et fiables (gouvernement, institutions, médias reconnus)
- Pour chaque source pertinente, fournis :
  * URL complète
  * Titre de la page
  * Extrait pertinent (2-3 phrases max)
  * Niveau de pertinence (Haute/Moyenne/Faible)
- Privilégie les sources récentes (2024-2025)
- Cite TOUTES les URLs utilisées

Format de réponse attendu :
[SOURCE 1]
URL: https://...
Titre: ...
Extrait: ...
Pertinence: Haute

[SOURCE 2]
URL: https://...
..."""
```

### 14.2 Extraction sources depuis réponse

**Parsing manuel** avec regex :

```python
import re

source_blocks = re.split(r'\[SOURCE \d+\]', response_text)

for block in source_blocks[1:]:
    source = {}

    # URL
    url_match = re.search(r'URL:\s*(.+)', block)
    if url_match:
        source["url"] = url_match.group(1).strip()

    # Titre
    title_match = re.search(r'Titre:\s*(.+)', block)
    if title_match:
        source["titre"] = title_match.group(1).strip()

    # Extrait
    extrait_match = re.search(r'Extrait:\s*(.+?)(?=Pertinence:|$)', block, re.DOTALL)
    if extrait_match:
        source["extrait"] = extrait_match.group(1).strip()

    # Pertinence
    pertinence_match = re.search(r'Pertinence:\s*(.+)', block)
    if pertinence_match:
        source["pertinence"] = pertinence_match.group(1).strip()

    source["date_acces"] = datetime.now().strftime("%Y-%m-%d")

    if source.get("url"):
        sources.append(source)
```

### 14.3 Retry logic

```python
for attempt in range(max_retries):
    try:
        response = self.client.messages.create(...)
        return self._extract_sources(response)
    except anthropic.APITimeoutError:
        if attempt == max_retries - 1:
            logger.error("Échec après 3 tentatives")
            return []
        time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
```

---

## 15. Spécifications détaillées - Calcul score de priorité

### 15.1 Formule de calcul

```python
def _calculate_priority_score(self, reco: dict, risque: dict) -> float:
    """
    Score = (criticité × 0.4) + (impact × 0.3) + (facilité × 0.3)
    """

    # Score criticité risque (0-10)
    niveau_scores = {
        "Critique": 10,
        "Élevé": 7,
        "Moyen": 4,
        "Faible": 2
    }
    score_criticite = niveau_scores.get(risque["niveau"], 5)

    # Score impact financier (0-10)
    pct_impact = risque["exposition_pct"]
    if pct_impact >= 50:
        score_impact = 10
    elif pct_impact >= 30:
        score_impact = 7
    elif pct_impact >= 15:
        score_impact = 5
    else:
        score_impact = 3

    # Score facilité (0-10) - inverse de difficulté
    difficulte_scores = {
        "Faible": 10,
        "Moyenne": 6,
        "Élevée": 3
    }
    score_facilite = difficulte_scores.get(reco["difficulte"], 5)

    # Score pondéré
    score_final = (
        score_criticite * 0.4 +
        score_impact * 0.3 +
        score_facilite * 0.3
    )

    return round(score_final, 1)
```

### 15.2 Classification des recommandations

```python
if score >= 8:
    recommandations["prioritaires"].append(reco)
elif score >= 5:
    recommandations["secondaires"].append(reco)
else:
    recommandations["long_terme"].append(reco)
```

---

## 16. Spécifications détaillées - Injection HTML

### 16.1 Injection champs simples

```python
def _inject_simple_fields(self, soup, data):
    """Injecte les champs simples [data-field]
    Supporte les éléments conditionnels et l'injection HTML
    """

    mappings = {
        "patrimoine_total": ("synthese.patrimoine_total", self._format_currency),
        "actifs_financiers": ("synthese.patrimoine_financier", self._format_currency),
        "immobilier": ("synthese.patrimoine_immobilier", self._format_currency),
        "score_global": ("synthese.score_global", lambda x: f"{x}/10"),
        "risque_principal": ("synthese.risque_principal", str),
        "priorites": ("synthese.priorites", str),
        # Alerte de concentration (conditionnel)
        "concentration_alert_content": (self._analyze_concentration_alert, None),
        # ... autres champs
    }

    for field_name, (json_path_or_func, formatter) in mappings.items():
        # Traiter fonction lambda ou chemin JSON
        if callable(json_path_or_func):
            value = json_path_or_func(data)
        else:
            value = self._get_nested_value(data, json_path_or_func)

        # Trouver tous les éléments avec ce data-field
        elements = soup.find_all(attrs={"data-field": field_name})

        for el in elements:
            if value is None:
                # Si la valeur est None et que l'élément a un parent avec data-conditional,
                # supprimer tout le parent conditionnel
                parent = el.find_parent(attrs={"data-conditional": True})
                if parent:
                    parent.decompose()
                    self.logger.debug(f"→ Alerte conditionnelle '{field_name}' supprimée")
            else:
                # Appliquer formateur si présent
                if formatter:
                    value = formatter(value)

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

def _get_nested_value(self, data: dict, path: str):
    """Récupère valeur dans dict imbriqué via chemin type 'synthese.patrimoine_total'"""
    keys = path.split('.')
    value = data
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return None
        if value is None:
            return None
    return value

def _format_currency(self, value: float) -> str:
    """Format : 470354 → '470 354 €'"""
    return f"{value:,.0f} €".replace(",", " ")
```

### 16.2 Injection lignes répétées (tableaux)

```python
def _inject_repeated_rows(self, soup, data):
    """Duplique et remplit lignes répétées [data-repeat]"""

    # Établissements
    tbody = soup.find("tbody")
    template_row = soup.find("tr", attrs={"data-repeat": "etablissement"})

    if template_row and tbody:
        template_row.extract()  # Retirer template du DOM

        for etab in data["repartition"]["par_etablissement"]:
            # Clone template
            new_row = BeautifulSoup(str(template_row), 'lxml').find("tr")

            # Remplir champs
            new_row.find(attrs={"data-field": "etablissement_name"}).string = etab["nom"]
            new_row.find(attrs={"data-field": "etablissement_montant"}).string = self._format_currency(etab["montant"])
            new_row.find(attrs={"data-field": "etablissement_pct"}).string = f"{etab['pourcentage']} %"

            # Badge risque - logique dynamique
            niveau_risque = etab.get("niveau_risque", "Normal")
            badge = new_row.find(attrs={"data-field": "etablissement_risk"})
            if badge:
                badge.string = niveau_risque
                # Calculer la classe CSS appropriée
                risk_class = self._get_badge_class(niveau_risque)

                # Appliquer la classe dynamiquement
                if badge.has_attr("class"):
                    # Supprimer les anciennes classes de sévérité
                    badge_classes = [c for c in badge["class"] if c not in ["high", "mid", "low", "crit"]]
                    badge_classes.append(risk_class)
                    badge["class"] = badge_classes
                else:
                    badge["class"] = ["badge", risk_class]

            # Ajouter au tbody
            tbody.append(new_row)

    # Stress tests - logique similaire
    template_div = soup.find("div", attrs={"data-repeat": "stress_test"})
    if template_div:
        parent = template_div.find_parent()
        template_div.extract()

        for test in data.get("stress_tests", []):
            new_div = BeautifulSoup(str(template_div), "html.parser").find("div")

            # Remplir champs...
            self._set_field(new_div, "test_scenario", test.get("scenario", ""))
            # ...

            # Badge et classe CSS dynamiques
            severite = test.get("severite", "Moyenne")
            severite_class = self._get_stress_severity_class(severite)

            # Appliquer classe à la div principale
            if new_div.has_attr("class"):
                classes = [c for c in new_div["class"] if c not in ["high", "mid", "low", "crit"]]
                classes.append(severite_class)
                new_div["class"] = classes
            else:
                new_div["class"] = ["stress", severite_class]

            # Badge de sévérité
            badge_el = new_div.find("div", class_="badge")
            if badge_el:
                badge_el.string = severite.upper()
                if badge_el.has_attr("class"):
                    badge_classes = [c for c in badge_el["class"] if c not in ["high", "mid", "low", "crit"]]
                    badge_classes.append(severite_class)
                    badge_el["class"] = badge_classes
                else:
                    badge_el["class"] = ["badge", severite_class]

            parent.append(new_div)

def _get_badge_class(self, niveau: str) -> str:
    """Retourne classe CSS selon niveau risque"""
    mapping = {
        "Critique": "crit",
        "Élevé": "mid",
        "Moyen": "mid",
        "Faible": "low",
        "Normal": "low"
    }
    return mapping.get(niveau, "mid")

def _get_stress_severity_class(self, severite: str) -> str:
    """Retourne classe CSS selon sévérité du stress test"""
    severite_lower = severite.lower()
    if severite_lower in ["critique", "élevée", "élevé", "high"]:
        return "high"
    elif severite_lower in ["moyenne", "modérée", "modéré", "medium", "mid"]:
        return "mid"
    elif severite_lower in ["faible", "basse", "low"]:
        return "low"
    else:
        return "mid"  # Par défaut
```

#### 16.2.1 Injection tableau classes d'actifs (structure à deux lignes)

**Particularité** : La colonne "Classe d'actifs" affiche le type d'actif et le détail du compte sur deux lignes distinctes.

**Structure du template** :
```html
<tbody data-repeat="classes">
    <tr>
        <td>
            <span class="cell-primary" data-field="class_name_primary">…</span>
            <span class="cell-secondary" data-field="class_name_secondary">…</span>
        </td>
        <td class="right" data-field="class_etablissement">…</td>
        <td class="right" data-field="class_amount">0 €</td>
        <td class="right" data-field="class_pct">0 %</td>
    </tr>
</tbody>
```

**Logique d'injection** :
```python
def _inject_classes_actifs(self, soup: BeautifulSoup, data: dict):
    """Injecte les lignes de classes d'actifs avec séparation établissement/détail"""
    tbody = soup.find("tbody", attrs={"data-repeat": "classes"})
    if not tbody:
        return

    template_row = tbody.find("tr")
    if not template_row:
        return

    template_html = str(template_row)
    tbody.clear()

    for actif in data.get("repartition", {}).get("par_classe_actifs", []):
        new_row = BeautifulSoup(template_html, "html.parser").find("tr")

        type_actif = actif.get("type_actif", "")
        etablissement_raw = actif.get("etablissement", "")

        # Parser l'établissement pour séparer "Établissement (Détail)"
        # Pattern: "Crédit Agricole (AV - Fonds Euro)" →
        #   etab="Crédit Agricole", detail="AV - Fonds Euro"
        match = re.match(r'^(.+?)\s*\((.+)\)$', etablissement_raw)

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
        self._set_field(new_row, "class_amount", self._format_currency(actif.get("montant", 0)))
        self._set_field(new_row, "class_pct", f"{actif.get('pourcentage', 0)} %")

        tbody.append(new_row)
```

**Rendu visuel** :
```
┌────────────────────┬──────────────────┬─────────────┬───────────────┐
│ Classe d'actifs    │ Établissement    │ Montant     │ % Patrimoine  │
├────────────────────┼──────────────────┼─────────────┼───────────────┤
│ Obligations        │ Crédit Agricole  │ 58 100 €    │ 13.9 %        │
│ AV - Fonds Euro    │                  │             │               │
├────────────────────┼──────────────────┼─────────────┼───────────────┤
│ Actions            │ Degiro           │ 42 500 €    │ 10.2 %        │
│ PEA                │                  │             │               │
└────────────────────┴──────────────────┴─────────────┴───────────────┘
```

**Points clés** :
- Ligne 1 (`class_name_primary`) : Type d'actif brut (Obligations, Actions, Liquidités, etc.)
- Ligne 2 (`class_name_secondary`) : Détail du compte (PEA, AV - Fonds Euro, CTO, etc.)
- Le parsing regex extrait les deux parties du champ `etablissement` : nom et détail entre parenthèses
- Si aucune parenthèse n'est trouvée, `etablissement_name` reste vide

### 16.3 Injection graphique Chart.js

```python
def _inject_chart_data(self, soup, data):
    """Injecte données dans script Chart.js"""

    script_tag = soup.find("script", string=re.compile("radarChart"))
    if script_tag:
        # Extraction scores
        scores = data["synthese"]["scores_details"]
        scores_array = [
            scores["diversification"],
            scores["resilience"],
            scores["liquidite"],
            scores["fiscalite"],
            scores["croissance"]
        ]

        # Remplacement dans script
        new_script = script_tag.string.replace(
            "data: [8,7.5,6.5,7,8.5]",
            f"data: {scores_array}"
        )
        script_tag.string = new_script
```

### 16.4 Classes CSS des badges

Les badges utilisent un système de classes CSS pour afficher visuellement le niveau de risque ou de sévérité.

**Classes de base** :
- `.badge` : Classe de base commune à tous les badges

**Classes de sévérité** (exclusives, une seule par badge) :
- `.badge.crit` : Critique (rouge foncé, texte blanc, gras)
- `.badge.high` : Élevé (rouge clair, texte rouge foncé)
- `.badge.mid` : Moyen (jaune, texte or foncé)
- `.badge.low` : Faible/Normal (vert clair, texte vert foncé)

**Styles CSS** (`templates/rapport.css`) :

```css
/* Classe de base */
.badge {
    display: inline-block;
    padding: 5px 10px;
    border-radius: 999px;
    font-size: 8.5pt;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.4px;
}

/* Déclinaisons par criticité */
.badge.crit {
    background: var(--red-dark);
    color: white;
    font-weight: 600;
}

.badge.high {
    background: var(--red-light);
    color: var(--red-dark);
}

.badge.mid {
    background: var(--gold-light);
    color: var(--gold-dark);
}

.badge.low {
    background: var(--green-light);
    color: var(--green-dark);
}

/* Badge neutre (optionnel) */
.badge.neutral {
    background: var(--blue-light);
    color: var(--blue-dark);
}

/* Variante pour les badges en tableau (plus compacts) */
table .badge {
    padding: 3px 8px;
}
```

**Utilisation dans le template** :

Les badges ne doivent PAS avoir de classe de sévérité hardcodée :

```html
<!-- ✓ Correct : classe dynamique appliquée par le générateur -->
<span class="badge" data-field="etablissement_risk">…</span>

<!-- ✗ Incorrect : classe hardcodée -->
<span class="badge high" data-field="etablissement_risk">…</span>
```

**Variables CSS utilisées** :

```css
:root {
    --red-dark: #991b1b;      /* Critique */
    --red-light: #fee2e2;     /* Élevé - fond */
    --red: #dc2626;           /* Élevé - texte */
    --gold-dark: #92400e;     /* Moyen - texte */
    --gold-light: #fef3c7;    /* Moyen - fond */
    --green-dark: #065f46;    /* Faible - texte */
    --green-light: #d1fae5;   /* Faible - fond */
    --blue-dark: #1e3a8a;     /* Neutre - texte */
    --blue-light: #dbeafe;    /* Neutre - fond */
}
```

**Mapping niveau → classe CSS** :

| Niveau risque | Classe CSS | Couleur | Cas d'usage |
|---------------|------------|---------|-------------|
| Critique | `crit` | Rouge foncé | Concentration >50%, risques majeurs |
| Élevé | `high` | Rouge clair | Concentration >30%, risques importants |
| Moyen | `mid` | Jaune | Risques modérés |
| Faible / Normal | `low` | Vert | Pas de risque particulier |

---

## 17. Spécifications détaillées - Stress Tests

### 17.1 Crise bancaire + Sapin 2

```python
def _test_banking_crisis(self, data: dict) -> Dict:
    """Scénario : Crise bancaire + activation Loi Sapin 2"""

    patrimoine_financier = data["patrimoine"]["financier"]["total"]

    # Actifs gelés
    av_gele = 0
    depots_geles = 0

    for etab in data["patrimoine"]["financier"]["etablissements"]:
        if etab["juridiction"] == "France":
            for compte in etab.get("comptes", []):
                if compte["type"] == "Assurance-vie":
                    av_gele += compte["montant"]
                elif compte["type"] == "Compte de dépôts":
                    # Hypothèse : 50% des dépôts gelés temporairement
                    depots_geles += compte["montant"] * 0.5

    total_gele = av_gele + depots_geles
    patrimoine_accessible = patrimoine_financier - total_gele
    pct_accessible = (patrimoine_accessible / patrimoine_financier) * 100

    return {
        "scenario": "Crise bancaire + Sapin 2",
        "description": "Blocage AV + gel partiel dépôts bancaires",
        "impact_montant": -total_gele,
        "impact_pct": -round((total_gele / patrimoine_financier) * 100, 1),
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
```

### 17.2 Krach actions -30%

```python
def _test_market_crash(self, data: dict) -> Dict:
    """Scénario : Krach boursier -30%"""

    patrimoine_total = (
        data["patrimoine"]["financier"]["total"] +
        data["patrimoine"].get("crypto", {}).get("total", 0) +
        data["patrimoine"].get("immobilier", {}).get("total", 0)
    )

    # Exposition actions (PEA, CTO, UC AV)
    exposition_actions = 0

    for etab in data["patrimoine"]["financier"]["etablissements"]:
        for compte in etab.get("comptes", []):
            if compte["type"] in ["PEA", "PEA-PME", "CTO"]:
                exposition_actions += compte["montant"]
            elif compte["type"] == "Assurance-vie":
                # Extraction UC (hors fonds euro)
                fonds = compte.get("fonds", [])
                for fond in fonds:
                    if "Euro" not in fond.get("nom", ""):
                        exposition_actions += fond.get("montant", 0)

    # Impact -30% sur actions
    perte = exposition_actions * 0.30
    patrimoine_final = patrimoine_total - perte
    pct_impact = (perte / patrimoine_total) * 100

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
```

### 17.3 Perte d'emploi

```python
def _test_job_loss(self, data: dict) -> Dict:
    """Scénario : Perte d'emploi prolongée"""

    revenu_mensuel = data["profil"].get("revenu_mensuel_net", 0)

    # Hypothèse dépenses : 70% du revenu
    depenses_mensuelles = revenu_mensuel * 0.70

    # Liquidité disponible
    liquidite = 0
    for etab in data["patrimoine"]["financier"]["etablissements"]:
        for compte in etab.get("comptes", []):
            if compte["type"] in ["Compte de dépôts", "Livret A", "LDD", "PEL"]:
                liquidite += compte["montant"]

    # Durée tenable
    if depenses_mensuelles > 0:
        duree_mois = int(liquidite / depenses_mensuelles)
    else:
        duree_mois = 999

    return {
        "scenario": "Perte d'emploi 12-24 mois",
        "description": f"Capacité maintien niveau de vie ({depenses_mensuelles:,.0f}€/mois)",
        "duree_mois": duree_mois,
        "severite": "Faible" if duree_mois >= 12 else ("Moyenne" if duree_mois >= 6 else "Haute"),
        "details": {
            "liquidite_disponible": liquidite,
            "depenses_mensuelles": depenses_mensuelles,
            "revenu_mensuel": revenu_mensuel
        },
        "recommandation": f"Cible : 12 mois ({depenses_mensuelles * 12:,.0f}€)"
    }
```

---

## 18. Dépendances Python (`requirements.txt`)

```txt
# Core
python>=3.10

# Data processing
pandas>=2.0.0
numpy>=1.24.0

# File parsing
pdfplumber>=0.10.0
PyPDF2>=3.0.0
openpyxl>=3.1.0

# HTML/Web
beautifulsoup4>=4.12.0
lxml>=4.9.0

# API
anthropic>=0.25.0
requests>=2.31.0

# Config
pyyaml>=6.0

# Utils
python-dateutil>=2.8.0
```

---

## 19. Checklist de développement

### Phase 1 : Infrastructure (Jour 1)

- [ ] Créer arborescence complète
- [ ] Configurer logging
- [ ] Créer fichiers `__init__.py`
- [ ] Implémenter `main.py` (structure de base)
- [ ] Tester génération logs

### Phase 2 : Normalizer (Jour 2-3)

- [ ] Parser `patrimoine.md` (structure basique)
- [ ] Implémenter `FileParser.parse_csv()`
- [ ] Implémenter `FileParser.parse_pdf()`
- [ ] Implémenter calcul totaux récursifs
- [ ] Générer `patrimoine_input.json` valide
- [ ] Tests unitaires normalizer

### Phase 3 : Web Research (Jour 4-5)

- [ ] Implémenter `WebResearcher.search()`
- [ ] Intégrer API Anthropic
- [ ] Implémenter extraction sources
- [ ] Implémenter retry logic
- [ ] Tester avec 5-10 requêtes réelles
- [ ] Tests unitaires web_research

### Phase 4 : Risk Analyzer (Jour 6-8)

- [ ] Implémenter analyse concentration
- [ ] Implémenter analyse réglementaire (Loi Sapin 2)
- [ ] Implémenter analyse fiscale
- [ ] Implémenter analyse marché
- [ ] Implémenter analyse liquidité
- [ ] Intégrer recherches web dans analyse risques
- [ ] Tests unitaires risk_analyzer

### Phase 5 : Recommender (Jour 9-10)

- [ ] Implémenter génération recommandations
- [ ] Implémenter calcul score priorité
- [ ] Implémenter classification recommandations
- [ ] Lier recommandations aux risques
- [ ] Tests unitaires recommendations

### Phase 6 : Stress Tester (Jour 11)

- [ ] Implémenter 5 scénarios stress tests
- [ ] Valider calculs impacts
- [ ] Tests unitaires stress_tester

### Phase 7 : Analyzer (Jour 12-13)

- [ ] Orchestrer tous les modules
- [ ] Implémenter synthèse globale
- [ ] Générer `patrimoine_analysis.json` complet
- [ ] Valider structure JSON sortie
- [ ] Tests intégration analyzer

### Phase 8 : Generator (Jour 14-15)

- [ ] Implémenter injection champs simples
- [ ] Implémenter duplication lignes répétées
- [ ] Implémenter injection graphique Chart.js
- [ ] Générer rapport HTML complet
- [ ] Valider rendu HTML
- [ ] Tests unitaires generator

### Phase 9 : Tests & Polish (Jour 16-17)

- [ ] Tests end-to-end complets
- [ ] Vérifier gestion erreurs
- [ ] Optimiser performances
- [ ] Améliorer messages logs
- [ ] Documentation code

### Phase 10 : Validation finale (Jour 18)

- [ ] Test avec vrai fichier `patrimoine.md`
- [ ] Vérifier 40-50 recherches web
- [ ] Valider rapport HTML final
- [ ] Vérifier logs complets
- [ ] Documentation utilisateur

---

## 20. Exemple de session complète

### Entrée : `sources/patrimoine.md`

```markdown
# Patrimoine financier

## Profil
- Genre : Homme
- Date de naissance : 23/11/1975
- Situation familiale : Marié
- Type d'investissement : Dynamique
- Revenu : 3500 € / mois

## Epargne

### CA (Crédit Agricole)
- Assurance vie (AV) : 106 046,01 €
- Livrets A : 24 327,95 €
- PEA : 82 186,48 €
- Voir fichier "[CA] - PEA.pdf"

### DGO (Degiro)
- CTO : 30 596,54 €
- Voir fichier "[DGO] - CTO.csv"
```

### Sortie : `generated/rapport_20251021_143330.html`

```html
<!DOCTYPE html>
<html lang="fr">
<head>
  <title>Rapport Patrimonial — 21 octobre 2025</title>
  ...
</head>
<body>
  <section class="cover">
    <h1 class="title">Rapport Patrimonial</h1>
    <div class="subtitle">21 octobre 2025</div>
  </section>

  <section class="metrics">
    <div class="card">
      <div class="label">Patrimoine total</div>
      <div class="value">470 354 €</div>
    </div>
    ...
  </section>

  <section id="risques">
    <h2>Risques patrimoniaux</h2>
    <div class="alert">
      <strong>1. Loi Sapin 2 — Blocage assurance-vie :</strong>
      exposition AV = 106 046 € (30.1% du patrimoine financier)
    </div>
    ...
  </section>

  <section id="recommandations">
    <h2>Recommandations prioritaires</h2>
    <div class="reco">
      <h3>Réduire exposition Loi Sapin 2 (AV)</h3>
      <p><strong>Action :</strong> transférer 40 000 € vers PEA</p>
      <p><strong>Bénéfice :</strong> réduction exposition de 30.1% à 18.8%</p>
    </div>
    ...
  </section>
</body>
</html>
```

---

## 21. Points d'attention pour Claude Code

### 21.1 Priorités d'implémentation

1. **Focus initial** : Normalizer → Structure JSON solide
2. **Critique** : Web Research → Sources citées obligatoires
3. **Qualité** : Risk Analyzer → Analyse approfondie
4. **Finition** : Generator → Injection propre sans bugs

### 21.2 Pièges à éviter

- ❌ Ne pas inventer de données manquantes
- ❌ Ne pas modifier le template HTML
- ❌ Ne pas faire d'hypothèses sur structure fichiers sources
- ❌ Ne pas oublier gestion
