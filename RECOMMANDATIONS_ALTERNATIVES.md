# Recommandations Dynamiques - Approches Alternatives

## Problème identifié

Le système de validation web (v2.1.4) échoue pour plusieurs questions car :
1. **Pas de consensus chiffré** dans les sources CGP (ex: "montant minimum livret")
2. **Questions trop subjectives** (dépendent du contexte individuel)
3. **Extraction numérique impossible** (sources donnent des plages, pas des seuils)

## Solutions proposées

### 🎯 OPTION A : Recommandations basées sur RÈGLES MÉTIER (sans web)

**Principe** : Utiliser des règles internes bien documentées, sans validation web.

**Avantages** :
- ✅ Fiable (pas de dépendance API externe)
- ✅ Rapide (pas de latence réseau)
- ✅ Déterministe (même patrimoine = mêmes recommandations)

**Inconvénients** :
- ❌ Pas de mise à jour automatique avec l'actualité
- ❌ Nécessite maintenance manuelle des seuils

#### Exemples de règles métier

```yaml
# config/recommendations_rules.yaml

regles_comptes_inefficaces:
  livret_doublon:
    description: "Détecte livrets A en doublon avec montant faible"
    condition: "nb_livrets_a > 1 AND min(montants) < 1000"
    recommandation: "Consolider les livrets A sur un seul compte"
    criticite: 3
    impact: 3
    facilite: 10

  pea_inactif_faible:
    description: "PEA avec montant faible et frais annuels"
    condition: "montant < 2000 AND frais_annuels > 0"
    recommandation: "Clôturer le PEA ou l'alimenter au-delà de 5000€"
    criticite: 4
    impact: 5
    facilite: 8

  av_frais_excessifs:
    description: "AV avec frais de gestion > 1%"
    condition: "frais_gestion > 1.0"
    recommandation: "Transférer vers contrat avec frais < 0.8%"
    criticite: 6
    impact: 7
    facilite: 5

regles_diversification:
  concentration_custodian:
    description: "Plus de 50% du patrimoine chez un seul établissement"
    condition: "max(part_custodian) > 0.5"
    recommandation: "Diversifier sur au moins 2-3 établissements"
    criticite: 7
    impact: 8
    facilite: 6

  mono_juridiction:
    description: "100% du patrimoine dans une seule juridiction"
    condition: "nb_juridictions == 1 AND patrimoine_total > 100000"
    recommandation: "Diversifier géographiquement (5-10% à l'international)"
    criticite: 6
    impact: 7
    facilite: 4

regles_liquidites:
  fonds_urgence_insuffisant:
    description: "Moins de 3 mois de dépenses en liquidités"
    condition: "liquidites / depenses_mensuelles < 3"
    recommandation: "Constituer fonds d'urgence de 3-6 mois de dépenses"
    criticite: 8
    impact: 9
    facilite: 7

regles_fiscales:
  pea_sous_utilise:
    description: "PEA ouvert depuis < 5 ans avec faible montant"
    condition: "anciennete_pea < 5 AND montant < 10000"
    recommandation: "Alimenter le PEA pour atteindre 10-15k€ (avantage fiscal à 5 ans)"
    criticite: 5
    impact: 6
    facilite: 8
```

#### Implémentation

```python
# tools/utils/rule_based_recommendations.py

class RuleBasedRecommendationEngine:
    """
    Moteur de recommandations basé sur règles métier
    (alternative au système de validation web)
    """

    def __init__(self, rules_config: dict):
        self.rules = rules_config
        self.logger = logging.getLogger(__name__)

    def generate_recommendations(self, data: dict) -> List[Dict]:
        """Génère recommandations basées sur règles"""
        recommendations = []

        # 1. Comptes inefficaces
        recommendations.extend(self._check_inefficient_accounts(data))

        # 2. Diversification
        recommendations.extend(self._check_diversification(data))

        # 3. Liquidités
        recommendations.extend(self._check_liquidity(data))

        # 4. Fiscalité
        recommendations.extend(self._check_tax_optimization(data))

        return recommendations

    def _check_inefficient_accounts(self, data: dict) -> List[Dict]:
        """Détecte comptes à faible valeur ajoutée"""
        recommendations = []

        # Livrets A en doublon
        livrets_a = self._extract_livrets_a(data)
        if len(livrets_a) > 1:
            smallest = min(livrets_a, key=lambda x: x['montant'])
            if smallest['montant'] < 1000:
                recommendations.append({
                    "type": "compte_inefficace",
                    "titre": f"Consolider livret A {smallest['custodian']} ({smallest['montant']}€)",
                    "description": "Livret A en doublon avec montant trop faible",
                    "score_criticite": 3,
                    "score_impact": 3,
                    "score_facilite": 10
                })

        # PEA faible montant avec frais
        peas = self._extract_peas(data)
        for pea in peas:
            if pea['montant'] < 2000 and pea.get('frais_annuels', 0) > 0:
                recommendations.append({
                    "type": "compte_inefficace",
                    "titre": f"Clôturer ou alimenter PEA {pea['custodian']}",
                    "description": f"PEA de {pea['montant']}€ avec {pea['frais_annuels']}€ de frais annuels",
                    "score_criticite": 4,
                    "score_impact": 5,
                    "score_facilite": 8
                })

        return recommendations
```

---

### 🎯 OPTION B : Recommandations basées sur COMPARAISON (benchmarking)

