"""
Tests pour le CacheManager (v2.1)

Ce module teste toutes les fonctionnalités du système de cache :
- Hashing de fichiers (SHA-256)
- Génération de clés de cache
- Sauvegarde et chargement
- Validation et invalidation
- Gestion de la taille (LRU)

Version: v2.1
Auteur: Claude Code
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime
from tools.cache_manager import CacheManager


@pytest.fixture
def temp_cache_dir():
    """Crée un répertoire de cache temporaire pour les tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_file():
    """Crée un fichier temporaire pour les tests."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write("test,data,here\n")
        f.write("1,2,3\n")
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


class TestCacheManager:
    """Tests du CacheManager."""

    def test_init_creates_directory(self, temp_cache_dir):
        """Test que l'initialisation crée le répertoire de cache."""
        cache_dir = temp_cache_dir / "new_cache"
        assert not cache_dir.exists()

        cm = CacheManager(str(cache_dir))

        assert cache_dir.exists()
        assert cache_dir.is_dir()

    def test_get_file_hash_sha256(self, temp_file):
        """Test que get_file_hash retourne un hash SHA-256 valide."""
        cm = CacheManager()

        file_hash = cm.get_file_hash(str(temp_file))

        # SHA-256 produit 64 caractères hexadécimaux
        assert len(file_hash) == 64
        assert all(c in '0123456789abcdef' for c in file_hash)

    def test_get_file_hash_deterministic(self, temp_file):
        """Test que le hash est déterministe (même fichier = même hash)."""
        cm = CacheManager()

        hash1 = cm.get_file_hash(str(temp_file))
        hash2 = cm.get_file_hash(str(temp_file))

        assert hash1 == hash2

    def test_get_file_hash_changes_with_content(self, temp_cache_dir):
        """Test que le hash change si le contenu change."""
        file1 = temp_cache_dir / "file1.txt"
        file2 = temp_cache_dir / "file2.txt"

        file1.write_text("content A")
        file2.write_text("content B")

        cm = CacheManager()
        hash1 = cm.get_file_hash(str(file1))
        hash2 = cm.get_file_hash(str(file2))

        assert hash1 != hash2

    def test_get_cache_key_with_year(self):
        """Test génération de clé avec année dans le nom."""
        cm = CacheManager()

        key = cm.get_cache_key("bitstack", "[BIT] - 2023.csv")

        assert key == "bitstack_2023"

    def test_get_cache_key_without_year(self):
        """Test génération de clé sans année."""
        cm = CacheManager()

        key = cm.get_cache_key("broker", "account.csv")

        assert key == "broker_account"

    def test_save_and_load_cache(self, temp_cache_dir, temp_file):
        """Test sauvegarde et chargement du cache."""
        cm = CacheManager(str(temp_cache_dir))

        test_data = [
            {"nom": "Position 1", "valeur": 1000},
            {"nom": "Position 2", "valeur": 2000}
        ]
        metadata = {"year": 2023, "custodian": "bitstack"}

        # Sauvegarder
        cm.save_to_cache("test_key", str(temp_file), test_data, metadata)

        # Charger
        cached = cm.load_from_cache("test_key")

        assert cached is not None
        assert cached['data'] == test_data
        assert cached['_metadata']['custom_metadata'] == metadata
        assert 'file_hash' in cached['_metadata']
        assert 'cached_at' in cached['_metadata']

    def test_load_nonexistent_cache(self, temp_cache_dir):
        """Test chargement d'un cache inexistant."""
        cm = CacheManager(str(temp_cache_dir))

        cached = cm.load_from_cache("nonexistent_key")

        assert cached is None

    def test_is_cached_valid(self, temp_cache_dir, temp_file):
        """Test détection de cache valide."""
        cm = CacheManager(str(temp_cache_dir))

        test_data = [{"test": "data"}]
        cm.save_to_cache("test_key", str(temp_file), test_data)

        is_valid = cm.is_cached("test_key", str(temp_file))

        assert is_valid is True

    def test_is_cached_file_modified(self, temp_cache_dir, temp_file):
        """Test détection de fichier modifié."""
        cm = CacheManager(str(temp_cache_dir))

        test_data = [{"test": "data"}]
        cm.save_to_cache("test_key", str(temp_file), test_data)

        # Modifier le fichier
        temp_file.write_text("modified content")

        is_valid = cm.is_cached("test_key", str(temp_file))

        assert is_valid is False

    def test_is_cached_nonexistent(self, temp_cache_dir, temp_file):
        """Test détection de cache inexistant."""
        cm = CacheManager(str(temp_cache_dir))

        is_valid = cm.is_cached("nonexistent_key", str(temp_file))

        assert is_valid is False

    def test_should_cache_year_past(self):
        """Test que les années passées doivent être cachées."""
        cm = CacheManager()
        current_year = datetime.now().year

        should_cache = cm.should_cache_year(current_year - 1)

        assert should_cache is True

    def test_should_cache_year_current(self):
        """Test que l'année courante ne doit pas être cachée."""
        cm = CacheManager()
        current_year = datetime.now().year

        should_cache = cm.should_cache_year(current_year)

        assert should_cache is False

    def test_should_cache_year_future(self):
        """Test que les années futures ne doivent pas être cachées."""
        cm = CacheManager()
        current_year = datetime.now().year

        should_cache = cm.should_cache_year(current_year + 1)

        assert should_cache is False

    def test_invalidate_cache(self, temp_cache_dir, temp_file):
        """Test invalidation d'un cache."""
        cm = CacheManager(str(temp_cache_dir))

        test_data = [{"test": "data"}]
        cm.save_to_cache("test_key", str(temp_file), test_data)

        # Vérifier qu'il existe
        assert cm.load_from_cache("test_key") is not None

        # Invalider
        cm.invalidate_cache("test_key")

        # Vérifier qu'il n'existe plus
        assert cm.load_from_cache("test_key") is None

    def test_clear_all(self, temp_cache_dir, temp_file):
        """Test vidage complet du cache."""
        cm = CacheManager(str(temp_cache_dir))

        # Créer plusieurs caches
        cm.save_to_cache("key1", str(temp_file), [{"a": 1}])
        cm.save_to_cache("key2", str(temp_file), [{"b": 2}])
        cm.save_to_cache("key3", str(temp_file), [{"c": 3}])

        # Vérifier qu'ils existent
        assert len(list(temp_cache_dir.glob("*.json"))) == 3

        # Tout vider
        cm.clear_all()

        # Vérifier qu'ils sont supprimés
        assert len(list(temp_cache_dir.glob("*.json"))) == 0

    def test_get_cache_stats(self, temp_cache_dir, temp_file):
        """Test récupération des statistiques."""
        cm = CacheManager(str(temp_cache_dir))

        # Créer quelques caches
        cm.save_to_cache("key1", str(temp_file), [{"a": 1}])
        cm.save_to_cache("key2", str(temp_file), [{"b": 2}])

        stats = cm.get_cache_stats()

        assert stats['cache_dir'] == str(temp_cache_dir)
        assert stats['file_count'] == 2
        assert stats['total_size_bytes'] > 0
        assert stats['total_size_mb'] >= 0
        assert len(stats['files']) == 2
        assert 'key1.json' in stats['files']
        assert 'key2.json' in stats['files']

    def test_enforce_cache_limit_under_limit(self, temp_cache_dir, temp_file):
        """Test que enforce_cache_limit ne supprime rien si sous la limite."""
        cm = CacheManager(str(temp_cache_dir))

        # Créer un petit cache
        cm.save_to_cache("key1", str(temp_file), [{"a": 1}])

        # Appliquer une limite élevée
        cm.enforce_cache_limit(max_size_mb=100)

        # Vérifier que le fichier existe toujours
        assert cm.load_from_cache("key1") is not None

    def test_enforce_cache_limit_over_limit(self, temp_cache_dir):
        """Test que enforce_cache_limit supprime les fichiers LRU."""
        cm = CacheManager(str(temp_cache_dir))

        # Créer plusieurs fichiers avec du contenu
        import time
        for i in range(5):
            temp_f = temp_cache_dir / f"source_{i}.txt"
            temp_f.write_text("x" * 50000)  # 50KB
            cm.save_to_cache(f"key{i}", str(temp_f), [{"data": "x" * 10000}])
            time.sleep(0.01)  # Assurer des timestamps différents

        # Vérifier qu'on a 5 fichiers
        assert cm.get_cache_stats()['file_count'] == 5

        # Appliquer limite très basse (devrait supprimer les plus vieux)
        cm.enforce_cache_limit(max_size_mb=0.2)  # 200KB

        # Vérifier que certains fichiers ont été supprimés
        final_count = cm.get_cache_stats()['file_count']
        assert final_count < 5
        assert final_count >= 1  # Au moins un reste

    def test_enforce_cache_limit_lru_order(self, temp_cache_dir):
        """Test que enforce_cache_limit supprime d'abord les plus anciens (LRU)."""
        cm = CacheManager(str(temp_cache_dir))

        import time

        # Créer fichiers dans un ordre spécifique
        files_created = []
        for i in range(3):
            temp_f = temp_cache_dir / f"source_{i}.txt"
            temp_f.write_text("x" * 50000)
            cm.save_to_cache(f"key{i}", str(temp_f), [{"data": "x" * 10000}])
            files_created.append(f"key{i}")
            time.sleep(0.05)

        # Appliquer limite pour garder seulement 2 fichiers
        cm.enforce_cache_limit(max_size_mb=0.15)

        # Les plus récents devraient rester (key1, key2)
        # Le plus ancien devrait être supprimé (key0)
        assert cm.load_from_cache("key0") is None  # Plus vieux, supprimé
        # Au moins un des plus récents devrait exister
        recent_exists = (cm.load_from_cache("key1") is not None or
                        cm.load_from_cache("key2") is not None)
        assert recent_exists


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
