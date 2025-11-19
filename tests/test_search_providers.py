#!/usr/bin/env python3
"""
Tests unitaires pour les search providers
"""

import sys
import os
import logging
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.utils.search_providers import (
    SearchProviderFactory,
    SearchParams,
    DDGSSearchProvider,
    ProviderConfig,
)


def setup_logging():
    """Configure le logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def test_ddgs_provider():
    """Test basique du provider DuckDuckGo (ne nécessite pas de clé API)"""
    print("\n" + "=" * 70)
    print("TEST: DuckDuckGo Search Provider")
    print("=" * 70)

    # Créer une config minimale pour DDGS
    config = ProviderConfig(
        name="ddgs",
        enabled=True,
        api_key=None,  # DDGS n'a pas besoin de clé
        rate_limit=2.0,
        timeout=20,
        retry_count=2,
        max_results=5,
        priority=4
    )

    try:
        provider = DDGSSearchProvider(config)
        print(f"✓ Provider créé: {provider.provider_name}")
        print(f"✓ Disponible: {provider.is_available()}")

        if provider.is_available():
            # Test de recherche simple
            params = SearchParams(
                query="Python programming",
                lang="fr",
                country="FR",
                max_results=3
            )

            print(f"\nRecherche: '{params.query}'")
            results = provider.search(params)

            print(f"✓ Résultats trouvés: {len(results)}")

            if results:
                print("\nAperçu des résultats:")
                for i, result in enumerate(results[:3], 1):
                    print(f"\n  [{i}] {result.title[:60]}")
                    print(f"      URL: {result.url[:70]}")
                    print(f"      Pertinence: {result.relevance}")
                    print(f"      Provider: {result.provider}")

            return True
        else:
            print("✗ Provider non disponible")
            return False

    except Exception as e:
        print(f"✗ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_factory():
    """Test de la Factory avec configuration minimale"""
    print("\n" + "=" * 70)
    print("TEST: SearchProviderFactory")
    print("=" * 70)

    # Config minimale (juste DDGS pour éviter besoin de clés API)
    config = {
        "analyzer": {
            "web_research": {
                "enabled": True,
                "provider": "ddgs",
                "enable_fallback": False,
                "default_rate_limit": 2.0,
                "default_timeout": 20,
                "default_retry_count": 2,
                "default_max_results": 5,
                "providers": {
                    "ddgs": {
                        "enabled": True,
                        "rate_limit": 2.0,
                        "timeout": 20,
                        "retry_count": 2,
                        "max_results": 5,
                        "priority": 1
                    }
                }
            }
        }
    }

    try:
        factory = SearchProviderFactory()
        print("✓ Factory créée")

        provider = factory.create_provider("ddgs", config)
        print(f"✓ Provider créé via factory: {provider.provider_name}")
        print(f"✓ Disponible: {provider.is_available()}")

        return True

    except Exception as e:
        print(f"✗ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 70)
    print("TESTS DES SEARCH PROVIDERS")
    print("=" * 70)

    setup_logging()

    results = []

    # Test 1: DDGS Provider
    results.append(("DDGS Provider", test_ddgs_provider()))

    # Test 2: Factory
    results.append(("Factory", test_factory()))

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
        print("TOUS LES TESTS ONT RÉUSSI ✓")
    else:
        print("CERTAINS TESTS ONT ÉCHOUÉ ✗")
    print("=" * 70)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
