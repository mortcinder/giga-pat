#!/usr/bin/env python3
"""
Test unitaire pour valider le fonctionnement de _calculate_resilience_score
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml

# Import minimal de la classe
from tools.analyzer import PatrimoineAnalyzer

def test_resilience_score_return_format():
    """Teste que _calculate_resilience_score retourne le bon format"""

    print("\n" + "="*60)
    print("TEST DU FORMAT DE RETOUR DU SCORE DE RÉSILIENCE")
    print("="*60 + "\n")

    # Configuration minimale
    config = {
        "paths": {
            "sources": "sources/",
            "generated": "generated/",
        },
        "analyzer": {
            "output_file": "patrimoine_analysis.json",
            "risk_thresholds": {
                "concentration_etablissement_critique": 50,
                "concentration_etablissement_eleve": 30,
                "concentration_juridiction_critique": 80,
                "concentration_juridiction_eleve": 60,
            }
        },
        "analysis": {
            "config_file": "analysis.yaml",
            "active_profile": "default"
        }
    }

    # Initialiser l'analyzer
    analyzer = PatrimoineAnalyzer(config)

    # Données de test - stress tests
    test_analysis = {
        "stress_tests": [
            {"nom": "Krach boursier", "severite": "Haute"},
            {"nom": "Hausse taux", "severite": "Moyenne"},
        ],
        "risques": {
            "critiques": [],  # 0 risque critique → bonus
            "eleves": [],
        }
    }

    # Test 1: Appeler la fonction
    print("🧪 Appel de _calculate_resilience_score...")
    result = analyzer._calculate_resilience_score(test_analysis)

    # Test 2: Vérifier que c'est un dict
    assert isinstance(result, dict), f"❌ Le retour devrait être un dict, pas {type(result)}"
    print("✅ Retourne un dictionnaire")

    # Test 3: Vérifier que "score" existe
    assert "score" in result, "❌ La clé 'score' manque dans le résultat"
    print(f"✅ Clé 'score' présente: {result['score']}")

    # Test 4: Vérifier que "label" existe
    assert "label" in result, "❌ La clé 'label' manque dans le résultat"
    print(f"✅ Clé 'label' présente: '{result['label']}'")

    # Test 5: Vérifier les types
    assert isinstance(result["score"], (int, float)), "❌ Le score devrait être un nombre"
    assert isinstance(result["label"], str), "❌ Le label devrait être une chaîne"
    print("✅ Types corrects (score: float, label: str)")

    # Test 6: Vérifier que le score est dans [0-10]
    assert 0 <= result["score"] <= 10, f"❌ Score hors limites: {result['score']}"
    print(f"✅ Score dans la plage [0-10]: {result['score']}/10")

    # Test 7: Vérifier que le label est cohérent avec le score
    score = result["score"]
    label = result["label"]

    expected_label_map = {
        (9, 10): "Patrimoine résilient",
        (7, 9): "Patrimoine solide",
        (5, 7): "Patrimoine vulnérable",
        (3, 5): "Patrimoine fragile",
        (0, 3): "Patrimoine critique",
    }

    expected_label = None
    for (min_s, max_s), lbl in expected_label_map.items():
        if min_s <= score < max_s or (score == 10 and max_s == 10):
            expected_label = lbl
            break

    assert label == expected_label, f"❌ Label incohérent: attendu '{expected_label}', obtenu '{label}' pour score {score}"
    print(f"✅ Label cohérent avec le score: '{label}'")

    # Test 8: Calculer le score attendu manuellement
    # Base: 8.0
    # Pénalité Haute: -2.0 (1 test haute sévérité)
    # Pénalité Moyenne: -0.5 (1 test moyenne sévérité)
    # Bonus 0 risque critique: +1.0
    # Total: 8.0 - 2.0 - 0.5 + 1.0 = 6.5
    expected_score = 6.5

    assert result["score"] == expected_score, f"❌ Score incorrect: attendu {expected_score}, obtenu {result['score']}"
    print(f"✅ Calcul du score correct: {expected_score}/10")

    print("\n📊 Résultat final:")
    print(f"   Score: {result['score']}/10")
    print(f"   Label: {result['label']}")

    # Test 9: Tester un cas avec beaucoup de risques critiques
    print("\n🧪 Test avec ≥3 risques critiques...")
    test_analysis_critical = {
        "stress_tests": [],
        "risques": {
            "critiques": [{"id": 1}, {"id": 2}, {"id": 3}],  # 3 risques → malus
            "eleves": [],
        }
    }

    result_critical = analyzer._calculate_resilience_score(test_analysis_critical)
    # Base: 8.0, Malus 3 risques: -1.5 = 6.5
    expected_critical = 6.5

    assert result_critical["score"] == expected_critical, f"❌ Score critique incorrect"
    print(f"✅ Score avec 3 risques critiques: {result_critical['score']}/10 ({result_critical['label']})")

    print("\n" + "="*60)
    print("✅ TOUS LES TESTS PASSENT")
    print("="*60 + "\n")

    return True

if __name__ == "__main__":
    try:
        test_resilience_score_return_format()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ ÉCHEC: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERREUR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
