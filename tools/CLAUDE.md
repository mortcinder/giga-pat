# tools/ - Technical Implementation Guide

This file provides detailed technical guidance for working with the 3-stage pipeline implementation.

## Stage 1: Normalizer (`normalizer.py`)

**Purpose**: Parse files, integrate manual data, output normalized JSON.

**Execution Flow**:
1. Load & validate `manifest.json` (v2.1 structure)
2. Parse `comptes_titres[]` via ParserRegistry (PEA, AV, CTO, PER)
3. Group by custodian
4. Integrate manual sections (liquidites, obligations, crypto, metals, real estate)
5. Enrich with metadata (juridictions from `config/etablissements_financiers.yaml`)
6. Calculate totals
7. Output `generated/patrimoine_input.json`

**Key v2.1 Methods**:
- `_group_comptes_titres()`: Groups parsed securities by custodian
- `_integrate_liquidites()`, `_integrate_obligations()`, `_integrate_crypto()`, `_integrate_metaux_precieux()`, `_integrate_immobilier()`
- `_create_etablissement_entry()`: Creates custodian entry for manual assets
- `_enrich_etablissements_metadata()`: Enriches with juridiction data

### Pluggable Parsers System (v2.0)

**Architecture**:
- **BaseParser** interface: `strategy_name`, `can_parse()`, `parse()`, `validate()`
- **ParserRegistry**: Central registry with fallback mechanism
- **Strategy pattern**: Each parser handles specific file formats

**Available Parsers**:
- `credit_agricole.pea.v2025`: PEA/PEA-PME PDF format (multi-page web format)
- `credit_agricole.av.v2_lignes`: Assurance-vie 2-line format
- `generic.csv.flexible`: Flexible CSV mapping with column configuration
- `bitstack.transaction_history.v2025`: Bitstack crypto transactions (v2.1+)

### Multi-File Parsing with Cache (v2.1+)

**Pattern Matching**:
- Use `source_pattern` in manifest.json: `"Bitstack/[BIT] - *.csv"`
- Matches multiple files automatically
- Processes all matches in order

**Intelligent Caching**:
- **Automatic**: Years < current year cached by default
- **MD5-based**: Cache invalidated if file content changes
- **Performance**: 80% faster on subsequent runs (3 cached + 1 parsed vs 4 parsed)
- **Location**: `generated/cache/{custodian}_{year}.json`
- **Enable**: Set `cache_historical_years: true` in manifest.json

**Cache Invalidation**:
- File modification detected via MD5 hash
- Manual deletion: `rm generated/cache/*.json`

### Adding New Parser

**Step-by-Step**:
1. Create `tools/parsers/{bank}/{type}_v{year}.py`
2. Implement `BaseParser` interface:
   ```python
   class MyParser(BaseParser):
       strategy_name = "bank.type.v2025"

       def can_parse(self, file_path: str, config: dict) -> bool:
           # Return True if parser can handle this file

       def parse(self, file_path: str, config: dict) -> dict:
           # Return {"positions": [...], "metadata": {...}}

       def validate(self, data: dict) -> bool:
           # Validate parsed data structure
   ```
3. Register in `normalizer.py` `__init__()`:
   ```python
   self.parser_registry.register(MyParser())
   ```
4. Update `manifest.json`:
   ```json
   {
     "parser_strategy": "bank.type.v2025",
     "source_file": "path/to/file.pdf"
   }
   ```
5. Optional: Add `source_pattern` for multi-file + `cache_historical_years: true`

**Parser Best Practices**:
- Use `can_parse()` to check file format/structure before attempting parse
- Raise descriptive exceptions with file path context
- Return consistent position structure with required fields
- Log parsing steps for debugging

### PDF Parsing Details

**Assurance-Vie (2-line format)**:
- **Line 0**: Support name + total valorization
- **Line 1**: UC breakdown with percentages
- Pattern: `"Nom Support\s+([0-9\s,]+)"` for amounts
- UC detection: presence of percentage on line 1

**PEA/PEA-PME (multi-page web format)**:
- Multi-page PDF processing
- Cash extraction from "Ma valorisation totale"
- Pattern: `"Ma valorisation totale.*?([0-9\s,]+)\s*€"`
- Stock positions from tabular data

