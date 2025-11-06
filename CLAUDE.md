# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Patrimoine Analyzer is an automated wealth report generator that transforms source files (CSV, PDF, Markdown) into professional HTML reports with deep analysis, web research, and risk assessment. The system follows a strict 3-stage pipeline architecture with no user interaction during execution.

**Note**: Since October 2025, PEA and PEA-PME files from Crédit Agricole use PDF format instead of CSV.

## Core Commands

```bash
# Generate full report (main workflow)
python main.py

# OR, if using Claude Code:
/report

# Test individual components
python tests/test_normalizer.py   # Test stage 1: Data normalization
python tests/test_analyzer.py     # Test stage 2: Analysis & web research
python tests/test_generator.py    # Test stage 3: HTML generation
python tests/test_web_research.py # Test Brave Search API integration

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Then edit .env and add your BRAVE_API_KEY
```

## Architecture: 3-Stage Pipeline

The system transforms data through three independent stages, each with strict input/output contracts:

```
sources/patrimoine.md + CSV/PDF files
    ↓
[Stage 1: Normalizer] → generated/patrimoine_input.json
    ↓
[Stage 2: Analyzer] → generated/patrimoine_analysis.json
    ↓
[Stage 3: Generator] → generated/rapport_YYYYMMDD_HHMMSS.html
```

### Stage 1: Normalizer (`tools/normalizer.py`)

**Purpose**: Parse heterogeneous source files and output normalized JSON.

**Key responsibilities**:
- Parse `sources/patrimoine.md` as entry point
- Extract data from referenced CSV files (via `tools/utils/file_parser.py`)
- Extract data from PDF files using `pdfplumber` (bank statements, insurance contracts)
- Handle French number formats (comma as decimal separator)
- Calculate investor age from birthdate
- Output: `generated/patrimoine_input.json` with structure:
  ```json
  {
    "profil": {...},      // Investor profile
    "patrimoine": {...},  // Financial, real estate, crypto assets
    "sources_files": [...] // List of parsed files
  }
  ```

**Critical parsing logic**:
- AV (assurance-vie) PDF tables: 2-line format per fund (line 0: name + valorization, line 1: breakdown)
- PEA/PEA-PME PDF tables: Multi-page web format (see **PEA/PEA-PME PDF parsing** section below)
- CSV columns mapped flexibly: "valeur totale", "montant en eur", "ticker/isin" etc. (used for CTO and other accounts)
- French numbers converted: `6804,08` → `6804.08`

### Stage 2: Analyzer (`tools/analyzer.py`)

**Purpose**: Deep analysis with web research, risk assessment, recommendations, stress tests.

**Key responsibilities**:
- Répartition analysis (concentration by institution, jurisdiction, asset class)
  - **Automatic aggregation**: Multiple assets of same type in same institution are merged into one line (e.g., all AV UC funds → single "Actions AV - UC" line)
- **7 risk categories** via `tools/utils/risk_analyzer.py`:
  1. Concentration (>30% = high, >50% = critical)
  2. Regulatory (Loi Sapin 2, deposit guarantee €100k, PEA caps)
  3. Fiscal (PFU, AV taxation, IFI)
  4. Market (volatility, correlations)
  5. Liquidity (locked assets: AV, PER, real estate)
  6. Political (instability, nationalization)
  7. **Currency** (USD exposure, crypto, foreign real estate)
- Web research via Brave Search API (`tools/utils/web_research.py`):
  - Rate limiting: 1.1-1.5s between requests
  - Typically 15-18 searches per analysis
  - Sources cited and stored per risk
- Recommendations via `tools/utils/recommendations.py`:
  - Scoring: `(criticité × 0.4) + (impact × 0.3) + (facilité × 0.3)`
- Stress tests via `tools/utils/stress_tester.py`:
  - 5 scenarios: banking crisis, market crash, job loss, inflation, real estate crisis
