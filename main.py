#!/usr/bin/env python3
"""
Patrimoine Analyzer - Point d'entrée principal
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
import yaml
import time
from dotenv import load_dotenv

from tools.normalizer import PatrimoineNormalizer
from tools.analyzer import PatrimoineAnalyzer
from tools.generator import ReportGenerator


def setup_logging(log_file: str):
    """Configure le système de logging"""
    Path("logs").mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)


def load_config() -> dict:
    """Charge la configuration"""
    config_path = Path("config/config.yaml")
    
    if not config_path.exists():
        raise FileNotFoundError(f"Fichier de configuration introuvable : {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def print_banner():
    """Affiche la bannière"""
    banner = """
╔═══════════════════════════════════════════════╗
║     PATRIMOINE ANALYZER v2.1.0                ║
║     Rapport patrimonial automatisé            ║
╚═══════════════════════════════════════════════╝
    """
    print(banner)


def format_duration(seconds: float) -> str:
    """Formate une durée"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def main():
    """Fonction principale"""
    # Charger les variables d'environnement depuis .env
    load_dotenv()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/rapport_{timestamp}.log"

    logger = setup_logging(log_file)
    print_banner()

    start_time = time.time()

    try:
        # Chargement configuration
        logger.info("Chargement configuration...")
        config = load_config()
        
        # ÉTAPE 1 : NORMALISATION
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 📥 Étape 1/3 : Normalisation")
        step1_start = time.time()
        
        normalizer = PatrimoineNormalizer(config)
        patrimoine_input = normalizer.normalize()
        
        step1_duration = time.time() - step1_start
        print(f"  ⏱️  Durée : {step1_duration:.1f}s")
        
        # ÉTAPE 2 : ANALYSE
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🔍 Étape 2/3 : Analyse approfondie")
        step2_start = time.time()
        
        analyzer = PatrimoineAnalyzer(config)
        patrimoine_analysis = analyzer.analyze(patrimoine_input)
        
        step2_duration = time.time() - step2_start
        print(f"  ⏱️  Durée : {format_duration(step2_duration)}")
        
        # ÉTAPE 3 : GÉNÉRATION
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 📄 Étape 3/3 : Génération rapport HTML")
        step3_start = time.time()
        
        generator = ReportGenerator(config)
        rapport_path = generator.generate(patrimoine_analysis, timestamp)
        
        step3_duration = time.time() - step3_start
        print(f"  ⏱️  Durée : {step3_duration:.1f}s")
        
        # RÉSUMÉ
        total_duration = time.time() - start_time
        
        summary = f"""
╔═══════════════════════════════════════════════╗
║  ✅ RAPPORT GÉNÉRÉ AVEC SUCCÈS                ║
╠═══════════════════════════════════════════════╣
║  📊 Patrimoine total : {patrimoine_analysis['synthese']['patrimoine_total']:,.0f} €              ║
║  ⚠️  Risques critiques : {len(patrimoine_analysis['risques']['critiques'])}                    ║
║  💡 Recommandations : {len(patrimoine_analysis['recommandations']['prioritaires'])}                       ║
║  📁 Fichier : {Path(rapport_path).name:<30} ║
║  📋 Log : {log_file:<38} ║
╚═══════════════════════════════════════════════╝

⏱️  Durée totale : {format_duration(total_duration)}
        """
        print(summary)
        
        logger.info("=" * 60)
        logger.info("EXÉCUTION TERMINÉE AVEC SUCCÈS")
        logger.info("=" * 60)
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"❌ Fichier introuvable : {e}")
        return 1
        
    except Exception as e:
        logger.error(f"❌ Erreur inattendue : {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
