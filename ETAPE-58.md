# ÉTAPE 58 — Mémoire TMDB incrémentale + couverture complète des acteurs/studios

**Version : V58** · 1 fichier modifié : `app.py`

## Ce que ça règle

### 1. Augmenter le nombre d'appels TMDB (vos points n°1 et n°3)
- **Budget porté de 2000 → 6000 contenus.** Un gros consommateur (321 films,
  des milliers d'épisodes, 270 watchlist) est désormais couvert sans être
  coupé par le plafond de sécurité.
- **Couverture COMPLÈTE de l'historique** : auparavant, seuls les médias
  ayant *déjà* des genres étaient enrichis en acteurs/studios. Désormais,
  **tout média manquant de genres, studios OU acteurs** est interrogé.
  → Tu as désormais **tous tes acteurs et tous tes studios** de **tout ton
  historique** (page Statistiques + Que regarder ?), plus de doute possible.

### 2. Mémoire incrémentale basée sur les nouveautés (ton point n°2)
- `_fetch_tmdb_item` est désormais **cachée par contenu pendant 30 jours**
  (`@st.cache_data`). Chaque fiche film/série est mémorisée individuellement.
- **Un rechargement ne refait QUE les contenus NOUVEAUX** (ajoutés à une
  liste, vus depuis le dernier passage). Les contenus déjà enrichis ne
  déclenchent **aucun** appel TMDB → c'est exactement la « mémoire basée sur
  les dates d'action » que tu décrivais : on ne ré-interroge que les
  changements récents.
- **Gestion intelligente des échecs** :
  - Succès (200) → mis en cache.
  - 404 (inexistant) → mis en cache comme « rien à récupérer » (on ne
    réessaie jamais un id qui n'existe pas côté TMDB).
  - 5xx / coupure réseau / JSON cassé → **NON mis en cache** : l'item sera
    réessayé au prochain passage. Une micro-coupure ne « fige » donc jamais
    un contenu sans ses acteurs.

### 3. Impact sur les 40 s et la déconnexion mobile (ton point n°5)
- **Dans une même session/appareil** : le second chargement (et tous les
  suivants) est quasi instantané côté TMDB, car chaque fiche est déjà en
  mémoire. Le bouton « Actualiser » et les F5 à chaud ne rejouent plus les
  40 s.
- La charge de 40 s était aussi la **cause racine de la déconnexion mobile**
  (une WebSocket qui coupe pendant un long chargement). En réduisant cette
  charge sur les rechargements, le risque de déconnexion F5 diminue
  fortement.

## ⚠️ Limite honnête à connaître (Streamlit Community gratuit)

Le cache `st.cache_data` est **en mémoire** sur le serveur. Sur l'offre
gratuite, le conteneur **dort** après inactivité et la mémoire s'évapore.
Conséquence : le **tout premier** chargement de la journée (conteneur froid)
prend encore ~30-40 s **une fois**, puis tous les suivants sont rapides
tant que le conteneur reste éveillé.

> Si tu veux que **même le démarrage à froid** soit rapide (chargement de
> base en 2-3 s, enrichissement TMDB en option via un bouton), c'est le **V59**
> proposé : on te laisse décider après avoir testé le V58.

## Tests réalisés
- `python3 -m py_compile` ✅
- 14 tests unitaires (`tests/`) ✅
- AppTest : l'app démarre, écran d'accueil OK, aucune exception ✅
- Test focalisé : couverture (A/B enrichis, C complet exclu, D sans id = 0
  appel) ✅ et `_apply_tmdb_payload` (genres + studios compagnie+network +
  acteurs top 10) ✅

## Fichiers
- `app.py` (uniquement `_fetch_tmdb_item` et `_enrich_tmdb_metadata`)
