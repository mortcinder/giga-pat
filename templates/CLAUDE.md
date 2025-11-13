# templates/ - Template System Guide

This file provides detailed guidance for working with the HTML template injection system.

## Template Overview

**Main Template**: `templates/rapport_template.html`

**Design Principles**:
1. **Data-driven**: All dynamic content via `data-field` and `data-repeat` attributes
2. **Standalone**: CSS inlined, no external dependencies
3. **Safe injection**: No direct HTML string manipulation
4. **Structured**: Semantic HTML5 with BEM-like CSS classes

**Generated Output**: `generated/rapport_YYYYMMDD_HHMMSS.html` (timestamped, never overwritten)

## Injection System

**Implementation**: `tools/generator.py`

### 7 Injection Mechanisms

#### 1. CSS Inlining

**Purpose**: Make HTML standalone (no external CSS file)

**Implementation**:
- Reads `templates/rapport.css`
- Injects into `<style>` tag in `<head>`
- Result: Single HTML file with all assets

**Method**: `_inline_css()`

**Example**:
```html
<!-- Before -->
<link rel="stylesheet" href="rapport.css">

<!-- After -->
<style>
  /* Full CSS content here */
</style>
```

#### 2. Simple Fields

**Purpose**: Replace single values in template

**Syntax**: `data-field="fieldname"`

**Implementation**:
- Maps JSON path to element
- Replaces `{{fieldname}}` or element text content
- Handles nested paths with dot notation

**Method**: `_inject_simple_fields()`

**Example**:
```html
<!-- Template -->
<h1 data-field="titre">{{titre}}</h1>
<p data-field="patrimoine.total">{{patrimoine.total}}</p>

<!-- JSON -->
{
  "titre": "Rapport Patrimonial 2025",
  "patrimoine": {"total": "500,000 €"}
}

<!-- Result -->
<h1>Rapport Patrimonial 2025</h1>
<p>500,000 €</p>
```

**Available Fields**: See "Field Reference" section below

#### 3. Repeated Rows

**Purpose**: Clone and populate rows for lists

**Syntax**: `data-repeat="typename"`

**Implementation**:
- Identifies template row
- Clones for each item in JSON array
- Populates each clone with item data
- Removes original template row

**Method**: `_inject_repeated_rows()`

**Example**:
```html
<!-- Template -->
<tr data-repeat="etablissement">
  <td data-field="nom">{{nom}}</td>
  <td data-field="total">{{total}}</td>
</tr>

<!-- JSON -->
{
  "etablissements": [
    {"nom": "Crédit Agricole", "total": "250,000 €"},
    {"nom": "Fortuneo", "total": "150,000 €"}
  ]
}

<!-- Result -->
<tr>
  <td>Crédit Agricole</td>
  <td>250,000 €</td>
</tr>
<tr>
  <td>Fortuneo</td>
  <td>150,000 €</td>
</tr>
```

**Available Types**:
- `etablissement`: Custodians list
- `actif`: Assets within custodian
- `risque`: Risk items
- `recommandation`: Recommendation items
- `classe_actif`: Asset class rows (special handling)

#### 4. Conditional Elements

**Purpose**: Remove elements if condition not met

**Syntax**: `data-conditional="identifier"`

**Implementation**:
- Checks if data exists for identifier
- Removes element if missing or false
- Keeps element if present and truthy

**Method**: `_inject_conditional_elements()`

**Example**:
```html
<!-- Template -->
<div data-conditional="optimisation_portfolio">
  <h2>Portfolio Optimization</h2>
  <p data-field="optimisation_portfolio.sharpe_ratio">{{sharpe}}</p>
</div>

<!-- JSON (no optimization data) -->
{}

<!-- Result -->
<!-- Element completely removed -->
```

**Common Uses**:
- Hide sections when data unavailable
- Optional features (e.g., portfolio optimization)
- Conditional warnings

#### 5. Dynamic Badges

**Purpose**: Apply severity CSS classes to badges

**Syntax**: `class="badge"` (NO hardcoded severity)

**Implementation**:
- Reads severity from data (`crit`, `high`, `mid`, `low`)
- Dynamically applies CSS class
- Removes unused badge elements

**Method**: `_inject_repeated_rows()` (handles badges automatically)

**Example**:
```html
<!-- Template (CORRECT) -->
<span class="badge">{{severite}}</span>

<!-- Template (WRONG - never hardcode severity) -->
<span class="badge crit">{{severite}}</span>  ❌

<!-- JSON -->
{
  "risques": [
    {"severite": "crit", "titre": "Concentration élevée"}
  ]
}

<!-- Result -->
<span class="badge crit">Critique</span>
```

