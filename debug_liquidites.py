import json

# Charger patrimoine_input.json
with open('generated/patrimoine_input.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=== STRUCTURE PATRIMOINE INPUT ===")
patrimoine = data.get('patrimoine', {})
print(f"Keys: {list(patrimoine.keys())}")

print(f"\nTotal liquidites: {patrimoine.get('total_liquidites', 0):,.0f} EUR")
print(f"Total patrimoine: {patrimoine.get('patrimoine_total', 0):,.0f} EUR")

# Etablissements
etablissements = patrimoine.get('etablissements', [])
print(f"\nNombre etablissements: {len(etablissements)}")

total_liquide = 0
for e in etablissements:
    nom = e.get('nom', '?')
    total = e.get('total', 0)
    print(f"\n{nom}: {total:,.0f} EUR")

    comptes = e.get('comptes', [])
    for c in comptes[:5]:
        compte_type = c.get('type', '?')
        montant = c.get('montant', 0)
        print(f"  - {compte_type}: {montant:,.0f} EUR")

        # Identifier liquidités
        if any(x in compte_type.lower() for x in ['livret', 'compte', 'depot', 'ldd', 'ldds', 'pel', 'lep']):
            total_liquide += montant
            print(f"    -> LIQUIDE")

print(f"\n=== TOTAL CALCULE ===")
print(f"Liquidites identifiees: {total_liquide:,.0f} EUR")
