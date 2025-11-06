"""
Test unitaire pour le score de diversification enrichi
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import yaml


def test_diversification_score():
    """Test du calculateur de score de diversification"""

    # Charger la configuration
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'analysis.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        analysis_config = yaml.safe_load(f)

    div_config = analysis_config.get("scores", {}).get("diversification", {})

    print("=" * 70)
    print("TEST DU SCORE DE DIVERSIFICATION ENRICHI")
    print("=" * 70)
    print()

    # Test 1: Vérifier la structure de configuration
    print("Test 1: Vérifier la structure de configuration")
    assert "weights" in div_config, "❌ 'weights' manquant dans la config"
    assert div_config["weights"]["institutional"] == 0.6, "❌ Poids institutionnel incorrect"
    assert div_config["weights"]["jurisdictional"] == 0.4, "❌ Poids juridictionnel incorrect"
    print(f"  ✓ Poids institutionnel: {div_config['weights']['institutional']}")
    print(f"  ✓ Poids juridictionnel: {div_config['weights']['jurisdictional']}")
    print()

    # Test 2: Vérifier les bonus
    print("Test 2: Vérifier les bonus configurés")
    bonuses = div_config.get("bonuses", {})
    assert "asset_classes_5plus" in bonuses, "❌ Bonus classes d'actifs manquant"
    assert bonuses["asset_classes_5plus"] == 1.0, "❌ Bonus classes d'actifs incorrect"
    assert "positions_10plus" in bonuses, "❌ Bonus positions manquant"
    assert bonuses["positions_10plus"] == 0.5, "❌ Bonus positions incorrect"
    assert "international_15plus" in bonuses, "❌ Bonus international manquant"
    assert bonuses["international_15plus"] == 0.5, "❌ Bonus international incorrect"
    print(f"  ✓ Bonus ≥5 classes d'actifs: +{bonuses['asset_classes_5plus']}")
    print(f"  ✓ Bonus ≥10 positions: +{bonuses['positions_10plus']}")
    print(f"  ✓ Bonus >15% international: +{bonuses['international_15plus']}")
    print()

    # Test 3: Vérifier les labels de qualité
    print("Test 3: Vérifier les labels de qualité")
    quality_labels = div_config.get("quality_labels", [])
    assert len(quality_labels) == 5, f"❌ Devrait y avoir 5 labels, trouvé {len(quality_labels)}"

    for label_range in quality_labels:
        min_score, max_score, label = label_range
        print(f"  • {min_score}-{max_score}: {label}")

    assert quality_labels[0][2] == "Excellente diversification", "❌ Label 9-10 incorrect"
    assert quality_labels[4][2] == "Concentration critique", "❌ Label 0-3 incorrect"
    print("  ✓ Tous les labels sont corrects")
    print()

    # Test 4: Simuler un calcul simple
    print("Test 4: Simuler un calcul de score")
    base_score = div_config.get("base_score", 10.0)

    # Simulation: pas de concentration
    score_institutional = base_score  # 10
    score_jurisdictional = base_score  # 10

    # Score pondéré
    score_weighted = (
        score_institutional * div_config["weights"]["institutional"] +
        score_jurisdictional * div_config["weights"]["jurisdictional"]
    )

    # Ajouter tous les bonus (scénario optimal)
    bonus_total = (
        bonuses["asset_classes_5plus"] +
        bonuses["positions_10plus"] +
        bonuses["international_15plus"]
    )

    score_final = score_weighted + bonus_total
    score_final = min(10, score_final)  # Plafonner à 10

    print(f"  Score institutionnel: {score_institutional}/10")
    print(f"  Score juridictionnel: {score_jurisdictional}/10")
    print(f"  Score pondéré (60%/40%): {score_weighted:.1f}/10")
    print(f"  Bonus total: +{bonus_total:.1f}")
    print(f"  Score final (plafonné): {score_final:.1f}/10")

    assert score_weighted == 10.0, f"❌ Score pondéré devrait être 10, obtenu {score_weighted}"
    assert bonus_total == 2.0, f"❌ Bonus total devrait être 2.0, obtenu {bonus_total}"
    assert score_final == 10.0, f"❌ Score final devrait être 10 (plafonné), obtenu {score_final}"
    print("  ✓ Calcul correct")
    print()

    # Test 5: Mapper les labels
    print("Test 5: Vérifier le mapping des labels")
    test_scores = [9.5, 7.5, 6.0, 4.0, 2.0]
    expected_labels = [
        "Excellente diversification",
        "Bonne diversification",
        "Concentration modérée",
        "Forte concentration",
        "Concentration critique"
    ]

    for test_score, expected_label in zip(test_scores, expected_labels):
        found_label = None
        for label_range in quality_labels:
            min_s, max_s, lbl = label_range
            if min_s <= test_score < max_s or (test_score == 10 and max_s == 10):
                found_label = lbl
                break

        print(f"  Score {test_score:.1f} → {found_label}")
        assert found_label == expected_label, f"❌ Label incorrect pour score {test_score}"

    print("  ✓ Tous les mappings sont corrects")
    print()

    print("=" * 70)
    print("✓ TOUS LES TESTS RÉUSSIS")
    print("=" * 70)


if __name__ == "__main__":
    test_diversification_score()
