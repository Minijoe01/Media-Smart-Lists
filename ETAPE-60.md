# ÉTAPE 60 — Revue UX « Que regarder ? » + bouton « Actualiser TMDB »

**Version : V60** · 1 fichier modifié : `app.py`

## A. Audit UX « Que regarder ? » (réalisée en me mettant à la place d'un nouvel utilisateur)

### Problèmes repérés et corrigés

**1. Surcharge visuelle : les 3 menus déroulants étaient TOUS ouverts.**
Un nouvel utilisateur arrivait face à ~15 réglages d'un coup avant même de voir ses recommandations.
→ **« 🔍 Filtres » et « 🔃 Tri & affichage » sont maintenant repliés par défaut.**
« 🗂️ Sélection de contenu » reste ouvert (c'est le périmètre principal). Avantage : on voit **d'abord ses résultats** (tri « ✨ Pour moi » appliqué automatiquement), puis on ouvre un menu pour affiner. Les valeurs par défaut fonctionnent même replié → aucun résultat perdu.

**2. Incohérence des modes ET/OU.**
Le mode des acteurs était *en ligne* (3ᵉ colonne), celui des genres était *tout seul sur une ligne séparée*, et l'ordre des options différiait (ET d'abord pour les genres, OU d'abord pour les acteurs). Perturbant.
→ **Les deux modes sont réunis sur une même ligne**, traités à l'identique : « Genres : correspondance » et « Acteurs : correspondance », avec **« Au moins un (OU) » en premier** (comportement par défaut) partout. Les studios restent en « au moins un » (sans sélecteur, comme avant).

### Ce qui est déjà bien placé (confirmé, inchangé)
- **Tri « Trier par »** : l'ordre est logique et groupé par paires croissant/décroissant — notes (haut/bas), durée (court/long), popularité (haut/bas), ancienneté d'ajout (récent/ancien), année de sortie (récent/ancien), effort (facile/exigeant), puis type (films/séries) et « pas pour moi ». Rien à déplacer.
- **Répartition Sélection / Filtres / Tri** : le modèle mental tient (« je choisis le périmètre » → « j'affine » → « j'ordonne »).

### Réutilisation sur d'autres pages (analyse honnête)
« Que regarder ? » est effectivement le plus gros consommateur de filtres. Les autres pages ont **déjà leurs propres filtres adaptés** à leur contexte (En cours = genre/progression ; Calendrier = type/période ; Nettoyage = signaux). Forcer les mêmes filtres n'aurait pas de sens (ex. « Temps max » sur un calendrier ?). Je n'ai donc **pas dupliqué** les menus à tort-à-travers — mais la structure repliable est désormais cohérente partout.

## B. Bouton « 🎭 Actualiser acteurs & studios (TMDB) »
Ajouté **à côté** de « 🔄 Actualiser les données MDBList » (en bas du tableau de bord). N'apparaît que si une clé TMDB est configurée.
- **Effet** : vide le cache TMDB par contenu (30 j) puis recharge → **tous** tes titres sont ré-interrogés (≈30 s).
- **Usage** : facultatif. La fréquence auto (30 j + nouveautés) suffit en général, mais tu gardes la main pour forcer un refresh quand tu veux des acteurs/studios à jour.
- Légende claire sous les deux boutons expliquant qui fait quoi et la fréquence TMDB.

## Tests
`py_compile` ✅ · 14 tests unitaires ✅ · AppTest (démarrage, 0 exception) ✅

## Fichiers
- `app.py` (uniquement `render_watchlist_page` pour l'UX, et `page_dashboard` pour le bouton TMDB)
