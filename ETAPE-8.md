# Media Smart Lists — Étape 8 : reconnexion instantanée

## Optimisation

Le cookie chiffré v2 contient désormais :

- access token ;
- refresh token ;
- expiration ;
- résumé du compte et des listes.

Au retour sur le même navigateur, si l'access token est encore valable, la connexion et les métriques sont restaurées sans appel réseau. Quand il expire, le refresh OAuth automatique reste utilisé. Les anciens cookies v1 sont lus puis convertis automatiquement.

## Interface

- le ruban `CHOISIS TA SOURCE` disparaît dès qu'une source est sélectionnée ou que MDBList est connecté ;
- bouton `Actualiser les compteurs` pour demander volontairement les dernières valeurs ;
- déconnexion inchangée et toujours révocatrice.

## Installation

1. GitHub : **Add file → Upload files**.
2. Envoyer `app.py`, `mdblist_oauth.py` et `ETAPE-8.md`.
3. Commit : `perf: restore encrypted MDBList session instantly from cookie`.
4. Attendre le redéploiement.
5. Se connecter une fois si nécessaire pour convertir l'ancien cookie, fermer l'onglet puis revenir.
