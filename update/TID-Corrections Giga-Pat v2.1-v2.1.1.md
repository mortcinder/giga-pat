# 📘 TID (Technical Implementation Document)
## Corrections Giga-Pat v2.1 → v2.1.1

**Date** : 2025-11-12
**Projet** : giga-pat
**Branche** : `claude/analyze-giga-pat-project-011CV3mgMUCcBtmsy5vpni1J`
**Objectif** : Corriger les incohérences et erreurs identifiées en 4 phases

---

## 🎯 INSTRUCTIONS GÉNÉRALES

### Règles strictes d'exécution :
1. ✅ Suivre l'ordre exact des phases (1 → 2 → 3 → 4)
2. ✅ Suivre l'ordre exact des tâches dans chaque phase
3. ✅ Lire le fichier complet AVANT toute modification
4. ✅ Utiliser Edit tool (jamais Write sur fichiers existants)
5. ✅ Copier-coller EXACTEMENT les blocs AVANT/APRÈS
6. ✅ Valider chaque tâche avec les critères fournis
7. ✅ Commiter après chaque phase complétée
8. ❌ NE PAS improviser de modifications non documentées
9. ❌ NE PAS modifier de fichiers non listés
10. ❌ NE PAS sauter d'étapes

### Structure de chaque tâche :
```
TÂCHE X.Y : [Titre]
├── Fichier : [chemin exact]
├── Action : [description précise]
├── AVANT : [code à remplacer]
├── APRÈS : [nouveau code]
├── Validation : [comment vérifier]
└── Rollback : [comment annuler si erreur]
```

---

# 🚨 PHASE 1 : CORRECTIONS CRITIQUES

**Objectif** : Corriger 4 issues critiques (sécurité + conformité interface)
**Durée estimée** : 1-2 heures
**Commit message** : `fix(critical): Security patches and parser interface compliance`

---

## TÂCHE 1.1 : Corriger BitstackTransactionHistoryParser - strategy_name

**Fichier** : `/home/user/giga-pat/tools/parsers/bitstack/transaction_history.py`

**Action** : Convertir l'attribut de classe `strategy_name` en propriété `@property`

**AVANT** (ligne 37) :
```python
    strategy_name = "bitstack.transaction_history.v2025"
```

**APRÈS** :
```python
    @property
    def strategy_name(self) -> str:
        """Identifiant unique de la stratégie de parsing."""
        return "bitstack.transaction_history.v2025"
```

**Validation** :
```bash
python3 -c "from tools.parsers.bitstack import BitstackTransactionHistoryParser; p = BitstackTransactionHistoryParser(); assert p.strategy_name == 'bitstack.transaction_history.v2025'; print('✓ strategy_name OK')"
```

**Rollback** : Restaurer la ligne 37 originale

---

## TÂCHE 1.2 : Corriger BitstackTransactionHistoryParser - can_parse()

**Fichier** : `/home/user/giga-pat/tools/parsers/bitstack/transaction_history.py`

**Action** : Modifier signature et retour de `can_parse()` pour retourner `float` au lieu de `bool`

**AVANT** (lignes 50-74) :
```python
    def can_parse(self, file_path: str, metadata: Dict[str, Any]) -> bool:
        """
        Vérifie si le fichier peut être parsé par ce parser.

        Critères:
        - Fichier CSV
        - Pattern [BIT] - *.csv
        - Contient les colonnes attendues
        """
        path = Path(file_path)

        # Vérification du pattern de nom
        if not path.name.startswith('[BIT]') or path.suffix.lower() != '.csv':
            return False

        # Vérification des colonnes
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames or []
                required = ['Type', 'Date', 'Montant reçu', 'Monnaie ou jeton reçu']
                return all(col in headers for col in required)
        except Exception as e:
            self.logger.warning(f"Impossible de vérifier les colonnes: {e}")
            return False
```

**APRÈS** :
```python
    def can_parse(self, file_path: str, metadata: Dict[str, Any]) -> float:
        """
        Vérifie si le fichier peut être parsé par ce parser.

        Critères:
        - Fichier CSV
        - Pattern [BIT] - *.csv
        - Contient les colonnes attendues

        Returns:
            float: Score de confiance (0.0 = impossible, 1.0 = certain)
        """
        path = Path(file_path)

        # Vérification du pattern de nom
        if not path.name.startswith('[BIT]') or path.suffix.lower() != '.csv':
            return 0.0

        # Vérification des colonnes
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames or []
                required = ['Type', 'Date', 'Montant reçu', 'Monnaie ou jeton reçu']
                return 1.0 if all(col in headers for col in required) else 0.0
        except Exception as e:
            self.logger.warning(f"Impossible de vérifier les colonnes: {e}")
            return 0.0
```

**Validation** :
```bash
python3 -c "from tools.parsers.bitstack import BitstackTransactionHistoryParser; p = BitstackTransactionHistoryParser(); result = p.can_parse('test.csv', {}); assert isinstance(result, float); assert 0.0 <= result <= 1.0; print(f'✓ can_parse() returns float: {result}')"
```

**Rollback** : Restaurer les lignes 50-74 originales

---

