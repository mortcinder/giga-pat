# config/ - Configuration Guide

This file provides detailed guidance for working with configuration files in the Patrimoine Analyzer.

## Configuration Files Overview

### `config.yaml` - Main Configuration

**Purpose**: Global settings, paths, active profile selection

**Key Sections**:
```yaml
paths:
  sources: sources/
  templates: templates/
  generated: generated/
  logs: logs/

analysis:
  active_profile: "equilibre"  # dynamique, equilibre, prudent, default

web_research:
  enabled: true
  rate_limit_seconds: 1.1  # Brave API: 1 req/sec

risk_thresholds:
  concentration_custodian: 0.40  # 40% in one custodian triggers alert
  concentration_class: 0.70      # 70% in one asset class triggers alert
  liquidity_minimum: 0.15        # 15% minimum liquid assets
```

**Common Changes**:
- Switch profile: Change `analysis.active_profile`
- Disable web research: Set `web_research.enabled: false`
- Adjust risk thresholds: Modify values under `risk_thresholds`

### `analysis.yaml` - Analysis Parameters

**Purpose**: Investor profiles, asset statistics, correlations, benchmarks, score parameters

**Structure**:
```yaml
profiles:
  dynamique:
    return_assumptions: {...}
    volatility_assumptions: {...}
  equilibre:
    return_assumptions: {...}
    volatility_assumptions: {...}
  prudent:
    return_assumptions: {...}
    volatility_assumptions: {...}

asset_classes:
  Actions: {expected_return: 0.08, volatility: 0.18}
  Obligations: {expected_return: 0.03, volatility: 0.05}
  # ... 12 asset classes total

correlation_matrix: [...]  # 12x12 matrix

benchmarks:
  dynamique: {...}
  equilibre: {...}
  prudent: {...}

scores:
  diversification: {...}
  resilience: {...}
  liquidity: {...}
  fiscal: {...}
  growth: {...}

classification_keywords: {...}
```

**See sections below for detailed explanations of each section.**

### `risks.yaml` - Risk Configuration

**Purpose**: Risk detection settings, contextual searches

**Structure**:
```yaml
risk_settings:
  enable_contextual_detection: true

structural_risks:
  concentration:
    custodian_threshold: 0.40
    asset_class_threshold: 0.70
  liquidity:
    minimum_threshold: 0.15
  currency:
    foreign_exposure_threshold: 0.20
  regulatory:
    sapin_2_threshold: 0.30

contextual_searches:
  regulatory_risk_france:
    enabled: true
    queries:
      - "réglementation épargne France 2025"
      - "loi sapin 2 assurance vie actualité"
    relevance_threshold: 0.7
  # ... more contextual searches
```

**See "Risk Detection System" section below for details.**

### `manifest.schema.json` - Validation Schema

**Purpose**: JSON Schema validation for v2.1 manifest structure

**Usage**: Automatic validation during normalization (Stage 1)

**Key Definitions**:
- `patrimoine.comptes_titres[]`: Parsable securities accounts
- `patrimoine.liquidites[]`: Cash accounts
- `patrimoine.obligations[]`: Bonds (multi-currency)
- `patrimoine.crypto[]`: Cryptocurrencies (all custody types)
- `patrimoine.metaux_precieux[]`: Precious metals
- `patrimoine.immobilier[]`: Real estate

**Validation**: All fields documented with types, required flags, descriptions

## Investor Profiles

**4 Profiles Available**:

### 1. Dynamique (Aggressive Growth)
- **Target Return**: 8%
- **Volatility**: 15%
- **Asset Mix**: Heavy equities, minimal bonds
- **Benchmark**: 70% Actions, 5% Obligations, 10% Crypto, 5% Immobilier

### 2. Equilibre (Balanced)
- **Target Return**: 6%
- **Volatility**: 10%
- **Asset Mix**: Balanced equities/bonds
- **Benchmark**: 50% Actions, 25% Obligations, 5% Crypto, 10% Immobilier

### 3. Prudent (Conservative)
- **Target Return**: 4%
- **Volatility**: 6%
- **Asset Mix**: Heavy bonds/cash, minimal equities
- **Benchmark**: 25% Actions, 45% Obligations, 20% Liquidités, 5% Immobilier

### 4. Default (Fallback)
- **Target Return**: 5%
- **Volatility**: 8%
- **Asset Mix**: Generic balanced allocation

**Selecting Profile**:
- Edit `config.yaml` → `analysis.active_profile`
- Profile flows through all 3 stages unchanged
- Impacts benchmarks, recommendations, stress tests

