# Media Smart Lists — Étape 31 : thème des boutons, bascule de source, posters fiables

## Boutons au thème + bouton « Gérer la connexion » réparé

- Le CSS des boutons couvre maintenant **toutes les structures de boutons de
  Streamlit 1.60** (`stBaseButton-primary/secondary`, `baseButton-*`) : plus
  aucun bouton ne retombe sur le style par défaut (bleu/gris) ; tout suit le
  thème verre vert / dégradé vert.
- **Bug corrigé** : le bouton « 🔐 Gérer la connexion MDBList » partageait la
  même clé Streamlit que « Préparer la connexion MDBList » → il ne faisait
  rien. Il a sa propre clé, déclenche un `st.rerun()` et ouvre bien le
  connecteur.

## Basculer facilement entre ZIP Trakt et MDBList

Quand des données ZIP Trakt sont affichées, un bouton **« 🚪 Quitter les
données ZIP Trakt »** apparaît : il retire les données ZIP et vous ramène au
choix de source (avec le bouton « Charger mes données MDBList » si connecté).
Les deux cartes de choix restent toujours visibles en haut du tableau de bord.

## Avertissement « REMPLACEMENT » corrigé

Le message « ⚠️ REMPLACEMENT » ne s'affiche plus par erreur : il n'apparaît
que lorsque des données ZIP Trakt sont **réellement affichées** et que vous
cliquez pour charger MDBList. Il indique aussi comment retirer d'abord le ZIP.

## Posters fiables (ex. « Chronicle » → mauvais poster corrigé)

Cause : quand le ZIP Trakt ne contenait pas d'identifiant TMDb pour un film,
l'application utilisait l'identifiant Trakt à la place — or chez MDBList,
l'`id` à plat EST l'id TMDb → un AUTRE film recevait le poster.

Corrections :
- l'`id` à plat n'est renseigné que si l'identifiant TMDb est réellement
  connu (jamais l'id Trakt) ;
- l'enrichissement gère en plus les **identifiants IMDb** : un film sans TMDb
  mais avec un IMDb est enrichi via le lot IMDb (genres, poster, durée, note)
  → plus aucun contenu sans métadonnées, et plus de poster erroné.

## « Vu · à revoir » / « Vu · à retirer » vérifié

La comparaison utilise la date d'ajout dans la liste (`listed_at`) et la date
du dernier visionnage. Comportement vérifié sur 4 cas :
- ajouté **après** le visionnage → « Vu · à revoir » ;
- ajouté **avant** le visionnage → « Vu · à retirer » ;
- date d'ajout inconnue → simple « Déjà vu » (neutre, aucune supposition) ;
- dates égales → « Vu · à retirer » (cas prudent).

## Installation

Envoyer ces fichiers à la racine du dépôt :

- `app.py` (modifié)
- `list_audit_engine.py` (modifié)
- `trakt_zip_provider.py` (modifié)
- `ETAPE-31.md` (NOUVEAU)

Aucun fichier à supprimer. Ne pas retoucher les autres fichiers (déjà à jour
en ligne). Aucun secret à modifier.

Commit conseillé :

```text
fix: themed buttons, source switching, reliable posters, watch audit
```
