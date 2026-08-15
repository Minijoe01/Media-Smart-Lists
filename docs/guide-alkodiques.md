# 🧹 Media Smart Lists : la relève de Trakt Smart Lists, pour MDBList (et votre ZIP Trakt)

> **Article de communauté — Alkodiques** — suite de l'article
> [« Trakt Smart Lists : l'outil maison qui remet de l'ordre dans vos listes Trakt ! »](https://lesalkodiques.com/portail/space/kodi/post/trakt-smart-lists-l-outil-maison-qui)
> (voir plus bas pour la situation de l'ancienne app).

## ⚠️ Petite mise au point sur Trakt Smart Lists

Vous l'avez peut-être remarqué : **Trakt Smart Lists est pour le moment en stand-by** 🕓.

Le temps que je prenne une décision définitive, sachez que la seule façon de la
réactiver serait de passer sur un compte **Trakt VIP** — et dans ce cas, seuls
les utilisateurs **VIP** pourraient continuer à l'utiliser. C'est un choix que
je ne fais pas à la légère, d'où la pause.

➡️ **C'est là que Media Smart Lists entre en scène** : elle reprend l'esprit de
Trakt Smart Lists, mais en s'appuyant sur **MDBList** (connexion directe) et
sur votre **export ZIP Trakt** (lecture locale, sans API Trakt).

---

## 🚀 Media Smart Lists, c'est quoi ?

**Media Smart Lists** est une application web **gratuite** et **open source**,
en français, qui croise votre historique avec vos listes pour :

- **éviter de dupliquer des contenus** dans vos listes (le même film dans 3
  listes ? l'app vous montre où, et retire les copies en un clic, avec
  sauvegarde et confirmation) ;
- **faire le ménage** : contenus déjà vus encore présents (avec la distinction
  maligne « ajouté avant d'être vu » → à retirer / « ajouté après » → conservé
  pour un éventuel re-visionnage), doublons, et **fantômes 👻** (les entrées
  plantées dans « Continuer à regarder ») ;
- **répondre à « qu'est-ce que je regarde ce soir ? »** : chaque contenu est
  **scoré sur 100 avec une explication transparente** (chaque pastille justifie
  son influence), avec des **presets** (« Film rapide », « Soirée cinéma »,
  « Presque finies », « Pépites confidentielles »…) et une **roulette** 🎲 ;
- **suivre vos séries en cours** : progression, temps restant, prochain épisode,
  rythme hebdomadaire et même une **date de fin projetée** ;
- **statistiques** façon Trakt Smart Lists (heatmap, graphiques, ADN cinéphile,
  studios, marathons, évolution des goûts) ;
- **calendrier des sorties** de vos contenus (jusqu'à 1 an et demi), **61 badges**
  à débloquer, **Wrapped annuel** en image partageable, **sauvegarde JSON**
  restaurable et **rapport Excel** multi-onglets.

**🚀 L'app en ligne :** [media-smart-lists.streamlit.app](https://media-smart-lists.streamlit.app)  
**📁 Le code :** [github.com/Minijoe01/Media-Smart-Lists](https://github.com/Minijoe01/Media-Smart-Lists)

---

## 🔗 Deux façons de l'utiliser

### 1. Connexion directe MDBList (recommandé)

1. Cliquez sur **« Préparer la connexion MDBList »** ;
2. autorisez avec le **code affiché** (ou le **QR code** depuis votre téléphone) ;
3. cliquez sur **« Charger mes données MDBList »** — c'est parti.

Un **cache d'une heure** évite de recharger et de consommer votre quota à chaque
visite.

### 2. Import de votre ZIP Trakt (local, lecture seule)

Vous avez encore un compte Trakt (ou un ancien export) ? Pas de souci : Trakt
reste utilisable **via un fichier ZIP**, sans aucune API.

**Comment obtenir ce ZIP ?**

1. Rendez-vous sur [app.trakt.tv/settings/data?mode=media](https://app.trakt.tv/settings/data?mode=media) (connectez-vous) ;
2. scrollez jusqu'à la section **« Export »** ;
3. cliquez sur **« Exporter maintenant »** — l'export peut prendre **quelques minutes** ;
4. téléchargez le fichier `export-trakt-*.zip` ;
5. dans Media Smart Lists, cliquez sur **« Préparer l'import ZIP Trakt »**, déposez le ZIP, puis **« Importer et charger mes données »**.

> 🔒 L'import est **100 % local et en lecture seule** : rien n'est modifié sur
> Trakt, le ZIP n'est pas conservé. En option, si vous êtes connecté à MDBList,
> l'app peut **enrichir** vos données ZIP avec les métadonnées MDBList
> (genres, posters, durées, notes).

---

## 🔒 Côté confiance

- **Open source** : le code est lisible par tous sur GitHub ;
- connexion **OAuth directe** avec MDBList (jamais de mot de passe) ;
- les écritures (suppressions, vu/non-vu, abandon) ne se font **que sur vos
  clics, avec aperçu, sauvegarde de sécurité et confirmation** ;
- aucun serveur ne stocke vos données.

**Envie du détail complet ?** Le [README du projet](https://github.com/Minijoe01/Media-Smart-Lists) documente chaque fonctionnalité. Et pour comprendre d'où vient tout ça, l'[article d'origine sur Trakt Smart Lists](https://lesalkodiques.com/portail/space/kodi/post/trakt-smart-lists-l-outil-maison-qui) reste disponible.

**Bonne analyse… et surtout : bon visionnage ! 🍿**