**Badge CSS Classes**:
- `.badge.crit`: Critical (red-dark)
- `.badge.high`: High (red-light)
- `.badge.mid`: Medium (gold)
- `.badge.low`: Normal (green)

#### 6. Chart Injection

**Purpose**: Inject radar chart data for scores

**Syntax**: Regex-based replacement in `<script>` tag

**Implementation**:
- Finds Chart.js configuration
- Replaces placeholder values with actual scores
- Injects labels and data arrays

**Method**: `_inject_chart_data()`

**Example**:
```html
<!-- Template -->
<script>
const radarData = {
  labels: ['Diversification', 'Résilience', 'Liquidité', 'Fiscal', 'Croissance'],
  datasets: [{
    data: [0, 0, 0, 0, 0]  // Placeholder
  }]
};
</script>

<!-- Result -->
<script>
const radarData = {
  labels: ['Diversification', 'Résilience', 'Liquidité', 'Fiscal', 'Croissance'],
  datasets: [{
    data: [8.5, 7.2, 9.0, 6.8, 7.5]  // Actual scores
  }]
};
</script>
```

#### 7. Two-Line Asset Classes

**Purpose**: Display primary (asset type) + secondary (account detail) rows

**Syntax**: `data-repeat="classe_actif"`

**Implementation**:
- Special handling in `_inject_classes_actifs()`
- Primary row: Asset class totals
- Secondary row: Account-level breakdown
- Indentation and styling applied

**Method**: `_inject_classes_actifs()`

**Example**:
```html
<!-- Result -->
<tr class="primary">
  <td>Actions</td>
  <td>250,000 €</td>
  <td>50%</td>
  <td><span class="badge mid">Dans la cible</span></td>
</tr>
<tr class="secondary">
  <td>└─ PEA Crédit Agricole</td>
  <td>150,000 €</td>
  <td>30%</td>
  <td></td>
</tr>
<tr class="secondary">
  <td>└─ CTO Fortuneo</td>
  <td>100,000 €</td>
  <td>20%</td>
  <td></td>
</tr>
```

## Modifying the Template

### Rules and Best Practices

**MUST PRESERVE**:
- `data-field="fieldname"` attributes
- `data-repeat="typename"` attributes
- `data-conditional="identifier"` attributes
- Badge structure: `class="badge"` only (NO severity classes)

**SAFE TO MODIFY**:
- HTML structure (divs, sections, headings)
- CSS classes (except `data-*` and badge classes)
- Text labels and headers
- Layout and styling
- Chart configurations

**NEVER**:
- Hardcode severity classes on badges
- Remove `data-*` attributes without updating generator.py
- Modify field names without checking JSON structure
- Add external dependencies (CSS, JS libraries) - keep standalone

### Adding New Field

**Scenario**: You want to display a new data point

**Steps**:
1. Add `data-field="newfield"` to template:
   ```html
   <p data-field="new_field">{{new_field}}</p>
   ```

2. Add mapping in `tools/generator.py` → `_inject_simple_fields()`:
   ```python
   def _inject_simple_fields(self, html, data):
       field_map = {
           # Existing fields...
           "new_field": data.get("new_field", "N/A")
       }
       # ... rest of method
   ```

3. Ensure data exists in `patrimoine_analysis.json` (Stage 2 output)

4. Test: `python main.py` and check generated HTML

### Adding New Repeated Section

**Scenario**: You want to add a list of items (e.g., "transactions")

**Steps**:
1. Add template row with `data-repeat="transaction"`:
   ```html
   <table>
     <tbody>
       <tr data-repeat="transaction">
         <td data-field="date">{{date}}</td>
         <td data-field="description">{{description}}</td>
         <td data-field="amount">{{amount}}</td>
       </tr>
     </tbody>
   </table>
   ```

2. Add handling in `tools/generator.py` → `_inject_repeated_rows()`:
   ```python
   elif row.get("data-repeat") == "transaction":
       transactions = data.get("transactions", [])
       for transaction in transactions:
           new_row = copy.deepcopy(row)
           # Populate fields...
           result_rows.append(new_row)
   ```

3. Ensure `transactions[]` array exists in JSON output

4. Test: `python main.py` and verify rows are cloned correctly

### Adding Conditional Section

**Scenario**: Hide a section if optional data is missing

**Steps**:
1. Add `data-conditional="identifier"` to wrapper element:
   ```html
   <section data-conditional="stress_tests">
     <h2>Stress Tests</h2>
     <!-- Content here -->
   </section>
   ```

2. The generator automatically removes if `data.get("stress_tests")` is None or False