- **Portfolio optimization** via `tools/utils/portfolio_optimizer.py`:
  - **Configuration**: All parameters externalized in `config/analysis.yaml`
  - **4 investor profiles**: default, dynamique (dynamic), equilibre (balanced), prudent
    - Active profile selected via `config.yaml` → `analysis.active_profile`
    - Each profile has different return/volatility assumptions based on investment horizon and risk tolerance
  - Markowitz efficient frontier using statistical estimates by asset class
  - Sharpe ratio calculation for current and optimal portfolios
  - Generates base64 PNG chart with both efficient and inefficient frontiers
  - Method: Statistical averages (no external API, no real-time market data)
  - Only includes liquid risky assets (stocks, crypto, gold) - excludes savings accounts and real estate
  - All parameters configurable: asset statistics, correlations, optimization params, chart colors/sizes
- **Analysis scores** via `tools/analyzer.py`:
  - **5 scores** (0-10): diversification, resilience, liquidity, fiscal, growth
  - **All scores enriched** with labels and detailed breakdowns:
    - **Diversification (v1.1)**: Returns dict with score, label, institutional/jurisdictional components, bonuses
    - **Resilience (v1.0)**: Returns dict with score, label
    - **Liquidité (v2.0)**: Returns dict with score, label, ratio liquidités/cible, adaptation profil (9-15 mois)
    - **Fiscalité (v2.0)**: Returns dict with score, label, enveloppes fiscales (PEA/CTO/AV/PER), bonus/pénalités
    - **Croissance (v2.1)**: Returns dict with score, label, exposition actions + cryptos pondérées 50% (%), adaptation profil (30-85%)
  - All scoring parameters externalized in `config/analysis.yaml`
  - Scores vary by active profile (e.g., growth optimal ranges differ for prudent vs. dynamique profiles)
- **Important**: Pass through `profil` from input to output (added at line 44 of analyzer.py)

**Output structure**:
```json
{
  "profil": {...},              // Passed through from input
  "synthese": {
    "patrimoine_total": 479949,
    "score_global": 7.6,
    "scores_details": {"diversification": 10, "resilience": 5, "liquidite": 10, "fiscalite": 9, "croissance": 4},
    "diversification_details": {"score": 10, "label": "Excellente diversification", "details": {...}},
    "resilience_details": {"score": 5, "label": "Patrimoine vulnérable"},
    "liquidity_details": {"score": 10, "label": "Excellente liquidité", "details": {...}},
    "fiscal_details": {"score": 9, "label": "Optimisation fiscale excellente", "details": {...}},
    "growth_details": {"score": 4, "label": "Potentiel de croissance limité", "details": {...}}
  },
  "repartition": {...},         // Distribution analysis
  "risques": {                  // Risks by severity
    "critiques": [...],
    "eleves": [...],
    "moyens": [...],
    "faibles": [...]
  },
  "recommandations": {...},
  "stress_tests": [...],
  "optimisation_portefeuille": {  // Markowitz optimization
    "portefeuille_actuel": {...}, // Current portfolio (return, volatility, Sharpe)
    "portefeuille_optimal": {...}, // Optimal portfolio
    "frontiere_efficiente": {...}, // Efficient frontier data
    "graphique_base64": "..."      // PNG chart in base64
  },
  "recherches_web": [...]       // All web searches with sources
}
```

### Stage 3: Generator (`tools/generator.py`)

**Purpose**: Inject analysis data into HTML template using BeautifulSoup and generate standalone HTML file with inline CSS.

**Injection system**:
1. **CSS inlining**: Automatically incorporates `templates/rapport.css` into HTML
   - Replaces `<link rel="stylesheet" href="rapport.css">` with `<style>...</style>`
   - Generated HTML is completely **standalone** (no external CSS dependency)
   - Can be shared, archived, or moved without breaking styling

2. **Simple fields** (`data-field` attributes): Direct text replacement
   ```html
   <div data-field="patrimoine_total">470 354 €</div>
   <!-- Gets replaced with actual value from JSON -->
   ```

3. **Repeated rows** (`data-repeat` attributes): Clone and populate
   ```html
   <tr data-repeat="etablissement">
     <td data-field="etablissement_name">CA</td>
     <td data-field="etablissement_montant">100000 €</td>
   </tr>
   <!-- Template row is cloned for each establishment -->
   ```

