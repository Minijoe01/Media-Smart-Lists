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
- [x] **Captures d'écran à jour** : le contenu de docs/Dashboard.png, series.png,
      Doublons.png, quoi_regarder.png, statistiques.png a été remplacé par
      l'utilisateur (17/08/2026) — SANS renommer les fichiers.
- [ ] **Partager l'article Alkodiques** sur le portail
      (lesalkodiques.com) — pas encore publié.
- [ ] (Optionnel) Supprimer docs/audit-fichiers-github.xlsx une fois lu.

---

## 🎨 Futur thème « vivant » — idées à retenir (V51+, idée utilisateur)

L'utilisateur a fourni **`docs/preview-look.html`** (enregistré en V51) : il
l'adore et veut que l'app s'en rapproche dans les prochaines versions. Les
patterns CSS viennent aussi de son site sport-auto / worker Cloudflare
(analysé en V51). Rien n'est encore intégré : **les fonctionnalités passent
d'abord**, le thème ensuite, SANS casser l'existant (posters, infos…).

### À reproduire (liste exhaustive des demandes)
- [ ] **Ruban « comet » biseauté** en haut : `clip-path: polygon(21px 0, 100% 0,
      calc(100% - 21px) 100%, 0 100%)` (biseau au début ET à la fin), bandes
      diagonales 115°, `animation: comet 8s linear infinite`.
      **Couleur préférée de l'utilisateur** : vert `rgba(0,163,146,.95)` +
      citron `rgba(206,220,0,.25)` (celle de preview-look.html, PAS le citron
      seul de ma maquette).
- [ ] **Rubans déroulants (widgets) avec une icône devant** : rangée =
      icône dans une tuile (fond dégradé sombre, liseré interne) + titre +
      ligne de méta + chevron ▾. Au survol : tuile en dégradé vert, lueur.
- [ ] **Icônes/cartes en fondu en cascade** (`fadeUp` + `animation-delay`
      croissant ~40 ms) et **surbrillance au survol** (translateY(-3px),
      fond teinté, bordure, ombre lumineuse).
- [ ] **Bandeau de métriques** en haut du tableau de bord (films vus ·
      épisodes vus · temps total · rythme), comme dans preview-look.html.
- [ ] **Wordmark** avec logo-tuile (rectangle arrondi + triangle de lecture +
      point), italique 900 majuscule, halo vert sous le svg.
- [ ] **Swoosh** (trait dégradé) sous le titre + **grain** subtil du fond.
- [ ] **Barre de progression** segmentée en dégradé vert→citron (déjà en
      place sur les cartes contenus, à généraliser).
- [ ] Le thème doit être appliqué sur **TOUS les onglets** (pas seulement le
      dashboard), en reprenant les éléments actuels (posters, liens,
      badges, cartes contenus) avec la mise en forme de preview-look.html.

### Éléments de maquette-animations.html jugés au-dessus (à proposer)
- [ ] **Barre de répartition colorée du créneau** (Matin/Après-midi/Soir/Nuit
      en segments verts/citron) — plus lisible que des % seuls.
- [ ] **Mini-cartes « records »** (jour / mois / série avalée) en 3 colonnes
      avec les gros chiffres citron.

### Rappels techniques
- CSS injecté dans `app.py` (bloc `st.markdown(unsafe_allow_html=True)`) ;
  boutons Streamlit 1.60 : `type="primary"` SANS `help=` ; les expandeurs
  actuels resteront (avec habillage « ruban »).
- Ne pas toucher aux couleurs officielles (#00A392, #00524B, #CEDC00).
- `worker (3).js` (catalogue 1fichier/Kodi de l'utilisateur) : analysé pour
  les patterns, PAS ajouté au dépôt (fichier privé de l'utilisateur).

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
