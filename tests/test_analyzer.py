#!/usr/bin/env python3
"""
Script de test de l'analyzer complet
"""

import sys
import logging
import yaml
import json
from pathlib import Path

# Ajouter le répertoire parent au path pour importer tools
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.analyzer import PatrimoineAnalyzer

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

def load_input_data():
    """Charge les données d'input"""
    input_path = Path(__file__).parent / "generated" / "patrimoine_input.json"
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    print("=" * 70)
    print("TEST DE L'ANALYZER - Patrimoine Analyzer v1.0.0")
    print("=" * 70)
    print()

    setup_logging()

    # Chargement config
    config = load_config()

    # Ajuster les chemins pour être relatifs au script
    base_dir = Path(__file__).parent
    for key in config["paths"]:
        config["paths"][key] = str(base_dir / config["paths"][key])

    # Chargement input
    try:
        input_data = load_input_data()
        print(f"✓ Données input chargées : {input_data['patrimoine']['financier']['total']:,.0f}€")
    except FileNotFoundError:
        print("✗ ERREUR : patrimoine_input.json introuvable")
        print("  → Exécutez d'abord: python test_normalizer.py")
        return 1

    # Création de l'analyzer
    analyzer = PatrimoineAnalyzer(config)

    # Analyse
    print()
    try:
        result = analyzer.analyze(input_data)

        print()
        print("=" * 70)
        print("RÉSULTATS DE L'ANALYSE")
        print("=" * 70)
        print(f"✓ Patrimoine total : {result['synthese']['patrimoine_total']:,.0f}€")
        print(f"✓ Score global : {result['synthese']['score_global']}/10")
        print(f"  - Diversification : {result['synthese']['scores_details']['diversification']}/10")
        print(f"  - Résilience : {result['synthese']['scores_details']['resilience']}/10")
        print(f"  - Liquidité : {result['synthese']['scores_details']['liquidite']}/10")
        print(f"  - Fiscalité : {result['synthese']['scores_details']['fiscalite']}/10")
        print(f"  - Croissance : {result['synthese']['scores_details']['croissance']}/10")
        print()
        print(f"⚠️  Risque principal : {result['synthese']['risque_principal']}")
        print(f"💡 Priorité : {result['synthese']['priorites']}")
        print()
        print(f"📊 Répartition :")
        print(f"  - Établissements : {len(result['repartition']['par_etablissement'])}")
        print(f"  - Classes d'actifs : {len(result['repartition']['par_classe_actifs'])}")
        print()
        print(f"⚠️  Risques :")
        print(f"  - Critiques : {len(result['risques']['critiques'])}")
        print(f"  - Élevés : {len(result['risques']['eleves'])}")
        print(f"  - Moyens : {len(result['risques']['moyens'])}")
        print(f"  - Faibles : {len(result['risques']['faibles'])}")
        print()
        print(f"💡 Recommandations :")
        print(f"  - Prioritaires : {len(result['recommandations']['prioritaires'])}")
        print(f"  - Secondaires : {len(result['recommandations']['secondaires'])}")
        print(f"  - Long terme : {len(result['recommandations']['long_terme'])}")
        print()
        print(f"🧪 Stress tests : {len(result['stress_tests'])} scénarios")
        print(f"🔍 Recherches web : {result['meta']['web_searches_count']} requêtes")
        print(f"⏱️  Durée : {result['meta']['analysis_duration_seconds']}s")
        print()
        print(f"JSON généré : {base_dir / 'generated' / config['analyzer']['output_file']}")
        print()

    except Exception as e:
        print(f"✗ ERREUR : {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
