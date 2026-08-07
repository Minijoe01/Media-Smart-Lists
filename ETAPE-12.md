# Media Smart Lists — Étape 12 : modèle commun, sources personnalisées et progression legacy

## Modèle normalisé

Ajout de `normalized_model.py` avec :

- identité média et déduplication ;
- sources individuelles ;
- vues agrégées ;
- progression de série normalisée ;
- version de schéma pour invalider automatiquement les anciens datasets en mémoire après déploiement.

## Sources Que regarder ?

- Watchlist MDBList ;
- chaque liste statique ;
- chaque liste dynamique ;
- toutes les listes statiques ;
- toutes les listes dynamiques ;
- toutes les listes personnelles ;
- Watchlist + toutes les listes.

Les agrégats sont dédupliqués. Le filtre genre fonctionne aussi sur les agrégats et affiche son coût API avant mise en cache de session.

## Progression

Chaque série Up Next affiche :

- poster w500 agrandi ;
- épisodes vus / total ;
- temps estimé regardé ;
- épisodes et temps restants ;
- pourcentage ;
- barre jaune/verte legacy ;
- prochain épisode.

## Installation

Envoyer `app.py`, `mdblist_oauth.py`, `mdblist_provider.py`, `normalized_model.py`, `ETAPE-12.md`.

Commit : `feat: add normalized sources and legacy series progress widgets`.

Après redéploiement, le dataset précédent sera invalidé : cliquer une fois sur `Charger mes données MDBList`.