**Customizing Profile**:
- Edit `config/analysis.yaml` → `profiles.[name]`
- Modify `return_assumptions` per asset class
- Adjust `volatility_assumptions`
- Update benchmarks to match investment strategy

## Asset Statistics (12 Classes)

**Configured in** `analysis.yaml` → `asset_classes`

**Available Classes**:
1. **Actions**: Expected return 8%, volatility 18%
2. **Obligations**: Expected return 3%, volatility 5%
3. **Liquidités**: Expected return 1%, volatility 1%
4. **Immobilier**: Expected return 5%, volatility 12%
5. **Cryptomonnaies**: Expected return 15%, volatility 60%
6. **Métaux précieux**: Expected return 4%, volatility 15%
7. **Matières premières**: Expected return 6%, volatility 25%
8. **Private equity**: Expected return 12%, volatility 30%
9. **Hedge funds**: Expected return 7%, volatility 10%
10. **Infrastructure**: Expected return 6%, volatility 8%
11. **Forêts et terres agricoles**: Expected return 5%, volatility 7%
12. **Art et collections**: Expected return 6%, volatility 20%

**Parameters**:
- `expected_return`: Annual expected return (0-1 scale)
- `volatility`: Standard deviation of returns (0-1 scale)

**Usage**:
- Portfolio optimization (Markowitz efficient frontier)
- Sharpe ratio calculations
- Stress testing scenarios
- Recommendation scoring

**Customization**:
- Update return/volatility based on research
- Add new asset classes (requires code changes in analyzer.py)

## Correlation Matrix

**Configured in** `analysis.yaml` → `correlation_matrix`

**Structure**: 12x12 symmetric matrix (-1 to +1)

**Example Correlations**:
- Actions ↔ Obligations: -0.2 (slight negative)
- Actions ↔ Crypto: 0.3 (moderate positive)
- Liquidités ↔ All: ~0 (uncorrelated)
- Métaux précieux ↔ Actions: 0.1 (low positive)

**Usage**:
- Portfolio optimization
- Diversification score calculation
- Risk assessment

**Updating**:
- Based on historical data analysis
- Use 10-year rolling correlations
- Update annually or when market regime changes

## Benchmarks (Allocation Targets)

**Configured in** `analysis.yaml` → `benchmarks.[profile]`

**Structure per Profile**:
```yaml
equilibre:
  Actions: {min: 40, target: 50, max: 60}
  Obligations: {min: 20, target: 25, max: 30}
  Liquidités: {min: 5, target: 10, max: 15}
  Immobilier: {min: 5, target: 10, max: 15}
  Cryptomonnaies: {min: 0, target: 5, max: 10}
  # ... other classes
```

**Interpretation**:
- **min**: Below this = "sous-pondéré" (underweight)
- **target**: Optimal allocation
- **max**: Above this = "surpondéré" (overweight)

**Benchmark Gap Status** (5 levels):
1. **dans_la_cible**: Between min and max (green)
2. **sous_pondere_modere**: 0-5% below min (yellow)
3. **sous_pondere_fort**: >5% below min (red)
4. **sur_pondere_modere**: 0-5% above max (yellow)
5. **sur_pondere_fort**: >5% above max (red)

**Usage**:
- Displayed in asset classes table
- Drives allocation recommendations
- Referenced in benchmark gap analysis

**Customization**:
- Adjust ranges based on investment strategy
- Add new asset classes (must sum to 100%)
- Profile-specific targets (dynamique vs prudent)

## Scores (5 Metrics)

**All scores**: 0-10 scale with enriched breakdowns

### 1. Diversification Score v1.1

**Formula**: `(Institutional × 60%) + (Jurisdictional × 40%) + Bonuses`

**Components**:
- **Institutional (60%)**: HHI-based custodian concentration
  - Perfect: 10 custodians equally weighted
  - Acceptable: 5+ custodians
  - Risky: 1-2 custodians
- **Jurisdictional (40%)**: Geographic diversification
  - Excellent: 3+ jurisdictions
  - Good: 2 jurisdictions
  - Poor: 1 jurisdiction only

**Bonuses** (max +2.0):
- ≥5 asset classes: +1.0
- ≥10 positions: +0.5
- >15% international exposure: +0.5

**Labels** (5 levels):
- Excellente (9-10)
- Bonne (7-9)
- Modérée (5-7)
- Forte concentration (3-5)
- Critique (0-3)

**Configuration**: `analysis.yaml` → `scores.diversification`

### 2. Resilience Score

