# ÉTAPE 61 — Genres en français + Filtres (durée) + Presets triés + fraîcheur date-based

**Version : V61** · 4 fichiers : `app.py`, `normalized_model.py`, `recommendation_engine.py`, **`genre_translations.py` (nouveau)**

## A. 🇫🇷 Genres traduits en français PARTOUT
TMDB et MDBList livrent les genres en anglais (« Comedy », « Science Fiction »…). Désormais ils sont en **français partout** : dashboard, statistiques, Que regarder ? (filtres ET menu déroulant de la Watchlist), cartes, profil de goûts.

- **Nouveau module `genre_translations.py`** : table de traduction officielle TMDB-FR + fonction `translate_genre` (idempotente : un genre déjà en français reste en français).
- **Point d'entrée unique** : la traduction est appliquée dans `normalize_provider_dataset` → couvre **MDBList + TMDB + ZIP Trakt** d'un seul endroit, en descendant dans les médias imbriqués (épisodes → série, reprises…).
- **Menu déroulant des genres** : seul le libellé affiché est traduit ; le **slug est préservé** (il est envoyé tel quel à l'API MDBList pour filtrer — aucune casse).
- **Presets par genre** : `preset_matches` reconnaît maintenant les genres FR **et** EN (sécurité), donc « Envie de rire » (Comédie), « Science-fiction », « Frissons » (Horreur)… continuent de fonctionner.

## B. 🔍 Filtres « Que regarder ? » : durée réunie
« **Temps max** » et « **Durée minimum** » forment une paire complémentaire (un « entre » de durée) : ils sont désormais **côte à côte, en premier**. Viennent ensuite Recherche, Note minimum, Statut.

## C. 🎚️ Presets : tri logique
Le menu « Preset rapide » est réorganisé par groupes cohérents :
1. **Durée & effort** (⚡ Rapide, 🎬 Marathon, 🚪 Zéro effort)
2. **Séries** (📺 Binge, ♾️ Interminables, 🌙 Épisodes courts, ▶️ Continuer, 🎯 Presque finies)
3. **Humeurs & genres** (😄😱💥🕵️🚀❤️🎞️)
4. **Qualité** (🍿🧠💎🔥🗳️✨)
5. **Ancienneté** (🆕⏳🏆)
6. **Découverte** (👨‍👩‍👧🌍🧭)

→ Les 2 presets par durée sont **ensemble**, les filtres série sont **ensemble**, etc.

## D. 📅 V61 — fraîcheur « date-based » des données MDBList
Ton idée « mon cache va de telle date à telle date » : maintenant le tableau de bord affiche **« Données MDBList (extrait du cache) : [date] · il y a X j »** et précise que **le cache est valide 7 jours → un F5 ou un changement de page ne consomme AUCUN appel MDBList**. L'app « sait » que tes données sont fraîches et ne recharge pas tant que le cache tient ; tu forces la recharge via « Actualiser ». (Le mécanisme existait via le TTL ; il est maintenant **visible et expliqué**.)

## Tests
- `py_compile` (4 fichiers) ✅
- 14 tests unitaires ✅
- AppTest : démarrage, 0 exception ✅
- Test focalisé traduction : chaînes ET dicts, `episode.show`, remplissage watchlist, slug API intact, presets FR ✅

## Fichiers
- `genre_translations.py` (nouveau)
- `normalized_model.py` (traduction au point d'entrée unique)
- `recommendation_engine.py` (ordre des presets + correspondance FR)
- `app.py` (filtres durée + fraîcheur date-based)
