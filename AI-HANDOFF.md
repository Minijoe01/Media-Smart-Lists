# Media Smart Lists — dossier de reprise pour une autre IA

> À transmettre avec `MEDIA-SMART-LISTS-TODO.md` si la conversation Arena
> arrive à sa limite. Copie-colle l'URL de cette conversation à l'agent de
> remplacement, ou donne-lui ce fichier.
> **Dernière mise à jour : 14 août 2026 · version déployée : V38.**
>
> ⚠️ **V38/V39** : la « déconnexion durable » a été RETIRÉE (elle causait des
> fausses déconnexions). Comportement actuel : on reste connecté au F5 ; la
> déconnexion ne vaut que pour la session en cours. Voir `mdblist_oauth.py`.
> Écritures disponibles : suppression sécurisée (listes/Watchlist), vu/non-vu,
> abandonnée. La note a été retirée de l'UI (les notes MDBList se gèrent côté
> MDBList). Docs publiées : README, CHANGELOG, social card, guide Alkodiques, CI.

## Mission

Continuer **Media Smart Lists**, clone fournisseur-neutre de l'ancienne
application **Trakt Smart Lists**, sans repartir de zéro et sans réinventer
l'interface.

Règles impératives :

- **Toujours communiquer en français**, avancer une étape à la fois ;
- livrer à chaque étape un **ZIP minimal** (uniquement les fichiers
  modifiés/ajoutés) + un fichier `INSTALLATION-V{XX}.txt` expliquant quoi
  remplacer sur GitHub, + `ETAPE-{XX}.md` (changelog) ;
- l'utilisateur **n'est pas développeur** : il extrait le zip et l'envoie sur
  GitHub via « Add file → Upload files », puis Reboot + Clear cache sur
  Streamlit ;
- **jamais de secret** : `.streamlit/secrets.toml` ne va pas sur GitHub ;
- le thème Aston Martin doit être respecté partout (boutons dégradé vert,
  badges citron, fond radial) ;
- quand un point est incertain, demander à l'utilisateur plutôt que deviner.

## Liens

```text
Dépôt actuel : https://github.com/Minijoe01/Media-Smart-Lists
App actuelle : https://media-smart-lists.streamlit.app
Ancien dépôt  : https://github.com/Minijoe01/Trakt-Smart-Lists
Ancienne app  : https://trakt-smart-lists.streamlit.app
```

## Date et localisation de référence

```text
13 août 2026
Europe/Paris — Dunkerque, France
```

## Architecture actuelle (fonctionnelle)

```text
MDBListProvider ──┐
                  ├── NormalizedDataset ── UI commune (10 pages)
TraktZipProvider ─┘
```

Principaux fichiers :

```text
app.py                   → toute l'UI + logigramme dashboard + enrichissement ZIP
mdblist_oauth.py         → OAuth device code, cookies, déconnexion durable (?msl_logged_out=1)
mdblist_provider.py      → appels API MDBList (lecture) + media_info_batch tmdb/imdb
trakt_zip_provider.py    → import ZIP Trakt sécurisé → NormalizedDataset
normalized_model.py      → build_sources, build_progress (durées d'épisode normalisées)
recommendation_engine.py → scores, signaux, presets (21 presets)
stats_engine.py          → statistiques détaillées (heatmap, graphiques ECharts)
achievements_engine.py   → 61 badges Succès
wrapped_engine.py        → Rendez-vous annuel + image PNG 1080×1350
dashboard_engine.py      → widgets rythme, compteurs à vie, projection de fin
excel_export.py          → rapport Excel multi-onglets (6 onglets)
list_audit_engine.py     → audit des listes (doublons, vu·à retirer / vu·à revoir)
calendar_engine.py       → calendrier (officiel + secours + enrichi)
history_engine.py        → historique normalisé (durées d'épisode corrigées)
legacy_trakt_app.py      → ancienne app (archivée, à ne pas utiliser)
scripts/migrate_trakt_zip_to_mdblist.py → script de migration CLI (voir scripts/README-migration-cli.md)
```

## État de l'application (13 août 2026)

**Tout est fonctionnel et déployé (V35)** :

- **Tableau de bord** : badge de source (🔵 MDBList / 🟢 Trakt / ⚠️ aucune),
  carte de choix (Connexion MDBList / Import ZIP Trakt), boutons au thème,
  ruban compte/quota toujours visible, widgets rythme (bilan du mois,
  ép./semaine, date de fin projetée), compteurs à vie, digest 7 jours,
  derniers visionnages, métriques temps total/séries/films ;
- **Connexion MDBList** : OAuth device code, QR, lien direct avec code
  pré-rempli, cache persistant 1 h (rechargé au F5), **déconnexion durable
  via `?msl_logged_out=1` dans l'URL** (testé : F5 → reste déconnecté) ;
- **Import ZIP Trakt** : sécurisé (zip-slip, tailles), produit le même
  NormalizedDataset, rewatches inclus, upnext/playback reconstruits,
  **enrichissement automatique** si connecté (genres, posters, durées, notes,
  ratings, country, certification, status, studios — par lots de 200) avec
  **vérification de cohérence du titre** (anti mauvais poster) ; bouton
  « 🚪 Quitter les données ZIP Trakt » pour basculer ;
