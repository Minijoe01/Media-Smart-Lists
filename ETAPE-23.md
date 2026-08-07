# Media Smart Lists — Étape 23 : calendrier enrichi et statistiques détaillées façon Trakt Smart Lists

## Calendrier : complétude des dates à venir

Le calendrier ne montrait presque rien au-delà du court terme, alors que des
contenus de vos listes sortiront dans les prochains mois (et que des séries en
cours ont des épisodes annoncés).

### Trois sources fusionnées

1. **Calendrier officiel MDBList** (`/calendar/events`, découpé en tranches de
   120 jours pour les horizons longs) ;
2. **Dates déjà présentes dans vos données** (Up Next, Watchlist, listes) ;
3. **Nouveau — dates à venir récupérées par appels groupés** : l'application
   interroge MDBList par lots de 200 identifiants (vos séries en cours, puis
   votre Watchlist, puis vos listes) et récupère les vraies dates futures
   annoncées : prochain épisode d'une série en cours ou en pause
   (`next_episode_to_air`), date de sortie d'un film, première diffusion d'une
   série.

Résultat : une série comme **Silo** dont l'épisode suivant n'est pas encore
diffusé apparaît désormais avec sa date annoncée, de même que tous les films et
séries de vos listes dont la date de sortie est connue (fin 2026, 2027…).

Le bouton indique le nombre total d'appels réels (segments + lots groupés), et
le message sous le calendrier détaille la provenance des événements.

## Statistiques : page reconstruite à l'identique de l'ancienne application

La page **📊 Statistiques** reproduit la disposition et les couleurs exactes de
la page Statistiques de Trakt Smart Lists :

- **Filtres** en haut : Type de contenu (Tous/Films/Séries), Période (Tout,
  Cette année, 12 derniers mois, 6 derniers mois, Ce mois-ci, Mois dernier,
  Aujourd'hui, Période personnalisée), Genre ;
- **5 indicateurs** : Nombre de visionnages, Temps de visionnage (format
  précis), Note moyenne /10, Moyenne par jour, Record en 1 jour ;
- **🗓️ Heatmap d'activité** (une case par jour, légende en couleurs réelles,
  52 dernières semaines si « Tout ») ;
- **Heures par mois** (courbe citron #CEDC00) ;
- **Genres les plus regardés** (camembert, palette du thème) et **par heure de
  la journée** (barres dégradé vert) ;
- **Par jour de la semaine** (barres citron) et **par année de sortie** (barres
  dégradé vert) ;
- **🧬 Ton ADN cinéphile** : répartition par genre (heures) + grands équilibres
  (Films ⇄ Séries, Récent ⇄ Ancien, Films courts ⇄ longs) ;
- **🏢 Tes studios préférés** (séries, heures cumulées par studio/chaîne) ;
- **🏆 Marathons** (4+ épisodes de la même série en 1 jour) ;
- **📈 L'évolution de tes goûts** (5 genres principaux, année par année,
  barres empilées) ;
- **📋 Détail des visionnages** (tableau filtrable).

L'historique des vues repliable (étape 21) reste disponible au-dessus.

### Barres de progression aux couleurs du thème

Les barres de progression (genres, ADN, studios) respectent désormais
toujours le thème : fond sombre + remplissage en dégradé vert → citron
(#00A392 → #CEDC00), appliqué globalement par CSS.

### Graphiques sans dépendance cassée

Le paquet `streamlit-echarts` est incompatible avec Streamlit 1.60 (l'import
provoquait une erreur de composant). Les graphiques utilisent maintenant
`st.iframe` + Apache ECharts via CDN : même rendu, aucune dépendance fragile.

## Installation

Envoyer ces fichiers à la racine du dépôt :

- `app.py` (modifié)
- `history_engine.py` (modifié)
- `stats_engine.py` (NOUVEAU)
- `ETAPE-23.md` (NOUVEAU)

Aucun fichier à supprimer. Aucun secret à modifier.

Commit conseillé :

```text
feat: enriched long-range calendar and Trakt-style detailed stats
```
