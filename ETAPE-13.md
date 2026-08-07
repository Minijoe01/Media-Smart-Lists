# Media Smart Lists — Étape 13 : moteur personnel legacy

## Corrections

- libellé Dashboard : `Contenus dans votre Watchlist` ;
- cartes Que regarder avec liseré lime comme En cours ;
- schéma versionné : un ancien dataset Streamlit est invalidé automatiquement.

## Sources personnalisées

- Watchlist ;
- chaque liste statique ;
- chaque liste dynamique ;
- toutes les statiques ;
- toutes les dynamiques ;
- toutes les personnelles ;
- Watchlist + toutes les listes.

Noms et types proviennent exclusivement du compte MDBList connecté. Aucun nom utilisateur n'est codé en dur.

## Moteur sans requête supplémentaire

Ajout de `recommendation_engine.py` :

- profil de goûts ;
- score explicable /100 ;
- friction /100 ;
- raisons, alertes et tags ;
- filtres recherche/note/temps/statut ;
- tris historiques ;
- 21 presets legacy ;
- roulette pondérée et roulette découverte.

Le moteur utilise uniquement le dataset déjà chargé. Les filtres, scores, tris, presets et roulettes ne consomment aucun appel MDBList. Seul un filtre Genre demandé pour une source non encore filtrée peut coûter une requête par source composante, ensuite mise en cache de session.

## Installation

Envoyer `app.py`, `mdblist_oauth.py`, `mdblist_provider.py`, `normalized_model.py`, `recommendation_engine.py`, `ETAPE-13.md`.

Commit : `feat: restore provider-neutral personal scoring presets and roulette`.

Après redéploiement, recharger une fois les données MDBList.