**Formula**: Weighted sum of protective factors

**Components**:
- Liquidity buffers (≥15% liquid)
- Asset class diversification (≥5 classes)
- Hedge positions (bonds, gold, etc.)
- Geographic diversification

**Labels**:
- Excellente (9-10)
- Bonne (7-9)
- Modérée (5-7)
- Faible (3-5)
- Très faible (0-3)

**Configuration**: `analysis.yaml` → `scores.resilience`

### 3. Liquidity Score

**Formula**: Weighted liquidity by asset class

**Liquidity Ratings** (0-10):
- Liquidités: 10 (instant)
- Actions PEA/CTO: 9 (1 day)
- Obligations: 8 (1-3 days)
- AV-UC: 5 (3-10 days)
- AV-Fonds euros: 3 (30+ days due to Sapin 2)
- Immobilier: 2 (months)
- Crypto: 7 (depends on custody type)

**Labels**: Same as resilience (Excellente → Très faible)

**Configuration**: `analysis.yaml` → `scores.liquidity`

### 4. Fiscal Score

**Formula**: Tax efficiency score

**Components**:
- Tax-advantaged accounts (PEA, PER, AV)
- Holding periods (long-term capital gains)
- Tax-efficient asset placement
- Foreign tax exposure

**Labels**: Same as resilience (Excellente → Très faible)

**Configuration**: `analysis.yaml` → `scores.fiscal`

### 5. Growth Score v2.1

**Formula**: Weighted growth potential

**Weights**:
- Actions/UC/PER: 100% (full growth)
- Crypto: 50% (high growth but speculative)
- Immobilier: 70% (moderate growth)
- Obligations: 20% (minimal growth)
- Liquidités: 0% (no growth)

**Rationale**: Recognizes crypto growth potential while accounting for speculation risk

**Labels**: Same as resilience (Excellente → Très faible)

**Configuration**: `analysis.yaml` → `scores.growth`

### Score Configuration Parameters

**Common Parameters** (in `analysis.yaml` → `scores.[score_name]`):
```yaml
diversification:
  weights:
    institutional: 0.6
    jurisdictional: 0.4
  bonuses:
    asset_classes_threshold: 5
    asset_classes_bonus: 1.0
    positions_threshold: 10
    positions_bonus: 0.5
    international_threshold: 0.15
    international_bonus: 0.5
  labels:
    - {min: 9, max: 10, label: "Excellente"}
    - {min: 7, max: 9, label: "Bonne"}
    - {min: 5, max: 7, label: "Modérée"}
    - {min: 3, max: 5, label: "Forte concentration"}
    - {min: 0, max: 3, label: "Critique"}
```

**Customizing Scores**:
- Adjust weights to prioritize different factors
- Modify bonuses to incentivize desired behaviors
- Change label thresholds to recalibrate ratings
- Add new components (requires code changes in analyzer.py)

## Risk Detection System v2.0

**3 Detection Levels**:

### Level 1: Structural Risks (Coded)

**Always Active** - Implemented in `tools/risk_analyzer.py`

**Categories**:
1. **Concentration Risks**:
   - Custodian: >40% in one custodian
   - Asset class: >70% in one class
   - Single position: >30% in one position

2. **Liquidity Risks**:
   - <15% liquid assets
   - >30% illiquid (Sapin 2, real estate)

3. **Currency Risks**:
   - >20% foreign currency exposure
   - No hedging strategy

4. **Regulatory Risks**:
   - >30% exposed to Sapin 2
   - >50% in regulated envelope (AV)

5. **Market Risks**:
   - High volatility portfolio (>15%)
   - Excessive leverage

6. **Political Risks**:
   - >80% single-country exposure
   - Regulatory capture risk

7. **Fiscal Risks**:
   - Inefficient account usage
   - High tax exposure

**Configuration**: Thresholds in `config.yaml` → `risk_thresholds` and `config/risks.yaml` → `structural_risks`

### Level 2: Contextual Risks (Web-Based)

**Optional** - Enable in `risks.yaml` → `enable_contextual_detection: true`

**Implementation**:
- Dynamic web searches via Brave API
- Queries defined in `risks.yaml` → `contextual_searches`
- Relevance scoring (0-1 scale)
- Source tracking for transparency

**Available Contextual Risks**:
- `regulatory_risk_france`: French regulation changes
- `market_volatility_2025`: Current market conditions
- `crypto_regulation`: Crypto regulatory environment
- `real_estate_market`: Real estate trends
- `currency_risks`: FX market volatility

