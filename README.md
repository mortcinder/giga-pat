# 💼 Patrimoine Analyzer

**Générateur automatisé de rapports patrimoniaux professionnels**

**Version 2.0** - Architecture manifest-driven avec parsers pluggables

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

## 📄 Licence

MIT License - Voir LICENSE pour détails

## 👤 Auteur

Gilles HOFF - Développeur informatique

## 🔗 Liens utiles

- Documentation Brave Search API : https://api.search.brave.com/
- PDFPlumber : https://github.com/jsvine/pdfplumber
- Pandas : https://pandas.pydata.org/
