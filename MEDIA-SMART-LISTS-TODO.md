# Media Smart Lists — TODO actif

> Dernière mise à jour : 21 octobre 2026 · Dernière version déployée : V193.
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
- [x] « Pop »-like : suggestions IA par humeur — FAIT en V149 (page 🍿 POP,
      moteur Gemini + repli local, voir « Fait en V149 »).
- [ ] Anecdotes : aucune source gratuite fiable (Trakt = ses propres utilisateurs) ;
      possible seulement via IA générative (clé ci-dessus) — à discuter.

### Fait en V148
- [x] BUG Supercopter (faux badge Watchlist sur la fiche de Bryan Cranston) :
      `_media_tmdb_id_strict` — les croisements n'utilisent PLUS le repli « id »
      interne (MDBList/Trakt) qui entrait en collision numérique avec de vrais
      ids TMDB. Appliqué aux badges + pastilles d'état (testé 6/6).
- [x] Cartes personnes : LISERÉ JAUNE (harmonisé avec le bouton), plus compactes
      (photo 40px, 5 par ligne).
- [x] « N déjà dans ton historique » (français naturel, retour utilisateur).
- [x] RECHERCHE d'acteur/réalisateur dans Statistiques — même hors de ton top
      (TMDB /search/person, cache 7 j, boutons Fiche).
- [x] Tuiles En cours/Fantôme : écart 1-2px carte-bouton supprimé (marge basse 0).
- [x] Séries abandonnées : bouton « Voir la fiche » ajouté, liseré VERT
      (harmonisé avec la tuile sans jaune — volontaire).
- [x] GUIDE-CLE-IA.txt : création clé Google AI Studio + secrets Streamlit +
      limites (Flash ~1500 req/jour) + alternatives (Groq, OpenRouter).

### Fait en V149 (retours du 07/10)
- [x] COMPTEURS UNIFIÉS — la tuile utilise la MÊME méthode que la fiche
      (fini le « 12 côté fiche vs 9 côté tuile » et le « 0 vu avec Scorsese ») :
      • nouvelle fonction centrale `_person_filmography` (cache 7 j) = filmo
        TMDB en DEUX facettes (acteur = cast, réalisateur = crew Director) ;
      • `_collect_people_stats`/`_collect_director_stats` réécrits : scan local
        par ID TMDB STRICT (plus par nom) → 24 candidats → comptage EXACT
        filmo ∩ ids vus (parallélisé, spinner, 48 appels max puis cache 7 j) ;
      • CAUSE RACINE du « 0 Scorsese » : la condition de ré-enrichissement ne
        contenait pas `directors` → les films enrichis AVANT l'existence de ce
        champ n'étaient jamais ré-examinés. Corrigé par `ENRICH_VERSION = 2`
        (marqueur `_enrich_v` par média ; re-traitement GRATUIT car les
        payloads TMDB sont en cache 30 j).
- [x] FICHE PERSONNE DOUBLE FACETTE : un réalisateur qui joue (Scorsese et ses
      caméos) voit ses DEUX carrières — « EN TANT QUE RÉALISATEUR » puis
      « EN TANT QU'ACTEUR », sections Films/Séries (vus + listes) par facette,
      compteur d'en-tête = UNION dédupliquée des facettes. Séparateur affiché
      seulement si les deux facettes existent.
- [x] ÉCART TUILE-BOUTON 2.61px (En cours/Fantôme/Abandonnées, mesuré au banc
      Chromium) : les boutons SANS help= n'ont pas le wrapper FLEX des tooltips
      Streamlit → bouton compacté 24px aligné sur une line box inline ~26.6px.
      Fix : `div.stButton { display: flex }` ciblé aux boutons fusionnés →
      gap mesuré 0px sur TOUTES les cartes (28/28 vérifications).
- [x] SÉRIES ABANDONNÉES : tuiles COMPACTES (nom seul, 34px mesurés, classe
      `.dropped-compact`) + liseré bouton ramené à 3px = liseré tuile.
- [x] 🍿 POP — NOUVELLE PAGE « une pépite ? » : humeur (8 pills) + type →
      Gemini choisit LA pépite parmi le top 40 de tes listes/Watchlist (scoré
      localement) et justifie en 2-3 phrases sans spoiler. `pop_engine.py`
      séparé ; endpoint NATIF Gemini (compatible clés AQ. ET AIza) ; repli
      LOCAL sans clé (humeur → genres) ; exclusions des tirages de la session ;
      confidentialité : seules fiches techniques (titre/genres/durée/note)
      envoyées — audité au banc (aucune note personnelle dans le prompt).
- [x] Clarté cartes stats : « N déjà vus » (comptage exact identique à la fiche) ;
      résultats de recherche : « Ouvre la fiche pour le détail ».
- [x] 23/23 tests unitaires + non-régression fiche cinéma (vague animée,
      sections, score) vérifiées au banc.

### Fait en V150 (retours du 07/10 soir)
- [x] 🎯 BUG COLLISION FILM/SÉRIE (trouvé par L'UTILISATEUR — félicitations) :
      Days of Thunder (movie/2119) et Supercopter (tv/2119) partagent le
      MÊME id TMDB — or tous les croisements comparaient des ints sans le
      TYPE → faux badge « 📌 Watchlist » sur Supercopter dans la fiche de
      Bryan Cranston. CORRECTION EN PROFONDEUR, partout :
      • `_seen_watchlist_listname_ids` renvoie des clés TYPO-PRÉFIXÉES
        « movie:{id} » / « tv:{id} » ;
      • badges Similaires/Saga (`_sim_card`), fiches personnes (`_bucket`,
        compteur union), comptage exact des tuiles stats, pastille d'état
        de la fiche (`_fiche_status_pill` + paramètre kind), recherche du
        média pour les fiches (`_history_fiche_row` filtre par type),
        post-passe d'enrichissement (clés typées), durées de la page
        « En cours », pool POP — tout est typé.
- [x] POP « · Local » malgré la clé : les modèles Gemini 2.5 « réfléchissent »
      par défaut et le thinking est DÉCOMPTÉ de maxOutputTokens → réponse
      VIDE → bascule locale silencieuse. Fix : thinkingBudget 0 +
      maxOutputTokens 1200. ET l'erreur Gemini reste AFFICHÉE (avant, elle
      était effacée quand le local prenait le relais). NOUVEAU :
      « 🔧 Diagnostic de la clé Gemini » (1 appel lecture seule, 0 quota).
