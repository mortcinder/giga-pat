"""
Recherche web pour etablir regles metier CGP
Ces regles seront ensuite utilisees sans re-validation
"""
import os
import sys
import yaml
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
load_dotenv()

from tools.utils.tavily_search import TavilySearcher

def research_cgp_rules():
    """Recherche systematique des regles metier CGP"""

    config = {"analyzer": {"web_research": {"timeout_seconds": 30}}}
    tavily = TavilySearcher(config)

    if not tavily.enabled:
        print("ERREUR: TAVILY_API_KEY non definie")
        return

    print("="*80)
    print("RECHERCHE DES REGLES METIER CGP")
    print("="*80)

    rules = {
        "version": "1.0.0",
        "date_recherche": datetime.now().strftime("%Y-%m-%d"),
        "description": "Regles metier CGP etablies par recherche web",
        "maintenance": "Revision trimestrielle",
        "regles": {}
    }

    # =========================================================================
    # 1. COMPTES INEFFICACES
    # =========================================================================

    print("\n" + "="*80)
    print("CATEGORIE 1: COMPTES INEFFICACES")
    print("="*80)

    queries_comptes = [
        "quand fermer compte bancaire faible montant CGP",
        "livret doublon combien minimum garder conseiller patrimoine",
        "PEA montant minimum viable frais",
        "assurance-vie frais gestion trop eleves seuil"
    ]

    sources_comptes = []
    for q in queries_comptes:
        print(f"\n  Recherche: {q}")
        results = tavily.search(q, search_depth="advanced", max_results=5)
        sources_comptes.extend(results)
        print(f"    -> {len(results)} sources")

    print(f"\n  Total: {len(sources_comptes)} sources")

    # Extraire insights (skip print pour eviter encodage)

    rules["regles"]["comptes_inefficaces"] = {
        "description": "Regles pour detecter comptes a faible valeur ajoutee",
        "sources": [{"url": s["url"], "titre": s["titre"], "extrait": s.get("extrait", "")} for s in sources_comptes[:10]],
        "date_etablissement": datetime.now().strftime("%Y-%m-%d"),
        "regles_identifiees": "A determiner apres analyse manuelle des sources"
    }

    # =========================================================================
    # 2. DIVERSIFICATION BANCAIRE
    # =========================================================================

    print("\n" + "="*80)
    print("CATEGORIE 2: DIVERSIFICATION BANCAIRE")
    print("="*80)

    queries_diversif = [
        "diversification bancaire combien etablissements recommandation CGP",
        "concentration bancaire limite pourcentage patrimoine",
        "nombre banques optimal securiser patrimoine",
        "risque concentration bancaire seuil critique"
    ]

    sources_diversif = []
    for q in queries_diversif:
        print(f"\n  Recherche: {q}")
        results = tavily.search(q, search_depth="advanced", max_results=5)
        sources_diversif.extend(results)
        print(f"    -> {len(results)} sources")

    print(f"\n  Total: {len(sources_diversif)} sources")

    rules["regles"]["diversification_bancaire"] = {
        "description": "Regles de diversification entre etablissements",
        "sources": [{"url": s["url"], "titre": s["titre"], "extrait": s.get("extrait", "")} for s in sources_diversif[:10]],
        "date_etablissement": datetime.now().strftime("%Y-%m-%d"),
        "regles_identifiees": "A determiner apres analyse manuelle des sources"
    }

    # =========================================================================
    # 3. ALLOCATION PAR PROFIL
    # =========================================================================

    print("\n" + "="*80)
    print("CATEGORIE 3: ALLOCATION PAR PROFIL")
    print("="*80)

    for profil in ["dynamique", "equilibre", "prudent"]:
        print(f"\n  --- PROFIL: {profil.upper()} ---")

        queries_profil = [
            f"allocation actions profil {profil} pourcentage CGP",
            f"portefeuille {profil} repartition actifs recommandation",
            f"investisseur {profil} allocation obligations liquidites"
        ]

        sources_profil = []
        for q in queries_profil:
            print(f"\n    Recherche: {q}")
            results = tavily.search(q, search_depth="advanced", max_results=5)
            sources_profil.extend(results)
            print(f"      -> {len(results)} sources")

        print(f"\n    Total: {len(sources_profil)} sources")

        rules["regles"][f"allocation_{profil}"] = {
            "description": f"Allocation d'actifs pour profil {profil}",
            "sources": [{"url": s["url"], "titre": s["titre"], "extrait": s.get("extrait", "")} for s in sources_profil[:10]],
            "date_etablissement": datetime.now().strftime("%Y-%m-%d"),
            "regles_identifiees": "A determiner apres analyse manuelle des sources"
        }

    # =========================================================================
    # 4. FONDS D'URGENCE
    # =========================================================================

    print("\n" + "="*80)
    print("CATEGORIE 4: FONDS D'URGENCE")
    print("="*80)

    queries_urgence = [
        "fonds urgence combien mois depenses recommandation",
        "epargne precaution montant minimum CGP",
        "reserve liquidites pourcentage patrimoine"
    ]

    sources_urgence = []
    for q in queries_urgence:
        print(f"\n  Recherche: {q}")
        results = tavily.search(q, search_depth="advanced", max_results=5)
        sources_urgence.extend(results)
        print(f"    -> {len(results)} sources")

    print(f"\n  Total: {len(sources_urgence)} sources")

    rules["regles"]["fonds_urgence"] = {
        "description": "Regles pour fonds d'urgence et liquidites",
        "sources": [{"url": s["url"], "titre": s["titre"], "extrait": s.get("extrait", "")} for s in sources_urgence[:10]],
        "date_etablissement": datetime.now().strftime("%Y-%m-%d"),
        "regles_identifiees": "A determiner apres analyse manuelle des sources"
    }

    # =========================================================================
    # SAUVEGARDE
    # =========================================================================

    output_file = "config/cgp_rules_research.yaml"
    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(rules, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

    print(f"\n\n{'='*80}")
    print(f"RECHERCHE TERMINEE")
    print(f"{'='*80}")
    print(f"Fichier genere: {output_file}")
    print(f"Total sources collectees: {len(sources_comptes) + len(sources_diversif) + len(sources_urgence)}")
    print(f"\nProchaine etape: Analyser manuellement les sources et extraire regles concretes")

if __name__ == "__main__":
    research_cgp_rules()