4. **Cover page structure** (3 levels):
   - `title`: Static "Rapport Patrimonial"
   - `subtitle`: "Analyse approfondie • Recommandations • Synthèse — {date}"
   - `subtitle_profile`: Dynamic investor profile synthesis
     - Format: "Prénom NOM • age • situation • profil • profession • revenu"
     - Generated by `_synthesize_investor_profile()` using **active_profile from config/analysis.yaml**
     - **IMPORTANT**: Profil shown is determined by `config.analysis.active_profile`, NOT by `patrimoine.md`
     - Profile mapping: `dynamique` → "Dynamique", `equilibre` → "Équilibré", `prudent` → "Prudent", `default` → "Équilibré"

4. **Chart data injection**: Radar chart scores replaced in JavaScript via regex

5. **Conditional elements** (`data-conditional` attributes): Elements that can be removed if conditions aren't met
   ```html
   <div class="alert" data-conditional="concentration_alert">
     <span data-field="concentration_alert_content"></span>
   </div>
   <!-- Entire div removed if _analyze_concentration_alert() returns None -->
   ```
   - **Multiple alerts**: Each alert displayed on separate line with `<div style="margin-bottom: 8px;">` wrapper
   - Improves visual separation and readability when multiple concentration issues detected

6. **Dynamic CSS badges**: Badge severity classes applied dynamically based on risk level
   - Template badges have NO hardcoded severity classes (only `class="badge"`)
   - Generator applies: `crit` (critical), `high` (elevated), `mid` (medium), `low` (normal)
   - Applies to: establishment risk badges, stress test badges

7. **Two-line structure for asset classes table**: The "Classe d'actifs" column displays data on two lines
   ```html
   <td>
     <span class="cell-primary" data-field="class_name_primary">Obligations</span>
     <span class="cell-secondary" data-field="class_name_secondary">AV - Fonds Euro</span>
   </td>
   ```
   - Line 1 (`class_name_primary`): Asset type (Obligations, Actions, Liquidités, etc.)
   - Line 2 (`class_name_secondary`): Account detail (PEA, AV - Fonds Euro, CTO, etc.)
   - Regex parsing extracts establishment name and detail from `"Établissement (Détail)"` format
   - Separate column shows establishment name via `class_etablissement` field

**Critical methods**:
- `_inline_css()`: Incorporates CSS from `templates/rapport.css` into `<style>` tag, making HTML standalone
- `_inject_simple_fields()`: Maps JSON paths to `data-field` attributes; handles conditional elements and HTML injection
- `_inject_repeated_rows()`: Handles establishments, asset classes, risks, recommendations, stress tests with dynamic badge classes
- `_inject_classes_actifs()`: Special handling for asset classes table with two-line structure and establishment parsing
- `_inject_chart_data()`: Injects scores into Chart.js radar chart
- `_synthesize_investor_profile()`: Builds cover page profile summary using active_profile from config/analysis.yaml (NOT patrimoine.md)
- `_analyze_concentration_alert()`: Analyzes concentration data and generates alert message(s) or returns None; multiple alerts wrapped in separate divs
- `_get_badge_class()`: Maps risk level to CSS class (Critique→crit, Élevé→mid, etc.)
- `_get_stress_severity_class()`: Maps stress test severity to CSS class

## Configuration

All settings in `config/config.yaml`:
- **Risk thresholds**: Concentration, liquidity limits
- **Web research**: Max queries (50), timeout (30s), retry count (3)
- **Paths**: sources/, templates/, generated/, logs/
- **File naming**: Output prefix, timestamp format
- **Analysis**: References `analysis.yaml`, selects active profile (default/dynamique/equilibre/prudent)

Analysis and optimization settings in `config/analysis.yaml`:
- **Investor profiles**: 4 predefined profiles with different return/volatility assumptions
- **Asset statistics**: Returns and volatilities for 12 asset classes
- **Correlations**: Correlation matrix between asset classes
- **Benchmarks**: Target allocation ranges by asset class and profile
  - Format: `{min: %, target: %, max: %}` for each asset class
  - Example: Actions (dynamique) → `min: 70, target: 77.5, max: 85`
  - Used for benchmark gap calculation in reports (see `tools/utils/benchmark_gap.py`)
