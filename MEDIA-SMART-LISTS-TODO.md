# Media Smart Lists — TODO actif

> Dernière mise à jour : 6 octobre 2026 · Dernière version déployée : V147.
> Dépôt : https://github.com/Minijoe01/Media-Smart-Lists
> Application : https://media-smart-lists.streamlit.app
> Ancienne application (référence) : https://github.com/Minijoe01/Trakt-Smart-Lists
> Transmission IA : voir `AI-HANDOFF.md` (à donner à un agent de remplacement).

---

## Règles permanentes

- [x] Application fournisseur-neutre : `MDBListProvider` et `TraktZipProvider` produisent le même `NormalizedDataset`.
- [x] Aucun accès API Trakt requis.
- [x] OAuth Device Code MDBList : URL, QR, lien direct code pré-rempli, polling, refresh et déconnexion.
- [x] Tokens chiffrés dans un cookie ; aucune vraie clé dans GitHub.
- [x] Ne jamais demander à l'utilisateur ses secrets dans une conversation.
- [x] Quota MDBList pris en compte : cache persistant 1 h, appels groupés, « Actualiser » pour forcer.
- [x] Calculs, filtres, tris, recommandations et audits locaux dès que possible.
- [x] Aucune suppression distante sans aperçu, sauvegarde et confirmation explicite.
- [x] Thème legacy conservé : fond radial Aston Martin, boutons dégradé vert, badges citron.
- [x] Déconnexion : ne vaut que pour la session (au F5 on reste connecté via le cookie OAuth). Le marqueur `?msl_logged_out=1` a été RETIRÉ en V38-V39 (il causait de fausses déconnexions).

---

## Fonctionnalités terminées (V35 — tout est en ligne)

### Sources de données
- [x] Connexion MDBList (OAuth device code) + déconnexion durable.
- [x] Chargement MDBList : watched, ratings, Watchlist, listes, playback, Up Next, dropped, genres.
- [x] Cache persistant 1 h (rechargé au F5, 0 appel API si chaud) + bouton Actualiser.
- [x] Session MDBList expirée → déconnexion propre + message clair.
- [x] Import ZIP Trakt sécurisé (zip-slip, tailles) → même NormalizedDataset, rewatches inclus.
- [x] Enrichissement ZIP automatique (si connecté) : genres, posters, durées, notes, ratings, pays, certification, statut, studios — par lots de 200, avec vérification de cohérence du titre (anti mauvais poster).
- [x] Bascule Trakt ↔ MDBList : bouton « 🚪 Quitter les données ZIP Trakt ».

### Pages (10)
- [x] Tableau de bord : badge de source, widgets rythme (bilan mois, ép./semaine, date de fin projetée), compteurs à vie, digest 7 j, derniers visionnages, métriques temps total/séries/films.
- [x] En cours de lecture : cartes aérées, progression (MDBList) ou nb épisodes vus (ZIP), liens badges (JustWatch/TMDB/MDBList).
- [x] Progression Fantôme : reprises en pause, filtres, temps restant, liens.
- [x] Nettoyage des listes : audit local, doublons, « Vu · à retirer » / « Vu · à revoir », conteneurs exacts, exports.
- [x] Que regarder ? : 21 presets, scores 0-100, signaux avec info-bulles (restaurés à 100 %), une carte sous l'autre.
- [x] Calendrier des sorties : 3 sources fusionnées, horizons longs, diagnostics visibles.
- [x] Statistiques : slicers uniques, vue d'ensemble « non filtrée » mentionnée, heatmap, graphiques, mois triés.
- [x] Rendez-vous annuel (Wrapped) : indicateurs annuels + image PNG partageable.
- [x] Succès : 61 badges avec progression.
- [x] Sauvegarde : JSON restaurable (même sans connexion) + Excel 6 onglets (Résumé, Historique, Mes contenus, Listes, Statistiques, Badges).

