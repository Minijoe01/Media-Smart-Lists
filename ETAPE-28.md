# Media Smart Lists — Étape 28 : import ZIP Trakt complet (v2)

## Ce qui a été corrigé après votre test du ZIP Trakt

### Tableau de bord (ZIP)
Les widgets du tableau de bord (temps total à vie, répartition séries/films,
rythme, bilan du mois, date de fin projetée, derniers visionnages)
s'affichent désormais **aussi avec un dataset ZIP Trakt**, sans nécessiter de
connexion MDBList.

### Libellés « MDBList » corrigés
Les sources issues du ZIP affichent maintenant « Watchlist Trakt (import ZIP) »
au lieu de « Watchlist MDBList ». L'historique des ajouts aux listes utilise le
même libellé (la colonne conteneur est cohérente).

### « En cours de lecture » et « Progression Fantôme » (ZIP)
- Les **reprises en pause** du ZIP (fichiers `playback-*.json`) alimentent la
  page Progression Fantôme ;
- Les **séries en cours** sont reconstruites depuis l'historique du ZIP :
  elles apparaissent dans « En cours de lecture » avec le nombre d'épisodes
  vus et la date du dernier visionnage. Sans les métadonnées MDBList, la
  progression totale est inconnue — l'interface l'indique honnêtement
  (« progression totale inconnue sans MDBList »).

### « Que regarder ? » (ZIP) — grâce au nouvel enrichissement
Un bouton **« ✨ Enrichir avec MDBList (genres, posters, durées, notes) »**
apparaît sur le dashboard quand les données viennent d'un ZIP. Il interroge
MDBList par lots (lecture seule, 1 appel par lot de 200) et fusionne dans le
dataset :
- les **genres** (le filtre « Genre » de Que regarder apparaît alors) ;
- les **posters** ;
- les **durées réelles** (films et épisodes) ;
- les **notes communautaires** (scores différenciés, fini les 38/100 partout).

Sans connexion, le message explique que l'enrichissement est possible en se
connectant (lecture seule). Les filtres de type (Films/Séries) et la
navigation restent disponibles.

### Calendrier (ZIP, sans connexion)
Le calendrier fonctionne désormais en mode local **sans connexion MDBList**
quand un dataset (ZIP ou MDBList) est chargé : dates déjà présentes dans les
données + dates complétées si la session MDBList est disponible.

### Restauration JSON accessible sans connexion
La section « 📥 Restaurer une sauvegarde » de la page Sauvegarde est
désormais affichée **avant** le bloc d'export, donc disponible même sans
données chargées ni connexion. Vous pouvez recharger votre sauvegarde JSON
sans repasser par l'API MDBList.

### Historique des ajouts aux listes (ZIP)
Les dates `listed_at` du ZIP sont conservées : « 🕒 Historique des ajouts aux
listes » fonctionne pour l'import Trakt.

## Liens

Les badges de liens (🔎 Où regarder · TMDB · MDBL) sont maintenant aussi
présents sur les cartes de **Que regarder ?**, et le premier badge affiche
« 🔎 Où regarder » (texte) au lieu de la seule icône.

## Installation

Envoyer ces fichiers à la racine du dépôt :

- `app.py` (modifié)
- `trakt_zip_provider.py` (modifié)
- `normalized_model.py` (modifié)
- `list_audit_engine.py` (modifié)
- `ETAPE-28.md` (NOUVEAU)

Aucun fichier à supprimer. Ne pas retoucher `calendar_engine.py`,
`history_engine.py`, `stats_engine.py`, `wrapped_engine.py`,
`achievements_engine.py`, `dashboard_engine.py`, `excel_export.py`,
`mdblist_provider.py` (déjà à jour en ligne). Aucun secret à modifier.

Commit conseillé :

```text
feat: complete Trakt ZIP support (dashboard, watch, recommend, restore)
```
