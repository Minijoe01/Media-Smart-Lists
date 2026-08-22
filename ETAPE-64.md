# ÉTAPE 64 — Durée d'épisode ROBUSTE (seuil 100 min) + scoring acteurs/studios gradué

**Version : V64** · 2 fichiers : `app.py`, `recommendation_engine.py`

## A. 🕐 Durée d'épisode : le VRAI correctif (robuste, indépendant de TMDB)
V63 s'appuyait sur `episode_run_time` de TMDB — mais pour tes séries, **l'enrichissement TMDB ne s'était pas appliqué** (elles étaient « déjà enrichies » dans le cache serveur, donc non retraitées ; j'ai vérifié : Adolescence = 4 ép. de ~50-65 min sur TMDB, donc la valeur 3h52 était fausse). Résultat : le correctif V63 n'a pas pris.

**Nouveau filet de sécurité au rendu** : un épisode dépasse **quasiment jamais 100 min**. Toute valeur > 100 min (232, 246, 208…) est cumulée/erronée → **divisée par le nombre d'épisodes**. Toute valeur < 10 min → durée inconnue (masquée). Vérifié sur tes exemples :
- **Adolescence** 232 → /4 = **58 min/ép.** ✅
- **Kimmy Diore** 246 → /6 = **41 min/ép.** ✅
- **A Knight…** 208 → /6 = **35 min/ép.** ✅
- **1883** 9 → **inconnue** (masquée plutôt que fausse) ✅
- Family Guy / South Park (déjà justes) → **inchangés** ✅

Ce filet agit **même si TMDB ne s'applique pas** → ça marchera cette fois sans dépendre d'un enrichissement réussi. `episode_run_time` TMDB reste utilisée en bonus quand elle est dispo (plus précise).

## B. 🎭 Scoring acteurs/studios GRADUÉ (ta remarque était juste)
Avant : un acteur/studio « familier » rapportait un bonus **plat de +4**, qu'il apparaisse dans 2 ou 10 de tes contenus. Désormais **gradué** :
| Titres vus | Bonus | Intitulé acteur |
|---|---|---|
| 2 | +3 | 🎭 Visage familier |
| 3-4 | +5 | 🎭 Visage familier |
| 5-9 | +7 | ⭐ Acteur incontournable |
| 10+ | +9 | ⭐ Acteur incontournable |

→ Un acteur vu dans 5 films **batt** clairement un vu dans 2. Idem pour les studios.

## ⚠️ IMPORTANT — pourquoi V63 n'a pas marché + le bon geste cache
Le cache du dataset (`st.cache_data`, 7 jours) est **côté serveur**, pas dans Chrome. Quand des séries étaient « déjà enrichies » dans ce cache, le retraitement TMDB était sauté. **Le bon geste après chaque nouvelle version** :
1. **Reboot app** (⋮) — vide la mémoire serveur (le plus important).
2. **Clear cache** (⋮) — ceinture+bretelles.
→ **Pas besoin** de vider le cache de Chrome. V64 ne dépend plus de ça (filet au rendu).

## Tests
`py_compile` ✅ · 14 tests unitaires ✅ · AppTest (0 exception) ✅ · test focalisé seuil 100 (tes 3 exemples + 1883 + Family Guy) ✅

## Fichiers
- `app.py` (`_sane_episode_runtime` seuil 100)
- `recommendation_engine.py` (bonus gradué acteurs/studios)
