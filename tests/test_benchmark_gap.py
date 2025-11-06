"""
Test unitaire pour le module benchmark_gap
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tools.utils.benchmark_gap import BenchmarkGapCalculator


def test_benchmark_gap():
    """Test du calculateur d'écart benchmark"""

    # Configuration minimale
    config = {
        "benchmarks": {
            "default": {
                "Actions": {
                    "min": 60,
                    "target": 65,
                    "max": 70
                },
                "Obligations": {
                    "min": 10,
                    "target": 15,
                    "max": 20
                },
                "Liquidités": {
                    "min": 5,
                    "target": 7.5,
                    "max": 10
                }
            }
        }
    }

    calculator = BenchmarkGapCalculator(config, "default")

    print("=" * 70)
    print("TEST DU CALCULATEUR D'ÉCART BENCHMARK")
    print("=" * 70)
    print()

    # Test 1: Dans la cible
    print("Test 1: Actions à 65% (dans la cible)")
    result = calculator.calculate_gap("Actions", 65.0)
    print(f"  Écart: {result['ecart_pct']}%")
    print(f"  Status: {result['status']}")
    print(f"  Niveau: {result['niveau']}")
    print(f"  Message: {result['message']}")
    assert result['status'] == 'dans_la_cible'
    assert result['niveau'] == 'normal'
    print("  ✓ Test réussi\n")

    # Test 2: Légèrement au-dessus de la cible (dans la fourchette)
    print("Test 2: Actions à 68% (légèrement sur-pondéré)")
    result = calculator.calculate_gap("Actions", 68.0)
    print(f"  Écart: {result['ecart_pct']}%")
    print(f"  Status: {result['status']}")
    print(f"  Niveau: {result['niveau']}")
    print(f"  Message: {result['message']}")
    assert result['status'] == 'sur_pondere_modere'
    assert result['niveau'] == 'normal'
    print("  ✓ Test réussi\n")

    # Test 3: Sous-pondération modérée (hors fourchette)
    print("Test 3: Actions à 55% (sous-pondéré)")
    result = calculator.calculate_gap("Actions", 55.0)
    print(f"  Écart: {result['ecart_pct']}%")
    print(f"  Écart borne: {result['ecart_borne']}%")
    print(f"  Status: {result['status']}")
    print(f"  Niveau: {result['niveau']}")
    print(f"  Message: {result['message']}")
    assert result['status'] == 'sous_pondere_modere'
    assert result['niveau'] == 'attention'
    assert result['ecart_borne'] < 0
    print("  ✓ Test réussi\n")

    # Test 4: Sur-pondération forte
    print("Test 4: Actions à 85% (fortement sur-pondéré)")
    result = calculator.calculate_gap("Actions", 85.0)
    print(f"  Écart: {result['ecart_pct']}%")
    print(f"  Écart borne: {result['ecart_borne']}%")
    print(f"  Status: {result['status']}")
    print(f"  Niveau: {result['niveau']}")
    print(f"  Message: {result['message']}")
    assert result['status'] == 'sur_pondere_fort'
    assert result['niveau'] == 'alerte'
    assert result['ecart_borne'] >= 10
    print("  ✓ Test réussi\n")

    # Test 5: Classe sans benchmark
    print("Test 5: Classe inconnue (pas de benchmark)")
    result = calculator.calculate_gap("Autre", 10.0)
    print(f"  Status: {result['status']}")
    print(f"  Niveau: {result['niveau']}")
    print(f"  Message: {result['message']}")
    assert result['status'] == 'pas_de_benchmark'
    assert result['niveau'] == 'normal'
    print("  ✓ Test réussi\n")

    # Test 6: calculate_all_gaps
    print("Test 6: Calcul des écarts pour toutes les classes")
    classes = [
        {"type_actif": "Actions", "pourcentage": 75.0, "montant": 100000},
        {"type_actif": "Obligations", "pourcentage": 15.0, "montant": 20000},
        {"type_actif": "Liquidités", "pourcentage": 10.0, "montant": 13000}
    ]

    enriched = calculator.calculate_all_gaps(classes)

    for classe in enriched:
        print(f"  {classe['type_actif']}: {classe['pourcentage']}% → {classe['benchmark_gap']['message']}")
        assert 'benchmark_gap' in classe

    print("  ✓ Test réussi\n")

    print("=" * 70)
    print("✓ TOUS LES TESTS RÉUSSIS")
    print("=" * 70)


if __name__ == "__main__":
    test_benchmark_gap()
