# Media Smart Lists — Étape 30 : dashboard clair, bouton MDBList restauré, cache, audit listes

## 🔴 Bouton « Charger mes données MDBList » restauré (bug critique V29)

La V29 avait supprimé, après connexion MDBList, le bouton permettant de
charger les données (un `return` placé trop tôt dans le logigramme). Ce bouton
est de retour, plus visible que jamais, avec un libellé clair :
- « 📥 Charger mes données MDBList » quand rien n'est encore chargé ;
- « 🔄 Actualiser mes données MDBList » quand les données sont déjà affichées.

## Cache persistant (moins d'appels API)

Le chargement MDBList passe par un **cache d'une heure** : un simple
rechargement de la page (F5) ou un retour sur l'application ne rejoue plus
tous les appels API. Le cache est par utilisateur (clé dérivée du token, jamais
le token lui-même). Le bouton « Actualiser » vide ce cache et recharge depuis
l'API. Une mention « extrait du cache » l'indique le cas échéant.

## Tableau de bord : clarté maximale (badge de source)

Le dashboard indique désormais en permanence **quelle source on consulte** :

- 🔵 **DONNÉES MDBLIST · TEMPS RÉEL** : données de ton compte MDBList ;
- 🟢 **DONNÉES TRAKT · IMPORT ZIP** : données de ton export ZIP Trakt ;
- ⚠️ **AUCUNE DONNÉE CHARGÉE** : rien à afficher pour l'instant.

Ordre logique des actions :
1. badge de source ;
2. deux cartes de choix (Connecter MDBList / Importer un ZIP Trakt) avec état ;
3. actions en attente (connexion ou import) ;
4. données actives + leurs boutons (Charger/Actualiser pour MDBList,
   Enrichir pour ZIP) ;
5. vue d'ensemble + widgets (temps, rythme, compteurs à vie).

Plus aucun bloc n'écrase un autre : tout est visible, dans l'ordre.

## Enrichissement ZIP : tous les contenus, posters inclus

L'enrichissement ZIP interroge désormais **tous** les contenus par lots de
200 (1 appel par lot), au lieu des 200 premiers seulement. C'était la cause
des posters manquants : avec 570+ identifiants, seuls les 200 premiers étaient
enrichis. Vérifié : 250 contenus → 2 lots → 250/250 posters + genres.

## Session MDBList expirée : déconnexion propre

Quand la session MDBList est révoquée (ex. « 8 sections indisponibles »),
l'application déconnecte proprement et invite à se reconnecter, au lieu d'un
« CHARGEMENT PARTIEL » silencieux.

## Nettoyage des listes : distinguer « à retirer » et « à revoir »

Nouveaux indicateurs dans « Nettoyage des listes », basés sur la comparaison
entre la date d'ajout dans la liste et la date du dernier visionnage :

- 📌 **Vu · à retirer** : contenu déjà vu, ajouté à la liste AVANT son
  visionnage → probablement oublié de l'enlever ;
- 🔄 **Vu · à revoir** : contenu déjà vu, ajouté APRÈS son visionnage →
  remis exprès pour le revoir un jour.

Une explication affiche les compteurs, et deux nouveaux filtres « Signaux »
permettent de ne voir que l'une ou l'autre catégorie.

## Installation

Envoyer ces fichiers à la racine du dépôt :

- `app.py` (modifié)
- `list_audit_engine.py` (modifié)
- `ETAPE-30.md` (NOUVEAU)

Aucun fichier à supprimer. Ne pas retoucher `normalized_model.py` (déjà à
jour en ligne, V29) ni les autres fichiers. Aucun secret à modifier.

Commit conseillé :

```text
fix: restore MDBList load button, persistent cache, list watch audit
```
