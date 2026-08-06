# Media Smart Lists — Étape 9 : premières données MDBList

## OAuth et interface

- URL manuelle MDBList affichée en toutes lettres pour les utilisateurs sans smartphone ;
- QR code et bouton prérempli conservés ;
- boutons `Actualiser les compteurs` et `Se déconnecter` forcés dans le style primaire legacy ;
- sélecteurs CSS renforcés pour le DOM Streamlit récent.

## Chargement en lecture seule

Le bouton `Charger mes données MDBList` charge uniquement au clic :

- historique films/épisodes ;
- Watchlist avec genres ;
- listes statiques et leurs éléments ;
- notes ;
- points de reprise ;
- Up Next ;
- séries abandonnées.

Aucune écriture MDBList.

## Premières pages fonctionnelles

- Tableau de bord : compteurs principaux ;
- Que regarder ? : Watchlist filtrable localement par genre et type ;
- En cours de lecture : reprises, Up Next et Dropped ;
- Nettoyage des listes : inventaire statique en lecture seule ;
- Statistiques : première synthèse commune.

## Installation

1. Envoyer à la racine GitHub : `app.py`, `mdblist_oauth.py`, `mdblist_provider.py`, `ETAPE-9.md`.
2. Commit : `feat: load core MDBList dataset and genre-filtered watchlist`.
3. Attendre le redéploiement, actualiser les compteurs puis charger les données.
