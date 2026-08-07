# Media Smart Lists — Étape 25 : calendrier réparé (vraie cause), badges Succès

## Calendrier : la vraie cause racine (confirmée par la doc officielle)

Les étapes précédentes échouaient car le code cherchait les identifiants
TMDb uniquement dans un bloc `ids` imbriqué… or la structure réelle des
réponses MDBList varie selon l'endpoint :

- **Watchlist** : les items portent `imdb_id` et surtout **`id` à plat**
  (chez MDBList, l'id d'un média **est** l'id TMDb — exemple : id 917496 =
  tmdb 917496) ;
- **Listes** : bloc `ids` imbriqué avec `tmdb` ;
- **Up Next** : `show.ids.tmdb`.

La nouvelle collecte (`_extract_media_ids`) lit donc toutes les formes :
`ids.tmdb`, `id` à plat, `tmdb_id`/`tmdbid`, `imdb_id` en secours, et les
items imbriqués (`{"movie": …}`, `{"show": …}`).

### Endpoints batch conformes à la doc officielle

La spécification OpenAPI officielle de MDBList
(github.com/linaspurinis/api.mdblist.com) confirme :

```text
POST /{provider}/any   avec {"ids": ["116006", "125198"], "append_to_response": […]}
```

Les identifiants sont des **chaînes**, le type `any` accepte films et séries
mélangés, 200 identifiants par appel. L'enrichissement utilise donc
`POST /tmdb/any` puis `POST /imdb/any` (pour les contenus sans id TMDb), avec
un second essai sans `append_to_response` si une version de l'API le refuse.

### Diagnostics visibles dans le calendrier

Un panneau « 🔍 Pourquoi ce calendrier contient-il ce qu'il contient ? »
affiche désormais : contenus scannés, identifiants TMDb/IMDb trouvés, fiches
reçues de MDBList, dates à venir dans l'horizon, et toute erreur éventuelle.
Si un contenu manque, ce panneau explique pourquoi (ex. série dont la date de
reprise n'est pas encore publiée).

## Mois triés chronologiquement (blindé)

Le graphique « Heures par mois » trie maintenant explicitement par clé
numérique (année × 100 + mois) — l'ordre alphabétique (01-2021, 01-2022,
02-2021…) est impossible. Les valeurs restent alignées sur les libellés.

## Barres de progression : fond vert

Le fond des barres de progression (genres, ADN, studios) n'est plus noir :
il reprend le vert translucide des barres des cartes « En cours de lecture »
(rgba(0,163,146,0.22) + bordure verte), avec le remplissage en dégradé
vert → citron.

## Page Succès restaurée (61 badges)

La page « 🏆 Succès » reprend la liste complète des badges de l'ancienne
application Trakt Smart Lists, branchée sur le modèle normalisé MDBList :

- paliers de temps (1 h → 5 ans) ;
- films (1 → 5000) ; épisodes (1 → 25 000) ; séries suivies (10+ épisodes,
  jusqu'à 200 épisodes d'une même série) ;
- marathons (4, 8, 12, 20 épisodes en 1 jour) ;
- diversité (genres, années de sortie) ;
- nocturne (20, 100, 500 vues de nuit, nuit blanche) ;
- visionnages totaux (1 → 50 000) ;
- rythme (365/730 jours, séries de 7/30 jours d'affilée) ;
- rewatchs (5/10 films revus) et coup de cœur (note ≥ 9).

Chaque badge verrouillé affiche sa barre de progression vers le déblocage,
triés du plus proche au plus lointain.

## Installation

Envoyer ces fichiers à la racine du dépôt :

- `app.py` (modifié)
- `mdblist_provider.py` (modifié)
- `stats_engine.py` (modifié)
- `achievements_engine.py` (NOUVEAU)
- `ETAPE-25.md` (NOUVEAU)

Aucun fichier à supprimer. Ne pas retoucher `calendar_engine.py`,
`history_engine.py` ni `wrapped_engine.py` (déjà à jour en ligne).
Aucun secret à modifier.

Commit conseillé :

```text
fix: real calendar id extraction, restore achievements badges
```
