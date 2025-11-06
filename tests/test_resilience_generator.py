#!/usr/bin/env python3
"""
Test unitaire pour valider l'injection des labels de résilience dans le générateur
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bs4 import BeautifulSoup

def test_resilience_template_fields():
    """Teste que le template contient les champs nécessaires pour la résilience"""

    print("\n" + "="*60)
    print("TEST DES CHAMPS DE RÉSILIENCE DANS LE TEMPLATE")
    print("="*60 + "\n")

    # Charger le template
    template_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "templates",
        "rapport_template.html"
    )

    with open(template_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    # Test 1: Section détails résilience existe
    resilience_details = soup.find("details", class_="resilience-details")
    assert resilience_details is not None, "❌ Section <details class='resilience-details'> manquante"
    print("✅ Section <details class='resilience-details'> trouvée")

    # Test 2: Badge res_label existe
    res_label = soup.find(attrs={"data-field": "res_label"})
    assert res_label is not None, "❌ Badge [data-field='res_label'] manquant"
    assert "badge" in res_label.get("class", []), "❌ Badge res_label n'a pas la classe 'badge'"
    print("✅ Badge [data-field='res_label'] trouvé avec classe 'badge'")

    # Test 3: Score final res_score_final existe
    res_score_final = soup.find(attrs={"data-field": "res_score_final"})
    assert res_score_final is not None, "❌ Champ [data-field='res_score_final'] manquant"
    print("✅ Champ [data-field='res_score_final'] trouvé")

    # Test 4: Vérifier la structure symétrique avec diversification
    div_details = soup.find("details", class_="diversification-details")
    assert div_details is not None, "❌ Section diversification manquante (référence)"

    # Comparer la structure
    div_summary = div_details.find("summary")
    res_summary = resilience_details.find("summary")

    assert div_summary is not None and res_summary is not None, "❌ Summary manquant"
    print("✅ Structure <summary> cohérente avec diversification")

    # Test 5: Texte descriptif
    descriptive_text = resilience_details.find("p", style=lambda x: x and "italic" in x)
    assert descriptive_text is not None, "❌ Texte descriptif manquant"
    assert "résilience" in descriptive_text.text.lower(), "❌ Texte descriptif ne mentionne pas la résilience"
    print("✅ Texte descriptif présent et pertinent")

    print("\n" + "="*60)
    print("✅ TOUS LES TESTS TEMPLATE PASSENT")
    print("="*60 + "\n")

    return True

def test_resilience_badge_mapping():
    """Teste le mapping des labels vers les classes CSS"""

    print("\n" + "="*60)
    print("TEST DU MAPPING LABELS → CLASSES CSS")
    print("="*60 + "\n")

    from tools.generator import ReportGenerator

    config = {
        "paths": {
            "templates": "templates/",
            "generated": "generated/",
        },
        "generator": {
            "output_prefix": "rapport",
        }
    }

    generator = ReportGenerator(config)

    # Test cases: (label, expected_class)
    test_cases = [
        ("Patrimoine résilient", "low"),
        ("Patrimoine solide", "low"),
        ("Patrimoine vulnérable", "mid"),
        ("Patrimoine fragile", "high"),
        ("Patrimoine critique", "crit"),
        ("Label inconnu", "mid"),  # Fallback
    ]

    print("📊 Test du mapping:\n")

    for label, expected_class in test_cases:
        result_class = generator._get_resilience_badge_class(label)
        assert result_class == expected_class, \
            f"❌ Mapping incorrect: '{label}' → '{result_class}' (attendu: '{expected_class}')"
        print(f"   ✅ '{label}' → classe '{result_class}'")

    print("\n" + "="*60)
    print("✅ TOUS LES MAPPINGS CORRECTS")
    print("="*60 + "\n")

    return True

if __name__ == "__main__":
    try:
        test_resilience_template_fields()
        test_resilience_badge_mapping()
        print("\n🎉 IMPLÉMENTATION RÉSILIENCE COMPLÈTE ET VALIDÉE\n")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ ÉCHEC: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERREUR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
