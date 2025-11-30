"""
Gestionnaire de cache pour données historiques immuables.

Ce module gère le cache des données qui ne changent plus (années passées),
optimisant ainsi les performances lors de la génération de rapports successifs.

Cas d'usage:
- Fichiers CSV annuels (ex: Bitstack 2022, 2023, 2024)
- Données qui ne seront plus modifiées

Version: v2.1
Auteur: Claude Code
PRD: Extension du système de parsing (Section 2.1.2)
"""

import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List


class CacheManager:
    """Gère le cache des données historiques parsées."""

    def __init__(self, cache_dir: str = "generated/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)

    def get_file_hash(self, file_path: str) -> str:
        """
        Calcule le hash SHA-256 d'un fichier pour vérification d'intégrité.

        Args:
            file_path: Chemin vers le fichier

        Returns:
            Hash SHA-256 hexadécimal
        """
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
        return hasher.hexdigest()

    def get_cache_key(self, custodian: str, file_name: str) -> str:
        """
        Génère une clé de cache unique.

        Args:
            custodian: Identifiant du custodian (ex: bitstack)
            file_name: Nom du fichier source

        Returns:
            Clé de cache (ex: bitstack_2022)
        """
        # Extraire l'année ou un identifiant du nom de fichier
        import re
        year_match = re.search(r'(\d{4})', file_name)
        identifier = year_match.group(1) if year_match else Path(file_name).stem
        return f"{custodian}_{identifier}"

    def is_cached(self, cache_key: str, file_path: str) -> bool:
        """
        Vérifie si les données sont en cache et valides.

        Args:
            cache_key: Clé de cache
            file_path: Chemin du fichier source

        Returns:
            True si cache valide, False sinon
        """
        cache_file = self.cache_dir / f"{cache_key}.json"

        if not cache_file.exists():
            return False

        try:
            cached_data = self.load_from_cache(cache_key)
            if not cached_data:
                return False

            # Vérifier le hash pour détecter les modifications
            current_hash = self.get_file_hash(file_path)
            cached_hash = cached_data.get('_metadata', {}).get('file_hash', '')

            if current_hash != cached_hash:
                self.logger.info(f"Cache invalide pour {cache_key}: fichier modifié")
                return False

            self.logger.info(f"✓ Cache valide trouvé pour {cache_key}")
            return True

        except Exception as e:
            self.logger.warning(f"Erreur lors de la vérification du cache {cache_key}: {e}")
            return False

    def save_to_cache(
        self,
        cache_key: str,
        file_path: str,
        parsed_data: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Sauvegarde des données dans le cache.

        Args:
            cache_key: Clé de cache
            file_path: Chemin du fichier source
            parsed_data: Données parsées à cacher
            metadata: Métadonnées additionnelles
        """
        cache_file = self.cache_dir / f"{cache_key}.json"

        cache_entry = {
            '_metadata': {
                'cache_key': cache_key,
                'file_path': file_path,
                'file_hash': self.get_file_hash(file_path),
                'cached_at': datetime.now().isoformat(),
                'custom_metadata': metadata or {}
            },
            'data': parsed_data
        }

        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_entry, f, indent=2, ensure_ascii=False)

            self.logger.info(f"✓ Données sauvegardées en cache: {cache_key}")

        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde du cache {cache_key}: {e}")

    def load_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Charge des données depuis le cache.

        Args:
            cache_key: Clé de cache

        Returns:
            Dictionnaire avec 'data' et '_metadata', ou None
        """
        cache_file = self.cache_dir / f"{cache_key}.json"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement du cache {cache_key}: {e}")
            return None

    def should_cache_year(self, year: int) -> bool:
        """
        Détermine si une année doit être mise en cache.

        Règle: Toutes les années AVANT l'année courante sont cachées.
        - Années passées (ex: 2022-2024): Cachées (données figées)
        - Année courante (ex: 2025): Toujours recalculée (données évolutives)

        Métadonnées du cache incluent:
        - file_hash: Hash MD5 du fichier source (pour détection de modifications)
        - cached_at: Timestamp ISO de création du cache
        - year: Année fiscale concernée
        - custodian: Établissement financier

        Args:
            year: Année à vérifier

        Returns:
            True si l'année doit être cachée (year < année courante)
        """
        current_year = datetime.now().year
        return year < current_year

    def invalidate_cache(self, cache_key: str) -> None:
        """
        Invalide (supprime) une entrée de cache.

        Args:
            cache_key: Clé de cache à invalider
        """
        cache_file = self.cache_dir / f"{cache_key}.json"

        if cache_file.exists():
            cache_file.unlink()
            self.logger.info(f"✓ Cache invalidé: {cache_key}")

    def clear_all(self) -> None:
        """Vide complètement le cache."""
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
        self.logger.info("✓ Cache complet vidé")

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Retourne des statistiques sur le cache.

        Returns:
            Dictionnaire avec statistiques (nombre de fichiers, taille totale)
        """
        cache_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)

        return {
            'cache_dir': str(self.cache_dir),
            'file_count': len(cache_files),
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'files': [f.name for f in cache_files]
        }

    def enforce_cache_limit(self, max_size_mb: int = 100) -> None:
        """
        Nettoie le cache si la taille dépasse la limite.

        Stratégie: Suppression des fichiers les plus anciens (LRU).

        Args:
            max_size_mb: Taille maximale du cache en Mo
        """
        if not self.cache_dir.exists():
            return

        # Calculer taille totale
        total_size = 0
        cache_files = []

        for cache_file in self.cache_dir.glob("*.json"):
            size = cache_file.stat().st_size
            mtime = cache_file.stat().st_mtime
            total_size += size
            cache_files.append({
                'path': cache_file,
                'size': size,
                'mtime': mtime
            })

        total_size_mb = total_size / (1024 * 1024)

        if total_size_mb <= max_size_mb:
            self.logger.info(f"Cache size: {total_size_mb:.2f} MB (under limit: {max_size_mb} MB)")
            return

        # Trier par date de modification (plus ancien en premier)
        cache_files.sort(key=lambda x: x['mtime'])

        # Supprimer les plus anciens jusqu'à passer sous la limite
        removed_count = 0
        for cache_file in cache_files:
            if total_size_mb <= max_size_mb:
                break

            cache_file['path'].unlink()
            total_size_mb -= cache_file['size'] / (1024 * 1024)
            removed_count += 1

        self.logger.info(f"Cache cleanup: removed {removed_count} files, new size: {total_size_mb:.2f} MB")
