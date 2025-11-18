#!/usr/bin/env python3
"""
Test d'intégration WebResearcher v2.0 - Vérifie la compatibilité
"""

import sys
import os
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


def test_initialization():
    """Test 1: Initialisation de WebResearcher"""
    print("\n" + "=" * 70)
    print("TEST 1: Initialisation WebResearcher v2.0")
    print("=" * 70)

    try:
        config = load_config()
        researcher = WebResearcher(config)

        print(f"✓ WebResearcher créé")
        print(f"✓ Enabled: {researcher.enabled}")
        print(f"✓ Nombre de providers: {len(researcher.providers)}")

        if researcher.providers:
            print("\nProviders disponibles:")
            for i, provider in enumerate(researcher.providers, 1):
                print(f"  {i}. {provider.provider_name} (priorité {i})")

        return True

    except Exception as e:
        print(f"✗ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_compatibility():
    """Test 2: Compatibilité API publique (analyzer.py ne doit pas casser)"""
    print("\n" + "=" * 70)
    print("TEST 2: Compatibilité API Publique")
    print("=" * 70)

    try:
        config = load_config()
        researcher = WebResearcher(config)

        # Vérifier que les méthodes publiques existent
        assert hasattr(researcher, 'search'), "Méthode search() manquante"
        assert hasattr(researcher, 'get_history'), "Méthode get_history() manquante"
        assert hasattr(researcher, 'get_search_count'), "Méthode get_search_count() manquante"

        print("✓ Méthode search() existe")
        print("✓ Méthode get_history() existe")
        print("✓ Méthode get_search_count() existe")

        # Tester get_history() et get_search_count()
        history = researcher.get_history()
        count = researcher.get_search_count()

        print(f"✓ get_history() retourne: {type(history).__name__}")
        print(f"✓ get_search_count() retourne: {count}")

        return True

    except Exception as e:
        print(f"✗ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_loading():
    """Test 3: Vérification de la configuration multi-provider"""
    print("\n" + "=" * 70)
    print("TEST 3: Configuration Multi-Provider")
    print("=" * 70)

    try:
        config = load_config()
        web_config = config.get("analyzer", {}).get("web_research", {})

        print(f"✓ Provider principal: {web_config.get('provider')}")
        print(f"✓ Fallback activé: {web_config.get('enable_fallback')}")

        fallback_providers = web_config.get('fallback_providers', [])
        print(f"✓ Ordre de fallback: {fallback_providers}")

        # Vérifier l'ordre
        expected_order = ["brave", "serper", "tavily", "ddgs"]
        if fallback_providers == expected_order:
            print(f"✓ Ordre de fallback correct: {fallback_providers}")
        else:
            print(f"✗ Ordre de fallback incorrect!")
            print(f"  Attendu: {expected_order}")
            print(f"  Trouvé: {fallback_providers}")
            return False

        # Vérifier les configs individuelles
        providers_config = web_config.get('providers', {})
        print(f"\nConfiguration des providers:")
        for name in expected_order:
            if name in providers_config:
                prov_config = providers_config[name]
                print(f"  {name}:")
                print(f"    - enabled: {prov_config.get('enabled')}")
                print(f"    - rate_limit: {prov_config.get('rate_limit')}s")
                print(f"    - timeout: {prov_config.get('timeout')}s")
                print(f"    - priority: {prov_config.get('priority')}")

        return True

    except Exception as e:
        print(f"✗ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 70)
    print("TESTS D'INTÉGRATION WEBRESEARCHER V2.0")
    print("=" * 70)

    setup_logging()

    results = []

    # Test 1: Initialisation
    results.append(("Initialisation", test_initialization()))

    # Test 2: API Compatibility
    results.append(("Compatibilité API", test_api_compatibility()))

    # Test 3: Configuration
    results.append(("Configuration", test_config_loading()))

    # Résumé
    print("\n" + "=" * 70)
    print("RÉSUMÉ DES TESTS")
    print("=" * 70)

    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(success for _, success in results)

    print("\n" + "=" * 70)
    if all_passed:
        print("TOUS LES TESTS D'INTÉGRATION ONT RÉUSSI ✓")
        print("\nLe code est prêt à être commité.")
    else:
        print("CERTAINS TESTS ONT ÉCHOUÉ ✗")
    print("=" * 70)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