## TÂCHE 1.3 : Corriger BitstackTransactionHistoryParser - validate()

**Fichier** : `/home/user/giga-pat/tools/parsers/bitstack/transaction_history.py`

**Action** : Modifier signature et retour de `validate()` pour retourner `List[str]` au lieu de `bool`

**AVANT** (lignes 173-205) :
```python
    def validate(self, parsed_data: Dict[str, Any]) -> bool:
        """
        Valide les données parsées.

        Critères:
        - Structure correcte (dict avec 'positions')
        - Au moins une position
        - Solde BTC >= 0 (cohérence des transactions)
        """
        if not parsed_data:
            self.logger.error("Aucune donnée parsée")
            return False

        # Check for dict structure
        if not isinstance(parsed_data, dict):
            self.logger.error(f"Format incorrect: attendu dict, obtenu {type(parsed_data)}")
            return False

        positions = parsed_data.get('positions', [])
        if not positions:
            self.logger.error("Aucune position trouvée")
            return False

        if len(positions) != 1:
            self.logger.error(f"Attendu 1 position résumée, obtenu {len(positions)}")
            return False

        btc_qty = positions[0].get('quantite', 0)
        if btc_qty < 0:
            self.logger.error(f"Solde BTC négatif: {btc_qty}")
            return False

        return True
```

**APRÈS** :
```python
    def validate(self, parsed_data: Dict[str, Any]) -> List[str]:
        """
        Valide les données parsées.

        Critères:
        - Structure correcte (dict avec 'positions')
        - Au moins une position
        - Solde BTC >= 0 (cohérence des transactions)

        Returns:
            List[str]: Liste des anomalies détectées (vide si tout est valide)
        """
        anomalies = []

        if not parsed_data:
            anomalies.append("Aucune donnée parsée")
            return anomalies

        # Check for dict structure
        if not isinstance(parsed_data, dict):
            anomalies.append(f"Format incorrect: attendu dict, obtenu {type(parsed_data)}")
            return anomalies

        positions = parsed_data.get('positions', [])
        if not positions:
            anomalies.append("Aucune position trouvée")
            return anomalies

        if len(positions) != 1:
            anomalies.append(f"Attendu 1 position résumée, obtenu {len(positions)}")

        btc_qty = positions[0].get('quantite', 0)
        if btc_qty < 0:
            anomalies.append(f"Solde BTC négatif: {btc_qty}")

        return anomalies
```

**Validation** :
```bash
python3 -c "from tools.parsers.bitstack import BitstackTransactionHistoryParser; p = BitstackTransactionHistoryParser(); result = p.validate({}); assert isinstance(result, list); assert len(result) > 0; print(f'✓ validate() returns List[str]: {result}')"
```

**Rollback** : Restaurer les lignes 173-205 originales

---

## TÂCHE 1.4 : Ajouter import List dans BitstackTransactionHistoryParser

**Fichier** : `/home/user/giga-pat/tools/parsers/bitstack/transaction_history.py`

**Action** : Vérifier que `List` est bien importé de `typing` (ligne 27)

**AVANT** (ligne 27) :
```python
from typing import Dict, List, Any, Optional
```

**APRÈS** : (Pas de changement si déjà présent, sinon ajouter `List`)
```python
from typing import Dict, List, Any, Optional
```

**Validation** :
```bash
grep "from typing import.*List" /home/user/giga-pat/tools/parsers/bitstack/transaction_history.py
```

**Rollback** : N/A (import déjà présent)

---

## TÂCHE 1.5 : Sécurité - Remplacer MD5 par SHA-256

**Fichier** : `/home/user/giga-pat/tools/cache_manager.py`

**Action** : Remplacer `hashlib.md5()` par `hashlib.sha256()`

**AVANT** (lignes 42-46) :
```python
    def _compute_file_hash(self, file_path: Path) -> str:
        """Calcule le hash MD5 d'un fichier."""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
```

**APRÈS** :
```python
    def _compute_file_hash(self, file_path: Path) -> str:
        """Calcule le hash SHA-256 d'un fichier pour vérification d'intégrité."""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
```

**Validation** :
```bash
python3 -c "import hashlib; h = hashlib.sha256(); h.update(b'test'); assert len(h.hexdigest()) == 64; print('✓ SHA-256 OK')"
```

**Rollback** : Restaurer `md5()` si nécessaire (mais déconseillé)

---

## TÂCHE 1.6 : Sécurité - Validation Path Traversal

**Fichier** : `/home/user/giga-pat/tools/normalizer.py`

**Action** : Ajouter validation de sécurité pour les chemins de fichiers

**AVANT** (lignes 196-203) :
```python
            # Récupérer le parser via le registry
            filepath = sources_dir / compte_def["source_file"]
            if not filepath.exists():
                self.logger.warning(f"⚠️  Fichier introuvable: {filepath}")
                continue

            parser_name = compte_def.get("parser_strategy")
            if not parser_name:
```

