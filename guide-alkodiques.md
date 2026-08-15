# 🧹 Media Smart Lists : la suite de mon petit outil maison, maintenant pour MDBList (et votre ZIP Trakt) !

Salut à tous ! 👋

Vous vous souvenez peut-être de mon article sur **Trakt Smart Lists**, mon petit
outil maison pour remettre de l'ordre dans les listes ? Eh bien, il a un
successeur ! 🎉

## ⏸️ D'abord, une petite nouvelle sur Trakt Smart Lists

Pour ceux qui suivaient, **Trakt Smart Lists est pour le moment en pause** 🕓.

Sans rentrer dans les détails, Trakt a durci ses conditions pour les comptes
gratuits, et la seule façon de la réactiver serait de passer sur un compte
**Trakt VIP** (auquel cas seuls les VIP pourraient l'utiliser). C'est une
décision que je ne prends pas à la légère… donc pour l'instant, l'app reste en
stand-by.

➡️ Mais bonne nouvelle : je n'ai pas chômé ! J'ai créé **Media Smart Lists**,
dans le même esprit, avec le même amour du détail — mais cette fois basée sur
**MDBList** (connexion directe) et sur votre **export ZIP Trakt** (en local,
sans aucune API Trakt).

## 🚀 Alors, c'est quoi Media Smart Lists ?

**Media Smart Lists**, c'est une application web **gratuite**, **open source**,
**en français**, qui croise votre historique avec vos listes pour vous éviter
le grand bazar. Concrètement :

- **Fini les doublons !** 🧹 Le même film dans trois listes ? L'app vous montre
  exactement où, et vous pouvez le retirer **d'une liste précise ou de partout**
  en un clic — avec une sauvegarde de sécurité et une confirmation avant chaque
  écriture (parce que je vous respecte, moi 😄).

- **Le ménage intelligent** : elle repère les contenus **déjà vus encore
  présents** dans vos listes, avec la distinction maligne :
  * ajouté **avant** d'être vu → à retirer (il a fait son temps) ;
  * ajouté **après** visionnage → conservé (s'il est là malgré tout, c'est
    peut-être que vous voulez le **revoir** 😉).
  Et elle exorcise aussi les **fantômes 👻** — ces entrées plantées dans
  « Continuer à regarder » qui polluent même le widget « En cours » de vos
  Kodi à la maison !

- **« Qu'est-ce que je regarde ce soir ? »** 🎯 — fini les 40 minutes de scroll !
  L'app construit **votre profil de visionnage** (genres fétiches, durées
  préférées, décennies, pays, studios…), puis **score chaque contenu sur 100
  en vous expliquant pourquoi** (aucune boîte noire : chaque pastille justifie
  son influence exacte). Et pour les indécis : des **presets** (« Film rapide »,
  « Soirée cinéma », « Presque finies », « Pépites confidentielles »…) et une
  **🎲 roulette** !

- **Le suivi de vos séries** 📺 : progression, temps restant, prochain épisode,
  votre **rythme** (épisodes/semaine, bilan du mois) et même une **date de fin
  projetée** de vos séries en cours. Si, si 😅

- **Et dans la hotte** 🎁 : un **calendrier des sorties** de vos contenus
  (jusqu'à 1 an et demi !), des **statistiques** détaillées (heatmap,
  graphiques, ADN cinéphile, marathons…), **61 badges** à débloquer, votre
  **Wrapped annuel** en image partageable, une **sauvegarde JSON** restaurable
  et un **rapport Excel** multi-onglets.

**🚀 L'app en ligne :** [media-smart-lists.streamlit.app](https://media-smart-lists.streamlit.app)  
**📁 Le code :** [github.com/Minijoe01/Media-Smart-Lists](https://github.com/Minijoe01/Media-Smart-Lists)

## 🔗 Deux façons de l'utiliser

### 1. La connexion directe MDBList (recommandée) ⭐

1. Cliquez sur **« Préparer la connexion MDBList »** ;
2. autorisez avec le **code affiché** (ou scannez le **QR code** avec votre
   téléphone) ;
3. cliquez sur **« Charger mes données MDBList »**… et c'est parti !

Un **cache d'une heure** évite de recharger et de consommer votre quota à
chaque visite. Pratique, non ?

### 2. Votre ZIP Trakt (local, lecture seule) 📦

Vous avez encore un compte Trakt, ou un vieil export qui traîne ? Pas de souci,
Trakt reste utilisable **via un fichier ZIP**, sans aucune API.

**Comment obtenir ce ZIP ?** C'est simple :

1. Allez sur [app.trakt.tv/settings/data?mode=media](https://app.trakt.tv/settings/data?mode=media) (connectez-vous) ;
2. scrollez jusqu'à la section **« Export »** ;
3. cliquez sur **« Exporter maintenant »** — comptez **quelques minutes** ;
4. téléchargez le fichier `export-trakt-*.zip` ;
5. dans Media Smart Lists : **« Préparer l'import ZIP Trakt »** → déposez le
   ZIP → **« Importer et charger mes données »**. Et voilà ! 🎉

> 🔒 L'import est **100 % local et en lecture seule** : rien n'est modifié sur
> Trakt, le ZIP n'est pas conservé. Et si vous êtes connecté à MDBList, l'app
> peut **enrichir** vos données ZIP avec les métadonnées MDBList (genres,
> posters, durées, notes).

## 🔒 Côté confiance

- **Open source** : le code est lisible par tous sur GitHub ;
- connexion **OAuth directe** avec MDBList (jamais de mot de passe) ;
- les écritures (suppressions, vu/non-vu, abandon) ne se font **que sur vos
  clics, avec aperçu, sauvegarde de sécurité et confirmation** ;
- aucun serveur ne stocke vos données.

**Envie du détail complet ?** Le [README du projet](https://github.com/Minijoe01/Media-Smart-Lists) documente chaque fonctionnalité. Et pour le contexte (et l'histoire de TV Time 😉), l'[article d'origine sur Trakt Smart Lists](https://lesalkodiques.com/portail/space/kodi/post/trakt-smart-lists-l-outil-maison-qui) reste disponible.

Bref : c'est le même esprit que Trakt Smart Lists, en mieux et prêt pour
MDBList. 🚀

**Bonne analyse… et surtout : bon visionnage ! 🍿**
