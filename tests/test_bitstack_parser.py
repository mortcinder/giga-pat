"""
Tests unitaires pour le parser Bitstack.

Version: v2.1
"""

import unittest
import sys
from pathlib import Path
from decimal import Decimal

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.parsers.bitstack import BitstackTransactionHistoryParser


class TestBitstackParser(unittest.TestCase):
    """Tests pour BitstackTransactionHistoryParser"""

    def setUp(self):
        """Initialisation avant chaque test"""
        self.parser = BitstackTransactionHistoryParser()
        self.test_files_dir = Path(__file__).parent.parent / "sources" / "Bitstack"

    def test_can_parse_valid_file(self):
        """Test: Détection d'un fichier Bitstack valide"""
        test_file = self.test_files_dir / "[BIT] - 2022.csv"

        if not test_file.exists():
            self.skipTest(f"Fichier de test non trouvé: {test_file}")

        result = self.parser.can_parse(str(test_file), {})
        self.assertTrue(result, "Le parser doit reconnaître un fichier Bitstack valide")

    def test_can_parse_invalid_pattern(self):
        """Test: Rejet d'un fichier avec mauvais pattern"""
        # Fichier qui n'existe pas mais avec mauvais pattern
        result = self.parser.can_parse("test.csv", {})
        self.assertFalse(result, "Le parser doit rejeter un fichier sans pattern [BIT]")

    def test_parse_2022_file(self):
        """Test: Parsing du fichier 2022"""
        test_file = self.test_files_dir / "[BIT] - 2022.csv"

        if not test_file.exists():
            self.skipTest(f"Fichier de test non trouvé: {test_file}")

        metadata = {
            "etablissement": "bitstack",
            "type_compte": "Crypto"
        }

        parsed = self.parser.parse(str(test_file), metadata)

        # Vérifications
        self.assertIsInstance(parsed, list, "Le résultat doit être une liste")
        self.assertEqual(len(parsed), 1, "Doit retourner exactement 1 ligne résumée")

        entry = parsed[0]
        self.assertIn("nom", entry)
        self.assertIn("type", entry)
        self.assertIn("quantite", entry)
        self.assertIn("metadata", entry)

        # Vérifier le type
        self.assertEqual(entry["type"], "BTC")

        # Vérifier les métadonnées
        self.assertEqual(entry["metadata"]["year"], "2022")
        self.assertIn("transaction_count", entry["metadata"])

        # Vérifier que le solde est positif (après achats - retraits)
        self.assertGreaterEqual(entry["quantite"], 0, "Le solde BTC doit être >= 0")

        print(f"\n✓ Fichier 2022 parsé: {entry['quantite']} BTC, {entry['metadata']['transaction_count']} transactions")

    def test_parse_2024_file(self):
        """Test: Parsing du fichier 2024"""
        test_file = self.test_files_dir / "[BIT] - 2024.csv"

        if not test_file.exists():
            self.skipTest(f"Fichier de test non trouvé: {test_file}")

        metadata = {
            "etablissement": "bitstack",
            "type_compte": "Crypto"
        }

        parsed = self.parser.parse(str(test_file), metadata)

        self.assertEqual(len(parsed), 1)
        entry = parsed[0]

        # Le fichier 2024 devrait avoir plus de transactions
        self.assertGreater(entry["metadata"]["transaction_count"], 50, "2024 devrait avoir >50 transactions")

        print(f"\n✓ Fichier 2024 parsé: {entry['quantite']} BTC, {entry['metadata']['transaction_count']} transactions")

    def test_parse_all_years(self):
        """Test: Parsing de tous les fichiers disponibles"""
        if not self.test_files_dir.exists():
            self.skipTest(f"Répertoire Bitstack non trouvé: {self.test_files_dir}")

        files = sorted(self.test_files_dir.glob("[BIT] - *.csv"))

        if not files:
            self.skipTest("Aucun fichier Bitstack trouvé")

        total_btc = Decimal('0')
        total_transactions = 0

        metadata = {
            "etablissement": "bitstack",
            "type_compte": "Crypto"
        }

        for file in files:
            parsed = self.parser.parse(str(file), metadata)
            entry = parsed[0]

            total_btc += Decimal(str(entry["quantite"]))
            total_transactions += entry["metadata"]["transaction_count"]

            print(f"  {file.name}: {entry['quantite']:.8f} BTC, {entry['metadata']['transaction_count']} tx")

        print(f"\n✓ Total cumulé: {float(total_btc):.8f} BTC sur {total_transactions} transactions")

        self.assertGreater(float(total_btc), 0, "Le solde total doit être positif")

    def test_validate_positive_balance(self):
        """Test: Validation d'un solde positif"""
        valid_data = [{
            'nom': 'Bitcoin 2022',
            'type': 'BTC',
            'quantite': 0.005,
            'valeur_unitaire': 0,
            'valeur_totale': 0,
            'devise': 'BTC',
            'metadata': {
                'year': '2022',
                'transaction_count': 10
            }
        }]

        result = self.parser.validate(valid_data)
        self.assertTrue(result, "Un solde positif doit être valide")

    def test_validate_negative_balance(self):
        """Test: Validation échoue pour solde négatif"""
        invalid_data = [{
            'nom': 'Bitcoin 2022',
            'type': 'BTC',
            'quantite': -0.005,
            'valeur_unitaire': 0,
            'valeur_totale': 0,
            'devise': 'BTC'
        }]

        result = self.parser.validate(invalid_data)
        self.assertFalse(result, "Un solde négatif ne doit pas être valide")

    def test_validate_empty_data(self):
        """Test: Validation échoue pour données vides"""
        result = self.parser.validate([])
        self.assertFalse(result, "Des données vides ne doivent pas être valides")


def run_tests():
    """Exécute les tests"""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    run_tests()
