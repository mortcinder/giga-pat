# Search Providers - Architecture Multi-Provider v2.0

## Vue d'ensemble

Architecture pluggable pour les recherches web avec support de multiples providers et fallback automatique.

**Providers supportés** :
1. **Brave Search** - API officielle (2000 req/mois gratuit)
2. **Serper** - API Google Search (2500 req/mois gratuit)
3. **Tavily** - API AI-native search (1000 req/mois gratuit)
4. **DuckDuckGo** - Scraping gratuit illimité (pas de clé API)

## Architecture

```
search_providers/
├── __init__.py          # Exports publics
├── models.py            # SearchResult, ProviderConfig, SearchParams
├── base.py              # BaseSearchProvider (classe abstraite)
├── factory.py           # SearchProviderFactory (création + fallback)
├── brave_provider.py    # Implémentation Brave Search
├── serper_provider.py   # Implémentation Serper
├── tavily_provider.py   # Implémentation Tavily
├── ddgs_provider.py     # Implémentation DuckDuckGo
└── README.md            # Cette documentation
```

## Configuration

### config.yaml

```yaml
analyzer:
  web_research:
    # Provider principal
    provider: "brave"

    # Activer fallback automatique
    enable_fallback: true

    # Ordre de fallback (priorité décroissante)
    fallback_providers:
      - "brave"    # Priorité 1
      - "serper"   # Priorité 2
      - "tavily"   # Priorité 3
      - "ddgs"     # Priorité 4 (dernier recours)

    # Configuration par provider
    providers:
      brave:
        enabled: true
        rate_limit: 1.3
        timeout: 30
        retry_count: 3
        max_results: 10
```

### Variables d'environnement (.env)

```bash
# Clés API (seuls Brave, Serper et Tavily nécessitent une clé)
BRAVE_API_KEY=your-brave-api-key-here
SERPER_API_KEY=your-serper-api-key-here
TAVILY_API_KEY=your-tavily-api-key-here

# DuckDuckGo ne nécessite pas de clé
```

## Utilisation

### Via WebResearcher (recommandé)

```python
from tools.utils.web_research import WebResearcher

# Initialiser (lit config.yaml automatiquement)
config = load_config()
researcher = WebResearcher(config)

# Rechercher (API publique inchangée)
sources = researcher.search(
    sujet="Test",
    queries=["query 1", "query 2"],
    context="contexte"
)
```

### Utilisation directe d'un provider

```python
from tools.utils.search_providers import (
    SearchProviderFactory,
    SearchParams
)

# Créer un provider via factory
factory = SearchProviderFactory()
provider = factory.create_provider("brave", config)

# Rechercher
params = SearchParams(query="test", lang="fr", country="FR")
results = provider.search(params)

# results est une liste de SearchResult
for result in results:
    print(f"{result.title}: {result.url}")
```

### Créer une chaîne de fallback

```python
# Créer automatiquement la chaîne depuis config.yaml
providers = factory.create_fallback_chain(config)

# providers = [BraveProvider, SerperProvider, TavilyProvider, DDGSProvider]
# (seulement ceux qui sont disponibles)
```

## Ajouter un nouveau provider

1. **Créer le fichier** `{provider}_provider.py`

2. **Hériter de BaseSearchProvider** :

```python
from .base import BaseSearchProvider
from .models import SearchResult, SearchParams

class MyProvider(BaseSearchProvider):
    @property
    def provider_name(self) -> str:
        return "myprovider"

    def is_available(self) -> bool:
        return self.config.enabled and bool(self.config.api_key)

    def search(self, params: SearchParams) -> List[SearchResult]:
        # Implémenter la logique de recherche
        # Retourner une liste de SearchResult
        pass
```

3. **Enregistrer dans factory.py** :

```python
from .myprovider_provider import MyProvider

class SearchProviderFactory:
    PROVIDERS = {
        "brave": BraveSearchProvider,
        "serper": SerperSearchProvider,
        "tavily": TavilySearchProvider,
        "ddgs": DDGSSearchProvider,
        "myprovider": MyProvider,  # Ajouter ici
    }
```

4. **Ajouter dans config.yaml** :

```yaml
providers:
  myprovider:
    enabled: true
    rate_limit: 1.0
    timeout: 30
    retry_count: 3
    max_results: 10
    priority: 5
```

5. **Ajouter variable d'environnement** :

```bash
MYPROVIDER_API_KEY=your-key-here
```

## Fallback automatique

Le système essaie les providers dans l'ordre défini par `fallback_providers` :

1. **Brave** (API officielle, quota 2000/mois)
   - Si échec (quota épuisé, erreur réseau, etc.) → passe au suivant

2. **Serper** (API Google, quota 2500/mois)
   - Si échec → passe au suivant

3. **Tavily** (API AI-native, quota 1000/mois)
   - Si échec → passe au suivant

4. **DuckDuckGo** (scraping gratuit illimité)
   - Dernier recours (pas de limite)

### Logs de fallback

```
[INFO] Tentative 1/4: brave
[WARNING] ✗ Échec brave: Rate limit exceeded (429)
[INFO] → Fallback vers serper...
[INFO] Tentative 2/4: serper
[INFO] ✓ 5 résultats via serper
```

## Format des résultats

Tous les providers retournent le même format normalisé :

```python
SearchResult(
    url="https://example.com",
    title="Titre de la page",
    snippet="Extrait de la description...",
    relevance="Haute",  # "Haute", "Moyenne", "Faible"
    accessed_date="2025-11-18",
    provider="brave"  # Provider utilisé
)
```

## Tests

```bash
# Tests unitaires des providers
python tests/test_search_providers.py

# Tests d'intégration WebResearcher
python tests/test_web_research_integration.py
```

## Dépendances

```bash
# Obligatoires
pip install requests>=2.31.0

# Optionnelles (selon providers utilisés)
pip install duckduckgo-search>=6.0.0  # Pour DDGS
```

## Migration depuis v1.0

**Avant (v1.0)** :
- Un seul provider (Brave uniquement)
- Pas de fallback
- Configuration simple

**Après (v2.0)** :
- 4 providers disponibles
- Fallback automatique
- Configuration par provider
- **API publique inchangée** (compatibilité totale)

**Aucun changement nécessaire** dans analyzer.py ou risk_analyzer.py !

## Troubleshooting

### "Provider non disponible"

```
[WARNING] ✗ Provider brave non disponible: clé API manquante (BRAVE_API_KEY)
```

**Solution** : Ajouter la clé API dans `.env`

### "Tous les providers ont échoué"

```
[ERROR] Tous les providers ont échoué pour: query
```

**Causes possibles** :
- Toutes les clés API invalides/expirées
- Problème réseau
- Quotas épuisés pour tous les providers

**Solution** : Vérifier les logs pour identifier le problème spécifique

### "module duckduckgo-search non installé"

```
[WARNING] Module duckduckgo-search non installé
```

**Solution** : `pip install duckduckgo-search`

## Performances

**Rate limiting** :
- Configurable par provider
- Randomisation ±10% pour éviter patterns
- Respecte les limites API

**Retry logic** :
- Exponential backoff (1s, 2s, 4s...)
- Configurable par provider
- Timeout configurable

**Caching** :
- Pas de cache actuellement
- Pourrait être ajouté dans une future version

## Sécurité

- **Clés API** : Masquées dans les logs (`[REDACTED]`)
- **SSL** : Vérification activée pour toutes les requêtes
- **Variables d'environnement** : Jamais committées (`.env` dans `.gitignore`)

## Licence

Fait partie du projet Patrimoine Analyzer v2.1.3