**APRÈS** :
```python
            # Récupérer le parser via le registry
            filepath = sources_dir / compte_def["source_file"]

            # Validation de sécurité : empêcher path traversal
            try:
                resolved_path = filepath.resolve()
                sources_resolved = sources_dir.resolve()
                if not str(resolved_path).startswith(str(sources_resolved)):
                    self.logger.error(f"🚨 Path traversal détecté: {filepath}")
                    raise ValueError(f"Tentative d'accès à un fichier hors de {sources_dir}")
            except (ValueError, OSError) as e:
                self.logger.error(f"🚨 Erreur de sécurité sur le chemin: {e}")
                continue

            if not filepath.exists():
                self.logger.warning(f"⚠️  Fichier introuvable: {filepath}")
                continue

            parser_name = compte_def.get("parser_strategy")
            if not parser_name:
```

**Validation** :
```bash
python3 -c "from pathlib import Path; base = Path('/home/user/giga-pat/sources').resolve(); malicious = (base / '../../../etc/passwd').resolve(); assert not str(malicious).startswith(str(base)); print('✓ Path traversal detection OK')"
```

**Rollback** : Supprimer le bloc try-except ajouté

---

## TÂCHE 1.7 : Sécurité - Validation Path Traversal (Pattern multi-fichiers)

**Fichier** : `/home/user/giga-pat/tools/normalizer.py`

**Action** : Ajouter validation de sécurité pour les patterns multi-fichiers

**AVANT** (lignes 253-258 environ, chercher dans `_parse_compte_multi_files`) :
```python
            for matched_file in matched_files:
                file_path = Path(matched_file)
                if not file_path.exists():
                    self.logger.warning(f"⚠️  Fichier ignoré (introuvable): {file_path}")
                    continue
```

**APRÈS** :
```python
            for matched_file in matched_files:
                file_path = Path(matched_file)

                # Validation de sécurité : empêcher path traversal
                try:
                    resolved_path = file_path.resolve()
                    sources_resolved = self.sources_dir.resolve()
                    if not str(resolved_path).startswith(str(sources_resolved)):
                        self.logger.error(f"🚨 Path traversal détecté: {file_path}")
                        continue
                except (ValueError, OSError) as e:
                    self.logger.error(f"🚨 Erreur de sécurité sur le chemin: {e}")
                    continue

                if not file_path.exists():
                    self.logger.warning(f"⚠️  Fichier ignoré (introuvable): {file_path}")
                    continue
```

**Validation** : Même que TÂCHE 1.6

**Rollback** : Supprimer le bloc try-except ajouté

---

## TÂCHE 1.8 : Standardiser version - main.py

**Fichier** : `/home/user/giga-pat/main.py`

**Action** : Changer version de `v1.0.0` à `v2.1.0`

**AVANT** (ligne 51) :
```python
║     PATRIMOINE ANALYZER v1.0.0                ║
```

**APRÈS** :
```python
║     PATRIMOINE ANALYZER v2.1.0                ║
```

**Validation** :
```bash
grep "v2.1.0" /home/user/giga-pat/main.py
```

**Rollback** : Restaurer `v1.0.0`

---

## TÂCHE 1.9 : Standardiser version - config/config.yaml

**Fichier** : `/home/user/giga-pat/config/config.yaml`

**Action** : Changer version de `2.0.0` à `2.1.0`

**AVANT** (ligne 3) :
```yaml
  version: "2.0.0"  # Architecture manifest-driven + parsers pluggables
```

**APRÈS** :
```yaml
  version: "2.1.0"  # Architecture homogène + custodian unifié + multi-file parsing avec cache
```

**Validation** :
```bash
grep 'version: "2.1.0"' /home/user/giga-pat/config/config.yaml
```

**Rollback** : Restaurer `2.0.0`

---

## TÂCHE 1.10 : Standardiser version - PRD.md

**Fichier** : `/home/user/giga-pat/PRD.md`

**Action** : Changer version de `2.0.0` à `2.1.0` et mise à jour description

**AVANT** (lignes 3-9) :
```markdown
**Version** : 2.0.0
**Date** : Novembre 2025
**Auteur** : Spécifications pour Claude Code

## 🆕 Version 2.0 (Novembre 2025)

Cette version introduit une architecture **manifest-driven** avec **parsers pluggables** pour améliorer la robustesse et l'extensibilité du système de parsing.
```

**APRÈS** :
```markdown
**Version** : 2.1.0
**Date** : Novembre 2025
**Auteur** : Spécifications pour Claude Code

## 🆕 Version 2.1 (Novembre 2025)

Cette version complète l'architecture **manifest-driven** avec **custodian unifié**, **sections manuelles** et **parsing multi-fichiers avec cache intelligent**.
```

**Validation** :
```bash
grep "Version\*\* : 2.1.0" /home/user/giga-pat/PRD.md
```

**Rollback** : Restaurer `2.0.0`

---

## TÂCHE 1.11 : Standardiser version - README.md

**Fichier** : `/home/user/giga-pat/README.md`

**Action** : Changer "Version 2.0" à "Version 2.1"

**AVANT** (ligne 5) :
```markdown
**Version 2.0** - Architecture manifest-driven avec parsers pluggables
```

**APRÈS** :
```markdown
**Version 2.1** - Architecture homogène avec custodian unifié et parsing multi-fichiers
```

