# 📊 Patrimoine Analyzer

Générateur automatisé de rapports patrimoniaux professionnels avec analyse approfondie et recherches web.

## 🎯 Objectif

Transformer vos fichiers sources (CSV, PDF, Markdown) en un rapport patrimonial complet avec :
- ✅ Analyse détaillée de la répartition des actifs
- ✅ **Identification des risques v2.0** (7 catégories + détection dynamique contextuelle)
- ✅ Recommandations prioritisées et actionnables
- ✅ Stress tests (crise bancaire, krach, perte emploi, crise immobilière...)
- ✅ **Optimisation de portefeuille (Markowitz)** avec frontière efficiente et ratio de Sharpe
- ✅ **4 profils d'investisseur configurables** (default, dynamique, équilibré, prudent)
- ✅ **Benchmark gap** : comparaison allocation actuelle vs cibles par profil
- ✅ **Scores enrichis v2.0** avec labels qualitatifs et détails complets
- ✅ Recherches web exhaustives avec sources citées et affichées
- ✅ Profil investisseur personnalisé sur la page de couverture
- ✅ Rapport HTML premium professionnel **autonome** (CSS intégré)

## 🎯 Fonctionnalités détaillées

### Analyse des risques (7 catégories + détection dynamique v2.0)
1. **Concentration** : Détection des sur-expositions par établissement, juridiction ou classe d'actifs
2. **Réglementaire** : Vérification Loi Sapin 2, garantie dépôts 100k€, plafonds PEA
3. **Fiscal** : Analyse PFU, fiscalité AV, IFI
4. **Marché** : Volatilité actions, corrélations entre actifs
5. **Liquidité** : Identification des actifs bloqués (AV, PER, immobilier)
6. **Politique** : Risques d'instabilité, nationalisation
7. **Changes** : Exposition aux devises étrangères (USD, crypto)

**🆕 Détection dynamique v2.0** :
- **Architecture hybride** : Risques structurels + risques contextuels
- **Risques contextuels** : Détection automatique de risques émergents via recherche web
  - Actualité économique France
  - Risques bancaires systémiques
  - Évolution fiscalité
  - Risques géopolitiques
  - Volatilité marchés
  - Régulation crypto
- **Configuration** : Activation/désactivation dans `config/risks.yaml`
- **Performance** : +10-20s si activé (+6-12 recherches web)

### Recherches web intelligentes
- Requêtes automatiques via Brave Search API
- 15-18 recherches par analyse
- Sources web citées et affichées dans chaque section de risque
- Sections dépliables pour consulter les sources

