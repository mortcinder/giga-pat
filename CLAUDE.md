# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project Overview

Patrimoine Analyzer is an automated wealth report generator that transforms source files (CSV, PDF, Markdown) into professional HTML reports with deep analysis, web research, and risk assessment. The system follows a strict 3-stage pipeline architecture with no user interaction during execution.

**Version**: v2.1 (November 2025) - Architecture homogène avec custodian unifié et sections manuelles

**Note**: Since October 2025, PEA and PEA-PME files from Crédit Agricole use PDF format instead of CSV.

## v2.1 Key Changes (November 2025)

1. **Homogeneous Custodian Architecture**
   - Unified `custodian` + `custodian_name` + `custody_type` across ALL asset types
   - Custody types: `institutional`, `custodial_platform`, `self_custody`, `defi`, `direct_ownership`
   - Unique IDs for all assets: `{custodian}_{type}_{seq}`

2. **Manual Data Sections in manifest.json**
   - `patrimoine.liquidites[]`: Livrets, PEL, LDD, comptes dépôt
   - `patrimoine.obligations[]`: T-Bonds (multi-currency support)
   - `patrimoine.crypto[]`: All cryptos (custodial, self-custody, DeFi)
   - `patrimoine.metaux_precieux[]`: Gold, silver, platinum
   - `patrimoine.immobilier[]`: Real estate properties
   - `patrimoine.comptes_titres[]`: Parsable securities accounts

3. **Currency Standardization**
   - Explicit `currency` field (ISO 4217: "EUR", "USD")
   - `montant_eur_equivalent` for foreign currencies

4. **Migration v2.0 → v2.1**
   - Move `comptes[]` → `patrimoine.comptes_titres[]`
   - Rename `etablissement` → `custodian` + add `custodian_name`, `custody_type`
   - Add manual sections with currency fields
   - Test: `python main.py` and verify `generated/patrimoine_input.json`

## Core Commands

```bash
# Generate full report
python main.py
# OR use slash command:
/report

# Test individual components
python tests/test_normalizer.py
python tests/test_analyzer.py
python tests/test_generator.py

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env and add BRAVE_API_KEY (get from https://api.search.brave.com/app/dashboard)
```

## Architecture: 3-Stage Pipeline

```
sources/manifest.json (v2.1) + CSV/PDF files
    ↓
[Stage 1: Normalizer + Parsers + Manual Data] → generated/patrimoine_input.json
    ↓
[Stage 2: Analyzer + Web Research] → generated/patrimoine_analysis.json
    ↓
[Stage 3: Generator] → generated/rapport_YYYYMMDD_HHMMSS.html
```

### Stage 1: Normalizer (`tools/normalizer.py`)

**Purpose**: Parse files, integrate manual data, output normalized JSON.

**Flow**:
1. Load & validate `manifest.json` (v2.1 structure)
2. Parse `comptes_titres[]` via ParserRegistry (PEA, AV, CTO, PER)
3. Group by custodian
4. Integrate manual sections (liquidites, obligations, crypto, metals, real estate)
5. Enrich with metadata
6. Calculate totals
7. Output `patrimoine_input.json`

**Key v2.1 Methods**:
- `_group_comptes_titres()`: Groups parsed securities by custodian
- `_integrate_liquidites()`, `_integrate_obligations()`, `_integrate_crypto()`, `_integrate_metaux_precieux()`, `_integrate_immobilier()`
- `_create_etablissement_entry()`: Creates custodian entry for manual assets

**Pluggable Parsers System** (v2.0):
- **BaseParser** interface: `strategy_name`, `can_parse()`, `parse()`, `validate()`
- **ParserRegistry**: Central registry with fallback mechanism
- **Available parsers**:
  - `credit_agricole.pea.v2025`: PEA/PEA-PME PDF format
  - `credit_agricole.av.v2_lignes`: Assurance-vie 2-line format
  - `generic.csv.flexible`: Flexible CSV mapping
  - `bitstack.transaction_history.v2025`: Bitstack crypto transactions (v2.1+)

**Multi-File Parsing with Cache** (v2.1+):
- **Pattern matching**: `source_pattern: "Bitstack/[BIT] - *.csv"` matches multiple files
- **Intelligent caching**: Years < current year cached automatically (MD5-based invalidation)
- **Performance**: 80% faster on subsequent runs (3 cached + 1 parsed vs 4 parsed)
- **Cache location**: `generated/cache/{custodian}_{year}.json`

