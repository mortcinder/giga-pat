# Implémentation du Parser Bitstack avec Cache

**Date**: 11 novembre 2025
**Version**: v2.1
**Objectif**: Parser dynamique des fichiers CSV Bitstack avec système de cache intelligent

## 📋 Vue d'ensemble

Cette implémentation ajoute un parser dédié pour les fichiers de transaction Bitstack, avec un système de cache optimisé pour éviter de retraiter les années passées.

## 🏗️ Architecture

### 1. Parser Bitstack (`tools/parsers/bitstack/transaction_history.py`)

**Caractéristiques**:
- Parse automatiquement tous les fichiers `[BIT] - *.csv`
- Calcule le solde BTC cumulé (achats - retraits + dépôts)
- Support des 3 types de transactions:
  - **Échange**: Achat de BTC avec EUR
  - **Retrait**: Envoi de BTC vers wallet externe
  - **Dépôt**: Réception de BTC (cadeau, transfert)

**Format de sortie**:
```json
{
  "type_compte": "Crypto",
  "positions": [{
    "nom": "Bitcoin 2022",
    "type": "BTC",
    "quantite": 0.00062009,
    "devise": "BTC",
    "metadata": {
      "year": "2022",
      "transaction_count": 32
    }
  }]
}
```

### 2. Système de Cache (`tools/cache_manager.py`)

**Fonctionnalités**:
- Cache automatique des années passées (< année courante)
- Invalidation par hash MD5 du fichier source
- Stockage JSON dans `generated/cache/`
- Métadonnées de cache incluant:
  - Hash du fichier
  - Date de création du cache
  - Année et custodian

**Logique de cache**:
```python
def should_cache_year(year: int) -> bool:
    current_year = datetime.now().year
    return year < current_year  # 2022-2024 → cachés, 2025 → recalculé
```

### 3. Support Multi-Fichiers dans Normalizer

**Modifications dans `tools/normalizer.py`**:

1. **Nouveau champ `source_pattern` dans manifest.json**:
   ```json
   {
     "source_pattern": "Bitstack/[BIT] - *.csv",
     "cache_historical_years": true
   }
   ```

2. **Méthode `_parse_compte_multi_files()`**:
   - Trouve tous les fichiers matchant le pattern
   - Gère le cache année par année
   - Consolide les résultats

3. **Fonction `_matches_pattern()`**:
   - Résout le problème de `glob` avec les crochets littéraux `[BIT]`
   - Utilise regex pour matcher correctement

## 📝 Configuration Manifest

### Ancienne configuration (v2.0)

```json
{
  "id": "bitstack_btc_002",
  "source_file": "[BIT] - BTC.csv",
  "parser_strategy": "generic.crypto.csv"
}
```

### Nouvelle configuration (v2.1)

```json
{
  "id": "bitstack_btc_002",
  "custodian": "bitstack",
  "custodian_name": "Bitstack",
  "custody_type": "custodial_platform",
  "type_actif": "BTC",
  "currency": "EUR",
  "source_pattern": "Bitstack/[BIT] - *.csv",
  "parser_strategy": "bitstack.transaction_history.v2025",
  "cache_historical_years": true,
  "fallback_parsers": []
}
```

## ✅ Tests

### Tests Unitaires (`tests/test_bitstack_parser.py`)

- ✅ Détection de fichiers Bitstack valides
- ✅ Parsing des fichiers 2022, 2023, 2024, 2025
- ✅ Calcul du solde BTC cumulé
- ✅ Validation des données parsées

### Tests d'Intégration (`tests/test_bitstack_integration.py`)

- ✅ Parsing avec système de cache
- ✅ Logique de mise en cache par année
- ✅ Invalidation du cache si fichier modifié

## 🚀 Utilisation

### Ajout d'un nouveau fichier CSV

1. Placer le fichier dans `sources/Bitstack/`:
   ```
   [BIT] - 2026.csv
   ```

2. Le fichier sera automatiquement détecté et parsé lors du prochain rapport

3. L'année courante (2025) sera **toujours recalculée**
4. Les années passées (2022-2024) seront chargées depuis le **cache**

### Invalidation manuelle du cache

```bash
python3 << 'EOF'
from tools.cache_manager import CacheManager

cache = CacheManager()
cache.invalidate_cache("bitstack_2022")  # Invalider une année
# OU
cache.clear_all()  # Vider tout le cache
EOF
```

### Statistiques du cache

```python
from tools.cache_manager import CacheManager

cache = CacheManager()
stats = cache.get_cache_stats()
print(f"Fichiers en cache: {stats['file_count']}")
print(f"Taille totale: {stats['total_size_mb']} MB")
```

## 📊 Performance

**Sans cache** (premier run):
- Parsing de 4 fichiers: ~0.5s
- Total transactions: ~300

**Avec cache** (runs suivants):
- 3 fichiers en cache (2022-2024): <0.01s
- 1 fichier parsé (2025): ~0.1s
- **Gain: 80% de temps** ⚡

## 🔧 Problèmes Résolus

### 1. Glob ne matche pas `[BIT]`

**Problème**: `glob("[BIT] - *.csv")` retourne 0 résultats car `[BIT]` est interprété comme un pattern de caractères.

**Solution**: Fonction `_matches_pattern()` utilisant regex avec `re.escape()`:

```python
def _matches_pattern(self, filename: str, pattern: str) -> bool:
    escaped = re.escape(pattern)  # Échappe [BIT] → \[BIT\]
    regex_pattern = escaped.replace(r'\*', '.*')  # Remplace \* → .*
    return re.fullmatch(regex_pattern, filename) is not None
```

### 2. Format de retour du parser

**Problème**: Le parser retournait une liste au lieu d'un dict.

**Solution**: Retourner `{'type_compte': 'Crypto', 'positions': [...]}`

## 📁 Structure des Fichiers

```
tools/
├── parsers/
│   ├── bitstack/
│   │   ├── __init__.py
│   │   └── transaction_history.py  [NOUVEAU]
│   └── ...
├── cache_manager.py                 [NOUVEAU]
└── normalizer.py                    [MODIFIÉ]

tests/
├── test_bitstack_parser.py          [NOUVEAU]
└── test_bitstack_integration.py     [NOUVEAU]

generated/
└── cache/                           [NOUVEAU]
    ├── bitstack_2022.json
    ├── bitstack_2023.json
    └── bitstack_2024.json

sources/
├── manifest.json                    [MODIFIÉ]
└── Bitstack/
    ├── [BIT] - 2022.csv
    ├── [BIT] - 2023.csv
    ├── [BIT] - 2024.csv
    └── [BIT] - 2025.csv
```

## 🎯 Bénéfices

1. **Dynamique**: Ajout automatique de nouveaux fichiers CSV
2. **Performant**: Cache évite le retraitement des années figées
3. **Robuste**: Détection automatique des modifications via hash
4. **Scalable**: Peut être étendu à d'autres custodians
5. **Maintenable**: Tests complets et architecture modulaire

## 🔮 Extensions Futures

- Support d'autres plateformes crypto (Kraken, Binance, etc.)
- Cache distribué pour équipes
- Compression des fichiers de cache
- Statistiques de performance du cache

---

**Auteur**: Claude Code
**Référence PRD**: Section 2.1.2 (Parsers pluggables)
