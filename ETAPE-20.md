# Media Smart Lists — Étape 20 : Calendrier et historique des vues

## Calendrier des sorties restauré

La page **Calendrier des sorties** utilise l'endpoint personnel MDBList prévu à cet effet.

### Chargement maîtrisé

Un horizon complet est obtenu avec une seule requête ciblée :

- 7 jours ;
- 14 jours ;
- 30 jours ;
- 60 jours ;
- 90 jours ;
- 120 jours, maximum accepté par MDBList.

Le résultat, limité à 1000 événements par MDBList, est mémorisé pour la session. Changer les filtres, le tri ou la recherche ne consomme ensuite aucun quota supplémentaire.

### Événements

Le normaliseur accepte :

- sorties de films ;
- premières de séries ;
- prochains épisodes ;
- réponses MDBList directes ou regroupées par type/date ;
- sorties liées aux acteurs et membres d'équipe favoris, optionnelles.

### Filtres et affichage

- Films / Séries / Épisodes ;
- aujourd'hui ;
- 7, 30 ou 90 prochains jours ;
- recherche par titre ou épisode ;
- tri par date, titre ou type ;
- regroupement par journée ;
- heure locale Europe/Paris ;
- posters depuis les données déjà chargées, avec enrichissement groupé facultatif si nécessaire.

### Exports

- CSV ;
- fichier `.ics` importable dans Google Agenda, Apple Calendar, Outlook et les applications compatibles.

## Historique des vues restauré

L'historique se trouve dans la page **Statistiques**, comme dans l'application legacy.

Il fusionne :

- films vus ;
- épisodes vus ;
- métadonnées des séries ;
- genres ;
- runtimes ;
- nombres de lectures lorsqu'ils sont fournis ;
- notes personnelles de films, séries ou épisodes.

### Filtres

- tout l'historique ;
- 7, 30 ou 90 derniers jours ;
- année en cours ;
- période personnalisée ;
- Films / Épisodes ;
- genre ;
- recherche ;
- tri récent, ancien, titre ou durée.

### Indicateurs

- nombre d'entrées ;
- lectures connues ;
- films ;
- temps de visionnage estimé ;
- six genres les plus regardés ;
- tableau détaillé Date, Type, Titre, Épisode, Année, Genres, Durée, Lectures et Note personnelle.

### Exports

- historique CSV ;
- historique JSON fournisseur-neutre et versionné.

## Limite MDBList clairement indiquée

MDBList fournit principalement la dernière date connue pour chaque film ou épisode, accompagnée du nombre de lectures lorsque ce champ existe. Il ne permet donc pas toujours de reconstruire la chronologie détaillée de tous les revisionnages.

Le futur `TraktZipProvider` pourra conserver tous les événements originaux présents dans un export ZIP Trakt et alimenter exactement la même interface.

## Sécurité et quota

- historique : données déjà chargées, aucun appel supplémentaire ;
- calendrier : un appel ciblé par horizon demandé ;
- filtres, tris, recherche et exports : calcul local ;
- aucun secret dans les exports ;
- aucune écriture MDBList.

## Installation

Envoyer uniquement ces cinq fichiers à la racine du dépôt :

- `app.py`
- `mdblist_provider.py`
- `calendar_engine.py`
- `history_engine.py`
- `ETAPE-20.md`

Commit conseillé :

```text
feat: restore personal calendar and viewing history
```

Aucun secret à modifier et aucun rechargement complet obligatoire pour ouvrir le calendrier ou consulter l'historique déjà présent.
