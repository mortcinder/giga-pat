# BoursoBank Parsers

## PER v2025 (`per_v2025.py`)

### Problème : Encodage Unicode propriétaire

Les PDFs de relevés PER BoursoBank utilisent un **encodage propriétaire** qui remplace TOUS les caractères par des codes Unicode dans la zone "Private Use Area" (U+E000 à U+F8FF).

**Exemple** :
- Le texte "PER 1,234.56 €" apparaît comme `\ue0d8\ue0c6\ue0da \ue0f2\ue06c\ue0f3\ue0f4\ue0f5\ue04c\ue0f6\ue0f7 \ue113`
- Tous les chiffres, lettres et symboles sont encodés de cette manière

### Solution implémentée

#### 1. Fonction `clean_pdf_text()` (lignes 14-133)

Mapping complet de 123 caractères :

**Chiffres** :
- `\ue0f1` → `0`
- `\ue0f2` → `1`
- ... jusqu'à `\ue0fa` → `9`

**Lettres majuscules** :
- `\ue0c2` → `A`
- `\ue0c3` → `B`
- ... jusqu'à `\ue0ea` → `Y`

**Lettres minuscules** :
- `\ue082` → `a`
- `\ue083` → `b`
- ... jusqu'à `\ue0aa` → `z`

**Ponctuation et symboles** :
- `\ue06c` → `,` (virgule)
- `\ue113` → `€` (euro)
- `\ue062` → `/` (slash)
- `\ue04c` → `.` (point)
- etc. (voir code complet)

#### 2. Gestion des lignes fusionnées

Certaines lignes de tableau contiennent **plusieurs fonds fusionnés** :
```
PD ISHARES FUND A
PD ISHARES FUND B    |    € 1,190.76
                           € 1,162.88
```

**Détection** : Pattern `\nPD ` dans le nom du support
**Solution** : Split des noms et association avec chaque montant trouvé (lignes 324-362)

#### 3. Stratégie de fallback

Si l'extraction PDF échoue complètement :
1. Tentative d'extraction standard (`_parse_pdf_standard`)
2. Si échec → fallback vers montant manuel (`_fallback_manual`)
3. Montant recherché dans : `metadata.montant_manuel` ou `metadata.montant`

**Indicateur** : `metadata_parsing.fallback_used = true` dans le JSON de sortie

### Utilisation

Dans `manifest.json` :

```json
{
  "id": "bob_per_004",
  "custodian": "boursobank",
  "custodian_name": "BoursoBank",
  "type_compte": "PER",
  "source_file": "[BOB] - PER.pdf",
  "parser_strategy": "boursobank.per.v2025"
}
```

### Vérification parsing réussi

Logs à chercher :
```
[INFO] Tentative parsing avec boursobank.per.v2025...
[INFO] ✓ Parsing réussi avec boursobank.per.v2025
[INFO]     ✓ 9 éléments parsés
```

Dans `patrimoine_input.json`, vérifier :
```json
{
  "metadata_parsing": {
    "parser_used": "boursobank.per.v2025",
    "extraction_method": "pdf_standard",
    "fallback_used": false
  }
}
```

Si `fallback_used: true`, le parsing PDF a échoué et le montant vient de `metadata.montant_manuel`.

### Débogage

Si le parsing échoue :

1. **Vérifier le texte brut extrait** :
```python
import pdfplumber
with pdfplumber.open('path/to/per.pdf') as pdf:
    text = pdf.pages[0].extract_text()
    print(text[:500])  # Affiche les 500 premiers caractères
```

2. **Analyser les codes Unicode** :
```python
for char in text[:100]:
    print(f"{char} = U+{ord(char):04X}")
```

3. **Tester le nettoyage** :
```python
from tools.parsers.boursobank.per_v2025 import clean_pdf_text
cleaned = clean_pdf_text(text)
print(cleaned[:500])
```

### Notes techniques

- **Raw strings** : Les docstrings utilisent `r"""` pour éviter que Python interprète `\ue0xx` comme des séquences d'échappement
- **Regex cleanup** : `re.sub(r'[\ue000-\uf8ff]', '', cleaned)` supprime les caractères non mappés restants
- **Performance** : Le nettoyage s'applique à toutes les pages ET à toutes les cellules de tableaux pour garantir l'extraction complète

### Historique

- **14 novembre 2025** : Implémentation initiale avec mapping complet et gestion des lignes fusionnées
- **Problème résolu** : Parsing qui échouait avec `ParsingError: PDF vide ou corrompu`
- **Résultat** : 9 positions extraites, montant total 3 930,45 € (correspondant à la page 1 du PDF)