### Optimisation de portefeuille (Markowitz)
- **Frontière efficiente** : Calcul automatique du portefeuille optimal
- **Ratio de Sharpe** : Comparaison portefeuille actuel vs optimal
- **Graphique PNG intégré** : Visualisation de la frontière efficiente et inefficiente
- **Recommandations d'allocation** : Propositions concrètes pour améliorer le rendement/risque
- **Méthode statistique** : Basé sur moyennes historiques (pas d'API externe)
- **Configuration flexible** : Tous les paramètres dans `config/analysis.yaml`

### Profils d'investisseur configurables
Le système supporte **4 profils d'investisseur** avec des paramètres adaptés à chaque horizon et tolérance au risque :

1. **Default** : Statistiques historiques long terme (20-30 ans)
   - Actions : 60-75% | Obligations : 15-25% | Liquidités : 5-10%
   - Profil équilibré classique

2. **Dynamique** : Croissance agressive (jeune actif, horizon >15 ans)
   - Actions : 70-85% | Obligations : 5-15% | Liquidités : 3-8%
   - Maximisation du potentiel de croissance

3. **Équilibré** : Compromis rendement/risque (horizon 10-15 ans)
   - Actions : 50-65% | Obligations : 20-30% | Liquidités : 5-12%
   - Balance entre sécurité et performance

4. **Prudent** : Préservation du capital (proche retraite)
   - Actions : 30-45% | Obligations : 25-40% | Liquidités : 10-20%
   - Priorité à la stabilité

**Configuration** : Modifiez `config/config.yaml` → `analysis.active_profile` pour changer de profil.

### Benchmark gap (écarts d'allocation)
- **Comparaison automatique** : Allocation actuelle vs cibles du profil sélectionné
- **Colonne dédiée** : "Écart benchmark" dans le tableau des classes d'actifs
- **5 niveaux de statut** :
  - ✅ Dans la cible (±2pts)
  - ⚠️ Sur/sous-pondéré modéré (<10pts hors bornes)
  - 🚨 Sur/sous-pondéré fort (≥10pts hors bornes)
- **Badges colorés** : Identification visuelle des déséquilibres majeurs

### Scores enrichis v3.0
Les 5 scores (0-10) incluent désormais des **labels qualitatifs simplifiés** et des **détails complets** :

1. **Diversification (v1.1)** : "Excellente", "Bonne", "Modérée", "Forte concentration", "Critique"
   - Composantes institutionnelles et juridictionnelles pondérées
   - 3 bonus : ≥5 classes d'actifs, ≥10 positions, >15% international

2. **Résilience (v1.0)** : "Robuste", "Solide", "Vulnérabilités", "Vulnérable", "Critique"
   - Impact des stress tests et nombre de risques critiques

3. **Liquidité (v2.0)** : "Excellente", "Bonne", "Adéquate", "Faible", "Critique"
   - Ratio liquidités/cible adapté au profil (9-15 mois selon profil)
   - Alertes sur-liquidité et sous-liquidité

4. **Fiscalité (v2.0)** : "Excellente", "Bonne", "Moyenne", "Perfectible", "Défavorable"
   - Analyse enveloppes fiscales (PEA, AV, PER, CTO, crypto)
   - Liste bonus/pénalités détaillée

5. **Croissance (v2.0)** : "Exceptionnel", "Élevé", "Équilibré", "Modéré", "Limité"
   - Exposition actions avec contexte profil
   - Fourchette optimale personnalisée

**Affichage** (design épuré v3.0) :
- Sections statiques avec bordure gauche grise (pas de collapsible)
- Badges avec labels simplifiés (1-2 mots)
- Notes formatées en listes avec libellés standardisés sur la même ligne
- Parfait pour l'impression, plus concis et professionnel

### Profil investisseur personnalisé
- Affichage du profil complet sur la page de couverture
- Format: Prénom NOM • âge • situation • profil • profession • revenu
- Données personnelles extraites de `sources/patrimoine.md`
- **Type de profil** (Dynamique/Équilibré/Prudent) déterminé par `config/config.yaml → analysis.active_profile`

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

Le système utilise **3 fichiers de configuration YAML** pour une personnalisation complète :

### 1. `config/config.yaml` (Configuration principale)
Paramètres généraux du système :
- **Chemins** : sources/, templates/, generated/, logs/
- **Seuils de risques** : Concentration, liquidité, juridiction
- **Recherches web** : Nombre max (50), timeout (30s), retry (3×)
- **Profil actif** : Sélection du profil d'investisseur (`analysis.active_profile`)
- **Formats** : Dates, noms de fichiers

### 2. `config/analysis.yaml` (Configuration de l'analyse - 827 lignes)
Tous les paramètres d'analyse et d'optimisation :
- **4 profils d'investisseur** : default, dynamique, équilibré, prudent
  - Statistiques de marché par classe d'actifs (rendements, volatilités)
  - Matrice de corrélations entre classes d'actifs
- **Benchmarks d'allocation** : Fourchettes cibles (min/target/max) par classe et profil
- **Paramètres des 5 scores** : Diversification, résilience, liquidité, fiscalité, croissance
  - Pondérations, pénalités, bonus, labels qualitatifs
- **Classification des actifs** : Tickers et mots-clés pour identifier les classes
- **Optimiseur Markowitz** : Contraintes, itérations, paramètres graphiques
- **Interprétation** : Seuils pour l'analyse des résultats

**Personnalisation** : Vous pouvez créer vos propres profils ou ajuster les benchmarks existants.

### 3. `config/research_prompts.yaml` (Prompts de recherche web)
Templates de requêtes pour les recherches Brave Search API par catégorie de risque.

### 4. `config/risks.yaml` (Configuration des risques v2.0 - 350 lignes) 🆕
Système de détection des risques dynamique et configurable :
- **risk_settings** : Activation/désactivation de la détection contextuelle
- **structural_risks** : Définitions des 13 risques structurels (concentration, réglementaire, fiscal, etc.)
- **contextual_searches** : Configuration des 6 recherches contextuelles pour détecter les risques émergents
- **metadata** : Versioning et changelog

**Activer/désactiver la détection contextuelle** :
```yaml
# config/risks.yaml
risk_settings:
  enable_contextual_detection: true  # false pour désactiver
```

**Ajouter une nouvelle recherche contextuelle** :
```yaml
contextual_searches:
  nouvelle_reforme:
    enabled: true
    priority: "high"
    queries:
      - "nouvelle taxe patrimoine France 2026"
      - "réforme taxation immobilière"
```

**Exemple de modification de profil** :
```yaml
# Modifier le profil actif dans config.yaml
analysis:
  active_profile: "dynamique"  # Changer de default à dynamique

# Ajuster les benchmarks dans analysis.yaml
benchmarks:
  dynamique:
    Actions:
      min: 75      # Au lieu de 70
      target: 80   # Au lieu de 77.5
      max: 85
```

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

## 🧪 Tests unitaires

Le projet inclut une suite complète de tests pour chaque composant :

```bash
# Tester la normalisation (Stage 1)
python tests/test_normalizer.py

# Tester l'analyse (Stage 2)
python tests/test_analyzer.py

# Tester la génération HTML (Stage 3)
python tests/test_generator.py

# Tester les recherches web
python tests/test_web_research.py

# Tests spécialisés
python tests/test_benchmark_gap.py              # Écarts d'allocation
python tests/test_diversification_score.py      # Score diversification v1.1
python tests/test_resilience_complete.py        # Score résilience complet
python tests/test_resilience_all_labels.py      # Labels de résilience
python tests/test_resilience_generator.py       # Injection HTML résilience
python tests/test_risk_config.py                # Configuration des risques v2.0 🆕
```

**Couverture** : Tous les composants critiques sont testés (normalizer, analyzer, generator, web research, scores, benchmarks, configuration des risques).

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

**Version** : 2.0.0
**Dernière mise à jour** : Novembre 2025

## 📝 Changelog

### v2.0.0 (Novembre 2025) 🆕
- ✨ **Système de détection des risques dynamique** : Architecture hybride à 3 niveaux
  - Niveau 1 : Risques structurels (7 catégories, toujours actifs)
  - Niveau 2 : Risques contextuels (6 recherches web configurables, optionnel)
  - Niveau 3 : Analyse LLM (réservé pour évolution future)
- ✨ **Configuration risks.yaml** : Externalisation complète des règles de détection
  - 13 risques structurels configurables
  - 6 recherches contextuelles (actualité économique, bancaire, fiscale, géopolitique, marchés, crypto)
  - Activation/désactivation par catégorie
- ✨ **Détection automatique** : Génération de risques si ≥2 sources web confirment
- ✨ **Test de validation** : `tests/test_risk_config.py` pour vérifier la configuration
- 📈 **Impact performance** : +10-20s si détection contextuelle activée
- 🎨 **Design épuré v3.0** : Refonte complète de l'affichage des sections de scores
  - Remplacement des sections `<details>` collapsibles par des blocs statiques
  - Labels de badges simplifiés (1-2 mots au lieu de phrases complètes)
  - Notes formatées en listes (`<ul>`) avec libellés standardisés
  - Amélioration de la lisibilité pour l'impression

### v1.1.0 (Novembre 2025)
- ✨ **Optimisation de portefeuille Markowitz** : Frontière efficiente, ratio de Sharpe, graphique PNG
- ✨ **4 profils d'investisseur** : default, dynamique, équilibré, prudent
- ✨ **Benchmark gap** : Comparaison allocation vs cibles avec badges colorés
- ✨ **Scores enrichis v2.0** : Labels qualitatifs et détails complets
  - Diversification v1.1 (composantes + 3 bonus)
  - Liquidité v2.0 (ratio adapté au profil)
  - Fiscalité v2.0 (enveloppes + bonus/pénalités)
  - Croissance v2.0 (contexte profil + fourchette optimale)
- ✨ **Configuration analysis.yaml** : 827 lignes, tous paramètres externalisés
- ✨ **Suite de tests complète** : 12 fichiers de tests unitaires

### v1.0.0 (Octobre 2025)
- 🎉 Version initiale : Pipeline 3 stages, 7 catégories de risques, recherches web, stress tests