- **Score calculation**: Parameters for 5 scores (diversification, resilience, liquidity, fiscal, growth)
  - **Diversification score (v1.1)**: Weighted components (60% institutional + 40% jurisdictional) + intra-portfolio bonuses
    - 3 bonuses: ≥5 asset classes (+1.0), ≥10 positions (+0.5), >15% international (+0.5)
    - 5 quality labels: "Excellente" (9-10), "Bonne" (7-9), "Modérée" (5-7), "Forte" (3-5), "Critique" (0-3)
    - Returns enriched dict with score, label, and detailed breakdown (see `analyzer.py:488-606`)
  - **Growth score (v2.1)**: Exposure calculation with partial crypto weighting
    - Actions/UC/PER: 100% (productive assets with cash flows)
    - Cryptomonnaies: 50% (alternative growth, high volatility, no productive flows)
    - Rationale: Recognizes long-term growth potential while accounting for speculative nature
    - See `update/calculate_growth_score_(crypto).md` for methodology details
- **Account classification**: Keywords and mapping to identify account types
- **Risk justifications**: Text for risk level explanations
- **Technical parameters**: Iterations, constraints, interpretation thresholds
- **Chart parameters**: Colors, sizes, DPI

## Environment Variables

Required in `.env`:
```bash
BRAVE_API_KEY=your-api-key-here
```

Get free API key at: https://api.search.brave.com/app/dashboard

## Key Design Principles

1. **No file modification**: Tools never modify source files or templates
2. **Timestamped outputs**: All reports saved as `rapport_YYYYMMDD_HHMMSS.html`
3. **Zero interaction**: `python main.py` runs completely autonomously
4. **Template injection**: HTML template uses `data-field` and `data-repeat` attributes for safe injection
5. **Web research integration**: All risk analyses backed by web sources (15-18 API calls per run)
6. **Investor profile passthrough**: `profil` data flows from normalizer → analyzer → generator unchanged

## Modifying the Template

The HTML template (`templates/rapport_template.html`) can be freely customized:

**Rules**:
- Preserve all `data-field="fieldname"` attributes for simple injection
- Preserve all `data-repeat="typename"` attributes for repeated elements
- **NEW**: Use `data-conditional="identifier"` for elements that may be removed (e.g., alerts)
- **NEW**: Badges must have ONLY `class="badge"` - NO hardcoded severity classes (`high`, `mid`, `low`, `crit`)
- Available fields documented in PRD.md section 3.3.5
- CSS variables can be adjusted (lines 17-29)
- Chart.js radar chart requires pattern: `data: [8, 7.5, 6.5, 7, 8.5]` for injection

**Badge CSS classes** (PRD.md section 16.4):
- `.badge.crit`: Critical (red-dark background, white text, bold)
- `.badge.high`: High (red-light background, red-dark text)
- `.badge.mid`: Medium (gold-light background, gold-dark text)
- `.badge.low`: Low/Normal (green-light background, green-dark text)

**Enriched scores sections** (lines ~489-817 in template):
- **5 scores** have detailed `<details>` collapsible sections with labels and badges:
  - **Diversification** (v1.1): Shows components, bonuses, metrics (nb classes, positions, % international)
  - **Resilience** (v1.0): Shows stress tests impact and risk count
  - **Liquidité** (v2.0): Shows liquidités actuelles/cible, ratio, target months by profile, overliquidity alert
  - **Fiscalité** (v2.0): Shows enveloppes (PEA, CTO, AV, PER, cryptos), optimizations, bonus/penalties lists
  - **Croissance** (v2.1): Shows exposition actions + cryptos pondérées 50%, %, profile, optimal range, contextualized interpretation