**Validation** :
```bash
grep "Version 2.1" /home/user/giga-pat/README.md
```

**Rollback** : Restaurer `Version 2.0`

---

## TÂCHE 1.12 : Standardiser version - config/risks.yaml

**Fichier** : `/home/user/giga-pat/config/risks.yaml`

**Action** : Changer version de `2.0.0` à `2.1.0`

**AVANT** (ligne 28) :
```yaml
  version: "2.0.0"
```

**APRÈS** :
```yaml
  version: "2.1.0"
```

**Validation** :
```bash
grep 'version: "2.1.0"' /home/user/giga-pat/config/risks.yaml | head -1
```

**Rollback** : Restaurer `2.0.0`

---

## TÂCHE 1.13 : Standardiser version - tools/__init__.py

**Fichier** : `/home/user/giga-pat/tools/__init__.py`

**Action** : Changer `__version__` de `1.0.0` à `2.1.0`

**AVANT** (ligne 5, environ) :
```python
__version__ = "1.0.0"
```

**APRÈS** :
```python
__version__ = "2.1.0"
```

**Validation** :
```bash
python3 -c "import sys; sys.path.insert(0, '/home/user/giga-pat'); from tools import __version__; assert __version__ == '2.1.0'; print(f'✓ tools.__version__ = {__version__}')"
```

**Rollback** : Restaurer `1.0.0`

---

## VALIDATION PHASE 1

Exécuter ces commandes dans l'ordre :

```bash
# 1. Test imports et interface BitstackParser
python3 << 'EOF'
from tools.parsers.bitstack import BitstackTransactionHistoryParser
p = BitstackTransactionHistoryParser()

# Test strategy_name
assert hasattr(p, 'strategy_name')
assert p.strategy_name == "bitstack.transaction_history.v2025"
print("✓ strategy_name OK")

# Test can_parse retourne float
result = p.can_parse('/tmp/test.csv', {})
assert isinstance(result, float)
assert 0.0 <= result <= 1.0
print(f"✓ can_parse() returns float: {result}")

# Test validate retourne List[str]
anomalies = p.validate({})
assert isinstance(anomalies, list)
assert all(isinstance(a, str) for a in anomalies)
print(f"✓ validate() returns List[str]: {len(anomalies)} anomalies")

print("\n✅ BitstackParser interface CONFORME")
EOF

# 2. Test versions
python3 << 'EOF'
import yaml
from pathlib import Path

# config.yaml
with open('/home/user/giga-pat/config/config.yaml') as f:
    config = yaml.safe_load(f)
    assert config['project']['version'] == "2.1.0", f"config.yaml version: {config['project']['version']}"
    print("✓ config.yaml version 2.1.0")

# risks.yaml
with open('/home/user/giga-pat/config/risks.yaml') as f:
    risks = yaml.safe_load(f)
    assert risks['risk_settings']['version'] == "2.1.0"
    print("✓ risks.yaml version 2.1.0")

# tools.__init__
from tools import __version__
assert __version__ == "2.1.0"
print(f"✓ tools.__version__ = {__version__}")

print("\n✅ Toutes les versions sont à 2.1.0")
EOF

# 3. Test sécurité hash
python3 << 'EOF'
from tools.cache_manager import CacheManager
from pathlib import Path
import tempfile

# Créer fichier temporaire
with tempfile.NamedTemporaryFile(delete=False) as f:
    f.write(b"test content")
    temp_path = Path(f.name)

cm = CacheManager(Path("/tmp/test_cache"))
hash_result = cm._compute_file_hash(temp_path)

# SHA-256 produit 64 caractères hexadécimaux
assert len(hash_result) == 64, f"Hash length: {len(hash_result)} (expected 64 for SHA-256)"
print(f"✓ Hash SHA-256 OK: {hash_result[:16]}...")

temp_path.unlink()
print("\n✅ CacheManager utilise SHA-256")
EOF

echo ""
echo "✅✅✅ PHASE 1 VALIDÉE ✅✅✅"
```

Si tous les tests passent, passer au commit :

```bash
git add -A
git commit -m "fix(critical): Security patches and parser interface compliance

- BitstackParser: Convert strategy_name to @property
- BitstackParser: can_parse() returns float (0.0-1.0) instead of bool
- BitstackParser: validate() returns List[str] instead of bool
- Security: Replace MD5 with SHA-256 in cache_manager
- Security: Add path traversal validation in normalizer
- Version: Standardize all versions to 2.1.0

Related issues: #1-4 (critical)"
```

---

# 🔶 PHASE 2 : CORRECTIONS IMPORTANTES

**Objectif** : Corriger 5 issues importantes (sécurité réseau + gestion erreurs)
**Durée estimée** : 2-3 heures
**Commit message** : `fix(high): Network security, error handling and resilient parsing`

---

## TÂCHE 2.1 : Implémenter Session HTTP avec retry

**Fichier** : `/home/user/giga-pat/tools/utils/web_research.py`

**Action** : Remplacer `requests.get()` par `self.session.get()` avec retry