- [x] Pépites déjà tirées : chaque chip devient un LIEN vers la fiche TMDB.
- [x] 🎲 ANECDOTES IA : une anecdote Gemini dans la fiche cinéma (sous le
      synopsis) et la fiche personne (sous la bio) — NOUVELLE à chaque
      ouverture (purge à l'ouverture), re-tirable (« 🎲 Une autre »),
      consigne zéro-spoiler, mention « générée par IA ». Sans clé : rien.
- [x] FIX INFO-BULLES HEATMAP (séries) : les bulles ::after s'affichent
      AU-DESSUS des cellules mais .ep-heatmap a overflow-x:auto — qui
      CLIPPE AUSSI l'axe Y → bulles de la 1re ligne coupées. Fix :
      padding-top 3.2rem (l'espace de la bulle vit DANS la boîte visible).
- [x] RÉGRESSION bouton « Voir la fiche » plus court que la tuile (Que
      regarder ?) : display:flex V149 était appliqué aussi aux boutons
      AVEC info-bulle → le wrapper tooltip se rétractait. Fix : sélecteur
      `div.stButton:has(> button)` (boutons SANS wrapper uniquement).
- [x] README : l'utilisateur préfère le refaire lui-même À LA FIN — plus
      aucun README dans les livraisons (retiré de V150).

### Fait en V151 (retours du 07/10 au soir, 2e vague)
- [x] 🎯 404 « Modèle gemini-2.5-flash indisponible » (POP + anecdotes) :
      gemini-2.5-flash est RÉSERVÉ aux projets qui l'utilisaient déjà (les
      nouveaux projets/projets par défaut reçoivent 404 — vérifié sur les
      forums Google et la doc Firebase, oct. 2026). CORRECTION DÉFINITIVE :
      PLUS AUCUN NOM DE MODÈLE EN DUR — l'app LISTE les modèles disponibles
      POUR TA CLÉ (GET /v1beta/models, 0 quota) et choisit automatiquement
      le meilleur Flash : alias « gemini-flash-latest » en priorité, sinon
      stable avant preview, version la plus haute, flash avant flash-lite
      (cache 6 h par clé, hashée). Message 404 réorienté vers le diagnostic.
      Diagnostic de clé enrichi : modèle retenu + liste des Flash visibles.
      8/8 tests unitaires de résolution (dont le cas réel 2.5→3.6).
- [x] Heatmap : bulle COUPÉE À GAUCHE par le bord de la fiche (retour avec
      capture) : la bulle centrée (min-width 180px) débordait à gauche du
      conteneur scrollable pour les premiers épisodes. Fix ×2 : padding-left
      3.6rem + ancrage spécifique 1re cellule (bulle décalée vers la
      droite, ne peut plus jamais déborder). Mesures : marge 1re cellule
      88.8px, bulle à 39.2px du bord, 5 752 px au survol.
- [x] Heatmap : 2e info-bulle (title natif, celle qui apparaissait quelques
      secondes après) SUPPRIMÉE — demande utilisateur : seule la bulle
      CSS instantanée reste.
- [x] Quota affiché corrigé : ~1 000 requêtes/jour (Flash gratuit 2026),
      et non ~1 500.

### Fait en V152 (retours du 07/10, 3e vague — l'IA au cœur)
- [x] ERREURS 503 / ReadTimeout (retours utilisateur) : RETRY automatique —
      2 tentatives avec 1 s de pause sur HTTP 503 (Google surchargé) et les
      timeouts réseau, pour POP, les anecdotes ET le POP libre.
- [x] 🎲 « L'INFO DES COULISSES » (ex-anecdote, enrichie) : anecdote de
      tournage + ✅ POINTS FORTS / ⚠️ POINTS DE VIGILANCE « côté
      spectateurs » (ex. rythme lent) — des infos introuvables sur TMDB,
      en UN SEUL appel Gemini.
- [x] FLUX REPUSENSÉ (demandes utilisateur) :
      • plus AUCUN chargement auto dans les fiches — la fiche s'ouvre
        instantanément, un BOUTON « ✨ L'info des coulisses » propose l'IA ;
      • PRÉCALCUL en arrière-plan (thread) pendant la lecture de la fiche
        → au clic, affichage quasi instantané dans la plupart des cas ;
      • fiche PERSONNE : les films vus/listes s'affichent AVANT le bouton
        IA (l'anecdote était avant les sections — corrigé) ;
      • « 🎲 Une autre » régénère.
- [x] LOOK du bloc : couleur d'ACCENT de la fiche (bordure gauche), spark
      dégradé façon Gemini (SVG inline), bouton principal en verre dégradé
      bleu-violet-rose + « Une autre » compact — finies les couleurs
      « message d'alerte » (demande utilisateur).
- [x] POP : la fiche film est juste sous la tuile, EXACTEMENT comme
      « Que regarder ? » (bouton fusionné : gap 0, même largeur — mesuré),
      puis la raison en dessous (thème conservé).
- [x] ✍️ POP LIBRE : un champ « décris ton envie en une phrase » (ex.
      « un film d'amour sur un bateau ») → Gemini propose 1 contenu DE tes
      listes + 1 œuvre HORS listes (retrouvée sur TMDB via recherche par
      titre), avec justification. Requiert la clé IA (pas de repli local).
- [x] Heatmap : RÉALIGNÉE à gauche comme à l'origine (padding-left
      retiré — retour utilisateur) tout en gardant les bulles entières :
      ancrage spécifique des 3 premières cellules de chaque rangée
      (1re : part vers la droite ; 2e-3e : retrait contrôlé). Mesures :
      1re cellule à 31,2 px du bord (comme avant), ancres 0 / -25,6 px,
      title natif toujours absent (1 seule bulle, instantanée).
- [x] Banc : 28/28 vérifications (retry 503 prouvé, POP libre complet,
      ordre fiche personne, heatmap) + 23/23 tests + smoke test app réelle.

### Fait en V153 (retours du 08/10 — l'IA dans le décor de la fiche)
- [x] 🎯 QUOTA 429 (« je crois que je n'ai que 20 tokens par jour ») : le
      résolveur choisissait le flash le plus RÉCENT, dont le quota gratuit
      est très bas ; les FLASH-LITE gardent un quota bien plus large.
      NOUVELLE stratégie : flash-lite EN PREMIER + BASCULE AUTOMATIQUE de
      modèle en cas de 429 (jusqu'à 3 modèles essayés) + 503 → 3 tentatives
      (pause 1 s puis 2,5 s). Le diagnostic affiche modèle + secours.
- [x] CHARGEMENT AUTOMATIQUE de l'info des coulisses (retour : « elle doit
      se charger avec la fiche, sans bouton ») : la fonction est appelée
      en FIN de fiche, le précalcul démarre au début du rendu → PREUVE AU
      CHRONO au banc : sections visibles à 1,1 s PENDANT la préparation,
      l'info apparaît à 5,3 s en bas, sans clic. « 🎲 Une autre anecdote »
      conservé, rendu après le bloc (toujours visible).
- [x] 💡 « Le saviez-vous ? » en préfixe de l'anecdote (demande utilisateur).
- [x] COULEURS : retour avec capture — le violet « Gemini » dénaturait la
      fiche. TOUT EST À L'ACCENT DE LA FICHE désormais : bordure gauche et
      titre en couleur d'accent (a2 du film / jaune pour les personnes),
      anecdote en accent clair (a3) comme le synopsis, spark SVG en dégradé
      accent → blanc, fond « glass » légèrement obscurci (backdrop blur
      7 px), pros/cons en vert/jaune DU THÈME. Mesures : bordure
      rgb(255,178,57) = accent du film de test, zéro violet.
- [x] Fiche personne : films vus et listes AVANT le bloc IA (déjà V152,
      re-vérifié) + chargement auto (plus de bouton).
- [x] PAGE POP : panneau « glass » façon Tableau de bord autour des choix
      (fond vert translucide + blur + liseré 4 px + coins 16 px, mesuré),
      le callout « CHOISIS TON HUMEUR » devient une caption douce.
- [x] (fix interne) _render_pop_result réinsérée après une suppression
      accidentelle lors du remplacement de bloc — non-régression vérifiée.
- [x] Banc : 22/22 vérifications (chrono du streaming, couleurs mesurées,
      429→bascule, 503→retry, panneau) + 23/23 tests + smoke test.

### Fait en V154 (retours du 08/10 — double provider + REFONTE STATISTIQUES)
- [x] 🎯 ERREUR 400 (retour utilisateur avec capture) : cause = thinkingBudget
      refusé par les Gemini 3.x. DOUBLE CEINTURE : thinkingConfig ADAPTÉ au
      modèle (aucun sur les 3.x) + si un 400 survient quand même → RETRY
      immédiat en corps « safe » (sans thinkingConfig, budget relevé).
      Preuve au banc : 400 forcé au 1er appel → l'info des coulisses
      s'affiche quand même.
- [x] ⚡ PROVIDER GROQ (réponse à « faut-il remplacer Gemini ? ») : si une
      clé GROQ_API_KEY est posée (console.groq.com, gratuit, ~1 000 req/j,
      très rapide), l'app l'utilise EN PRIORITÉ — Gemini reste en SECOURS
      (et réciproquement : secours croisé). Modèle Groq résolu dynamiquement
      (gpt-oss-20b d'après les quotas 2026), JSON strict, retries 503/429.
      Diagnostic étendu aux deux providers. 19/19 au banc avec Groq actif.
- [x] ⭐ REFONTE STATISTIQUES (fini le fourre-tout — demande utilisateur :
      « rassembler mes stats de vu avec les notes, les stats acteur et
      réal, de façon intuitive ») :
      • NAVIGATION « glass » 4 onglets (inspiration boutons de l'utilisateur) :
        👁️ Vue d'ensemble (compteurs ALL-TIME + heatmap + graphiques) ·
        🎭 Goûts (ADN cinéphile, évolution, studios, marathons, ⭐ contenus
        notés) · 👥 Personnes (acteurs/réalisateurs/studios + recherche) ·
        🗓️ Temps (historique + exports) ;
      • l'onglet ACTIF a le liseré jaune + texte blanc + lueur (mesuré) ;
      • PANNEAU DE FILTRES partagé en verre (période/type/genre/note) ;
      • RÉACTIVITÉ : chaque onglet ne calcule que SA matière (les
        filmographies TMDB de Personnes ne tournent plus à chaque affichage)
        et l'onglet actif est lu APRÈS les boutons → le contenu change au
        CLIC, sans second rerun (bug trouvé au banc) ;
      • animations d'entrée (nav + panneau), hover glass.
- [x] (fix harnais) sélecteurs nav : les colonnes Streamlit 1.60 sont des
      stVerticalBlock (plus stColumn) — 10 sélecteurs corrigés.
- [x] Banc : 19/19 (400→safe, Groq, nav mesurée, 4 onglets, isolation des
      matières) + 23/23 tests + smoke test app réelle.

### Fait en V155 (retours du 08/10 au soir — stats affinées + IA peaufinée)
- [x] IA — ANECDOTES : le prompt exige désormais de VARIER les sujets (pas
      systématiquement l'anecdote du rôle le plus iconique — retour : « ça
      parle de Breaking Bad, pas de Cranston »).
- [x] IA — SPINNER stylé (Manrope + couleurs du thème, fin du texte gris
      standard qui dénotait) et bouton « 🎲 Une autre » SOUDÉ au bloc
      (gap mesuré ≈ 0 px, coins raccords).
- [x] STATS — NAVIGATION : les 4 onglets vivent dans UNE BARRE « liquid
      glass » (blur + lueur interne) ; l'onglet ACTIF est en VERT avec un
      LÉGER ZOOM (scale 1.05, texte blanc) — le jaune était trop criard
      (retour utilisateur) ; marqueur aligné DÈS le clic (st.rerun
      immédiat — fin de la latence « ça ne devient pas actif »).
- [x] STATS — FILTRES : la RECHERCHE de contenu rejoint le panneau de
      filtres en haut de page (« tout dans le même bloc ») et filtre
      l'historique ET les notes. La recherche acteur reste dans Personnes
      (elle cherche sur TMDB, ce n'est pas un filtre du dataset).
- [x] STATS — FINI LA REDONDANCE : la vue d'ensemble all-time séparée est
      supprimée ; ses KPI (Watchlist, Listes, Contenus en listes, totaux)
      sont FUSIONNÉS dans l'onglet Vue d'ensemble avec les KPI filtrés.
      Plus de sous-titre « Statistiques détaillées ».
- [x] STATS — FUSION HISTORIQUE + NOTES (demande clé) : l'onglet « Temps »
      devient « 📜 Historique & notes » avec un VRAI toggle : off =
      historique des vues (ouvert), on = ⭐ contenus notés. La recherche
      du panneau filtre les deux. EXPORT EXCEL 2 ONGLETS (Vues + Notes)
      ajouté à côté des CSV/JSON.
- [x] Banc : 19/19 (barre mesurée blur 10/radius 16, actif vert + zoom,
      sans latence, toggle notes/historique, Excel proposé, KPI fusionnés,
      IA soudée, non-régressions) + 23/23 tests + smoke test.

### Fait en V156 (retours du 09/10 — La Pépite + stats finies + Groq activé)
- [x] 🐛 BUG POP LIBRE : la section « ✍️ décris ton envie » n'apparaissait
      qu'après avoir choisi une humeur (le `return` arrivait avant son
      rendu). Elle est désormais rendue AVANT toute sortie — toujours
      visible.
- [x] 🎲 RENOMMAGE PRUDENT : « 🍿 POP — une pépite ? » devient « 🎲 La
      Pépite » (inquiétude de plagiat du nom de l'autre outil — retour
      utilisateur). Badge « 💎 LA PÉPITE », libellés généralisés.
- [x] 🎯 4 HUMEURS SUPPLÉMENTAIRES (12 au total) : 🕵️ Enquête & mystère ·
      🍿 Pop-corn fun · 💔 Déchirant · 🤪 Décalé & culte (mapping local
      inclus pour le repli sans IA).
- [x] 🔍 RECHERCHE GLOBALE : la recherche du panneau filtre désormais TOUT
      (heatmap, graphiques, goûts, ADN…), plus seulement l'historique et
      les notes — appliquée au dataframe filtré.
- [x] 📊 KPI LISTES : « Films vus (total) » et « Épisodes vus (total) »
      RETIRÉS (redondants avec les KPI filtrés) ; ajout du DÉTAIL par
      liste (chips « nom · nb contenus ») sous le sous-titre « Les
      statistiques de tes listes ».
- [x] 📜 HISTORIQUE & NOTES : les deux tableaux vivent À PLAT (plus
      d'expander) → l'état déroulé est STABLE au toggle (retour : « la
      liste s'enroule sur elle-même »). Case à cocher glass stylée
      (Streamlit 1.60 rend le toggle en checkbox — découvert au banc).
- [x] 👥 PERSONNES : titre de section « ACTEURS, RÉALISATEURS & STUDIOS »
      (fini « LES GENS »).
- [x] 🎲 IA : bouton « Une autre » au style EXACT du bouton fiche des
      tuiles — liseré 4px qui PROLONGE celui du bloc (mesuré 0.06 px) ;
      spinner en COULEUR D'ACCENT de la fiche (injecté par fiche).
- [x] 🧭 NAV STATS : DOUBLE RAIL sous la barre glass (rail vert lumineux
      + rail fin jaune — inspiration de l'exemple utilisateur « boutons
      + 2 barres horizontales »).
- [x] Banc : 16/16 (POP libre sans humeur, 12 humeurs, double rail
      mesuré, recherche globale, KPI listes, tableaux à plat stables,
      bouton IA 0.06 px, non-régressions) + 23/23 tests + smoke test.

### Fait en V157 (retours du 09/10 — pépites unifiées + crash corrigé)
- [x] 🐛 CRASH RECHERCHE STATS (traceback utilisateur) : KeyError « title »
      — la colonne du DataFrame s'appelle « titre ». Corrigé avec repli
      sûr + recherche étendue à l'étiquette d'épisode. La recherche filtre
      TOUT : KPI, heatmap, graphiques, goûts (testé « blade » → Films 1).
- [x] 🎲 LA PÉPITE — TUILES UNIFIÉES avec « Que regarder ? » (demande :
      « copier-coller ces tuiles ») : poster + chip type + titre + CHIPS
      (genres/durée/note) + pastilles D'ÉTAT STANDARD (📂 source pour
      dans tes listes, 🌐 Hors de tes listes) + bouton fiche soudé
      (gap 0, même largeur — mesuré). Fini les tuiles spéciales.
- [x] 🎲 TIRAGE PAR HUMEUR : propose désormais DEUX contenus — un DANS
      tes listes ET une œuvre HORS de tes listes (demande utilisateur),
      comme l'envie libre. Sections titrées « 📂 DANS TES LISTES » /
      « 🌐 HORS DE TES LISTES ».
- [x] 🎯 TYPE RESPECTÉ : l'envie libre hérite du pills Film/Série du
      panneau — règle ABSOLUE dans le prompt (fini Shogun pour « un film
      d'amour sur un bateau ») ; les candidats de tes listes sont aussi
      filtrés par type.
- [x] ✍️ Phrase d'intro de l'envie libre : entière, dans un encart
      dédié (elle était tronquée sous la 1re tuile).
- [x] 🧭 NAV STATS : retour à l'inspiration utilisateur — les BOUTONS
      AU-DESSUS, nus (fini le cadre englobant « trop de cadre »), puis
      DEUX BARRES horizontales en dessous : verte lumineuse (3px, lueur)
      + jaune fine (1.5px, en retrait).
- [x] 📊 KPI LISTES : de vraies TUILES par liste (demande : « des tuiles
      avec le nom de mes listes et le nombre de contenu ») sous le
      sous-titre « Les statistiques de tes listes » — jusqu'à 8 listes.
- [x] 📜 HISTORIQUE : le compte suit les FILTRES (fini le 6753 all-time
      avec une période restreinte) ; colonne « Ma note » retirée du
      détail des visionnages (le toggle ⭐ y pourvoit) ; toggle rendu
      plus visible (titre « Vues ou notes ? » + libellé éclairci).
- [x] (fix interne) collision de clés de boutons pépite quand le tirage
      humeur ET l'envie libre proposaient la même œuvre — badges
      préfixés (humeur_/libre_).
- [x] Banc : 16/16 (crash, tuiles fusion 0px, 2 propositions humeur,
      phrase entière, type, nav sans cadre + 2 barres, tuiles listes,
      compte filtré, non-régressions) + 23/23 tests + smoke test.

### Fait en V158 (retours du 10/10 — pépites parfaites + Excel + session)
- [x] 🎲 LA PÉPITE — LA VRAIE TUILE « Que regarder ? » (retour : « reprends
      vraiment la tuile, dans son look OU son contenu ») : les propositions
      passent par `_pepite_scored_row` → `score_item` → le MÊME rendu que
      les tuiles de reco. Concrètement : année en PASTILLE (fini les
      parenthèses à côté du titre), pastille durée/saisons-épisodes, note ⭐,
      SCORE perso /100 + FRICTION (oui, compatibles : calculés pareil pour
      le contenu de tes listes ET pour le hors-listes via la fiche TMDB),
      signaux « ℹ️ Pourquoi ce score ? », chips genres/studios/acteurs,
      LIENS 🔎 JustWatch · TMDB · MDBL, bouton fiche soudé. Le média
      original est retrouvé dans le dataset (données enrichies complètes).
- [x] 🎲 FICHE DES PROPOSITIONS HORS LISTES : bannière + couleur
      d'accentuation RÉPARÉES (le backdrop manquait dans l'item → il est
      désormais récupéré depuis la fiche TMDB déjà chargée par la fiche).
- [x] 🎲 ESPACEMENT : titres « 📂 DANS TES LISTES » / « 🌐 HORS DE TES
      LISTES » collés à leur tuile (retour avec capture : « trop
      d'espace ») — marge négative ciblée.
- [x] 🧭 NAV STATS : UNE SEULE barre sous les boutons (la VERTE lumineuse
      3px) — la barre jaune fine est retirée (retour utilisateur).
- [x] 📊 STATS : « 📈 LES STATISTIQUES DE TES VISIONNAGES » (titre des KPI
      filtrés) + UN SEUL groupe « 🗂️ LES STATISTIQUES DE TES LISTES » :
      Watchlist · Listes personnelles · Contenus en listes + les tuiles
      par liste coulent ENSEMBLE (fini les lignes éparpillées).
- [x] 📥 EXPORT EXCEL REFONDU (onglet Historique & notes) : vrais tableaux
      striés + filtres + en-tête figé, colonnes PROPRES (fini poster/clés
      techniques), vraies dates, largeurs auto, genres « · » — + 3e onglet
      « Analyses » : visionnages par mois, top genres, films vs épisodes,
      répartition de tes notes, avec GRAPHIQUES Excel natifs (barres,
      barres horizontales, camembert). Réponse donnée : CSV/JSON/Excel ne
      sont PAS des formats d'import Trakt/MDBList (aucun import d'historique
      n'existe côté Trakt web ; MDBList synchronise AVEC Trakt) — ce sont
      des formats d'analyse/sauvegarde.
- [x] 🎲 BOUTON « Une autre » (info des coulisses) : AUX COULEURS DU BLOC
      (fond verre + liseré accent + texte accent clair) avec SURBRILLANCE
      au survol (fond accent, lueur) pour montrer qu'il est cliquable.
- [x] 🐛 SESSION QUI « SE DÉCONNECTE » après ~5 min d'inactivité (retour :
      « il faut que je repasse par le Tableau de bord, c'est vraiment
      pénible ») : cause racine analysée AU BANC — le serveur Streamlit
      DÉTRUIT la session après inactivité (TTL 120 s), la nouvelle session
      démarre vide et dépend du handshake du contrôleur de cookies. Fix :
      marqueur d'URL `msl_on=1` (survit à la perte de session, retiré à la
      déconnexion) + `_session_self_heal` : quelques reruns rapprochés
      (bornés, jamais de boucle) relancent TOUTE la chaîne de
      restauration — tu restes sur ta page, les données reviennent seules.
      Vérifié au banc (mini-app dédiée + coupure websocket + redémarrage
      serveur : restauration auto sans passer par le Tableau de bord).
- [x] Décisions notées : transitions/flèches entre widgets des stats →
      DÉCONSEILLÉ (fragile en Streamlit + mobile), le scroll reste ;
      recherche par acteur dans la recherche globale → idée ajoutée au
      TODO (possible via TMDB, coût d'appels à évaluer).
- [x] Banc : verify158 + mini-banc session dédié + 23/23 tests + smoke test.

### Fait en V159 (retours du 10/10 soir — finitions + style Spotify)
- [x] 🎲 PASTILLE « HORS DE TES LISTES » : VÉRITÉ DU STATUT (retour : l'IA a
      proposé un film « hors listes » qui était EN FAIT dans les listes).
      Double correctif : (1) le PROMPT reçoit la liste des titres déjà en
      Watchlist/listes à ÉVITER (l'IA ne voyait que 40 candidats sur ~300) ;
      (2) filet de sécurité au rendu — si l'œuvre proposée est en réalité
      dans les listes, la tuile affiche 📂 + le VRAI nom de liste.
- [x] 🎲 TITRES DE SECTION (« DANS TES LISTES » / « HORS DE TES LISTES ») :
      la marge négative V158 + la remontée des tuiles les faisaient
      CHEVAUCHER (retour avec capture) — nouveau réglage : titre
      AU-DESSUS de sa tuile, écart propre ~12 px mesuré, z-index de
      protection.
- [x] 📊 STATS : ARRIVÉE EN HAUT DE PAGE (retour : « j'arrive en plein
      milieu, jamais en haut ») — micro-composant scroll-to-top rendu
      uniquement à l'arrivée sur la page et au changement d'onglet (la
      position de défilement des autres interactions est préservée).
      Découverte au banc : en Streamlit 1.60 la page défile sur
      section[data-testid="stMain"], PAS sur window.
- [x] 🎨 BARRES DE PROGRESSION STYLE SPOTIFY (retour avec capture du
      dashboard Spotify) : partie « déjà » VERTE · ESPACE VIDE · CURSEUR
      (tiret blanc lumineux, 4×18 px) · partie « à voir » JAUNE décalée —
      sur TOUTES les barres (tuiles Que regarder/Pépite/En cours/Fantôme
      + fiche). Sur la FICHE : la VAGUE (déjà vu) et le trait PLAT (à
      voir) sont maintenant COUPÉS par un espace vide, avec un CURSEUR
      vertical arrondi au milieu (l'ancien point blanc est remplacé).
- [x] Banc : 27/27 (re-badge Titanic 📂, prompt anti-doublon, écart titre
      12 px, barres mesurées curseur 4×18 px + écart 3 px, vague + rect
      rx, non-régressions) + preuve scroll dédiée (remonte OUI / stable
      sans changement) + 23/23 tests + smoke test app réelle.

### Fait en V160 (retours du 10/10 soir — barres, lenteur, acteur)
- [x] 🎨 BARRES SPOTIFY : ESPACE VIDÉE clairement visible entre le vert et
      le jaune (9 px de chaque côté du curseur — avant, le curseur
      remplissait l'espace ; retour : « je ne vois pas d'espace »).
- [x] 🎨 ANIMATION D'INITIALISATION (demande utilisateur) : la barre part
      de ZÉRO et s'arrête au score, UNE fois — à l'ouverture d'une fiche
      et quand une nouvelle tuile apparaît. Sur la fiche, la VAGUE se
      révèle de gauche à droite (largeur du clip animée) puis le trait
      plat et le curseur apparaissent en fondu. Technique : @property
      CSS (variable --pct animable) + animation des largeurs SVG.
- [x] 🐛 BARRE TMDB DU TABLEAU DE BORD (oubli V159) : tous les st.progress
      natifs sont remplacés par les barres Spotify (dashboard, Que
      regarder pendant l'enrichissement, Goûts : genres/équilibres/
      studios) — sans animation pour celles qui se rafraîchissent toutes
      les 2,5 s.
- [x] ⚡ LENTEUR EN NAVIGATION (retour V159) : CAUSE TROUVÉE AU BANC —
      l'export Excel (~2 s sur 7000 lignes) était reconstruit À CHAQUE
      rendu de l'onglet Historique. Il est désormais PRÉPARÉ AU CLIC
      (bouton Préparer → spinner → Télécharger). + cache du profil de
      goûts sur la page Pépite. NB : après chaque déploiement, les caches
      serveur se reconstruisent (enrichissement en arrière-plan) —
      quelques minutes de relative lenteur sont normales.
- [x] 🎨 ONGLETS STATS : effet LIQUID GLASS « goutte d'eau » (demande avec
      capture) — transitions ressort doux, halo radial qui se diffuse au
      survol, zoom 1.04 + illumination ; le bouton actif garde son zoom.
- [x] 📊 ORDRE DES TUILES « LES STATISTIQUES DE TES LISTES » (retour) :
      Listes personnelles (le contenant) → Watchlist → Contenus en
      listes (les volumes) → détail par liste.
- [x] 🔎 RECHERCHE PAR ACTEUR/RÉALISATEUR dans la recherche globale des
      stats (demande utilisateur) : si aucun titre ne correspond, la
      personne est cherchée sur TMDB (cache 7 j) et l'historique est
      filtré par sa filmographie — encart « 🎭 PERSONNE DÉTECTÉE » avec
      le nombre de visionnages ; toute la page suit (KPI, heatmap,
      graphiques, historique). Coût : 2 appels TMDB max par recherche
      infructueuse, ensuite le cache prend le relais.
- [x] Banc : 24/24 (espace 9 px mesuré, animations mslBarGrow/mslWaveGrow,
      hover mesuré matrix(1.04…), ordre des tuiles, Cranston → 5
      visionnages, Excel au clic 3 onglets + 4 graphiques,
      non-régressions) + 23/23 tests + smoke test.

### Fait en V161 (retours du 11/10 — glass v2, acteur complet, statuts)
- [x] 📊 ORDRE DES TUILES (décision tranchée à la demande de l'utilisateur) :
      ⭐ Watchlist → 📦 Contenus en listes (les volumes ensemble) → 🗂️ Listes
      personnelles (le contenant, qui introduit le détail) → détail par liste.
- [x] 🎨 ONGLETS STATS « CLEAR GLASS v2 » (retour : « j'ai l'impression de
      voir des onglets Excel ») : pilules translucides (radius 999px, flou
      16px, fond blanc 5,5 %, reflet interne), GOUTTE qui monte du bas au
      survol, BALAYAGE lumineux (shine) qui traverse, zoom 1.045 ; actif =
      pilule de verre vert dense à liseré menthe.
- [x] 🐛 RECHERCHE PAR ACTEUR → HISTORIQUE ET NOTES (retour : « je ne vois
      aucun film dans l'historique ou les contenus notés ») : le filtre
      filmo ne s'appliquait qu'au DataFrame (KPI/graphiques) — les tableaux
      refaisaient leur propre recherche par titre (vide). Désormais les
      DEUX tableaux suivent la personne (la recherche texte est écartée
      quand une personne est détectée).
- [x] 🏷️ PASTILLES D'ÉTAT « ▶️ En cours » / « 🚫 Abandonnée » (retour : The
      Office proposée « hors listes » alors qu'elle est en cours) : sur les
      TUILES (à la place de 🌐 quand ça s'applique, en plus de 📂 sinon) et
      dans la FICHE (priorité : abandonnée > en cours > vu > liste).
      Sources : Up Next + reprises en pause (en cours), section dropped
      (abandonnées).
- [x] 🐛 FICHE DYNASTY (séries abandonnées) : les séries droppées ne vivent
      pas dans le dataset croisé — la fiche partait d'un item minimal
      (sans année ni note). Nouveau `_dropped_fiche_row` (item direct) +
      repli du nombre de saisons sur le PAYLOAD TMDB (la fiche l'a déjà
      chargé). Reproduit et vérifié au banc : bannière + saisons rendues,
      pastille « 🚫 Abandonnée », aucun crash. À confirmer en réel — si ça
      plante encore, me donner le texte exact de l'erreur rouge.
- [x] Banc : 19/19 (ordre, glass v2 mesuré, acteur → historique 5 + notes 1,
      The Office ▶️, Dynasty complète, non-régressions) + 23/23 tests +
      smoke test.

### Fait en V162 (retours du 11/10 soir — LES 4 IDÉES IA + finitions)
- [x] 💬 « POURQUOI CE SCORE ? » NARRATIF (idée IA validée) : dans chaque
      fiche, sous les pastilles de signaux, l'IA résume le score en UNE
      phrase vivante (tutoiement, 40 mots max). Précalculée en thread au
      chargement de la fiche (Groq prioritaire) — jamais bloquante : si
      l'IA n'est pas prête, les pastilles seules s'affichent.
- [x] ⚖️ RÉSOLVEUR DE DILEMME (idée IA validée) : sur « Que regarder ? »,
      un panneau « J'hésite entre deux ou trois… » — multiselect des
      résultats filtrés (2-3 max) → l'IA tranche (gagnant + ordre conseillé
      + 2-3 phrases) + bouton fiche du gagnant.
- [x] 🎬 « APRÈS CE FILM » (idée IA validée) : dans la fiche, un bouton
      « Que regarder ensuite ? » → les 3 MEILLEURES suites de soirée dans
      TES listes (échos d'ambiance/thème/énergie), avec une phrase
      alléchante par enchaînement + lien TMDB.
- [x] 🌙 « TON SOIR PARFAIT » (idée IA validée) : sur La Pépite, un panneau
      heure + temps dispo + humeur (les 12) + type → l'IA compose un
      mini-programme avec les contenus de tes listes (durées réelles
      respectées, somme sous la limite), horaires par étape, phrase
      d'ambiance + boutons fiche par étape.
- [x] 🏷️ PASTILLES : UNE SEULE par tuile (retour : « une série peut être
      en cours, watchlist ET déjà vue ») — priorité demandée : 1. ▶️ En
      cours · 2. 🚫 Abandonnée · 3. 📂 ta liste · 4. ✅ Vu · 5. 🌐 Hors.
- [x] 🎨 COULEURS distinctes (retour : « en cours » était jaune comme la
      Watchlist) : ▶️ En cours = ORANGE (#ffc069), 🚫 Abandonnée = ROUGE
      doux (#ff9aab) — sur tuiles ET fiches. Vert = vu, jaune = liste,
      bleu = hors (inchangés).
- [x] 🎨 ONGLETS GLASS v3 (retour : « enlève les bordures des boutons, un
      seul encadré clear glass ») : UNE pilule translucide englobe les 4
      boutons (999px, flou 16px, liseré unique) ; boutons NUS (sans
      bordure) ; survol = goutte + shine + zoom locaux ; ACTIF = verre
      givré vert (liseré interne lumineux, pas de bordure dure).
- [x] Banc : 17/17 (phrase 💬 dans la fiche, dilemme parsé, après-film 3
      suggestions, soir parfait (programme + boutons), pastille unique
      Severance en orange, pilule unique + boutons nus + actif givré
      mesurés, non-régressions) + 23/23 tests + smoke test.

### Fait en V163 (retours du 11/10 nuit — 4 idées IA affinées)
- [x] 💬 SCORE STORY : la phrase narrative passe à la couleur d'ACCENT
      PRINCIPALE de la fiche (plus saturée que l'accent clair — retour :
      « elle est blanche ») + !important. Économie confirmée : 1 appel
      PAR FICHE OUVERTE (jamais pour les fiches non consultées), cache
      15 min, ~300 tokens par appel.
- [x] ⚖️ DILEMME : BARRE DE RECHERCHE qui filtre les titres avant le
      multiselect (fini la liste de 1000 éléments — retour utilisateur),
      et le VERDICT s'affiche en VRAIES TUILES (pastilles, score,
      friction, bouton fiche) dans l'ordre conseillé par l'IA.
- [x] 🎬 APRÈS CE FILM : les 3 enchaînements sont des MINI-TUILES au
      thème de l'outil — poster CLIQUABLE (lien TMDB), chips
      durée/note/année, pastille d'état colorée (📂/▶️/🚫/🌐), liseré.
- [x] 🌙→🍿 FUSION « TON SOIR PARFAIT » (retour : « je ne vois pas la
      différence avec l'humeur… on garde Tire-moi la pépite en ajoutant
      le critère de durée ») : le panneau séparé est SUPPRIMÉ ; le
      tirage par humeur intègre un « ⏱️ Temps dispo » FACULTATIF
      (contrainte transmise au prompt IA), et l'humeur devient
      facultative aussi (sans choix → « Surprise-moi »).
- [x] 🎨 GLASS v4 (retour : « boutons trop bas, fond pas transparent ») :
      marqueurs masqués → boutons CENTRÉS verticalement dans la pilule
      (écart mesuré 0,1 px) ; bouton inactif SANS AUCUNE OMBRE, fond
      100 % transparent — on ne le distingue qu'au survol ou à la
      sélection (givré).
- [x] Banc : 18/18 (couleur accent, mini-tuiles après-film, fusion +
      tirage sans humeur + contrainte durée dans le prompt, centrage
      0,1 px, dilemme, non-régressions) + 23/23 tests + smoke test.

### Fait en V164 (retours du 12/10 — régression réparée + affinages)
- [x] 🐛 RÉGRESSION « PHRASE DU SCORE » (retour : « l'IA ne me dit plus
      pourquoi ce score est conseillé… ça charge indéfiniment ») : le
      mécanisme d'attente appelait le MAUVAIS CANAL IA en secours (celui
      des anecdotes) et bloquait 6 s. Corrigé : canal correct, attente
      3,5 s max, et JAMAIS d'appel bloquant — la phrase arrive en
      arrière-plan (cache 15 min). C'était ça, la « longueur avec
      Groq » : des appels en cascade inutiles.
- [x] ⚖️ DILEMME : pattern « Nettoyage des listes » (retour : « pas
      assez intuitif ») — barre de recherche + PILS CLIQUABLES dans le
      même bloc (on tape, la liste se réduit, on CLIQUE pour choisir,
      2-3 max). Verdict en tuiles conservé.
- [x] 🎬 APRÈS CE FILM : VRAIES TUILES identiques à « Que regarder ? »
      (poster réel, pastilles, score, friction — retour : « récupérer
      les mêmes tuiles »), poster CLIQUABLE (TMDB), liseré à l'ACCENT de
      la fiche courante (plus de vert/jaune standard), pourquoi 💬 par
      enchaînement, bouton au MÊME THÈME que « Une autre anecdote ».
      Liens fiables : les id hallucinés par l'IA sont filtrés (repli par
      titre, sinon la suggestion est ignorée).
- [x] 🍿 PÉPITE : les DEUX propositions (dans + hors listes) sont
      mémorisées dans « Pépites déjà tirées » (retour) ; la contrainte
      de durée est INTELLIGENTE : pour une SÉRIE, c'est la durée d'UN
      épisode qui doit rentrer dans le temps dispo (Game of Thrones
      OK pour 3 h — on regarde 1 épisode, retour utilisateur).
- [x] 🎨 ONGLETS : la pilule englobante est RETIRÉE (retour GSM :
      « horrible » sur smartphone) — option choisie par l'utilisateur :
      boutons nus, surbrillance au survol, actif givré, barre verte.
- [x] 📱 FICHE GSM : gros logo plafonné (58 px) + pastille d'état
      contenue dans la bannière (retour avec photo : « les pastilles
      sortent de la fiche »).
- [x] ✅ SÉRIES : la pastille « Vu le… » devient « ✅ 1er ép. le
      dd/mm/aaaa · dernier le dd/mm/aaaa » quand plusieurs dates
      existent (demande utilisateur).
- [x] Incident de développement (interne, résolu) : une édition a
      tronqué app.py en cours de version — restauré depuis la
      sauvegarde V163 et toutes les modifications refaites avec des
      ancres vérifiées + contrôles d'intégrité (14649 lignes, toutes
      les fonctions présentes).
- [x] Banc : 17/17 (phrase réparée + couleur, 3 vraies tuiles + poster
      cliquable + liseré accent, 2 pépites mémorisées, conteneur nu,
      GSM nav + logo 58 px + pastille contenue, non-régressions) +
      23/23 tests + smoke test.

### Fait en V165 (retours du 13/10 soir — fiche instantanée)
- [x] 💬 PHRASE DU SCORE RETIRÉE (retour : « pas certain de la plus
      value… prêt à m'en passer pour une fiche instantanée ») : la fiche
      s'ouvre sans AUCUN appel IA au chargement — les PASTILLES de
      signaux restent (explication locale, instantanée, 0 token).
      Économie : ~300 tokens par fiche ouverte.
- [x] 🎬 « APRÈS CE FILM » RETIRÉ (retour : « manque de pertinence…
      hyper long à charger… tu peux enlever »). Économie : 1 appel IA +
      1 build_profile par utilisation. L'INFO DES COULISSES reste
      (jugée « pertinente et vraiment géniale » — intacte).
- [x] 🐛 DILEMME : TypeError corrigé (retour avec traceback Python 3.14
      de Streamlit Cloud) — st.pills exige une LISTE, pas un range().
      + garde anti-liste-vide.
- [x] 📱 FICHE GSM : clear logo RESTAURÉ à sa taille/position d'avant
      (retour : « je préférerais que le clear logo reprenne sa position
      précédente ») ; les pastilles d'état passent SOUS la bannière,
      alignées à droite. PC inchangé.
- [x] ✅ PASTILLES SÉRIES : retour au simple « ✅ Vu le … » (retour :
      « déjà satisfait de ces pastilles génériques ») — le
      « 1er ép./dernier » est retiré.
- [x] ⚡ QUE REGARDER : CACHE du profil de goûts (retour : « met du
      temps à charger après la fermeture d'une fiche ») — recalculé
      seulement au rechargement du dataset.
- [x] Diagnostic réseau (demande) : app Streamlit Cloud SAINTE (statut
      RUNNING, pas de CPU throttle, 0,3 s), Groq et TMDB répondent en
      < 0,1 s → les lenteurs venaient du réseau de l'utilisateur
      (confirmé par lui : « en 5G ça va mieux ») + reconstruction des
      caches après déploiement (transitoire).
- [x] Inquiétude taille app.py : V164 = 703 949 octets (687 Ko, 14 655
      lignes) — PLUS GROS que V162 (700 545). Un affichage GitHub à
      184 Ko indiquerait un upload partiel → re-téléverser le fichier
      de la livraison.
- [x] Banc : 15/15 (fiche sans 💬 ni bouton après-film, ouverture
      1,7 s, coulisses intactes, GSM logo 90px + pastilles sous
      bannière, dilemme, non-régressions) + 23/23 tests + smoke test.

### Fait en V166 (retours du 13/10 nuit — VRAIE cause dilemme + finitions)
- [x] ⚖️ DILEMME — VRAIE CAUSE du TypeError (le fix V165 list() ne
      suffisait pas) : st.pills N'A PAS de paramètre max_selections
      (signature vérifiée : label/options/selection_mode/…) → mot-clé
      inattendu = crash. Corrigé : selection_mode="multi" + limite 2-3
      contrôlée par le bouton + rappel visuel au-delà de 3.
- [x] 📱 FICHE GSM : pastilles d'état EN HAUT de la bannière,
      au-dessus du clear logo (retour avec capture : « sous la
      bannière on ne les voit pas »). L'ancrage passe à la BANNIÈRE
      (.cinema-bottom en statique !important — découvert au banc que
      la règle de base écrasait). Logo 90px inchangé, PC inchangé.
- [x] ✅ SÉRIES — PASTILLES DE DATES (retour : « j'aime bien débuté
      le / dernier épisode vu le ») : « ✅ Vu » + « 1er ép. le … » +
      « dernier le … » en pastilles SÉPARÉES (sa proposition) ;
      pareil pour les EN COURS (« ▶️ En cours » + dates). Films :
      « ✅ Vu le … » inchangé. Les dates d'épisodes sont collectées
      via la SÉRIE imbriquée des entrées épisodes (l'entrée porte
      l'id de l'épisode, pas de la série — la cause du silence V164).
- [x] 🧭 POSITION PAR ONGLET STATS (retour : « chaque onglet avait une
      position propre — 1er chargement en haut, retour au point de
      reprise » — régression V159) : nouveau gestionnaire — 1re visite
      d'un onglet → haut ; retour → position restaurée (attribut DOM
      par onglet, sauvegarde continue 400 ms, une seule session).
      Logique validée au banc par injection directe ; le véhicule
      (components.html) est celui du scroll-to-top, prouvé en
      production chez l'utilisateur.
- [x] 🖼️ WORDMARK : le logo de l'app ne s'affichait plus (retour avec
      capture ; le favicon oui) — le service de fichiers statiques ne
      sert plus /app/static/* → le wordmark est embarqué en DATA-URI
      base64 (vérifié au banc : src=data:image/png;base64,…).
- [x] Banc : 15/15 (pastilles The Fall « Vu + 1er ép. + dernier »,
      fiche instantanée 2,1 s, GSM logo 90px + pastilles en haut,
      historique 8, dilemme, non-régressions) + AppTest pills multi
      + 23/23 tests + smoke test (wordmark data-URI ✓).

### Fait en V167 (retours du 14/10 — TON HISTOIRE livrée)
- [x] 📜 « TON HISTOIRE » DANS CHAQUE FICHE (la grande demande, enfin) :
      • SÉRIE VUE : carte « 1er épisode le … · dernier le … · série
        entière vue en X jours/mois · N épisodes · temps total ·
        rewatchs · ta note » + UNE SECTION PAR SAISON (expander) :
        chaque épisode avec sa date, « saison vue en X jours »,
        poster de saison (cache TMDB, 0 appel réseau garanti).
      • FILM VU : « Dernière vision le … · N visionnage(s) · temps ·
        ta note ».
      Source : le MÊME moteur normalisé que la page Historique —
      fiable en production. Lecture pure, rien n'est modifié. Le
      total (6 700+) et le tableau détaillé RESTENT intacts.
- [x] ✅ PASTILLES DE DATES FIABLES : « ✅ Vu + 1er ép. le … + dernier
      le … » calculées via le moteur normalisé (le scan brut des
      sections ne matchait pas les épisodes réels — retour : « je vois
      juste des Vu le »).
- [x] ⚖️ DILEMME : le MÊME SYSTÈME que « Signaux à rechercher » (retour
      avec capture : « c'est déjà dans mon app et ça marche nickel ») —
      UN SEUL multiselect avec recherche intégrée, placeholder clair,
      limite 2-3 native (max_selections). Fini pills + barre séparée.
- [x] 📱 FICHE GSM : pastilles EN BAS À DROITE de la bannière,
      exactement comme avant, mais SUR LEUR PROPRE COUCHE devant le
      clear logo (z-index 4) — leur position ne dépend plus de la
      taille du logo (retour utilisateur).
- [x] Banc : 19/19 (TON HISTOIRE série + film + saisons + épisodes
      datés + note, pastilles bannière fiables, dilemme multiselect,
      GSM bas-droite z-index 4, non-régressions) + 23/23 tests +
      smoke test.

### Fait en V168 (retours du 14/10 soir — TON HISTOIRE v2 + dilemme + bandes-annonces)
- [x] 📜 TON HISTOIRE v2 (refonte visuelle demandée) :
      • SAISONS ENROULÉES PAR DÉFAUT (<details> natif, dépliable sans
        rechargement — même mécanisme que « Pourquoi ce score ? ») : le
        chemin vers l'info des coulisses redevient court ;
      • POSTER DE SAISON sur la MÊME LIGNE que « Saison 1 · N épisode(s) »,
        à gauche (44px, 36px sur GSM) — la saison se déroule AVEC son
        poster, sans prendre trop de place ;
      • poster CLIQUABLE → page TMDB de la saison
        (themoviedb.org/tv/{id}/season/{n}, nouvel onglet) ;
      • ÉPISODES EN GRILLE ALIGNÉE : SxxEyy | titre | date — les codes,
        les titres ET les dates s'alignent chacun dans leur colonne,
        quelle que soit la longueur des titres (×N rewatch en chip) ;
      • AUCUN espace vide entre les saisons (empilement à 7 px) ;
      • TOUT aux couleurs d'accent de la fiche (bordures, titres, texte).
- [x] 🎬 BANDES-ANNONCES DISPARUES (Dragon Ball Z, Senna) — CAUSE
      RÉELLE TROUVÉE : leurs trailers TMDB n'existent qu'en ANGLAIS et
      l'appel principal de la fiche (language=fr-FR) ne renvoie QUE les
      vidéos françaises → la section disparaissait alors que la vidéo
      existe. Fix : second appel « toutes langues utiles »
      (include_video_language=fr,en,null, cache 30 j, uniquement si le
      1er appel ne trouve rien) +, en tout dernier recours, un BOUTON
      « ▶️ Chercher la bande-annonce sur YouTube » au lieu de rien.
- [x] ⚖️ DILEMME : ERREUR StreamlitDuplicateElementKey CORRIGÉE — les
      tuiles du verdict partageaient les clés des tuiles de la grille
      (mêmes contenus, préfixe identique). Les tuiles du verdict ont
      maintenant leur préfixe dédié « dlm_ » (_render_dilemma_tiles).
- [x] Banc : 24/24 (saisons enroulées, posters cliquables TMDB saison,
      grille alignée, gap 7px, accent, repli bande-annonce EN + bouton
      YouTube, collision dilemme ×2, GSM, non-régressions) + 23/23 tests.

### Fait en V169 (retours du 15/10 — TON HISTOIRE v3)
- [x] 📜 RUBAN « Mon histoire détaillée » : un niveau d'enroulement de
      PLUS — par défaut on ne voit que la carte de stats (1er épisode ·
      dernier · série entière en X jours · N épisodes · temps · rewatchs ·
      ta note) + un ruban fermé « 📜 Mon histoire détaillée · N saison(s) ».
      Dérouler le ruban → les saisons (enroulées) ; dérouler une saison →
      ses épisodes. (Retour : sur les séries longues comme DBZ, l'info des
      coulisses était très loin en bas.)
- [x] ▶️ Bouton YouTube (aucune vidéo TMDB) : l'ANNÉE du contenu est
      ajoutée à la recherche (« Senna 2010 bande-annonce ») — sinon on
      tombait sur un homonyme d'une autre année (ex. série Senna 2024).
- [x] Décision utilisateur : la largeur pleine de TON HISTOIRE / coulisses
      est GARDÉE telle quelle (pas de « feuille Word » — stabilité d'abord).
- [x] Banc : 22/22 (ruban fermé 41px, déroulé → saisons enroulées gap 7px,
      saison → grille alignée, accent, YouTube avec année, fiche film sans
      ruban, GSM, non-régressions) + 23/23 tests.

### Fait en V170 (retours du 15/10 soir — la grosse fournée)
- [x] 📜 TON HISTOIRE v4 :
      • DURÉES EXPLICITES : « 1 an 11 mois 15 jours » au lieu de « 23 mois »
        (partout : carte, saisons) ;
      • CARTE REFORMULÉE : « 1er épisode vu le … · dernier épisode vu le … ·
        série regardée durant … » · « N épisode(s) visionné(s) sur un total
        de X » (total TMDB, même appel que la fiche) et, pour une série EN
        COURS : « Il reste X épisode(s) à visionner, soit environ … » ;
      • SxxEyy CLIQUABLE → la page TMDB de l'ÉPISODE ;
      • RUBAN habillé en vrai bouton : bordure pleine, fond net,
        « dérouler / refermer » explicite, survol réactif (fini les tirets) ;
      • saisons sur fond TRANSPARENT (fini l'éclaircissement cumulé au
        déroulé du ruban).
- [x] ➕ AJOUTER À MES LISTES DEPUIS LA FICHE CINÉMA (demande du 07/10) :
      un expander « ➕ Ajouter à mes listes » en bas de fiche (session
      MDBList uniquement — invisible en mode ZIP Trakt). Choix Watchlist ou
      liste STATIQUE ; la Watchlist n'est pas proposée si le contenu y est
      déjà, chaque liste qui CONTIENT déjà le contenu est écartée, les
      listes dynamiques/IA jamais proposées. Mêmes appels éprouvés que la
      page « Que regarder ? ». Toast + libellé « ✓ Ajouté à mes listes » ;
      l'écriture part immédiatement, « Actualiser » resynchronise.
- [x] 👤 FICHE ACTEUR : score moyen de tes contenus NOTÉS avec cette
      personne (« note moyenne : 8,4/10 (12 notés) ») — local, instantané.
- [x] 🤝 STATS → onglet Personnes : « Tes duos favoris (acteur ×
      réalisateur) » — les associations les plus croisées de ton
      historique, liens TMDB (local, instantané, duos ≥ 2 contenus).
- [x] Banc : 28/28 (carte reformulée + total + reste, ruban-bouton, fond
      transparent, liens épisodes TMDB, score acteur, duos, ajout Watchlist
      + liste statique avec exclusions, non-régressions) + 23/23 tests.

### Fait en V171 (retours du 15/10 nuit — corrections ciblées)
- [x] 📜 TON HISTOIRE v5 :
      • lien SxxEyy en COULEUR D'ACCENT (plus de bleu hypertexte) ;
      • « dérouler / refermer » retiré du ruban (inutile) ;
      • ÉPISODES SPÉCIAUX (saison 00) exclus de TOUTES les stats —
        intervalle, épisodes vus, temps, « il reste », compte de saisons
        (retour DBZ : « 9 saisons régulières, pas 10 ») — mais toujours
        visibles dans le détail ; pastille bannière alignée (exclusion
        identique) ;
      • carte en VRAIE TUILE arrondie aux couleurs d'accent ;
      • posters de saisons : MÊME survol que les affiches de la fiche
        (translateY -3px + ombre, mesuré au banc).
- [x] ➕ Ruban d'ajout : habillage COULEURS D'ACCENT (bordure/fond/
      libellé) ; MASQUÉ si le contenu est déjà en Watchlist OU dans
      l'une des listes OU en cours de visionnage (retour : « on ne
      rajoute pas un contenu déjà rangé ou qu'on regarde »).
- [x] 👤 Fiche acteur : badges facettes « EN TANT QU'ACTEUR /
      RÉALISATEUR » espacés et encadrés, sections aérées, cartes
      crédits avec soulèvement au survol.
- [x] 📊 Stats : espace avant « 🤝 Tes duos favoris » (plus collé aux
      studios).
- [x] Banc : 28/28 (spéciaux exclus de bout en bout, tuile, lien
      accent, hover -3px mesuré, ruban d'ajout accent + masquages
      Titanic/First Man, facettes espacées, duos espacés,
      non-régressions) + 23/23 tests.

### Fait en V172 (retours du 16/10 — saisons cliquables, fin du vert, IA culture)
- [x] 📜 TON HISTOIRE :
      • chaque saison = TUILE CLIQUABLE SUR TOUTE SA SURFACE (plus besoin
        de viser le nom — comme le ruban) ;
      • EN-TÊTES DE COLONNES dans chaque saison déroulée : N° | Titre de
        l'épisode | Vu le (alignés sur la grille).
- [x] ➕ Ruban d'ajout : FINI LE VERT — fond du contenu déroulé, champ
      « Liste », pastilles radio et bouton « Ajouter » passent à la
      couleur d'accent de la fiche.
- [x] 👤 Fiche acteur (passe 2) : en-tête en TUILE arrondie, titres de
      section avec LISERÉ jaune, crédits en GRILLE uniforme (carré).
- [x] 🧭 Onglet « ▶️ En cours de lecture » → « ▶️ Vos visionnages en
      cours » (retour : le 1er indiquait une lecture à l'instant T).
- [x] 🕰️ IA SANS SPOILER — « POURQUOI MAINTENAU » (idée choisie par
      l'utilisateur) : bloc en bas de fiche avec l'HÉRITAGE CULTUREL de
      l'œuvre (objets iconiques, imaginaires collectifs, contexte de
      l'époque — ex. la DeLorean de Retour vers le futur), précalculé en
      arrière-plan comme l'info des coulisses (zéro lenteur) ; si l'IA
      n'a rien de notable → AUCUN bloc. Bouton « 🕰️ Une autre histoire ».
- [x] Banc : 28/29 (le 29e = artefact de charge du harnais ; le
      comportement « skip » a été prouvé par un test direct dédié) +
      23/23 tests.

### Fait en V173 (retours du 16/10 soir — coquilles + les 3 chantiers IA)
- [x] ✍️ COQUILLES : « POURQUOI MAINTENAU » → « POURQUOI ÇA COMPTE »
      (retour : « je ne sais pas ce que signifie MAINTENAU ») ; sous-titre
      « généré par IA · sans spoiler » ; blocs IA RAPPROCHÉS (marge
      conteneur 2,4 px mesurée).
- [x] 🎭 « L'ESPRIT DU FILM / DE LA SÉRIE » (idée retravaillée suite à
      « les mots-clés ne sont pas assez parlants ») : l'esprit de l'œuvre
      (1-2 phrases) + LE BON MOMENT pour la lancer + 2-3 SENSATIONS en
      mini-phrases. Précalculé, skip si méconnu.
- [x] 🔄 « MÊME ESPRIT » (demande utilisateur : « l'IA me fait des
      recommandations où je retrouve le même esprit, ex. The Office →
      Parks & Recreation ») : 2-3 œuvres au même esprit avec le pourquoi,
      chacune avec un lien TMDB. Précalculé, skip si pas d'équivalents.
- [x] 👤 « SON PARCOURS » sur la fiche acteur (idée « le rôle qui a tout
      changé / qui l'a aidé / le duo décisif ex. Jonah Hill & Michael
      Cera ») : le tournant de carrière + le duo décisif, sans raconter
      les films. Précalculé.
- [x] 🎬 FICHE DEPUIS UNE FICHE (maquette validée) : les POSTERS des
      sections Similaires/Saga ouvrent la FICHIE LOCALE du contenu
      (?msl_fiche=kind:id — la page se recharge et la fiche s'ouvre,
      données locales si présentes, sinon TMDB comme la Pépite) ; le
      TITRE garde le lien TMDB externe.
- [x] Banc : 16/16 + 2/2 (test lien fiche séparé : navigation réelle) +
      23/23 tests.

### Fait en V174 (retours du 16/10 nuit — écarts, tuiles, persistance)
- [x] 📏 ÉCARTS IA CORRIGÉS (retour : « chaque tuile est maintenant
      séparée de son bouton Une autre anecdote… ils doivent être
      collés » + « écart trop grand entre les blocs ») : cause racine =
      le GAP (16 px) du bloc vertical Streamlit entre chaque élément.
      Compensé par marges négatives ciblées sur le conteneur du bouton
      « Une autre… » (fiche film ET fiche acteur). Mesuré : tuile ↔
      bouton = 0,9 px (collés), les boutons « Fiche » des cartes
      personnes protégés (structure à colonnes exclue du sélecteur).
- [x] 🔄 MÊME ESPRIT en VRAIES TUILES (retour : « chaque élément proposé
      en format tuile comme dans Que regarder, avec les mêmes pastilles ») :
      recherche TMDB par titre (cache 30 j) → poster CLIQUABLE (fiche
      locale), pastille d'état (▶️/🚫/📂/✅/📌/🌐 croisé avec tes
      données), chips ⭐ note + 🗓️ année + type, et le pourquoi de l'IA.
      Si introuvable sur TMDB → tuile sans poster + lien de recherche.
- [x] 🎬 FICHE DEPUIS UNE FICHE — le VRAI BUG corrigé (retour : « la
      fiche ne reste qu'une seconde puis se ferme car le dashboard
      s'actualise ») : les reruns automatiques (restauration de session
      au chargement) fermaient le dialog. Pattern HEARTBEAT : le main
      ré-ouvre la fiche-lien tant qu'elle est vivante (battement posé au
      début ET à la fin du rendu) ; fermée par toi, le mode expire en
      ≤ 4 s et ne se ré-ouvre plus. Prouvé au banc : un rerun global
      juste après l'ouverture ne ferme plus la fiche ; après fermeture
      manuelle, un rerun ne la rouvre pas.
- [x] Banc : 18/18 + 3/3 (persistance testée séparément) + 23/23 tests.

### Fait en V175 (retours du 17/10 — calque cliquable, éco IA, tuiles)
- [x] 🖱️ TUILES « QUE REGARDER » ENTIÈREMENT CLIQUABLES (retour : « pourquoi
      ne pas utiliser le principe du bouton transparent depuis la tuile
      Que regarder, afin d'ouvrir la fiche ? Cela permettrait de supprimer
      le bouton Voir la fiche ») : le bouton devient un CALQUE TRANSPARENT
      couvrant toute la tuile — cliquer n'importe où ouvre la fiche (sans
      rechargement ni nouvel onglet). Pastilles (info-bulles), liens
      TMDB/MDBL/JustWatch et « Pourquoi ce score ? » restent actifs
      AU-DESSUS du calque. Prouvé au banc : couverture exacte (0 px
      d'écart), clic au centre ET au coin, info-bulles intactes.
- [x] 🎬 FICHE DEPUIS UNE FICHE SANS NOUVEL ONGLET (retour : « je perds
      tout juste en cliquant sur un poster », appli installée) : cause
      racine PROUVÉE au banc de sonde — Streamlit FORCE target="_blank"
      sur toutes les ancres du markdown, même internes (?msl_fiche).
      Fini les liens sur les posters : SIMILAIRES + SAGA deviennent des
      GRILLES (4 par ligne, tout visible d'un coup, PC comme GSM) où
      chaque carte est un bouton transparent → la fiche du contenu
      REMPLACE celle du dialog ouvert (le corps du dialog relit la row
      en session à chaque rerun de fragment) : instantané, session
      intacte, zéro onglet. Bonus : le bouton « 🎬 Ouvrir la fiche » du
      pied disparaît (la carte entière est le bouton). Les liens
      ?msl_fiche déjà partagés continuent de fonctionner (banc ✓).
- [x] 🌍 ÉCO IA (retour : « est-ce que cela provoque des appels IA/token
      supplémentaires ? Important de penser à la planète et la
      consommation d'eau ») : vérité d'avant V175 — le nonce posé à
      chaque ouverture de fiche invalidait le précalcul des 4 canaux
      « contenu » → POURQUOI ÇA COMPTE / L'ESPRIT / MÊME ESPRIT / SON
      PARCOURS étaient re-générés à CHAQUE nouvelle session pour chaque
      œuvre. V175 : ces 4 canaux passent par un cache 30 jours (générés
      UNE fois par œuvre, partagés entre sessions et appareils) ; SEULE
      l'INFO DES COULISSES reste régénérée à chaque ouverture (ta demande
      V152 : anecdote nouvelle à chaque fiche). « Une autre… » passe à
      la variante suivante (chaque variante est aussi mémorisée).
      Prouvé au banc : 2e session = 0 appel IA pour ces canaux (−75 %
      d'appels par œuvre et par session).
- [x] 🔄 MÊME ESPRIT au format EXACT des tuiles « Que regarder ? » (retour :
      « qu'elles ressemblent encore plus à mes tuiles, sauf la couleur ») :
      même structure (poster, tête de ligne + pastilles ⭐ note/année,
      chip d'état, lien TMDB, barre de progression, « Pourquoi ce
      contenu ? » déroulant, colonne note à droite) — couleurs d'ACCENT
      de la fiche. La note affichée est étiquetée « note TMDB » (jamais
      confondue avec ton score personnel). Tuiles cliquables (fiche dans
      le dialog, comme Similaires/Saga).
- [x] 🖱️ SOULÈVEMENT au survol corrigé : la carte ne bouge plus SEULE —
      c'est le BLOC ENTIER (carte + calque + pastilles) qui se soulève
      d'un tenant. Au banc, le translateY de la carte faisait glisser
      « Pourquoi ce score ? » de 2 px sous le pointeur entre l'appui et
      le relâchement → le déroulé ne s'activait pas toujours.
- [x] 📏 BOUTON « UNE AUTRE ANECDOTE » : +2 px de hauteur (retour fiche
      acteur : « légèrement tronqué en bas, il manque 1-2 pixel ») —
      mesuré au banc : 26 px, aucun rognage, fiche film ET fiche acteur.
- [x] Banc : 22/22 (calque exact, clics centre/coin, info-bulles, grilles
      Similaires/Saga, tuiles MÊME ESPRIT + accent, navigation dans le
      dialog sans onglet, éco sur 2 sessions, anecdote non tronquée,
      lien partagé, saga × similaires sans collision de clés,
      non-régressions Fantôme/personnes/BR2049).

### Fait en V176 (retours du 17/10 — bandeaux, haut de fiche, cadre, acteur)
- [x] 🎞️ SIMILAIRES/SAGA : RETOUR AU BANDEAU DÉFILANT (retour : « j'adorais
      la disposition, la possibilité de scroller vers la droite ») — les
      posters sont de nouveau côte à côte, même écart qu'avant (colonnes
      de 84 px, gap 8 px), ET chaque carte reste un bouton transparent
      (fiche dans la fenêtre, sans nouvel onglet). La rangée de colonnes
      défile en CSS, les cartes ne s'écrasent jamais, PC comme GSM.
- [x] ⬆️ Fiche ouverte depuis une fiche : elle démarre EN HAUT de la
      fenêtre (retour : « celle-ci garde la position de la précédente »).
      Un rerun de fragment conserve la position de défilement → on passe
      par une ré-ouverture complète (dialog NEUF, protégé par le mode
      heartbeat V174 contre les reruns automatiques). Mesuré au banc :
      scrollTop = 7 px après navigation depuis une fiche déscendue.
- [x] 🖼️ MÊME ESPRIT : CADRE UNI (retour : « entre la tête, les 3 tuiles
      puis le bouton, j'ai l'impression de sortir de MÊME ESPRIT, le
      cadre est comme cassé ») : tête + tuiles + bouton vivent dans UNE
      SEULE boîte bordée d'accent (même habillage que les autres blocs
      IA). + CHIPS COMPLÈTES comme les tuiles « Que regarder » (retour :
      « ajoute les genres, studios, acteur, réal, saga ») : 🎭 genres ·
      🏢 studios · 👥 acteurs · 🎬 réal · 🔗 saga + pilule de tête
      (durée du film ou 📺 saisons/épisodes). Enrichissement via TMDB
      (déjà en cache 30 j) — ZÉRO appel IA ajouté (prouvé au banc).
- [x] 🖱️ TUILES CLIQUABLES PARTOUT (retour : « reproduis la même chose
      partout où j'ai des tuiles ») : En cours de visionnage, Séries
      abandonnées, Progression Fantôme, Calendrier des sorties — même
      calque transparent, les boutons « Voir la fiche » deviennent
      invisibles (la tuile entière ouvre la fiche).
- [x] 💎 PÉPITE CORRIGÉE (retour : la 2e proposition n'apparaissait pas +
      le « pourquoi » affichait du JSON brut) : cause réelle = réponse
      Groq légèrement abîmée (accolade d'ouverture perdue + type « Séri »
      au lieu de « Série » → The Haunting of Hill House cherchée comme un
      film). Correctifs : récupération de JSON robuste (fences, accolades
      perdues) + normalisation du type. Testé au banc avec la VRAIE
      réponse de l'utilisateur : les DEUX tuiles reviennent.
- [x] 👤 FICHE ACTEUR : filmographie en BANDEAUX de posters cliquables
      (retour : « une vue poster comme avant, avec le nom du contenu en
      dessous, l'année, la pastille, ET le nom du personnage joué ») —
      chaque carte : poster, titre, personnage joué (italique), année,
      pastille (✅ Vu / 📂 liste / 📌 Watchlist / 🌐 À découvrir).
      Le clic ouvre la FICHE FILM ; FERMÉE, la FICHE ACTEUR REVIENT
      (retour : « fermée cette fiche film pourrait permettre de retrouver
      la fiche acteur du dessous »). Découverte au banc : fermer un
      dialog ne déclenche AUCUNE rerun dans Streamlit → utilisation du
      callback on_dismiss de st.dialog (pose un drapeau + rerun) : la
      fermeture éteint proprement le mode heartbeat ET rouvre la fiche
      acteur instantanément.
- [x] Banc : 22/22 (parser avec la vraie réponse abîmée, calque, bandeaux
      3+4 colonnes scrollables, scrollTop en haut, cadre uni + chips,
      filmo acteur + personnage + retour acteur, éco 2 sessions,
      non-régressions) + 23/23 tests cœur.

### Fait en V177 (retours du 17/10 soir — bugs d'affichage, alignements)
- [x] 🚨 BUG MAJEUR CORRIGÉ (retour : « des liserés accent partout, même
      devant la fiche ; le liseré arrive à gauche pour englober toute la
      fiche ; l'intégration de la bannière est cassée ; la couleur
      d'accentuation change quand MÊME ESPRIT finit de charger ») : le
      sélecteur CSS du « cadre uni » MÊME ESPRIT matchait AUSSI le bloc
      contenant TOUTE la fiche (le dialog enveloppe son contenu dans
      stLayoutWrapper > stVerticalBlock — prouvé au banc : un bloc de
      3688 px portait la bordure 4 px + le fond, d'où le liseré
      englobant, la teinte sur la bannière et « l'accent qui change »).
      Le sélecteur exige désormais la TÊTE du bloc en enfant direct —
      unique à la section MÊME ESPRIT. Prouvé : bloc total sans bordure
      ni fond, cadre présent sur la seule section (371 px).
- [x] 🎨 TITRES DE SECTION (La saga · Similaires · TON HISTOIRE ·
      Bande-annonce · Où le regarder) : couleur d'accent RETROUVÉE +
      ALIGNÉS sur les 1ers titres (Pourquoi ce score/Synopsis/
      Distribution). Causes : (1) une règle globale `p, li, label
      {color:var(--am-text)!important}` écrasait même les styles inline →
      !important ciblés + inline renforcés ; (2) les sections étaient
      sorties de la colonne d'infos en V176 → un SPACER invisible
      (14 % + 14 px, mêmes bases que la colonne poster) réaligne tout au
      pixel (mesuré : tous à 216 px, comme Synopsis, cartes comprises) ;
      GSM : retour au bord (layout empilé).
- [x] 🏷️ PASTILLES DES MINI-CARTES NON TRONQUÉES (retour : « les
      pastilles sont comme tronquées au milieu, comme si le bloc du
      dessous venait se mettre devant ») : dans les dialogs, Streamlit
      pose margin-bottom:-16px sur les conteneurs markdown → le conteneur
      d'une carte mesurait 16 px de MOINS que la carte → le badge du bas
      débordait et la section suivante (positionnée) le recouvrait.
      Annulé pour toutes les cartes (sim/alike/people). Prouvé :
      conteneur = hauteur carte, plus rien devant.
- [x] 🖼️ MÊME ESPRIT : écart tête→tuile réduit (7 px mesuré), écarts
      tuile→tuile 2 px, bouton « D'autres suggestions » referme l'encart
      sur toute sa largeur, ORDRE DES PASTILLES = Que regarder (état en
      DERNIER, retour : « même ordre que les pastilles de Que regarder »).
- [x] ⬆️ FICHE SUIVANTE EN HAUT — VRAIMENT (retour : « si je suis en bas
      d'une fiche, je suis à la même position sur la nouvelle ») :
      découvertes au banc : un clic dans le dialog ne déclenche qu'un
      rerun de FRAGMENT (le scroll serait conservé) ; st.rerun() global
      depuis le fragment FONCTIONNE (micro-test) ; un node réutilisé par
      React garde son scrollTop. Solution : RENDU VIDE INTERMÉDIAIRE —
      la fiche neuve s'affiche une fraction de seconde réduite à 2 px →
      le navigateur RAMÈNE le défilement à zéro par clampage (prouvé au
      micro-dialog : 800 → 0) → puis la fiche complète, en haut. Le
      rendu vide rafraîchit le heartbeat (fenêtre 4→6 s : elle expirait
      en cours de route → fermeture prématurée + faux « retour acteur »).
- [x] 👤 TUILES PERSONNES CLIQUABLES (retour : « rends les tuiles des
      acteurs directement cliquables, on enlève le bouton Fiche ») :
      Statistiques → chaque tuile personne est un bouton transparent
      (photo, nom, N déjà vus, lien TMDB actif au-dessus du calque).
- [x] Banc : 19/19 (pas de liseré global, bannière affleurante, titres
      accent + alignés à ±2 px, pastilles non tronquées, écarts MÊME
      ESPRIT, ordre pastilles, fiche suivante + retour acteur, people
      cards, parser, éco, anecdote) + 23/23 tests cœur.

### Fait en V178 (retours du 17/10 nuit — NameError, alignements, 1 ligne)
- [x] 🚨 NameError PRODUCTION corrigé (retour : erreur au clic sur un
      poster → « NameError … _dismissed ») : la variable _dismissed était
      UTILISÉE dans le main sans jamais être définie (le harnais de banc
      ne teste pas le main de l'app — le banc ne pouvait pas le voir ;
      ajout d'une garde source au banc). La navigation fiche → fiche
      fonctionne à nouveau.
- [x] 🔘 BOUTONS « UNE AUTRE… » réalignés (retour : « décalés par rapport
      à leur tuile, le bouton commence x pixels trop tôt ») : la marge
      pleine-largeur du bouton MÊME ESPRIT s'appliquait à TOUS les blocs
      IA (coulisses/pourquoi/esprit/parcours) → décalage de 7 px. Le
      sélecteur cible désormais le BLOC DE SECTION (identifié par sa tête
      en enfant direct). Prouvé : tous les boutons à 17 px = bord de leur
      bloc ; MÊME ESPRIT seul garde sa fermeture pleine largeur.
- [x] 👥 TUILES PERSONNES EMPILÉES corrigées (retour : « 2 acteurs
      sélectionnés qui se soulèvent ensemble, le clic ouvre toujours
      celui du dessous ») : quand une colonne porte 2 personnes, le
      calque couvrait la COLONNE entière. Chaque paire carte+bouton vit
      maintenant dans son PROPRE conteneur. Prouvé au banc (6 personnes/
      3 colonnes) : clic sur la carte du HAUT → SA fiche (Ryan Gosling),
      clic sur celle du BAS → SA fiche (Bryan Cranston).
- [x] 🎬 FICHE ACTEUR : les bandeaux filmo commencent À GAUCHE (retour :
      « contrairement à la fiche film, les films vus etc. commencent à
      gauche ») — classe marqueur act-filmo : le spacer 14 % + le padding
      .95rem de la fiche film sont exclus. Prouvé : 1re carte à 17 px =
      titre de section à 17 px.
- [x] 🎞️ BANDEAUX : UNE SEULE LIGNE à nouveau (retour : « tous les
      contenus apparaissent avec un retour à la ligne, la fiche est très
      longue — je veux 1 ligne à scroller vers la droite comme avant ») :
      Streamlit met flex-wrap:wrap par défaut sur ses rangées → nowrap
      forcé + ascenseur MASQUÉ (retour : « pas besoin de montrer qu'il y
      a un scroll possible, c'est intuitif »). Prouvé en GSM (390 px) :
      nowrap, débordement scrollable, hauteur = 1 carte.
- [x] Banc : 15/15 (NameError, boutons alignés, empilement people,
      bandeaux acteur à gauche, 1 seule ligne GSM, non-régressions liseré/
      titres/pastilles/anecdote/éco/retour acteur) + 23/23 tests cœur.

### Fait en V179 (retours du 18/10 matin — scroll, bouton, bande-annonce, pastilles)
- [x] 🚨 FICHE SUIVANTE EN HAUT — VRAIE SOLUTION (retour : « encore une
      fois, cela garde la position de l'ancienne fiche film lors de
      l'ouverture d'une nouvelle fiche film ») : le mécanisme V177 (rendu
      vide intermédiaire) n'a JAMAIS atteint le navigateur — son delta
      était ANNULÉ par le st.rerun() lancé dans le même run (prouvé au
      micro-banc : le marqueur du rendu vide n'apparaît jamais côté
      client). Nouveau mécanisme CÔTÉ NAVIGATEUR : un composant HTML
      invisible (height=0) en TÊTE de fiche ; son iframe recharge son
      script à chaque changement de marqueur (kind:id:nonce) et remet
      scrollTop=0 sur le DIALOG — c'est lui le vrai scrolleur
      (position:fixed, overflow-y:auto, mesuré au banc). La page DERRIÈRE
      garde sa position. Prouvé au banc : 839 px → 0 px avec nouveau
      marqueur ; « Une autre anecdote » (même fiche) → scroll CONSERVÉ à
      900 px (l'iframe ne recharge pas). Même composant sur la fiche
      ACTEUR (marqueur personne).
- [x] 🔘 BOUTON « D'AUTRES SUGGESTIONS » réaligné (retour : « trop haut et
      trop court en longueur ») : les marges -0.45rem le décalaient de
      7 px à GAUCHE des tuiles sans l'élargir + il mordait la dernière
      tuile de 5 px. Il vit maintenant dans SON PROPRE st.container,
      EXACTEMENT comme les tuiles → même largeur, même alignement PAR
      CONSTRUCTION. Prouvé : écarts 0 px gauche/droite, écart vertical
      +2 px (soudé sans chevaucher), habillage verre/liseré conservé.
- [x] 🎬 BANDE-ANNONCE PLEINE LARGEUR (retour : « plus grandes qu'en
      V174, elles sortent de l'écran ») : le pied V177 appliquait le
      spacer 14 % + 14 px à tous ses enfants alors que l'iframe vidéo
      fait 100 % de large → débordement à droite. La bande-annonce vit
      dans son PROPRE bloc sans spacer : elle commence à gauche (alignée
      sur le poster), occupe toute la largeur de la fiche, et son titre
      est aligné sur la vidéo (même départ → aucun effet de bug).
      Prouvé PC : vidéo 32→1248 px dans un dialog de 1280, zéro
      débordement ; GSM : 358/390 px. Plateformes/liens restent dans le
      pied aligné sur la colonne d'infos.
- [x] ⭐ NOTE TMDB EN PASTILLE dans MÊME ESPRIT (retour : « sur GSM,
      l'affichage de la note dans Que regarder est une pastille —
      reprends-la, avec info-bulle qu'il s'agit de la note TMDB ») :
      la pastille ⭐ x.x (même format que Que regarder) porte
      l'info-bulle « Note communauté TMDB (sur 10) — pas ton score
      personnel » ; la colonne /100 à droite est retirée ; la barre
      visualise toujours la note.
- [x] 🎨 CODE COULEUR COMPLET, PARTOUT (retour : « garder le code couleur
      vu / dans mes listes / hors de mes listes / en cours / abandonnée
      dans chaque pastille, partout où c'est possible ») : JAUNE =
      dans mes listes (📂/📌, nouvelle classe chip-liste), BLEU = hors de
      tes listes (chip-hors), ORANGE = en cours, ROUGE = abandonnée —
      désormais présents dans : MÊME ESPRIT (tous les états), bandeaux
      Similaires/Saga (en cours + abandonnée AJOUTÉS), filmographies
      acteur (en cours + abandonnée AJOUTÉES — elles restent visibles
      dans « dans tes listes » avec LEUR badge), tuiles Que regarder
      (📂 source passée en jaune). Styles prouvés au banc (jaune
      255,225,0 · bleu 45,156,219 · orange 255,192,105 · rouge 255,154,171).
- [x] Banc : 18/18 (scroll-top navigation + conservation anecdote, bouton
      aligné au pixel, bande-annonce sans débordement PC+GSM, pastille
      note, code couleur, non-régressions people/acteur/1 ligne/NameError/
      titres/anecdote) + flux retour acteur validé + 23/23 tests cœur.

### Fait en V180 (retours du 18/10 midi — bannière, bouton, zigzag, /100)
- [x] 🚨 BANNIÈRE PARFAITEMENT INTÉGRÉE (retour : « quelques pixels entre
      le haut de la fiche et le début de la bannière, je préfère comme
      avant ») : le composant scroll-top V179 laissait 2 × 16 px de gap
      flex autour de son conteneur invisible. Il est désormais HORS FLUX
      (position:absolute, 1×0 px) : il n'occupe AUCUN pixel, la bannière
      revient à 1 px du haut de la boîte (comme avant), et son script
      s'exécute toujours (prouvé : fiche suivante toujours en haut +
      « Une autre anecdote » conserve le scroll).
- [x] 🔘 BOUTON « D'AUTRES SUGGESTIONS » = PIED DU CADRE (retour : « il
      prend la taille de la tuile alors qu'il faudrait la taille du BLOC,
      et il devrait être accolé à la FIN du bloc ») : le bouton s'étend
      désormais jusqu'aux BORDS INTÉRIEURS du cadre MÊME ESPRIT (bord à
      bord) et referme le bas du bloc (léger écart de 5 px sous la
      dernière tuile, padding + bordure du cadre sous le bouton, coins
      arrondis alignés). Prouvé : écarts 1/2/3 px, largeur 1243/1246.
      Le sélecteur est scopé par un ~ : les TUILES précèdent l'ancre dans
      le MÊME bloc — ça n'existe que dans le cadre MÊME ESPRIT (les
      boutons « Une autre… » des autres sections restent à 17 px,
      non-régression vérifiée).
- [x] 🎬 FIN DU ZIGZAG (retour : « la bande-annonce tout à gauche puis le
      spacer pour Où le regarder, ça fait bizarre ; mets Où le regarder
      au-dessus ») : « Où le regarder » + liens passent AU-DESSUS de la
      bande-annonce (tout l'aligné ensemble : Similaires, Saga, Où le
      regarder à 216 px), puis la bande-annonce PLEINE LARGEUR (32 px).
      Et 📜 TON HISTOIRE passe TOUT À GAUCHE (32 px, aligné poster/
      bande-annonce/blocs IA — retour : « je veux vraiment éviter le
      zigzag »). Prouvé PC et GSM (vidéo et TON HISTOIRE tous deux à
      32 px).
- [x] ⭐ COLONNE /100 RESTAURÉE dans MÊME ESPRIT (retour : « j'aimais
      bien la colonne /100 ») : la pastille ⭐ (info-bulle « Note
      communauté TMDB (sur 10) — pas ton score personnel ») ET la
      colonne /100 cohabitent — sur GSM la colonne s'efface (règle du
      skin), la pastille prend le relais, exactement comme les tuiles
      « Que regarder ? ».
- [x] Banc : 19/19 (bannière 1 px, bouton bord à bord, fin du zigzag,
      /100 + pastille, scroll-top non-régression, anecdote conservée,
      people, acteur, GSM, code couleur) + 23/23 tests cœur.

### Fait en V181 (retours du 18/10 après-midi — lookup TMDB, bouton, fiche acteur enrichie)
- [x] 🔎 RECHERCHE TMDB ROBUSTE (retour : « certains films ne remontent
      pas en tuile, ni en poster » — ex. The Middle, dont la fiche TMDB
      existe bien : tv/1422) : l'IA propose parfois une ANNÉE erronée, et
      le filtre d'année TMDB renvoyait zéro résultat. Si la recherche
      AVEC année ne trouve rien, on RESSAYE SANS l'année (la tuile
      récupère poster, fiche, note et la VRAIE année TMDB). Prouvé au
      banc (test unitaire : The Middle, année erronée → 2e appel sans
      année → trouvée, id 1422). S'applique aussi aux pépites du POP.
- [x] 🔘 BOUTON « D'AUTRES SUGGESTIONS » : DERNIER pixel de la fiche
      film (retour : « qu'il soit le dernier élément, sans les quelques
      pixels vides dessous ») + FIN de la DOUBLE COUCHE de liseré
      (retour : « une double couche au niveau du liseré devant le
      bouton ») : le cadre MÊME ESPRIT porte son liseré, le bouton garde
      une bordure fine comme les boutons « Une autre… ». Prouvé :
      dBottom 1 px, bord gauche 1 px, bord à bord 1/2 px. (Pas besoin
      d'inverser les widgets IA — le bouton referme proprement la fiche.)
- [x] ⚡ PASTILLE FRICTION dans les tuiles MÊME ESPRIT (retour : les 2
      pastilles de « Que regarder ») : même formule que le moteur (durée
      courte / peu d'épisodes = facile à commencer), pastille verte à
      bord jaune + info-bulle. Le score personnel n'existe pas pour une
      suggestion IA (pas encore dans tes données) — la note TMDB et la
      friction sont les repères.
- [x] 🎬 FICHE ACTEUR ENRICHIE (le grand chantier) :
      • EN-TÊTE DÉGRADÉ Aston (vert foncé → vert clair, liseré discret)
        — « un beau dégradé respectant mon thème » ;
      • ÂGE (« 70 ans »), et si décédé : date de décès + âge au décès
        (« ✝️ décédé le 20/01/1993 à 63 ans ») + lieu de naissance ;
      • BLOC « 📜 DEPUIS MON HISTOIRE » : radios-pilules « En tant
        qu'acteur / réalisateur » (si les deux facettes ont des vus) +
        « 🎬 Films / 📺 Séries / 🗂️ Tout », tri par date de vision
        DÉCROISSANTE, contenus RÉPARTIS PAR ANNÉES de visionnage
        (inspiration Trakt / Cinopsys). Les toggles sont des radios
        horizontaux : le filtre s'applique INSTANTANÉMENT (un rerun
        global fermerait la fiche — les anciens bandeaux « Films/Séries
        vus » sont remplacés par ce bloc) ;
      • INFO-BULLES « Vu le 14/09/2026 » sur les pastilles Vu des cartes
        filmo (ou « Vu N fois · 1er le … · dernier le … » pour les
        rewatchs).
- [x] Banc : 13/13 (lookup, bouton dernier pixel + liseré simple,
      friction, dégradé + âge + décès, bloc historique + filtres
      instantanés + année + tooltips, non-régressions bannière/scroll/
      GSM/boutons) + 23/23 tests cœur.

### Fait en V182 (retours du 18/10 soir — bouton, friction, fond Aston, filtres globaux, frise, info-bulle)
- [x] 🔘 BOUTON « D'AUTRES SUGGESTIONS » : FOND et BORDURE TRANSPARENTS
      au repos (retour : « plus sombre que les autres, persuadé qu'il y
      a un autre contenu en dessous » — le verre du bouton se
      superposait au verre du cadre = double couche sombre). Au repos le
      bouton ne peint plus rien ; au survol il s'allume comme les autres
      (« parfait » selon le retour). Bas de fiche film RESSERRÉ
      (padding 10 → 2 px — retour : « un tout petit espace vide »).
      Prouvé : fond rgba(0,0,0,0), bordure transparente, dBottom 1 px.
- [x] ⚡ PASTILLE FRICTION RETIRÉE des tuiles MÊME ESPRIT (retour :
      « n'apporte rien d'intéressant et prend de l'espace à l'écran
      pour rien »).
- [x] 🎨 FICHE ACTEUR : fond de TOUTE la fiche aux COULEURS ASTON
      (retour : « le fond semble neutre, je vois mes couleurs
      uniquement dans l'en-tête ») — dégradé vert Aston (0,82,75) en
      haut, fondu vers le sombre. Prouvé : backgroundImage du cadre.
- [x] 🎛️ RADIOS GLOBAUX (retour : « films dans tes listes apparait à la
      fois si je coche film, série ou tout — ce n'est pas logique ») :
      les filtres acteur/réalisateur et Films/Séries/Tout s'appliquent
      désormais à TOUTE la fiche — historique, « dans tes listes » et
      « À découvrir ». Prouvé : clic Séries → historique (films) ET
      « Films dans tes listes » disparaissent ; clic Tout → tout revient.
- [x] 📜 HISTORIQUE sur UNE SEULE LIGNE (retour : « 1 année = 1 ligne me
      rallonge la fiche d'autant ») : frise chronologique CROISSANTE —
      premier visionnage à gauche, dernières découvertes à droite (la
      saga garde son ordre : BTTF1 le 25/12/25 puis BTTF2 le 01/01/26,
      retour utilisateur). Chaque carte indique « 📅 vu en YYYY ».
      Prouvé : une seule section, premier badge « Vu le 01/07/2026 »
      (date la plus ancienne = début de frise).
- [x] 💬 INFO-BULLE « Vu le … » RÉPARÉE (retour : « j'ai un ? qui
      apparait ») : le curseur ? venait de cursor:help mais la BULLE
      CSS était ROGNÉE par le bandeau défilant (overflow-x:auto rogne
      aussi en Y — même cause que la heatmap V150). Solution : attribut
      TITLE natif du navigateur (impossible à rogner) en plus du
      data-tooltip. Prouvé : title « Vu le 01/07/2026 » sur le badge.
- [x] Banc : 12/12 + 23/23 tests cœur.

### Fait en V183 (retours du 18/10 soir — titre original TMDB, bouton, frise, info-bulle)
- [x] 🔎 MÊME ESPRIT — RECHERCHE PAR TITRE ORIGINAL (retour : « le
      principal problème des contenus TMDB non trouvés est que le film
      est recherché en version française » — ex. « Les 12 Travaux
      d'Hercule » introuvable, le titre original trouvé) : l'IA fournit
      désormais le TITRE ORIGINAL de chaque proposition (pop_engine) ;
      la recherche l'essaie EN PREMIER puis le titre français — le
      résultat revient toujours avec TITRE et POSTER FRANÇAIS
      (language=fr-FR). Prouvé au banc : tuile au titre français
      volontairement inconnu de l'index → résolue via son original.
- [x] 🔘 BOUTON « D'AUTRES SUGGESTIONS » : DÉLIMITÉ sans assombrir
      (retour : « il n'y a pas de bouton délimité, sauf en
      surbrillance ») : un voile BLANC très léger + un filet discret en
      haut — plus de verre sombre empilé sur celui du cadre.
- [x] 🎨 FICHE ACTEUR : dégradé Aston à ARRÊTS EN PIXELS (retour : « la
      fiche grandit ou rapetisse au changement de radio — effet
      clignotant ») : le haut de la fiche reste IDENTIQUE quelle que
      soit la hauteur (seul le bas couleur unie s'allonge, invisible) ;
      + halo radial vert en tête de fiche (esthétique).
- [x] 📜 FRISE HISTORIQUE : l'année de visionnage affichée UNE SEULE
      FOIS EN GRAS, avec un SEGMENT coloré sous les contenus de l'année
      (retour : « plutôt que de répéter les années sous chaque
      contenu ») + bouton radio ⬆️ Croissant / ⬇️ Décroissant (retour :
      « mettre un autre bouton radio pour le tri »). Prouvé : 5
      segments, « 2026 » une fois, inversion exacte au clic.
- [x] 💬 INFO-BULLE « Vu le … » : la bulle STYLÉE s'affiche enfin —
     Cause racine (pas le bandeau !) : le badge avait overflow:hidden
      (ellipsis des longs noms de listes) → sa PROPRE bulle au-dessus
      de lui était ROGNÉE (prouvé au banc : opacity 1 mais pixels =
      fond de fiche). Fix : overflow:visible pour les badges à bulle ;
      title natif retiré (plus de double bulle décalée d'une seconde).
      Prouvé : 556 pixels de texte + 504 de bord jaune au survol.
- [x] Banc : 13/13 + 23/23 tests cœur. ATTENTION : pop_engine.py change
      aussi cette version (champ original dans le prompt MÊME ESPRIT).

### Fait en V184 (retours du 18/10 nuit — bouton, dégradé, rail, info-bulle)
- [x] 🔘 BOUTON « D'AUTRES SUGGESTIONS » : au SURVOL, exactement les
      couleurs des autres boutons « Une autre… » (retour : « la couleur
      n'est pas la même — pourquoi ne pas copier-coller un autre
      bouton ? ») : c'est fait — les déclarations :hover des autres
      boutons sont copiées telles quelles, portées par un sélecteur
      aussi spécifique que ma règle de repos (qui les écrasait).
      Prouvé : fond accent-soft, texte blanc, bord accent au survol.
- [x] 🎨 DÉGRADÉ ACTEUR : fondu BEAUCOUP PLUS LENT (retour : « tu passes
      très vite du vert au noir, le bas de la fiche est totalement
      noir ») : le vert Aston s'étire sur 2200 px. Prouvé au pixel :
      (1,57,51) à 1250 px de hauteur — toujours vert profond.
- [x] 📜 RAIL CONTINU (retour : « un segment continu qui court en
      dessous et le long des contenus, des traits qui indiquent le début
      et la fin d'une année, l'année centrée sur son segment, plus
      neutre ») : une PIÈCE par colonne (elle DÉFILE avec les cartes),
      la ligne se prolonge dans les interstices → rail continu, traits
      verticaux aux bornes de chaque année, année centrée sur la colonne
      du milieu en style neutre (texte doux, pas de jaune gras). FINI
      le trait jaune-vert sous chaque poster (retour : « de trop, ça
      fait tache »). Prouvé : 5 pièces/5 colonnes, ticks, année centrée
      à 0 px près.
- [x] 💬 INFO-BULLE (retours) : plus de curseur « ? » (cursor:default —
      le « ? » de Chrome venait de cursor:help), fond OPAQUE
      rgb(7,19,17) (on voyait la pastille à travers — réglé en battant
      la règle partagée par la spécificité), et ancrage AU BORD pour
      les 1ers contenus (la solution heatmap : l'info-bulle part du
      bord de la colonne vers l'intérieur, plus de rognage à gauche ;
      idem à droite pour les derniers). Prouvé : left 0px, fond opaque,
      596 pixels de texte visibles sur la 1re carte.
- [x] Banc : 9/9 + 23/23 tests cœur.

### Fait en V185 (retours du 19/10 — frise, bulle, CASTING cliquable)
- [x] 📜 FRISE — MARQUEURS D'ANNÉE (retour : « l'année cachée par la
      rubrique plus basse, pas centrée, le segment se lève au survol —
      as-tu une idée qui fasse propre ? ») : FINI le rail sous les
      cartes. Chaque groupe d'année est PRÉCÉDÉ d'une colonne MARQUEUR —
      un TRAIT VERTICAL pleine hauteur (la borne de l'année) et l'année
      centrée dedans, à mi-hauteur des posters. Colonne SÉPARÉE des
      cartes : jamais levée au survol, jamais recouverte, elle défile
      AVEC le bandeau. Prouvé : année à 10 px de la mi-hauteur des
      posters, aucune pièce sous les cartes.
- [x] 💬 INFO-BULLE : fond OPAQUE BLINDÉ (retour : « le fond est
      complètement transparent, teste l'info-bulle ») — background avec
      !important (aucune règle ne peut le ravaler) + ombre qui détache
      la bulle. Prouvé : rgb(10,26,23) calculé.
- [x] 🎭 CASTING CLIQUABLE (la variante demandée) : cliquer une personne
      du casting d'une fiche film → SA fiche acteur ; refermée, la
      FICHE FILM revient (miroir exact du flux filmographie : acteur →
      film → retour acteur). Le casting devient un BANDEAU DÉFILANT de
      cartes cliquables (calque transparent V175, réalisateur en tête),
      aligné comme les autres bandeaux ; les liens TMDB externes sont
      remplacés par la fiche intégrée. Mécanisme : drapeau
      _msl_casting_person + callback on_dismiss sur la fiche acteur +
      retour via _msl_return_to_fiche (heartbeat rafraîchi, la fiche
      revient à l'endroit où elle était). Prouvé : clic Denis
      Villeneuve → sa fiche ; fermeture → la fiche The Fall revient ;
      puis navigation fiche→fiche toujours en haut.
- [x] Banc : 10/10 + 23/23 tests cœur. (Leçon ré-confirmée : redémarrer
      le harnais AVANT chaque banc complet — un harnais épuisé fait
      échouer des clics qui marchent.)

### Fait en V186 (retours du 19/10 — gros chantier fiche acteur + fixes)
- [x] 🚨 FIX StreamlitDuplicateElementKey (erreur production) : un
      réalisateur figurant AUSSI dans le casting générait deux fois la
      clé castnav_ → DÉDOUBLONNAGE par personne (le réalisateur, en
      tête, prime) + clé indexée. Prouvé au banc avec un réalisateur
      volontairement doublé dans le cast : 1 seule carte, 0 exception.
- [x] 🎛️ RADIOS → SEGMENTS ASSEMBLÉS (« pièces de puzzle », retour avec
      3 images IA) : pastilles JOINTES en une seule tuile (rayons aux
      extrémités, gap 0), seule la sélection s'allume, hover léger.
      + FUSION demandée : facette TOUT (union DÉDUPLIQUÉE — un film
      réalisé ET interprété = 1 contenu dans « tout ») avec COMPTEURS
      de contenus vus par segment (Acteur · n / Réal. · n / Tout · n,
      suivant le type choisi). + UNE SEULE RANGÉE (facette | type |
      tri) — le tri n'est plus « en plein milieu d'un espace vide ».
      Prouvé : segments joints, compteurs exacts, TOUT = 2 contenus
      (pas 3).
- [x] 📜 MARQUEURS D'ANNÉE : NOMBRE de contenus vus SOUS l'année
      (« 2026 / 5 vus »), selon le type choisi (retour utilisateur).
- [x] 💬 INFO-BULLE AU PREMIER PLAN (retour : « les noms des films
      sont au 1er plan, les info-bulles derrière » — diagnostic
      utilisateur EXACT) : la carte survolée passe AU-DESSUS de ses
      voisines (z-60) pendant que sa bulle est ouverte. Prouvé :
      z-index 60 calculé au survol.
- [x] ✨ EN-TÊTE ACTEUR : BANDEAU BISEAUTÉ Aston en CSS
      (repeating-linear-gradient ANIMÉ — défilement lent, vert Aston
      pas vert lime) + HALO GLASS en haut à gauche (retours).
- [x] 📖 BIO : encadré NOIR CARBONE légèrement transparent
      rgba(9,13,12,.66), liseré jaune 3 px, icône de citation ❝
      jaune grasse et visible (retour utilisateur).
- [x] ⏳ SPINNER DE CHARGEMENT pendant les appels TMDB de la fiche
      acteur (retour : « radios déformées 2-3 s le temps des données
      TMDB ») : le dialog affiche « 🎭 Chargement de la fiche… » au
      lieu d'un vide. Prouvé : stSpinner visible pendant le chargement
      (personne lente simulée), puis la fiche.
- [x] 🎭 CASTING : SURVOL D'ORIGINE restauré (retour : « avant c'était
      parfait ») : la PHOTO s'anime (soulèvement + halo + liseré jaune)
      et le NOM passe en blanc — plus de lift de la carte entière.
- [x] Banc : 12/12 + 23/23 tests cœur.

### Fait en V187 (retours du 19-20/10 — VITESSE, ordre restauré, esthétique)
- [x] 🚨 FIX NameError production (multi_facets utilisé par la facette
      TOUT mais supprimé en V182 — le banc ne l'avait pas vu : la frise
      rend AVANT le crash ; leçon : contrôler les exceptions dans
      CHAQUE section du banc).
- [x] ⚡ VITESSE — LE GROS MORCEAU (retour : « je veux de la vitesse —
      les infos IA sont un nice to have, ça doit se faire
      silencieusement ») : les 4 sections IA (coulisses, pourquoi,
      esprit, même esprit, parcours) ne BLOQUENT PLUS le rendu —
      placeholder discret + fragment auto-pollé (1,5 s) ; dès que le
      précalcul est prêt : la donnée est posée en session + UN rerun
      global (garde anti-boucle) → le corps re-rend la section en
      direct. Les radios et les clics restent INSTANTANÉS pendant tout
      le chargement. Deux pièges trouvés et corrigés au banc : le rerun
      du poll devait rafraîchir le heartbeat de la fiche film ET les
      fiches ouvertes par BOUTON n'avaient pas link_mode (le poll les
      fermait !) ; la fiche ACTEUR bat désormais aussi le cœur
      (_msl_actor_open, rouverte par le main < 8 s). Prouvé : fiche
      interactive pendant l'IA, contenu arrivé, fiche conservée, 0
      exception.
- [x] 📽️ ORDRE D'ORIGINE DE LA FICHE FILM RESTAURÉ (retour : « avant
      j'avais distribution après synopsis, puis la saison, la heatmap
      puis similaire — reprends la précédente disposition ») : synopsis
      → Distribution (cliquable) → Saisons + heatmap (alignées sur la
      colonne d'infos) → Saga → Similaires. Prouvé : positions
      verticales dans l'ordre exact.
- [x] 🎛️ SEGMENTS PLUS MODERNES (retour : « un peu plus moderne ») :
      rail creux encastré + pastilles flottantes, transition douce.
      DÉFAUTS : Tout / Tout / Croissant (retour : toujours 1 option
      choisie, « tout » par défaut). Prouvé : Tout coché d'office,
      rail creux, pastille pleine sans bordure.
- [x] 📜 ASCENSEUR de la frise sur PC (fin, vert Aston, seulement si
      débordement) ; GSM : scroll tactile natif. Prouvu :
      scrollbar-width thin.
- [x] 💬 INFO-BULLES : fond OPAQUE pour TOUTES les bulles (la règle
      partagée passait rgba(0,0,0,.95) → on voyait le contenu à
      travers) + les TUILES passent au premier plan au survol.
- [x] ✨ RUBAN « comète » AU-DESSUS de l'en-tête (retour : « je le
      voulais derrière l'entête et au dessus, l'entête comme avant ») :
      filet défilant Aston au-dessus, l'en-tête revient à son look V185
      (plus de biseaux ni de halo dedans). Prouvé : ruban animé
      au-dessus, ::before/::after de l'en-tête vides.
- [x] 📖 BIO : l'icône ❝ vit dans sa PROPRE colonne (plus de
      superposition avec le texte — padding-left 2,35rem). Prouvu :
      37,6px calculés.
- [x] 🎭 CASTING : le survol FONCTIONNE (retour : « ça reste
      statique ») — cause : le CALQUE intercepte le pointeur, le :hover
      de la carte ne se déclençait jamais ; le sélecteur part du
      bouton survolé (technique V175). Prouvé : photo scale(1.05) +
      translateY(-3) + halo.
- [x] Banc : U1-U9 validés (2 en passes ciblées — le harnais dégradé
      fermait la fiche pendant les longues attentes IA) + 23/23 tests
      cœur.

### Fait en V188 (retours du 20/10 — fix navigation, comète, esthétique)
- [x] 🚨 FIX NAVIGATION ACTEUR → FILM (retour : « le clic sur une fiche
      film depuis une fiche acteur ne donne rien ; il faut quitter la
      fiche acteur, parfois changer d'onglet ; en quittant le film,
      la fiche acteur revient alors que je l'avais fermée ») : le cœur
      V187 de la fiche acteur (mimic < 8 s) passait AVANT la branche
      fiche film dans le main → il ROUVRAIT l'acteur et le film posé
      n'était jamais rendu. Désormais la fiche acteur CÈDE LA PLACE :
      son cœur est éteint au clic (comme son on_dismiss). Le MIROIR
      V176 est conservé : fermer la fiche film retrouve la fiche
      acteur. Prouvé : clic film → fiche film ouverte, acteur disparu,
      fermeture → retour acteur, 0 exception.
- [x] 🎛️ DÉFAUT DU RADIO TYPE (retour : « film/série/tout semble réglé
      par défaut sur film, je veux tout ») : comme la facette en V187,
      la valeur « tout » est posée en session AVANT le premier rendu du
      widget — sinon l'option 0 (« films ») était prise. Tri : défaut
      « croissant » posé explicitement. Prouvé : Tout / Tout /
      Croissant.
- [x] 🎛️ SEGMENTS : PASTILLE PLEINE HAUTEUR (retour : « agrandis la
      pastille, qu'elle ait la même hauteur que le rail creux ») :
      labels étirés sur toute la hauteur intérieure du rail (align-
      items:stretch + centrage du texte) + polish (liseré hairline,
      glow, transition 0,18 s). Prouvé : rail 40 px, pastille 32 px =
      intérieur exact (écart 0).
- [x] 📜 FRISE : TRAITS D'ANNÉE SOUS LES INFO-BULLES (retour : « il ne
      reste que les traits entre les années qui passent encore au-
      dessus de l'info-bulle ») : le marqueur est posé au plan 0 — la
      carte survolée (z-index 60) repasse devant, bulle comprise.
- [x] ✨ COMÈTE PLEIN EN-TÊTE (retour : « qu'elle démarre au 1er pixel
      en haut de la fiche, dégradé vers transparent, 100 % transparent
      au bas de l'en-tête ; le raccord du biseau doit être parfait ») :
      plus de ruban séparé — une couche .actor-comet couvre TOUT
      l'en-tête (masque vertical opaque → transparent), DERRIÈRE le
      contenu (.actor-head-in). RACCORD PARFAIT : la période du motif
      vaut 45,2548 px = 64 px/√2 — sa projection horizontale fait
      EXACTEMENT 64 px et l'animation déplace le fond de 64 px par
      cycle → le motif coïncide au pixel près à chaque boucle
      (l'ancien ruban glissait de 544 px = 40,24 périodes → la
      « petouille »).
- [x] 🔮 HALO « CLEAR GLASS » en haut à gauche de l'en-tête acteur
      (retour : « je ne vois pas de halo/clear glass, sais-tu le
      faire ? ») : reflet vitreux radial blanc doux (::after).
- [x] 📖 BIO : les 3 PHRASES dans l'encadré (retour : « tu as juste la
      1ère des 3 phrases ») : st.markdown PARSE le HTML en blocs — un
      double retour à la ligne FERMAIT le <p> et les phrases suivantes
      sortaient de l'encadré. Les paragraphes sont joints par <br><br>.
- [x] 📽️ GAP synopsis → Distribution RESSERRÉ (retour : « un plus gros
      gap qu'avant ») : le titre vit dans son propre bloc markdown
      depuis V187 → il cumulait le gap Streamlit inter-blocs + sa
      marge. Recalé (conteneur -0,15 rem + titre 0,6 rem). Prouvé :
      23,6 px mesurés (≈ l'écart d'avant).
- [x] 📱 GSM : CASTING À GAUCHE (retour : « un gros espace entre
      l'extrême gauche de la fiche et le réalisateur, ce n'est pas
      acceptable ») : le spacer 14 % (min-width 90 px !) du bandeau
      n'était pas masqué sur mobile — corrigé : la distribution
      commence à la marge interne du dialog. Prouvé : 16,8 px du bord.
- [x] ✨ ANIMATION D'ENTRÉE DES FICHES (idée esthétique) : la fiche
      apparaît en fondu + léger glissement (0,42 s). Posée par le
      composant invisible de tête de fiche UNIQUEMENT au changement de
      son marqueur (nouvelle fiche) — jamais pendant les polls IA
      (l'iframe ne recharge pas son script). Prouvé : animationstart
      compté 1× à l'ouverture, toujours 1 après les polls.
- [x] 🔢 COMPTEURS DE LA FRISE habillés (idée esthétique) : pastille
      pilule carbone, liseré vert doux, chiffre en blanc gras.
- [x] Banc : passe A 18/18 + passe B 5/5 (passes ciblées sur harnais
      frais — le harnais dégradé détache les boutons pendant les
      re-rendus IA) + 23/23 tests cœur. Deux infidélités du HARNAIS
      corrigées au passage (le handler de fermeture ne popait pas le
      cœur acteur ; le mimic n'avait pas le retour-acteur immédiat du
      vrai main) — l'app réelle était correcte.

### Fait en V189 (retours du 20/10 — comète en arrière-plan, alignements, ordre GSM)
- [x] ✨ COMÈTE EN ARRIÈRE-PLAN + EN-TÊTE V187 RESTAURÉ (retour : « remets
      mon en-tête comme la version précédente ; une comète VERT ASTON
      qui commence à fleur de la fiche tout en haut, en dégradé
      transparent jusqu'au bas de l'en-tête, mais TOUJOURS en
      arrière-plan ») : l'en-tête revient À L'IDENTIQUE de la V187 ; la
      comète (couleurs V187 : vert Aston translucide, biseaux 115°) est
      une couche z-index:-1 DANS le bloc markdown de l'en-tête — le
      composant invisible de tête de fiche MESURE sa géométrie
      (--msl-comet-top / --msl-comet-h) : elle part du 1er pixel du
      dialog et s'arrête au bas de l'en-tête, passant derrière l'en-tête
      ET les sections, devant le fond. RACCORD PARFAIT : période
      32,6271px = 36px×sin(115°) → projection horizontale de 36px PILE,
      animation de 576px/cycle (16 périodes). Prouvé : comète à 1px du
      haut, à 2px du bas de l'en-tête, z-index -1.
- [x] 📽️ GAP synopsis → Distribution ENCORE RESSERRÉ (retour : « encore
      pire qu'avant ! ») : conteneur -0,55rem + titre sans marge haute +
      padding du bandeau réduit. Prouvé : 7,9px (≈ le compact d'avant
      V187).
- [x] 📱 GSM : CASTING ALIGNÉ SUR LE SYNOPSIS (retour : « je veux que le
      casting commence au même niveau que le synopsis, tout aligné ») :
      spacer 14% masqué + padding .95rem. Prouvé : carte 32,2px =
      synopsis 32,2px, écart 0.
- [x] 🎛️ PASTILLE 40px (retour : « tu saurais l'augmenter ? 40px par
      exemple ? ») : min-height 40px. Prouvé : rail 48px, pastille
      40px, écart 0.
- [x] 💬 INFO-BULLE au-devant de TOUT (retour : « je vois encore le
      trait de l'année dans l'info-bulle et du texte derrière ») : la
      COLONNE de la carte survolée monte au plan 60 (le z-index de la
      carte seule ne suffisait pas — les conteneurs Streamlit créent
      leurs propres contextes d'empilement). Prouvé : colonne z=60 au
      survol + capture pixel : la zone de la bulle s'assombrit de
      12,4% (bulle opaque rgb(10,26,23) peinte au-dessus). NB :
      elementFromPoint ignore les pseudo-éléments — preuve par pixel.
- [x] 📖 BIO : ❝ EN HAUT alignée sur la 1re ligne (retour : « l'icône
      est devenue moche ») + espace inter-paragraphes RÉDUIT (retour :
      « le saut de ligne est trop marqué ») : <br class="bio-sep">
      stylé en bloc, marge 0,3rem (~5px au lieu de ~20px). Prouvé :
      ❝ top 8,8px, 2 séparateurs display:block.
- [x] 🔢 TOP ACTEURS GSM : ORDRE CORRIGÉ (retour : « sur GSM il y a des
      sauts : 12, 11, 12, 10, 11 ») : les colonnes étaient créées UNE
      fois puis remplies en round-robin (col 1 = items 1, 6, 11…) —
      sur GSM elles s'empilaient en 1, 6, 11, 2, 7… Désormais UNE
      RANGÉE de colonnes par ligne : l'ordre est conservé sur PC ET
      l'empilement mobile lit 1, 2, 3, 4, 5, 6. Prouvé : ordre DOM
      P1→P6 en PC ET en contexte mobile.
- [x] 🎭 FICHE ACTEUR VIA CASTING : ROBUSTESSE (retour : « l'encadré
      d'infos n'apparaît que pour mes acteurs du top 10, pas sur les
      fiches ouvertes depuis une fiche film ») : cause — un appel TMDB
      frais (surcharge 429, réseau) faisait ABANDONNER toute la fiche
      (les top, eux, sont en cache serveur). Désormais : 2 essais
      espacés + la fiche VIT sans détails TMDB (en-tête au nom du
      casting + bandeau discret + filmo locale). Prouvé : membre
      « fetch KO » → fiche avec nom du casting + bandeau, 0 exception.
- [x] Banc : passe A 19/19 + passe B 6/6 (passes ciblées sur harnais
      frais) + 23/23 tests cœur.

### Fait en V190 (retours du 20-21/10 — comète annulée, Distribution standard, pastille 40/40)
- [x] ✨ COMÈTE ANNULÉE (retour : « annule tout ce que tu as fait
      concernant la comète dans la fiche acteur, ça ne va pas, on va
      laisser sans comète ») : couche, CSS, keyframes et JS de mesure
      retirés. L'en-tête acteur reste à l'identique de la V187. Prouvé :
      plus de .actor-comet, dégradé d'origine présent.
- [x] 📽️ DISTRIBUTION : RETOUR AUX ÉCARTS STANDARD (retour : « je veux
      la disposition d'avant avec les fonctionnalités de maintenant —
      le même écart entre chaque fin et chaque début de widget ») : le
      titre avait DISPARU (la marge négative V189 le remontait SOUS le
      bloc du synopsis, et les cercles étaient tronqués au survol).
      Toutes les marges spéciales sont ANNULÉES : le titre porte les
      marges standard .cinema-section-title (comme Saisons/Similaires)
      et le bandeau retrouve le padding des autres bandeaux. Prouvé :
      titre visible, gap synopsis→titre 17px, titre→bandeau 6px,
      padding 7,2px, cercles à 3px du bord au survol (non tronqués).
      GSM inchangé (validé à nouveau : écart 0 avec le synopsis).
- [x] 🎛️ PASTILLE : rail 40px ET pastille 40px (retour : « je veux que
      le rail reste à 40px et que la pastille fasse aussi 40px pour la
      remplir entièrement ») : les labels débordent le padding du rail
      (margin -4px vertical) → la pastille couvre le rail BORD À BORD,
      le rail ne reste visible que comme un liseré. Prouvé : rail 40px,
      pastille 40px, couverture haute 0,0px / basse 0,0px.
- [x] 📖 BIO : ❝ AGRANDIE (retour : « tu peux augmenter la taille de
      ❝ si tu veux ») : 1,62rem (≈26px). Prouvé : 25,92px calculés.
- [x] 🔮 HALO DE LUMIÈRE au coin haut-gauche HYPER VISIBLE (retour :
      « est-ce possible de le faire partir du coin en haut à gauche de
      manière hyper visible ? comme un halo de lumière ? ») : double
      radial ancré PILE au coin (0% 0%), blanc à 55 % au centre. Prouvé :
      radial .55 présent sur le ::after de l'en-tête.
- [x] 🎭 ENCADRÉ TOP 10 (retour : « les encadrés ne fonctionnent pas
      pour les acteurs qui ne font pas partie de mon top 10, tanpi ») :
      aucun retrait — le filet de sécurité V189 reste (2 essais TMDB +
      fiche vivante au nom du casting si l'API ne répond pas).
- [x] Banc : passe PC 10/10 + passe GSM 2/2 + 23/23 tests cœur.

### Fait en V191 (retours du 21/10 — Distribution adaptative, en-tête verre futuriste)
- [x] 📽️ DISTRIBUTION ADAPTATIVE (retour : « l'écart entre le bas du
      synopsis et le début de la distribution est vraiment énorme — ou
      le problème vient que tu commences distribution juste après le
      bas du poster ? » — EXACTEMENT ça) : le bloc markdown fait la
      hauteur du POSTER, plus haut que le texte quand le synopsis est
      court. Le composant invisible de tête de fiche mesure EN
      PERMANENCE (800 ms) l'écart réel texte→titre et pose
      --msl-cast-lift : le conteneur du titre remonte d'autant → la
      Distribution démarre sous le SYNOPTIQUE avec l'écart classique
      (~17 px), même après un chargement tardif de l'affiche. Sur GSM
      (layout empilé), l'écart est déjà nominal → rien ne bouge.
      Prouvé : cas nominal écart 17 px ; poster artificiellement
      agrandi de 100 px → écart ramené à 18 px (lift 123 px posé).
- [x] 📺 SAISONS : couleur d'accentuation RESTAURÉE (retour : « n'est
      plus en couleur d'accentuation ») : le titre n'avait jamais eu la
      classe cinema-strip-title que Saga/Similaires/Distribution ont.
      Prouvé : même couleur que Similaires, plus le jaune standard.
- [x] 🎛️ PASTILLE : TOUT À 40px SANS LISERÉ (retour : « je veux le rail
      en 38 et la pastille en 40 — je ne veux plus voir le fin liseré
      lorsque le bouton est actif ; si tu sais l'enlever en mettant
      tout à 40px alors je prend ») : fait à 40/40 — hauteur du rail
      et des labels à 40 px, liseré du rail en inset-shadow couvert
      par la pastille sur tout son passage (l'input radio de baseWeb,
      qui faisait 36 px et étirait tout, est réduit à 16 px). Prouvé :
      rail 40, pastille 40, couverture 0/0.
- [x] 📖 ❝ ENCORE AGRANDIE (retour : « tu peux l'agrandir encore un
      peu ») : 1,9 rem (30,4 px calculés).
- [x] 🔮 EN-TÊTE « VERRE FUTURISTE » selon la description TRÈS précise
      de l'utilisateur : fond vert pétrole #003F3C non uniforme
      (dégradé vers #002E2D), rayon 18 px ; HALO TURQUOISE diffus au
      coin SUPÉRIEUR GAUCHE (cœur rgba(0,240,220,.30) → vert canard →
      fond, transitions douces — la signature visuelle) ; BORDURE fine
      dégradée par masque (turquoise lumineux au coin, #168A80
      translucide ailleurs) + léger halo externe ; 3 lignes diagonales
      très fines (reflets de verre secondaires) ; photo + informations
      DEVANT tous les effets (z-index 3) ; pas d'animation permanente.
      L'ancien halo blanc est EFFACÉ. Prouvé : fond rgb(0,63,60),
      halo rgba(0,240,220,.3), bordure mask-composite exclude,
      photo z-index 3, plus de radial blanc.
- [x] Banc : passe PC 13/13 + passe GSM 2/2 + 23/23 tests cœur.

### Fait en V192 (retours du 21/10 — lift annulé, saisons, pastille opaque, en-tête Aston)
- [x] 📽️ DISTRIBUTION : LIFT ANNULÉ, REMIS COMME AVANT (retour : « ta
      solution fait remonter le TITRE mais pas la distribution ni les
      widgets suivants — l'espace énorme se déplace du titre à la vraie
      distribution. Au final remets comme ce qui était avant, avec le
      titre distribution visible puis à un écart très acceptable la
      distribution ») : règle CSS, mesureur JS et classe --dist
      retirés. DIAGNOSTIC UTILISATEUR (juste) : le vide vient du bloc
      « Pourquoi ce score ? » présent au-dessus du synopsis dans « Que
      regarder ? » mais absent des fiches ouvertes ailleurs — sans lui
      le texte est plus court que le poster. Prouvé : marge du
      conteneur neutre, titre visible, bandeau à 6px sous le titre.
- [x] 📺 SAISONS : écart posters→heatmap RÉDUIT (retour : « l'écart
      est trop grand entre les posters de la saison et le début de la
      heatmap ») : le padding-top de la heatmap (réservé aux
      info-bulles des cellules) passe de 3,2rem (51px) à 1,9rem
      (30px) — les bulles gardent juste la place qu'il faut. Prouvé :
      30,4px calculés.
- [x] 🎛️ PASTILLE : OPAQUE + 42px (retour : « j'arrive encore à voir
      un peu du rail DERRIÈRE la pastille — enlève 1-2px au rail ou
      mets 1-2px en plus sur la pastille ») : la cause était la
      TRANSLUCIDITÉ (le dégradé à 66-88 % laissait voir le fond du
      rail à travers) → dégradé OPAQUE (.90/.97) + pastille 42px qui
      déborde du rail de 2px. Prouvé : 42px, déborde 0px haut / 2px
      bas, fond opaque.
- [x] 🔮 EN-TÊTE : COULEURS ASTON (retour : « inspire-toi surtout de
      mes couleurs Aston Martin — je veux bien un fondu mais moins
      prononcé ») : base #00524B (vert foncé Aston) avec un voile
      dégradé DOUX ; BORDURE ENCORE PLUS LUMINEUSE (coin .95) + glow
      externe 24px turquoise (retour : « effet de halo/lumière en plus
      de la bordure ») ; les 3 LIGNES DIAGONALES RETIRÉES (demande
      explicite). Prouvé : fond rgb(0,82,75), radial seul, bordure
      .95, glow, photo z-index 3.
- [x] Banc : passe PC 12/12 + passe GSM 2/2 + 23/23 tests cœur.

### Fait en V193 (retours du 21/10 — pastille extrémités, saisons, en-tête glow, README)
- [x] 🎛️ PASTILLE : RAIL INVISIBLE AUX EXTRÉMITÉS (retour : « on voit le
      rail sur le côté de Tout / Acteur / Film — la pastille du milieu
      est parfaite ; la root cause est l'arrondi différent entre la
      pastille et le rail ») : tout à 40px ; le rail n'a plus de
      padding horizontal (il S'ARRÊTE aux pastilles extrêmes) et les
      labels débordent de 1px de chaque côté → les arrondis de la
      pastille COUVRENT les extrémités du rail. Prouvé : rail 40,
      pastille 40, couverture 0/0, débordement 1px à gauche de la
      1re et à droite de la dernière.
- [x] 📺 SAISONS : heatmap ENCORE resserrée (retour : « tu peux réduire
      encore un peu ») : padding-top 1,9rem → 1,6rem (25,6px) ; et
      écart fin de saisons → Similaires LÉGÈREMENT AGRANDI (retour
      explicite) : padding-bottom .55rem sur le wrap (+8,8px).
- [x] 🔮 EN-TÊTE : un peu PLUS SOMBRE (retour : « plus de contraste
      entre l'en-tête et la fiche ») : base #00524B → #004C48 ; HALO
      RENFORCÉ pour l'effet glow (.30 → .38, diffusion étendue) ;
      BORDURE PLUS LUMINEUSE (coin OPAQUE rgb(0,240,228), corps .70)
      + glow externe 28px/.38.
- [x] 📖 README MIS À JOUR (demande explicite — récupéré du GitHub
      courant d'abord) : lignes 🎲 La Pépite (curateur IA selon
      l'humeur, zéro donnée personnelle) et 🎬 Fiches film & acteur au
      tableau des fonctionnalités ; section « 🎬 Les fiches : ton
      cinéma, en détail » (fiche film : bannière, distribution
      cliquable, saisons + heatmap, TON HISTOIRE, blocs IA ; fiche
      acteur : en-tête Aston, radios, frise, filmographie, note
      moyenne) ; section « 🤖 L'IA, seulement quand elle sert »
      (tableau pépite/dilemme/fiches + précalcul non bloquant) ; les 6
      captures existantes CONSERVÉES + 3 encarts prêts (docs/
      La_pepite.png, Fiche_film.png, Fiche_acteur.png — l'utilisateur
      dépose ses fichiers sous ces noms).
- [x] Banc : passe PC 9/9 + 23/23 tests cœur.

### PROCHAINES ÉTAPES (au choix de l'utilisateur)
- [ ] (facultatif) Score moyen sur la fiche acteur · duo favori stats
- [ ] README : refonte par l'utilisateur À LA FIN (il gère).
      (modélisation proposée : une ligne par série au lieu d'une ligne
      par épisode — titre · N épisodes · temps total · dernière vision ·
      ta note — clic → fiche avec les dates détaillées ; et dans chaque
      fiche d'un contenu VU : dates de visionnage, rewatchs, ta note).
      • « Pourquoi ce score ? » narratif par l'IA dans la fiche (les signaux expliqués en une phrase vivante) ;
      • « Résolveur de dilemme » : 2-3 contenus hésitants → l'IA tranche ;
      • « Après ce film » : depuis la fiche, l'IA propose les 3 suites logiques DANS tes listes ;
      • « Ton soir parfait » : heure + humeur + temps dispo → mini-programme de soirée.
- [ ] Anecdotes IA : à tester en vrai avec la clé de l'utilisateur — si
      « Local » s'affiche encore dans POP, ouvrir le « 🔧 Diagnostic de la
      clé Gemini » et me donner le message.
- [ ] README.md : refonte par l'utilisateur À LA FIN (il gère).
- [x] (fait en V170 — cf. ci-dessus) Ajouter un contenu à une liste / à la
      Watchlist DEPUIS LA FICHE CINÉMA (expander en bas de fiche, exclusions
      intelligentes, listes statiques uniquement).
- [x] (fait en V154 — cf. ci-dessus) Ancienne entrée refonte : onglets : 👁️ Vue d'ensemble / 🎭 Goûts / 👥 Personnes /
      🗓️ Temps — animation de transition + UN seul bloc de filtres partagé
      (recherche + période + type). Les infos par acteur/réalisateur restent
      dans Statistiques (décision utilisateur : c'est le bon endroit).
- [~] Historique PAR SÉRIE : ANNULÉ à la demande de l'utilisateur (15/10) —
      « euhhhh celui la je ne le comprend pas car j'ai déjà ça dans les fiches
      série ». (L'idée : regrouper le tableau Historique & notes — 6 700+
      lignes, une par ÉPISODE — en une ligne par SÉRIE. Redondant avec
      TON HISTOIRE : abandonné.)
- [x] (fait en V167 → affiné V168) Fiche film/série d'un contenu VU → bloc « 📜 TON HISTOIRE ».
- [x] (fait en V170) Fiche acteur → score moyen de ses contenus notés.
- [x] (fait en V170) Stats → « duo favori » (acteur × réalisateur le plus croisé).
- [x] (fait en V172) « Pourquoi maintenant » — héritage culturel.
- [x] (fait en V173) « L'esprit du film » + « Même esprit » + « Son parcours ».
- [ ] Suite IA éventuelle (contrainte : ZÉRO
      lenteur — précalcul comme l'info des coulisses) : « L'esprit du film »
      (3 mots-clés d'ambiance + humeur de visionnage), « Pourquoi maintenant »
      (contexte de sortie), fiche acteur enrichie (anecdote de carrière /
      le rôle qui a tout changé, sans raconter le film).
- [x] (fait en V173) Fiche depuis une fiche : posters Similaires/Saga →
      fiche locale (le titre garde TMDB). Casting : à voir si demandé.