### Crypto Price Conversion (v2.1+)

**Implementation** (`crypto_price_api.py`):
- **API**: CoinGecko (free, no key required)
- **Endpoint**: `/api/v3/simple/price`
- **Automatic**: BTC amounts auto-converted to EUR during parsing
- **Caching**: 5-minute cache to avoid rate limits
- **Error handling**: Falls back to 0 if API unavailable

**Usage in Parser**:
```python
from tools.crypto_price_api import CryptoPriceAPI

api = CryptoPriceAPI()
eur_value = api.get_price_in_eur("bitcoin", btc_amount)
```

### Juridictions (v2.1+)

**Comptes Titres (Parsed Accounts)**:
- **Source**: `config/etablissements_financiers.yaml`
- **Fields**: `juridiction_principale`, `pays`, `garantie_depots`, `exposition_sapin_2`, `exposition_risque_france`
- **Fallback**: "France" if custodian not found
- **Enrichment**: Automatic in `_enrich_etablissements_metadata()`

**Manual Assets (liquidites, obligations, crypto, metals, real estate)**:
- **Source**: `manifest.json` → `patrimoine.[section].[asset].metadata`
- **Required fields**: `juridiction`, `juridiction_pays`
- **Optional fields**: `garantie_depots`, `exposition_sapin_2`, `exposition_risque_france`
- **Example**:
  ```json
  {
    "metadata": {
      "juridiction": "Suisse",
      "juridiction_pays": "Suisse",
      "garantie_depots": "100000 CHF (esisuisse)",
      "exposition_sapin_2": "NON",
      "exposition_risque_france": "FAIBLE"
    }
  }
  ```

**Impact**:
- Feeds diversification score (jurisdictional component: 40%)
- Used in concentration risk detection
- Appears in report's custodian details

## Stage 2: Analyzer (`analyzer.py`)

**Purpose**: Deep analysis with web research, risk assessment, recommendations.

**Key Components**:
- **7 risk categories** (`risk_analyzer.py`): Concentration, regulatory, fiscal, market, liquidity, political, currency
- **Web research** (`web_research.py`): 15-18 searches via Brave API, rate limiting 1.1-1.5s
- **5 scores** (0-10): diversification, resilience, liquidity, fiscal, growth
  - All enriched with labels and breakdowns
  - Parameters in `config/analysis.yaml`
- **Portfolio optimization** (`portfolio_optimizer.py`): Markowitz efficient frontier, Sharpe ratios
- **Stress tests** (`stress_tester.py`): 5 scenarios (market crash, rate hike, inflation, etc.)
- **Recommendations** (`recommendations.py`): Scored by `(criticité × 0.4) + (impact × 0.3) + (facilité × 0.3)`
- **Benchmark gaps** (`benchmark_gap.py`): Compares allocation to target ranges

**4 Investor Profiles**:
- `dynamique`: High growth (8% return, 15% volatility)
- `equilibre`: Balanced (6% return, 10% volatility)
- `prudent`: Conservative (4% return, 6% volatility)
- `default`: Fallback profile

Configured in `config/analysis.yaml` → see `config/CLAUDE.md` for details.

### Account Classification

**Asset Classes**:
- **Liquidités**: Livret A, LDD, **PEL** (state-guaranteed savings), compte dépôts
- **Actions**: PEA, CTO, PER, AV-UC, Parts Sociales
- **Obligations**: T-Bonds, bond funds in AV
- **Cryptomonnaies**: All custody types (institutional, custodial_platform, self_custody, defi)
- **Métaux précieux**: Physical precious metals (gold, silver, platinum)
- **Immobilier**: SCPI, real estate properties

**Classification Logic**:
- Keywords-based detection (configured in `config/analysis.yaml`)
- Account type mapping (PEA → Actions, Livret A → Liquidités)
- Explicit `type` field in manual assets

### Risk Detection System

**3 Levels**:
1. **Structural Risks**: Coded in `risk_analyzer.py` (always active)
   - Concentration risks (>70% in one class, >40% in one custodian)
   - Liquidity risks (<15% liquid assets)
   - Currency risks (>20% foreign exposure)
   - Regulatory risks (Sapin 2 exposure >30%)