3. Test both scenarios:
   - With data: Section appears
   - Without data: Section removed

### Changing Badge Thresholds

**Scenario**: Adjust what qualifies as "critical" vs "high"

**Steps**:
1. Edit `config/risks.yaml` or `config/config.yaml` thresholds
2. Risk severity recalculated in Stage 2 (analyzer.py)
3. Template automatically applies correct badge class
4. NO template changes required

## Field Reference

**Complete list of available `data-field` values** (as of v2.1):

### General Fields
- `titre`: Report title
- `date_generation`: Generation date/time
- `patrimoine.total`: Total portfolio value
- `patrimoine.total_format`: Formatted total (with currency)
- `profil`: Active investor profile (dynamique, equilibre, prudent)

### Scores (5 metrics)
- `scores.diversification.score`: Diversification score (0-10)
- `scores.diversification.label`: Label (Excellente, Bonne, etc.)
- `scores.diversification.notes[]`: Breakdown notes
- `scores.resilience.score`: Resilience score
- `scores.resilience.label`
- `scores.resilience.notes[]`
- `scores.liquidity.score`: Liquidity score
- `scores.liquidity.label`
- `scores.liquidity.notes[]`
- `scores.fiscal.score`: Fiscal optimization score
- `scores.fiscal.label`
- `scores.fiscal.notes[]`
- `scores.growth.score`: Growth potential score
- `scores.growth.label`
- `scores.growth.notes[]`

### Etablissements (Repeated)
- `etablissements[].nom`: Custodian name
- `etablissements[].total`: Total value at custodian
- `etablissements[].pct`: Percentage of portfolio
- `etablissements[].juridiction`: Jurisdiction
- `etablissements[].actifs[]`: Assets within custodian

### Actifs (Repeated within Etablissement)
- `actifs[].type`: Asset type
- `actifs[].nom`: Asset name
- `actifs[].valorisation`: Current value
- `actifs[].pct`: Percentage of custodian

### Classes d'Actifs (Repeated with Two-Line Format)
- `classes_actifs[].classe`: Asset class name (Actions, Obligations, etc.)
- `classes_actifs[].montant`: Total amount in class
- `classes_actifs[].pct`: Percentage of portfolio
- `classes_actifs[].benchmark_gap`: Gap status (dans_la_cible, sous_pondere, etc.)
- `classes_actifs[].comptes[]`: Account-level breakdown

### Risques (Repeated)
- `risques[].severite`: Severity (crit, high, mid, low)
- `risques[].titre`: Risk title
- `risques[].description`: Detailed description
- `risques[].sources[]`: Web sources (URLs)

### Recommandations (Repeated)
- `recommandations[].titre`: Recommendation title
- `recommandations[].description`: Detailed description
- `recommandations[].priorite`: Priority score (0-10)
- `recommandations[].impact`: Expected impact
- `recommandations[].facilite`: Implementation difficulty

### Portfolio Optimization (Conditional)
- `optimisation_portfolio.sharpe_actuel`: Current Sharpe ratio
- `optimisation_portfolio.sharpe_optimal`: Optimal Sharpe ratio
- `optimisation_portfolio.allocation_optimale[]`: Optimal allocation

### Stress Tests (Conditional)
- `stress_tests[].scenario`: Scenario name
- `stress_tests[].impact`: Impact on portfolio (%)
- `stress_tests[].nouveau_total`: New portfolio value

## Badge System

**4 Severity Levels** (dynamically applied):

