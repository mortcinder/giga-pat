#!/usr/bin/env python3
"""
Script de test de l'intégration Brave Search API
"""

import sys
import os
import logging
import yaml
from pathlib import Path
from dotenv import load_dotenv

# Ajouter le répertoire parent (racine du projet) au path pour importer tools
sys.path.insert(0, str(Path(__file__).parent.parent))

# Charger les variables d'environnement depuis .env (à la racine)
load_dotenv(Path(__file__).parent.parent / ".env")

from tools.utils.web_research import WebResearcher

def setup_logging():
    """Configure le logging"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def load_config():
    """Charge la configuration"""
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def main():
    print("=" * 70)
    print("TEST DE L'INTÉGRATION BRAVE SEARCH API")
    print("=" * 70)
    print()

    setup_logging()

    # Vérifier la clé API
    api_key = os.environ.get("BRAVE_API_KEY")
    if not api_key:
        print("❌ ERREUR: Variable d'environnement BRAVE_API_KEY non définie")
        print()
        print("Pour définir votre clé API Brave:")
        print("  export BRAVE_API_KEY='votre_clé_api_ici'")
        print()
        print("Pour obtenir une clé API gratuite:")
        print("  https://api.search.brave.com/app/dashboard")
        print()
        return 1

    print(f"✓ Clé API Brave détectée: {api_key[:8]}...{api_key[-4:]}")
    print()

    # Chargement config
    config = load_config()

    # Création du WebResearcher
    researcher = WebResearcher(config)

    if not researcher.enabled:
        print("❌ WebResearcher désactivé")
        return 1

    print("✓ WebResearcher initialisé")
    print()

    # Test de recherche simple
    print("Test 1: Recherche simple")
    print("-" * 70)

    test_queries = [
        "Loi Sapin 2 assurance-vie France",
    ]

    try:
        sources = researcher.search(
            sujet="Test Loi Sapin 2",
            queries=test_queries,
            context="Test d'intégration Brave Search API"
        )

        print()
        print(f"✓ Recherche effectuée avec succès")
        print(f"  Nombre de sources: {len(sources)}")
        print()

        if sources:
            print("Aperçu des sources:")
            for i, source in enumerate(sources[:3], 1):
                print(f"  [{i}] {source.get('titre', 'N/A')[:60]}")
                print(f"      URL: {source.get('url', 'N/A')[:70]}")
                print(f"      Pertinence: {source.get('pertinence', 'N/A')}")
                print()

    except Exception as e:
        print(f"❌ ERREUR lors de la recherche: {e}")
        import traceback
        traceback.print_exc()
        return 1

    print()
    print("=" * 70)
    print("TEST RÉUSSI ✓")
    print("=" * 70)

    return 0

if __name__ == "__main__":
    sys.exit(main())
