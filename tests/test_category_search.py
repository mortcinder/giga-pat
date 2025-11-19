#!/usr/bin/env python3
"""
Test de la fonctionnalité search_by_category() - v2.2.1
"""

import sys
import logging
import yaml
from pathlib import Path
from dotenv import load_dotenv

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Charger les variables d'environnement
load_dotenv(Path(__file__).parent.parent / ".env")

from tools.utils.web_research import WebResearcher


def setup_logging():
    """Configure le logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def load_config():
    """Charge la configuration"""
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def test_search_by_category():
    """Test de la méthode search_by_category()"""
    print("\n" + "=" * 70)
    print("TEST: search_by_category() - v2.2.1")
    print("=" * 70)

    try:
        config = load_config()
        researcher = WebResearcher(config)

        print(f"\n✓ WebResearcher créé avec {len(researcher.providers)} provider(s)")

        # Vérifier que la méthode existe
        assert hasattr(researcher, 'search_by_category'), "Méthode search_by_category() manquante"
        print("✓ Méthode search_by_category() existe")

        # Vérifier la configuration du mapping
        web_config = config.get("analyzer", {}).get("web_research", {})
        provider_mapping = web_config.get("provider_mapping", {})

        print(f"\n✓ Configuration provider_mapping:")
        for category, provider in provider_mapping.items():
            print(f"  {category}: {provider}")

        # Test rapide d'une recherche (seulement si provider disponible)
        if researcher.enabled and researcher.providers:
            print("\n→ Test d'une recherche factuelle (catégorie: factual)...")

            results = researcher.search_by_category(
                category="factual",
                sujet="Test catégorie factuelle",
                queries=["garantie dépôts France"],
                context="Test unitaire"
            )

            print(f"✓ Recherche effectuée: {len(results)} résultat(s)")

            # Vérifier l'historique
            history = researcher.get_history()
            if history:
                last_search = history[-1]
                assert 'category' in last_search, "Category manquante dans l'historique"
                assert last_search['category'] == 'factual', "Catégorie incorrecte dans l'historique"
                print(f"✓ Historique enregistré avec category: {last_search['category']}")
                print(f"✓ Provider utilisé: {last_search.get('provider_used', 'N/A')}")
        else:
            print("\n⚠ Aucun provider disponible, skip test de recherche")

        print("\n" + "=" * 70)
        print("TEST RÉUSSI ✓")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"\n✗ Erreur: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "=" * 70)
        print("TEST ÉCHOUÉ ✗")
        print("=" * 70)
        return False


if __name__ == "__main__":
    setup_logging()
    success = test_search_by_category()
    sys.exit(0 if success else 1)