- **10 pages** : Tableau de bord, En cours de lecture (cartes aérées + liens
  badges), Progression Fantôme, Nettoyage des listes, Que regarder ?,
  Calendrier des sorties, Statistiques, Rendez-vous annuel (Wrapped + image
  PNG), Succès (61 badges), Sauvegarde (JSON restaurable + Excel 6 onglets) ;
- **Statistiques** : slicers uniques (Période/Type/Genre) appliqués partout,
  vue d'ensemble « non filtrée » mentionnée, heatmap, graphiques ECharts
  (rendu maison via st.iframe + CDN, pas de streamlit-echarts qui est cassé
  avec Streamlit 1.60), mois triés chronologiquement ;
- **Que regarder ?** : 21 presets, scores 0-100, signaux avec info-bulles
  (⭐ note, 👥 public, 🌍 pays, 🆕 récent, ⏱️ durée, 💎 pépite, 📥 ajout,
  🚪 zéro effort, 🏢 studio fétiche, 🎭 visage familier, 👨‍👩‍👧 famille,
  🏆 classique…), une carte sous l'autre ;
- **Calendrier** : 3 sources fusionnées (officiel MDBList + données locales +
  appels groupés tmdb/imdb), horizons longs (jusqu'à 1 an et demi), panneau
  « 🔍 Pourquoi ce calendrier… » avec diagnostics.

## Points sensibles / leçons apprises

1. **Boutons Streamlit 1.60** : les boutons secondaires et ceux avec `help=`
   (info-bulle) ont une structure DOM différente que le CSS du thème
   n'atteint pas. Solution fiable : `type="primary"` SANS `help=` (mettre
   l'explication en `st.caption` au-dessus).
2. **streamlit-echarts est incompatible** avec Streamlit 1.60 (erreur de
   composant v2). Les graphiques utilisent `st.iframe` + CDN ECharts.
3. **Cookies** : `cookies.remove()` n'est pas fiable (selon navigateur) ;
   `cookies.set()` l'est. Pour la déconnexion durable, **st.query_params
   dans l'URL** est la méthode la plus fiable (l'URL survit au F5).
4. **Durées d'épisode** : MDBList renvoie parfois la durée CUMULÉE d'une
   série → normaliser (1-300 min = épisode ; sinon /nb épisodes ou /60 pour
   des secondes). Toujours via `_episode_runtime_local` / `_episode_runtime`.
5. **Enrichissement ZIP** : ne PAS mettre l'id Trakt comme `id` à plat
   (chez MDBList, `id` = id TMDb → mauvais poster). Vérifier la cohérence
   titre/fichier avant d'appliquer poster/genres.
6. **Le bouton de chargement MDBList ne doit JAMAIS disparaître** : après
   connexion, le logigramme du dashboard doit toujours afficher
   « 📥 Charger mes données MDBList » (un `return` trop tôt l'avait supprimé
   en V29 — régression grave).
7. **Session expirée** : `load_dataset` renvoie des erreurs « expirée/révoquée
   » sur toutes les sections → détecter et déconnecter proprement au lieu du
   « CHARGEMENT PARTIEL » silencieux.

## Prochaines étapes (voir TODO pour le détail)

1. **Écritures MDBList** (le gros morceau, demandé par l'utilisateur) :
   supprimer un doublon sélectionné d'une liste statique, retirer de la
   Watchlist, marquer vu/non-vu, notes, dropped — toujours avec
   aperçu → export de sauvegarde → confirmation explicite → écriture →
   vérification GET. Jamais de delete en lot.
2. **Dépôt séparé `Minijoe01/Trakt-ZIP-to-MDBList`** : README, SECURITY.md,
   requirements.txt, start_windows.bat, release ZIP avec SHA-256, fixtures.
3. **Docs & qualité** : README à jour, licence, politique de confidentialité,
   SECURITY.md, tests CI (GitHub Actions : compile + tests + scan secrets),
   changelog synthétique.
4. **Kodi** (optionnel, plus tard) : tests MDBList Scrobbler.

## Méthode de travail avec l'utilisateur

1. Lire le retour de l'utilisateur (souvent plusieurs points à la fois) ;
2. investiguer le code, identifier les causes racines ;
3. implémenter + **tester** (AppTest pour les 10 pages, tests unitaires des
   moteurs, scénarios mock) ;
4. créer `ETAPE-{XX}.md` + `INSTALLATION-V{XX}.txt` ;
5. créer le **zip minimal** (uniquement les fichiers modifiés/ajoutés) ;
6. présenter le zip + résumé en français ;
7. après déploiement, l'utilisateur confirme ou donne de nouveaux retours.

## Règles de test (espace de travail Arena)

- `python3 -m pip install -r requirements.txt` est nécessaire à chaque
  session (les packages ne persistent pas) ;
- `streamlit.testing.v1.AppTest` pour tester les 10 pages sans crash ;
- les fonctions pures (moteurs) se testent avec des données factices ;
- les providers se mockent (faux `media_info_batch`, faux `ensure_valid_session`) ;
- `st.session_state.get` n'existe pas en test → utiliser
  `"key" in at.session_state` ou l'indexation directe.
