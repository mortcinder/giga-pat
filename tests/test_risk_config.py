#!/usr/bin/env python3
"""
Test simple pour vérifier le chargement de la configuration des risques v2.0
"""

import os
import sys
import yaml

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_load_risks_yaml():
    """Teste le chargement du fichier config/risks.yaml"""
    print("=" * 70)
    print("TEST DU SYSTÈME DE DÉTECTION DES RISQUES v2.0")
    print("=" * 70)
    print()

    # Chemin vers le fichier de configuration
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "config",
        "risks.yaml"
    )

    print(f"📄 Chargement du fichier: {config_path}")

    if not os.path.exists(config_path):
        print(f"❌ ERREUR: Fichier {config_path} introuvable")
        return False

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            risk_config = yaml.safe_load(f)
        print("✓ Fichier chargé avec succès")
    except Exception as e:
        print(f"❌ ERREUR lors du chargement: {e}")
        return False

    print()
    print("-" * 70)
    print("CONFIGURATION GÉNÉRALE")
    print("-" * 70)

    # Vérifier risk_settings
    if "risk_settings" in risk_config:
        settings = risk_config["risk_settings"]
        print(f"✓ Version: {settings.get('version', 'N/A')}")
        print(f"✓ Dernière mise à jour: {settings.get('last_updated', 'N/A')}")
        print(f"✓ Détection contextuelle: {'ACTIVÉE' if settings.get('enable_contextual_detection', False) else 'DÉSACTIVÉE'}")
        print(f"✓ Max risques contextuels par recherche: {settings.get('max_contextual_risks_per_search', 3)}")
    else:
        print("⚠ Section 'risk_settings' manquante")

    print()
    print("-" * 70)
    print("RISQUES STRUCTURELS")
    print("-" * 70)

    # Compter les risques structurels
    if "structural_risks" in risk_config:
        structural = risk_config["structural_risks"]
        enabled_count = sum(1 for risk in structural.values() if risk.get("enabled", False))
        print(f"✓ Total de risques structurels définis: {len(structural)}")
        print(f"✓ Risques structurels activés: {enabled_count}")
        print()
        print("Liste des risques structurels:")
        for risk_id, risk_data in structural.items():
            status = "✓" if risk_data.get("enabled", False) else "✗"
            category = risk_data.get("category", "N/A")
            print(f"  {status} {risk_id} ({category})")
    else:
        print("⚠ Section 'structural_risks' manquante")

    print()
    print("-" * 70)
    print("RECHERCHES CONTEXTUELLES")
    print("-" * 70)

    # Compter les recherches contextuelles
    if "contextual_searches" in risk_config:
        contextual = risk_config["contextual_searches"]
        enabled_count = sum(1 for search in contextual.values() if search.get("enabled", False))
        print(f"✓ Total de recherches contextuelles définies: {len(contextual)}")
        print(f"✓ Recherches contextuelles activées: {enabled_count}")
        print()
        print("Liste des recherches contextuelles:")
        for search_id, search_data in contextual.items():
            status = "✓" if search_data.get("enabled", False) else "✗"
            priority = search_data.get("priority", "N/A")
            num_queries = len(search_data.get("queries", []))
            print(f"  {status} {search_id} (priorité: {priority}, {num_queries} requêtes)")
    else:
        print("⚠ Section 'contextual_searches' manquante")

    print()
    print("-" * 70)
    print("MÉTADONNÉES")
    print("-" * 70)

    if "metadata" in risk_config:
        metadata = risk_config["metadata"]
        print(f"✓ Fréquence de mise à jour recommandée: {metadata.get('recommended_update_frequency', 'N/A')}")
        print(f"✓ Prochaine revue suggérée: {metadata.get('next_review_date', 'N/A')}")
        print(f"✓ Mainteneur: {metadata.get('maintainer', 'N/A')}")

        if "changelog" in metadata:
            print(f"✓ Historique des versions: {len(metadata['changelog'])} entrées")
    else:
        print("⚠ Section 'metadata' manquante")

    print()
    print("=" * 70)
    print("✅ TEST RÉUSSI : Configuration des risques v2.0 valide")
    print("=" * 70)

    return True


if __name__ == "__main__":
    success = test_load_risks_yaml()
    sys.exit(0 if success else 1)
