# Media Smart Lists — Étape 22 : durées réelles, temps global précis, calendrier long

## Durée réelle des épisodes (correction « Connasse »)

L'historique affichait parfois une durée cumulée au lieu d'une durée par épisode
(ex. « Connasse » : 71 épisodes d'~1 min, affichés 2 h 22 chacun).

Résolution corrigée :

1. durée explicite de l'épisode (1 à 90 min — les formats courts sont acceptés) ;
2. durée explicite par épisode au niveau de la série ;
3. runtime de la série s'il ressemble déjà à une durée d'épisode (≤ 90 min) ;
4. runtime cumulé (toute la série) divisé par le nombre d'épisodes connu ;
5. conversion secondes → minutes ;
6. secours 20 min pour Animation/Anime, sinon 45 min.

Le nombre d'épisodes vient d'abord des métadonnées de la série, puis du compte
des épisodes réellement vus dans l'historique.

Fixture validée :

```text
Connasse : 142 minutes cumulées / 71 épisodes = 2 minutes par épisode
```

## Temps global plus précis

Le formatage des grandes durées conserve maintenant les heures et les minutes :

```text
20 min
2h35            (format court sous 24 h)
3 j, 4 h
7 mois 15 j, 2 h 35 min
1 an 1 mois 10 j, 2 h 35 min
```

Le format court « 2h22 » reste utilisé pour les durées de moins d'un jour
(films, épisodes) afin de ne pas alourdir les listes.

## Calendrier : horizons longs (fin d'année, 2027)

### Nouvelles options d'horizon

L'horizon maximum passe de 120 jours à 1 an et demi :

```text
7 j · 14 j · 30 j · 60 j · 90 j · 120 j · 6 mois · 1 an · 1 an et demi
```

### Mode MDBList (calendrier officiel)

L'endpoint `/calendar/events` MDBList est limité à 120 jours par appel.
Pour les horizons plus longs, l'application découpe la période en tranches de
120 jours et fusionne les résultats. Le bouton indique le nombre d'appels
réels (« 1 appel », « 4 appels », …).

### Mode secours (sans service calendrier MDBList)

Le calendrier de secours n'est plus limité à 120 jours : il couvre tout
l'horizon choisi avec les dates déjà présentes dans les données chargées.

Il détecte maintenant davantage de champs de dates :

- films : `release_date`, `released`, `released_digital`,
  `digital_release_date`, `theatrical_date`, `premiere_date`, `digital_date`,
  `dvd_date`, `dvd_release_date`, `physical_release_date`, `bluray_date` ;
- séries : `first_air_date`, `next_air_date`, `premiere_date`, etc. ;
- épisodes futurs annoncés (`next_episode_to_air` / `last_episode_to_air`) :
  une série en pause dont la reprise est programmée (ex. janvier 2027)
  apparaît avec la date de son prochain épisode à venir.

Un événement dont la date est déjà passée n'apparaît jamais dans le calendrier.

## Installation

Envoyer ces fichiers à la racine du dépôt :

- `app.py`
- `calendar_engine.py`
- `history_engine.py`
- `ETAPE-22.md`

Commit conseillé :

```text
feat: real episode runtimes, precise durations and long-range calendar
```

Aucun secret à modifier.
