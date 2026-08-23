# ÉTAPE 65 — Réalisateurs 🎬 (filtre + scoring gradué + statistiques)

**Version : V65** · 2 fichiers : `app.py`, `recommendation_engine.py`

## 🎬 Réalisateur partout (comme les acteurs)
- **Capture TMDB** : films → `credits.crew` (job == Director) ; séries → `created_by` (créateurs). Top 5, avec photo TMDB.
- **Filtre « Que regarder ? »** : nouveau sélecteur **Réalisateur** (colonne entre Acteurs et Studios). Filtrage « au moins un » (comme les studios).
- **Scoring gradué** : un réalisateur vu dans plusieurs de tes contenus boost le score, par paliers (2→+3, 3-4→+5, 5-9→+7 « Réalisateur de confiance », 10+→+9). Pastille explicative sur la carte.
- **Statistiques** : nouvelle section « 🎬 Réalisateurs récurrents » (cartes photo + lien TMDB), **filtrable par période/type/genre** comme les acteurs.
- **Profil de goûts** : tes réalisateurs récurrents s'y affichent aussi.
- **Carte « Que regarder ? »** : ligne compacte « 🎬 Nolan » (info-bulle sur GSM).

## Éclaircissements importants (réponses à tes questions)
- **« ▶️ Continuer ce que tu as commencé »** = les **séries TV que tu as commencées** (tu es à mi-chemin), **PAS les sagas films**. Ne change pas.
- **Ton idée saga** (proposer Retour vers le futur 2 si tu as vu le 1) = détection de **franchise** via le champ TMDB `belongs_to_collection`. C'est une **belle idée, différente et faisable**, mais plus costaud (à faire dans une V66 dédiée si tu veux).
- **Âge/PEGI** : je te recommande de **garder juste le preset « Famille »**. Un PEGI précis par âge est peu fiable (les classifications varient par pays et demanderait un appel TMDB supplémentaire par titre) — le ROI est faible.
- **« Dispo où ? »** : abandonné (lien JustWatch déjà présent sur les cartes). ✅

## ⚠️ Déploiement
Dépose `app.py` + `recommendation_engine.py`, puis **`⋮ → Reboot app`** + **`Clear cache`** (le réalisateur est peuplé au prochain enrichissement TMDB ; sans reboot, les anciennes données sans réalisateurs restent).

## Tests
`py_compile` ✅ · 14 tests unitaires ✅ · AppTest (0 exception) ✅ · test focalisé réalisateur (capture TMDB + profil favori + bonus scoring + stats filtrables) ✅

## Fichiers
- `app.py` (`_apply_tmdb_payload`, `_collect_director_stats`, `_render_people_cards`, stats, profil, Que regarder filtre+carte, reset)
- `recommendation_engine.py` (`_directors`, `build_profile`, `score_item`)
