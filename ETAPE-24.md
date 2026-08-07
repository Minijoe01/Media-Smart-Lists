# Media Smart Lists — Étape 24 : calendrier réparé, graphiques nets, Rendez-vous annuel

## Calendrier : cause racine corrigée

Le calendrier ne montrait presque rien malgré l'enrichissement ajouté à l'étape
précédente. La cause a été trouvée : l'appel groupé MDBList utilisait
`POST /tmdb/any/`, un endpoint qui n'existe pas sous cette forme.

L'API MDBList expose en réalité deux endpoints séparés :

```text
POST /tmdb/movie   avec {"ids": ["123", "456"], "append_to_response": "genres,description"}
POST /tmdb/show    idem
```

Les identifiants sont des chaînes, et chaque appel accepte 200 médias maximum.
La correction :

- `media_info_batch` envoie désormais un appel par type (`/tmdb/movie` puis
  `/tmdb/show`) avec les bons identifiants ;
- les identifiants TMDb sont collectés **séparément** films / séries depuis
  vos séries en cours (Up Next), votre Watchlist et vos listes ;
- le calendrier fusionne toujours les 3 sources : calendrier officiel MDBList,
  dates déjà dans vos données, et dates à venir récupérées par les appels
  groupés (prochain épisode annoncé, date de sortie des films, première
  diffusion des séries).

Deux appels groupés suffisent (un pour les films, un pour les séries), quels
que soient la taille de vos listes et l'horizon choisi.

### Robustesse du calendrier officiel

L'endpoint `/calendar/events` peut être appelé avec ou sans le paramètre
`favorite_cast`. Si une version de l'API le refuse, un second appel sans ce
paramètre est tenté automatiquement au lieu d'échouer.

## Graphiques des statistiques : plus propres

- **Redimensionnement** : chaque graphique tient exactement dans son cadre
  (plus d'ascenseurs horizontaux ni verticaux) — contenu verrouillé
  (`overflow:hidden`), initialisation d'ECharts après le chargement du DOM et
  redimensionnement automatique avec la fenêtre.
- **Ordre des mois** : « Heures par mois » est désormais trié
  chronologiquement (07-2024, 07-2025, 05-2026, 07-2026…) au lieu de l'ordre
  alphabétique (01-2021, 01-2022, 02-2021…).
- **Info-bulles explicites** : chaque graphique précise son unité —
  « {b} : {c}h » pour les heures ; le camembert des genres affiche
  « {b} : {c} contenu(s) ({d}%) » ; l'évolution des goûts affiche « {value} h ».
- **Heatmap d'activité** : les info-bulles au survol (date + nombre de
  visionnages) repassent par le rendu Markdown, comme dans l'ancienne app.
- **Barres de progression** : le CSS est renforcé pour que toutes les barres
  (genres, ADN, studios, historique) respectent le thème : fond sombre,
  remplissage en dégradé vert → citron.

## Rendez-vous annuel (Wrapped) — restauré

La page « 🎬 Rendez-vous annuel » reprend la logique et le rendu de
l'ancienne application Trakt Smart Lists, branchée sur le modèle normalisé
MDBList :

- choix de l'année ;
- hero card « TON ANNÉE XXXX » avec le temps total de visionnage ;
- indicateurs : films uniques, séries suivies, épisodes, note moyenne,
  record en 1 jour, plus gros mois ;
- tops films / séries / genres de l'année ;
- graphique des heures par mois (barres citron) ;
- **image PNG 1080×1350 partageable** façon Spotify Wrapped, aux couleurs du
  thème (dégradé vert, citron), générée localement sans aucun appel réseau,
  téléchargeable.

## Installation

Envoyer ces fichiers à la racine du dépôt :

- `app.py` (modifié)
- `mdblist_provider.py` (modifié)
- `stats_engine.py` (modifié)
- `wrapped_engine.py` (NOUVEAU)
- `ETAPE-24.md` (NOUVEAU)

Aucun fichier à supprimer. Ne pas retoucher `calendar_engine.py` ni
`history_engine.py` (déjà à jour en V23). Aucun secret à modifier.

Commit conseillé :

```text
fix: correct media batch endpoint, tidy charts, restore annual wrapped page
```
