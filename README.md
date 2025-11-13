# 💼 Patrimoine Analyzer

![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)
![Version](https://img.shields.io/badge/version-2.1.0-orange.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**Générateur automatisé de rapports patrimoniaux professionnels**

**Version 2.1** - Architecture homogène avec custodian unifié et parsing multi-fichiers

Transformez vos fichiers sources (CSV, PDF, JSON) en rapports HTML détaillés avec analyse approfondie, recherches web et évaluation des risques.

## 🆕 Nouveautés v2.1 (Novembre 2025)

### Architecture homogène v2.1
- ✅ **Custodian unifié** : `custodian` + `custodian_name` + `custody_type` pour tous les actifs
- ✅ **Sections manuelles** : Liquidités, obligations, crypto, métaux, immobilier dans manifest
- ✅ **Multi-devises** : Support EUR/USD avec `montant_eur_equivalent`

### Parsing avancé v2.1
- ✅ **Multi-fichiers avec cache** : Parser plusieurs CSV avec cache intelligent (années passées)
- ✅ **Pattern matching** : `source_pattern: "Bitstack/[BIT] - *.csv"` détecte automatiquement
- ✅ **Performance** : 80% plus rapide avec cache (MD5-based invalidation)
- ✅ **Crypto API** : Conversion BTC→EUR automatique via CoinGecko (gratuit)

### Base v2.0
- ✅ **Manifest-driven** : `manifest.json` comme source de vérité unique
- ✅ **Parsers pluggables** : Ajout facile de nouveaux établissements
- ✅ **Profil investisseur** : Défini dans manifest (dynamique/équilibré/prudent)
- ✅ **Fallback automatique** : Robustesse accrue du parsing
- ✅ **Migration v1→v2** : Script automatique `generate_manifest.py`

---

## ⚠️ Prérequis

### Python 3.10 ou supérieur **OBLIGATOIRE**

**⛔ Ce projet n'est PAS compatible avec Python 3.7, 3.8 ou 3.9**

Le projet utilise des fonctionnalités modernes de Python qui ne sont disponibles qu'à partir de la version 3.10 :
- Type hints avec syntaxe native (`dict[str, Any]` au lieu de `Dict[str, Any]`)
- Méthodes de chaînes modernes (`removesuffix`, `removeprefix`)
- Dépendances récentes incompatibles avec les anciennes versions

**Vérifiez votre version Python :**

```bash
python --version
# ou
python3 --version
```

**Versions supportées :**
- ✅ Python 3.10.x
- ✅ Python 3.11.x
- ✅ Python 3.12.x
- ❌ Python 3.7 / 3.8 / 3.9 (incompatibles)

**Si vous avez Python <3.10**, le script `main.py` affichera un message d'erreur clair avec des instructions d'installation.

### Installation Python 3.10+

<details>
<summary>🪟 Windows</summary>

1. Télécharger l'installateur depuis [python.org](https://www.python.org/downloads/)
2. Lancer l'installateur
3. **Important** : Cocher "Add Python to PATH"
4. Vérifier : `python --version`

</details>

<details>
<summary>🍎 macOS</summary>

**Via Homebrew (recommandé) :**
```bash
brew install python@3.10
```

**Via pyenv (gestion multi-versions) :**
```bash
brew install pyenv
pyenv install 3.10.0
pyenv local 3.10.0
```

Vérifier : `python3 --version`

</details>

<details>
<summary>🐧 Linux</summary>

**Ubuntu/Debian :**
```bash
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip
```

**Fedora/RHEL :**
```bash
sudo dnf install python3.10
```

**Arch Linux :**
```bash
sudo pacman -S python
```

Vérifier : `python3 --version`

</details>

### Dépendances Python

Une fois Python 3.10+ installé :
```bash
pip install -r requirements.txt
```

---

## 🚀 Installation

```bash
# 1. Clone le repository
git clone https://github.com/mortcinder/giga-pat.git
cd giga-pat

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Configurer l'API Brave Search
cp .env.example .env
# Éditer .env et ajouter votre BRAVE_API_KEY
```

## 🔄 Migration v1 → v2 (utilisateurs existants)

Si vous avez déjà un fichier `patrimoine.md` :

```bash
# Générer manifest.json depuis patrimoine.md
python tools/generate_manifest.py

# Vérifier le manifest généré
cat sources/manifest.json

# Ajuster si nécessaire (profil_risque, parsers, etc.)
```

## 🎯 Quick Start v2.0

```bash
# 1. Créer votre manifest.json dans sources/
# Voir structure d'exemple ci-dessous

# 2. Placer vos fichiers CSV/PDF dans sources/

# 3. Générer le rapport
python main.py

# 4. Ouvrir le rapport HTML
open generated/rapport_*.html
```

## 📁 Structure manifest.json

Le `manifest.json` est le nouveau point d'entrée v2.0 qui définit :
- Profil investisseur (identité, profession, profil_risque)
- Liste des comptes avec mapping fichier → parser

```json
{
  "version": "2.0.0",
  "profil_investisseur": {
    "identite": {
      "genre": "Homme",
      "date_naissance": "1990-01-15",
      "situation_familiale": "Célibataire",
      "enfants": 0
    },
    "professionnel": {
      "statut": "Salarié",
      "profession": "Ingénieur",
      "revenu_mensuel_net": 3500
    },
    "investissement": {
      "profil_risque": "dynamique"
    }
  },
  "comptes": [
    {
      "id": "ca_pea_001",
      "etablissement": "credit_agricole",
      "type_compte": "PEA",
      "source_file": "[CA] - PEA.pdf",
      "parser_strategy": "credit_agricole.pea.v2025",
      "fallback_parsers": ["generic.csv.flexible"]
    }
  ]
}
```

**Profils disponibles** : `dynamique`, `equilibre`, `prudent`, `default`

## 🌍 Enrichir les juridictions des établissements

### Comptes titres (PEA, CTO, AV, PER)

Les juridictions des comptes parsés sont **enrichies automatiquement** depuis `config/etablissements_financiers.yaml`.

Le fichier contient 40+ établissements pré-configurés (banques françaises, courtiers internationaux, plateformes crypto, etc.).

**Aucune action requise** si votre établissement est dans la liste. Sinon, ajoutez-le :

```json
{
  "etablissements": {
    "votre_banque": {
      "nom": "Votre Banque",
      "juridiction_principale": "Luxembourg",
      "pays": "Luxembourg",
      "type": "Banque",
      "garantie_depots": "100000 EUR (FGDL)",
      "exposition_sapin_2": "NON",
      "exposition_risque_france": "FAIBLE"
    }
  }
}
```

### Actifs manuels (liquidités, obligations, crypto, métaux précieux, immobilier)

Pour les actifs saisis manuellement dans `manifest.json`, ajoutez les métadonnées de juridiction :

```json
{
  "patrimoine": {
    "liquidites": [
      {
        "id": "ubs_depot_001",
        "custodian": "ubs",
        "custodian_name": "UBS Bank",
        "custody_type": "institutional",
        "type_compte": "Compte dépôt",
        "currency": "CHF",
        "montant": 50000,
        "metadata": {
          "juridiction": "Suisse",
          "juridiction_pays": "Suisse",
          "garantie_depots": "100000 CHF (esisuisse)",
          "exposition_sapin_2": "NON",
          "exposition_risque_france": "FAIBLE"
        }
      }
    ],
    "crypto": [
      {
        "id": "ledger_btc_001",
        "custodian": "ledger",
        "custodian_name": "Ledger (self-custody)",
        "custody_type": "self_custody",
        "type_actif": "BTC",
        "currency": "EUR",
        "montant": 5000,
        "metadata": {
          "juridiction": "N/A",
          "juridiction_pays": "N/A"
        }
      }
    ]
  }
}
```

**Impact** : La juridiction alimente le score de diversification (40% du score) et les risques de concentration.

## 🏗️ Architecture v2.0

```
manifest.json + fichiers sources (CSV/PDF)
    ↓
[1. Normalisation + Parsers Registry] → patrimoine_input.json
    ↓
[2. Analyse + Web Research] → patrimoine_analysis.json
    ↓
[3. Génération HTML] → rapport_YYYYMMDD_HHMMSS.html
```

### Parsers pluggables (v2.0+)

```
tools/parsers/
├── base_parser.py              # Interface abstraite
├── registry.py                 # Registry + fallback
├── bitstack/                   # v2.1: Parser Bitstack
│   └── transaction_history.py
├── credit_agricole/
│   ├── pea_v2025.py           # Parser PEA CA format 2025
│   └── av_v2_lignes.py        # Parser AV CA 2 lignes
└── generic/
    └── csv_flexible.py         # Parser CSV générique
```

**Avantages** :
- ✅ Ajout d'un nouvel établissement = 1 parser + 1 ligne dans manifest
- ✅ Fallback automatique si parsing échoue
- ✅ Validation stricte (JSON Schema)
- ✅ Tests isolés par parser

### Multi-fichiers avec cache (v2.1+)

**Cas d'usage** : Transactions crypto réparties sur plusieurs années

```json
{
  "source_pattern": "Bitstack/[BIT] - *.csv",
  "cache_historical_years": true
}
```

**Fonctionnement** :
1. Détecte automatiquement `[BIT] - 2022.csv`, `[BIT] - 2023.csv`, etc.
2. Cache les années < année courante (MD5-based)
3. Reparse uniquement l'année courante
4. **Performance** : 80% plus rapide sur runs suivants

**Ajout nouveau fichier** :
```bash
# 1. Ajouter [BIT] - 2026.csv dans sources/Bitstack/
# 2. Relancer python main.py
# → Années passées depuis cache, 2026 parsé automatiquement
```

## 🎯 Fonctionnalités

### Analyse des risques (7 catégories)
1. **Concentration** : Sur-expositions établissement/juridiction
2. **Réglementaire** : Loi Sapin 2, garantie dépôts, plafonds PEA
3. **Fiscal** : PFU, AV, IFI
4. **Marché** : Volatilité, corrélations
5. **Liquidité** : Actifs bloqués (AV, PER, immobilier)
6. **Politique** : Instabilité, nationalisation
7. **Changes** : Exposition devises (USD, crypto)

### Optimisation de portefeuille
- Frontière efficiente (Markowitz)
- Ratio de Sharpe
- Graphique PNG intégré
- Recommandations d'allocation

### 4 Profils d'investisseur
- **Dynamique** : Actions 70-85% (croissance agressive)
- **Équilibré** : Actions 50-65% (compromis)
- **Prudent** : Actions 30-45% (préservation capital)
- **Default** : Statistiques historiques long terme

### Scores enrichis (0-10)
1. **Diversification** : Composantes institutionnelles + juridictionnelles + bonus
2. **Résilience** : Impact stress tests + risques critiques
3. **Liquidité** : Ratio adapté au profil (9-15 mois)
4. **Fiscalité** : Enveloppes fiscales + bonus/pénalités
5. **Croissance** : Exposition actions avec contexte profil

## 📚 Documentation

- **PRD.md** : Spécifications techniques complètes
- **CLAUDE.md** : Guide pour Claude Code (IA assistant)
- **README.md** : Ce fichier

## 🔧 Configuration

Tous les paramètres dans `config/`:
- `config.yaml` : Configuration générale + profil actif
- `analysis.yaml` : Profils investisseur, benchmarks, scores
- `manifest.schema.json` : Validation JSON Schema

## 📝 Exemple d'utilisation

```bash
# Exemple complet avec vos fichiers
cd giga-pat

# Si migration depuis v1.0
python tools/generate_manifest.py

# Vérifier/ajuster manifest
vim sources/manifest.json

# Générer rapport
python main.py

# Résultat
ls -lh generated/rapport_*.html
```

## 🆘 Rollback v1.0

Si besoin de revenir à l'ancienne architecture :

```bash
# Restaurer normalizer v1.0
cp tools/normalizer_v1_backup.py tools/normalizer.py

# Éditer config.yaml
# normalizer.input_file: "patrimoine.md"
# analysis.active_profile: "dynamique"

# Tester
python main.py
```

## 🔀 Workflow Git pour développement multi-instances

Si vous développez sur plusieurs machines (Windows, macOS) ou avec Claude Code Web, suivez ce workflow pour éviter le chaos de branches.

### Structure des branches

```
main        Production stable (tags: v2.0, v2.1, etc.)
  ↓
dev         Développement actif (toutes les instances travaillent ici)
  ↓
claude/[feature]-[ID]  Branches temporaires Claude Code Web (auto-supprimées après merge)
```

### Règles de base

**Sur Claude Code Desktop (Windows/macOS)** :
```bash
# Toujours travailler sur dev
git checkout dev
git pull origin dev

# Faire vos modifications
# ...

# Commit et push régulièrement
git add .
git commit -m "feat: description du changement"
git push origin dev
```

**Sur Claude Code Web** :
```bash
# Claude Code Web crée automatiquement des branches avec ID
# Format: claude/[description]-[ID]

# 1. Après le travail de Claude, merger vers dev
git checkout dev
git pull origin dev
git merge claude/[feature]-[ID]
git push origin dev

# 2. Supprimer la branche temporaire (local + remote)
git branch -d claude/[feature]-[ID]
git push origin --delete claude/[feature]-[ID]
```

**Release vers main** (uniquement quand version stable) :
```bash
# Merger dev → main
git checkout main
git pull origin main
git merge dev
git tag v2.2.0  # Ou version appropriée
git push origin main --tags
```

### Commandes utiles

```bash
# Voir toutes les branches
git branch -a

# Nettoyer les branches mergées localement
git branch --merged dev | grep -v "^\*\|main\|dev" | xargs git branch -d

# Nettoyer les branches remote obsolètes
git fetch --prune

# Voir l'historique des branches
git log --all --oneline --graph --decorate -10
```

### Synchronisation entre instances

**Avant de commencer à travailler** :
```bash
git checkout dev
git pull origin dev
```

**Après chaque session de travail** :
```bash
git add .
git commit -m "description"
git push origin dev
```

### En cas de conflit

```bash
# 1. Récupérer les derniers changements
git pull origin dev

# 2. Si conflit, résoudre manuellement
# Éditer les fichiers marqués en conflit

# 3. Marquer comme résolu
git add .
git commit -m "fix: resolve merge conflict"
git push origin dev
```

### Nettoyage périodique

**Mensuel ou après releases** :
```bash
# Lister toutes les branches remote
git branch -r

# Supprimer les branches claude/* obsolètes (déjà mergées)
git push origin --delete claude/[branch-name]

# Nettoyer les références locales
git fetch --prune
```

## 📄 Licence

MIT License - Voir LICENSE pour détails

## 👤 Auteur

Gilles HOFF - Développeur informatique

## 🔗 Liens utiles

- Documentation Brave Search API : https://api.search.brave.com/
- PDFPlumber : https://github.com/jsvine/pdfplumber
- Pandas : https://pandas.pydata.org/
