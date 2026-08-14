# Media Smart Lists — Étape 36 : documentation de transmission + écritures MDBList (v1)

## Documentation de transmission (pour un autre agent IA)

Deux fichiers ont été entièrement réécrits pour permettre la reprise du
projet par une autre IA (ou par toi-même après une limite de conversation) :

- **`AI-HANDOFF.md`** : le dossier de reprise complet — mission, liens, date,
  architecture, **état actuel (V35)**, points sensibles / leçons apprises,
  prochaines étapes, méthode de travail, règles de test ;
- **`MEDIA-SMART-LISTS-TODO.md`** : la feuille de route à jour — tout ce qui
  est terminé (V35) et ce qui reste (écritures MDBList, dépôt communautaire,
  docs & qualité, Kodi).

En cas de limite de conversation : copie l'URL de la conversation vers un
autre agent, ou transmets ces deux fichiers + le code GitHub.

## Écritures MDBList — première version (suppression sécurisée)

C'est le début des **écritures** (l'utilisateur veut retrouver le pouvoir de
l'ancienne app Trakt : supprimer un doublon sélectionné, etc.).

### Nouvelles méthodes dans `mdblist_provider.py`

```text
remove_watchlist_items(movies, shows)  → POST /watchlist/items/remove
remove_list_items(list_id, movies, shows) → POST /lists/{id}/items/remove
set_watched(movies, shows, watched)    → POST /sync/watched (ou /remove)
set_rating(movies, shows, rating)      → POST /sync/ratings (ou /remove)
set_dropped(shows, dropped)            → POST /sync/dropped (ou /remove)
```

Les payloads sont conformes à la documentation OpenAPI officielle MDBList
(`{"movies": [{"tmdb": …}], "shows": [{"imdb": …}]}`).

### UI « Suppression sécurisée » dans Nettoyage des listes

Un nouveau bloc « 🗑️ Suppression sécurisée dans cette liste » apparaît pour
les **listes statiques** et la **Watchlist** (jamais pour les listes
dynamiques/IA/flux ni les vues combinées) :

1. sélection d'un contenu individuel de la liste ;
2. **aperçu** de ce qui va être retiré ;
3. **téléchargement d'une sauvegarde de sécurité** (JSON) avant toute
   écriture ;
4. **confirmation explicite** (case à cocher) ;
5. écriture unique via l'API MDBList ;
6. message de confirmation + invitation à actualiser les données.

Les autres opérations d'écriture (marquer vu/non-vu, notes, abandonnées)
sont prêtes côté API et seront branchées dans les prochaines étapes.

## Installation

Envoyer ces fichiers à la racine du dépôt :

- `app.py` (modifié)
- `mdblist_provider.py` (modifié)
- `list_audit_engine.py` (modifié)
- `AI-HANDOFF.md` (réécrit)
- `MEDIA-SMART-LISTS-TODO.md` (réécrit)
- `ETAPE-36.md` (NOUVEAU)

Aucun fichier à supprimer. Ne pas retoucher les autres fichiers (déjà à jour
en ligne). Aucun secret à modifier.

Commit conseillé :

```text
feat: MDBList secure remove (lists/watchlist), fresh handoff docs
```
