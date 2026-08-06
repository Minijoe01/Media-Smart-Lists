# Media Smart Lists — Étape 10 : genres et affiches

## Up Next

- affiche de série issue directement de `/upnext` ;
- chemin TMDb transformé en URL `w342` sans appel supplémentaire ;
- cellule avec liseré lime comme les cartes importantes du legacy ;
- séparation nette du numéro et du titre d'épisode.

## Watchlist par genre

L'endpoint Watchlist n'a pas renvoyé les champs `genres` malgré `append_to_response`. Le correctif n'effectue pas d'appel par film :

1. charge la liste officielle des genres via `/genres` pendant le dataset ;
2. quand un genre est sélectionné, utilise `/watchlist/items?filter_genre=...` ;
3. une requête maximum par genre, puis cache de session ;
4. plus aucun texte `Genres indisponibles`.

Les posters et MDB Scores sont affichés lorsqu'ils sont présents dans la réponse Watchlist.

## Installation

1. Envoyer `app.py`, `mdblist_oauth.py`, `mdblist_provider.py`, `ETAPE-10.md`.
2. Commit : `fix: add Up Next posters and server-side watchlist genre filters`.
3. Après redéploiement, recharger le dataset (11 requêtes attendues avec deux listes statiques).