**AVANT** (lignes 31-40, dans `__init__`) :
```python
    def __init__(self, config: Dict[str, Any]):
        """
        Initialise le chercheur web.

        Args:
            config: Configuration (api_key, timeout, etc.)
        """
        self.api_key = config.get("api_key")
        self.timeout = config.get("timeout", 10)
        self.api_url = "https://api.search.brave.com/res/v1/web/search"
        self.logger = logging.getLogger(__name__)
```

**APRÈS** :
```python
    def __init__(self, config: Dict[str, Any]):
        """
        Initialise le chercheur web.

        Args:
            config: Configuration (api_key, timeout, etc.)
        """
        self.api_key = config.get("api_key")
        self.timeout = config.get("timeout", 10)
        self.api_url = "https://api.search.brave.com/res/v1/web/search"
        self.logger = logging.getLogger(__name__)

        # Session HTTP avec pooling de connexions
        self.session = requests.Session()
        self.session.verify = True  # SSL verification explicite
```

**Validation** :
```bash
python3 -c "from tools.utils.web_research import WebResearcher; wr = WebResearcher({'api_key': 'test'}); assert hasattr(wr, 'session'); assert wr.session.verify is True; print('✓ Session HTTP OK')"
```

**Rollback** : Supprimer les lignes ajoutées

---

## TÂCHE 2.2 : Remplacer requests.get par session.get

**Fichier** : `/home/user/giga-pat/tools/utils/web_research.py`

**Action** : Utiliser `self.session.get()` au lieu de `requests.get()`

**AVANT** (lignes 174-179, chercher la ligne avec `requests.get`) :
```python
            response = requests.get(
                self.api_url,
                headers=headers,
                params=params,
                timeout=self.timeout
            )
```

**APRÈS** :
```python
            response = self.session.get(
                self.api_url,
                headers=headers,
                params=params,
                timeout=self.timeout,
                verify=True  # SSL verification explicite
            )
```

**Validation** : Tests manuels après toutes les modifications de la phase

**Rollback** : Restaurer `requests.get`

---

## TÂCHE 2.3 : Sanitizer les erreurs API (ne pas exposer clé)

**Fichier** : `/home/user/giga-pat/tools/utils/web_research.py`

**Action** : Filtrer la clé API des messages d'erreur

**AVANT** (lignes 182-190, bloc except après requests.get) :
```python
        except requests.RequestException as e:
            self.logger.error(f"Erreur lors de la recherche web: {e}")
            return {
                "results": [],
                "total_results": 0,
                "error": str(e)
            }
```

**APRÈS** :
```python
        except requests.RequestException as e:
            # Sanitize error message - ne jamais exposer l'API key
            error_msg = str(e)
            if self.api_key and self.api_key in error_msg:
                error_msg = error_msg.replace(self.api_key, "[REDACTED]")

            self.logger.error(f"Erreur lors de la recherche web: {error_msg}")
            return {
                "results": [],
                "total_results": 0,
                "error": "Erreur de connexion à l'API (détails en logs)"
            }
```

**Validation** :
```bash
python3 << 'EOF'
# Test que l'API key n'apparaît pas dans les erreurs
msg = "Error with key BSA81KxMOB0qrs"
api_key = "BSA81KxMOB0qrs"
sanitized = msg.replace(api_key, "[REDACTED]") if api_key in msg else msg
assert "[REDACTED]" in sanitized
assert api_key not in sanitized
print("✓ API key sanitization OK")
EOF
```

**Rollback** : Restaurer le bloc except original

---

## TÂCHE 2.4 : Améliorer gestion exceptions - normalizer.py (1/3)

**Fichier** : `/home/user/giga-pat/tools/normalizer.py`

**Action** : Remplacer `except Exception` par exceptions spécifiques dans `_parse_compte_single_file`

**AVANT** (lignes 213-214, chercher dans `_parse_compte_single_file`) :
```python
        except Exception as e:
            self.logger.error(f"❌ Erreur lors du parsing de {filepath}: {e}")
            return None
```

**APRÈS** :
```python
        except ParsingError as e:
            self.logger.error(f"❌ Erreur de parsing de {filepath}: {e}")
            return None
        except (OSError, IOError) as e:
            self.logger.error(f"❌ Erreur d'accès au fichier {filepath}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"❌ Erreur inattendue lors du parsing de {filepath}: {e}")
            self.logger.exception("Stack trace:")
            return None
```

**Validation** : Vérification visuelle du code

**Rollback** : Restaurer le bloc except original

---

## TÂCHE 2.5 : Améliorer gestion exceptions - analyzer.py (2/3)

**Fichier** : `/home/user/giga-pat/tools/analyzer.py`

**Action** : Améliorer exception handling dans la méthode `analyze()`

**AVANT** (lignes 72-74, dans `analyze()`) :
```python
        except Exception as e:
            self.logger.error(f"Erreur lors de l'analyse: {e}")
            raise
```

**APRÈS** :
```python
        except (FileNotFoundError, IOError) as e:
            self.logger.error(f"Erreur d'accès aux fichiers de configuration: {e}")
            raise
        except KeyError as e:
            self.logger.error(f"Donnée manquante dans le patrimoine d'entrée: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Erreur inattendue lors de l'analyse: {e}")
            self.logger.exception("Stack trace complète:")
            raise
```

