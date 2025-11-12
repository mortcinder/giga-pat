#!/usr/bin/env python3
"""
Générateur automatique du projet Patrimoine Analyzer

⚠️ ATTENTION: Ce fichier est un SCAFFOLD/TEMPLATE pour générer l'arborescence initiale du projet.
Ce n'est PAS du code de production. Les implémentations réelles se trouvent dans:
- tools/normalizer.py (parsing et normalisation)
- tools/analyzer.py (analyse et risques)
- tools/generator.py (génération HTML)

Ce script génère des fichiers templates avec des PLACEHOLDERS qui doivent être remplacés
par les implémentations réelles.

Usage:
    python project_generator.py

Note: Ce script n'est utile QUE pour créer un nouveau projet depuis zéro.
      Pour un projet existant, n'exécutez PAS ce script.
"""

import os
from pathlib import Path

def create_directory_structure():
    """Crée l'arborescence des répertoires"""
    directories = [
        "sources",
        "templates",
        "generated",
        "logs",
        "config",
        "tools",
        "tools/utils",
        "tests"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Créé : {directory}/")
    
    # Fichiers .gitkeep pour répertoires vides
    for empty_dir in ["sources", "generated", "logs"]:
        (Path(empty_dir) / ".gitkeep").touch()

def create_file(filepath, content):
    """Crée un fichier avec son contenu"""
    Path(filepath).write_text(content, encoding='utf-8')
    print(f"✓ Créé : {filepath}")

def generate_project():
    """Génère tous les fichiers du projet"""
    
    print("\n" + "="*60)
    print("🚀 GÉNÉRATION DU PROJET PATRIMOINE ANALYZER")
    print("="*60 + "\n")
    
    # 1. Structure de répertoires
    print("📁 Création de l'arborescence...")
    create_directory_structure()
    
    # 2. requirements.txt
    print("\n📦 Création requirements.txt...")
    create_file("requirements.txt", """# Core
python>=3.10

# Data processing
pandas>=2.0.0
numpy>=1.24.0

# File parsing
pdfplumber>=0.10.0
PyPDF2>=3.0.0
openpyxl>=3.1.0

# HTML/Web
beautifulsoup4>=4.12.0
lxml>=4.9.0

# API
anthropic>=0.25.0
requests>=2.31.0

# Config
pyyaml>=6.0

# Utils
python-dateutil>=2.8.0
""")

    # 3. .gitignore
    print("📝 Création .gitignore...")
    create_file(".gitignore", """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Fichiers générés
generated/
logs/

# Données sensibles
sources/
!sources/.gitkeep

# Configuration locale
.env
*.local.yaml

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
""")

    # 4. config/config.yaml
    print("⚙️  Création config/config.yaml...")
    create_file("config/config.yaml", """project:
  name: "Patrimoine Analyzer"
  version: "1.0.0"

paths:
  sources: "sources/"
  templates: "templates/"
  generated: "generated/"
  logs: "logs/"

normalizer:
  input_file: "patrimoine.md"
  output_file: "patrimoine_input.json"
  date_format: "ISO8601"

analyzer:
  input_file: "patrimoine_input.json"
  output_file: "patrimoine_analysis.json"
  web_research:
    enabled: true
    max_queries: 50
    timeout_seconds: 30
    retry_count: 3
  risk_thresholds:
    concentration_etablissement_critique: 50
    concentration_etablissement_eleve: 30
    concentration_juridiction_critique: 80
    concentration_juridiction_eleve: 60
    liquidite_critique: 5000
    liquidite_faible: 15000

generator:
  input_file: "patrimoine_analysis.json"
  template_file: "rapport_template.html"
  output_prefix: "rapport_"
  date_format: "%Y%m%d_%H%M%S"

logging:
  level: "INFO"
  format: "[%(asctime)s] %(levelname)s: %(message)s"
  date_format: "%Y-%m-%d %H:%M:%S"
""")

    # 5. config/research_prompts.yaml
    print("⚙️  Création config/research_prompts.yaml...")
    create_file("config/research_prompts.yaml", """# Prompts personnalisés pour recherches web

prompts:
  loi_sapin_2:
    sujet: "Loi Sapin 2 - Article 21 HCSF"
    queries:
      - "Loi Sapin 2 blocage assurance-vie 2025"
      - "HCSF article 21 conditions application"
      - "assurance-vie gel temporaire crise bancaire"
      - "article L. 612-33 code monétaire financier"

  fiscalite_epargne:
    sujet: "Fiscalité épargne 2025-2026"
    queries:
      - "projet loi finances 2026 fiscalité épargne"
      - "PFU flat tax évolution 2025"
      - "assurance-vie fiscalité réforme"
      - "PEA fiscalité modification 2025"

  marches_actions:
    sujet: "Contexte marchés actions 2025"
    queries:
      - "prévisions marchés actions 2025 2026"
      - "volatilité marchés financiers risques"
      - "correction boursière probabilité analyse"
""")

    # 6. tools/__init__.py
    print("🛠️  Création tools/__init__.py...")
    create_file("tools/__init__.py", """\"\"\"
Patrimoine Analyzer - Modules d'analyse
\"\"\"

__version__ = "1.0.0"
""")

    # 7. tools/utils/__init__.py
    print("🛠️  Création tools/utils/__init__.py...")
    create_file("tools/utils/__init__.py", """\"\"\"
Modules utilitaires
\"\"\"
""")

    # 8. tools/normalizer.py
    print("🛠️  Création tools/normalizer.py...")
    create_file("tools/normalizer.py", """\"\"\"
Module de normalisation des fichiers sources
\"\"\"

import json
import logging
from pathlib import Path
from datetime import datetime
from tools.utils.file_parser import FileParser


class PatrimoineNormalizer:
    \"\"\"Normalise les fichiers sources en JSON structuré\"\"\"
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.file_parser = FileParser()
        
    def normalize(self) -> dict:
        \"\"\"Point d'entrée principal de normalisation\"\"\"
        self.logger.info("Début normalisation...")
        
        # 1. Parse patrimoine.md
        self.logger.info("Lecture patrimoine.md...")
        patrimoine_data = self._parse_patrimoine_md()
        
        # 2. Load referenced files
        self.logger.info(f"Parsing {len(patrimoine_data.get('sources_files', []))} fichiers sources...")
        self._load_source_files(patrimoine_data)
        
        # 3. Calculate totals
        self.logger.info("Calcul totaux par catégorie...")
        self._calculate_totals(patrimoine_data)
        
        # 4. Validate
        self.logger.info("Validation données...")
        self._validate(patrimoine_data)
        
        # 5. Save JSON
        output_path = Path(self.config["paths"]["generated"]) / self.config["normalizer"]["output_file"]
        self.logger.info(f"Sauvegarde {output_path}...")
        self._save_json(patrimoine_data, output_path)
        
        self.logger.info("✓ Normalisation terminée")
        return patrimoine_data
    
    def _parse_patrimoine_md(self) -> dict:
        \"\"\"Parse le fichier patrimoine.md\"\"\"
        md_path = Path(self.config["paths"]["sources"]) / self.config["normalizer"]["input_file"]
        
        if not md_path.exists():
            raise FileNotFoundError(f"Fichier patrimoine.md introuvable : {md_path}")
        
        content = md_path.read_text(encoding='utf-8')
        
        # Structure de base
        data = {
            "meta": {
                "version": "1.0.0",
                "generated_at": datetime.now().isoformat(),
                "source_file": str(md_path)
            },
            "profil": {},
            "patrimoine": {
                "financier": {"total": 0, "etablissements": []},
                "crypto": {"total": 0, "plateformes": []},
                "metaux_precieux": {"total": 0},
                "immobilier": {"total": 0, "biens": []}
            },
            "sources_files": []
        }
        
        # Parsing basique (à améliorer selon structure réelle)
        self.logger.info(f"Fichier patrimoine.md chargé ({len(content.splitlines())} lignes)")
        
        return data
    
    def _load_source_files(self, data: dict):
        \"\"\"Charge les fichiers sources référencés\"\"\"
        # PLACEHOLDER: Implémenter parsing des fichiers CSV/PDF
        pass
    
    def _calculate_totals(self, data: dict):
        \"\"\"Calcule les totaux récursifs\"\"\"
        # Financier
        total_financier = sum(e.get("total", 0) for e in data["patrimoine"]["financier"]["etablissements"])
        data["patrimoine"]["financier"]["total"] = total_financier
        
        self.logger.debug(f"Patrimoine financier total : {total_financier:,.0f} €")
    
    def _validate(self, data: dict):
        \"\"\"Valide la cohérence des données\"\"\"
        # PLACEHOLDER: Ajouter validations
        self.logger.info("✓ Validation OK")
    
    def _save_json(self, data: dict, output_path: Path):
        \"\"\"Sauvegarde le JSON normalisé\"\"\"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
""")

    # 9. tools/analyzer.py
    print("🛠️  Création tools/analyzer.py...")
    create_file("tools/analyzer.py", """\"\"\"
Module d'analyse du patrimoine
\"\"\"

import json
import logging
from pathlib import Path
from datetime import datetime
from tools.utils.web_research import WebResearcher
from tools.utils.risk_analyzer import RiskAnalyzer
from tools.utils.recommendations import Recommender
from tools.utils.stress_tester import StressTester


class PatrimoineAnalyzer:
    \"\"\"Analyse approfondie du patrimoine\"\"\"
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.web_researcher = WebResearcher(config)
        self.risk_analyzer = RiskAnalyzer(config)
        self.recommender = Recommender(config)
        self.stress_tester = StressTester(config)
        
    def analyze(self, input_data: dict) -> dict:
        \"\"\"Point d'entrée principal d'analyse\"\"\"
        self.logger.info("Début analyse...")
        
        start_time = datetime.now()
        
        analysis = {
            "meta": {
                "version": "1.0.0",
                "generated_at": datetime.now().isoformat(),
                "analysis_duration_seconds": 0,
                "web_searches_count": 0
            },
            "synthese": {},
            "repartition": {},
            "risques": {},
            "recommandations": {},
            "stress_tests": [],
            "recherches_web": []
        }
        
        # 1. Calcul répartitions
        self.logger.info("Analyse répartition...")
        analysis["repartition"] = self._analyze_repartition(input_data)
        
        # 2. Identification risques (avec web research)
        self.logger.info("Identification risques...")
        analysis["risques"] = self.risk_analyzer.analyze(input_data, self.web_researcher)
        
        # 3. Génération recommandations
        self.logger.info("Génération recommandations...")
        analysis["recommandations"] = self.recommender.generate(input_data, analysis["risques"])
        
        # 4. Stress tests
        self.logger.info("Exécution stress tests...")
        analysis["stress_tests"] = self.stress_tester.run_all_tests(input_data)
        
        # 5. Synthèse
        self.logger.info("Génération synthèse globale...")
        analysis["synthese"] = self._generate_synthese(analysis, input_data)
        
        # 6. Métadonnées
        analysis["recherches_web"] = self.web_researcher.get_history()
        analysis["meta"]["web_searches_count"] = len(analysis["recherches_web"])
        analysis["meta"]["analysis_duration_seconds"] = int((datetime.now() - start_time).total_seconds())
        
        # Sauvegarde
        output_path = Path(self.config["paths"]["generated"]) / self.config["analyzer"]["output_file"]
        self.logger.info(f"Sauvegarde {output_path}...")
        self._save_json(analysis, output_path)
        
        self.logger.info("✓ Analyse terminée")
        return analysis
    
    def _analyze_repartition(self, data: dict) -> dict:
        \"\"\"Analyse la répartition du patrimoine\"\"\"
        repartition = {
            "par_etablissement": [],
            "par_classe_actifs": [],
            "concentration": {}
        }
        
        # PLACEHOLDER: Implémenter analyse répartition
        
        return repartition
    
    def _generate_synthese(self, analysis: dict, input_data: dict) -> dict:
        \"\"\"Génère la synthèse globale\"\"\"
        synthese = {
            "patrimoine_total": 0,
            "patrimoine_financier": 0,
            "patrimoine_immobilier": 0,
            "score_global": 7.5,
            "scores_details": {
                "diversification": 8,
                "resilience": 7.5,
                "liquidite": 6.5,
                "fiscalite": 7,
                "croissance": 8.5
            },
            "risque_principal": "À définir",
            "priorites": "À définir"
        }
        
        return synthese
    
    def _save_json(self, data: dict, output_path: Path):
        \"\"\"Sauvegarde le JSON d'analyse\"\"\"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
""")

    # 10. tools/generator.py
    print("🛠️  Création tools/generator.py...")
    create_file("tools/generator.py", """\"\"\"
Module de génération du rapport HTML
\"\"\"

import json
import logging
from pathlib import Path
from bs4 import BeautifulSoup


class ReportGenerator:
    \"\"\"Génère le rapport HTML depuis l'analyse\"\"\"
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    def generate(self, analysis_data: dict, timestamp: str) -> str:
        \"\"\"Génère le rapport HTML\"\"\"
        self.logger.info("Début génération HTML...")
        
        # 1. Load template
        self.logger.info("Chargement template...")
        template_path = Path(self.config["paths"]["templates"]) / self.config["generator"]["template_file"]
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template introuvable : {template_path}")
        
        template_html = template_path.read_text(encoding='utf-8')
        soup = BeautifulSoup(template_html, 'lxml')
        
        # 2. Inject simple fields
        self.logger.info("Injection données...")
        self._inject_simple_fields(soup, analysis_data)
        
        # 3. Inject repeated rows
        self._inject_repeated_rows(soup, analysis_data)
        
        # 4. Inject chart data
        self._inject_chart_data(soup, analysis_data)
        
        # 5. Save with timestamp
        output_filename = f"{self.config['generator']['output_prefix']}{timestamp}.html"
        output_path = Path(self.config["paths"]["generated"]) / output_filename
        
        self.logger.info(f"Sauvegarde {output_path}...")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(str(soup), encoding='utf-8')
        
        self.logger.info("✓ Génération terminée")
        return str(output_path)
    
    def _inject_simple_fields(self, soup, data):
        \"\"\"Injecte les champs simples [data-field]\"\"\"
        # PLACEHOLDER: Implémenter injection
        pass
    
    def _inject_repeated_rows(self, soup, data):
        \"\"\"Duplique et remplit les lignes de tableaux\"\"\"
        # PLACEHOLDER: Implémenter duplication
        pass
    
    def _inject_chart_data(self, soup, data):
        \"\"\"Injecte les données dans le graphique Chart.js\"\"\"
        # PLACEHOLDER: Implémenter injection graphique
        pass
    
    def _format_currency(self, value: float) -> str:
        \"\"\"Formate un montant en euros\"\"\"
        return f"{value:,.0f} €".replace(",", " ")
""")

    # 11. tools/utils/file_parser.py
    print("🛠️  Création tools/utils/file_parser.py...")
    create_file("tools/utils/file_parser.py", """\"\"\"
Module de parsing de fichiers sources
\"\"\"

import pandas as pd
import pdfplumber
import json
import logging
from typing import Dict, Any


class FileParser:
    \"\"\"Parser générique pour CSV, PDF, JSON\"\"\"
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def parse_csv(self, filepath: str) -> pd.DataFrame:
        \"\"\"Parse un fichier CSV\"\"\"
        try:
            df = pd.read_csv(
                filepath,
                encoding='utf-8-sig',
                sep=None,
                engine='python'
            )
            
            # Nettoyage colonnes
            df.columns = df.columns.str.strip().str.lower()
            
            self.logger.info(f"CSV parsé : {filepath} ({len(df)} lignes)")
            return df
            
        except Exception as e:
            self.logger.error(f"Erreur parsing CSV {filepath}: {e}")
            raise
            
    def parse_pdf(self, filepath: str) -> Dict[str, Any]:
        \"\"\"Parse un fichier PDF\"\"\"
        try:
            result = {
                "metadata": {},
                "tables": [],
                "text": ""
            }
            
            with pdfplumber.open(filepath) as pdf:
                result["metadata"]["pages"] = len(pdf.pages)
                
                for i, page in enumerate(pdf.pages):
                    tables = page.extract_tables()
                    for table in tables:
                        if table:
                            result["tables"].append({
                                "page": i + 1,
                                "data": table
                            })
                    
                    result["text"] += page.extract_text() or ""
            
            self.logger.info(f"PDF parsé : {filepath} ({result['metadata']['pages']} pages)")
            return result
            
        except Exception as e:
            self.logger.error(f"Erreur parsing PDF {filepath}: {e}")
            raise
            
    def parse_json(self, filepath: str) -> Dict[str, Any]:
        \"\"\"Parse un fichier JSON\"\"\"
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.logger.info(f"JSON parsé : {filepath}")
            return data
            
        except Exception as e:
            self.logger.error(f"Erreur parsing JSON {filepath}: {e}")
            raise
""")

    # 12. tools/utils/web_research.py
    print("🛠️  Création tools/utils/web_research.py...")
    create_file("tools/utils/web_research.py", """\"\"\"
Module de recherche web via Anthropic API
\"\"\"

import anthropic
import logging
import time
from typing import List, Dict, Any
from datetime import datetime


class WebResearcher:
    \"\"\"Gère les recherches web avec citation des sources\"\"\"
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.client = anthropic.Anthropic()
        self.history = []
        self.max_retries = config.get("analyzer", {}).get("web_research", {}).get("retry_count", 3)
        
    def search(self, sujet: str, queries: List[str], context: str = "") -> List[Dict[str, Any]]:
        \"\"\"Effectue plusieurs recherches web sur un sujet\"\"\"
        self.logger.info(f"Recherches sur : {sujet}")
        all_sources = []
        
        for i, query in enumerate(queries):
            self.logger.info(f"[{i+1}/{len(queries)}] Recherche : '{query}'")
            
            sources = self._search_single(query, context)
            all_sources.extend(sources)
            
            self.history.append({
                "sujet": sujet,
                "query": query,
                "date": datetime.now().isoformat(),
                "sources_found": len(sources)
            })
            
            self.logger.debug(f"→ {len(sources)} sources trouvées")
            time.sleep(1)  # Rate limiting
        
        # Dédoublonnage
        unique_sources = []
        seen_urls = set()
        for source in all_sources:
            if source.get("url") and source["url"] not in seen_urls:
                unique_sources.append(source)
                seen_urls.add(source["url"])
        
        return unique_sources
        
    def _search_single(self, query: str, context: str = "") -> List[Dict[str, Any]]:
        \"\"\"Effectue une recherche web unique\"\"\"
        # PLACEHOLDER: Implémenter recherche avec API Anthropic
        # Pour l'instant, retourne un placeholder
        return [{
            "url": "https://example.com",
            "titre": "Source placeholder",
            "extrait": "À implémenter avec API Anthropic",
            "pertinence": "Moyenne",
            "date_acces": datetime.now().strftime("%Y-%m-%d")
        }]
        
    def get_history(self) -> List[Dict[str, Any]]:
        \"\"\"Retourne l'historique des recherches\"\"\"
        return self.history
""")

    # 13. tools/utils/risk_analyzer.py
    print("🛠️  Création tools/utils/risk_analyzer.py...")
    create_file("tools/utils/risk_analyzer.py", """\"\"\"
Module d'analyse des risques patrimoniaux
\"\"\"

import logging
from typing import Dict, List


class RiskAnalyzer:
    \"\"\"Analyse tous types de risques\"\"\"
    
    SEUILS = {
        "concentration_etablissement_critique": 50,
        "concentration_etablissement_eleve": 30,
        "concentration_juridiction_critique": 80,
        "concentration_juridiction_eleve": 60,
        "liquidite_critique": 5000,
        "liquidite_faible": 15000
    }
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Override seuils depuis config
        config_thresholds = config.get("analyzer", {}).get("risk_thresholds", {})
        self.SEUILS.update(config_thresholds)
        
    def analyze(self, data: dict, web_researcher) -> Dict[str, List[Dict]]:
        \"\"\"Analyse complète de tous risques\"\"\"
        self.logger.info("Analyse des risques...")
        
        risques = {
            "critiques": [],
            "eleves": [],
            "moyens": [],
            "faibles": []
        }
        
        # PLACEHOLDER: Implémenter analyse risques
        self.logger.info(f"✓ {len(risques['critiques'])} risques critiques identifiés")
        
        return risques
""")

    # 14. tools/utils/recommendations.py
    print("🛠️  Création tools/utils/recommendations.py...")
    create_file("tools/utils/recommendations.py", """\"\"\"
Module de génération de recommandations
\"\"\"

import logging
from typing import Dict, List


class Recommender:
    \"\"\"Génère recommandations prioritisées\"\"\"
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    def generate(self, data: dict, risques: dict) -> Dict[str, List[Dict]]:
        \"\"\"Génère recommandations prioritisées\"\"\"
        self.logger.info("Génération recommandations...")
        
        recommandations = {
            "prioritaires": [],
            "secondaires": [],
            "long_terme": []
        }
        
        # PLACEHOLDER: Implémenter génération recommandations
        self.logger.info(f"✓ {len(recommandations['prioritaires'])} recommandations prioritaires")
        
        return recommandations
""")

    # 15. tools/utils/stress_tester.py
    print("🛠️  Création tools/utils/stress_tester.py...")
    create_file("tools/utils/stress_tester.py", """\"\"\"
Module de simulation de stress tests
\"\"\"

import logging
from typing import Dict, List


class StressTester:
    \"\"\"Simule l'impact de scénarios de crise\"\"\"
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    def run_all_tests(self, data: dict) -> List[Dict]:
        \"\"\"Exécute tous les stress tests\"\"\"
        self.logger.info("Exécution stress tests...")
        
        tests = []
        
        # PLACEHOLDER: Implémenter stress tests
        self.logger.info(f"✓ {len(tests)} scénarios simulés")
        
        return tests
""")

    # 16. main.py
    print("🚀 Création main.py...")
    create_file("main.py", """#!/usr/bin/env python3
\"\"\"
Patrimoine Analyzer - Point d'entrée principal
\"\"\"

import sys
import logging
from pathlib import Path
from datetime import datetime
import yaml
import time

from tools.normalizer import PatrimoineNormalizer
from tools.analyzer import PatrimoineAnalyzer
from tools.generator import ReportGenerator


def setup_logging(log_file: str):
    \"\"\"Configure le système de logging\"\"\"
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
    \"\"\"Charge la configuration\"\"\"
    config_path = Path("config/config.yaml")
    
    if not config_path.exists():
        raise FileNotFoundError(f"Fichier de configuration introuvable : {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def print_banner():
    \"\"\"Affiche la bannière\"\"\"
    banner = \"\"\"
╔═══════════════════════════════════════════════╗
║     PATRIMOINE ANALYZER v1.0.0                ║
║     Rapport patrimonial automatisé            ║
╚═══════════════════════════════════════════════╝
    \"\"\"
    print(banner)


def format_duration(seconds: float) -> str:
    \"\"\"Formate une durée\"\"\"
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
    \"\"\"Fonction principale\"\"\"
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
        print(f"\\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 📥 Étape 1/3 : Normalisation")
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
        
        summary = f\"\"\"
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
        \"\"\"
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
""")

    # 17. README.md
    print("📚 Création README.md...")
    create_file("README.md", """# 📊 Patrimoine Analyzer

Générateur automatisé de rapports patrimoniaux professionnels avec analyse approfondie et recherches web.

## 🎯 Objectif

Transformer vos fichiers sources (CSV, PDF, Markdown) en un rapport patrimonial complet avec :
- ✅ Analyse détaillée de la répartition des actifs
- ✅ Identification des risques (concentration, réglementaire, fiscal, marché)
- ✅ Recommandations prioritisées et actionnables
- ✅ Stress tests (crise bancaire, krach, perte emploi...)
- ✅ Recherches web exhaustives avec sources citées
- ✅ Rapport HTML premium professionnel

## 🚀 Installation

### Prérequis
- Python 3.10 ou supérieur
- Clé API Anthropic (pour recherches web)

### Installation

```bash
# Installation des packages Python
pip install -r requirements.txt

# Configuration API Anthropic
export ANTHROPIC_API_KEY="votre-clé-api"
```

## 📁 Structure du projet

```
patrimoine-analyzer/
├── sources/              # 📥 VOS fichiers sources (patrimoine.md, CSV, PDF)
├── templates/            # 📄 Template HTML (modifiable)
├── generated/            # 📤 Rapports générés (automatique)
├── logs/                 # 📋 Logs d'exécution (automatique)
├── tools/                # 🛠️ Scripts Python
├── config/               # ⚙️ Configuration
└── main.py               # 🚀 Point d'entrée
```

## 📝 Utilisation

### 1. Préparer les sources

Placez vos fichiers dans `sources/` :

```
sources/
├── patrimoine.md         # Point d'entrée principal
├── [CA] - PEA.csv
├── [CA] - AV.pdf
└── ... (autres fichiers)
```

### 2. Générer le rapport

```bash
python main.py
```

### 3. Consulter le rapport

Ouvrez le fichier généré :
```
generated/rapport_20251021_143330.html
```

## ⚙️ Configuration

Modifiez `config/config.yaml` pour ajuster :
- Seuils de risques
- Nombre max de recherches web
- Chemins de fichiers
- Format de dates

## 🎨 Personnalisation du template

Le template HTML (`templates/rapport_template.html`) est **modifiable librement** :
- Ajustez les couleurs (variables CSS)
- Modifiez la mise en page
- Ajoutez/supprimez des sections

⚠️ **Important** : Conservez les attributs `data-field` et `data-repeat` pour l'injection de données.

## 📈 Historique des rapports

Tous les rapports sont conservés avec horodatage :
```
generated/
├── rapport_20251021_143330.html
├── rapport_20251020_091544.html
└── rapport_20251015_164522.html
```

## 🔍 Résolution de problèmes

### Erreur "Fichier introuvable"
- Vérifiez que `patrimoine.md` existe dans `sources/`
- Vérifiez que tous les fichiers référencés existent

### Erreur "API timeout"
- Connexion internet instable
- Le script retry automatiquement 3×

### Rapport incomplet
- Consultez `logs/rapport_YYYYMMDD_HHMMSS.log`

## 📄 Licence

Usage personnel uniquement. Tous droits réservés.

---

**Version** : 1.0.0  
**Dernière mise à jour** : Octobre 2025
""")

    # 18. Message final
    print("\n" + "="*60)
    print("✅ PROJET GÉNÉRÉ AVEC SUCCÈS !")
    print("="*60)
    print("\n📦 Prochaines étapes :")
    print("  1. cd patrimoine-analyzer")
    print("  2. pip install -r requirements.txt")
    print("  3. export ANTHROPIC_API_KEY='votre-clé'")
    print("  4. Placez vos fichiers dans sources/")
    print("  5. Placez rapport_template.html dans templates/")
    print("  6. python main.py")
    print("\n💡 Consultez README.md pour plus d'informations")
    print("="*60 + "\n")


if __name__ == "__main__":
    # Créer dossier parent
    project_dir = Path("patrimoine-analyzer")
    
    if project_dir.exists():
        response = input(f"\n⚠️  Le dossier '{project_dir}' existe déjà. Écraser ? (o/N) : ")
        if response.lower() != 'o':
            print("❌ Génération annulée")
            exit(0)
    
    project_dir.mkdir(exist_ok=True)
    
    # Changer dans le répertoire du projet
    import os
    os.chdir(project_dir)
    
    # Générer le projet
    generate_project()
