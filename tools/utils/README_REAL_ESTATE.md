# Real Estate Valorization Module

**Version**: 2.1.2+
**Module**: `tools/utils/real_estate_valorizer.py`

## Purpose

Automatically revalue real estate properties at each report generation by extracting market prices from web searches and applying intelligent fallback pricing.

## Architecture

```
RealEstateValorizer
├── extract_price_per_m2()        # Extract price/m² from web results or fallback
├── calculate_property_value()    # Calculate valuation + plus-value
└── _get_fallback_price()         # City-specific fallback prices
```

## Usage

### In risk_analyzer.py

```python
from tools.utils.real_estate_valorizer import RealEstateValorizer

# Initialize
valorizer = RealEstateValorizer()

# Calculate valuation
valorisation = valorizer.calculate_property_value(
    surface_m2=25,
    city="Nanterre",
    web_sources=[...],  # From Brave API
    acquisition_price=110000
)

# Result
{
    "valeur_actuelle": 132500,
    "prix_m2": 5300,
    "source": "fallback",  # or "web"
    "nb_sources_web": 0,
    "plus_value": 22500,
    "plus_value_pct": 20.5
}
```

## Web Extraction

### Search Queries

Performed by `risk_analyzer.py`:
```python
queries = [
    f"prix immobilier m² {city} 2025",
    f"marché immobilier {city} évolution",
    f"valorisation {property_type} {city}"
]
```

### Extraction Patterns

```python
patterns = [
    r"(\d[\d\s]*)\s*€\s*/\s*m[²2]",           # "5 300 €/m²"
    r"(\d[\d\s]*)\s*euros?\s*/\s*m[²2]",      # "5 300 euros/m²"
    r"prix\s+(?:moyen|médian)\s*:\s*(\d[\d\s]*)\s*€",  # "prix moyen : 5 300 €"
    r"(\d[\d\s]*)\s*€.*m[²2]",                # "5 300 € le m²"
]
```

### Filtering

- Valid range: 1,000 - 20,000 €/m²
- Returns **median** of extracted prices (robust against outliers)

## Fallback Pricing

### Default Prices (as of 2025)

```python
fallback_prices = {
    "nanterre": 5300,      # Hauts-de-Seine, proche Paris
    "paris": 10500,
    "lyon": 5800,
    "marseille": 4200,
    "toulouse": 4000,
    "bordeaux": 4500,
    "nice": 5500,
    "strasbourg": 3800,
    "lille": 3600,
    "rennes": 4100,
    "default": 3500        # National average
}
```

### Customization

Edit `tools/utils/real_estate_valorizer.py`:

```python
self.fallback_prices = {
    "nanterre": 5300,
    "your_city": 4500,  # ← Add your city
    "default": 3500
}
```

## Manifest Structure (v2.1.2)

**⚠️ IMPORTANT**: Do NOT include `valeur_actuelle` in manifest.json

```json
{
  "patrimoine": {
    "immobilier": [{
      "id": "nanterre_studio_001",
      "custodian": "self",
      "custodian_name": "Propriété directe",
      "custody_type": "direct_ownership",
      "type_bien": "Studio",
      "adresse": "34 rue Salvador Allende, 92000 Nanterre",
      "surface_m2": 25,
      "prix_acquisition": 110000,
      "currency": "EUR",
      "metadata": {
        "prix_m2_acquisition": 4400,
        "date_acquisition": "2016-06-30",
        "station_metro": "RER Nanterre-Préfecture"
      }
    }]
  }
}
```

**Required fields**:
- `surface_m2`: Surface in square meters (used for calculation)
- `prix_acquisition`: Acquisition price (reference for plus-value)
- `adresse`: Full address with postal code (for city extraction)

## Integration Flow

### Stage 1: Normalizer

```python
# tools/normalizer.py → _integrate_immobilier()

bien_entry = {
    "type": bien.get("type_bien", "Bien"),
    "adresse": bien.get("adresse", ""),
    "surface_m2": bien.get("surface_m2", 0),
    "prix_acquisition": bien.get("prix_acquisition", 0),
    "valeur_actuelle": bien.get("prix_acquisition", 0),  # Temporary
    "metadata": bien.get("metadata", {})
}
```

### Stage 2: Analyzer

```python
# tools/utils/risk_analyzer.py → _analyze_market_risks()

# Extract city from address
ville = re.search(r"\d{5}\s+([A-Za-zÀ-ÿ\s-]+)", adresse).group(1).strip()

# Web searches
sources_immo = self.web_researcher.search(
    f"Valorisation immobilière {ville}",
    [f"prix immobilier m² {ville} 2025", ...]
)

# Calculate valorization
valorisation = self.real_estate_valorizer.calculate_property_value(
    surface_m2=surface_m2,
    city=ville,
    web_sources=sources_immo,
    acquisition_price=prix_acquisition
)

# Update property
bien["valeur_actuelle"] = valorisation["valeur_actuelle"]
bien["prix_m2_actuel"] = valorisation["prix_m2"]
bien["valorisation_source"] = valorisation["source"]

# Recalculate total
data["patrimoine"]["immobilier"]["total"] = sum(
    b.get("valeur_actuelle", 0) for b in biens_immobiliers
)
```

### Stage 3: Report

```html
<h3>Valorisation Studio — Nanterre</h3>
<p>
Studio situé à 34 rue Salvador Allende, 92000 Nanterre.
Surface: 25m².
Valeur estimée actuelle: 132,500€
(prix m²: 5,300€, source: fallback).
Plus-value: +20.5% depuis acquisition (110,000€).
</p>
```

## Logging

```
[INFO] Recherche valorisation immobilière Nanterre: 0 sources
[WARNING] Aucune source web disponible pour Nanterre, utilisation fallback
[INFO] Prix fallback pour Nanterre: 5300 €/m²
[INFO] Valorisation calculée : 25m² × 5300€/m² = 132500€ (source: fallback)
[INFO] Valorisation Studio Nanterre: 132,500€ (25m² × 5300€/m², source: fallback)
[INFO] Total immobilier recalculé: 132,500€
```

## Testing

```bash
# Full pipeline test
python3 main.py

# Check logs for valorization
grep -E "(Valorisation|fallback|prix.*m²)" logs/rapport_*.log

# Verify in report
grep "Valeur estimée actuelle" generated/rapport_*.html
```

## Future Enhancements

1. **LLM-based extraction**: Use Claude to extract precise price/m² from web snippets
2. **Historical tracking**: Store valorization history in database
3. **Market trends**: Add trend indicators (↑/↓) based on historical data
4. **Neighborhood analysis**: Factor in micro-location (proximity to metro, schools, etc.)
5. **Automated alerts**: Notify when property value changes >5%

## References

- Main documentation: `tools/CLAUDE.md` → "Real Estate Valorization"
- Project overview: `CLAUDE.md` → v2.1.2 changes
- PRD: `PRD.md` → Version 2.1.2
