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
- `crypcool.csv.v2025`: CrypCool multi-crypto CSV aggregator (v2.1.1+)
- `bforbank.cto.v2025`: BforBank CTO PDF parser (v2.1+)
- `boursobank.per.v2025`: BoursoBank PER with Unicode corruption handling (v2.1+)

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

**BoursoBank PER (Unicode corruption handling)**:
- **Challenge**: BoursoBank PDFs use proprietary Unicode encoding (Private Use Area U+E000-U+F8FF)
- **Solution**: `clean_pdf_text()` function with complete character mapping
- **Mapping**:
  - Digits: `\ue0f1-\ue0fa` → `0-9`
  - Uppercase: `\ue0c2-\ue0ea` → `A-Z`
  - Lowercase: `\ue082-\ue0aa` → `a-z`
  - Punctuation: `\ue06c` → `,`, `\ue113` → `€`, etc.
- **Merged rows**: Detects multiple funds in single table row (split by `\nPD ` pattern)
- **Fallback**: Manual amount from metadata if PDF extraction fails
- **Location**: `tools/parsers/boursobank/per_v2025.py:14-133`

### Crypto Parsers (v2.1.1+)

**Bitstack Parser** (`bitstack.transaction_history.v2025`):
- **Format**: CSV transaction history with multi-file support
- **Logic**: Aggregates purchases, withdrawals, deposits across years
- **Output**: Single position per year with cumulative BTC balance
- **Ticker**: Generates `ticker: "BTC"` for generic EUR conversion
- **Caching**: Supports historical year caching (80% faster on re-runs)
- **Location**: `tools/parsers/bitstack/transaction_history.py`

**CrypCool Parser** (`crypcool.csv.v2025`):
- **Format**: CSV transaction history with multi-crypto columns
- **Logic**: Dynamic column detection + algebraic aggregation
- **Columns**: Auto-detects all crypto columns (BTC, ETH, VRO, etc.)
- **Aggregation**: `holdings[crypto] = sum(all transactions)` (+ and -)
- **Filter**: Only returns cryptos with `amount > 0` (positive balance)
- **Output**: One position per crypto with ticker for EUR conversion
- **Location**: `tools/parsers/crypcool/csv_transaction_aggregator_v2025.py`

**Known Issue - CrypCool CSV Data**:
- ⚠️ Some CrypCool CSV exports contain **negative balances** due to incomplete transaction history
- Example: User exchanges/withdraws MORE crypto than purchase records show
- Root cause: CSV export may not include all historical deposits or purchases
- **Parser behavior**: Correctly filters out negative balances (by design)
- **Resolution**: User must correct/complete their CSV export from CrypCool platform
- **Impact**: Missing cryptos won't appear in report until CSV data is corrected
- **Verification**: Parser treats ALL cryptos identically (no hardcoded logic)

**Crypto Parser Best Practices**:
- Always generate a `ticker` field (uppercase) for EUR conversion
- Use dynamic column detection (not hardcoded crypto names)
- Log conversion results with price and quantity
- Handle API failures gracefully (fallback to 0 or manual amounts)
- Include metadata (year, transaction_count) for debugging

### Crypto Price Conversion (v2.1.1+)

**Implementation** (`crypto_price_api.py`):
- **API**: CoinGecko (free, no key required)
- **Endpoint**: `/api/v3/simple/price`
- **Generic conversion**: ALL cryptos auto-converted to EUR via ticker mapping
- **Caching**: In-memory cache to avoid rate limits
- **Error handling**: Falls back to 0 if API unavailable or ticker unknown

**Supported Cryptos** (extensible via `TICKER_TO_COINGECKO_ID`):
- Major: BTC, ETH, BNB, SOL, ADA, DOT, AVAX, MATIC, LINK, UNI, ATOM
- Stablecoins: USDT, USDC
- Others: DOGE, LTC, XRP, VRO (VeraOne)

**Usage in Parser**:
```python
from tools.crypto_price_api import CryptoPriceAPI

api = CryptoPriceAPI()

# Generic method (works for any supported ticker)
eur_value = api.convert_crypto_to_eur("ETH", 0.5)  # 0.5 ETH → EUR
eur_value = api.convert_crypto_to_eur("VRO", 100)  # 100 VRO → EUR

# Legacy method (BTC only, deprecated)
eur_value = api.convert_btc_to_eur(0.001)  # 0.001 BTC → EUR
```

**Adding New Crypto**:
Add mapping in `crypto_price_api.py`:
```python
TICKER_TO_COINGECKO_ID = {
    'BTC': 'bitcoin',
    'ETH': 'ethereum',
    'NEWCOIN': 'coingecko-id-here',  # ← Add this line
    ...
}
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

### Crypto Integration in Normalizer (v2.1.1+)

**Method**: `_integrate_crypto()` (`normalizer.py:570-662`)

**Purpose**: Parse crypto files, valorize positions, store detailed `actifs[]` array

**Key Features**:
1. **Parse crypto files** via registered parsers (Bitstack, CrypCool, etc.)
2. **Generic EUR valorization** for ALL cryptos (not just BTC)
3. **Store detailed positions** in `actifs[]` field (required by analyzer)
4. **Multi-currency support**: EUR, USD, stablecoins, cryptos

**Valorization Logic** (lines 604-637):
```python
# Case 1: Fiat currencies (EUR, EURO)
if devise.upper() in ['EUR', 'EURO']:
    valeur_eur = quantite

# Case 2: USD stablecoins (approximation 1:1)
elif devise.upper() in ['USD', 'USDT', 'USDC', 'DAI', 'BUSD']:
    valeur_eur = quantite * 0.92  # ~USD→EUR conversion

