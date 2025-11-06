# 📊 Patrimoine Analyzer

Générateur automatisé de rapports patrimoniaux professionnels avec analyse approfondie et recherches web.

## 🎯 Objectif

Transformer vos fichiers sources (CSV, PDF, Markdown) en un rapport patrimonial complet avec :
- ✅ Analyse détaillée de la répartition des actifs
- ✅ Identification des risques (concentration, réglementaire, fiscal, marché, liquidité, politique, changes)
- ✅ Recommandations prioritisées et actionnables
- ✅ Stress tests (crise bancaire, krach, perte emploi, crise immobilière...)
- ✅ Recherches web exhaustives avec sources citées et affichées
- ✅ Profil investisseur personnalisé sur la page de couverture
- ✅ Rapport HTML premium professionnel **autonome** (CSS intégré)

## 🎯 Fonctionnalités détaillées

### Analyse des risques (7 catégories)
1. **Concentration** : Détection des sur-expositions par établissement, juridiction ou classe d'actifs
2. **Réglementaire** : Vérification Loi Sapin 2, garantie dépôts 100k€, plafonds PEA
3. **Fiscal** : Analyse PFU, fiscalité AV, IFI
4. **Marché** : Volatilité actions, corrélations entre actifs
5. **Liquidité** : Identification des actifs bloqués (AV, PER, immobilier)
6. **Politique** : Risques d'instabilité, nationalisation
7. **Changes** : Exposition aux devises étrangères (USD, crypto)

### Recherches web intelligentes
- Requêtes automatiques via Brave Search API
- 15-18 recherches par analyse
- Sources web citées et affichées dans chaque section de risque
- Sections dépliables pour consulter les sources

### Profil investisseur personnalisé
- Affichage du profil complet sur la page de couverture
- Format: Prénom NOM • âge • situation • profil • profession • revenu
- Extrait automatiquement depuis `sources/patrimoine.md`

## 🚀 Installation

### Prérequis
- Python 3.10 ou supérieur
- Clé API Brave Search (pour recherches web)

### Installation

```bash
# Installation des packages Python
pip install -r requirements.txt

# Configuration API Brave Search
# 1. Obtenez votre clé gratuite sur: https://api.search.brave.com/app/dashboard
# 2. Copiez .env.example vers .env
cp .env.example .env

# 3. Éditez .env et ajoutez votre clé API
export BRAVE_API_KEY="votre-clé-api-brave"
```

## 📁 Structure du projet

```
patrimoine-analyzer/
├── sources/              # 📥 VOS fichiers sources (patrimoine.md, CSV, PDF)
├── templates/            # 📄 Template HTML + CSS (modifiable)
│   ├── rapport_template.html
│   └── rapport.css       # Feuille de style (incorporée automatiquement)
├── generated/            # 📤 Rapports générés (automatique)
├── logs/                 # 📋 Logs d'exécution (automatique)
├── tools/                # 🛠️ Scripts Python
├── config/               # ⚙️ Configuration
└── main.py               # 🚀 Point d'entrée
```

## 📝 Utilisation

### 1. Préparer les sources

Placez vos fichiers dans `sources/` :

```
sources/
├── patrimoine.md         # Point d'entrée principal
├── [CA] - PEA.pdf
├── [CA] - PEA-PME.pdf
├── [CA] - AV.pdf
└── ... (autres fichiers CSV/PDF)
```

### 2. Générer le rapport

**Option 1 : Commande Python**
```bash
python main.py
```

**Option 2 : Commande slash (Claude Code uniquement)**
```
/report
```

### 3. Consulter le rapport

Ouvrez le fichier généré :
```
generated/rapport_20251021_143330.html
```

Le rapport HTML est **complètement autonome** :
- ✅ CSS incorporé directement dans le fichier
- ✅ Peut être déplacé, partagé ou archivé sans dépendances
- ✅ Aucun fichier CSS externe requis

## ⚙️ Configuration

Modifiez `config/config.yaml` pour ajuster :
- Seuils de risques
- Nombre max de recherches web
- Chemins de fichiers
- Format de dates

## 🎨 Personnalisation du template

Les templates sont **modifiables librement** :

**Template HTML** (`templates/rapport_template.html`) :
- Modifiez la structure des sections
- Ajoutez/supprimez des éléments
- ⚠️ Conservez les attributs `data-field` et `data-repeat` pour l'injection de données

**Feuille de style** (`templates/rapport.css`) :
- Ajustez les couleurs (variables CSS en haut du fichier)
- Modifiez la mise en page et les espacements
- Personnalisez les styles des badges et alertes
- Le CSS est **automatiquement incorporé** dans le HTML final

## 📈 Historique des rapports

Tous les rapports sont conservés avec horodatage :
```
generated/
├── rapport_20251021_143330.html
├── rapport_20251020_091544.html
└── rapport_20251015_164522.html
```

## 🔍 Résolution de problèmes

### Erreur "Fichier introuvable"
- Vérifiez que `patrimoine.md` existe dans `sources/`
- Vérifiez que tous les fichiers référencés existent

### Erreur "API timeout"
- Connexion internet instable
- Le script retry automatiquement 3×

### Rapport incomplet
- Consultez `logs/rapport_YYYYMMDD_HHMMSS.log`

## 📄 Licence

Usage personnel uniquement. Tous droits réservés.

---

**Version** : 1.0.0
**Dernière mise à jour** : Octobre 2025