### 1. Critical (`.badge.crit`)
- **Color**: Dark red (#c0392b)
- **Use Cases**:
  - Critical risks (>70% concentration)
  - Severe liquidity issues (<10% liquid)
  - Major regulatory exposure

### 2. High (`.badge.high`)
- **Color**: Light red (#e74c3c)
- **Use Cases**:
  - High risks (40-70% concentration)
  - Moderate liquidity issues (10-15% liquid)
  - Significant regulatory exposure

### 3. Medium (`.badge.mid`)
- **Color**: Gold (#f39c12)
- **Use Cases**:
  - Moderate risks (20-40% concentration)
  - Acceptable but suboptimal conditions
  - Benchmark gaps (sous/sur-pondéré modéré)

### 4. Low (`.badge.low`)
- **Color**: Green (#27ae60)
- **Use Cases**:
  - Normal/good conditions
  - Within target ranges
  - No concerns

**CSS Implementation** (in `rapport.css`):
```css
.badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.875rem;
  font-weight: 600;
}

.badge.crit { background: #c0392b; color: white; }
.badge.high { background: #e74c3c; color: white; }
.badge.mid { background: #f39c12; color: white; }
.badge.low { background: #27ae60; color: white; }
```

## Enriched Scores Design (v3.0)

**5 Scores with Detailed Breakdowns**

**Design Pattern**:
```html
<section class="syn-block">
  <div class="syn-head">
    <h3>Score de Diversification</h3>
    <span class="syn-score">8.5</span>
    <span class="syn-label">Bonne</span>
  </div>
  <div class="syn-grid">
    <div class="syn-note-list">
      <h4>Détails du calcul</h4>
      <ul>
        <li><strong>Bonus :</strong> +1.0 pour 5+ classes d'actifs</li>
        <li><strong>Pénalités :</strong> -2.0 pour concentration custodian</li>
        <li><strong>Alerte :</strong> Diversifier davantage les établissements</li>
        <li><strong>Interprétation :</strong> Score correct mais améliorable</li>
        <li><strong>Méthodologie :</strong> (Institutional × 60%) + (Jurisdictional × 40%) + Bonuses</li>
      </ul>
    </div>
  </div>
</section>
```

**Standardized Note Labels** (use consistently):
- **Bonus :** Positive factors that increase score
- **Pénalités :** Negative factors that decrease score
- **Alerte :** Warnings or concerns
- **Interprétation :** Human-readable explanation
- **Méthodologie :** Formula or calculation method

**CSS Classes**:
- `.syn-block`: Score section wrapper
- `.syn-head`: Header with score and label
- `.syn-score`: Large score number (0-10)
- `.syn-label`: Label (Excellente, Bonne, etc.)
- `.syn-grid`: Content grid
- `.syn-note-list`: Breakdown notes list

## Testing Template Changes

**Best Practice**: Test locally before deploying

**Steps**:
1. Modify template: `templates/rapport_template.html`
2. Run generator: `python main.py`
3. Open generated HTML: `generated/rapport_*.html`
4. Verify:
   - Data injected correctly
   - No missing fields (check for `{{}}` placeholders)
   - Badges styled correctly
   - Repeated rows cloned properly
   - Conditional sections show/hide correctly
5. Test edge cases:
   - Empty lists (no risks, no recommendations)
   - Missing optional data (stress tests, optimization)
   - Very long text content
   - Many items (20+ custodians, 100+ assets)

**Common Issues**:
- **Missing `data-field`**: Results in `{{fieldname}}` appearing in output
- **Wrong `data-repeat` type**: Rows not cloned or wrong data injected
- **Hardcoded badge class**: Badge always shows same severity regardless of data
- **Missing field in JSON**: Element shows "N/A" or empty
- **Broken chart**: Check `_inject_chart_data()` regex pattern

## Advanced Customization

### Adding New Chart

**Scenario**: Add a pie chart for asset allocation

**Steps**:
1. Add Chart.js canvas in template:
   ```html
   <canvas id="allocationChart"></canvas>
   <script>
   const ctx = document.getElementById('allocationChart').getContext('2d');
   const chart = new Chart(ctx, {
     type: 'pie',
     data: {
       labels: [],  // Will be injected
       datasets: [{
         data: []  // Will be injected
       }]
     }
   });
   </script>
   ```

2. Add injection method in `generator.py`:
   ```python
   def _inject_allocation_chart(self, html, data):
       classes = data.get("classes_actifs", [])
       labels = [c["classe"] for c in classes]
       values = [c["pct"] for c in classes]

       html = re.sub(
           r"labels:\s*\[\]",
           f"labels: {json.dumps(labels)}",
           html
       )
       html = re.sub(
           r"data:\s*\[\]",
           f"data: {json.dumps(values)}",
           html
       )
       return html
   ```

3. Call in `generate()` method

4. Test: `python main.py`

### Localizing Template

**Scenario**: Translate to English or another language

**Steps**:
1. Create `templates/rapport_template_en.html`
2. Translate all static text labels
3. Keep all `data-field` and `data-repeat` attributes unchanged
4. Update `generator.py` to accept `language` parameter
5. Load appropriate template based on language

**Note**: Data field names remain in French (JSON structure unchanged)

### Theming

**Scenario**: Apply dark mode or custom brand colors

**Steps**:
1. Create `templates/rapport_dark.css` or `rapport_branded.css`
2. Update CSS variables:
   ```css
   :root {
     --primary-color: #your-brand-color;
     --background: #1a1a1a;
     --text: #f0f0f0;
   }
   ```
3. Update `generator.py` → `_inline_css()` to load alternate CSS
4. Badge colors should remain accessible (WCAG AA)

**Accessibility**:
- Maintain contrast ratios (min 4.5:1 for text)
- Don't rely solely on color for severity (use icons too)
- Test with screen readers
