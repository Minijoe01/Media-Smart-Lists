# Media Smart Lists — dossier de reprise pour une autre IA

> À transmettre avec `MEDIA-SMART-LISTS-TODO.md` si la conversation Arena
> arrive à sa limite. Copie-colle l'URL de cette conversation à l'agent de
> remplacement, ou donne-lui ce fichier.
> **Dernière mise à jour : 20 août 2026 · version déployée : V54 · V55 à V57
> prêtes à livrer (les dernières étapes).**
>
> ⚠️ **Contexte clé** : la « déconnexion durable » (`?msl_logged_out=1`) a été
> RETIRÉE en V38/V39 (fausses déconnexions). On reste connecté au F5 ; la
> déconnexion ne vaut que pour la session. Depuis V52, un **skin « vivant »**
> (rubans déroulants, comet biseauté, bandeaux de cartes) est appliqué — voir
> section « Skin / thème ». Un **backup de l'état V51** existe :
> `BACKUP-Media-Smart-Lists-V51-avant-skin.zip` (hors dépôt).

## Mission

Continuer **Media Smart Lists**, clone fournisseur-neutre de l'ancienne
application **Trakt Smart Lists**, sans repartir de zéro et sans réinventer
l'interface.

Règles impératives :

- **Toujours communiquer en français**, avancer une étape à la fois ;
- livrer à chaque étape un **ZIP minimal** (uniquement les fichiers
  modifiés/ajoutés) + un fichier `INSTALLATION-V{XX}.txt` expliquant quoi
  remplacer sur GitHub, + `ETAPE-{XX}.md` ;
- l'utilisateur **n'est pas développeur** : il extrait le zip et l'envoie sur
  GitHub via « Add file → Upload files », puis Reboot + Clear cache sur
  Streamlit ;
- **jamais de secret** : `.streamlit/secrets.toml` ne va pas sur GitHub ;
- **le thème Aston Martin F1 2026 doit être respecté partout** : vert
  `#00A392`, vert foncé `#00524B`, citron `#CEDC00` (le citron est un ACCENT,
  pas un remplissage — les valeurs des cartes sont en blanc depuis V54) ;
- quand un point est incertain, demander à l'utilisateur plutôt que deviner.

## Liens

```text
Dépôt actuel : https://github.com/Minijoe01/Media-Smart-Lists
App actuelle : https://media-smart-lists.streamlit.app
Ancien dépôt  : https://github.com/Minijoe01/Trakt-Smart-Lists
Ancienne app  : https://trakt-smart-lists.streamlit.app
Article Alkodiques : https://lesalkodiques.com/portail/space/kodi/post/trakt-smart-lists-l-outil-maison-qui
```

## Date et localisation de référence

```text
18 août 2026
Europe/Paris — Dunkerque, France
```

## Architecture actuelle (fonctionnelle)

```text
MDBListProvider ──┐
                  ├── NormalizedDataset ── UI commune (11 pages)
TraktZipProvider ─┘
```

Principaux fichiers :

```text
app.py                   → toute l'UI + logigramme + skin (CSS) + helpers rubans
dashboard_engine.py      → compute_dashboard + compute_widgets (8 widgets restaurés)
mdblist_oauth.py         → OAuth device code, cookies, expire_local_session (sans marqueur)
mdblist_provider.py      → appels API MDBList (lecture) + media_info_batch tmdb/imdb + écritures
trakt_zip_provider.py    → import ZIP Trakt sécurisé → NormalizedDataset
normalized_model.py      → build_sources, build_progress (durées d'épisode normalisées)
history_engine.py        → historique normalisé (watched_at, plays, total_minutes, episode_label)
playback_engine.py       → normalize_playback, enrich_playback_posters, filtres fantômes
recommendation_engine.py → scores, signaux, presets (21 presets)
stats_engine.py          → statistiques détaillées (build_frame, heatmap, graphiques ECharts)
achievements_engine.py   → 61 badges Succès
wrapped_engine.py        → Rendez-vous annuel + image PNG 1080×1350
excel_export.py          → rapport Excel multi-onglets
list_audit_engine.py     → audit des listes (doublons, vu·à retirer / vu·à revoir)
calendar_engine.py       → calendrier (officiel + secours + enrichi)
migration_engine.py      → plan/payloads/rapport de la migration ZIP → MDBList
legacy_trakt_app.py      → ancienne app (archivée, à ne pas utiliser)
scripts/migrate_trakt_zip_to_mdblist.py → CLI de migration (voir scripts/README-migration-cli.md)
tests/test_core.py       → 13 tests unitaires (moteurs + widgets)
```