- All sections follow same design pattern: badge + collapsible details + metrics + interpretation
- Generator automatically applies CSS classes to badges based on label text
- Key generator functions:
  - `_get_diversification_badge_class()`: Maps diversification labels to CSS classes
  - `_get_resilience_badge_class()`: Maps resilience labels to CSS classes
  - `_get_liquidity_badge_class()`: Maps liquidity labels to CSS classes
  - `_get_fiscal_badge_class()`: Maps fiscal labels to CSS classes
  - `_get_growth_badge_class()`: Maps growth labels to CSS classes
  - `_format_diversification_bonus_details()`: Formats bonus HTML list
  - `_format_fiscal_bonuses()`: Formats fiscal bonuses HTML list
  - `_format_fiscal_penalties()`: Formats fiscal penalties HTML list
  - `_format_overliquidity_message()`: Conditional liquidity alert message
  - `_format_growth_optimal_range()`: Formats "X-Y%" range string

**Asset classes table - Two-line structure**:
- The "Classe d'actifs" column uses two spans for displaying data on separate lines
- Template structure:
  ```html
  <td>
    <span class="cell-primary" data-field="class_name_primary">…</span>
    <span class="cell-secondary" data-field="class_name_secondary">…</span>
  </td>
  ```
- `class_name_primary`: Asset type (filled with `type_actif` from JSON)
- `class_name_secondary`: Account detail (parsed from `etablissement` field)
- Separate column `class_etablissement` for establishment name
- Generator uses regex `r'^(.+?)\s*\((.+)\)$'` to parse "Establishment (Detail)" format
- **"Écart benchmark" column** (lines 158, 180-183 in template):
  - `class_gap_message`: Descriptive message from `benchmark_gap.message`
  - `class_gap_badge`: Optional badge (only shown if `niveau` is `attention` or `alerte`)
  - Badge classes: `.crit` (strong deviation), `.high` (alert), `.mid` (watch)
  - Generator logic in `_inject_classes_actifs()` (lines 306-335)

**Cover page customization**:
- `subtitle-profile` uses special CSS: lowercase, small-caps, italic (lines 118-131)
- Three-level hierarchy: title → subtitle → subtitle-profile

## Common Development Scenarios

**Adding a new risk** (see "Risk Detection System v2.0" section below for details):
- **Option 1**: Add contextual search in `config/risks.yaml` (no code, dynamic detection via web)
- **Option 2**: Add structural risk method in `risk_analyzer.py` (requires code)
- **Option 3**: Modify existing risk thresholds in `config/risks.yaml`

**Adding a new template field**:
1. Add `data-field="newfield"` in template HTML
2. Add mapping in `generator.py` `_inject_simple_fields()` around line 66-83
3. Either use lambda function or JSON path: `"newfield": ("json.path.here", formatter_function)`

**Modifying web research**:
- Rate limiting in `web_research.py`: `time.sleep(random.uniform(1.1, 1.5))`
- Search queries returned with: `titre, url, extrait, date`
- Sources displayed in collapsible `<details>` sections in HTML

**Customizing analysis and portfolio optimization**:
- **Change active profile**: Edit `config.yaml` → `analysis.active_profile` (default/dynamique/equilibre/prudent)
- **Adjust asset statistics**: Edit `config/analysis.yaml` → `profiles.[profile_name].asset_statistics`
- **Modify correlations**: Edit `config/analysis.yaml` → `profiles.[profile_name].correlations`
- **Adjust benchmarks**: Edit `config/analysis.yaml` → `benchmarks.[profile_name]` (target allocation ranges with median targets)
  - Each class has `{min: X, target: Y, max: Z}` format
  - Affects benchmark gap calculation and report display
- **Customize scores**: Edit `config/analysis.yaml` → `scores.[score_name]` (parameters for diversification, resilience, liquidity, fiscal, growth)
- **Modify account classification**: Edit `config/analysis.yaml` → `account_classification` (keywords for account types)
- **Create new profile**: Duplicate existing profile in `analysis.yaml` and customize all parameters
- **Adjust chart appearance**: Edit `technical.charting` section (colors, sizes, DPI)
- **Change interpretation thresholds**: Edit `interpretation_thresholds` section
- All changes take effect immediately on next run (no code modification required)

