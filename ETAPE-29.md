# Media Smart Lists — Étape 29 : durées corrigées, import ZIP fluide, enrichissement auto

## Durée de visionnage corrigée (fini les « 22 ans »)

La page « En cours de lecture » affichait des durées absurdes pour certaines
émissions (ex. « L'amour est dans le pré » : 22 ans de visionnage). La cause :
MDBList renvoie parfois la durée CUMULÉE de toute la série (ex. 32 220 min =
358 épisodes × ~90 min) à la place de la durée d'un épisode.

La durée d'un épisode est maintenant normalisée comme dans l'historique :
- 1 à 300 min → durée d'épisode ;
- au-delà → divisée par le nombre d'épisodes connu, ou convertie
  secondes → minutes ;
- sinon 45 min par défaut.

Exemple « L'amour est dans le pré » : 358/360 épisodes vus ≈ 22 jours (et non
22 ans), « il en reste 2 · environ 3 h ».

## Import ZIP Trakt : le blocage quand on est connecté est corrigé

Un bug faisait disparaître l'encart d'import ZIP quand on était déjà connecté
à MDBList : la restauration de session forçait le choix « MDBList » et
écrasait votre choix « Importer un ZIP Trakt ». Corrigé : votre choix explicite
n'est plus écrasé.

## Enrichissement automatique après import ZIP

Si vous êtes déjà connecté à MDBList, l'import ZIP déclenche **automatiquement**
l'enrichissement avec les métadonnées MDBList (genres, posters, durées, notes)
— quelques appels groupés seulement, en lecture seule, aucun quota épuisé.
Le message d'import l'indique. Sinon, un bouton « ✨ Enrichir avec MDBList »
reste disponible sur le dashboard.

L'enrichissement couvre désormais aussi les **séries en cours (Up Next)** et
les **reprises en pause (playback)** : les posters apparaissent dans « En
cours de lecture » et « Progression Fantôme ».

## Logigramme simplifié

Le tableau de bord affiche une seule source à la fois :
- si vous avez choisi « Connecter MDBList » → uniquement la connexion ;
- si vous avez choisi « Importer un ZIP Trakt » → uniquement l'import ;
- sinon → la source de données active (MDBList ou ZIP), avec ses boutons.

Fini le mélange de blocs qui déroutait.

## Chargement MDBList : session expirée détectée

Quand la session MDBList est révoquée ou expirée (ex. « 8 sections
indisponibles »), l'application déconnecte proprement et affiche un message
clair (« Reconnecte-toi ») au lieu d'un CHARGEMENT PARTIEL silencieux.
De plus, si vous chargez les données MDBList alors que des données ZIP sont
affichées, un avertissement « ⚠️ Remplacement » prévient que les données ZIP
seront remplacées.

## Installation

Envoyer ces fichiers à la racine du dépôt :

- `app.py` (modifié)
- `normalized_model.py` (modifié)
- `ETAPE-29.md` (NOUVEAU)

Aucun fichier à supprimer. Ne pas retoucher les autres fichiers (déjà à jour
en ligne). Aucun secret à modifier.

Commit conseillé :

```text
fix: sane episode runtimes, auto-enrich ZIP import, simpler dashboard flow
```