## État de l'application (18 août 2026)

**Déployé : V54.** Le skin « vivant » est en place (voir section dédiée) et
toutes les fonctionnalités historiques restent actives :

- **11 pages** : 🏠 Tableau de bord · ▶️ En cours de lecture · 👻 Progression
  Fantôme · 🧹 Nettoyage des listes · 🎯 Que regarder ? · 📅 Calendrier ·
  📊 Statistiques · 🎉 Rendez-vous annuel (Wrapped) · 🏆 Succès (61 badges) ·
  💾 Sauvegarde · 📦 Migration ZIP → MDBList.
- **Sources** : MDBList (OAuth device code, cache 1 h, rechargement au F5)
  et ZIP Trakt (lecture seule, enrichissement optionnel par lots de 200 avec
  vérification de cohérence du titre).
- **Widgets dashboard (0 appel API)** : ⏱️ rythme (bilan mois, ép./semaine,
  projection fin) · 🕘 derniers visionnages (avec SxxEyy) · 📅 sorties de la
  semaine · ⏳ plus ancien Watchlist · 🚦 pauses longues (≥ 2 ans, exclut
  terminées/abandonnées/vues en entier via Up Next) · 🔥 records de binge ·
  🕰️ créneau préféré (horaires affichés sous chaque étiquette) · ⭐ coups de
  cœur · 🧭 à contre-courant (thermomètre 5 paliers « PLUTÔT ») · 🔁 rewatch
  radar (dédoublonné pour le ZIP).
- **Statistiques** : slicers uniques, heatmap, graphiques ECharts via
  `st.iframe` + CDN (PAS `streamlit-echarts`, cassé avec Streamlit 1.60).
- **Nettoyage** : vu à retirer / à revoir, doublons multi-conteneurs,
  suppression sécurisée (aperçu → sauvegarde → confirmation), marquer
  vu/non-vu/abandonnée.
- **Migration web** : assistant en 4 étapes, simulation par défaut, vraies
  dates (`watched_at`), rapport Excel 7 onglets. CLI dans `scripts/`.
- **Docs** : README façon Trakt, CHANGELOG (V21→V54), SECURITY.md,
  docs/privacy.md, docs/guide-alkodiques.md, docs/social_card.png,
  docs/maquette-animations.html/.png, docs/preview-look.html,
  docs/preview-bandeau-jaune.html, docs/demo-skin-dashboard.html, CI
  (.github/workflows/ci.yml : compileall + scan secrets + tests).

## Skin / thème « vivant » (V52→V54, inspiré de preview-look)

Le user adore `docs/preview-look.html` et veut « de la modernité » +
« uniformiser tout l'outil ». État :

- **Rubans déroulants du dashboard** : `<details class="msl-widget">` avec
  icône en tuile (`.msl-ic`), titre, méta, chevron ▾ (qui pivote). Helpers
  dans app.py : `_ruban(emoji, titre, meta, body, delay)` + `_*_body()` pour
  chaque widget (rythme, derniers, sorties, plus_ancien, pause, records,
  creneau, coups, contre_courant, rewatch).
- **Comet biseauté** sur la barre du haut (`header[data-testid="stHeader"]::before`)
  : `clip-path: polygon(21px 0, 100% 0, calc(100% - 21px) 100%, 0 100%)`,
  bandes diagonales 115°, `animation: msl-comet 8s linear infinite`, couleurs
  **vert `rgba(0,163,146,.95)` + citron `rgba(206,220,0,.25)`** (préférence
  user). Menu ⋮ intact (pseudo-élément, `pointer-events:none`).