**Testing changes**:
- Each stage can be tested independently via `tests/test_*.py`
- Generated JSON files preserved in `generated/` for debugging
- Logs saved to `logs/rapport_YYYYMMDD_HHMMSS.log`

## Risk Detection System v2.0 (Dynamic & Configurable)

Starting with v2.0 (November 2025), the risk detection system is **hybrid and dynamic**:

### Architecture

The system operates on **3 levels**:

1. **Level 1: Structural Risks** (legacy methods, always active)
   - Concentration, regulatory, fiscal, market, liquidity, political, currency risks
   - Detection logic coded in `risk_analyzer.py` methods
   - Fully backward compatible with v1.0

2. **Level 2: Contextual Risks** (dynamic web detection, optional)
   - Automatic detection of emerging risks via web research
   - Searches on recent economic/political news, regulatory changes, market alerts
   - Configurable via `config/risks.yaml` → `contextual_searches`
   - Can be enabled/disabled via `risk_settings.enable_contextual_detection`

3. **Level 3: Future** (LLM-based analysis)
   - Reserved for future enhancement
   - Would use LLM to analyze web results and classify risks automatically

### Configuration File: `config/risks.yaml`

This file externalizes all risk detection rules and contextual searches.

**Structure**:
```yaml
risk_settings:
  enable_contextual_detection: true  # Enable/disable dynamic detection
  max_contextual_risks_per_search: 3 # Max contextual risks per search category
  version: "2.0.0"

structural_risks:
  concentration_etablissement_critique:
    enabled: true
    category: "Concentration"
    detection:
      type: "threshold"
      metric: "establishment_percentage"
      threshold: 50
    risk_properties:
      niveau: "Critique"
      titre_template: "Concentration excessive - {establishment_name}"
    web_research:
      enabled: true
      queries: [...]

contextual_searches:
  actualite_economique_france:
    enabled: true
    priority: "high"
    queries:
      - "nouvelles lois économiques France 2025 épargne"
      - "réformes fiscales France 2025 patrimoine"
    relevance_threshold: 0.7
```

### How It Works

**Structural risks** (level 1):
- Legacy methods in `risk_analyzer.py` run first
- Execute the 7 standard risk category checks
- Rules can be referenced in YAML but detection logic remains in code

**Contextual risks** (level 2):
- Only execute if `enable_contextual_detection: true`
- For each enabled search in `contextual_searches`:
  1. Execute web queries via Brave Search API
  2. Analyze results and determine relevance
  3. If ≥2 sources confirm, generate a contextual risk
  4. Attach web sources to the risk
- Generated risks have category suffix `" - Contexte"` for identification
- Examples:
  - "Évolution réglementaire économique France" (category: Réglementaire - Contexte)
  - "Risques système bancaire français" (category: Concentration - Contexte)
  - "Volatilité accrue des marchés" (category: Marché - Contexte)

### Adding/Modifying Risks

**Option 1: Add a contextual search** (no code changes)
```yaml
# In config/risks.yaml → contextual_searches
nouvelle_reforme_taxation:
  enabled: true
  priority: "high"
  description: "Détecte les nouvelles réformes de taxation"
  queries:
    - "nouvelle taxe patrimoine France 2026"
    - "réforme taxation plus-values immobilières"
  analysis_context: "Identifier nouvelles taxes sur le patrimoine"
  relevance_threshold: 0.7
```

Then add mapping in `risk_analyzer.py` → `_get_contextual_risk_mapping()`:
```python
"nouvelle_reforme_taxation": {
    "titre": "Nouvelle réforme de taxation",
    "description": "...",
    "niveau": "Moyen",
    "categorie": "Fiscal - Contexte",
    ...
}
```

**Option 2: Add a structural risk** (requires code)
1. Add detection logic in `tools/utils/risk_analyzer.py`
2. Call new method in `analyze()` around line 123
3. Return risk dict with: `id, titre, description, exposition_montant, exposition_pct, probabilite, impact, niveau, categorie, sources_web`
4. Risk automatically appears in HTML (generator shows all risk levels, limit 10)

