# Media Smart Lists — Étape 26 : tableau de bord enrichi, sauvegarde Excel, liens, confort

## Tableau de bord : rythme, compteurs à vie, temps de visionnage

Le bloc « Aperçu des possibilités conservées » (qui n'avait plus de sens) a été
remplacé par de vrais widgets, repris de l'ancienne application Trakt Smart
Lists, calculés 100 % localement (aucun appel API) :

- **Métriques temps** dans la vue d'ensemble : ⏱️ Temps total (à vie),
  📺 Temps séries, 🎬 Temps films, 🏃 Épisodes/semaine ;
- **⏱️ Ton rythme de visionnage** :
  - bilan du mois en cours (heures · épisodes · films) ;
  - rythme en épisodes/semaine (fenêtre 90 jours) ;
  - **date de fin projetée** : au rythme actuel, quand tu auras fini les
    épisodes restants de toutes tes séries en cours (Up Next) — les séries
    abandonnées (statut « dropped ») sont explicitement exclues du calcul ;
- **📼 Compteurs à vie** : heures passées sur les séries et sur les films ;
- **🍿 Cette semaine** : digest 7 jours (épisodes, films, durée) ;
- **🕘 Derniers visionnages** : les 5 derniers contenus vus.

## Page Sauvegarde (dernière page legacy)

La page « 📤 Sauvegarde » est désormais fonctionnelle :

- **Sauvegarde JSON** : export neutre et versionné du dataset normalisé
  (historique, Watchlist, listes, notes, progressions) — restaurable depuis
  la même page, sans nouvelle analyse ;
- **Rapport Excel multi-onglets** : un classeur avec un onglet par analyse
  (Résumé, Historique, Watchlist, Listes, Statistiques, Badges), entêtes
  verts et tableaux striés, comme dans Trakt Smart Lists ;
- aucun secret ni jeton n'est jamais inclus dans les exports.

## Calendrier : erreur du service officiel enfin visible

L'endpoint `/calendar/events` n'est pas documenté publiquement par MDBList.
Le code essaie désormais plusieurs combinaisons de paramètres (avec/sans
`favorite_cast`, `append_to_response`, `limit`) et, si tout échoue, le message
d'erreur exact (ex. « MDBList a répondu HTTP 4xx ») s'affiche dans le panneau
« 🔍 Pourquoi ce calendrier… ». Ce sera la clé pour diagnostiquer pourquoi les
dates d'épisodes individuels ne remontent pas depuis le calendrier officiel.
En attendant, le calendrier fusionne les dates connues localement
(Up Next + listes) et les sorties futures des films/séries de vos listes.

## Liens vers les contenus

Les cartes **En cours de lecture**, **Progression Fantôme** et **Calendrier**
affichent désormais des liens discrets : 🔎 Où regarder (JustWatch), TMDB
(fiche) et MDBList (fiche) quand l'identifiant est connu.

## Confort de lecture

- **En cours de lecture** : la carte est aérée (lignes espacées, icônes
  distinctes par information : dates, prochain épisode, progression, temps),
  toutes les informations sont conservées ;
- **Que regarder ?** : les recommandations s'affichent une sous l'autre
  (comme « En cours de lecture ») au lieu de deux par ligne — plus lisible,
  sans décalage de largeur entre colonnes.

## Déconnexion MDBList

Un bouton discret « 🔌 Se déconnecter de MDBList » est ajouté en bas de la
sidebar : accessible depuis toutes les pages, sans prendre de place à l'écran
(arbitrage : une seule déconnexion, toujours visible, plutôt qu'un bouton
répété sur chaque page).

## Installation

Envoyer ces fichiers à la racine du dépôt :

- `app.py` (modifié)
- `mdblist_provider.py` (modifié)
- `dashboard_engine.py` (NOUVEAU)
- `excel_export.py` (NOUVEAU)
- `ETAPE-26.md` (NOUVEAU)

Aucun fichier à supprimer. Ne pas retoucher `calendar_engine.py`,
`history_engine.py`, `stats_engine.py`, `wrapped_engine.py` ni
`achievements_engine.py` (déjà à jour en ligne). Aucun secret à modifier.

Commit conseillé :

```text
feat: enriched dashboard, excel backup, content links, readable cards
```
