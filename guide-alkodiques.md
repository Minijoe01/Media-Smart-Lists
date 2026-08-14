# 🧹 Media Smart Lists : l'outil maison qui remet de l'ordre dans vos listes — et bien plus !

> **Article de communauté — Alkodiques** (adapté de l'article « Trakt Smart Lists »,
> remplacée par Media Smart Lists suite aux changements des conditions d'utilisation
> pour les comptes Trakt **free**).

Vous connaissez peut-être cette situation… 😅

Vous avez une watchlist qui déborde, des listes dans tous les sens, et chaque soir la même question existentielle : **« mais QU'EST-CE que je regarde ce soir ?! »**

👉 J'ai décidé de me pencher sur le problème et de proposer une solution, sous la forme d'une application !

Elle s'appelle **Media Smart Lists**, elle est **gratuite** et **open source**.

**🚀 L'app en ligne :** [media-smart-lists.streamlit.app](https://media-smart-lists.streamlit.app)  
**📁 Le code :** [github.com/Minijoe01/Media-Smart-Lists](https://github.com/Minijoe01/Media-Smart-Lists)

---

## ℹ️ Pourquoi « Media » Smart Lists ?

Vous connaissiez peut-être **Trakt Smart Lists**, l'application maison que j'avais conçue pour croiser l'historique Trakt avec les listes. Suite aux **modifications des conditions d'utilisation pour les utilisateurs Trakt free**, cette application n'est pour le moment plus accessible.

**Media Smart Lists** prend le relais, dans le même esprit :

- connexion **MDBList** (temps réel, sans mot de passe) **OU** import de votre **export ZIP Trakt** (local, lecture seule, sans aucune API Trakt) ;
- toutes les fonctionnalités historiques, **plus** de nouvelles ;
- toujours **gratuit, open source, en français**.

---

## 📖 Tout est parti de la fin de TV Time…

Comme beaucoup d'entre vous, j'étais un utilisateur fidèle de **TV Time**. J'y avais stocké à la main **plus de 500 contenus** (films et séries) dans ma liste « à regarder ».

Quand TV Time a tiré sa révérence, il a fallu rebondir. Direction **Trakt**, que je n'utilisais jusque-là que pour le suivi « en cours » de mes visionnages, mon historique, et quelques contenus en watchlist pour du très court terme.

**🔢 Petit point limites (version 2026) :**

- Compte **FREE** Trakt : **5 listes de 250 contenus** chacune ;
- la **watchlist** reste limitée à **250 contenus**.

➡️ Mes 500+ contenus ne rentraient donc **pas** dans la seule watchlist. Il fallait détourner l'utilisation des Listes Trakt et répartir tous mes contenus dans plusieurs listes.

**😱 Le problème : plus mes listes grossissaient, plus c'était le bazar**

Et là, trois gros soucis que Trakt (en version free) ne gère pas pour vous :

**① Mes listes ne sont PAS des watchlists aux yeux de Trakt.**  
Quand je regarde un film ou que je démarre une série, Trakt marque le contenu comme « vu » ou « en cours » dans mon historique… mais il **reste dans ma liste** ! Résultat : doublons permanents entre mes listes et mes visionnages. 🤯

**② Où ai-je rangé ce film déjà ?**  
Plus de 500 contenus sur 5 listes : était-ce dans la liste A ? la B ? les deux ? Bonne chance pour retrouver un doublon à la main.

**③ Les fantômes 👻**  
Vous savez, ces contenus que vous avez lancés **même une milliseconde** (un essai, une fausse manip, votre neveu qui touche à tout…) et qui restent coincés dans « Continuer à regarder ». Sur Trakt c'est agaçant… **et ça vient aussi polluer le widget « En cours » de vos Kodi à la maison !**

**🧹 La solution : Media Smart Lists**

L'idée de l'outil : croiser **votre historique** avec **vos listes**, et faire le ménage **en quelques clics, directement dans l'application** — sans passer par les sites.

**Ce que l'app fait pour vous :**

✔️ **Nettoyage des listes** — repère les contenus déjà vus encore présents dans vos listes. Et malin en plus : il fait la distinction entre un contenu **ajouté avant d'être vu** (→ à retirer, il a fait son temps) et un contenu **ajouté après visionnage** (→ conservé : s'il est là malgré tout, c'est peut-être que vous voulez le **revoir** 😉)

✔️ **Chasse aux doublons** — le même film dans trois listes ? L'app vous montre où, et **retire les copies en un clic** (avec aperçu, sauvegarde de sécurité et confirmation, comme il se doit).

✔️ **Exorcisme des fantômes** 👻 — liste les entrées plantées dans « Continuer à regarder » avec leur vraie progression, pour les supprimer proprement… ou les finir ce soir (il vous dit même combien de temps il reste !).

**🎯 « Que regarder ? » — fini les 40 minutes de scroll**

C'est LA feature qui change les soirées.

À partir de votre historique, l'app construit **votre profil de visionnage** : vos genres fétiches, vos longueurs favorites, vos décennies, vos pays de cinéma, vos studios, vos notes perso… (tout ça est aussi visible dans la partie **📊 Statistiques**, filtrable par période / genre / type comme bon vous semble 😄).

Ensuite, sur n'importe laquelle de vos listes :

- vous posez vos **filtres** (type, genre, note, durée, statut…) ;
- l'app **score chaque contenu sur 100 en vous expliquant pourquoi** (aucune boîte noire : chaque pastille justifie son influence exacte, avec un indice « facilité de lancement » pour les soirs de flemme) ;
- vous n'avez plus qu'à piocher !

**⚡ Encore plus vite : les presets.** « Film rapide », « Soirée cinéma », « Presque finies », « Pépites confidentielles », « Hors zone de confort »… Un clic, et la présélection idéale sort instantanément. Et pour les indécis : une **🎲 roulette** (et sa variante **🧭 découverte** qui sort exprès de votre zone de confort).

**📺 Le suivi en temps réel**

- ▶️ **En cours de lecture** : pour chaque série commencée : le %, le temps déjà vu, le temps restant, et **le prochain épisode à regarder** (« S06E18 »), avec affiches ;
- 👻 **Progression Fantôme** : les reprises mises en pause et leur temps restant ;
- ⏱️ **Votre rythme** : récap du mois, épisodes par semaine, compteurs à vie… et même une **date de fin projetée** de vos séries en cours (si, si 😅) ;
- 🔗 La plupart des contenus ont des **liens directs** (Où regarder, TMDB, MDBList).

**🎁 Et dans la hotte :** un **calendrier des sorties** de vos listes (jusqu'à 1 an et demi), **61 badges** à débloquer (streaks, marathons, rewatch master…), votre **Wrapped annuel** en image partageable, l'export **sauvegarde JSON** (restaurable), un **rapport Excel** multi-onglets… et tout ça reste **rapide** grâce à un **cache malin** : pas de rechargement à rallonge.

**🎯 À qui s'adresse cet outil ?**

**💚 Principalement aux utilisateurs FREE de Trakt** (et à tous ceux qui veulent reprendre le contrôle de leurs listes).

➡️ Si vous avez un compte **gratuit** avec des listes qui débordent : cet outil vous offre **justement** ce que Trakt ne vous montre pas — le ménage de vos listes, vos stats, et la réponse à « qu'est-ce que je regarde ce soir ? ».

**🔒 Côté confiance :** l'app est **open source** (le code est lisible par tous sur GitHub). Vous vous connectez **directement** entre vous et MDBList (OAuth, sans mot de passe), ou vous importez votre ZIP Trakt en **lecture seule** — il n'y a ni compte à créer, ni serveur qui stocke vos données. Et les suppressions/écritures ne se font **que sur vos clics, avec aperçu, sauvegarde et confirmation**.

**🚀 Pour démarrer**

1. Ouvrez 👉 **[media-smart-lists.streamlit.app](https://media-smart-lists.streamlit.app)**
2. Choisissez votre source :
   - **🔗 MDBList** : « Préparer la connexion MDBList » → autorisez avec le code affiché (ou le QR code), puis « Charger mes données MDBList » ;
   - **📦 ZIP Trakt** : « Préparer l'import ZIP Trakt » → suivez le guide (trakt.tv → Settings → Your data → Export → Exporter maintenant, quelques minutes, téléchargez le ZIP) → déposez le fichier.
3. Explorez les 10 pages… et faites le ménage 🧹

**📖 Envie de tout le détail ?** Le README du projet explique chaque fonctionnalité : [github.com/Minijoe01/Media-Smart-Lists](https://github.com/Minijoe01/Media-Smart-Lists)

**✅ En résumé**

✔️ Né de la disparition de TV Time et d'une watchlist de 500+ contenus devenue ingérable  
✔️ Nettoie vos listes (vus, doublons, fantômes) **en quelques clics**  
✔️ Sait enfin répondre à « **qu'est-ce que je regarde ce soir ?** » avec un score 100 % expliqué  
✔️ **Gratuit, open source**, sans compte à créer, pensé pour les comptes **FREE** — MDBList **ou** ZIP Trakt  
✔️ Succède à **Trakt Smart Lists** (devenue inaccessible pour les comptes free) avec les mêmes idées et plus

👉 Après votre première analyse, laissez la magie du cache opérer : vos visites suivantes sont **quasi instantanées**.

🐛 **Un bug, une idée, une envie ?** Les **issues GitHub** du projet sont ouvertes — ou venez en parler directement avec nous, comme d'habitude !

**Bonne analyse… et surtout : bon visionnage ! 🍿**