### Divers
- [x] Liens contenus : badges discrets « 🔎 Où regarder · TMDB · MDBL » avec info-bulles.
- [x] Widgets du tableau de bord restaurés (V49) : **⭐ Mes coups de cœur**, **🧭 À contre-courant** (thermomètre de sévérité : mes notes vs public), **🔁 Rewatch radar**, **📅 Sorties de la semaine**, **⏳ Plus ancien de la Watchlist** — 0 appel API.
- [x] Widgets V50 : **🚦 Séries en pause longue** (2 ans+ sans épisode, non abandonnées/terminées), **🔥 Records de binge** (jour/mois record, série la plus avalée), **🕰️ Ton créneau préféré** (matin/après-midi/soir/nuit) — 0 appel API.
- [x] Thermomètre de sévérité **affiné à 5 paliers** (V50) : ±0,5 pt = « UN PEU sévère/indulgent », ±1,5 pt = « TRÈS » (l'ancien site étiquetait dès ±0,5 pt).
- [x] Ordre logique des widgets (V50) : action (sorties → plus ancien → pauses) → souvenirs (records → créneau) → goûts (coups de cœur → contre-courant → rewatch).
- [x] Sorties de la semaine : **corrigées pour le ZIP** (date copiée par l'enrichissement) + **dédoublonnées** (sources agrégées) — V50.
- [x] Rewatch radar **dédoublonné pour le ZIP** (chaque visionnage est une ligne) — V50.
- [x] Espacement entre widgets resserré (CSS hr + expandeurs) — V50.
- [x] Historique du tableau de bord : la **saison/épisode** (SxxEyy) est affichée.

### Acteurs favoris MDBList / recherche d'acteur (analyse V49)
- [ ] **Acteurs favoris** : pas d'endpoint public MDBList pour les lister (vérifié
      dans l'OpenAPI officiel). Le `favorite_cast` du calendrier est côté serveur,
      non lisible. À réévaluer si MDBList expose un jour un endpoint.
- [ ] **« Où ai-je vu cet acteur ? »** (façon Cinopsys) : nécessite les crédits
      des médias, absents du dataset sans appels supplémentaires (TMDB credits).
      Non prioritaire ; possible en option avec des appels TMDB dédiés.
- [x] Durées d'épisode corrigées (fini les « 22 ans » de visionnage).
- [x] Export Excel : largeurs auto, onglet « Mes contenus » avec colonne Liste.
- [x] Connexion « sans smartphone » : lien direct avec code pré-rempli.
- [x] Boutons tous au thème (type=primary sans help=).

---

## Priorité immédiate — ÉCRITURES MDBList (demandé par l'utilisateur)

L'utilisateur veut retrouver le pouvoir de l'ancienne app Trakt :
**sélectionner un contenu (ex. doublon) dans une liste et le supprimer
directement**, et plus largement gérer ses données MDBList.

- [x] Supprimer un contenu d'une liste statique (`POST /lists/{id}/items/remove`) — fait (V36, amélioré V37).
- [x] Retirer de la Watchlist (`POST /watchlist/items/remove`) — fait.
- [x] Marquer vu / non-vu (`POST /sync/watched` / `/sync/watched/remove`) — fait (V38).
- [x] Marquer « abandonné » (`POST /sync/dropped`) — fait (V38).
- [ ] Ajouter des notes (`POST /sync/ratings`) — API prête mais UI retirée (V38) : les notes MDBList se gèrent côté MDBList ; à réintégrer si besoin avec des entiers 0-10.
- [x] Ne JAMAIS écrire dans une liste dynamique/IA/flux.
- [x] Chaque opération : aperçu → export de sauvegarde → confirmation explicite → écriture.
- [x] Aucun delete en lot par défaut.
- [x] Journal local nettoyé de tous les secrets.

Règles d'implémentation (leçons des étapes précédentes) :
- ajouter les méthodes d'écriture dans `mdblist_provider.py` (POST) ;
- UI dans « Nettoyage des listes » (sélection + suppression doublon) et dans
  la Watchlist ; garder le thème (boutons type=primary sans help=) ;
- toujours montrer un résumé AVANT écriture et proposer un export JSON de
  sauvegarde ;
- tester avec AppTest + mock.

---

## Migration ZIP Trakt → MDBList

### Nouvelle piste : directement depuis l'application web (sans Python)

L'utilisateur ne peut pas lancer un script Python en local : il faut une
**interface web**. C'est faisable en réutilisant :
- `trakt_zip_provider.py` (parse le ZIP → NormalizedDataset) ;
- les méthodes d'écriture **OAuth** déjà dans `mdblist_provider.py`
  (`set_watched`, `set_rating`, `set_dropped`, `remove_*`, et à ajouter :
  `add_watchlist_items`, `create_list`, `add_list_items`) ;
- le flux sécurisé : aperçu des quantités → export de sauvegarde →
  confirmation explicite → écriture par lots → vérification GET.

Page proposée : « 📦 Migration ZIP Trakt → MDBList » (assistant en étapes).

- [x] Assistant web « Import ZIP Trakt → MDBList » (page dédiée au menu) :
      upload ZIP → aperçu (quantités + sans correspondance) → choix des
      sections → sauvegarde JSON → rapport Excel d'aperçu → confirmation →
      écriture par lots → rapport Excel final. Fait en V45.
- [x] Historique migré avec les **vraies dates** (`watched_at` par film/saison/
      épisode) ; rewatches comptés mais MDBList ne garde que la dernière date.
- [x] Contenus sans correspondance listés + onglet Excel dédié.
- [x] Mode **simulation (dry-run)** intégré (aucun POST).
- [x] Méthodes d'écriture ajoutées : `add_watchlist_items`, `create_list`,
      `add_list_items`, `raw_post` (+ `set_watched` avec dates).
- [x] Ne jamais écrire dans une liste dynamique/IA/flux (uniquement listes statiques).
- [ ] Tester la migration réelle sur un vrai compte MDBList (l'utilisateur a
      déjà migré : il faudra un compte de test ou un volontaire).

### Outil CLI pour les initiés (intégré au dépôt — pas de nouveau dépôt)

Décision (V48) : le script CLI reste **dans Media Smart Lists**, dossier
`scripts/` (pas de dépôt séparé).

- [x] Script déplacé dans `scripts/migrate_trakt_zip_to_mdblist.py`.
- [x] `scripts/README-migration-cli.md` (documentation complète : usage, options, sécurité, limites).
- [x] `scripts/start_windows.bat` (lanceur Windows).
- [x] bibliothèque standard uniquement ; dry-run par défaut ; aucune suppression ; clé masquée ; protections ZIP ; préflight ; confirmation `IMPORTER`.
- [ ] (Optionnel, plus tard) Release ZIP + SHA-256 si un jour un dépôt séparé est souhaité.

---

## Documentation et qualité

- [x] README du dépôt réécrit — complet, wordmark, fonctionnalités, sources, sécurité, installation, migration.
- [x] Changelog synthétique créé (CHANGELOG.md).
- [x] Social card régénérée (style Trakt, textes Media Smart Lists).
- [x] Guide communauté Alkodiques (docs/guide-alkodiques.md) + section migration.
- [x] CI GitHub Actions (compilation + scan de secrets) + tests unitaires.
- [x] Licence MIT (LICENSE).
- [x] Nettoyage du dépôt (GitHub Desktop) : les obsolètes sont supprimés ; il ne reste que l'essentiel.
- [x] SECURITY.md + politique de confidentialité (docs/privacy.md).
- [x] Tests unitaires versionnés dans le dépôt (tests/test_core.py, **13 tests** depuis V50) — exécutés par la CI.
- [x] Maquette du futur look animé (V50) : docs/maquette-animations.html + .png — « comet », fondu d'entrée, survol lumineux, en vert/citron. **À appliquer dans une version ultérieure** (les fonctionnalités passent d'abord).

### À faire PAR L'UTILISATEUR (rappels)
- [ ] **Captures d'écran à jour** : remplacer le CONTENU de docs/Dashboard.png,
      series.png, Doublons.png, quoi_regarder.png, statistiques.png par des
      captures prises sur une version récente (SANS renommer les fichiers).
      → toujours dans la todo : l'utilisateur ne les a PAS encore modifiées
      (17/08/2026).
- [ ] **Valider la démo du skin** (docs/demo-skin-dashboard.html) AVANT de
      déployer la V52 — puis donner son avis (garder / ajuster / revenir V51).

---

## 🎨 Futur thème « vivant » — PROGRESSION (V52-V57 : rubans ✅ · bandeaux ✅ · valeurs blanches ✅ · cartes premium ✅ · Que regarder ? boosté ✅)

L'utilisateur a validé le principe (« si tu te sens capable d'appliquer le
nouveau skin au site, vas-y, mais fais gaffe à pas tout péter »). Un backup
de l'état V51 existe : `BACKUP-Media-Smart-Lists-V51-avant-skin.zip`
(hors dépôt, dans le workspace). **V53 = uniformisation de tous les onglets**
(le user veut « de la modernité » et « uniformiser tout l'outil »).

### Fait en V52-V57
- [x] **Rubans déroulants** avec icône en tuile + titre + méta + chevron
      (rythme, derniers visionnages + les 8 widgets restaurés).
- [x] **Comet biseauté** sur la barre du haut, en vert `#00A392` + citron
      `#CEDC00` (préférence utilisateur), menu ⋮ intact.
- [x] **Fondu en cascade** (50 ms) + **surbrillance au survol**.
- [x] **Grain** subtil + **swoosh** sous les titres de page (tous les onglets).
- [x] Barre de répartition colorée du créneau + mini-cartes records (3 col.).
- [x] Expandeurs natifs des autres pages habillés « ruban » (léger).
- [x] **Bandeau de métriques moderne** (cartes k/v/d avec icône) : helper
      `_metric_cards()` dans app.py, utilisé sur **TOUTES les pages**
      (dashboard vue d'ensemble + ruban compte, En cours, Fantômes,
      Nettoyage, Calendrier ×2, Statistiques, Sauvegarde, Wrapped ×2,
      Migration). Les anciens `st.metric` sont remplacés partout.
- [x] Démo mise à jour : docs/demo-skin-dashboard.html inclut le bandeau.
- [x] **V54 — valeurs des cartes en BLANC** (fini le lime kitsch partout) :
      `.msl-mcard .v`, `.msl-subcard .v`, `.msl-creneau .v` → var(--am-text).
      Le citron reste un accent (comet, barre du créneau, badges, survol) —
      identité Aston Martin conservée.
- [x] **V54 — créneau préféré lisible** : étiquettes grandes (`.lb` 1.05rem),
      info-bulle retirée, horaires affichés sous chaque étiquette (`.pl`),
      % en grand et blanc.
- [x] **V55 — mobile** : `padding-top: 3.6rem` + `margin-top` sur le
      brand-title (le wordmark respire sous le bandeau).
- [x] **V55 — cartes contenus** : hover léger sur `.media-list-card`
      (soulèvement + lueur) + **tuile fallback** `.msl-poster-fallback`
      (helper `_poster_html`) quand un poster manque — appliqué à En cours,
      Fantômes, Calendrier, Que regarder ?.
- [x] **V55 — Progression Fantôme** : posters (ou tuile fallback) + liens
      TMDB/MDBList ; bloc « ⚡ Tu peux finir ça ce soir » SUPPRIMÉ
      (redondant avec les filtres) ; import `finishable_tonight` retiré.
- [x] **V55 — choix de source clarifié** (mobile) : callout « 👋 BIENVENUE »,
      badges 🔵/🟢, descriptions guidées, rappel « une seule source ».
- [x] **V55 — maquette variante** `docs/preview-bandeau-jaune.html`
      (comet/swoosh jaune citron) — à montrer au user, le vert reste en place.
- [x] **V56 — cartes contenus premium** (4 pages : Que regarder ?, En cours,
      Fantômes, Calendrier) : en-tête uniforme avec **badge de type**
      (`_type_chip`) + **note publique** (`_public_note_html`) + **%** en
      gros (En cours) ; **posters liserés** (bordure verte + ombre) ; titres
      épurés (plus de « Film — » en doublon) ; tuiles fallback conservées.
      Helpers : `_type_chip`, `_public_note`, `_public_note_html`.
- [x] **V56 — maquette vert Aston Martin** `docs/preview-bandeau-vert.html`
      (comet/swoosh/survol en vert officiel) — référence du thème.
- [x] **V56 — démo** `docs/demo-skin-dashboard.html` : section « Cartes
      contenus » avec chips + tuiles.
- [x] **V57 — preview comète test** `docs/preview-comet-test.html` :
      couleurs #042E2B + #00A392 (simple test — l'app garde vert+citron).
- [x] **V57 — Up Next** : badge « 📺 Série » retiré (séries évidentes) ;
      étiquettes Film/Série conservées sur les points de reprise.
- [x] **V57 — Que regarder ? boosté** :
      - 7 nouveaux presets (28) : Film marathon 2h30+, Séries courtes ≤30min,
        Séries 100+ ép., Polars & thrillers, Science-fiction, Romance,
        Documentaires ;
      - 6 tris inversés : Plus long d'abord, Notes basses, Moins populaires,
        Ajouté le plus ancien, Anciens d'abord, Plus exigeant ;
      - filtre « Durée minimum » (≥1h → ≥3h) ;
      - genres MULTIPLES ET/OU (multiselect + recherche intégrée).
- [x] **V57 — test unitaire** `TestRecommendationPresets` (14 tests OK).
- [x] **V111 — nettoyage des presets** (validation utilisateur) : les
      presets qui ne dupliquaient qu'un genre ou un style sont supprimés
      (Envie de rire, Envie de frissons, Adrénaline, Polars & thrillers,
      Science-fiction, Romance, Documentaires, Soirée en famille) —
      25 presets restants, uniquement des COMBINAISONS ; « Cinéma du
      monde » reste (pays ≠ USA + note, pas un doublon). Preset déménagé
      de « Tri & affichage » vers « Sélection de contenu » (sous les
      styles — un preset filtre, il ne trie pas) ; icône 🏷️ sur Genres,
      💡 sur le preset ; signets anciens assainis (preset disparu ignoré
      proprement, le reste du signet s'applique).
- [x] **V112 — icône devant chaque genre + 5 filtres** : `GENRE_EMOJI`
      (41 genres) affiché via `format_func` (valeur intacte → signets et
      filtres inchangés) sur les 4 sélecteurs de genres (Que regarder ?
      inclusion/exclusion, Progression Fantôme, Statistiques) ; icônes
      📂 Source · 📽️ Type · 👥 Acteurs · 🎬 Réalisateur · 🏢 Studios.
      Enquête « presets encore visibles » : GitHub était déjà à jour
      (25 presets vérifiés sur main) — observation faite avant la fin du
      Reboot ; remède Reboot + Clear cache + Ctrl+F5.
- [x] **V113 — peplum + mockumentaire élargi + DOCUMENTATION** : style
      « Aventure - 🛡️ Peplum » (mot-clé TMDB peplum=187305, vérifié :
      Troie/Hercule/Astérix le portent) ; « Parodie / spoof » élargi à
      parody+spoof (Naked Gun vérifié : parody 9755) ; « Mockumentaire »
      élargi à 6 mots-clés (mockumentary, pseudo-documentary 276164 =
      Blair Witch/Cloverfield/Paranormal Activity, pseudo documentary,
      fake/false/faux documentary) → 91 styles. README.md réécrit
      (mode d'emploi « Que regarder ? » : 3 familles de critères +
      différence, scoring chouchous/sagas détaillé, hors-listes,
      signets) ; guide-alkodiques.md aligné (ton communauté).
- [x] **V114 — corrections d'audit utilisateur (styles + scoring)** :
      Peplum = peplum + « sword and sandal » (Gladiator II porte le terme
      ANGLAIS, pas « peplum ») ; Parodie = parody + spoof + « satirical »
      (OSS 117 porte satirical, ni parody ni spoof) ; Mockumentaire
      REVENU au mot-clé unique « mockumentary » (les variantes
      pseudo/fake/faux documentary = found footage horreur — Blair Witch,
      PA — pas des mockumentaires ; The Office, The Paper, Cunk on Earth,
      Death to 2020 portent TOUS « mockumentary », vérifié) ; NOUVEAU
      style « Comédie - 🌶️ Ado épicée » (teen comedy + sex comedy +
      teenage sexuality, les 3 sur la fiche d'American Pie) → 92 styles.
      Scoring : malus « 👎 Tes ratages ici » PROPORTIONNEL (≥ 2 notes
      ≤ 3/10 ET ≥ 25 % des notés du genre — un grand fan de comédie avec
      3 navets sur 200 n'est plus pénalisé) ; nouveau profil
      « genre_rating_counts ». README + guide alignés (92 styles, 🌶️,
      barème ratages). 19/19 tests (4 nouveaux).
- [x] **V115 — films homonymes (Wrapped) + V14 non déployée + règle docs** :
      constat GitHub : la V114 n'a JAMAIS été uploadée (aucun marqueur sur
      main) → V115 regroupe tout. Bug signalé : le Rendez-vous annuel
      fusionnait les films homonymes (« Mortal Kombat · 2 visionnages » =
      1995 + 2024) et sous-comptait les films (titre unique) → tops et
      compteurs par couple (titre, année), année affichée seulement si
      ambiguïté ; idem séries. NOUVELLE RÈGLE : toute modif future du
      README/guide part du fichier COURANT du GitHub utilisateur (il
      édite lui-même — nouvelles captures déjà en place) ; workspace
      synchronisé ; la V113 postée sur les forums reste valable (deltas
      20/20 tests.
- [x] **V116 — ZIP sans MDBList : enrichissement TMDB pour tous** (retour
      d'un utilisateur du forum : menus vides + message trompeur sur la
      clé TMDB) : l'import ZIP lance désormais l'enrichissement TMDB en
      arrière-plan (clé de cache = hash du ZIP, réimport instantané) ;
      `_apply_tmdb_payload` complète pays/score/ratings/statut si absents
      (jamais d'écrasement) ; message profil reformulé quand la clé est
      là. Diagnostic : export Trakt = titres/ids/dates seulement, et le
      thread TMDB n'était lancé que dans le chemin MDBList. Pas un
      problème Linux/macOS/clavier. Réponses fournies au propriétaire :
      fichier guide à poster (V114), accroche About FR/EN + topics,
      réponse forum prête à coller (dont hébergement local : reverse
      proxy nginx + WebSockets, Node.js inutile).
- [x] **V117 — posters ZIP, barre de progression TMDB, En cours vs
      Fantôme, film à 0 %** (4 signalements utilisateur) :
      `_apply_tmdb_payload` remplit le poster si absent (les ZIP
      n'avaient aucune affiche dans les listes) ; canal `progress`
      {done,total,error} dans _ENRICH_STATE → vraie barre
      st.progress auto-rafraîchie sur « Que regarder ? » (2,5 s) et le
      tableau de bord (4 s + rerun), PLAFOND DE 100 s SUPPRIMÉ (la page
      s'affichait à moitié enrichie → scores faux) et erreur du thread
      affichée (mort silencieuse avant) ; bloc « 🔴 Lecture en cours
      maintenant » DÉMÉNAGÉ de Fantôme vers « ▶️ En cours de lecture »
      (fantôme = reprises en pause, per la logique utilisateur) avec
      actualisation auto à l'arrivée (cache > 5 min, 1 appel) ;
      film à 0 % : garde anti-fraction (0<p≤1 → ×100) + estimation
      depuis started_at quand le scrobbler ne rapporte pas la
      progression (Kodi sans interval). 23/23 tests
      (TestNowPlayingProgress). Dossier video-textes/ : 3 blocs-notes
      + présentateur HTML plein écran pour la vidéo de démonstration.
- [x] **V119 — 6 correctifs (retours utilisateur + testeur externe + CI)** :
      UNE seule barre de progression (mention discrète au milieu, barre
      auto-actualisée en fin de page) ; séries Up Next ZIP : total
      d'épisodes + poster + % complétés par post-passe d'enrichissement
      (0 appel réseau) ; roulette vs hors-listes : modes exclusifs
      (chaque clic purge les résultats de l'autre mode) ; signets
      inter-comptes : `_sanitize_bookmark_filters` valide contre les
      options réelles + bannière « ignoré car absent de tes données »
      (Streamlit ignorait silencieusement — testé) ; libellé « Listes
      personnelles » fournisseur-aware ; CI réparé : tests/test_core.py
      du repo obsolète depuis V111 (cause de l'exit 1) + ci.yml
      checkout@v5/setup-python@v6 (Node 24). 23/23 tests.
- [x] **V120 — CI réparé pour de bon + 5 retours du testeur externe** :
      CI : le test_core.py V119 avait été déposé à la RACINE du repo au
      lieu de tests/ (vérifié GitHub : racine = 23 tests, tests/ = ancien
      14) — procédure A/B fournie. Roulette : pool vide → la carte du
      tirage précédent restait « collée » → pop + callout explicite +
      badge de mode sur « Le hasard a choisi ». Calendrier ZIP :
      `_apply_tmdb_payload` remplit release_date/first_air_date (testé
      de bout en bout via build_local_calendar_events). Graphe
      évolution : axisPointer shadow→line (bande grise figée = bug
      iframe ECharts). « Note moyenne » : description « aucune note
      perso dans la sélection » quand vide. % >100 : comptage des
      épisodes DISTINCTS (saison+numéro) dans _build_upnext_from_watched
      (rewatches exclus — 10 ≠ 12 vérifié) + clamp 100 dans le
      post-passe. 23/23 tests.
- [x] **V121 — notes Trakt (vrai bug), calendrier local, fragments** :
      CAUSE des notes vides trouvée : l'export Trakt répartit les notes par
      type+pagination (ratings-movies-1.json, ratings-seasons-1.json…) et le
      parseur n'attendait que ratings-\d+ → toutes ignorées. Motifs élargis +
      notes de saison attribuées à la série (réimport nécessaire). Roulette
      découverte : pool vide diagnostiqué (genre à affinité ≥ 30 = zone de
      confort → message dédié). Calendrier : _render_calendar_body mutualisé,
      vue LOCALE immédiate (0 appel, dates TMDB) sans clic sur « Charger ».
      Scintillement « vue fantôme » : boucles sleep+st.rerun remplacées par
      @st.fragment (QR 2,5 s + dashboard 4 s, deux branches) — seule la barre
      se rafraîchit, un seul rerun complet à la fin. 23/23 tests.
- [x] **V122 — calendrier V121 cassé par la refactor** (rapport
      utilisateur : cartes + légende puis plus rien, même après le clic) :
      le bloc filtres+affichage (101 lignes) s'était retrouvé imbriqué dans
      le `with st.expander(diag)` — avec un diag vide (ZIP sans MDBList),
      tout était sauté. Mon test V121 passait car j'avais fourni un diag
      rempli. Désindenté ; vérifié sur les 3 chemins (locale immédiate,
      cache sans diag, cache avec diag). 23/23 tests.

### Reste à faire (idées en attente)
- [ ] Wordmark avec logo-tuile dans le header natif Streamlit (optionnel,
      délicat — à faire prudemment).
- [ ] Avis utilisateur : preview comète test #042E2B+#00A392 (décider si on
      garde vert+citron ou on change) + maquette jaune vs verte.
- [ ] **Wordmark avec logo-tuile** dans le header natif Streamlit (optionnel,
      délicat — à faire prudemment).
- [ ] Avis utilisateur sur la V53 → ajustements éventuels (couleurs,
      espacements, animations).

### Rappels techniques
- CSS injecté dans `app.py` (bloc <style>) ; boutons Streamlit 1.60 :
  `type="primary"` SANS `help=` ; ne pas toucher aux couleurs officielles
  (#00A392, #00524B, #CEDC00).
- Les rubans du dashboard sont des `<details>` HTML (interactivité native du
  navigateur) — helpers `_ruban` + `_*_body` + `_metric_cards`.
- **Référence visuelle** : `docs/preview-look.html` (fourni par l'utilisateur,
  enregistré en V51) ; patterns CSS aussi issus de son site sport-auto et de
  son `worker (3).js` (analysé, PAS ajouté au dépôt — fichier privé avec ses
  icônes).
- [ ] **Partager l'article Alkodiques** sur le portail
      (lesalkodiques.com) — pas encore publié.
- [ ] (Optionnel) Supprimer docs/audit-fichiers-github.xlsx une fois lu.

---

## Kodi (optionnel, plus tard)

- [ ] Tests du MDBList Scrobbler avec journal DEBUG ciblé.
- [ ] Vérifier les versions réellement distribuées par les dépôts Kodi.
- [ ] Identifier un seul auteur principal de scrobble par lecture pour éviter les doublons.

---

## Définition de la prochaine version stable (V36+)

- [ ] Écritures MDBList derrière aperçu + sauvegarde + confirmation (priorité 1).
- [ ] README et docs à jour.
- [ ] Tests reproductibles dans GitHub Actions.
- [ ] Aucun secret dans le dépôt ou les exports.

---

## À faire — décisions actées (V89, 25 août 2026)

### Bouton « ➕ Ajouter une découverte » — RÉALISÉ (V99-V100)
- [x] Popover au-dessus des sections hors-listes (parfaites + presque) :
      choix du contenu → « 📌 Ma Watchlist » OU « 🗂️ une de mes listes
      statiques » → ajout (une écriture, réversible). Uniquement hors-listes
      et connecté MDBList. Thème Aston Martin appliqué au bouton/panneau
      (V100). Décision assumée : pas de bouton DANS la carte HTML (les
      widgets Streamlit ne s'y insèrent pas ; le popover offre le même flux
      sans casser le GSM — leçon V87/V88).

### Mobile / PWA — en place depuis la V89
- [x] Manifest + icônes + plein écran : fonctionnel (validé utilisateur).
- [x] Icône/nom du raccourci : CLOS sans solution (le manifest injecté par
      Streamlit Cloud gagne ; cosmétique uniquement — décision utilisateur).
- [ ] (Optionnel) service worker pour un lancement hors-ligne plus rapide.

### Ascenseur intelligent — v2 (V100)
- [x] Changement de page → haut de page ; retour sur une page visitée →
      position restaurée (sessionStorage). v2 : détection du VRAI conteneur
      qui défile + double canal d'injection (st.iframe + composant HTML).
- [ ] À faire valider sur PC + GSM par l'utilisateur (v1 sans effet ?).

### Documentation
- [ ] README à remettre à jour (styles & ambiances, mots-clés TMDB,
      enrichissement en arrière-plan, ajout aux listes, pagination des
      propositions, « Mes contenus notés »…).
- [ ] guide-alkodiques.md (tuto non publié) : à aligner sur la V100.
- [ ] Captures d'écran GitHub OBSOLÈTES (signalé par l'utilisateur) :
      à refaire — Tableau de bord, Que regarder ? (avec le guide + styles),
      Statistiques (compteurs + Mes contenus notés), Fantôme (suppression),
      hors-listes (parfaites/presque + popover ➕).

### Idées UI en réserve
- [ ] Raccourcis de filtres « mémorisables » (signets de recherche) —
      demandé un jour puis repoussé par l'utilisateur (« on fera plus tard »).
- [ ] Légende d'une ligne « qu'est-ce qu'une progression fantôme ».
- [ ] Compression du grand bloc CSS dans un fichier statique.
- [x] **V124 — Habillage cinéma (inspiration FlickTrove, demande
      utilisateur)** : backdrop stocké dans _apply_tmdb_payload (0 appel —
      champ déjà présent) ; _fetch_tmdb_logo lazy (1 appel au 1er clic 🎬,
      cache 30 j, fr > en > null) ; fiche cinéma @st.dialog(width=large) :
      bannière backdrop w780 + dégradé + clear logo bas-gauche (ou titre),
      affiche, chips, score expliqué, casting, liens ; cartes : classe
      cinema-backdrop + voile rgba(3,29,25) .97→.66 gauche→droite (deviné,
      pas dominant) + bouton 🎬 (clé cin_{key}{_hl} anti-collision).
      Rollback = re-upload app.py V122. 23/23 tests.


---

## V139 (4 octobre 2026) — ajouté par l'agent

### Décisions utilisateur PRISES (04/10/2026 — appliquées en V140)
- [x] **Couleurs : TOUT-ACCENT** choisi (texte des pastilles + synopsis + casting
      dans la couleur du film, accent éclairci pour la lisibilité).
- [x] **Barres : Option B** (vague sur le vu + reste plat façon Spotify), animée —
      appliquée à la barre de la fiche (couleur d'accent) et aux tuiles
      « Que regarder ? » (vert/jaune, statique). ⚠️ ROLLBACK FACILE : constante
      `WAVE_BARS = True` en tête de `_wave_bar_html` dans app.py → `False` pour
      revenir aux barres plates d'avant (les deux codes coexistent).
- [ ] À réévaluer après test : si les vagues prennent trop de place à l'écran,
      repasser `WAVE_BARS` à False (demande utilisateur).

### Réflexion ouverte (demande utilisateur 04/10/2026)
- [ ] **Accès à la fiche des contenus VUS récemment (< 1 an)** : un contenu vu il y a
      moins d'un an n'apparaît ni dans « Que regarder ? » (logique — pas envie de le
      revoir tout de suite) ni dans « Hors de mes listes » (réservé aux vus > 1 an).
      Pourtant l'utilisateur veut parfois consulter leur fiche (saisons, heatmap,
      notes d'épisodes…). Pistes à discuter :
      - filtre « Vus récemment » (toggle) sur « Que regarder ? » ;
      - section « Vus récemment » sur le Tableau de bord (affiches cliquables → fiche) ;
      - accès depuis Statistiques → « Mes contenus notés » (déjà listés) ;
      - depuis « En cours de lecture » une fois terminé (historique récent).
- [ ] Bouton « ➕ Ajouter à une liste » depuis les sections Similaires/Saga de la fiche
      (le popover d'ajout existe déjà pour les découvertes — à brancher si simple).

### Fait en V139
- [x] Fiche acteur intégrée RETIRÉE (fiabilité) → retour aux liens TMDB sur les cercles.
- [x] Heatmap épisodes : contraste fort (luminance étalée 5.5→9.2 + gamma), halo jaune
      sur les épisodes ≥ 8.5 (lisibilité daltonien), info-bulle SxE · note décimale ·
      titre (CSS + title natif).
- [x] Affiches de saison = liens vers la saison TMDB.
- [x] « 💛 Ta note » dans la fiche (depuis la section notes du dataset).
- [x] Sections « La saga » (volets + badges ✅ Vu / 📂 nom de liste / 📌 Watchlist /
      🌐 Hors de tes listes) et « Similaires » (recommandations TMDB croisées).
- [x] Bouton « Voir la fiche » : MAJUSCULES + Manrope 900.

### Fait en V140
- [x] Heatmap épisodes : contraste RELATIF (min-max de la série, comme les vraies
      heatmaps) — quelques dixièmes d'écart se voient maintenant ; curseur normal
      (le « ? » était le curseur d'aide, pas un texte).
- [x] Bouton « VOIR LA FICHE » : style .mc-type (petit, très gras, majuscules espacées).
- [x] Cartes Similaires/Saga : titres limités à 2 lignes, badges alignés en bas.
- [x] Statistiques → « Détail des visionnages » : lignes CLIQUABLES → fiche du contenu.
- [x] « Que regarder ? » : case « 👁️ Inclure les vus récemment (moins d'un an) » →
      ils remontent dans « Déjà vu mais ça correspond » (fiches consultables).

### Fait en V141
- [x] Tuiles : retour barre plate (la vague ne vit que dans la fiche, 30px).
- [x] Heatmap ÉCHELLE HYBRIDE : <5/10 = sombre fixe ; ≥5/10 = relatif (plancher 5)
      → lisibles les séries serrées (Mr. Robot) ET écartées (Robot Chicken).
- [x] Bouton tuile : .68rem / poids 900.
- [x] Toggle « vus récemment » : vrai interrupteur (st.toggle).
- [x] Similaires/Saga : cartes cliquables → fiche TMDB.
- [x] Liens de la fiche sans soulignement (+ halo au survol).
- [x] Score/fiction mis en valeur à droite de la vague (gros chiffre Manrope).
- [x] Pastille « Hors de tes listes » : bleu identique aux tuiles.
- [x] Pastille d'état dans la fiche : ✅ Vu le dd/mm/aaaa / 📂 liste / 📌 Watchlist / 🌐 hors.
- [x] Boutons « VOIR LA FICHE » sur En cours de lecture, Progression Fantôme, Calendrier.
- [x] « Mes contenus notés » (Statistiques) : lignes cliquables → fiche.
- [x] Bannière en w1280 (fini l'étirement).
- [x] (V142) Tableaux « Historique des ajouts » et « audit des listes » rendus
      CLIQUABLES → fiche (ids remontés : `item` pour l'audit, `ids` ajoutés aux
      lignes d'ajouts dans list_audit_engine.py).

### Fait en V142
- [x] Vague fiche : 34px, amplitude doublée (12px), trait FIXE 4.6px (plus épais ni
      plus fin — juste la vague plus ample).
- [x] Heatmap : échelle ABSOLUE 5→10 (le relatif rendait le moins bon épisode
      d'une bonne série — Lizzie Borden 7.7 — très foncé). 7.7 ≈ mi-hauteur.
- [x] Bouton tuile : copie EXACTE du style .mc-type, couleur gris-vert incluse
      (les retouches de taille seules étaient imperceptibles).
- [x] Pastille « ✅ Vu le … » : plus de troncature dans les chips.
- [x] Affiches de saison : animation au survol (soulèvement, comme Similaires/Saga).
- [x] Migration Trakt → MDBList : les 4 options binaires sont de vrais toggles.

### Fait en V143
- [x] Vague fiche : 38px, amplitude 16.8px (22% de la hauteur), trait fixe 4.6px.
- [x] Heatmap : plancher ABSOLU 5.5→10 (décision utilisateur).
- [x] Friction : libellée « ⚡ Friction 18 » + info-bulle native.
- [x] MODE PROGRESSION : fiche ouverte depuis En cours/Fantôme → la barre montre
      le % DÉJÀ VU (comme la tuile d'origine) + « visionné » ; les fiches sans
      score NI progression (historique) n'affichent plus de barre du tout.
- [x] Repli par TITRE+ANNÉE : les fiches/cases fantômes sans ids TMDB
      (ex. Incredibles 2) retrouvent poster/bannière depuis le dataset enrichi.
- [x] Bannière UHD : qualité « original » de TMDB.
- [x] Pastille d'état déplacée dans la BANNIÈRE (bas droite, à côté du type).
- [x] DÉCISION PRISE (05/10) : tuiles colorées par le poster → REFUSÉES
      (« trop arc-en-ciel », l'utilisateur préfère son vert/jaune). Ne pas proposer.

### Fait en V145
- [x] Vague fiche : RETOUR à l'amplitude V142 (18%, 34px) — à 22% les courbes
      devenaient anguleuses (retour utilisateur).
- [x] Friction : police légèrement plus grande (.68rem) + padding accru.
- [x] Incredibles 2 : repli par titre NORMALISÉ (articles/ponctuation enlevés,
      « The Incredibles 2 » = « Incredibles 2 ») + contenance stricte ≥ 85%.
- [x] Bannière : retour w1280 (pixel parfait pour ~1250px affichés — l'UHD
      « original » pesait 3-5× plus lourd sans différence visible).
- [x] Pastille d'état bannière : MÊME format que le badge Film/Série, placée
      juste DESSOUS (pile alignée à droite).
- [x] BUG « Horreur + Séries » : TMDB n'a pas de genre TV « Horreur » → le
      bassin « hors de mes listes » retombait sur les genres d'affinité SANS
      contrainte (des drames/crime comme Lioness/MobLand remontaient). Fix :
      résolution du genre en MOT-CLÉ TMDB (« horror ») pour les séries — le
      bassin est cherché avec ce mot-clé ET chaque candidate doit le porter.
      Idem côté contenus de tes listes (groupe élargi au mot-clé).
- [x] Keep-alive V144 : vraie visite navigateur + clic de réveil + échec
      bruyant (validé par l'utilisateur : run vert, ~1 min).

### Fait en V146
- [x] BUG « Horreur + Séries » hors-listes (0 résultat) : les mots-clés n'étaient
      extraits QUE si `keyword_resolved` était rempli → item_kw vide → toutes les
      séries rejetées. Fix : extraire si `keyword_resolved OR tv_only_kw`.
- [x] Friction : pastille non tronquée (max-width none) + police .68rem.
- [x] BOUTON « VOIR LA FICHE » — le VRAI bug enfin trouvé : le <p> INTERNE du
      bouton Streamlit porte SA PROPRE typo qui écrasait nos styles → le <p> est
      maintenant ciblé aussi. (C'est pour ça que les changements semblaient
      invisibles depuis des versions !)
- [x] Tableaux cliquables : DÉCOCHER une ligne ré-arme le clic (on peut rouvrir
      la même fiche sans devoir en choisir une autre).
- [x] FICHE ACTEUR DE RETOUR — dans Statistiques, par BOUTON NATIF « 👤 Fiche »
      sous chaque carte acteur/réalisateur : dialog SANS AUCUN rechargement
      (contrairement à la V137). Contenus vus + dans tes listes + à découvrir.
- [ ] Idées en discussion : réorganisation de la page Statistiques (onglets ?),
      bloc « anecdote » (TMDB n'en fournit pas — voir ETAPE-146 pour les pistes).

### Fait en V147
- [x] Fiche ACTEUR / Fiche RÉALISATEUR séparées (directors = crew « Director » de TMDB),
      boutons différenciés (👤 / 🎬), libellés « avec cet acteur / ce réalisateur ».
- [x] Fiche personne : contenus vus ET en listes SPLITÉS Films / Séries, badge
      📂 nom de la liste (ou 📌 Watchlist) sur chaque contenu, chaque contenu =
      LIEN TMDB cliquable (comme la fiche film), compteur « N déjà vu(s) avec toi ».
- [x] Cartes personnes : bouton FUSIONNÉ à la carte (look tuile, écart 0px mesuré,
      même hauteur qu'avant — 24px).
- [x] Compteur Pedro Pascal (9 vs 12) : l'enrichissement n'enregistrait que les
      10 premiers acteurs génériqués → cap porté à 20. ⚠️ Clear cache + rechargement
      des données nécessaire pour recalculer les compteurs (données en mémoire).
- [x] Bouton « VOIR LA FICHE » : hauteur compacte (24px) AVEC la typo .mc-type
      (le <p> avait un padding/min-height parasite — nettoyé).
- [x] Friction : alignement vertical/droite vérifié (Δ 0px entre score et pastille).
- [ ] Limitation Streamlit 1.60 (testée) : la sélection d'un st.dataframe est en
      LECTURE SEULE (« Widget state is read-only ») → impossible de décocher
      programmatiquement une ligne après fermeture de fiche. Le flux reste :
      décocher → recocher la même ligne (V146).
### Pistes en discussion
- [ ] Onglets Statistiques (avec animation de transition) + unification des filtres.
- [ ] « Pop »-like : suggestions IA par humeur — POSSIBLE avec une clé Google AI
      Studio (gratuite, aistudio.google.com) posée dans les SECRETS Streamlit
      (jamais dans le code). L'IA classerait TES contenus scorés localement.
- [ ] Anecdotes : aucune source gratuite fiable (Trakt = ses propres utilisateurs) ;
      possible seulement via IA générative (clé ci-dessus) — à discuter.
