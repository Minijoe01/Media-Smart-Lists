# Media Smart Lists — Étape 18 : lecture active ciblée et fusion des doublons

## Pourquoi la page ne montrait que les pauses

MDBList sépare maintenant deux états :

- `/sync/playback` : reprises mises en pause ;
- `/sync/now-playing` : scrobbles réellement actifs.

L'étape 17 utilisait uniquement la première section, comme l'écran Activity de MDBList. Ce n'était donc pas une erreur de tri : la source interrogée représentait seulement les pauses.

## Lecture en cours maintenant

La page **Progression Fantôme** contient désormais deux blocs distincts :

1. `Lecture en cours maintenant` ;
2. `Reprises mises en pause`.

Le bouton :

```text
Actualiser la lecture en cours · 1 appel
```

interroge uniquement `/sync/now-playing`. Il ne recharge plus les onze sections du dataset.

### Progression locale

Après cet unique contrôle réseau, la progression est estimée localement à partir :

- du pourcentage renvoyé par MDBList ;
- du runtime ;
- du temps écoulé depuis le contrôle.

Le fragment visuel est recalculé chaque minute sans appel API supplémentaire.

### Actualisation automatique facultative

Une option désactivée par défaut permet un nouveau contrôle toutes les cinq minutes tant que la page reste ouverte :

```text
environ 12 appels MDBList par heure maximum
```

Le coût est affiché avant activation. Le mode manuel reste le mode par défaut.

## Posters

Les posters absents de `/sync/playback` ou `/sync/now-playing` sont recherchés localement dans :

- la Watchlist ;
- les listes personnelles ;
- Up Next / En cours ;
- l'historique déjà chargé.

Le rapprochement utilise les identifiants TMDb, IMDb, TVDb, Trakt et MDBList, puis titre + année. Aucun appel supplémentaire n'est effectué pour un poster.

Si un contenu actif n'existe dans aucune section déjà chargée et que MDBList ne fournit aucun poster, la carte reste volontairement sans image plutôt que de déclencher une requête par contenu.

## Fusion de Recherche de doublons

L'onglet séparé **Recherche de doublons** est supprimé du menu.

Dans **Nettoyage des listes**, la colonne `Présent dans` affiche maintenant les noms exacts de tous les conteneurs lorsqu'un contenu correspond au signal `Présents dans plusieurs conteneurs`.

La fonctionnalité est donc conservée sans doublonner l'interface.

## Boutons d'export

Les boutons :

- Télécharger l'audit CSV ;
- Télécharger l'audit JSON ;

utilisent maintenant explicitement le style primaire legacy : gradient vert Aston Martin, coins et dimensions historiques, sans vert olive Streamlit.

## Sécurité et quota

- mode live manuel par défaut : 0 appel tant que le bouton n'est pas utilisé ;
- actualisation manuelle : 1 appel ciblé ;
- calcul de progression entre deux contrôles : 0 appel ;
- recherche locale du poster : 0 appel ;
- aucune suppression ;
- aucune écriture MDBList ;
- cache live effacé à la déconnexion.

## Installation

Envoyer uniquement ces quatre fichiers à la racine du dépôt :

- `app.py`
- `mdblist_provider.py`
- `playback_engine.py`
- `ETAPE-18.md`

Commit conseillé :

```text
feat: add targeted now playing refresh and merge duplicate audit
```

Aucun secret à modifier et aucun rechargement complet du dataset n'est nécessaire pour tester la lecture active.
