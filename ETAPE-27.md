# Media Smart Lists — Étape 27 : import ZIP Trakt, Excel affiné, liens uniformisés

## Import ZIP Trakt — fonctionnel 🎉

Le bouton « 📦 Importer un ZIP Trakt » du tableau de bord est désormais réel.
Il suffit de déposer votre export ZIP Trakt (Settings → Your data → Export) :

- **lecture seule** : aucune écriture, aucun appel API, aucune connexion Trakt ;
- **mêmes protections que le script de migration** : zip-slip, chemins
  absolus, ZIP invalides, fichiers ou archives trop volumineux sont refusés ;
- **le même NormalizedDataset que MDBList est produit** : historique
  événementiel complet (rewatches inclus), notes, Watchlist, listes
  statiques, reprises en pause, séries abandonnées ;
- toutes les pages fonctionnent ensuite à l'identique : Statistiques,
  Rendez-vous annuel, Succès, Calendrier, Sauvegarde, Tableau de bord.

Un récapitulatif s'affiche à l'import (films vus, épisodes, séries, notes,
watchlist, listes). Les dates complètes de chaque visionnage sont conservées
(les rewatches apparaissent dans l'historique, contrairement à MDBList qui ne
garde que la dernière date).

## Export Excel affiné

- **Largeurs de colonnes automatiques** : chaque colonne s'ajuste à la
  largeur maximale de son contenu (en-tête compris), bornée entre 8 et 80
  caractères — fini les colonnes trop étroites au moment de l'ouverture ;
- **onglet « Mes contenus »** (remplace « Watchlist ») : tous les contenus de
  la Watchlist ET de chaque liste (statique, dynamique, IA, flux) avec une
  colonne « Liste » indiquant le conteneur de provenance.

## Liens contenus uniformisés

Les 3 liens (JustWatch, TMDB, MDBList) des cartes En cours / Fantôme /
Calendrier sont maintenant de petits **badges citron discrets** avec
info-bulle au survol :
- 🔎 « Où regarder sur JustWatch »
- TMDB « Lien vers la fiche TMDB »
- MDBL « Lien vers la fiche MDBList »

Même style partout, peu de place, couleur cliquable.

## Connexion sans smartphone : lien direct

Le bloc « SANS SMARTPHONE » propose désormais un **lien direct cliquable** :
la page d'autorisation s'ouvre avec le code déjà pré-rempli
(`verification_uri_complete`), le code reste affiché en gros en secours.

## Calendrier : diagnostic du service officiel enrichi

Le message du calendrier indique maintenant clairement pourquoi le service
officiel n'a pas répondu :
- erreur HTTP précise (ex. « MDBList a répondu HTTP 4xx ») ;
- ou « réponse HTTP 200 mais aucun événement » (structure vide) ;
- ou « réponse avec une structure non reconnue » (clés de la réponse).

Ces informations s'affichent à la fois dans le message principal et dans le
panneau « 🔍 Pourquoi ce calendrier… ».

## Déconnexion

Un espace a été ajouté entre le texte de la sidebar et le bouton
« 🔌 Se déconnecter de MDBList » pour une meilleure lisibilité.

## Installation

Envoyer ces fichiers à la racine du dépôt :

- `app.py` (modifié)
- `mdblist_provider.py` (modifié)
- `excel_export.py` (modifié)
- `trakt_zip_provider.py` (NOUVEAU)
- `ETAPE-27.md` (NOUVEAU)

Aucun fichier à supprimer. Ne pas retoucher `calendar_engine.py`,
`history_engine.py`, `stats_engine.py`, `wrapped_engine.py`,
`achievements_engine.py`, `dashboard_engine.py` (déjà à jour en ligne).
Aucun secret à modifier.

Commit conseillé :

```text
feat: Trakt ZIP import, refined excel export, uniform content links
```
