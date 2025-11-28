import json
from pathlib import Path

# Charger le patrimoine
with open('generated/patrimoine_input.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Patterns
world_patterns = ["MSCI WORLD", "FTSE ALL-WORLD", "GLOBAL", "MONDE"]
us_patterns = ["S&P 500", "NASDAQ", "RUSSEL", "USA", "MSCI USA", "ACTIONS USA", " USA ", "UNITED STATES", "AMERICAN"]
em_patterns = ["EMERGING", "MSCI EM", "MARCHÉS ÉMERGENTS", "EMERGENT"]
asia_patterns = ["JAPAN", "JPXNK", "ASIA", "ASIAN", "CHINA", "HONG KONG", "INDIA", "NORDIC", "CHINE", "INDE"]

total_international = 0
detected_items = []

# Parcourir tous les établissements et comptes
for etab in data.get("patrimoine", {}).get("financier", {}).get("etablissements", []):
    etab_nom = etab.get("nom", "?")
    for compte in etab.get("comptes", []):
        compte_type = compte.get("type", "?")
        # Support pour les deux structures
        items = compte.get("positions", []) + compte.get("fonds", [])

        print(f"\n{etab_nom} - {compte_type}: {len(items)} items")

        for item in items:
            nom = item.get("nom", "").upper()
            valeur = item.get("valeur", item.get("montant", 0))

            # Identifier le type
            is_world = any(pattern in nom for pattern in world_patterns)
            is_us = any(pattern in nom for pattern in us_patterns)
            is_em = any(pattern in nom for pattern in em_patterns)
            is_asia = any(pattern in nom for pattern in asia_patterns)

            if is_world or is_us or is_em or is_asia:
                total_international += valeur
                detected_items.append({
                    "etablissement": etab_nom,
                    "compte": compte_type,
                    "nom": item.get("nom", "?"),
                    "valeur": valeur,
                    "type": "World" if is_world else ("US" if is_us else ("EM" if is_em else "Asia"))
                })
                print(f"  [OK] {item.get('nom', '?')[:50]}: {valeur:,.0f}EUR ({detected_items[-1]['type']})")

print(f"\n=== RÉSUMÉ ===")
print(f"Total international détecté: {total_international:,.0f}€")
print(f"Nombre de positions: {len(detected_items)}")

# Grouper par établissement
by_etab = {}
for item in detected_items:
    etab = item["etablissement"]
    if etab not in by_etab:
        by_etab[etab] = 0
    by_etab[etab] += item["valeur"]

print(f"\nPar établissement:")
for etab, montant in by_etab.items():
    print(f"  {etab}: {montant:,.0f}€")
