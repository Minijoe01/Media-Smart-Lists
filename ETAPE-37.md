# Media Smart Lists — Étape 37 : ruban non dupliqué, guide ZIP, suppression intelligente

## Ruban compte/quota : plus de doublon

Quand on se connectait puis qu'on chargeait ses données MDBList, le ruban
« ✓ CONNECTÉ À MDBLIST · Forfait · Quota · Listes » s'affichait **deux fois** :
une fois dans le connecteur et une fois dans la section « Vos données MDBList ».

Corrigé : le connecteur, si déjà connecté, n'affiche plus que le message
« ✓ CONNECTÉ À MDBLIST » (sans le ruban). Le ruban complet (avec « Actualiser
les compteurs » et « Se déconnecter ») ne vit que dans la section « Vos
données MDBList » du dashboard.

## Guide pas à pas pour l'import ZIP Trakt

Quand on clique sur « Préparer l'import ZIP Trakt », un panneau repliable
« ❓ Comment obtenir mon ZIP Trakt ? (guide pas à pas) » explique :

1. aller sur app.trakt.tv/settings/data?mode=media ;
2. scroller jusqu'à « Export » et cliquer sur « Exporter maintenant » ;
3. attendre quelques minutes (le calcul peut prendre du temps) ;
4. télécharger le fichier ZIP ;
5. revenir ici et déposer le ZIP dans la zone d'import.

## Suppression sécurisée : version user-friendly (cases à cocher + choix intelligents)

Le bloc « 🗑️ Suppression sécurisée » est repensé, beaucoup plus simple :

- des **cases à cocher** listent les contenus de la liste (un à la fois) ;
- quand un contenu est coché, un **aperçu** montre dans combien de conteneurs
  il se trouve (ex. « Titanic est présent dans 3 conteneurs : Watchlist ·
  Gros films · Films d'amour ») ;
- des **actions intelligentes** sont proposées selon les conteneurs :
  « Retirer de « Gros films » », « Retirer de « Watchlist » », ou
  « Retirer de TOUS les conteneurs (cette action en fera plusieurs) » ;
- une **sauvegarde de sécurité** est téléchargeable avant confirmation ;
- la confirmation explicite reste obligatoire, puis l'écriture est faite une
  à une (une action = un contenu, comme dans l'ancienne app Trakt).

C'est exactement le principe que vous décriviez : chaque ligne indique où le
contenu se trouve, et on choisit précisément d'où le retirer.

## Installation

Envoyer ce fichier à la racine du dépôt :

- `app.py` (modifié)
- `ETAPE-37.md` (NOUVEAU)

Aucun fichier à supprimer. Ne pas retoucher les autres fichiers (déjà à jour
en ligne). Aucun secret à modifier.

Commit conseillé :

```text
feat: dedup account ribbon, trakt zip guide, smart multi-list removal
```
