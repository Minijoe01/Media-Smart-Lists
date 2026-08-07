# Media Smart Lists — Étape 21 : corrections statistiques, ajouts et continuité IA

## Durées intelligentes

L'affichage des grandes durées choisit maintenant automatiquement l'unité :

```text
20 min
2h05
3 j 4 h
10 mois 12 j
87 ans 4 mois
```

Un total aberrant n'est donc plus affiché sous la forme `31902j 7h`.

## Runtime des épisodes corrigé

L'historique ne réutilise plus aveuglément le champ `runtime` d'une série pour chacun de ses épisodes.

Ordre de résolution :

1. runtime propre à l'épisode ;
2. champ explicite `episode_runtime`, `runtime_per_episode` ou `average_runtime` ;
3. runtime de série s'il ressemble déjà à une durée d'épisode ;
4. durée cumulée de la série divisée par le nombre total d'épisodes ;
5. conversion secondes → minutes lorsque le format le justifie ;
6. secours 20 minutes pour Animation/Anime, sinon 45 minutes.

Fixture validée :

```text
Dragon Ball Z : 4560 minutes cumulées / 228 épisodes = 20 minutes par épisode
```

Les statistiques globales et par genre utilisent la valeur corrigée.

## Historique des vues repliable

Dans **Statistiques**, tout le module `Historique des vues` est maintenant placé dans un expander fermé par défaut. Les compteurs généraux restent visibles, mais les filtres et milliers de lignes ne prennent de place que lorsque l'utilisateur les demande.

## Calendrier de secours

Si `/calendar/events` MDBList échoue ou renvoie une liste vide, Media Smart Lists construit un calendrier depuis :

- les prochains épisodes Up Next ;
- les dates de sortie déjà présentes dans la Watchlist et les listes.

Le mode de secours est clairement indiqué et conserve filtres, cartes, CSV et ICS.

## Historique des ajouts aux listes

Dans **Nettoyage des listes**, un nouveau panneau repliable affiche une ligne par appartenance réelle :

- date et heure d'ajout Europe/Paris ;
- film ou série ;
- titre et année ;
- conteneur exact ;
- filtre par conteneur, période et type ;
- recherche ;
- tri récent/ancien/conteneur/titre ;
- export CSV.

Les vues agrégées ne sont pas comptées comme des conteneurs. Une date absente de la réponse MDBList est affichée honnêtement comme non fournie.

## Continuité si la conversation atteint sa limite

Trois fichiers de transmission sont ajoutés :

### `MEDIA-SMART-LISTS-TODO.md`

Feuille de route active et à jour : fonctionnalités terminées, prochaines pages legacy, TraktZipProvider, écritures MDBList, qualité, Kodi et outil communautaire.

### `AI-HANDOFF.md`

Contexte compact destiné à une autre intelligence artificielle : liens, architecture, secrets interdits, règles visuelles, état de migration, méthode de travail et ordre de reprise.

### `migrate_trakt_zip_to_mdblist.py`

Script local qui a servi à la migration réelle. Il reste :

- dry-run par défaut ;
- sans suppression ;
- avec clé masquée ;
- avec sauvegarde des rewatches ;
- protégé contre les ZIP dangereux ;
- avec préflight et confirmation `IMPORTER`.

SHA-256 du script fourni :

```text
011ba6b514cb27ee4c8d297ee28b39b1930cc325b2b71cb93ab6c63ec86c8b7b
```

Il est le candidat principal au futur dépôt séparé `Minijoe01/Trakt-ZIP-to-MDBList`.

## Installation

Envoyer ces neuf fichiers à la racine du dépôt :

- `app.py`
- `mdblist_provider.py`
- `calendar_engine.py`
- `history_engine.py`
- `list_audit_engine.py`
- `MEDIA-SMART-LISTS-TODO.md`
- `AI-HANDOFF.md`
- `migrate_trakt_zip_to_mdblist.py`
- `ETAPE-21.md`

Commit conseillé :

```text
fix: correct episode runtimes and add project handoff
```

Aucun secret à modifier. Le script de migration ne contient aucune clé réelle.
