# CLAUDE.md

**Context**: This file is loaded automatically by Claude Code. Keep it concise (100-150 lines). Detailed docs are in folder-specific CLAUDE.md files.

## Project Overview

Patrimoine Analyzer is an automated wealth report generator that transforms source files (CSV, PDF, Markdown) into professional HTML reports with deep analysis, web research, and risk assessment.

**Version**: v2.2.0 (November 2025) - Multi-provider web search with automatic fallback

**Architecture**: 3-stage pipeline with NO user interaction during execution

```
sources/manifest.json (v2.1) + CSV/PDF files
    ↓
[Stage 1: Normalizer + Parsers] → generated/patrimoine_input.json
    ↓
[Stage 2: Analyzer + Web Research] → generated/patrimoine_analysis.json
    ↓
[Stage 3: Generator] → generated/rapport_YYYYMMDD_HHMMSS.html
```

## ⚠️ Critical Prerequisites

**Python 3.10+ REQUIRED** - NOT compatible with 3.7, 3.8, or 3.9

The codebase uses modern Python features unavailable in earlier versions:
- Native type hints: `dict[str, Any]`, `list[str]`
- String methods: `str.removesuffix()`, `str.removeprefix()`
- Modern dependencies: pandas>=2.0, scipy>=1.11

**Enforcement**: `main.py` includes fail-fast version check (lines 14-36)

## Quick Commands

```bash
# Generate full report
python main.py          # OR use slash command: /report

# Test individual stages
python tests/test_normalizer.py
python tests/test_analyzer.py
python tests/test_generator.py

# Setup
pip install -r requirements.txt
cp .env.example .env    # Add API keys (Brave, Serper, Tavily - DuckDuckGo works without key)
```

## v2.2 Key Changes (November 2025)

1. **Multi-Provider Web Search Architecture**
   - **4 providers**: Brave (2000 req/month), Serper (2500 req/month), Tavily (1000 req/month), DuckDuckGo (unlimited)
   - **Automatic fallback**: Brave → Serper → Tavily → DuckDuckGo
   - **Pluggable architecture**: Add new providers by creating a single class
   - **Configuration-driven**: All settings in `config.yaml` (rate limits, timeouts, priorities)
   - **Backward compatible**: API unchanged, no modifications required in analyzer.py
   - See `tools/utils/search_providers/README.md` for architecture details

## v2.1 Key Changes (November 2025)

1. **Unified Custodian Architecture**
   - `custodian` + `custodian_name` + `custody_type` across ALL assets
   - Types: `institutional`, `custodial_platform`, `self_custody`, `defi`, `direct_ownership`
   - Unique IDs: `{custodian}_{type}_{seq}`

2. **Manual Data Sections** (in `manifest.json`)
   - `patrimoine.liquidites[]`: Cash accounts (Livret A, PEL, LDD)
   - `patrimoine.obligations[]`: Bonds (multi-currency)
   - `patrimoine.crypto[]`: All cryptos (all custody types)
   - `patrimoine.metaux_precieux[]`: Precious metals
   - `patrimoine.immobilier[]`: Real estate
   - `patrimoine.comptes_titres[]`: Parsable securities (PEA, AV, CTO, PER)

3. **Currency Standardization**
   - Explicit `currency` field (ISO 4217: "EUR", "USD")
   - `montant_eur_equivalent` for foreign currencies

4. **Automatic Real Estate Valorization** (v2.1.2+)
   - **Dynamic revaluation**: Property values recalculated at EVERY report generation
   - **Web extraction**: Parses price/m² from web search results (multi-provider)
   - **Intelligent fallback**: City-specific prices when API unavailable (Nanterre: 5300€/m², Paris: 10500€/m²)
   - **Plus-value tracking**: Auto-calculates appreciation since acquisition
   - **⚠️ DO NOT** include `valeur_actuelle` in manifest.json - only `prix_acquisition` + `surface_m2`
   - See `tools/CLAUDE.md` → "Real Estate Valorization" for details

5. **CrypCool Parser v2026** (v2.1.3+)
   - **Transactional format**: Supports new CSV format with Timestamp, Operation type, Base amount, etc.
   - **Fee deduction**: Crypto fees automatically deducted from holdings
   - **Crypto-to-crypto trades**: Full support (e.g., BTC spent to buy VRO)
   - **Accurate valuation**: Shows real liquidable value (~2-3% lower than CrypCool display)
   - See `tools/CLAUDE.md` → "Crypto Parsers" for details

## Key Design Principles

1. **No file modification**: Never modify source files or templates
2. **Timestamped outputs**: `rapport_YYYYMMDD_HHMMSS.html` (no overwrites)
3. **Zero interaction**: Fully autonomous execution
4. **Safe injection**: Via `data-field` and `data-repeat` attributes only
5. **Web-backed risks**: All risks backed by web sources (15-18 API calls)
6. **Profile passthrough**: `profil` flows through all stages unchanged

## Configuration Files

**Main**: `config/config.yaml`
- Risk thresholds, web research settings
- Paths, active profile selection

