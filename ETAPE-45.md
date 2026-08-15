# Media Smart Lists — Étape 45 : assistant « Migration ZIP Trakt → MDBList »

## 🚀 Nouvelle page au menu : « 📦 Migration Trakt → MDBList »

Un assistant web complet, dans un menu séparé (la 11ᵉ page), qui permet de
migrer les données d'un ZIP Trakt vers son compte MDBList **sans Python et
sans clé API** — juste la session OAuth déjà connectée.

### Le flux en 4 étapes

1. **Déposer le ZIP Trakt** (même parseur sécurisé que l'import local) ;
2. **Aperçu** : films vus, épisodes vus, séries concernées, rewatches
   (informés : MDBList ne garde que la dernière date), et **contenus sans
   correspondance** (pas d'id TMDb/IMDb utilisable) listés à l'écran ;
   choix des sections à migrer (historique, notes, Watchlist, listes) ;
   **mode simulation (dry-run)** par défaut — aucun POST ;
3. **Sauvegarde de sécurité** JSON + **rapport Excel d'aperçu** téléchargeables ;
4. **Confirmation explicite** → **écriture par lots** (100 max par appel)
   → **rapport Excel final** avec les onglets : Résumé, Historique films,
   Historique épisodes, Sans correspondance, Watchlist, Listes, Échecs.

### Points clés

- **Vraies dates conservées** : `POST /sync/watched` accepte `watched_at` par
  film, saison et épisode — l'historique migré garde les dates du ZIP ;
- **sans correspondance** identifiés et exclus (listés + onglet Excel) ;
- **écritures par lots** avec comptage des succès/échecs (onglet Échecs) ;
- listes **créées si absentes** (`create_list`) puis remplies
  (`add_list_items`) — jamais d'écriture dans une liste dynamique ;
- **simulation par défaut** : parfait pour valider le flux sans risque ;
- l'utilisateur a déjà migré son compte : la V45 sera testée en simulation
  avec un ZIP de test fourni, et l'écriture réelle reste à valider sur un
  compte de test.

## Fichiers

- `app.py` (modifié) — page + menu + dispatch ;
- `mdblist_provider.py` (modifié) — `raw_post`, `add_watchlist_items`,
  `create_list`, `add_list_items` ;
- `migration_engine.py` (NOUVEAU) — plan, payloads avec dates, rapport Excel ;
- `MEDIA-SMART-LISTS-TODO.md` (mis à jour).

## Installation

Envoyer ces fichiers à la racine du dépôt :

- `app.py`
- `mdblist_provider.py`
- `migration_engine.py` (NOUVEAU)
- `MEDIA-SMART-LISTS-TODO.md`
- `ETAPE-45.md` (NOUVEAU)

Aucun fichier à supprimer. Aucun secret à modifier.