**Adding New Parser**:
1. Create `tools/parsers/{bank}/{type}_v{year}.py` implementing `BaseParser`
2. Register in `normalizer.py` `__init__()`
3. Update `manifest.json` with `parser_strategy`
4. Optional: Use `source_pattern` for multi-file + `cache_historical_years: true`

### Stage 2: Analyzer (`tools/analyzer.py`)

**Purpose**: Deep analysis with web research, risk assessment, recommendations.

**Key Components**:
- **7 risk categories** (`risk_analyzer.py`): Concentration, regulatory, fiscal, market, liquidity, political, currency
- **Web research** (`web_research.py`): 15-18 searches via Brave API, rate limiting 1.1-1.5s
- **5 scores** (0-10): diversification, resilience, liquidity, fiscal, growth
  - All enriched with labels and breakdowns
  - Parameters in `config/analysis.yaml`
- **Portfolio optimization** (`portfolio_optimizer.py`): Markowitz efficient frontier, Sharpe ratios
- **Stress tests** (`stress_tester.py`): 5 scenarios
- **Recommendations** (`recommendations.py`): Scored by `(criticité × 0.4) + (impact × 0.3) + (facilité × 0.3)`
- **Benchmark gaps** (`benchmark_gap.py`): Compares allocation to target ranges

**4 Investor Profiles**: dynamique, equilibre, prudent, default (configured in `config/analysis.yaml`)

### Stage 3: Generator (`tools/generator.py`)

**Purpose**: Inject data into HTML template, generate standalone HTML.

**Injection System**:
1. **CSS inlining**: `rapport.css` → `<style>` tag (standalone HTML)
2. **Simple fields**: `data-field="fieldname"` → direct replacement
3. **Repeated rows**: `data-repeat="typename"` → clone and populate
4. **Conditional elements**: `data-conditional="identifier"` → remove if condition not met
5. **Dynamic badges**: Severity classes applied dynamically (`crit`, `high`, `mid`, `low`)
6. **Chart injection**: Radar chart scores via regex
7. **Two-line asset classes**: Primary (asset type) + secondary (account detail)

**Key Methods**:
- `_inline_css()`: Makes HTML standalone
- `_inject_simple_fields()`: Maps JSON paths to template fields
- `_inject_repeated_rows()`: Handles establishments, assets, risks, recommendations
- `_inject_classes_actifs()`: Special handling for asset classes table
- `_inject_chart_data()`: Radar chart scores

## Configuration

**`config/config.yaml`**:
- Risk thresholds, web research settings
- Paths (sources/, templates/, generated/, logs/)
- Active profile selection

**`config/analysis.yaml`**:
- 4 investor profiles with return/volatility assumptions
- Asset statistics (12 classes)
- Correlation matrix
- Benchmarks: `{min, target, max}` allocation ranges per profile
- Score calculation parameters
- Account classification keywords

**`config/manifest.schema.json`**: JSON Schema validation for v2.1 structure

## Key Design Principles

1. **No file modification**: Never modify source files or templates
2. **Timestamped outputs**: `rapport_YYYYMMDD_HHMMSS.html`
3. **Zero interaction**: Fully autonomous execution
4. **Template injection**: Safe via `data-field` and `data-repeat` attributes
5. **Web research**: All risks backed by sources (15-18 API calls)
6. **Profile passthrough**: `profil` flows through all stages unchanged

## Modifying the Template

**Rules** (`templates/rapport_template.html`):
- Preserve `data-field="fieldname"` attributes
- Preserve `data-repeat="typename"` attributes
- Use `data-conditional="identifier"` for removable elements
- Badges: ONLY `class="badge"` (NO hardcoded severity classes)
- Available fields documented in `PRD.md` section 3.3.5

**Badge CSS Classes**:
- `.badge.crit`: Critical (red-dark)
- `.badge.high`: High (red-light)
- `.badge.mid`: Medium (gold)
- `.badge.low`: Normal (green)

**Enriched Scores Sections** (design v3.0):
- 5 scores with detailed breakdowns
- Design pattern: `.syn-block` → `.syn-head` → `.syn-grid` → `.syn-note-list`
- Standardized note labels: **Bonus :**, **Pénalités :**, **Alerte :**, **Interprétation :**, **Méthodologie :**

## Common Development Scenarios

