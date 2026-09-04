# 🧹 Media Smart Lists : le grand ménage de vos listes… et le coach « quoi regarder ce soir » !

Salut à tous ! 👋

Vous vous souvenez peut-être de mon article sur **Trakt Smart Lists**, mon petit
outil maison pour remettre de l'ordre dans les listes ? Eh bien, son
successeur **Media Smart Lists** a bien grandi — et il est temps de vous
faire le tour complet du propriétaire. 🎉

**🚀 L'app en ligne :** [media-smart-lists.streamlit.app](https://media-smart-lists.streamlit.app)  
**📁 Le code :** [github.com/Minijoe01/Media-Smart-Lists](https://github.com/Minijoe01/Media-Smart-Lists)

## ⏸️ D'abord, une petite nouvelle sur Trakt Smart Lists

Pour ceux qui suivaient, **Trakt Smart Lists est pour le moment en pause** 🕓.
Trakt a durci ses conditions pour les comptes gratuits, et la seule façon de
la réactiver serait de passer sur un compte **Trakt VIP**. En attendant,
Media Smart Lists reprend le flambeau — basé sur **MDBList** (connexion
directe) et sur votre **export ZIP Trakt** (en local, sans aucune API Trakt).

## 🚀 Alors, c'est quoi Media Smart Lists ?

Une application web **gratuite**, **open source**, **en français**, qui croise
votre historique avec vos listes pour vous éviter le grand bazar :

- **Fini les doublons !** 🧹 Le même film dans trois listes ? L'app vous montre
  exactement où, et vous pouvez le retirer **d'une liste précise ou de
  partout** — avec sauvegarde de sécurité et confirmation avant chaque
  écriture.
- **Le ménage intelligent** : les contenus **déjà vus encore présents** dans
  vos listes, avec la distinction maligne *ajouté avant le visionnage → à
  retirer* / *ajouté après → à garder (vous voulez le revoir)*. Et elle
  exorcise les **fantômes 👻** de « Continuer à regarder » (oui, ceux qui
  polluent le widget « En cours » de vos Kodi !).
- **Le suivi de vos séries** 📺 : progression, temps restant, prochain
  épisode, **rythme** (ép./semaine) et **date de fin projetée**.
- **Les extras** 🎁 : calendrier des sorties (jusqu'à 1 an et demi),
  statistiques détaillées (heatmap, ADN cinéphile, **Mes contenus notés** ⭐),
  61 badges, votre **Wrapped** annuel partageable, sauvegarde JSON + rapport
  Excel.

Mais la page qui a le plus évolué, c'est **« 🎯 Que regarder ? »** — et c'est
ce dont je veux vous parler aujourd'hui.

## 🎯 « Que regarder ? » : le mode d'emploi complet

L'idée : vous remplissez vos critères, l'app filtre **vos listes**, les
classe par **score personnel** (explicable à 100 %), et peut même chercher
**dans tout TMDB** pour vous dénicher des pépites que vous n'avez pas encore.

### Les 3 familles de critères (ne les confondez plus !)

| | 🏷️ **Genres** | 🎭 **Styles & ambiances** | 💡 **Presets** |
|---|---|---|---|
| **C'est quoi ?** | La classification officielle TMDB | **91 styles** = des **mots-clés TMDB** bien plus fins que les genres | **25 combinaisons prêtes à l'emploi** |
| **Exemples** | 💥 Action, 😱 Horreur, ❤️ Romance, 🚀 Science-fiction… | 🧠 Mindfuck, 🩸 Gore, 🏁 Formule 1, 🛡️ Peplum, 📸 Mockumentaire, 🔍 Polar, 🎅 Noël, 🏔️ Montagne… | ⚡ Rapide — film < 1h30 · 📺 Binge express · 🍿 Soirée cinéma · 📚 Suite d'une saga entamée |
| **Quand ?** | « Je veux un film d'horreur » | « Un found footage avec des fantômes » · « un docu sur la F1 » | « Je n'ai qu'une heure et demie ce soir » · « finis-moi une mini-série » |

**En une phrase** : le **genre** classe le contenu, le **style** décrit sa
saveur, le **preset** est un **raccourci** qui combine plusieurs critères
pour une envie du soir. Un preset ne duplique JAMAIS un genre ou un style —
c'est la règle maison depuis le grand nettoyage. 😉

**Exemple vécu** : envie d'horreur ? → 🏷️ genre **Horreur**. Envie d'horreur
filmée caméra à l'épaule ? → + 🎭 style **Found footage**. Une heure et
demie devant vous et pas plus ? → + 💡 preset **Zéro effort ce soir**. Les
trois familles se combinent librement.

> 💡 Astuce : les listes de la page ont une **recherche intégrée** — tapez
> « peplum », « gore » ou « DiCaprio » plutôt que scroller.

### 🏷️ Genres : inclure ET exclure

- Choisissez plusieurs genres avec le mode **« Au moins un (OU) »** ou
  **« Tous (ET) »** ;
- la liste **🚫 Genres à exclure** barre les familles dont vous ne voulez
  pas entendre parler ;
- chaque genre a **son icône** (😂 Comédie, 🤠 Western, 🏅 Sport…) pour
  repérer du regard ;
- et les genres sans équivalent TMDB sont **traduits automatiquement** :
  filtrer **Biographie** trouve aussi les contenus taggés **Histoire**,
  **Sport** part sur le mot-clé TMDB « sports »…

### 👥 Acteurs, 🎬 réalisateurs, 🏢 studios, 🌍 pays

- **👥 Acteurs** : plusieurs possibles, mode **OU** (au moins un) ou **ET**
  (tous) — la liste déroulante ne contient QUE les gens présents dans vos
  contenus ;
- **🎬 Réalisateur** et **🏢 Studios** : même principe ;
- **🌍 Pays d'origine** : à inclure **et** à exclure (envie de cinéma du
  monde ? excluez 🇺🇸 USA).

### 🧠 Le score : vos chouchous sont récompensés

Chaque carte affiche un score /100 **totalement transparent** : survolez une
pastille, elle vous dit son influence exacte. Les pièces maîtresses :

**Vos acteurs / réalisateurs / studios favoris** — détectés
**automatiquement** dans votre historique (croisés au moins 2 fois, et pas
déçus en moyenne) :

| Situation | Pastille | Points |
|---|---|---|
| Acteur croisé 2 fois | 🎭 Visage familier | +3 |
| Acteur croisé 3-4 fois | ⭐ Acteur incontournable | +5 à +7 |
| Acteur croisé 5 fois et + | ⭐ Acteur incontournable | +7 à **+9** |
| Réalisateur vu 5 fois et + | 🎬 Réalisateur de confiance | +5 à +9 |
| Studio bien exploré | 🏢 Studio fétiche | +3 à +9 |

Un seul navet ne « sacque » pas un favori : la moyenne ignore la note la
plus basse. Pas d'effet domini. 😌

**Vos sagas** — le film appartient à une saga que vous avez commencée :

| Votre saga | Pastille | Points |
|---|---|---|
| Commencée (1 film vu) | 🔗 Saga commencée | +3 « pour la finir » |
| Commencée (2 films et +) | 🔗 Saga commencée | +4 |
| Notée ≥ 7/10 par vous | 🔗 Saga adorée | +5 à +6 |
| Notée < 5/10 par vous | 👎 Saga déçue | **−12** — les suites d'une déception sont pénalisées |

Et le reste du barème : affinité avec vos genres (jusqu'à +28, pondérée par
la **récence** de vos goûts), vos **notes personnelles** par genre, la note
de la communauté (bonus au-delà de 5.5, **malus** en dessous), votre durée
idéale calculée sur VOS visionnages, le format court favorisé après 22 h…

### 🎯 Le bouton « Hors de mes listes »

Le plus magique : remplissez vos critères (titre, genres, styles, preset,
acteurs, réalisateur, studio, pays, époque, durée, note…) et cliquez
**« 🎯 Hors de mes listes »**. La recherche part dans un **grand bassin
TMDB** — filmographies complètes de vos acteurs, suites de vos sagas,
recherche par titre, découverte diversifiée — puis chaque résultat est
**scoré par VOTRE profil**. Pas juste les blockbusters populaires : vos
meilleurs scores.

Trois sections de résultats :

- **🎯 Propositions parfaites** : tout respecte ;
- **✨ Pas parfait, mais ça pourrait te plaire** : un seul critère manque,
  indiqué par la pastille 🧩 (ex. le bon réalisateur, mais pas l'acteur
  choisi) ;
- **👀 Déjà vu, mais ça correspond** : des vus de plus d'un an qui collent à
  votre demande — parfait pour une rewatch ou pour faire découvrir.

Et le petit **« ➕ Ajouter une découverte à mes listes »** range le bon
trouveau directement dans votre **Watchlist** ou une de vos **listes
statiques** MDBList, sans quitter l'app. 🤯

### 🎲 Roulettes et 🔖 signets

- **🎲 Roulette — choisir pour moi** tranche parmi vos contenus bien notés ;
  **🧭 Roulette découverte** pousse hors des sentiers battus ;
- **🔖 Signets de recherche** : mémorisez une combinaison de filtres sous un
  nom, rechargez-la en un clic, et copiez un **lien** qui la restaure sur
  n'importe quel appareil — pratique pour retrouver « horreur psy un soir
  d'hiver » sans tout reconfigurer. Vous pouvez même partager **tous vos
  signets d'un seul lien**. 📤

## 🔗 Deux façons d'alimenter l'app

### 1. La connexion directe MDBList (recommandée) ⭐

1. Cliquez sur **« Préparer la connexion MDBList »** ;
2. autorisez avec le **code affiché** (ou scannez le **QR code**) ;
3. cliquez sur **« Charger mes données MDBList »**.

Un **cache d'une heure** évite de consommer votre quota à chaque visite. Et
au premier chargement, vos listes s'affichent **immédiatement** pendant que
l'enrichissement TMDB (acteurs, studios, mots-clés pour les styles…)
travaille **en arrière-plan**.

### 2. Votre ZIP Trakt (local, lecture seule) 📦

1. Sur [app.trakt.tv/settings/data?mode=media](https://app.trakt.tv/settings/data?mode=media),
   section **« Export »** → **« Exporter maintenant »** (quelques minutes) ;
2. téléchargez `export-trakt-*.zip` ;
3. dans l'app : **« Préparer l'import ZIP Trakt »** → déposez le ZIP →
   **« Importer et charger mes données »**.

> 🔒 100 % local et en lecture seule : rien n'est modifié sur Trakt.

Et pour basculer définitivement sur MDBList, la page **« 📦 Migration Trakt
→ MDBList »** transfère historique (avec les vraies dates), notes, Watchlist
et listes — **mode simulation par défaut**, écriture par lots, rapport Excel
final.

## 🔒 Côté confiance

- **Open source** : le code est lisible par tous sur GitHub ;
- connexion **OAuth directe** avec MDBList (jamais de mot de passe) ;
- les écritures ne se font **que sur vos clics**, avec aperçu, sauvegarde de
  sécurité et confirmation ;
- aucun serveur ne stocke vos données.

**Envie du détail complet ?** Le [README du projet](https://github.com/Minijoe01/Media-Smart-Lists)
documente chaque fonctionnalité. Et pour le contexte (et l'histoire de TV
Time 😉), l'[article d'origine sur Trakt Smart Lists](https://lesalkodiques.com/portail/space/kodi/post/trakt-smart-lists-l-outil-maison-qui)
reste disponible.

Bref : listes propres, séries suivies, et **zéro excuse pour scroller 40
minutes** ce soir. 🚀

**Bonne analyse… et surtout : bon visionnage ! 🍿**