- **Fondu en cascade** : `@keyframes msl-fadeUp`, `animation-delay` croissant
  (50 ms rubans / 40 ms cartes). **Surbrillance au survol** : translateY(-2/-3px),
  fond teinté, bordure, ombre lumineuse.
- **Bandeaux de métriques** : helper `_metric_cards([{emoji,k,v,d}])` →
  grille `.msl-metrics` de cartes `.msl-mcard` (icône à droite, k en petites
  capitales, **v en BLANC** (V54), d en sous-titre). Utilisé sur TOUTES les
  pages (dashboard vue d'ensemble + ruban compte, En cours, Fantômes,
  Nettoyage, Calendrier ×2, Statistiques, Sauvegarde, Wrapped ×2, Migration).
- **Créneau préféré** (V54) : étiquettes grandes (`.lb`), horaires affichés
  sous chaque étiquette (`.pl`, ex. « 18 h → 22 h »), % en grand blanc,
  barre colorée 4 segments (vert foncé/vert/citron/menthe). Info-bulle
  retirée.
- **Cartes contenus (V56, premium)** : en-tête uniforme avec **badge de
  type** (`.mc-chip` via `_type_chip`), **note publique** (`.mc-note` via
  `_public_note_html`), **% en gros** (`.mc-pct`, En cours) ; **posters
  liserés** (bordure verte + ombre sur `.media-list-card img`) ; titres
  épurés (Que regarder ? sans « Type — ») ; tuiles fallback
  `.msl-poster-fallback` (`_poster_html`) quand le poster manque.
  Appliqué à : Que regarder ?, En cours de lecture, Progression Fantôme,
  Calendrier.
- **Mobile** (V55) : `padding-top: 3.6rem` + `margin-top` sur le brand-title
  (le wordmark respire sous le bandeau).
- **Maquettes** : `docs/preview-bandeau-jaune.html` (variante jaune, idée)
  et `docs/preview-bandeau-vert.html` (**vert officiel** = référence).
  `docs/demo-skin-dashboard.html` = démo du dashboard + cartes contenus.

## Points sensibles / leçons apprises

1. **Boutons Streamlit 1.60** : `type="primary"` SANS `help=` (le `help=`
   change la structure DOM et casse le CSS du thème) ; l'explication passe
   en `st.caption`.
2. **streamlit-echarts incompatible** avec Streamlit 1.60 → graphiques via
   `st.iframe` + CDN ECharts (`_render_echarts`).
3. **Déconnexion** : la méthode `?msl_logged_out=1` a été RETIRÉE (V38/V39,
   fausses déconnexions). On reste connecté au F5 ; la déconnexion ne vaut
   que pour la session. `mdblist_oauth.py` : `expire_local_session()` (sans
   marqueur) et `disconnect()`.
4. **Durées d'épisode** : MDBList renvoie parfois la durée CUMULÉE d'une
   série → normaliser via `_episode_runtime_local` (normalized_model) /
   `_episode_runtime` (history_engine) : 1-300 min = épisode, sinon
   /nb épisodes ou /60 secondes.
5. **Enrichissement ZIP** : ne PAS mettre l'id Trakt comme `id` à plat
   (chez MDBList, `id` = id TMDb → mauvais poster). Vérifier la cohérence
   titre/fichier (`_titles_coherent`) avant d'appliquer poster/genres.
6. **Le bouton de chargement MDBList ne doit JAMAIS disparaître** : après
   connexion, le logigramme du dashboard doit toujours afficher
   « 📥 Charger mes données MDBList » (régression V29, corrigée).
7. **Session expirée** : détectée seulement si ≥ 4 des 8 sections échouent
   avec erreur auth → `expire_local_session` sans marqueur.
8. **Tests** : `st.session_state.get` n'existe pas en AppTest → utiliser
   `"key" in at.session_state`. Les packages doivent être réinstallés à
   chaque session (`pip install -r requirements.txt`).
9. **Skin** : les rubans du dashboard sont des `<details>` HTML natifs ;
   ne PAS réintroduire `_render_restored_widgets` (remplacé par les helpers).
   Les couleurs officielles sont sacrées ; le citron est un accent (V54).
