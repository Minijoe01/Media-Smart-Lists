# Changelog — Media Smart Lists

Toutes les évolutions notables de Media Smart Lists.

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