**Option 3: Modify existing structural risk thresholds**
- Edit `config/risks.yaml` → `structural_risks.[risk_id].detection.threshold`
- Example: Change concentration critical threshold from 50% to 60%
- Note: Detection logic must be updated in code to use YAML thresholds (future enhancement)

### Activating/Deactivating Features

**Enable contextual detection**:
```yaml
# config/risks.yaml
risk_settings:
  enable_contextual_detection: true  # Set to false to disable
```

**Disable specific contextual search**:
```yaml
# config/risks.yaml → contextual_searches
regulation_crypto:
  enabled: false  # Skip this search
```

**Disable specific structural risk**:
```yaml
# config/risks.yaml → structural_risks
plafond_pea:
  enabled: false  # Skip this risk check
```
Note: Structural risk enable/disable requires code modification in v2.0 (reads legacy methods)

### Maintenance

**Update frequency**: Quarterly recommended (see `metadata.recommended_update_frequency`)

**What to update**:
- Contextual search queries to reflect current concerns
- Risk thresholds based on regulatory changes
- New contextual searches for emerging risk categories
- Remove obsolete searches (e.g., past crises)

**Version control**:
- `risk_settings.version`: Semantic versioning (2.0.0)
- `risk_settings.last_updated`: Date of last modification
- `metadata.changelog`: Track all changes

### Performance Impact

- **Contextual detection disabled**: No performance impact vs v1.0
- **Contextual detection enabled**:
  - Additional 6-12 web searches (depending on enabled searches)
  - ~10-20 seconds added to analysis time
  - Rate limiting: 1.1-1.5s between requests (Brave API compliance)

### Example Output

With contextual detection enabled, the report may show:
- Traditional risks: "Concentration excessive - Crédit Agricole" (Critique)
- Contextual risks: "Évolution réglementaire économique France" (Moyen, category: Réglementaire - Contexte)
- Each contextual risk includes 2-3 web sources for validation

## Important Implementation Details

**Account type classification** (`analyzer.py` lines 180-245):
- Assets are classified by type and institution during `_analyze_repartition()`
- **Automatic aggregation** (lines 297-312): Assets with same `(type_actif, etablissement)` key are merged and amounts summed
  - Example: 10 UC funds in AV → single aggregated line "Actions - Crédit Agricole (AV - UC)"
