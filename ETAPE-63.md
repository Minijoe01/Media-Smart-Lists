# ÉTAPE 63 — Durée d'épisode autoritaire TMDB + info-bulle provenance

**Version : V63** · 1 fichier : `app.py`

## A. 🕐 Durée d'épisode : source TMDB autoritaire (le vrai correctif)
Mon calcul « durée cumulée ÷ épisodes » n'était pas fiable (tu avais raison). D'après la **doc TMDB**, la durée fiable d'un épisode est le champ **`episode_run_time`** (durée moyenne d'un épisode, au niveau série) ; pour les films c'est `runtime`. Le champ `runtime` de MDBList est peu fiable pour les séries.

→ `_apply_tmdb_payload` récupère maintenant **`episode_run_time`** (séries) et **`runtime`** (films) depuis TMDB et fixe la durée **autoritaire**. Résultat (vérifié en test) :
- **Kimmy Diore** : 246 → **52 min/ép.** ✅
- **A Knight of the Seven Kingdoms** : 208 → **~60 min/ép.** ✅
- **1883** : 9 → **53 min/ép.** ✅
- Family Guy / South Park déjà corrects : inchangés ✅

Le calcul « ÷ épisodes » reste en **filet de sécurité** pour les rares séries sans `episode_run_time` chez TMDB. La « durée totale pour tout voir » est désormais juste elle aussi (durée/ép. × épisodes).

⚠️ Fais un **Clear cache** au déploiement : les durées sont corrigées au prochain enrichissement TMDB.

## B. 💬 Info-bulle sur la provenance (ta question → oui, utile)
Tu avais repéré « Série » (le type 📺) ET « Séries » (la liste d'origine) qui se ressemblaient. Maintenant la **liste/source** est préfixée **📂** et porte une **info-bulle** : « Provenance : la liste ou la source où se trouve ce contenu ». On ne confond plus 📺 (type) et 📂 (liste).

## Tests
`py_compile` ✅ · 14 tests unitaires ✅ · AppTest (0 exception) ✅ · test focalisé runtime TMDB (série + film + fallback) ✅

## Fichiers
- `app.py` (uniquement `_apply_tmdb_payload` pour le runtime + `_render_recommendation_card` pour la provenance)
