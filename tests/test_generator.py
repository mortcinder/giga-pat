#!/usr/bin/env python3
"""
Script de test du generator HTML
"""

import sys
import logging
import yaml
import json
from pathlib import Path
from datetime import datetime

# Ajouter le répertoire parent au path pour importer tools
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.generator import ReportGenerator

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

def load_analysis_data():
    """Charge les données d'analyse"""
    analysis_path = Path(__file__).parent / "generated" / "patrimoine_analysis.json"
    with open(analysis_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    print("=" * 70)
    print("TEST DU GENERATOR HTML - Patrimoine Analyzer v1.0.0")
    print("=" * 70)
    print()

    setup_logging()

    # Chargement config
    config = load_config()

    # Ajuster les chemins pour être relatifs au script
    base_dir = Path(__file__).parent
    for key in config["paths"]:
        config["paths"][key] = str(base_dir / config["paths"][key])

    # Chargement données d'analyse
    try:
        analysis_data = load_analysis_data()
        print(f"✓ Données d'analyse chargées")
        print(f"  - Patrimoine total : {analysis_data['synthese']['patrimoine_total']:,.0f}€")
        print(f"  - Score global : {analysis_data['synthese']['score_global']}/10")
    except FileNotFoundError:
        print("✗ ERREUR : patrimoine_analysis.json introuvable")
        print("  → Exécutez d'abord: python test_analyzer.py")
        return 1

    # Génération timestamp
    timestamp = datetime.now().strftime(config["generator"]["date_format"])

    # Création du generator
    generator = ReportGenerator(config)

    # Génération HTML
    print()
    try:
        output_path = generator.generate(analysis_data, timestamp)

        print()
        print("=" * 70)
        print("RÉSULTATS DE LA GÉNÉRATION")
        print("=" * 70)
        print(f"✓ Rapport HTML généré avec succès")
        print()
        print(f"📄 Fichier : {output_path}")
        print()

        # Statistiques
        output_file = Path(output_path)
        if output_file.exists():
            size_kb = output_file.stat().st_size / 1024
            print(f"📊 Taille : {size_kb:.1f} KB")
            
            # Compter les lignes
            with open(output_file, 'r', encoding='utf-8') as f:
                lines = len(f.readlines())
            print(f"📊 Lignes HTML : {lines}")
        
        print()
        print("Pour visualiser le rapport, ouvrez le fichier HTML dans un navigateur.")
        print()

    except Exception as e:
        print(f"✗ ERREUR : {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
