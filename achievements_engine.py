"""Succès (badges) de Media Smart Lists.

Reprend la liste complète des badges de l'ancienne application Trakt Smart
Lists, calculée à partir du modèle normalisé MDBList (via build_frame).
"""

from __future__ import annotations

from typing import Any

import pandas as pd


def _hours(df: pd.DataFrame) -> float:
    return float(df["duree"].fillna(0).sum()) / 60


def compute_achievements(df: pd.DataFrame) -> dict[str, Any]:
    """Calcule toutes les métriques de badges et la liste obtenus / verrouillés."""
    if df.empty:
        return {"badges": [], "obtenus": [], "locks": [], "total": 0, "obtenu_count": 0}

    films_df = df[df["type"] == "Film"]
    eps_df = df[df["type"] == "Épisode"]

    total_h = _hours(df)
    total_jours = total_h / 24
    total_films = int(films_df["titre"].nunique())
    total_eps = int(len(eps_df))
    total_vues = int(df["lectures"].sum())

    # Films revus au moins 2 fois (rewatches).
    if not films_df.empty:
        vues_films = films_df.groupby("titre")["lectures"].sum()
        nb_rewatch = int((vues_films >= 2).sum())
    else:
        nb_rewatch = 0

    # Diversité genres / années de sortie.
    genres_diff: set[str] = set()
    annees_diff: set[int] = set()
    for raw in df["genre"].astype(str).str.split(" · "):
        for genre in raw:
            if genre and genre != "Inconnu":
                genres_diff.add(genre)
    for value in df["annee"].dropna():
        try:
            annees_diff.add(int(value))
        except (TypeError, ValueError):
            pass
    nb_genres = len(genres_diff)
    nb_annees = len(annees_diff)

    # Marathon : max d'épisodes d'une même série en 1 jour.
    rec_jour = 0
    if not eps_df.empty:
        grouped = eps_df.groupby([eps_df["date_dt"].dt.date, "titre"]).size()
        rec_jour = int(grouped.max()) if not grouped.empty else 0

    # Visionnages nocturnes (0h-5h).
    vues_nuit = int(((df["date_dt"].dt.hour >= 0) & (df["date_dt"].dt.hour < 5)).sum())

    # Séries avec beaucoup d'épisodes.
    if not eps_df.empty:
        par_serie = eps_df.groupby("titre").size()
        series_10ep = int((par_serie >= 10).sum())
        series_50ep = int((par_serie >= 50).sum())
        series_100ep = int((par_serie >= 100).sum())
        series_200ep = int((par_serie >= 200).sum())
    else:
        series_10ep = series_50ep = series_100ep = series_200ep = 0

    # Jours distincts + plus longue série de jours consécutifs.
    jours = sorted({d.date() for d in df["date_dt"]})
    nb_jours_diff = len(jours)
    streak_max = 1 if jours else 0
    current = 1
    for a, b in zip(jours, jours[1:]):
        if (b - a).days == 1:
            current += 1
            if current > streak_max:
                streak_max = current
        else:
            current = 1

    # Nuit blanche : 3+ contenus entre 0h et 6h sur une même nuit.
    nocturnes = df[(df["date_dt"].dt.hour >= 0) & (df["date_dt"].dt.hour < 6)]
    nuit_blanche = bool(
        (not nocturnes.empty) and (nocturnes.groupby(nocturnes["date_dt"].dt.date).size() >= 3).any()
    )

    # Coup de cœur : note >= 9.
    note_coup_coeur = bool((df["note"] >= 9).any())

    # Liste complète des badges : (id, emoji, titre, desc, condition, progression %).
    badges = [
        # -- Paliers de temps --
        ("h1", "🌱", "Première heure", "Tu as regardé ton premier contenu", total_h >= 1, min(total_h / 1 * 100, 100)),
        ("h10", "⏳", "Dix heures", "10 heures de visionnage cumulées", total_h >= 10, min(total_h / 10 * 100, 100)),
        ("h24", "⏰", "Un jour complet", "24h passées devant des films et séries", total_h >= 24, min(total_h / 24 * 100, 100)),
        ("h168", "📅", "Une semaine entière", "Tu as passé une semaine entière de visionnage (168h)", total_h >= 168, min(total_h / 168 * 100, 100)),
        ("h720", "🗓️", "Un mois de binge", "30 jours complets de visionnage (720h)", total_h >= 720, min(total_h / 720 * 100, 100)),
        ("h2160", "🏁", "Trimestre sur écran", "3 mois entiers à regarder des contenus (2160h)", total_h >= 2160, min(total_h / 2160 * 100, 100)),
        ("h8760", "👑", "Une année d'écran", "1 AN de visionnage cumulé (8760h) — statut de légende", total_h >= 8760, min(total_h / 8760 * 100, 100)),
        ("h26k", "⚜️", "Empereur du canapé", "3 ANS de visionnage — tu vis sur ton canapé (26 280h)", total_h >= 26280, min(total_h / 26280 * 100, 100)),
        ("h43k", "🧙", "Archiviste ultime", "5 ANS entiers de visionnage — tu as vu presque tout (43 800h)", total_h >= 43800, min(total_h / 43800 * 100, 100)),

        # -- Films --
        ("f1", "🎬", "Premier film", "Ton premier film vu", total_films >= 1, min(total_films / 1 * 100, 100)),
        ("f10", "🎞️", "Dix films", "10 films différents vus", total_films >= 10, min(total_films / 10 * 100, 100)),
        ("f50", "🎥", "Cinéphile", "50 films différents vus", total_films >= 50, min(total_films / 50 * 100, 100)),
        ("f100", "🍿", "Cent films", "100 films vus !", total_films >= 100, min(total_films / 100 * 100, 100)),
        ("f250", "🏅", "Amoureux du 7ème art", "250 films vus — une belle cinémathèque", total_films >= 250, min(total_films / 250 * 100, 100)),
        ("f500", "🎭", "Véritable cinéphile", "500 films différents vus", total_films >= 500, min(total_films / 500 * 100, 100)),
        ("f1000", "🎪", "Maître du grand écran", "1000 films, impressionnant !", total_films >= 1000, min(total_films / 1000 * 100, 100)),
        ("f2000", "🏛️", "Bibliothèque vivante", "2000 films — ta culture ciné est immense", total_films >= 2000, min(total_films / 2000 * 100, 100)),
        ("f5000", "🧠", "Encyclopédie du cinéma", "5000 films différents — tu devrais écrire un blog", total_films >= 5000, min(total_films / 5000 * 100, 100)),

        # -- Séries --
        ("s1", "📺", "Premier épisode", "Ton tout premier épisode vu", total_eps >= 1, min(total_eps / 1 * 100, 100)),
        ("s10", "📡", "Dix épisodes", "10 épisodes vus", total_eps >= 10, min(total_eps / 10 * 100, 100)),
        ("s100", "📶", "Cent épisodes", "100 épisodes vus", total_eps >= 100, min(total_eps / 100 * 100, 100)),
        ("s500", "💻", "Accro aux séries", "500 épisodes — les séries n'ont plus de secrets pour toi", total_eps >= 500, min(total_eps / 500 * 100, 100)),
        ("s1000", "🔥", "Mille épisodes", "1000 épisodes ! Une belle performance", total_eps >= 1000, min(total_eps / 1000 * 100, 100)),
        ("s2500", "🚀", "Marathonien TV", "2500 épisodes — tu vis littéralement devant les séries", total_eps >= 2500, min(total_eps / 2500 * 100, 100)),
        ("s5000", "🏯", "Forteresse de canapé", "5000 épisodes — rien ne t'arrête", total_eps >= 5000, min(total_eps / 5000 * 100, 100)),
        ("s10k", "🌋", "Dix mille épisodes", "10 000 épisodes. Juste... wow.", total_eps >= 10000, min(total_eps / 10000 * 100, 100)),
        ("s25k", "🌌", "Univers télévisuel", "25 000 épisodes — tu as plus vu de séries que la plupart des gens", total_eps >= 25000, min(total_eps / 25000 * 100, 100)),

        # -- Séries suivies --
        ("sv1", "✅", "Une série suivie", "Au moins 10 épisodes vus d'une même série", series_10ep >= 1, min(series_10ep / 1 * 100, 100)),
        ("sv5", "💪", "Cinq séries suivies", "Tu as vu 10+ épisodes de 5 séries différentes", series_10ep >= 5, min(series_10ep / 5 * 100, 100)),
        ("sv10", "📚", "Dix séries suivies", "10 séries dont tu as vu plus de 10 épisodes", series_10ep >= 10, min(series_10ep / 10 * 100, 100)),
        ("sv25", "🗂️", "Collectionneur", "25 séries différentes avec 10+ épisodes chacune", series_10ep >= 25, min(series_10ep / 25 * 100, 100)),
        ("sv50", "💎", "Fan inconditionnel", "Une série avec plus de 50 épisodes vus", series_50ep >= 1, min(series_50ep / 1 * 100, 100)),
        ("sv100", "💍", "Relation sérieuse", "Une série avec plus de 100 épisodes vus — un investissement", series_100ep >= 1, min(series_100ep / 1 * 100, 100)),
        ("sv200", "👑", "Série culte", "Une série avec plus de 200 épisodes — un compagnon de vie", series_200ep >= 1, min(series_200ep / 1 * 100, 100)),

        # -- Marathons --
        ("mar4", "🏃", "Marathonien", "4+ épisodes d'une même série en 1 jour", rec_jour >= 4, min(rec_jour / 4 * 100, 100)),
        ("mar8", "⚡", "Marathon éclair", "8+ épisodes en une seule journée", rec_jour >= 8, min(rec_jour / 8 * 100, 100)),
        ("mar12", "🚄", "Train fou", "12+ épisodes en 1 jour — ça c'est du binge !", rec_jour >= 12, min(rec_jour / 12 * 100, 100)),
        ("mar20", "🏁", "Journée sans sortir", "20+ épisodes en 1 jour — tu n'as pas vu le soleil", rec_jour >= 20, min(rec_jour / 20 * 100, 100)),

        # -- Diversité --
        ("divg", "🌈", "Explorateur de genres", "Tu as touché à au moins 10 genres différents", nb_genres >= 10, min(nb_genres / 10 * 100, 100)),
        ("divg2", "🎨", "Palette complète", "20 genres différents explorés", nb_genres >= 20, min(nb_genres / 20 * 100, 100)),
        ("diva", "🕰️", "Voyageur temporel", "Tu as vu des contenus de 20 années de sortie différentes", nb_annees >= 20, min(nb_annees / 20 * 100, 100)),
        ("diva3", "🗿", "Amateur de classiques", "Des contenus de 40 années différentes — du vieux au neuf !", nb_annees >= 40, min(nb_annees / 40 * 100, 100)),
        ("diva6", "🏛️", "Passé et présent", "60 années de cinéma/séries — des années 60 à aujourd'hui", nb_annees >= 60, min(nb_annees / 60 * 100, 100)),

        # -- Nocturne --
        ("nuit", "🌙", "Oiseau de nuit", "Plus de 20 visionnages entre minuit et 5h du matin", vues_nuit >= 20, min(vues_nuit / 20 * 100, 100)),
        ("nuit2", "🦉", "Chouette cinéphile", "Plus de 100 visionnages nocturnes", vues_nuit >= 100, min(vues_nuit / 100 * 100, 100)),
        ("nuit3", "🦇", "Créature de la nuit", "Plus de 500 visionnages entre minuit et 5h", vues_nuit >= 500, min(vues_nuit / 500 * 100, 100)),
        ("nuitb", "🌃", "Nuit blanche", "Plus de 3 visionnages entre minuit et 6h sur une même nuit", nuit_blanche, 100 if nuit_blanche else 0),

        # -- Global --
        ("all1", "👶", "Nouveau venu", "Ton tout premier visionnage", total_vues >= 1, min(total_vues / 1 * 100, 100)),
        ("all100", "⭐", "Cent visionnages", "100 visionnages au total (films + épisodes)", total_vues >= 100, min(total_vues / 100 * 100, 100)),
        ("all1k", "🌟", "Mille visionnages", "1000 visionnages, belle courbe de progression !", total_vues >= 1000, min(total_vues / 1000 * 100, 100)),
        ("all5k", "💫", "Cinq mille", "5000 visionnages, une véritable habitude", total_vues >= 5000, min(total_vues / 5000 * 100, 100)),
        ("all10k", "🪽", "Dix mille", "10 000 visionnages — c'est de la passion à ce niveau", total_vues >= 10000, min(total_vues / 10000 * 100, 100)),
        ("all25k", "🔱", "25 000", "25 000 visionnages, tu es un abonné historique", total_vues >= 25000, min(total_vues / 25000 * 100, 100)),
        ("all50k", "🌠", "50 000", "50 000 visionnages, la légende est en marche", total_vues >= 50000, min(total_vues / 50000 * 100, 100)),

        # -- Rythme --
        ("ryth", "📆", "Un an de fidélité", "Visionnages répartis sur au moins 365 jours différents", nb_jours_diff >= 365, min(nb_jours_diff / 365 * 100, 100)),
        ("ryth2", "🗓️", "Deux ans de fidélité", "Contenus vus sur plus de 730 jours différents", nb_jours_diff >= 730, min(nb_jours_diff / 730 * 100, 100)),
        ("str7", "🔥", "Semaine de feu", "Tu as regardé du contenu 7 jours d'affilée (au moins une fois)", streak_max >= 7, min(streak_max / 7 * 100, 100)),
        ("str30", "🥵", "Mois de feu", "30 jours d'affilée avec au moins un visionnage — une machine !", streak_max >= 30, min(streak_max / 30 * 100, 100)),
        ("note9", "💯", "Critique exigeant", "Au moins un contenu noté 9 ou 10 — tu as eu un coup de cœur", note_coup_coeur, 100 if note_coup_coeur else 0),
        ("rew5", "🔁", "Fan de rewatch", "5 films revus au moins 2 fois — les bons films méritent un second regard", nb_rewatch >= 5, min(nb_rewatch / 5 * 100, 100)),
        ("rew10", "♾️", "Maître du rewatch", "10 films revus au moins 2 fois — tu cultives tes classiques perso", nb_rewatch >= 10, min(nb_rewatch / 10 * 100, 100)),
    ]

    obtenus = [badge for badge in badges if badge[4]]
    locks = [badge for badge in badges if not badge[4]]
    locks = sorted(locks, key=lambda badge: -badge[5])
    return {
        "badges": badges,
        "obtenus": obtenus,
        "locks": locks,
        "total": len(badges),
        "obtenu_count": len(obtenus),
    }
