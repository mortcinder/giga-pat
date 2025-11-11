# TID : Implémentation Architecture Multi-Agents - Risques Contextuels

**Version** : 1.0.0
**Date** : 2025-11-11
**Type** : Technical Implementation Document
**Priorité** : Medium (Démonstrateur technologique)
**Complexité estimée** : Faible (~50-70 lignes de code)

---

## Table des matières

1. [Contexte et objectif](#1-contexte-et-objectif)
2. [État actuel vs État cible](#2-état-actuel-vs-état-cible)
3. [Architecture technique](#3-architecture-technique)
4. [Spécifications d'implémentation](#4-spécifications-dimplémentation)
5. [Critères d'acceptation](#5-critères-dacceptation)
6. [Plan de tests](#6-plan-de-tests)
7. [Rollback et désactivation](#7-rollback-et-désactivation)
8. [Documentation](#8-documentation)

---

## 1. Contexte et objectif

### 1.1 Problématique

Le générateur de rapports patrimoniaux exécute actuellement **toutes les analyses de manière séquentielle** :

```

[Normalisation] → [Risques structurels] → [Risques contextuels] → [Scores] → [Rapport]

     ~8s                  ~20s                   ~15s               ~5s        ~2s



Total : ~50s

```

Les **risques contextuels** (veille économique/réglementaire via web) sont **totalement indépendants** des risques structurels (analyse du patrimoine). Ils peuvent être exécutés en parallèle.

### 1.2 Objectif principal

**Démontrer la valeur de l'architecture multi-agents de Claude Code** en déléguant l'analyse des risques contextuels à un sous-agent autonome qui s'exécute en parallèle.

### 1.3 Bénéfices attendus

✅ **Performance** : Réduction de 15-25% du temps total (~40s au lieu de ~50s)
✅ **Pédagogie** : Vitrine technologique de l'orchestration multi-agents
✅ **Architecture** : Séparation claire des responsabilités
✅ **Scalabilité** : Base pour ajouter d'autres agents (stress tests, optimisation, etc.)

---

## 2. État actuel vs État cible

### 2.1 État actuel (séquentiel)

**Fichier** : `tools/analyzer.py`, méthode `analyze()` (lignes 92-150)

```python

def analyze(self, input_data: dict) -> dict:
    """Point d'entrée principal d'analyse"""

    # 1. Répartition
    analysis["repartition"] = self._analyze_repartition(input_data)

    # 2. Risques (structurels + contextuels en séquence)
    analysis["risques"] = self.risk_analyzer.analyze(input_data)
    #   └─→ _analyze_concentration_risks()      ~3s + 2 web calls
    #   └─→ _analyze_regulatory_risks()         ~2s + 2 web calls
    #   └─→ _analyze_fiscal_risks()             ~2s + 2 web calls
    #   └─→ _analyze_market_risks()             ~2s + 2 web calls
    #   └─→ _analyze_liquidity_risks()          ~2s
    #   └─→ _analyze_political_risks()          ~2s + 2 web calls
    #   └─→ _analyze_currency_risks()           ~2s + 2 web calls
    #   └─→ _detect_contextual_risks()          ~15s (6 recherches web) ⚠️ CIBLE

    # 3. Recommandations
    analysis["recommandations"] = self.recommender.generate(...)

    # 4-6. Stress tests, optimisation, synthèse
    ...

```

**Flux temporel** :

```

T=0s    : Début risques structurels
T=20s   : Fin risques structurels
T=20s   : Début risques contextuels  ← Attend fin structurels
T=35s   : Fin risques contextuels
T=35s   : Suite (recommandations...)

```

### 2.2 État cible (parallèle)

**Nouveau flux temporel** :

```

T=0s    : Début risques structurels
T=0s    : Lancement agent contextuel (parallèle) ← Démarrage simultané
T=20s   : Fin risques structurels
T=20s   : Attente agent contextuel (si pas terminé)
T=22s   : Agent contextuel terminé
T=22s   : Fusion résultats + suite

Gain : 35s → 22s = -13s (37% plus rapide sur cette partie)

```

**Architecture cible** :

```

┌─────────────────────────────────────────────────────┐
│  PatrimoineAnalyzer.analyze()  (Agent principal)    │
│                                                     │
│  1. Répartition                                     │
│  2. LANCER agent contextuel ────────────┐           │
│  3. Risques structurels (7 catégories)  │           │
│  4. ATTENDRE agent contextuel ──────────┘           │
│  5. Fusion résultats                                │
│  6. Recommandations, stress tests, etc.             │
└─────────────────────────────────────────────────────┘
                    │
                    │ Task()
                    ▼
┌─────────────────────────────────────────────────────┐
│  ContextualRiskAgent  (Sous-agent autonome)         │
│                                                     │
│  • Charge config/risks.yaml                         │
│  • Exécute 6 recherches contextuelles               │
│  • Génère risques avec sources web                  │
│  • Retourne JSON des risques détectés               │
└─────────────────────────────────────────────────────┘

```

---

## 3. Architecture technique

### 3.1 Composants à créer

#### 3.1.1 Nouveau module : `tools/utils/contextual_risk_agent.py`

**Responsabilité** : Encapsuler la logique d'analyse contextuelle pour exécution par un agent autonome.

**Interface publique** :

```python

class ContextualRiskAgent:
    """
    Agent autonome pour la détection de risques contextuels
    via recherche web (actualité économique, réglementaire, fiscale).

    Conçu pour s'exécuter en parallèle de l'analyse structurelle.
    """

    def __init__(self, config: dict):
        """
        Args:
            config: Configuration complète (config.yaml)
        """

    def analyze(self, patrimoine_data: dict) -> dict:
        """
        Point d'entrée principal - Analyse les risques contextuels.

        Args:
            patrimoine_data: Données normalisées du patrimoine (JSON)

        Returns:
            {
                "risks": [
                    {
                        "id": "RISK_001",
                        "titre": "Évolution réglementaire économique France",
                        "description": "...",
                        "niveau": "Moyen",
                        "categorie": "Réglementaire - Contexte",
                        "sources_web": [...]
                    },
                    ...
                ],
                "meta": {
                    "searches_executed": 6,
                    "duration_seconds": 14.2,
                    "risks_detected": 2
                }
            }
        """
```

**Implémentation** : Extraire la logique de `risk_analyzer.py:_detect_contextual_risks()` (lignes 637-691).

#### 3.1.2 Modifications dans `tools/analyzer.py`

**Changements dans la méthode `analyze()`** (lignes 92-150) :

```python

# AVANT (séquentiel)
analysis["risques"] = self.risk_analyzer.analyze(input_data)

# APRÈS (parallèle)
from tools.utils.contextual_risk_agent import ContextualRiskAgent

# Étape 2A : Lancer l'agent contextuel (non-bloquant)
contextual_agent_result = None

if self.risk_settings.get("enable_contextual_detection", False):
    self.logger.info("Lancement agent contextuel (parallèle)...")
    contextual_agent_result = self._launch_contextual_agent(input_data)
else:
    self.logger.info("Détection contextuelle désactivée")

# Étape 2B : Risques structurels (pendant que l'agent travaille)
self.logger.info("Analyse risques structurels...")
structural_risks = self.risk_analyzer.analyze_structural_only(input_data)

# Étape 2C : Attendre et fusionner résultats
if contextual_agent_result:
    self.logger.info("Attente agent contextuel...")
    contextual_data = self._await_contextual_agent(contextual_agent_result)
    analysis["risques"] = self._merge_risks(structural_risks, contextual_data)
else:
    analysis["risques"] = structural_risks
```

#### 3.1.3 Modifications dans `tools/utils/risk_analyzer.py`

**Nouvelle méthode** : `analyze_structural_only()` (extraire lignes 98-124)

```python

def analyze_structural_only(self, data: dict) -> Dict[str, List[Dict]]:
    """
    Analyse UNIQUEMENT les risques structurels (patrimoine actuel).
    Les risques contextuels sont gérés par l'agent dédié.

    Returns:
        Dictionnaire des risques par niveau (critiques, eleves, moyens, faibles)
    """
    all_risks = []

    # 1-7. Risques structurels uniquement
    all_risks.extend(self._analyze_concentration_risks(data))
    all_risks.extend(self._analyze_regulatory_risks(data))
    all_risks.extend(self._analyze_fiscal_risks(data))
    all_risks.extend(self._analyze_market_risks(data))
    all_risks.extend(self._analyze_liquidity_risks(data))
    all_risks.extend(self._analyze_political_risks(data))
    all_risks.extend(self._analyze_currency_risks(data))

    # Catégorisation
    return self._categorize_risks(all_risks)
```

**Refactoring** : La méthode `analyze()` existante devient obsolète ou appelle `analyze_structural_only()`.

### 3.2 Orchestration multi-agents

**Méthode à ajouter dans `tools/analyzer.py`** :

```python

def _launch_contextual_agent(self, patrimoine_data: dict):
    """
    Lance l'agent contextuel en parallèle via Claude Code Task API.

    Returns:
        Future/Task handle pour récupération ultérieure des résultats
    """
    from antml.tools import Task
    import json

    # Préparer le prompt pour l'agent
    agent_prompt = f"""

Tu es un agent spécialisé dans la détection de risques contextuels pour les portefeuilles patrimoniaux français.

TÂCHE :
Analyse les risques contextuels (actualité économique, réglementaire, fiscale) en utilisant le module ContextualRiskAgent.

DONNÉES PATRIMOINE :
{json.dumps(patrimoine_data, ensure_ascii=False, indent=2)}

INSTRUCTIONS :
1. Importe le module : from tools.utils.contextual_risk_agent import ContextualRiskAgent
2. Charge la configuration depuis config/config.yaml
3. Exécute agent.analyze(patrimoine_data)
4. Retourne le résultat JSON complet

IMPORTANT :
- Utilise UNIQUEMENT le module ContextualRiskAgent
- Ne modifie AUCUN fichier
- Retourne UNIQUEMENT du JSON valide
- Respecte le rate limiting des recherches web (1.1-1.5s entre requêtes)

FORMAT DE SORTIE ATTENDU :{{
    "risks": [...],
    "meta": {{...}}
}}
"""
    # Lancer l'agent

    task = Task(
        subagent_type="general-purpose",
        prompt=agent_prompt,
        description="Détection risques contextuels"
    )

    return task

def _await_contextual_agent(self, task) -> dict:
    """
    Attend la fin de l'agent contextuel et récupère les résultats.

    Args:
        task: Task handle retourné par _launch_contextual_agent()

    Returns:
        Résultats de l'agent : {"risks": [...], "meta": {...}}
    """
    import json

    # Attendre la fin de l'agent
    result = task.result()  # Bloquant

    # Parser le résultat JSON
    try:
        contextual_data = json.loads(result)
        self.logger.info(f"✓ Agent contextuel terminé : "
                        f"{len(contextual_data['risks'])} risques détectés "
                        f"en {contextual_data['meta']['duration_seconds']:.1f}s")
        return contextual_data
    except Exception as e:
        self.logger.error(f"Erreur parsing résultat agent contextuel : {e}")
        return {"risks": [], "meta": {}}

def _merge_risks(self, structural_risks: dict, contextual_data: dict) -> dict:
    """
    Fusionne les risques structurels et contextuels.

    Args:
        structural_risks: {"critiques": [...], "eleves": [...], ...}
        contextual_data: {"risks": [...], "meta": {...}}

    Returns:
        Dictionnaire fusionné avec tous les risques catégorisés
    """
    # Catégoriser les risques contextuels
    for risk in contextual_data.get("risks", []):
        niveau = risk["niveau"]
        if niveau == "Critique":
            structural_risks["critiques"].append(risk)
        elif niveau == "Élevé":
            structural_risks["eleves"].append(risk)
        elif niveau == "Moyen":
            structural_risks["moyens"].append(risk)
        else:
            structural_risks["faibles"].append(risk)

    return structural_risks
```

---

## 4. Spécifications d'implémentation

### 4.1 Fichier 1 : `tools/utils/contextual_risk_agent.py` (NOUVEAU)

**Lignes de code estimées** : ~150 lignes

**Structure** :

```python

"""
Agent autonome de détection de risques contextuels
Conçu pour exécution parallèle via Claude Code Task API
"""

import logging
import yaml
import os
from typing import Dict, List, Any
from datetime import datetime
from tools.utils.web_research import WebResearcher


class ContextualRiskAgent:
    """
    Agent spécialisé dans la détection de risques contextuels via web research.

    Responsabilités :
    - Charger les recherches contextuelles depuis config/risks.yaml
    - Exécuter les recherches web (Brave API)
    - Générer les risques détectés avec sources
    - Retourner résultats structurés en JSON
    """

    def __init__(self, config: dict):
        """
        Initialise l'agent contextuel.

        Args:
            config: Configuration complète (chargée depuis config/config.yaml)
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Charger risks.yaml
        self.risk_definitions = self._load_risk_definitions()
        self.contextual_searches = self.risk_definitions.get("contextual_searches", {})
        self.risk_settings = self.risk_definitions.get("risk_settings", {})

        # Initialiser web researcher
        self.web_researcher = WebResearcher(config)

        # Compteur pour IDs uniques
        self.risk_id_counter = 1000  # Commence à 1000 pour éviter conflits
        self.logger.info("ContextualRiskAgent initialisé")

    def analyze(self, patrimoine_data: dict) -> dict:
        """
        Point d'entrée principal - Détecte les risques contextuels.

        Args:
            patrimoine_data: Données normalisées du patrimoine

        Returns:
            {
                "risks": [...],
                "meta": {
                    "searches_executed": 6,
                    "duration_seconds": 14.2,
                    "risks_detected": 2,
                    "timestamp": "2025-11-11T14:23:10"
                }
            }
        """
        start_time = datetime.now()
        self.logger.info("Début analyse risques contextuels...")

        risks = []
        searches_executed = 0

        # Parcourir les recherches contextuelles configurées
        for search_id, search_config in self.contextual_searches.items():
            if not search_config.get("enabled", False):
                continue

            self.logger.info(f"  → Recherche : {search_id}")

            # Exécuter recherche web
            queries = search_config.get("queries", [])
            context = search_config.get("analysis_context", "")

            search_results = self.web_researcher.search(
                sujet=f"Contexte: {search_id}",
                queries=queries,
                context=context
            )

            searches_executed += 1

            # Analyser résultats et générer risques
            detected_risks = self._analyze_search_results(
                search_id=search_id,
                search_config=search_config,
                search_results=search_results,
                patrimoine_data=patrimoine_data
            )

            risks.extend(detected_risks)
            self.logger.info(f"    ✓ {len(detected_risks)} risques détectés")

        duration = (datetime.now() - start_time).total_seconds()

        self.logger.info(f"✓ Analyse contextuelle terminée : "
                        f"{len(risks)} risques en {duration:.1f}s")

        return {
            "risks": risks,
            "meta": {
                "searches_executed": searches_executed,
                "duration_seconds": duration,
                "risks_detected": len(risks),
                "timestamp": datetime.now().isoformat()
            }
        }

    def _load_risk_definitions(self) -> dict:
        """Charge config/risks.yaml"""

        # [COPIER depuis risk_analyzer.py:56-78]
        ...

    def _analyze_search_results(
        self,
        search_id: str,
        search_config: dict,
        search_results: List[Dict],
        patrimoine_data: dict
    ) -> List[Dict[str, Any]]:
        """
        Génère des risques depuis les résultats de recherche.

        Args:
            search_id: ID de la recherche (ex: "actualite_economique_france")
            search_config: Configuration de la recherche
            search_results: Résultats web
            patrimoine_data: Données patrimoine pour calcul exposition

        Returns:
            Liste de risques détectés
        """

        # [COPIER depuis risk_analyzer.py:693-738]
        # + appel à _get_contextual_risk_mapping()
        ...

    def _get_contextual_risk_mapping(
        self,
        search_id: str,
        patrimoine_data: dict
    ) -> Optional[Dict[str, Any]]:
        """
        Mappe search_id vers propriétés du risque.

        Returns:
            Dictionnaire avec titre, description, niveau, etc.
            ou None si non pertinent
        """

        # [COPIER depuis risk_analyzer.py:740-844]
        ...

    def _calculate_equity_exposure(self, data: dict) -> float:
        """Calcule exposition actions"""

        # [COPIER depuis risk_analyzer.py:846-856]
        ...

    def _get_risk_id(self) -> str:
        """Génère ID unique pour risque"""

        risk_id = f"RISK_{self.risk_id_counter:04d}"
        self.risk_id_counter += 1

        return risk_id
```

**Sources à copier** :
- `risk_analyzer.py:56-78` → `_load_risk_definitions()`
- `risk_analyzer.py:693-738` → `_analyze_search_results()`
- `risk_analyzer.py:740-844` → `_get_contextual_risk_mapping()`
- `risk_analyzer.py:846-856` → `_calculate_equity_exposure()`

### 4.2 Fichier 2 : `tools/analyzer.py` (MODIFICATIONS)

**Lignes modifiées** : ~30 lignes

**Lignes ajoutées** : ~80 lignes

#### Modification 1 : Import (ligne ~18)

```python

# AJOUTER après les imports existants

from tools.utils.contextual_risk_agent import ContextualRiskAgent
import json
```

#### Modification 2 : Méthode `analyze()` (lignes 92-150)

**REMPLACER** la section risques (lignes ~119-124) :

```python

# AVANT
analysis["risques"] = self.risk_analyzer.analyze(input_data)

# APRÈS
# 2A. Lancer agent contextuel (parallèle)
contextual_agent_task = None
if self.risk_settings.get("enable_contextual_detection", False):
    self.logger.info("Lancement agent contextuel (parallèle)...")
    contextual_agent_task = self._launch_contextual_agent(input_data)

# 2B. Risques structurels
self.logger.info("Analyse risques structurels...")
structural_risks = self.risk_analyzer.analyze_structural_only(input_data)

# 2C. Fusionner résultats
if contextual_agent_task:
    contextual_data = self._await_contextual_agent(contextual_agent_task)
    analysis["risques"] = self._merge_risks(structural_risks, contextual_data)
else:
    analysis["risques"] = structural_risks
```

#### Modification 3 : Nouvelles méthodes (après ligne ~150)

**AJOUTER** les 3 méthodes d'orchestration :

- `_launch_contextual_agent()` (voir section 3.2)
- `_await_contextual_agent()` (voir section 3.2)
- `_merge_risks()` (voir section 3.2)

### 4.3 Fichier 3 : `tools/utils/risk_analyzer.py` (MODIFICATIONS)

**Lignes ajoutées** : ~25 lignes

#### Modification 1 : Nouvelle méthode `analyze_structural_only()` (après ligne 147)

```python

def analyze_structural_only(self, data: dict) -> Dict[str, List[Dict]]:
    """
    Analyse UNIQUEMENT les risques structurels (patrimoine actuel).
    Les risques contextuels sont délégués à l'agent dédié.

    Args:
        data: Données du patrimoine normalisées

    Returns:
        Dictionnaire des risques catégorisés par niveau
    """

    self.logger.info("Analyse des risques structurels...")

    all_risks = []

    # 1-7. Risques structurels uniquement
    self.logger.info("  → Risques de concentration")
    all_risks.extend(self._analyze_concentration_risks(data))

    self.logger.info("  → Risques réglementaires")
    all_risks.extend(self._analyze_regulatory_risks(data))

    self.logger.info("  → Risques fiscaux")
    all_risks.extend(self._analyze_fiscal_risks(data))

    self.logger.info("  → Risques de marché")
    all_risks.extend(self._analyze_market_risks(data))

    self.logger.info("  → Risques de liquidité")
    all_risks.extend(self._analyze_liquidity_risks(data))

    self.logger.info("  → Risques politiques")
    all_risks.extend(self._analyze_political_risks(data))

    self.logger.info("  → Risques de changes")
    all_risks.extend(self._analyze_currency_risks(data))

    # Catégorisation
    risques = {
        "critiques": [r for r in all_risks if r["niveau"] == "Critique"],
        "eleves": [r for r in all_risks if r["niveau"] == "Élevé"],
        "moyens": [r for r in all_risks if r["niveau"] == "Moyen"],
        "faibles": [r for r in all_risks if r["niveau"] == "Faible"]
    }

    self.logger.info(f"✓ {len(all_risks)} risques structurels identifiés")

    return risques
```

#### Modification 2 : Mise à jour méthode `analyze()` (lignes 80-147)

**OPTION A** : Rendre obsolète avec dépréciation

```python

def analyze(self, data: dict) -> Dict[str, List[Dict]]:
    """
    [DEPRECATED] Utiliser analyze_structural_only() à la place.
    L'analyse contextuelle est maintenant gérée par ContextualRiskAgent.
    """
    import warnings
    warnings.warn("analyze() est obsolète, utiliser analyze_structural_only()",
                  DeprecationWarning)

    return self.analyze_structural_only(data)

```

**OPTION B** : Garder pour compatibilité descendante

```python

def analyze(self, data: dict) -> Dict[str, List[Dict]]:
    """
    Analyse complète (structurel + contextuel) - MODE LEGACY.
    Note: En mode multi-agents, utiliser analyze_structural_only().
    """

    # Risques structurels
    all_risks = []
    all_risks.extend(self._analyze_concentration_risks(data))

    # ... (code existant lignes 98-124)

    # Risques contextuels (si activé)
    if self.risk_settings.get("enable_contextual_detection", False):
        contextual_risks = self._detect_contextual_risks(data)
        all_risks.extend(contextual_risks)

    # Catégorisation
    return self._categorize_risks(all_risks)
```

**RECOMMANDATION** : Choisir OPTION B pour ne pas casser les tests existants.

### 4.4 Fichier 4 : `CLAUDE.md` (DOCUMENTATION)

**Lignes ajoutées** : ~60 lignes

**AJOUTER** nouvelle section après "Common Development Scenarios" :

```markdown
## Architecture Multi-Agents (Démonstrateur Technologique)

Depuis novembre 2025, le projet utilise l'architecture multi-agents de Claude Code
pour optimiser la génération des rapports patrimoniaux.

### Agent principal (orchestrateur)

**Responsabilités** :

- Normalisation des données sources (Stage 1)
- Analyse des risques structurels (patrimoine actuel)
- Génération des recommandations, stress tests, optimisation
- Génération du rapport HTML (Stage 3)

**Fichier** : `tools/analyzer.py`

### Agent secondaire (veille contextuelle)

**Responsabilités** :

- Surveillance de l'actualité économique française
- Détection des risques émergents (réglementaire, fiscal, marché)
- Exécution parallèle pendant l'analyse structurelle

**Fichier** : `tools/utils/contextual_risk_agent.py`

### Flux d'exécution parallèle
```

T=0s PatrimoineAnalyzer.analyze()
        │
        ├──→ [Agent contextuel] → Recherches web (15s)
        │                            ↓
        └──→ Risques structurels (20s)
                ↓
        Attente agent contextuel (si pas fini)
                ↓
        Fusion résultats
                ↓
        Suite (recommandations, stress tests...)
````

### Gains de performance

| Métrique | Séquentiel (legacy) | Parallèle (multi-agents) | Gain |
|----------|---------------------|--------------------------|------|
| **Risques structurels** | 20s | 20s | 0% |
| **Risques contextuels** | 15s | 15s (parallèle) | -13s |
| **Total Stage 2** | 35s | 22s | **37%** |
| **Total complet** | 50s | 37s | **26%** |

### Activation/désactivation

#### Désactiver l'analyse contextuelle

Dans `config/risks.yaml` :

```yaml

risk_settings:
  enable_contextual_detection: false  # Désactive complètement

````

#### Désactiver le mode multi-agents

Dans `tools/analyzer.py:analyze()`, remplacer par l'ancien code :

```python

# Mode séquentiel (legacy)
analysis["risques"] = self.risk_analyzer.analyze(input_data)

```

### Débogage

Logs typiques en mode multi-agents :

```

[2025-11-11 14:23:10] INFO: Analyse approfondie...
[2025-11-11 14:23:10] INFO: Lancement agent contextuel (parallèle)...
[2025-11-11 14:23:11] INFO: Analyse risques structurels...
[2025-11-11 14:23:11] INFO:   → Risques de concentration
[2025-11-11 14:23:15] INFO:   → Risques réglementaires
...
[2025-11-11 14:23:30] INFO: ✓ 12 risques structurels identifiés
[2025-11-11 14:23:30] INFO: Attente agent contextuel...
[2025-11-11 14:23:33] INFO: ✓ Agent contextuel terminé : 2 risques détectés en 22.4s
[2025-11-11 14:23:33] INFO: ✓ 14 risques totaux identifiés
```

### Ajout de nouveaux agents

Pour ajouter d'autres agents (stress tests, optimisation, etc.), suivre le pattern :

1. Créer module agent : `tools/utils/{nom}_agent.py`
2. Exposer méthode `analyze()` retournant JSON
3. Lancer en parallèle dans `analyzer.py` via `Task()`
4. Fusionner résultats

Exemple :

```python

# Lancer 3 agents en parallèle
contextual_task = self._launch_contextual_agent(data)
stress_task = self._launch_stress_test_agent(data)
optim_task = self._launch_optimization_agent(data)

# Attendre tous les résultats
contextual_data = self._await_agent(contextual_task)
stress_data = self._await_agent(stress_task)
optim_data = self._await_agent(optim_task)
```

````

---

## 5. Critères d'acceptation

### 5.1 Fonctionnalité

✅ **CA-1** : L'agent contextuel s'exécute en parallèle des risques structurels
✅ **CA-2** : Le rapport final contient les risques contextuels avec sources web
✅ **CA-3** : Les résultats sont identiques au mode séquentiel (même risques détectés)
✅ **CA-4** : Le temps d'exécution total est réduit de 15-25%
✅ **CA-5** : Le mode peut être désactivé via `config/risks.yaml`

### 5.2 Qualité du code

✅ **CA-6** : Aucune régression sur les tests existants
✅ **CA-7** : Logging clair indiquant le lancement et la fin de l'agent
✅ **CA-8** : Gestion des erreurs si l'agent échoue (fallback séquentiel)
✅ **CA-9** : Code documenté (docstrings sur toutes les méthodes publiques)
✅ **CA-10** : Respect des conventions du projet (PEP8, nommage, structure)

### 5.3 Documentation

✅ **CA-11** : Section ajoutée dans `CLAUDE.md` expliquant l'architecture multi-agents
✅ **CA-12** : Logs de débogage documentés
✅ **CA-13** : Instructions de désactivation claires

---

## 6. Plan de tests

### 6.1 Tests unitaires (optionnel)

**Nouveau fichier** : `tests/test_contextual_agent.py`

```python

"""Tests pour l'agent contextuel"""

import unittest
from tools.utils.contextual_risk_agent import ContextualRiskAgent


class TestContextualRiskAgent(unittest.TestCase):

    def setUp(self):
        """Charge configuration test"""

        self.config = {...}  # Config minimale
        self.agent = ContextualRiskAgent(self.config)

    def test_analyze_returns_valid_structure(self):
        """Vérifie structure JSON retournée"""

        patrimoine_data = {...}
        result = self.agent.analyze(patrimoine_data)

        self.assertIn("risks", result)
        self.assertIn("meta", result)
        self.assertIsInstance(result["risks"], list)

    def test_no_risks_if_no_searches(self):
        """Si aucune recherche activée, retourne liste vide"""

        # Désactiver toutes les recherches dans config
        result = self.agent.analyze({...})
        self.assertEqual(len(result["risks"]), 0)
````

### 6.2 Tests d'intégration

**Test 1 : Exécution complète avec agent**

```bash

# Activer détection contextuelle
# config/risks.yaml : enable_contextual_detection: true

python main.py

# Vérifier :
# - Logs montrent "Lancement agent contextuel"
# - Logs montrent "✓ Agent contextuel terminé"
# - Rapport HTML contient risques avec catégorie "- Contexte"
# - Temps total < 45s
```

**Test 2 : Exécution sans agent (désactivé)**

```bash

# Désactiver détection contextuelle
# config/risks.yaml : enable_contextual_detection: false

python main.py

# Vérifier :
# - Logs montrent "Détection contextuelle désactivée"
# - Aucun risque avec catégorie "- Contexte"
# - Temps total ~35s (plus rapide, pas de web recherches)
```

**Test 3 : Comparaison résultats (mode legacy vs multi-agents)**

```bash

# Mode 1 : Legacy (séquentiel)
git checkout main  # Version avant multi-agents
python main.py
mv generated/rapport_*.html generated/rapport_legacy.html

# Mode 2 : Multi-agents (parallèle)
git checkout feature/multi-agents
python main.py
mv generated/rapport_*.html generated/rapport_multiagents.html

# Comparer manuellement les 2 rapports :
# - Nombre de risques identique
# - Contenu identique (sauf ordre possible)
# - Temps multi-agents < temps legacy
```

### 6.3 Tests de robustesse

**Test 4 : Agent contextuel échoue**

```python

# Simuler erreur dans l'agent (ex: API Brave inaccessible)
# Vérifier que le rapport est quand même généré avec risques structurels
```

**Test 5 : Timeout agent**

```python

# Simuler agent très lent (>60s)
# Vérifier que le système attend ou timeout proprement
```

---

## 7. Rollback et désactivation

### 7.1 Désactivation temporaire

**Option 1** : Via configuration (sans modification code)

```yaml
# config/risks.yaml

risk_settings:
  enable_contextual_detection: false
```

**Option 2** : Commentaire code

```python

# tools/analyzer.py, méthode analyze()
# DÉSACTIVER multi-agents (rollback temporaire)
# contextual_agent_task = self._launch_contextual_agent(input_data)
# structural_risks = self.risk_analyzer.analyze_structural_only(input_data)
# ...

# MODE LEGACY (séquentiel)
analysis["risques"] = self.risk_analyzer.analyze(input_data)
```

### 7.2 Rollback complet (git)

```bash

# Si problème critique, revenir à la version avant multi-agents
git revert <commit-hash-multi-agents>

# OU
git checkout main
git branch -D feature/multi-agents
```

### 7.3 Gestion d'erreurs

**Dans `analyzer.py:_await_contextual_agent()`**, ajouter :

```python

def _await_contextual_agent(self, task) -> dict:
    """Attend résultats avec gestion d'erreur"""

    try:
        result = task.result(timeout=60)  # Timeout 60s
        return json.loads(result)
    except TimeoutError:
        self.logger.error("Agent contextuel timeout (>60s), skip")
        return {"risks": [], "meta": {}}
    except Exception as e:
        self.logger.error(f"Agent contextuel erreur : {e}")
        return {"risks": [], "meta": {}}
```

---

## 8. Documentation

### 8.1 Fichiers à modifier

1. ✅ `CLAUDE.md` : Ajouter section "Architecture Multi-Agents"
2. ✅ `README.md` : Mentionner optimisation multi-agents dans features
3. ✅ `tools/utils/contextual_risk_agent.py` : Docstrings complètes
4. ✅ `tools/analyzer.py` : Commenter nouvelles méthodes

### 8.2 Exemples de docstrings

```python

class ContextualRiskAgent:
    """
    Agent autonome de détection de risques contextuels.

    Cet agent est conçu pour s'exécuter en parallèle de l'analyse
    structurelle du patrimoine, via l'architecture multi-agents de Claude Code.

    Il surveille l'actualité économique, réglementaire et fiscale française
    pour détecter des risques émergents, en utilisant les recherches web
    configurées dans config/risks.yaml.

    Usage:
        >>> from tools.utils.contextual_risk_agent import ContextualRiskAgent
        >>> agent = ContextualRiskAgent(config)
        >>> result = agent.analyze(patrimoine_data)
        >>> print(result["risks"])  # Liste des risques détectés

    Attributes:
        config (dict): Configuration complète du projet
        web_researcher (WebResearcher): Instance pour recherches Brave API
        contextual_searches (dict): Recherches configurées dans risks.yaml

    See Also:
        - tools/utils/risk_analyzer.py : Analyse risques structurels
        - config/risks.yaml : Configuration des recherches contextuelles
        - CLAUDE.md : Documentation architecture multi-agents
    """
```

### 8.3 Commentaires inline

```python

# Dans analyzer.py:analyze()

# ========================================================================
# ARCHITECTURE MULTI-AGENTS (Nov 2025)
# ========================================================================

# L'analyse des risques est divisée en 2 agents parallèles :
#

# Agent 1 (principal) : Risques structurels
#   - Concentration, réglementaire, fiscal, marché, liquidité, politique, change
#   - Basé sur les données du patrimoine actuel
#   - Durée : ~20s
#

# Agent 2 (contextuel) : Risques émergents
#   - Actualité économique, réglementaire, fiscale française
#   - Basé sur recherches web (Brave API)
#   - Durée : ~15s (parallèle)
#

# Gain : 35s → 22s (37% plus rapide)
# ========================================================================

self.logger.info("Lancement agent contextuel (parallèle)...")
contextual_agent_task = self._launch_contextual_agent(input_data)
```

---

## Annexes

### Annexe A : Fichiers concernés

| Fichier | Type | Lignes modifiées | Description |
|---------|------|------------------|-------------|
| `tools/utils/contextual_risk_agent.py` | **NOUVEAU** | ~150 | Module agent contextuel |
| `tools/analyzer.py` | MODIFIÉ | +80, ~30 | Orchestration multi-agents |
| `tools/utils/risk_analyzer.py` | MODIFIÉ | +25 | Méthode `analyze_structural_only()` |
| `CLAUDE.md` | MODIFIÉ | +60 | Documentation architecture |
| `README.md` | MODIFIÉ | +5 | Mention optimisation |
| `tests/test_contextual_agent.py` | NOUVEAU | ~50 | Tests unitaires (optionnel) |

**Total estimé** : ~370 lignes ajoutées/modifiées

### Annexe B : Checklist d'implémentation

Utiliser cette checklist pour valider chaque étape :

- [ ] **Étape 1** : Créer `tools/utils/contextual_risk_agent.py`
  - [ ] Copier logique depuis `risk_analyzer.py`
  - [ ] Implémenter méthode `analyze()`
  - [ ] Ajouter docstrings complètes
  - [ ] Tester import : `from tools.utils.contextual_risk_agent import ContextualRiskAgent`

- [ ] **Étape 2** : Modifier `tools/utils/risk_analyzer.py`
  - [ ] Ajouter méthode `analyze_structural_only()`
  - [ ] Mettre à jour méthode `analyze()` (compatibilité legacy)
  - [ ] Tester : `python -c "from tools.utils.risk_analyzer import RiskAnalyzer"`

- [ ] **Étape 3** : Modifier `tools/analyzer.py`
  - [ ] Ajouter import `ContextualRiskAgent`
  - [ ] Implémenter `_launch_contextual_agent()`
  - [ ] Implémenter `_await_contextual_agent()`
  - [ ] Implémenter `_merge_risks()`
  - [ ] Modifier méthode `analyze()` pour orchestration parallèle
  - [ ] Ajouter gestion d'erreurs

- [ ] **Étape 4** : Tests d'intégration
  - [ ] Test avec détection contextuelle activée
  - [ ] Test avec détection contextuelle désactivée
  - [ ] Vérifier temps exécution (gain 15-25%)
  - [ ] Comparer résultats (risques identiques)

- [ ] **Étape 5** : Documentation
  - [ ] Mettre à jour `CLAUDE.md` (section multi-agents)
  - [ ] Mettre à jour `README.md` (mention gains)
  - [ ] Vérifier docstrings complètes
  - [ ] Commenter code complexe

- [ ] **Étape 6** : Validation finale
  - [ ] Tous les tests passent
  - [ ] Logs clairs et informatifs
  - [ ] Aucune régression détectée
  - [ ] Git commit avec message descriptif
  - [ ] Git push sur branche feature

### Annexe C : Dépendances

**Aucune nouvelle dépendance** requise. Le projet utilise :

- Modules standard : `json`, `logging`, `datetime`, `typing`
- Modules existants : `WebResearcher`, configuration YAML
- Claude Code SDK : `Task` (déjà disponible)

### Annexe D : Estimation temps

| Tâche | Temps estimé | Complexité |
|-------|--------------|------------|
| Créer `contextual_risk_agent.py` | 1h | Faible (copie/adaptation) |
| Modifier `risk_analyzer.py` | 30min | Faible |
| Modifier `analyzer.py` | 1h30 | Moyenne |
| Tests d'intégration | 1h | Moyenne |
| Documentation | 1h | Faible |
| **TOTAL** | **5h** | **Faible-Moyenne** |

---

**FIN DU DOCUMENT**

Pour toute question ou clarification sur cette implémentation, consulter :

- `CLAUDE.md` : Documentation projet complète
- `PRD.md` : Spécifications fonctionnelles
- `config/risks.yaml` : Configuration risques contextuels
