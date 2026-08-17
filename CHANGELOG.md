# Changelog — Media Smart Lists

Toutes les évolutions notables de Media Smart Lists.

## [V50] — 17 août 2026

- 🧭 **Thermomètre de sévérité affiné à 5 paliers** : ±0,5 pt = « UN PEU sévère/indulgent », ±1,5 pt = « TRÈS sévère/indulgent » (l'ancien site étiquetait « indulgent » dès 0,5 pt — 0,5 pt c'est peu, donc maintenant c'est « 🙂 UN PEU INDULGENT »).
- 🚦 **Nouveau widget « Séries en pause longue »** : séries dont le dernier épisode vu date d'il y a 2 ans ou plus, non abandonnées (dropped) et non terminées/annulées — à reprendre… ou à abandonner ?
- 🔥 **Nouveau widget « Records de binge »** : jour record (nb d'épisodes + série dominante), mois record, série la plus « avalée » en heures.
- 🕰️ **Nouveau widget « Ton créneau préféré »** : répartition matin / après-midi / soir / nuit en % de temps de visionnage.
- 🧭 **Ordre logique des widgets du tableau de bord** : l'action d'abord (sorties → plus ancien watchlist → pauses longues), puis les souvenirs (records → créneau), puis les goûts (coups de cœur → à contre-courant → rewatch radar).
- 📅 **Sorties de la semaine** : corrigées pour l'import ZIP (la date de sortie est maintenant copiée par l'enrichissement MDBList) et **dédoublonnées** (un film n'apparaît qu'une fois, malgré les sources agrégées).
- 🔁 **Rewatch radar dédoublonné pour le ZIP** : dans un ZIP Trakt chaque visionnage est une ligne séparée — un film revu n'apparaît plus plusieurs fois.
- 📏 **Espacement resserré entre les widgets** (séparateurs et expandeurs plus compacts, sans casser le thème).
- 🧪 **6 nouveaux tests unitaires** (13 au total) : thermomètre nuancé, pause longue, records, créneau, rewatch ZIP, sorties dédupliquées.
- 🎨 **Maquette du futur look animé** (`docs/maquette-animations.html` + `docs/maquette-animations.png`) : balayage « comet », entrée en fondu, survol lumineux — à appliquer dans une version ultérieure.

## [V49] — 16 août 2026

- 🕘 Derniers visionnages du tableau de bord : **saison/épisode affichés** (ex. « Silo · S01E05 »).
- 🧭 **Widgets restaurés de Trakt Smart Lists** (0 appel API) : ⭐ coups de cœur (note ≥ 9), 🧭 à contre-courant (thermomètre de sévérité + écarts ≥ 2 pts), 🔁 rewatch radar (1 seule vue il y a ≥ 3 ans, public ≥ 8), 📅 sorties de la semaine, ⏳ plus ancien de la Watchlist — tous en expandeurs repliés.
- 🎬 Analyse acteurs favoris MDBList : pas d'endpoint public (vérifié dans l'OpenAPI) ; « où ai-je vu cet acteur ? » nécessiterait les crédits TMDB (optionnel, coûteux).
- 📱 Cinopsys (tracker Android basé sur Trakt/Simkl) et **Reeel** (l'app mobile officielle MDBList) documentés.

## [V48] — 16 août 2026

- 🧰 Outil CLI de migration intégré dans `scripts/` : `migrate_trakt_zip_to_mdblist.py` (dry-run par défaut, clé MDBLIST_API_KEY, `--apply`, `--check-api`, `--sections`, `--list-layout`), `README-migration-cli.md`, `start_windows.bat` (l'ancien script à la racine est déplacé).
- 📄 README : section « 🧰 Outil CLI (utilisateurs avancés) » ; AI-HANDOFF et TODO mis à jour.

## [V47] — 16 août 2026

- 🔒 `SECURITY.md` (signalement responsable d'une vulnérabilité) et `docs/privacy.md` (politique de confidentialité complète).
- 🧪 Tests unitaires dans `tests/test_core.py` (7 tests) + CI GitHub Actions (`.github/workflows/ci.yml` : compileall + scan secrets + tests).

## [V46] — 16 août 2026

- 📄 README : ligne « 📦 Migration Trakt → MDBList » dans le tableau des fonctionnalités + section « 🚚 Le grand transfert » (5 étapes, mise en garde, simulation recommandée).
- 📰 Guide Alkodiques : section « Et si vous voulez carrément passer à MDBList ? ».

## [V45] — 16 août 2026

- 🚀 **Nouvelle page « 📦 Migration Trakt → MDBList »** (11ᵉ page, menu séparé) : assistant web en 4 étapes (déposer le ZIP → aperçu avec sans-correspondance et mode simulation → sauvegarde JSON + rapport Excel → confirmation → écriture par lots → rapport final 7 onglets). Vraies dates conservées (`watched_at`), listes créées si absentes, jamais d'écriture dans les listes dynamiques.

## [V44] — 15 août 2026

- 🧹 Nettoyage des listes : la description couvre maintenant explicitement les **doublons entre listes** (README) + piste documentée de la migration ZIP → MDBList depuis le site web.

## [V43] — 15 août 2026

- 📄 README : ligne « 🔁 Doublons » retirée du tableau (intégrée à Nettoyage des listes).
- 🖼️ Social card **reproduite fidèlement** de l'originale Trakt (même fond radial, même icône citron, proportions vérifiées pixel par pixel, police Manrope, aucun lien cliquable).

## [V42] — 15 août 2026

- 📄 **README réécrit façon Trakt Smart Lists** : « 🤔 Le problème », tableau Page / Ce qu'elle fait (11 pages), score « Que regarder ? », captures en blocs centrés (`docs/*.png`), tuto ZIP complet, vie privée.
- 🖼️ Social card reconstruite en PIL sur le modèle de l'originale (fond dégradé radial, liseré citron, URL `media-smart-lists.streamlit.app`).

## [V41] — 15 août 2026

- 🖼️ Social card finale : aucun lien cliquable, URL correcte, tagline neutre.
- 📄 README corrigé (« Pour qui » : MDBList prioritaire, ZIP expliqué) ; article Alkodiques plus convivial.

## [V40] — 15 août 2026

- ❓ Guide ZIP Trakt : HTML pur + entièrement jaune citron (plus de balises `**` visibles).
- ✍️ « Marquer vu / non-vu » : recherche par frappe (multiselect) + filtre par type + flux action → confirmation → exécuter.
- 📚 Docs : README (MDBList prioritaire), social card, article Alkodiques réécrit, CI.

## [V39] — 14 août 2026

- 🔴 Déconnexion stabilisée : retour au comportement « toujours connecté » au F5 (toute la mécanique de marqueur `?msl_logged_out=1` est retirée) ; la déconnexion ne vaut que pour la session en cours. Plus de fausse déconnexion au clic « Charger mes données MDBList ».
- ✍️ « Marquer vu / non-vu » repensé : recherche par frappe (multiselect, comme la suppression), filtre par type, flux action → confirmation → exécuter, boutons au thème. Fonctionnalité de note retirée.
- 🗑️ Titres des panneaux de nettoyage liés au « Conteneur à auditer ».
- ❓ Guide ZIP Trakt : HTML pur (fini les `**` visibles) et texte jaune citron.
- 📚 Documentation & qualité : README réécrit (MDBList prioritaire), CHANGELOG, licence MIT, social card régénérée, article Alkodiques, CI GitHub Actions.
- 🧹 Nettoyage du dépôt : liste des fichiers obsolètes à supprimer (Excel d'audit fourni), toutes les ETAPE-* résumées dans ce changelog.

## [V38] — 14 août 2026

- 🔴 **Bug critique corrigé** : plus de fausse déconnexion au clic « Charger mes données MDBList » (retour au comportement « toujours connecté » au rechargement de page ; la déconnexion ne vaut que pour la session en cours).
- ✍️ Panneau « Marquer vu / non-vu » repensé : recherche + filtre par type, flux « choisir une action → confirmer → exécuter », boutons tous au thème. Fonctionnalité de note retirée (les notes MDBList se gèrent côté MDBList).
- 🗑️ Titres des panneaux de nettoyage liés au « Conteneur à auditer » sélectionné.
- ❓ Guide d'import ZIP Trakt plus compact et au thème.
- Tri de la liste des contenus à supprimer par priorité de nettoyage.

## [V37] — 14 août 2026

- Ruban compte/quota MDBList : plus de doublon entre le connecteur et le dashboard.
- Guide pas à pas « Comment obtenir mon ZIP Trakt ? ».
- Suppression sécurisée user-friendly : cases à cocher + actions intelligentes selon les conteneurs (retirer d'une liste précise, de la Watchlist, ou de tous), sauvegarde + confirmation.

## [V36] — 13 août 2026

- Documentation de transmission réécrite (`AI-HANDOFF.md`, `MEDIA-SMART-LISTS-TODO.md`).
- Écritures MDBList v1 : suppression sécurisée d'un contenu d'une liste statique / Watchlist (aperçu → sauvegarde → confirmation → écriture).

## [V35] — 13 août 2026

- Boutons « Charger », « Enrichir », « Quitter » au thème (retrait du `help=` qui cassait le CSS).
- Déconnexion durable via marqueur d'URL (retirée en V38 — voir ci-dessus).

## [V34] — 13 août 2026

- Boutons d'action en `primary` (dégradé vert).
- Renforcement de la déconnexion (cookie écrasé).

## [V33] — 13 août 2026

- Thème unifié des boutons (sélecteurs CSS universels).
- Signaux de recommandation restaurés pour l'import ZIP (votes, pays, certification, statut, studios, date d'ajout).

## [V32] — 9 août 2026

- Statistiques unifiées : un seul jeu de filtres appliqué à toute la page, vue d'ensemble « non filtrée » mentionnée.
- Cache persistant 1 h avec rechargement après F5.

## [V31] — 8 août 2026

- Boutons au thème + bouton « Gérer la connexion » réparé.
- Bascule ZIP ↔ MDBList (« Quitter les données ZIP Trakt »).
- Posters fiables (vérification de cohérence du titre ; enrichissement par IMDb).

## [V30] — 8 août 2026

- Bouton « Charger mes données MDBList » restauré (régression V29).
- Cache persistant 1 h.
- Badge de source clair sur le dashboard.
- Enrichissement ZIP sur tous les contenus (par lots de 200).
- Nettoyage : distinction « Vu · à retirer » / « Vu · à revoir ».

## [V29] — 8 août 2026

- Durées d'épisode corrigées (fini les « 22 ans » de visionnage).
- Import ZIP réparé quand connecté + enrichissement automatique.
- Logigramme du dashboard simplifié (une source à la fois).

## [V28] — 8 août 2026

- Import ZIP Trakt complet : dashboard, en cours, fantôme, que regarder (enrichissement), calendrier local, restauration JSON sans connexion, libellés corrigés, historique des ajouts.

## [V27] — 8 août 2026

- Import ZIP Trakt fonctionnel (sécurisé, rewatches inclus, même modèle que MDBList).
- Export Excel : largeurs auto + onglet « Mes contenus » avec colonne Liste.
- Liens contenus uniformisés (badges).
- Connexion « sans smartphone » : lien direct avec code pré-rempli.

## [V26] — 7 août 2026

- Dashboard enrichi : temps total à vie, répartition séries/films, rythme, compteurs à vie, date de fin projetée.
- Page Sauvegarde : JSON restaurable + rapport Excel multi-onglets.
- Liens JustWatch/TMDB/MDBList ; cartes « En cours » aérées ; « Que regarder » en une carte sous l'autre.

## [V25] — 7 août 2026

- Calendrier : vraie cause corrigée (identifiants MDBList, endpoint batch officiel), panneau de diagnostic.
- Mois triés chronologiquement (blindé) ; barres de progression au thème.
- Page Succès restaurée (61 badges).

## [V24] — 7 août 2026

- Calendrier enrichi (endpoints batch corrigés, retry `favorite_cast`).
- Graphiques sans ascenseurs, tooltips avec unités, heatmap avec info-bulles.
- Page Rendez-vous annuel (Wrapped) restaurée avec image PNG.

## [V23] — 7 août 2026

- Calendrier enrichi par appels groupés (dates futures des contenus).
- Statistiques détaillées façon Trakt Smart Lists (filtres, heatmap, graphiques, ADN, studios, marathons, évolution).
- Barres de progression aux couleurs du thème.

## [V22] — 7 août 2026

- Durée réelle des épisodes corrigée (« Connasse » : 2 min au lieu de 2 h 22).
- Temps global précis (« 7 mois 15 j, 2 h 35 min »).
- Calendrier long (jusqu'à 1 an et demi), épisodes futurs annoncés.

## [V21] — 7 août 2026

- Corrections statistiques : durées intelligentes, runtime des épisodes, historique repliable, calendrier de secours, historique des ajouts.
- Fichiers de transmission IA (AI-HANDOFF, TODO, script de migration).
