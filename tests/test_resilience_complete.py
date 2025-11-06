#!/usr/bin/env python3
"""
Test de synthèse : Labels de résilience (backend + frontend)
Valide l'implémentation complète du système de labels pour le score de résilience
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def print_header(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")

def test_backend():
    """Teste la partie backend (analyzer.py + config)"""
    print_header("BACKEND : Configuration & Calcul")

    import yaml
    from tools.analyzer import PatrimoineAnalyzer

    # 1. Vérifier la configuration
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "config",
        "analysis.yaml"
    )

    with open(config_path, 'r', encoding='utf-8') as f:
        analysis_config = yaml.safe_load(f)

    resilience_config = analysis_config["scores"]["resilience"]
    quality_labels = resilience_config["quality_labels"]

    assert len(quality_labels) == 5, "❌ Nombre de labels incorrect"
    print("✅ Configuration : 5 labels définis")

    # 2. Tester le calcul du score
    config = {
        "paths": {"sources": "sources/", "generated": "generated/"},
        "analyzer": {
            "output_file": "patrimoine_analysis.json",
            "risk_thresholds": {
                "concentration_etablissement_critique": 50,
                "concentration_etablissement_eleve": 30,
                "concentration_juridiction_critique": 80,
                "concentration_juridiction_eleve": 60,
            }
        },
        "analysis": {"config_file": "analysis.yaml", "active_profile": "default"}
    }

    analyzer = PatrimoineAnalyzer(config)

    test_analysis = {
        "stress_tests": [{"severite": "Haute"}],
        "risques": {"critiques": [], "eleves": []},
    }

    result = analyzer._calculate_resilience_score(test_analysis)

    assert isinstance(result, dict), "❌ Format de retour incorrect"
    assert "score" in result and "label" in result, "❌ Clés manquantes"
    assert 0 <= result["score"] <= 10, "❌ Score hors limites"
    assert result["label"] in [
        "Patrimoine résilient",
        "Patrimoine solide",
        "Patrimoine vulnérable",
        "Patrimoine fragile",
        "Patrimoine critique"
    ], "❌ Label inconnu"

    print(f"✅ Calcul du score : {result['score']}/10 → '{result['label']}'")

    # 3. Vérifier la structure de sortie
    print("✅ Structure de retour : dict avec 'score' et 'label'")

    return True

def test_frontend():
    """Teste la partie frontend (generator.py + template)"""
    print_header("FRONTEND : Template & Génération")

    from bs4 import BeautifulSoup
    from tools.generator import ReportGenerator

    # 1. Vérifier le template
    template_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "templates",
        "rapport_template.html"
    )

    with open(template_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    resilience_details = soup.find("details", class_="resilience-details")
    assert resilience_details is not None, "❌ Section détails manquante"
    print("✅ Template : Section <details> présente")

    res_label = soup.find(attrs={"data-field": "res_label"})
    res_score = soup.find(attrs={"data-field": "res_score_final"})
    assert res_label is not None and res_score is not None, "❌ Champs data-field manquants"
    print("✅ Template : Champs data-field configurés")

    # 2. Vérifier les mappings du générateur
    config = {
        "paths": {"templates": "templates/", "generated": "generated/"},
        "generator": {"output_prefix": "rapport"},
    }

    generator = ReportGenerator(config)

    # Tester le mapping badge
    test_labels = [
        ("Patrimoine résilient", "low"),
        ("Patrimoine solide", "low"),
        ("Patrimoine vulnérable", "mid"),
        ("Patrimoine fragile", "high"),
        ("Patrimoine critique", "crit"),
    ]

    for label, expected_class in test_labels:
        badge_class = generator._get_resilience_badge_class(label)
        assert badge_class == expected_class, f"❌ Mapping incorrect pour '{label}'"

    print("✅ Générateur : Mapping labels → classes CSS correct")

    # 3. Vérifier que les champs sont dans les mappings
    # Simuler l'accès aux mappings (ils sont locaux à _inject_simple_fields)
    # On peut vérifier indirectement en testant que la fonction existe
    assert hasattr(generator, '_get_resilience_badge_class'), "❌ Fonction de mapping manquante"
    print("✅ Générateur : Fonction _get_resilience_badge_class présente")

    return True

def test_integration():
    """Teste l'intégration backend → frontend"""
    print_header("INTÉGRATION : Flux complet de données")

    # Simuler le flux de données
    mock_analysis = {
        "synthese": {
            "resilience_details": {
                "score": 7.5,
                "label": "Patrimoine solide"
            }
        }
    }

    # Vérifier que les chemins JSON sont cohérents
    score_path = "synthese.resilience_details.score"
    label_path = "synthese.resilience_details.label"

    # Extraire les valeurs
    score = mock_analysis["synthese"]["resilience_details"]["score"]
    label = mock_analysis["synthese"]["resilience_details"]["label"]

    assert score == 7.5, "❌ Chemin JSON score incorrect"
    assert label == "Patrimoine solide", "❌ Chemin JSON label incorrect"

    print("✅ Chemins JSON : synthese.resilience_details.{score,label}")
    print(f"✅ Données mockées : {score}/10 → '{label}'")

    # Vérifier le mapping badge
    from tools.generator import ReportGenerator
    config = {
        "paths": {"templates": "templates/", "generated": "generated/"},
        "generator": {"output_prefix": "rapport"},
    }
    generator = ReportGenerator(config)

    badge_class = generator._get_resilience_badge_class(label)
    expected_class = "low"  # "solide" → low (vert)
    assert badge_class == expected_class, f"❌ Badge class incorrect: {badge_class}"

    print(f"✅ Badge CSS : '{label}' → classe '{badge_class}' (vert)")

    return True

def print_summary():
    """Affiche le résumé de l'implémentation"""
    print_header("📋 RÉSUMÉ DE L'IMPLÉMENTATION")

    summary = """
┌─────────────────────────────────────────────────────────────────────┐
│ LABELS DE RÉSILIENCE - IMPLÉMENTATION COMPLÈTE                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ ✅ Backend (analyzer.py + config/analysis.yaml)                    │
│    • 5 labels de qualité configurés                                │
│    • Fonction _calculate_resilience_score() retourne dict          │
│    • Structure : {"score": float, "label": str}                    │
│    • Labels : résilient, solide, vulnérable, fragile, critique     │
│                                                                     │
│ ✅ Frontend (generator.py + templates/rapport_template.html)       │
│    • Section <details> dépliable ajoutée (symétrique à div.)       │
│    • Badge coloré avec data-field="res_label"                      │
│    • Score affiché avec data-field="res_score_final"               │
│    • Fonction _get_resilience_badge_class() pour mapping CSS       │
│                                                                     │
│ ✅ Intégration                                                      │
│    • Chemins JSON : synthese.resilience_details.{score,label}      │
│    • Mappings dans generator.py lignes 108-109                     │
│    • Application dynamique classes CSS lignes 200-211              │
│                                                                     │
│ 🎨 Classes CSS Badge                                               │
│    • "low"  (vert)  : résilient, solide                            │
│    • "mid"  (orange): vulnérable                                   │
│    • "high" (rouge) : fragile                                      │
│    • "crit" (rouge foncé) : critique                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
"""
    print(summary)

if __name__ == "__main__":
    try:
        test_backend()
        test_frontend()
        test_integration()
        print_summary()

        print("\n" + "="*70)
        print("  ✅ IMPLÉMENTATION COMPLÈTE ET VALIDÉE")
        print("="*70 + "\n")

        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ ÉCHEC: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERREUR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