2. **Contextual Risks**: Dynamic web detection via `config/risks.yaml` (optional)
   - Emerging market risks
   - Regulatory changes
   - Geopolitical events

3. **Future**: LLM-based analysis (reserved)

See `config/CLAUDE.md` for configuration details.

### Web Research

**Implementation** (`web_research.py`):
- **API**: Brave Search API (requires key in `.env`)
- **Rate limiting**: 1.1-1.5s between requests (API limit: 1 req/sec)
- **Queries**: 15-18 searches covering:
  - Regulatory risks per jurisdiction
  - Market trends per asset class
  - Custodian stability
  - Emerging risks
- **Source tracking**: All findings include URLs for transparency

**Adding Custom Search**:
- Edit `config/risks.yaml` → `contextual_searches`
- No code changes required

## Stage 3: Generator (`generator.py`)

**Purpose**: Inject data into HTML template, generate standalone HTML.

**Key Methods**:
- `_inline_css()`: Makes HTML standalone by embedding `rapport.css`
- `_inject_simple_fields()`: Maps JSON paths to `data-field` attributes
- `_inject_repeated_rows()`: Clones and populates rows for `data-repeat` attributes
- `_inject_classes_actifs()`: Special handling for asset classes table (two-line format)
- `_inject_chart_data()`: Injects radar chart scores via regex

**Output**:
- Timestamped: `generated/rapport_YYYYMMDD_HHMMSS.html`
- Standalone: CSS inlined, no external dependencies
- Ready to share: Single HTML file with all assets

See `templates/CLAUDE.md` for injection system details and template modification guide.

## Common Development Scenarios

### Adding a Parser

**Scenario**: You need to support a new bank or file format.

**Steps**:
1. Create parser class in `tools/parsers/{bank}/{type}_v{year}.py`
2. Implement `BaseParser` interface (see "Adding New Parser" section above)
3. Register parser in `normalizer.py` `__init__()`
4. Add test case in `tests/test_normalizer.py`
5. Update `manifest.json` with new `parser_strategy`

**Example**: Adding a Boursorama CTO parser
```python
# tools/parsers/boursorama/cto_v2025.py
from tools.parsers.base_parser import BaseParser

class BoursoramaCTOParser(BaseParser):
    strategy_name = "boursorama.cto.v2025"

    def can_parse(self, file_path: str, config: dict) -> bool:
        return "boursorama" in file_path.lower() and file_path.endswith(".csv")

    def parse(self, file_path: str, config: dict) -> dict:
        # Parsing logic here
        pass
```

### Testing Stages Independently

**Stage 1 (Normalizer)**:
```bash
python tests/test_normalizer.py
# Or directly:
python -c "from tools.normalizer import Normalizer; Normalizer().run()"
# Check output: cat generated/patrimoine_input.json
```

**Stage 2 (Analyzer)**:
```bash
python tests/test_analyzer.py
# Check output: cat generated/patrimoine_analysis.json
```

**Stage 3 (Generator)**:
```bash
python tests/test_generator.py
# Check output: ls -la generated/rapport_*.html
```

### Debugging Parsing Issues

**Common Issues**:
1. **Parser not recognized**: Check `parser_strategy` matches registered name
2. **File not found**: Verify `source_file` path relative to `sources/`
3. **Parsing fails**: Check logs in `logs/rapport_YYYYMMDD_HHMMSS.log`
4. **Cache issues**: Delete cache and re-run: `rm generated/cache/*.json && python main.py`

**Debugging Tips**:
- Add `print()` statements in parser's `parse()` method
- Use `can_parse()` to verify file detection logic
- Test parser in isolation before integrating
- Check generated JSON structure matches expected format

### Performance Optimization

**Caching**:
- Enable for historical data: `cache_historical_years: true`
- Cache location: `generated/cache/`
- Invalidation: Automatic on file modification (MD5)

**Web Research**:
- Disable contextual risks: `config/risks.yaml` → `enable_contextual_detection: false`
- Reduces 5-8 web searches (saves ~10 seconds)

**Parsing**:
- Use multi-file patterns to batch process files
- Leverage cache for unchanged historical files