**Principe** : Comparer le patrimoine de l'utilisateur aux **benchmarks du profil** déjà définis dans `config/analysis.yaml`.

**Exemple** :

```python
def generate_allocation_recommendations(data: dict, profile: str) -> List[Dict]:
    """Recommandations basées sur écarts aux benchmarks"""
    recommendations = []

    benchmarks = data['config']['benchmarks'][profile]
    allocation_actuelle = data['repartition']['par_classe']

    for classe, bench in benchmarks.items():
        pct_actuel = allocation_actuelle.get(classe, {}).get('pourcentage', 0)
        target = bench['target']
        min_bench = bench['min']
        max_bench = bench['max']

        # Sous-pondération forte
        if pct_actuel < min_bench - 5:
            recommendations.append({
                "titre": f"Augmenter allocation {classe}",
                "description": f"{pct_actuel:.1f}% (cible: {target}%, minimum: {min_bench}%)",
                "score_criticite": 7,
                "score_impact": 8,
                "score_facilite": 6
            })

        # Sur-pondération forte
        elif pct_actuel > max_bench + 5:
            recommendations.append({
                "titre": f"Réduire allocation {classe}",
                "description": f"{pct_actuel:.1f}% (cible: {target}%, maximum: {max_bench}%)",
                "score_criticite": 6,
                "score_impact": 7,
                "score_facilite": 5
            })

    return recommendations
```

---

### 🎯 OPTION C : Approche HYBRIDE (règles + web sélectif)

**Principe** :
- Utiliser **règles métier** pour 80% des recommandations (fiables)
- Utiliser **validation web** uniquement pour données volatiles (taux, rendements)

**Architecture** :

```yaml
recommendations_hybrid:
  # Règles métier (pas de web)
  rules_based:
    - comptes_inefficaces
    - diversification_custodian
    - fonds_urgence
    - allocation_vs_benchmark

  # Validation web (seulement si nécessaire)
  web_validated:
    - taux_livret_a_actuel       # ✅ Fonctionne
    - rendement_fonds_euro_moyen # ✅ Fonctionne
    - fonds_urgence_mois         # ✅ Fonctionne
```

**Implémentation** :

```python
def generate_recommendations_hybrid(data: dict) -> List[Dict]:
    """Approche hybride : règles + web sélectif"""
    recommendations = []

    # 1. Règles métier (80% - fiable)
    rule_engine = RuleBasedRecommendationEngine(rules_config)
    recommendations.extend(rule_engine.generate_recommendations(data))

    # 2. Validation web (20% - données volatiles uniquement)
    if web_research_enabled:
        # Seulement pour taux/rendements actuels
        web_data = validate_market_data()
        recommendations.extend(generate_market_based_recommendations(web_data))

    return recommendations
```

---

## 📊 Comparaison des approches

| Critère | Option A (Règles) | Option B (Benchmark) | Option C (Hybride) |
|---------|------------------|---------------------|-------------------|
| **Fiabilité** | 🟢 Très haute | 🟢 Haute | 🟢 Haute |
| **Maintenance** | 🟡 Manuelle | 🟢 Auto (via config) | 🟡 Mixte |
| **Actualité** | 🔴 Statique | 🔴 Statique | 🟢 Web pour taux |
| **Rapidité** | 🟢 Instant | 🟢 Instant | 🟡 ~10s (web) |
| **Complexité** | 🟢 Simple | 🟢 Très simple | 🟡 Moyenne |

---

## 💡 Recommandation finale

**Pour la v2.1.5, je propose l'OPTION C (Hybride)** :

### Phase 1 (Quick Win - 1h) ✅
1. Activer **3 validations web qui fonctionnent** :
   - `fonds_urgence_mois`
   - `taux_livret_a_actuel`
   - `rendement_fonds_euro_moyen`

2. Générer recommandations basées sur ces 3 données

### Phase 2 (Court terme - 2-3h) 🎯
1. Implémenter **règles métier** pour :
   - Comptes inefficaces (livrets doublons, PEA faibles)
   - Diversification custodian
   - Allocation vs benchmark

2. Combiner règles + web validé

### Phase 3 (Moyen terme - 1 jour) 🚀
1. Approche **qualitative/NLP** pour questions non-numériques
2. Extraction de bonnes pratiques textuelles (diversification, etc.)

---

## 🎯 Exemple de recommandation générée

**Avec Option C (Hybride)** :

```json
{
  "id": "REC_001",
  "type": "liquidites",
  "source": "rule_based",  // ← Règle métier
  "titre": "Augmenter fonds d'urgence",
  "description": "Fonds d'urgence actuel : 2.1 mois de dépenses. Recommandation CGP : 6 mois minimum.",
  "validation_web": {
    "consensus": "6 mois",
    "sources": 3,
    "confiance": "high"
  },
  "score_criticite": 8,
  "score_impact": 9,
  "score_facilite": 7,
  "actions_concretes": [
    "Transférer 12,000€ vers Livret A",
    "Objectif : 6 mois × 2,450€ = 14,700€"
  ]
}
```

**Avantages** :
- ✅ Recommandation basée sur règle fiable (fonds urgence < 3 mois)
- ✅ Validée par web (consensus : 6 mois)
- ✅ Montant personnalisé (dépenses mensuelles utilisateur)

Qu'en penses-tu ? Quelle option préfères-tu implémenter ?
