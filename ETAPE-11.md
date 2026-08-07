# Media Smart Lists — Étape 11 : sources de listes et posters legacy

## Posters

- URLs TMDb `w500` ;
- taille desktop : 88×132 px dans Que regarder, 100×150 px dans Up Next ;
- taille mobile responsive : 76×114 et 84×126 px ;
- proportions verticales conservées, chargement différé du navigateur.

## Que regarder ?

Ajout d'un sélecteur Source :

- Watchlist native ;
- toutes les listes statiques ;
- toutes les listes dynamiques.

Le filtre Genre fonctionne aussi sur une liste sélectionnée avec une seule requête par couple source/genre, puis cache de session.

Les lignes d'information privilégient maintenant, selon disponibilité :

- genres ;
- durée ;
- note IMDb/TMDb/Trakt ;
- MDB Score ;
- nom de la source.

## Listes

La page inventorie désormais les listes statiques et dynamiques avec leur type et leurs compteurs.

## Installation

1. Envoyer `app.py`, `mdblist_oauth.py`, `mdblist_provider.py`, `ETAPE-11.md`.
2. Commit : `feat: add all MDBList sources and restore larger high-res posters`.
3. Recharger le dataset après redéploiement.