**Analysis**: `config/analysis.yaml`
- 4 investor profiles (dynamique, equilibre, prudent, default)
- Asset statistics (12 classes), correlation matrix
- Benchmarks: `{min, target, max}` allocation ranges
- Score parameters (5 scores: diversification, resilience, liquidity, fiscal, growth)

**Risks**: `config/risks.yaml`
- Structural risk thresholds
- Contextual search queries (web-based detection)

**Schema**: `config/manifest.schema.json`
- JSON Schema validation for v2.1 manifest structure

**Detailed config docs**: `config/CLAUDE.md`

## Architecture Deep Dive

### Stage 1: Normalizer (`tools/normalizer.py`)
- Parse files via ParserRegistry (pluggable parsers)
- Integrate manual data sections
- Enrich with metadata (juridictions from `config/etablissements_financiers.yaml`)
- Output: `patrimoine_input.json`

**Parsers**: credit_agricole.pea.v2025, credit_agricole.av.v2_lignes, generic.csv.flexible, bitstack.transaction_history.v2025, crypcool.csv.v2025, crypcool.csv.v2026, bforbank.cto.v2025, boursobank.per.v2025

**Multi-file parsing**: Pattern matching + intelligent caching (80% faster on re-runs)

**Detailed docs**: `tools/CLAUDE.md`

### Stage 2: Analyzer (`tools/analyzer.py`)
- 7 risk categories (concentration, regulatory, fiscal, market, liquidity, political, currency)
- 5 enriched scores (0-10 scale with labels and breakdowns)
- Web research via multi-provider architecture (Brave/Serper/Tavily/DuckDuckGo with automatic fallback)
- Portfolio optimization (Markowitz), stress tests (5 scenarios)
- Recommendations (scored by criticité/impact/facilité)
- Benchmark gaps (5 status levels)

**Detailed docs**: `tools/CLAUDE.md`

### Stage 3: Generator (`tools/generator.py`)
- Inject data into HTML template
- 7 injection mechanisms: CSS inlining, simple fields, repeated rows, conditional elements, dynamic badges, chart injection, two-line asset classes
- Output: Standalone HTML (no external dependencies)

**Detailed docs**: `templates/CLAUDE.md`

## Common Tasks

**Add parser**:
1. Create `tools/parsers/{bank}/{type}_v{year}.py` implementing `BaseParser`
2. Register in `normalizer.py`
3. Update `manifest.json` with `parser_strategy`
→ Details: `tools/CLAUDE.md` → "Adding New Parser"

**Add risk**:
- **No code**: Add contextual search in `config/risks.yaml`
- **Requires code**: Add structural risk in `risk_analyzer.py`
→ Details: `config/CLAUDE.md` → "Risk Detection System"

**Modify template**:
1. Edit `templates/rapport_template.html`
2. Preserve `data-field` and `data-repeat` attributes
3. Badges: ONLY `class="badge"` (NO hardcoded severity)
4. Add field mapping in `generator.py` if needed
→ Details: `templates/CLAUDE.md` → "Modifying the Template"

**Change profile**:
- Edit `config.yaml` → `analysis.active_profile` (dynamique/equilibre/prudent)
→ Details: `config/CLAUDE.md` → "Investor Profiles"

**Customize scores/benchmarks**:
- Edit `config/analysis.yaml` → `scores.*` or `benchmarks.*`
→ Details: `config/CLAUDE.md` → "Scores" / "Benchmarks"

## Testing

**Independent stage tests**:
```bash
python tests/test_normalizer.py  # Check patrimoine_input.json
python tests/test_analyzer.py    # Check patrimoine_analysis.json
python tests/test_generator.py   # Check rapport_*.html
```

**Check outputs**:
- JSON: `generated/*.json`
- HTML: `generated/rapport_*.html`
- Logs: `logs/rapport_*.log`

## Folder-Specific Documentation

**Detailed guides** (automatically loaded by Claude Code when working in these folders):
- `tools/CLAUDE.md`: Stage implementations, parsers, debugging
- `config/CLAUDE.md`: Configuration files, scores, risks, profiles
- `templates/CLAUDE.md`: Injection system, badges, field reference

**Complete spec**: `PRD.md` (900+ lines) - comprehensive technical specification

## Implementation Quick Reference

**Parsers**: Pluggable via `BaseParser` interface (`can_parse()`, `parse()`, `validate()`)

**Cache**: Multi-file parsing with MD5-based invalidation (`generated/cache/`)

**Scores**: All 0-10 scale with labels (Excellente/Bonne/Modérée/Faible/Critique)

**Risks**: 3 levels (Structural/Contextual/Future-LLM)

**Badges**: 4 severities (crit/high/mid/low) - dynamically applied, NEVER hardcoded

**Juridictions**: Auto-enriched from `config/etablissements_financiers.yaml` + manual in manifest

**Crypto prices**: CoinGecko API (free, auto-conversion BTC→EUR)

**Benchmark gaps**: 5 statuses (dans_la_cible, sous/sur_pondere_modere/fort)