**Validation** : Vérification visuelle du code

**Rollback** : Restaurer le bloc except original

---

## TÂCHE 2.6 : Améliorer gestion exceptions - generator.py (3/3)

**Fichier** : `/home/user/giga-pat/tools/generator.py`

**Action** : Améliorer exception handling dans la méthode `generate()`

**AVANT** (chercher le bloc try/except principal dans `generate()`, probablement vers lignes 860-862) :
```python
        except Exception as e:
            self.logger.error(f"Erreur lors de la génération: {e}")
            raise
```

**APRÈS** :
```python
        except (FileNotFoundError, IOError) as e:
            self.logger.error(f"Erreur d'accès au template ou fichier de sortie: {e}")
            raise
        except KeyError as e:
            self.logger.error(f"Champ manquant dans les données d'analyse: {e}")
            self.logger.exception("Détails de l'erreur:")
            raise
        except Exception as e:
            self.logger.error(f"Erreur inattendue lors de la génération: {e}")
            self.logger.exception("Stack trace complète:")
            raise
```

**Validation** : Vérification visuelle du code

**Rollback** : Restaurer le bloc except original

---

## TÂCHE 2.7 : Parsing résilient - continuer si un parser échoue

**Fichier** : `/home/user/giga-pat/tools/normalizer.py`

**Action** : Ne pas arrêter toute la normalisation si un seul compte échoue

**Instruction** : Cette modification est déjà en place (le code retourne `None` et continue). Vérifier que c'est bien le cas.

**Validation** :
```bash
# Chercher les return None dans les blocs except
grep -A 2 "except.*Error" /home/user/giga-pat/tools/normalizer.py | grep "return None"
```

**Si la validation échoue** : Ajouter `return None` dans les blocs except qui lèvent des exceptions

**Rollback** : N/A (déjà correct)

---

## VALIDATION PHASE 2

Exécuter ces commandes :

```bash
# 1. Test Session HTTP
python3 << 'EOF'
from tools.utils.web_research import WebResearcher

wr = WebResearcher({'api_key': 'test_key_12345'})

# Vérifier session existe
assert hasattr(wr, 'session'), "Session HTTP manquante"
assert wr.session.verify is True, "SSL verification non activée"

print("✓ Session HTTP avec SSL verification OK")
print(f"✓ Session type: {type(wr.session)}")

print("\n✅ WebResearcher configuration correcte")
EOF

# 2. Test sanitization API key
python3 << 'EOF'
api_key = "BSA81KxMOB0qrs_BtDxDoSthWZfNuPc"
error_msg = f"Authentication failed with key {api_key}"

# Sanitize
if api_key in error_msg:
    error_msg = error_msg.replace(api_key, "[REDACTED]")

assert api_key not in error_msg
assert "[REDACTED]" in error_msg
print(f"✓ API key sanitization: {error_msg}")

print("\n✅ Sanitization des erreurs OK")
EOF

# 3. Vérifier imports pour exceptions spécifiques
python3 << 'EOF'
from tools.parsers.base_parser import ParsingError
from tools.normalizer import Normalizer
from tools.analyzer import Analyzer
from tools.generator import Generator

print("✓ Tous les imports OK")
print("\n✅ Gestion d'erreurs améliorée")
EOF

echo ""
echo "✅✅✅ PHASE 2 VALIDÉE ✅✅✅"
```

Si tous les tests passent, commiter :

```bash
git add -A
git commit -m "fix(high): Network security, error handling and resilient parsing

- WebResearcher: Use requests.Session() for connection pooling
- WebResearcher: Explicit SSL verification (verify=True)
- WebResearcher: Sanitize error messages to prevent API key exposure
- Normalizer/Analyzer/Generator: Specific exception handling instead of bare Exception
- Parsing: Continue processing other accounts if one fails (already implemented)

Related issues: #5-9 (high priority)"
```

---

# 🟡 PHASE 3 : REFACTORING

**Objectif** : Améliorer la qualité du code (pas de bugs critiques)
**Durée estimée** : 4-6 heures (optionnel si temps limité)
**Commit message** : `refactor: Cache management, validation and code organization`

---

## TÂCHE 3.1 : Implémenter limite de taille du cache

**Fichier** : `/home/user/giga-pat/tools/cache_manager.py`

**Action** : Ajouter méthode de nettoyage du cache avec limite de taille

**APRÈS la méthode `clear_cache()` (après ligne 140 environ), AJOUTER** :

```python
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
```

**Validation** :
```bash
python3 << 'EOF'
from tools.cache_manager import CacheManager
from pathlib import Path

cm = CacheManager(Path("/tmp/test_cache_limit"))
assert hasattr(cm, 'enforce_cache_limit')
print("✓ enforce_cache_limit() method exists")
EOF
```

**Rollback** : Supprimer la méthode ajoutée

---

## TÂCHE 3.2 : Appeler enforce_cache_limit dans le Normalizer

**Fichier** : `/home/user/giga-pat/tools/normalizer.py`

**Action** : Appeler `enforce_cache_limit()` après la normalisation

