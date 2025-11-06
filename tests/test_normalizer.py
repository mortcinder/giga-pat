#!/usr/bin/env python3
"""
Script de test du normalizer
"""

import sys
import logging
import yaml
from pathlib import Path

# Ajouter le répertoire parent (racine du projet) au path pour importer tools
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.normalizer import PatrimoineNormalizer

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

def main():
    print("=" * 60)
    print("TEST DU NORMALIZER - Patrimoine Analyzer v1.0.0")
    print("=" * 60)
    print()
    
    setup_logging()
    
    # Chargement config
    config = load_config()
    
    # Ajuster les chemins pour être relatifs au script
    base_dir = Path(__file__).parent
    for key in config["paths"]:
        config["paths"][key] = str(base_dir / config["paths"][key])
    
    # Création du normalizer
    normalizer = PatrimoineNormalizer(config)
    
    # Normalisation
    try:
        result = normalizer.normalize()
        
        print()
        print("=" * 60)
        print("RÉSULTATS")
        print("=" * 60)
        print(f"✓ Profil : {result['profil'].get('genre', 'N/A')}, {result['profil'].get('age', 'N/A')} ans")
        print(f"✓ Établissements financiers : {len(result['patrimoine']['financier']['etablissements'])}")
        print(f"✓ Total financier : {result['patrimoine']['financier']['total']:,.2f} €")
        print(f"✓ Total crypto : {result['patrimoine']['crypto']['total']:,.2f} €")
        print(f"✓ Total métaux : {result['patrimoine']['metaux_precieux']['total']:,.2f} €")
        print(f"✓ Fichiers sources : {len(result['sources_files'])}")
        print()
        print(f"JSON généré : {base_dir / config['normalizer']['output_file']}")
        print()
        
    except Exception as e:
        print(f"✗ ERREUR : {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