# Case 3: Cryptocurrencies (BTC, ETH, VRO, etc.)
else:
    valeur_eur = self.crypto_api.convert_crypto_to_eur(ticker, quantite)
```

**Output Structure** (v2.1.1):
```python
plateforme_entry = {
    "nom": "CrypCool",
    "code": "crypcool",
    "type": "Crypto multi-actifs",
    "custody_type": "custodial_platform",
    "total": 121.15,  # ✅ Sum of all actifs
    "juridiction": "France",
    "juridiction_pays": "France",
    "actifs": [  # ✅ NEW: Detailed positions array
        {
            "ticker": "ETH",
            "nom": "ETH",
            "quantite": 0.03587361,
            "devise": "ETH",
            "valeur_eur": 98.63
        },
        {
            "ticker": "VRO",
            "nom": "VRO",
            "quantite": 0.19543974,
            "devise": "VRO",
            "valeur_eur": 22.52
        }
    ]
}
```

**Critical Fields**:
- `actifs[]`: **REQUIRED** by analyzer for position counting (line 721)
- `total`: Sum of all `valeur_eur` from actifs
- `ticker`: **REQUIRED** for EUR conversion via CoinGecko API
- `devise`: Usually same as ticker for cryptos

**Fallbacks**:
1. If API fails → check `pos.get('valeur_totale')` from parser
2. If no valeur → log warning and set to 0
3. Manual-only crypto (no source_file) → empty `actifs[]`, manual total

### Real Estate Valorization (v2.1.2+)

**Purpose**: Automatically revalue real estate at each report generation via web research + intelligent fallback.

**Architecture** (`tools/utils/real_estate_valorizer.py`):
- **Web extraction**: Parses price/m² from Brave API search results
- **Intelligent fallback**: City-specific prices when API unavailable (Nanterre: 5300€/m², Paris: 10500€/m², etc.)
- **Automatic calculation**: `valeur_actuelle = surface_m2 × prix_m2`
- **Plus-value tracking**: Auto-calculates appreciation since acquisition

**Integration Flow**:
1. **Normalizer** (`_integrate_immobilier()`):
   - Stores `prix_acquisition` as temporary `valeur_actuelle`
   - Preserves `surface_m2`, `adresse`, `metadata`
2. **Analyzer** (`risk_analyzer.py`, `_analyze_market_risks()`):
   - Performs web searches: `"prix immobilier m² {city} 2025"`
   - Calls `RealEstateValorizer.calculate_property_value()`
   - Updates `bien["valeur_actuelle"]` with calculated value
   - Stores `prix_m2_actuel`, `valorisation_source` (web/fallback)
   - Recalculates `data["patrimoine"]["immobilier"]["total"]`
3. **Report**: Displays updated valorization with enriched details

**Manifest Structure** (v2.1.2):
```json
{
  "patrimoine": {
    "immobilier": [{
      "id": "nanterre_studio_001",
      "type_bien": "Studio",
      "adresse": "34 rue Salvador Allende, 92000 Nanterre",
      "surface_m2": 25,
      "prix_acquisition": 110000,
      "currency": "EUR",
      "metadata": {
        "prix_m2_acquisition": 4400,
        "date_acquisition": "2016-06-30"
      }
    }]
  }
}
```

**⚠️ IMPORTANT**:
- **DO NOT** include `valeur_actuelle` in manifest.json
- Value is recalculated at EVERY report generation
- `prix_acquisition` is the only static reference value

**Example Output** (logs):
```
[INFO] Prix fallback pour Nanterre: 5300 €/m²
[INFO] Valorisation calculée : 25m² × 5300€/m² = 132500€ (source: fallback)
[INFO] Valorisation Studio Nanterre: 132,500€ (25m² × 5300€/m², source: fallback)
[INFO] Total immobilier recalculé: 132,500€
```

**Report Display**:
```
Valorisation Studio - Nanterre
Studio situé à 34 rue Salvador Allende, 92000 Nanterre.
Surface: 25m².
Valeur estimée actuelle: 132,500€
(prix m²: 5,300€, source: fallback).
Plus-value: +20.5% depuis acquisition (110,000€).
```

**Fallback Prices** (default values in `real_estate_valorizer.py`):
- Nanterre: 5300€/m²
- Paris: 10500€/m²
- Lyon: 5800€/m²
- Marseille: 4200€/m²
- Default: 3500€/m² (national average)

**Web Extraction Patterns**:
- `(\d[\d\s]*)\s*€\s*/\s*m[²2]` → "5 300 €/m²"
- `prix\s+(?:moyen|médian)\s*:\s*(\d[\d\s]*)\s*€` → "prix moyen : 5 300 €"
- Filters aberrant values (valid range: 1000-20000 €/m²)
- Returns median of extracted prices (robust against outliers)

**Customizing Fallback Prices**:
Edit `tools/utils/real_estate_valorizer.py` → `self.fallback_prices`:
```python
self.fallback_prices = {
    "nanterre": 5300,
    "my_city": 4500,  # Add your city
    "default": 3500
}
```

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

**Special Case: PDF Character Encoding Issues**:
- **Symptom**: PDF text appears as garbled Unicode characters (`\ue0xx`)
- **Diagnosis**:
  1. Extract raw text: `pdf.pages[0].extract_text()`
  2. Inspect character codes: `for char in text: print(f"{char} = U+{ord(char):04X}")`
  3. Look for Private Use Area (U+E000-U+F8FF) patterns
- **Solution**:
  1. Create character mapping dictionary (reverse-engineer from PDF samples)
  2. Apply cleaning function to all text before parsing
  3. Use raw strings (`r"""`) in docstrings to avoid Python Unicode escape issues
- **Example**: See `tools/parsers/boursobank/per_v2025.py` for complete implementation

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