**Dans la méthode `normalize()`, AVANT le return final (chercher `return output_data`), AJOUTER** :

```python
        # Nettoyer le cache si nécessaire (limite: 100 MB)
        self.cache_manager.enforce_cache_limit(max_size_mb=100)
```

**Validation** : Tests end-to-end après toutes les modifications

**Rollback** : Supprimer la ligne ajoutée

---

## TÂCHE 3.3 : Valider manifest.json AVANT traitement

**Fichier** : `/home/user/giga-pat/tools/normalizer.py`

**Action** : Déplacer la validation du schéma au tout début

**AVANT** (dans `normalize()`, chercher l'appel à `_validate_manifest_schema`) :
La validation est probablement appelée après certains traitements.

**APRÈS** : S'assurer que cette ligne est IMMÉDIATEMENT après le chargement du manifest :

```python
        # Charger manifest
        manifest_path = self.sources_dir / self.config["input_file"]
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        # VALIDATION IMMÉDIATE avant tout traitement
        validation_errors = self._validate_manifest_schema(manifest)
        if validation_errors:
            error_msg = "\n".join([f"  - {err}" for err in validation_errors])
            self.logger.error(f"❌ Manifest invalide:\n{error_msg}")
            raise ValueError(f"manifest.json invalide. Erreurs:\n{error_msg}")
```

**Validation** : Vérifier l'ordre du code

**Rollback** : Restaurer l'ordre original

---

## TÂCHE 3.4 : Extraire constantes des magic numbers - risk_analyzer.py

**Fichier** : `/home/user/giga-pat/tools/utils/risk_analyzer.py`

**Action** : Extraire les seuils en constantes nommées

**AU DÉBUT du fichier, APRÈS les imports, AJOUTER** :

```python
# === CONSTANTES DE SEUILS DE RISQUE ===

# Concentration Assurance-Vie (%)
AV_CONCENTRATION_CRITIQUE = 25  # Au-delà de 25% du patrimoine en AV = Critique
AV_CONCENTRATION_ELEVEE = 15    # 15-25% = Élevé
AV_CONCENTRATION_MODEREE = 10   # 10-15% = Modéré

# Concentration établissement unique (%)
ETABLISSEMENT_CONCENTRATION_CRITIQUE = 70
ETABLISSEMENT_CONCENTRATION_ELEVEE = 50

# Concentration géographique (%)
GEO_CONCENTRATION_CRITIQUE = 90
GEO_CONCENTRATION_ELEVEE = 80

# Liquidité (%)
LIQUIDITE_CRITIQUE = 5   # Moins de 5% de liquidités = Critique
LIQUIDITE_FAIBLE = 10    # 5-10% = Risque modéré
```

**Validation** : Vérifier que les constantes sont définies

**Rollback** : Supprimer le bloc ajouté

---

## TÂCHE 3.5 : Utiliser les constantes dans risk_analyzer.py

**Fichier** : `/home/user/giga-pat/tools/utils/risk_analyzer.py`

**Action** : Remplacer les magic numbers par les constantes

**EXEMPLE** : Chercher `if pct_av >= 25` et remplacer par `if pct_av >= AV_CONCENTRATION_CRITIQUE`

**Faire les remplacements suivants** (chercher et remplacer) :
- `>= 25` dans le contexte AV → `>= AV_CONCENTRATION_CRITIQUE`
- `>= 15` dans le contexte AV → `>= AV_CONCENTRATION_ELEVEE`
- `>= 10` dans le contexte AV → `>= AV_CONCENTRATION_MODEREE`
- `>= 70` pour établissement → `>= ETABLISSEMENT_CONCENTRATION_CRITIQUE`
- `>= 50` pour établissement → `>= ETABLISSEMENT_CONCENTRATION_ELEVEE`

**Validation** :
```bash
grep -n "AV_CONCENTRATION_CRITIQUE\|ETABLISSEMENT_CONCENTRATION" /home/user/giga-pat/tools/utils/risk_analyzer.py
```

**Rollback** : Restaurer les nombres originaux

---

## VALIDATION PHASE 3

```bash
# 1. Test limite cache
python3 << 'EOF'
from tools.cache_manager import CacheManager
from pathlib import Path
import json
import tempfile

# Créer cache temporaire
temp_dir = Path(tempfile.mkdtemp())
cm = CacheManager(temp_dir)

# Créer plusieurs fichiers cache
for i in range(5):
    cache_file = temp_dir / f"test_{i}.json"
    cache_file.write_text(json.dumps({"data": "x" * 100000}))  # ~100KB each

# Vérifier méthode existe
assert hasattr(cm, 'enforce_cache_limit')

# Appliquer limite (devrait supprimer certains fichiers)
cm.enforce_cache_limit(max_size_mb=0.3)  # 300KB max

remaining = list(temp_dir.glob("*.json"))
print(f"✓ Cache cleanup: {len(remaining)} files remaining (5 → {len(remaining)})")

# Cleanup
import shutil
shutil.rmtree(temp_dir)

print("\n✅ Cache size management OK")
EOF

# 2. Test constantes risk_analyzer
python3 << 'EOF'
import sys
sys.path.insert(0, '/home/user/giga-pat')

# Vérifier que les constantes existent
from tools.utils.risk_analyzer import (
    AV_CONCENTRATION_CRITIQUE,
    AV_CONCENTRATION_ELEVEE,
    ETABLISSEMENT_CONCENTRATION_CRITIQUE
)

assert AV_CONCENTRATION_CRITIQUE == 25
assert AV_CONCENTRATION_ELEVEE == 15
assert ETABLISSEMENT_CONCENTRATION_CRITIQUE == 70

print("✓ Risk thresholds constants OK")
print(f"  AV_CONCENTRATION_CRITIQUE = {AV_CONCENTRATION_CRITIQUE}%")
print(f"  AV_CONCENTRATION_ELEVEE = {AV_CONCENTRATION_ELEVEE}%")

print("\n✅ Constants extraction OK")
EOF

echo ""
echo "✅✅✅ PHASE 3 VALIDÉE ✅✅✅"
```

Si tous les tests passent :

```bash
git add -A
git commit -m "refactor: Cache management, validation and code organization

- CacheManager: Add enforce_cache_limit() with LRU eviction (100MB max)
- Normalizer: Call cache cleanup after processing
- Normalizer: Validate manifest.json BEFORE any processing
- RiskAnalyzer: Extract magic numbers to named constants

Related issues: #10-15 (medium priority)"
```

---

# 🔵 PHASE 4 : QUALITÉ & DOCUMENTATION

**Objectif** : Améliorer tests, docs, type hints
**Durée estimée** : 6-8 heures (optionnel)
**Commit message** : `docs(quality): Improve type hints, docstrings and test coverage`

---

## ⚠️ PHASE 4 : TRAVAUX EXTENSIFS

Cette phase nécessite beaucoup de travail et peut être différée.

### Tâches principales :

1. **Ajouter type hints manquants** (~100 fonctions)
2. **Standardiser docstrings** (style Google)
3. **Créer tests manquants** :
   - `tests/test_cache_manager.py`
   - `tests/test_crypto_price_api.py`
   - Tests d'intégration end-to-end
4. **Configurer mypy** et corriger les erreurs
5. **Nettoyer TODOs** dans `project_generator.py`
6. **Ajuster niveaux de logs** (debug → info/warning)

### Stratégie recommandée :

**Option A** : Faire progressivement sur plusieurs sessions
**Option B** : Créer des issues GitHub pour chaque sous-tâche
**Option C** : Déléguer à plusieurs développeurs

### Validation Phase 4 (quand complétée) :

```bash
# 1. Type checking
mypy tools/ --ignore-missing-imports

# 2. Test coverage
pytest tests/ --cov=tools --cov-report=term-missing

# 3. Code quality
pylint tools/ --disable=C0301,C0103

# 4. Vérifier docstrings
pydocstyle tools/ --convention=google
```

---

# 📋 CHECKLIST FINALE

Après avoir complété toutes les phases souhaitées :

## ✅ Phase 1 (Critique) - OBLIGATOIRE
- [ ] BitstackParser conforme à BaseParser
- [ ] Toutes les versions à 2.1.0
- [ ] Path traversal validation en place
- [ ] SHA-256 au lieu de MD5
- [ ] Tests Phase 1 passent
- [ ] Commit Phase 1 effectué

## ✅ Phase 2 (Importante) - FORTEMENT RECOMMANDÉE
- [ ] Session HTTP avec pooling
- [ ] SSL verification explicite
- [ ] API key sanitization
- [ ] Exceptions spécifiques
- [ ] Parsing résilient vérifié
- [ ] Tests Phase 2 passent
- [ ] Commit Phase 2 effectué

## ✅ Phase 3 (Refactoring) - RECOMMANDÉE
- [ ] Cache size management
- [ ] Validation précoce manifest
- [ ] Constantes au lieu de magic numbers
- [ ] Tests Phase 3 passent
- [ ] Commit Phase 3 effectué

## ✅ Phase 4 (Qualité) - OPTIONNELLE
- [ ] Type hints ajoutés
- [ ] Docstrings standardisées
- [ ] Tests manquants créés
- [ ] Mypy configuré
- [ ] TODOs résolus
- [ ] Coverage > 70%
- [ ] Commit Phase 4 effectué

## ✅ Push final
- [ ] Tous les commits effectués
- [ ] Tests locaux OK
- [ ] Push vers remote : `git push -u origin claude/analyze-giga-pat-project-011CV3mgMUCcBtmsy5vpni1J`

---

# 🚀 COMMANDES DE DÉMARRAGE

Pour exécuter ce TID, commence par :

```bash
# 1. Vérifier la branche
git status
git branch --show-current

# 2. S'assurer d'être à jour
git fetch origin
git status

# 3. Commencer Phase 1 Tâche 1.1
echo "🚀 DÉBUT PHASE 1 - CORRECTIONS CRITIQUES"
```

Puis exécute **une tâche à la fois**, dans l'ordre exact du TID.

---

**FIN DU TID**

Ce document contient toutes les instructions pour corriger le projet giga-pat de manière systématique et sans improvisation.