- **Liquidités** (Savings): Livret A, LDD, **PEL** (Plan d'Épargne Logement), compte de dépôts
  - Note: PEL is classified as "Liquidités" (regulated savings), NOT "Obligations"
  - Rationale: PEL is a state-guaranteed savings product, not a tradable bond
- **Actions** (Equities): PEA, PEA-PME, CTO, PER, Parts Sociales, Assurance-vie (UC)
- **Obligations** (Bonds): Spiko (T-Bonds), specific bond funds in AV
- **Cryptomonnaies**: Crypto platforms and self-custody wallets
- **Métaux précieux**: Physical gold
- **Immobilier**: SCPI, real estate

**Benchmark gap calculation** (`tools/utils/benchmark_gap.py`):
- Compares actual asset allocation to target benchmarks by investor profile
- Each asset class enriched with `benchmark_gap` object containing:
  - `ecart_pct`: Difference in percentage points from target median
  - `ecart_borne`: Distance from min/max bounds (0 if within range)
  - `status`: One of 5 levels:
    - `dans_la_cible`: Within 2pts of target (normal)
    - `sous_pondere_modere` / `sur_pondere_modere`: Out of range < 10pts (attention)
    - `sous_pondere_fort` / `sur_pondere_fort`: Out of range ≥ 10pts (alert)
  - `niveau`: `normal`, `attention`, or `alerte`
  - `message`: Descriptive text for report display
- Displayed in HTML report as new "Écart benchmark" column with optional colored badges
- Activated automatically in `analyzer.py` line 386-387 during repartition analysis

**Enriched diversification score calculation (v1.1)** (`analyzer.py:488-606`):
- Returns dict instead of simple float, with score, label, and detailed breakdown
- **Formula**: `Score = (Institutional × 60%) + (Jurisdictional × 40%) + Bonuses`
- **Institutional component** (60%):
  - Base 10, penalties for concentration: >70% (-3.0), >50% (-2.0), >30% (-0.5)
- **Jurisdictional component** (40%):
  - Base 10, penalty for concentration: >85% (-2.0)
- **3 intra-portfolio bonuses** (cumulative):
  - ≥5 distinct asset classes: +1.0
  - ≥10 individual positions/accounts: +0.5
  - >15% international exposure: +0.5
- **5 quality labels** with colored badges:
  - 9-10: "Excellente diversification" (green `.low`)
  - 7-9: "Bonne diversification" (green `.low`)
  - 5-7: "Concentration modérée" (orange `.mid`)
  - 3-5: "Forte concentration" (red light `.high`)
  - 0-3: "Concentration critique" (red dark `.crit`)
- **HTML display**:
  - Score shown in radar chart + badge with label
  - Collapsible `<details>` section with full breakdown (lines 478-570 in template)
  - Shows both component scores, weighted score, bonus details, and metrics
- **Generator injection**:
  - 10 new fields in `_inject_simple_fields()` (lines 97-106)
  - `_format_diversification_bonus_details()` formats HTML list of bonuses (lines 610-644)
  - `_get_diversification_badge_class()` maps labels to CSS classes (lines 711-729)
- All parameters configurable in `config/analysis.yaml` → `scores.diversification`

**Currency risk detection** (lines 464-545 in `risk_analyzer.py`):
- Detects USD accounts (Spiko T-Bonds)
- Detects crypto exposure
- Detects foreign real estate
- Threshold: 3% of total wealth triggers web research

**AV PDF parsing** (lines 716-776 in `normalizer.py`):
- Modern format: 2-line tables per fund
- Line 0: Fund name + "Valorisation : XXX €"
- Line 1: Breakdown + gains
- Regex: `r"Valorisation\s*:\s*([\d\s,]+)\s*€"`

**PEA/PEA-PME PDF parsing** (Crédit Agricole web format, lines 807-923 in `normalizer.py`):
- Detection: "MANDAT PEA" or "compte PEA" + "portefeuille" (before "PER" to avoid false positives)
- **Cash balance extraction** (lines 807-850, `_extract_solde_especes()`):
  - Extracted from "Ma valorisation totale" line format: "X € = Y € + Z € = ..."
  - Example: "6 133,22 € = 970,14 € + **5 163,08 €**" → cash = 5 163,08 €
  - Uses 3rd amount in valorisation formula (not "Solde disponible" which may differ due to pending operations)
  - Fallback: "Solde disponible" line if valorisation line parsing fails
  - Result stored in `compte["solde_especes"]`
- **Position parsing** (lines 852-923):
  - Multi-page structure with different column layouts:
    - **Page 1**: 10 columns (0-1 empty, data in 2-9), offset=2
    - **Page 2+**: 9 columns (data in 0-7), offset=0, no header repetition
  - Column structure (without offset): [Valeur, Quantité, Cours, Variation(1J), Prix de revient, Valorisation, +/- Value latente]
  - Valeur cell format: "NOM ACTION\nISIN CODE" (2 lines)
  - Valorisation column: index 7 (page 1 with offset) or 6 (page 2+ without offset)
  - ISIN extraction: Split "FR0000120404 AC" → keep first part
  - `_parse_amount()` updated to handle € symbol and spaces (lines 586-609)
  - Header detection persists across pages (header_found flag)
- **Total calculation** (lines 933-940 in `_calculate_totals()`):
  - `compte["montant"] = sum(positions) + solde_especes`
  - Ensures complete account valuation matching PDF "Ma valorisation totale"

**Recommendation scoring** (lines 197-212 in `recommendations.py`):
- Formula: `Score = (criticité × 0.4) + (impact × 0.3) + (facilité × 0.3)`
- Sorted by score descending
- Top 5 marked as "prioritaires"

## Documentation

- `PRD.md`: Complete technical specification (900+ lines)
- `README.md`: User-facing documentation
- All code follows PRD section references in comments
