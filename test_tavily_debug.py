"""
Script de debug pour analyser les réponses Tavily
"""
import os
import sys
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

# Setup path
sys.path.insert(0, str(Path(__file__).parent))

# Load .env
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(levelname)s] %(message)s'
)

from tools.utils.tavily_search import TavilySearcher

def test_tavily_search():
    """Test Tavily avec les vraies requêtes du knowledge validator"""

    # Config minimale
    config = {
        "analyzer": {
            "web_research": {
                "timeout_seconds": 30
            }
        }
    }

    tavily = TavilySearcher(config)

    if not tavily.enabled:
        print("ERREUR: TAVILY_API_KEY non definie dans .env")
        return

    print("=" * 80)
    print("TEST TAVILY - Recherche recommandations patrimoniales")
    print("=" * 80)

    # Les 3 requêtes du knowledge validator pour "montant_minimum_livret"
    queries = [
        "montant minimum livret épargne rentable",
        "fermer livret faible montant recommandation CGP",
        "livret doublon montant seuil"
    ]

    all_sources = []

    for i, query in enumerate(queries, 1):
        print(f"\n{'='*80}")
        print(f"QUERY {i}/3: {query}")
        print('='*80)

        sources = tavily.search(
            query,
            search_depth="advanced",
            max_results=5
        )

        print(f"\nTavily retourne: {len(sources)} sources\n")

        for j, source in enumerate(sources, 1):
            print(f"\n--- SOURCE {j} ---")
            print(f"URL: {source.get('url', 'N/A')}")
            print(f"Titre: {source.get('titre', 'N/A')}")
            print(f"Score: {source.get('score', 0):.3f}")
            print(f"Pertinence: {source.get('pertinence', 'N/A')}")
            print(f"\nEXTRAIT (300 car):")
            print(f"{source.get('extrait', 'N/A')}")
            print()

            # Chercher montants dans l'extrait
            import re
            extrait = source.get('extrait', '')

            # Pattern pour montants (€)
            montants = re.findall(
                r'(\d+(?:\s?\d{3})*)\s*(?:€|EUR|euros?)',
                extrait,
                re.IGNORECASE
            )

            if montants:
                print(f"MONTANTS TROUVES: {montants}")
            else:
                print("Aucun montant extractible avec regex actuelle")

        all_sources.extend(sources)

    print(f"\n{'='*80}")
    print(f"RÉSUMÉ GLOBAL")
    print('='*80)
    print(f"Total sources: {len(all_sources)}")

    # Analyser tous les extraits
    all_montants = []
    for source in all_sources:
        extrait = source.get('extrait', '')
        montants = re.findall(
            r'(\d+(?:\s?\d{3})*)\s*(?:€|EUR|euros?)',
            extrait,
            re.IGNORECASE
        )
        for m in montants:
            try:
                valeur = int(m.replace(' ', ''))
                all_montants.append(valeur)
                print(f"  Montant extrait: {valeur}€ depuis {source.get('url', '')[:50]}")
            except ValueError:
                pass

    print(f"\nMontants totaux extraits: {len(all_montants)}")

    if all_montants:
        # Filtrer dans fourchette [3000, 10000]
        valid = [m for m in all_montants if 3000 <= m <= 10000]
        print(f"Montants dans fourchette [3000, 10000]: {len(valid)}")
        if valid:
            print(f"Valeurs: {sorted(valid)}")
            print(f"Mediane: {sorted(valid)[len(valid)//2]} euros")
        else:
            print(f"Tous les montants hors fourchette: {sorted(all_montants)}")
    else:
        print("AUCUN MONTANT EXTRACTIBLE")
        print("\nRECOMMANDATION: Les snippets de 300 caracteres sont probablement trop courts")
        print("   ou les sources ne mentionnent pas de montants explicites.")

if __name__ == "__main__":
    test_tavily_search()