10. **Backup** : avant un gros changement cosmétique, fournir un backup zip
    complet hors dépôt (ex. `BACKUP-Media-Smart-Lists-V51-avant-skin.zip`)
    + rappeler les 3 façons de revenir en arrière (message à l'IA, revert
    GitHub, zip de backup).

## V55-V57 (prêtes à livrer — à déployer avec le user)

- **Mobile** : espace entre le bandeau du haut et le wordmark (padding-top
  3.6rem + margin-top).
- **Cartes contenus** : hover léger + **tuile fallback poster** partout
  (helper `_poster_html`), y compris **Progression Fantôme** (posters +
  boutons TMDB/MDBList déjà présents, désormais avec fallback élégant).
- **Bloc « ⚡ Tu peux finir ça ce soir » SUPPRIMÉ** de Progression Fantôme
  (redondant avec les filtres en dessous) — import `finishable_tonight`
  retiré.
- **Choix de source** : callout « 👋 BIENVENUE » + descriptions guidées des
  2 cartes + rappel mobile « choisis une seule source » (les données
  affichées suivent toujours la source choisie).
- **Maquette** `docs/preview-bandeau-jaune.html` (idée à montrer, on garde
  le vert).

**V56** : cartes contenus premium (chips type + note publique + % + posters
liserés) sur 4 pages ; maquette verte officielle ; démo mise à jour.

**V57** : preview comète test `docs/preview-comet-test.html` (#042E2B + #00A392) ;
Up Next sans badge « Série » ; Que regarder ? boosté : 7 nouveaux presets (28),
6 tris inversés (dont « Plus long d'abord »), filtre « Durée minimum », genres
multiples ET/OU (multiselect + recherche, mode « Tous (ET) » filtré en local).

## Prochaines étapes (voir TODO pour le détail)

1. Recueillir l'avis du user sur la V55 (et sur la maquette jaune).
2. **Embellir les cartes contenus** (Que regarder ?, En cours de lecture) si
   le user valide — en gardant posters, liens, infos (hover déjà en place,
   éventuels badges/icônes en plus).
3. Wordmark avec logo-tuile dans le header natif Streamlit (optionnel,
   délicat).
4. Rappels user : remplacer les captures `docs/*.png` (Dashboard.png,
   series.png, Doublons.png, quoi_regarder.png, statistiques.png — SANS
   renommer), publier l'article Alkodiques, (optionnel) supprimer
   docs/audit-fichiers-github.xlsx.
5. Idées en attente : notes UI (API `set_rating` prête), page « À propos »,
   « où ai-je vu cet acteur ? » (crédits TMDB, coûteux), acteurs favoris
   MDBList (pas d'endpoint public).

## Méthode de travail avec l'utilisateur

1. Lire le retour de l'utilisateur (souvent plusieurs points à la fois) ;
2. investiguer le code, identifier les causes racines ;
3. implémenter + **tester** (AppTest pour les 11 pages, tests unitaires des
   moteurs, scénarios mock) ;
4. créer `ETAPE-{XX}.md` + `INSTALLATION-V{XX}.txt` ;
5. créer le **zip minimal** (uniquement les fichiers modifiés/ajoutés) ;
6. présenter le zip + résumé en français (et la démo HTML quand le rendu
   change) ;
7. après déploiement, l'utilisateur confirme ou donne de nouveaux retours.

## Règles de test (espace de travail Arena)

- `python3 -m pip install -r requirements.txt` est nécessaire à chaque
  session (les packages ne persistent pas) ;
- `streamlit.testing.v1.AppTest` pour tester les 11 pages sans crash ;
- les fonctions pures (moteurs) se testent avec des données factices
  (`tests/test_core.py`, 13 tests : `python3 -m unittest discover -s tests`) ;
- les providers se mockent (faux `media_info_batch`, faux `ensure_valid_session`) ;
- les datasets de test doivent être **déterministes** (heures fixes pour les
  films — le créneau dépend de l'heure de la journée).
