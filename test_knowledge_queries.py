"""
Test des requetes de validation du knowledge validator
Verifie quelles questions sont validables et lesquelles echouent
"""
import os
import sys
import re
import yaml
from pathlib import Path
from dotenv import load_dotenv

# Setup
sys.path.insert(0, str(Path(__file__).parent))
load_dotenv()

from tools.utils.tavily_search import TavilySearcher

def extract_values_from_sources(sources, value_type, value_range):
    """Extrait valeurs selon le type (copie de knowledge_validator logic)"""
    found_values = []

    for source in sources:
        extrait = source.get('extrait', '')

        if value_type == "pourcentage":
            matches = re.findall(
                r'(\d+(?:[.,]\d+)?)\s*(?:%|pour\s*cent|pourcent)',
                extrait,
                re.IGNORECASE
            )
            for m in matches:
                try:
                    found_values.append(float(m.replace(',', '.')))
                except ValueError:
                    pass

        elif value_type in ["entier", "mois"]:
            matches = re.findall(
                r'(\d+)\s*(?:mois|etablissement|compte|banque|an|annee)',
                extrait,
                re.IGNORECASE
            )
            for m in matches:
                try:
                    found_values.append(int(m))
                except ValueError:
                    pass

        elif value_type == "montant":
            matches = re.findall(
                r'(\d+(?:\s?\d{3})*)\s*(?:€|EUR|euros?)',
                extrait,
                re.IGNORECASE
            )
            for m in matches:
                try:
                    found_values.append(int(m.replace(' ', '')))
                except ValueError:
                    pass

    # Filtrer dans range
    valid_values = [v for v in found_values if value_range[0] <= v <= value_range[1]]
    return found_values, valid_values

def test_query(tavily, key, config):
    """Teste une requete de validation"""
    print(f"\n{'='*80}")
    print(f"TEST: {key}")
    print(f"Description: {config['description']}")
    print('='*80)

    queries = config.get('queries', [])
    value_type = config['valeur_attendue']['type']
    value_range = config['valeur_attendue']['fourchette']

    print(f"Type attendu: {value_type}")
    print(f"Fourchette: {value_range}")
    print(f"Queries: {len(queries)}")

    all_sources = []
    for i, query in enumerate(queries, 1):
        print(f"\n  [{i}/{len(queries)}] {query}")
        sources = tavily.search(query, search_depth="advanced", max_results=5)
        print(f"      -> {len(sources)} sources")
        all_sources.extend(sources)

    print(f"\nTotal sources: {len(all_sources)}")

    # Extraire valeurs
    all_values, valid_values = extract_values_from_sources(
        all_sources, value_type, value_range
    )

    print(f"\nValeurs extraites (total): {len(all_values)}")
    if all_values:
        print(f"  Exemples: {sorted(set(all_values))[:10]}")

    print(f"\nValeurs dans fourchette {value_range}: {len(valid_values)}")
    if valid_values:
        valid_sorted = sorted(valid_values)
        median = valid_sorted[len(valid_sorted)//2]
        print(f"  Valeurs: {valid_sorted}")
        print(f"  Mediane: {median}")

    # Verdict
    min_sources = 2  # Comme dans knowledge_validator
    if len(valid_values) >= min_sources:
        print(f"\n*** RESULTAT: SUCCES (>= {min_sources} valeurs valides)")
        return True
    else:
        print(f"\n*** RESULTAT: ECHEC (< {min_sources} valeurs valides)")
        return False

def main():
    # Load config
    with open('config/recommendations_knowledge.yaml', 'r', encoding='utf-8') as f:
        knowledge_config = yaml.safe_load(f)

    config = {"analyzer": {"web_research": {"timeout_seconds": 30}}}
    tavily = TavilySearcher(config)

    if not tavily.enabled:
        print("ERREUR: TAVILY_API_KEY non definie")
        return

    print("="*80)
    print("TEST DE VALIDATION DES REQUETES KNOWLEDGE")
    print("="*80)

    # Queries a tester (les "probablement validables")
    test_keys = [
        "fonds_urgence_mois",
        "taux_livret_a_actuel",
        "rendement_fonds_euro_moyen",
        "seuil_concentration_etablissement",
        "nombre_etablissements_optimal",
    ]

    results = {}

    for key in test_keys:
        query_config = knowledge_config['requetes_validation'].get(key)
        if not query_config:
            print(f"\nWARNING: {key} non trouve dans config")
            continue

        try:
            success = test_query(tavily, key, query_config)
            results[key] = success
        except Exception as e:
            print(f"\nERREUR lors du test de {key}: {e}")
            results[key] = False

    # Resume
    print(f"\n\n{'='*80}")
    print("RESUME DES TESTS")
    print('='*80)

    for key, success in results.items():
        status = "OK" if success else "ECHEC"
        symbol = "✓" if success else "✗"
        print(f"  [{status:6}] {key}")

    success_count = sum(results.values())
    total_count = len(results)
    print(f"\nTaux de succes: {success_count}/{total_count} ({100*success_count/total_count:.0f}%)")

if __name__ == "__main__":
    main()