**Adding New Contextual Risk** (No Code Required):

1. **Add to `config/risks.yaml`**:
   ```yaml
   contextual_searches:
     my_new_risk:
       enabled: true
       queries:
         - "search query 1"
         - "search query 2"
       relevance_threshold: 0.7  # 0-1 scale
   ```

2. **Add mapping in `tools/risk_analyzer.py`** → `_get_contextual_risk_mapping()`:
   ```python
   "my_new_risk": {
       "category": "market",  # or regulatory, political, etc.
       "description": "Description of the risk"
   }
   ```

3. **Test**: Run `python main.py` and check `generated/patrimoine_analysis.json`

**Disabling Contextual Risks**:
- Set `enable_contextual_detection: false` in `risks.yaml`
- Or disable individual searches: `my_risk.enabled: false`

### Level 3: LLM-Based Analysis (Reserved)

**Future Enhancement** - Not yet implemented

**Planned Features**:
- Semantic risk detection via LLM
- Natural language risk explanations
- Cross-domain risk correlation analysis

## Classification Keywords

**Configured in** `analysis.yaml` → `classification_keywords`

**Purpose**: Maps account types and keywords to asset classes

**Structure**:
```yaml
classification_keywords:
  Actions:
    - "PEA"
    - "CTO"
    - "PER"
    - "Parts Sociales"
  Liquidités:
    - "Livret A"
    - "LDD"
    - "PEL"
    - "Compte dépôt"
  Obligations:
    - "T-Bond"
    - "Obligations"
  # ... etc.
```

**Usage**:
- Automatic asset classification in Stage 2 (analyzer.py)
- Account type detection
- Asset class aggregation

**Customization**:
- Add new keywords for specific products
- Map new account types to existing classes
- Use regex patterns for flexible matching

## Common Configuration Scenarios

### Changing Active Profile

**Use Case**: Switch from balanced to aggressive strategy

**Steps**:
1. Edit `config/config.yaml`:
   ```yaml
   analysis:
     active_profile: "dynamique"  # was "equilibre"
   ```
2. Run `python main.py`
3. Report will use "dynamique" benchmarks, risk tolerance, recommendations

### Adjusting Risk Thresholds

**Use Case**: You want stricter concentration limits

**Steps**:
1. Edit `config/config.yaml`:
   ```yaml
   risk_thresholds:
     concentration_custodian: 0.30  # was 0.40 (more strict)
     concentration_class: 0.60      # was 0.70 (more strict)
   ```
2. Run `python main.py`
3. More concentration risks will be detected

### Disabling Web Research

**Use Case**: Faster execution, no API key, or testing

**Steps**:
1. Edit `config/config.yaml`:
   ```yaml
   web_research:
     enabled: false
   ```
2. Run `python main.py`
3. Skips 15-18 web searches (saves ~20 seconds)
4. Contextual risks will not be detected

### Customizing Asset Statistics

**Use Case**: Update expected returns based on new research

**Steps**:
1. Edit `config/analysis.yaml` → `asset_classes`:
   ```yaml
   asset_classes:
     Actions:
       expected_return: 0.07  # was 0.08 (more conservative)
       volatility: 0.20        # was 0.18 (higher risk)
   ```
2. Run `python main.py`
3. Portfolio optimization and recommendations will use new assumptions

### Adding Custom Benchmark

**Use Case**: Create a new "très prudent" profile

**Steps**:
1. Edit `config/analysis.yaml` → `profiles`:
   ```yaml
   tres_prudent:
     return_assumptions: {...}
     volatility_assumptions: {...}
   ```
2. Add benchmarks in `benchmarks`:
   ```yaml
   tres_prudent:
     Actions: {min: 5, target: 10, max: 15}
     Obligations: {min: 50, target: 60, max: 70}
     Liquidités: {min: 20, target: 25, max: 30}
   ```
3. Set in `config.yaml`: `active_profile: "tres_prudent"`
4. Run `python main.py`

## Testing Configuration Changes

**Best Practice**: Test incrementally

**Steps**:
1. Make ONE configuration change at a time
2. Run `python main.py`
3. Check output:
   - `generated/patrimoine_analysis.json` for scores, risks, recommendations
   - `generated/rapport_*.html` for visual report
   - `logs/rapport_*.log` for detailed execution log
4. Verify change had expected impact
5. Repeat for next change

**Common Validation Checks**:
- Scores changed as expected?
- New risks detected (or disappeared)?
- Recommendations aligned with new strategy?
- Benchmark gaps recalculated correctly?
