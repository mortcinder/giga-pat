"""
Test d'intégration Bitstack avec le normalizer et le cache.

Version: v2.1
"""

import unittest
import sys
import json
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.normalizer import PatrimoineNormalizer
from tools.cache_manager import CacheManager


class TestBitstackIntegration(unittest.TestCase):
    """Tests d'intégration pour le parser Bitstack"""

    def setUp(self):
        """Configuration avant chaque test"""
        self.project_root = Path(__file__).parent.parent
        self.test_manifest = self.project_root / "sources" / "manifest_test_bitstack.json"
        self.cache_dir = self.project_root / "generated" / "cache_test"

        # Créer un manifest de test
        self._create_test_manifest()

        # Configuration minimale
        self.config = {
            "paths": {
                "sources": str(self.project_root / "sources"),
                "generated": str(self.project_root / "generated"),
                "logs": str(self.project_root / "logs")
            },
            "normalizer": {
                "input_file": "manifest_test_bitstack.json",
                "output_file": "patrimoine_input_test.json"
            }
        }

        # Créer CacheManager
        self.cache_manager = CacheManager(cache_dir=str(self.cache_dir))

    def tearDown(self):
        """Nettoyage après chaque test"""
        # Supprimer le manifest de test
        if self.test_manifest.exists():
            self.test_manifest.unlink()

        # Supprimer le cache de test
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)

        # Supprimer le fichier de sortie
        output_file = self.project_root / "generated" / "patrimoine_input_test.json"
        if output_file.exists():
            output_file.unlink()

    def _create_test_manifest(self):
        """Crée un manifest de test avec Bitstack"""
        manifest = {
            "version": "2.1.0",
            "generated_at": "2025-11-11T12:00:00.000000",
            "profil_investisseur": {
                "identite": {"genre": "Homme", "date_naissance": "1975-11-23"},
                "professionnel": {"statut": "Actif"},
                "investissement": {"profil_risque": "dynamique"}
            },
            "patrimoine": {
                "comptes_titres": [
                    {
                        "id": "bitstack_btc_test",
                        "custodian": "bitstack",
                        "custodian_name": "Bitstack",
                        "custody_type": "custodial_platform",
                        "type_compte": "Crypto",
                        "source_pattern": "Bitstack/[BIT] - *.csv",
                        "parser_strategy": "bitstack.transaction_history.v2025",
                        "cache_historical_years": True,
                        "fallback_parsers": []
                    }
                ],
                "liquidites": [],
                "obligations": [],
                "crypto": [],
                "metaux_precieux": [],
                "immobilier": []
            }
        }

        with open(self.test_manifest, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

    def test_parse_bitstack_with_cache(self):
        """Test: Parsing Bitstack avec système de cache"""
        bitstack_dir = self.project_root / "sources" / "Bitstack"
        if not bitstack_dir.exists():
            self.skipTest("Répertoire Bitstack non trouvé")

        # Vérifier qu'il y a des fichiers CSV (sans glob car [] pose problème)
        all_files = list(bitstack_dir.iterdir()) if bitstack_dir.exists() else []
        csv_files = [f for f in all_files if f.is_file() and f.name.startswith('[BIT]') and f.name.endswith('.csv')]
        if not csv_files:
            self.skipTest("Aucun fichier CSV Bitstack trouvé")

        print(f"\n✓ Trouvé {len(csv_files)} fichier(s) Bitstack: {[f.name for f in csv_files]}")

        # Vider le cache avant le test
        self.cache_manager.clear_all()

        # Premier passage : parsing sans cache
        print("\n=== Premier passage (parsing complet) ===")
        normalizer = PatrimoineNormalizer(self.config)
        result1 = normalizer.normalize()

        # Vérifier les données parsées
        self.assertIn("etablissements", result1)
        bitstack = next((e for e in result1["etablissements"] if e["code"] == "bitstack"), None)
        self.assertIsNotNone(bitstack, "Bitstack doit être présent")

        # Vérifier le cache créé
        cache_stats = self.cache_manager.get_cache_stats()
        print(f"\n✓ Cache créé: {cache_stats['file_count']} fichier(s)")

        # Les années passées doivent être en cache
        self.assertGreater(cache_stats['file_count'], 0, "Au moins un fichier doit être en cache")

        # Deuxième passage : utilisation du cache
        print("\n=== Deuxième passage (avec cache) ===")
        normalizer2 = PatrimoineNormalizer(self.config)
        result2 = normalizer2.normalize()

        # Vérifier que les résultats sont identiques
        bitstack2 = next((e for e in result2["etablissements"] if e["code"] == "bitstack"), None)
        self.assertIsNotNone(bitstack2)

        # Les montants doivent être les mêmes
        self.assertEqual(
            bitstack["total"],
            bitstack2["total"],
            "Le total doit être identique avec ou sans cache"
        )

        print(f"\n✓ Total Bitstack: {bitstack['total']:.2f} EUR (identique avec/sans cache)")

    def test_cache_year_logic(self):
        """Test: Logique de mise en cache selon l'année"""
        from datetime import datetime

        current_year = datetime.now().year

        # Les années passées doivent être cachées
        self.assertTrue(
            self.cache_manager.should_cache_year(2022),
            "2022 doit être caché"
        )
        self.assertTrue(
            self.cache_manager.should_cache_year(2024),
            "2024 doit être caché"
        )

        # L'année courante ne doit PAS être cachée
        self.assertFalse(
            self.cache_manager.should_cache_year(current_year),
            f"{current_year} ne doit pas être caché"
        )

    def test_cache_invalidation_on_file_change(self):
        """Test: Le cache est invalidé si le fichier change"""
        test_file = self.project_root / "sources" / "Bitstack" / "[BIT] - 2022.csv"

        if not test_file.exists():
            self.skipTest("Fichier test non trouvé")

        # Créer un cache initial
        cache_key = self.cache_manager.get_cache_key("bitstack", test_file.name)
        test_data = [{"test": "data"}]

        self.cache_manager.save_to_cache(cache_key, str(test_file), test_data)

        # Vérifier que le cache est valide
        self.assertTrue(
            self.cache_manager.is_cached(cache_key, str(test_file)),
            "Le cache doit être valide"
        )

        # Modifier le fichier (simulé en changeant le hash attendu)
        cached = self.cache_manager.load_from_cache(cache_key)
        cached['_metadata']['file_hash'] = "wrong_hash"

        cache_file = self.cache_dir / f"{cache_key}.json"
        with open(cache_file, 'w') as f:
            json.dump(cached, f)

        # Le cache ne doit plus être valide
        self.assertFalse(
            self.cache_manager.is_cached(cache_key, str(test_file)),
            "Le cache doit être invalidé si le fichier change"
        )


def run_tests():
    """Exécute les tests"""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    run_tests()
