# Media Smart Lists — TODO actif

> Dernière mise à jour : 17 août 2026 · Dernière version déployée : V50.
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

## 🎨 Futur thème « vivant » — PROGRESSION (V52-V56 : rubans ✅ · bandeaux ✅ · valeurs blanches ✅ · cartes contenus premium ✅)

L'utilisateur a validé le principe (« si tu te sens capable d'appliquer le
nouveau skin au site, vas-y, mais fais gaffe à pas tout péter »). Un backup
de l'état V51 existe : `BACKUP-Media-Smart-Lists-V51-avant-skin.zip`
(hors dépôt, dans le workspace). **V53 = uniformisation de tous les onglets**
(le user veut « de la modernité » et « uniformiser tout l'outil »).

### Fait en V52-V56
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

### Reste à faire (idées en attente)
- [ ] Wordmark avec logo-tuile dans le header natif Streamlit (optionnel,
      délicat — à faire prudemment).
- [ ] Avis utilisateur sur la maquette **bandeau jaune** vs **verte**
      (docs/preview-bandeau-jaune.html / preview-bandeau-vert.html) —
      le vert officiel reste la référence.
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
