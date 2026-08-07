# Media Smart Lists — Étape 17 : audits combinés et Progression Fantôme

## Correction de l'audit des listes

Le sélecteur **Conteneur à auditer** propose maintenant les mêmes sources que **Que regarder ?** :

- Watchlist MDBList ;
- chaque liste statique ;
- chaque liste dynamique ;
- toutes les listes statiques ;
- toutes les listes dynamiques ;
- toutes les listes personnelles ;
- Watchlist + toutes les listes.

Les vues combinées sont dédupliquées et clairement identifiées comme des aperçus non modifiables.

Important : elles restent exclues de l'index des conteneurs réels utilisé par la Recherche de doublons. Elles ne créent donc aucun faux doublon.

## « Combiner les signaux » clarifié

L'ancien menu grisé a été supprimé.

- aucun signal sélectionné : tous les contenus sont affichés ;
- un seul signal : ce signal est appliqué directement ;
- au moins deux signaux : le choix apparaît avec une explication :
  - `Au moins un` = le contenu correspond à n'importe lequel des critères ;
  - `Tous les signaux` = le contenu doit correspondre à chacun des critères.

## Progression Fantôme restaurée

La page legacy **Progression Fantôme** utilise la section `/sync/playback` déjà chargée dans le dataset :

- films et épisodes en reprise ;
- pourcentage visionné ;
- durée et temps restant lorsqu'ils sont connus ;
- date de dernière activité ;
- prochain épisode identifié par saison et numéro ;
- poster lorsqu'il est fourni ;
- indication des progressions manuelles.

### « Tu peux finir ça ce soir »

Les trois contenus au temps restant le plus court sont proposés automatiquement, sans requête supplémentaire.

### Filtres et tris

- recherche locale ;
- Films / Épisodes ;
- tranches de progression ;
- activité récente ou ancienne ;
- temps restant court ou long ;
- progression croissante ou décroissante ;
- titre A → Z ou Z → A ;
- affichage de 30, 60 ou toutes les progressions.

## Sécurité et quota

- aucun appel API supplémentaire ;
- aucune suppression de progression ;
- aucune écriture MDBList ;
- aucun changement de secret ;
- aucune dépendance Plex ou Kometa.

L'application Kodi reste indépendante. Les idées de Kometa sont utilisées uniquement pour structurer les moteurs locaux de règles et d'aperçu.

## Installation

Envoyer uniquement ces quatre fichiers à la racine du dépôt :

- `app.py`
- `list_audit_engine.py`
- `playback_engine.py`
- `ETAPE-17.md`

Commit conseillé :

```text
feat: add aggregate audits and restore local ghost progress
```

Aucun rechargement obligatoire du dataset.