**Adding a risk**:
- **Option 1**: Add contextual search in `config/risks.yaml` (no code)
- **Option 2**: Add structural risk method in `risk_analyzer.py` (requires code)

**Adding template field**:
1. Add `data-field="newfield"` in template
2. Add mapping in `generator.py` `_inject_simple_fields()`

**Customizing analysis**:
- Change profile: `config.yaml` → `analysis.active_profile`
- Adjust statistics/correlations: `config/analysis.yaml` → `profiles.[name]`
- Adjust benchmarks: `config/analysis.yaml` → `benchmarks.[profile]`
- Customize scores: `config/analysis.yaml` → `scores.[score_name]`

**Testing**:
- Test stages independently: `tests/test_*.py`
- Check generated JSON: `generated/`
- Review logs: `logs/rapport_YYYYMMDD_HHMMSS.log`

## Risk Detection System v2.0

**3 Levels**:
1. **Structural Risks**: Coded in `risk_analyzer.py` (always active)
2. **Contextual Risks**: Dynamic web detection via `config/risks.yaml` (optional)
3. **Future**: LLM-based analysis (reserved)

**Configuration** (`config/risks.yaml`):
- `risk_settings.enable_contextual_detection`: true/false
- `structural_risks`: Thresholds and detection rules
- `contextual_searches`: Web queries for emerging risks

**Adding Contextual Risk** (no code):
```yaml
# In config/risks.yaml → contextual_searches
my_risk:
  enabled: true
  queries: ["query 1", "query 2"]
  relevance_threshold: 0.7
```

Then add mapping in `risk_analyzer.py` → `_get_contextual_risk_mapping()`

## Important Implementation Details

**Account Classification** (`analyzer.py`):
- **Liquidités**: Livret A, LDD, **PEL** (state-guaranteed savings), compte dépôts
- **Actions**: PEA, CTO, PER, AV-UC, Parts Sociales
- **Obligations**: T-Bonds, bond funds in AV
- **Cryptomonnaies**: All custody types
- **Métaux précieux**: Physical precious metals
- **Immobilier**: SCPI, real estate

**PDF Parsing**:
- **AV**: 2-line format (line 0: name + valorization, line 1: breakdown)
- **PEA**: Multi-page web format, cash extraction from "Ma valorisation totale"

**Crypto Price Conversion** (v2.1+):
- **API**: CoinGecko (free, no key required)
- **Automatic**: BTC amounts auto-converted to EUR during parsing
- **Module**: `tools/crypto_price_api.py`

**Juridictions des établissements** (v2.1+):

1. **Comptes titres parsés** (PEA, CTO, AV, PER):
   - Enrichis automatiquement depuis `sources/etablissements_financiers.json`
   - Clés utilisées: `juridiction_principale`, `pays`, `garantie_depots`, `exposition_sapin_2`, `exposition_risque_france`
   - Fallback: "France" si établissement non trouvé
   - Module: `tools/normalizer.py` → `_enrich_etablissements_metadata()`

2. **Actifs manuels** (liquidités, obligations, métaux précieux, crypto, immobilier):
   - Spécifier dans `metadata.juridiction` et `metadata.juridiction_pays`
   - Lecture depuis `manifest.json` → `patrimoine.[section].[actif].metadata`
   - Exemple:
   ```json
   {
     "id": "ubs_compte_depot_001",
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
   ```

3. **Validation**: Schéma JSON (`config/manifest.schema.json`) documente tous les champs disponibles

4. **Impact**: La juridiction alimente le score de diversification (composante juridictionnelle 40%) et les risques de concentration

**Benchmark Gap**: Compares allocation to targets, 5 status levels (dans_la_cible, sous/sur_pondere_modere/fort)

**Diversification Score v1.1**:
- Formula: `(Institutional × 60%) + (Jurisdictional × 40%) + Bonuses`
- 3 bonuses: ≥5 classes (+1.0), ≥10 positions (+0.5), >15% intl (+0.5)
- 5 labels: Excellente (9-10), Bonne (7-9), Modérée (5-7), Forte (3-5), Critique (0-3)

**Growth Score v2.1**: Actions/UC/PER 100%, Crypto 50% (recognizes growth potential while accounting for speculation)

## Documentation

- `PRD.md`: Complete technical specification (900+ lines)
- `README.md`: User-facing documentation
- All code includes PRD section references in comments
