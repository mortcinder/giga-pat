#!/usr/bin/env python3
"""
Test unitaire pour valider les labels de résilience
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml

def test_resilience_labels():
    """Teste que les labels de résilience sont bien configurés"""

    # Charger la configuration
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "config",
        "analysis.yaml"
    )

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # Vérifier que les labels existent
    resilience_config = config.get("scores", {}).get("resilience", {})
    quality_labels = resilience_config.get("quality_labels", [])

    print("\n" + "="*60)
    print("TEST DES LABELS DE RÉSILIENCE")
    print("="*60 + "\n")

    # Test 1: Les labels existent
    assert quality_labels, "❌ Les quality_labels n'existent pas"
    print("✅ Les quality_labels existent dans la configuration")

    # Test 2: Il y a 5 labels (comme diversification)
    assert len(quality_labels) == 5, f"❌ Nombre de labels incorrect: {len(quality_labels)}"
    print(f"✅ Nombre de labels correct: {len(quality_labels)}")

    # Test 3: Affichage des labels
    print("\n📊 Labels de qualité configurés:\n")
    for label_range in quality_labels:
        min_score, max_score, label = label_range
        print(f"   [{min_score}-{max_score}]: {label}")

    # Test 4: Vérifier la cohérence des plages
    print("\n🔍 Vérification de la cohérence des plages:")

    # Les plages doivent couvrir [0-10] sans chevauchement
    sorted_labels = sorted(quality_labels, key=lambda x: x[0])

    for i, (min_s, max_s, label) in enumerate(sorted_labels):
        # Vérifier que min < max
        assert min_s < max_s or (min_s == max_s == 10), f"❌ Plage invalide: [{min_s}-{max_s}]"

        # Vérifier la continuité avec la plage suivante
        if i < len(sorted_labels) - 1:
            next_min = sorted_labels[i + 1][0]
            assert max_s == next_min, f"❌ Gap détecté: [{min_s}-{max_s}] puis [{next_min}-...]"

    print("   ✅ Plages continues et cohérentes")

    # Test 5: Vérifier que la première plage commence à 0
    assert sorted_labels[0][0] == 0, f"❌ La première plage devrait commencer à 0, pas {sorted_labels[0][0]}"
    print("   ✅ Couverture complète de [0-10]")

    # Test 6: Vérifier que la dernière plage va jusqu'à 10
    assert sorted_labels[-1][1] == 10, f"❌ La dernière plage devrait aller jusqu'à 10, pas {sorted_labels[-1][1]}"
    print("   ✅ Plage maximale atteint 10")

    # Test 7: Vérifier les labels suggérés
    expected_labels = {
        "Patrimoine résilient",
        "Patrimoine solide",
        "Patrimoine vulnérable",
        "Patrimoine fragile",
        "Patrimoine critique"
    }

    actual_labels = {label for _, _, label in quality_labels}
    assert actual_labels == expected_labels, f"❌ Labels différents des attendus: {actual_labels}"
    print("   ✅ Labels conformes aux recommandations")

    print("\n" + "="*60)
    print("✅ TOUS LES TESTS PASSENT")
    print("="*60 + "\n")

    return True

if __name__ == "__main__":
    try:
        test_resilience_labels()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ ÉCHEC: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERREUR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
