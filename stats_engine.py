"""Statistiques détaillées de Media Smart Lists.

Reprend la disposition et les couleurs de la page Statistiques de l'ancienne
application Trakt Smart Lists, alimentée par les données normalisées MDBList
(fonction normalize_history). Les fonctions sont pures : l'interface reste
dans app.py.

Couleurs du thème Aston Martin F1 2026 :
    vert #00A392 · vert foncé #00524B · citron #CEDC00 · texte #F0FAF8
    texte atténué #9DC5BF · séparateurs rgba(18,90,84,0.4)
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Iterable

import pandas as pd

# ── Palette du thème ─────────────────────────────────────────────────────────
COL_GREEN = "#00A392"
COL_GREEN_DARK = "#00524B"
COL_LIME = "#CEDC00"
COL_TEXT = "#F0FAF8"
COL_MUTED = "#9DC5BF"
COL_SPLIT = "rgba(18,90,84,0.4)"
COL_TRACK = "rgba(255,255,255,0.08)"
PIE_COLORS = ["#00A392", "#CEDC00", "#00524B", "#A3B300", "#E8F064", "#869400", "#00A392", "#E8F064"]
STACK_COLORS = ["#00A392", "#CEDC00", "#00524B", "#A3B300", "#E8F064"]
BAR_GRADIENT = {
    "type": "linear",
    "x": 0,
    "y": 0,
    "x2": 0,
    "y2": 1,
    "colorStops": [{"offset": 0, "color": COL_GREEN}, {"offset": 1, "color": COL_GREEN_DARK}],
}

# Échelle de la heatmap d'activité (seuil, couleur, libellé).
HM_ECHELLE = [
    (0, "rgba(157,197,191,0.10)", "0"),
    (1, "#0E7566", "1"),
    (2, "#00A392", "2 à 3"),
    (4, "#CEDC00", "4 et +"),
]

PERIOD_OPTIONS = [
    "Tout",
    "Cette année",
    "12 derniers mois",
    "6 derniers mois",
    "Ce mois-ci",
    "Mois dernier",
    "Aujourd'hui",
    "Période personnalisée",
]

TYPE_OPTIONS = ["Tous", "Films", "Séries"]


def _hm_couleur(nb_vues: int) -> str:
    couleur = HM_ECHELLE[0][1]
    for seuil, coul, _label in HM_ECHELLE:
        if nb_vues >= seuil:
            couleur = coul
    return couleur


def build_frame(rows: Iterable[dict[str, Any]]) -> pd.DataFrame:
    """Construit le DataFrame d'analyse depuis les lignes normalisées.

    Une ligne = un film ou un épisode vu (avec son nombre de lectures).
    """
    values = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        watched_at = row.get("watched_at")
        if watched_at is None:
            continue
        kind = str(row.get("type") or "Épisode")
        plays = max(int(row.get("plays") or 1), 1)
        duree = max(int(row.get("total_minutes") or 0), 0)
        if duree <= 0:
            duree = max(int(row.get("runtime") or 0) * plays, 0)
        genres = row.get("genres") or []
        genre_text = " · ".join(str(value) for value in genres) if genres else "Inconnu"
        values.append(
            {
                "date_dt": watched_at,
                "type": "Film" if kind == "Film" else "Épisode",
                "titre": str(row.get("title") or "Inconnu"),
                "serie": str(row.get("title") or "Inconnu"),
                "annee": row.get("year"),
                "genre": genre_text,
                "duree": duree,
                "lectures": plays,
                "note": float(row["personal_rating"]) if row.get("personal_rating") else 0.0,
                "studios": list(row.get("studios") or []),
            }
        )
    if not values:
        return pd.DataFrame()
    return pd.DataFrame(values)


def apply_period(
    df: pd.DataFrame,
    period: str,
    now: datetime,
    custom_start: date | None = None,
    custom_end: date | None = None,
) -> pd.DataFrame:
    """Filtre temporel identique à l'ancienne application."""
    if df.empty:
        return df
    if period == "Cette année":
        return df[df["date_dt"].dt.year == now.year]
    if period == "12 derniers mois":
        return df[df["date_dt"] >= now - pd.DateOffset(months=12)]
    if period == "6 derniers mois":
        return df[df["date_dt"] >= now - pd.DateOffset(months=6)]
    if period == "Ce mois-ci":
        return df[(df["date_dt"].dt.year == now.year) & (df["date_dt"].dt.month == now.month)]
    if period == "Mois dernier":
        previous = (now.replace(day=1) - timedelta(days=1)).date()
        return df[
            (df["date_dt"].dt.year == previous.year) & (df["date_dt"].dt.month == previous.month)
        ]
    if period == "Aujourd'hui":
        return df[df["date_dt"].dt.date == now.date()]
    if period == "Période personnalisée" and custom_start is not None and custom_end is not None:
        return df[
            (df["date_dt"].dt.date >= custom_start) & (df["date_dt"].dt.date <= custom_end)
        ]
    return df


def available_months(df: pd.DataFrame) -> list[str]:
    """Mois disponibles (MM-AAAA) triés chronologiquement, pour la période personnalisée."""
    if df.empty:
        return []
    months = sorted(df["date_dt"].dt.strftime("%m-%Y").unique())
    return months


def heatmap_html(df: pd.DataFrame) -> str:
    """Heatmap d'activité (52 dernières semaines si l'écart dépasse 371 jours)."""
    if df.empty:
        return ""
    lectures = df.groupby(df["date_dt"].dt.date)["lectures"].sum()
    dmax = lectures.index.max()
    dmin_all = lectures.index.min()
    if (dmax - dmin_all).days > 371:
        start = dmax - timedelta(days=dmax.weekday() + 7 * 52)
    else:
        start = dmin_all - timedelta(days=dmin_all.weekday())

    weeks: dict[int, dict[int, tuple[date, int, str]]] = {}
    cursor = start
    while cursor <= dmax:
        count = int(lectures.get(cursor, 0))
        week = (cursor - start).days // 7
        weeks.setdefault(week, {})[cursor.weekday()] = (cursor, count, _hm_couleur(count))
        cursor += timedelta(days=1)

    html = ['<div style="display:flex; gap:3px; padding:6px 2px; overflow-x:auto;">']
    for week in sorted(weeks):
        html.append('<div style="display:flex; flex-direction:column; gap:3px;">')
        for weekday in range(7):
            cell = weeks[week].get(weekday)
            if cell:
                day, count, bg = cell
                plural = "s" if count > 1 else ""
                html.append(
                    f'<div title="{day.strftime("%d/%m/%Y")} — {count} visionnage{plural}" '
                    f'style="width:11px; height:11px; border-radius:2px; background:{bg};"></div>'
                )
            else:
                html.append('<div style="width:11px; height:11px;"></div>')
        html.append("</div>")
    html.append("</div>")
    html.append(
        '<div style="display:flex; align-items:center; gap:6px; padding:10px 2px 0; '
        'font-size:12px; color:#9DC5BF; flex-wrap:wrap;"><span>Légende :</span>'
    )
    for _seuil, coul, label in HM_ECHELLE:
        html.append(
            f'<span title="{label} visionnage(s) / jour" style="width:11px; height:11px; '
            f'border-radius:2px; background:{coul}; display:inline-block; flex:none;"></span>'
            f'<span style="margin-right:10px;">{label}</span>'
        )
    html.append('<span>visionnage(s) / jour</span></div>')
    return "".join(html)


def _base_text_style() -> dict[str, Any]:
    return {
        "backgroundColor": "transparent",
        "textStyle": {"color": COL_TEXT},
        "tooltip": {"trigger": "axis", "formatter": "{b} : {c}h"},
        "xAxis": {"type": "category", "data": [], "axisLabel": {"color": COL_MUTED}},
        "yAxis": {
            "type": "value",
            "name": "Heures",
            "axisLabel": {"color": COL_MUTED},
            "splitLine": {"lineStyle": {"color": COL_SPLIT}},
        },
    }


def monthly_options(df: pd.DataFrame) -> dict[str, Any]:
    """Heures par mois — courbe citron, triée chronologiquement."""
    if df.empty:
        return {}
    df = df.copy()
    df["an_mois"] = df["date_dt"].dt.year * 100 + df["date_dt"].dt.month
    df["mois"] = df["date_dt"].dt.strftime("%m-%Y")
    # Tri explicitement chronologique : (année, mois) numérique, jamais alphabétique.
    series_by_key: dict[int, tuple[str, float]] = {}
    for (an_mois, mois), duree in df.groupby(["an_mois", "mois"])["duree"].sum().round(1).items():
        series_by_key[int(an_mois)] = (str(mois), float(duree))
    ordered = [series_by_key[key] for key in sorted(series_by_key)]
    labels = [label for label, _ in ordered]
    values = [value for _, value in ordered]
    option = _base_text_style()
    option["title"] = {"text": "Heures par mois", "textStyle": {"color": COL_TEXT}}
    option["xAxis"] = {"type": "category", "data": labels, "axisLabel": {"color": COL_MUTED}}
    option["series"] = [
        {
            "data": values,
            "type": "line",
            "smooth": True,
            "lineStyle": {"color": COL_LIME, "width": 3},
            "areaStyle": {"color": "rgba(206,220,0,0.10)"},
            "itemStyle": {"color": COL_LIME},
        }
    ]
    return option


def genre_pie_options(df: pd.DataFrame) -> dict[str, Any]:
    """Genres les plus regardés (nombre de contenus) — camembert."""
    if df.empty:
        return {}
    counts: dict[str, int] = {}
    for raw in df["genre"].astype(str).str.split(" · "):
        for genre in raw:
            if genre and genre != "Inconnu":
                counts[genre] = counts.get(genre, 0) + 1
    data = [{"name": key, "value": value} for key, value in sorted(counts.items(), key=lambda kv: -kv[1])[:8]]
    return {
        "title": {
            "text": "Genres les plus regardés (nombre de contenus)",
            "left": "center",
            "textStyle": {"color": COL_TEXT},
        },
        "tooltip": {"trigger": "item", "formatter": "{b} : {c} contenu(s) ({d}%)"},
        "backgroundColor": "transparent",
        "legend": {"bottom": 0, "textStyle": {"color": COL_MUTED}},
        "series": [
            {
                "type": "pie",
                "radius": ["40%", "70%"],
                "data": data,
                "itemStyle": {"borderRadius": 8, "borderColor": "#042E2B", "borderWidth": 2},
                "label": {"color": COL_TEXT},
            }
        ],
        "color": PIE_COLORS,
    }


def hourly_options(df: pd.DataFrame) -> dict[str, Any]:
    """Heures par heure de la journée — barres dégradé vert."""
    if df.empty:
        return {}
    df = df.copy()
    df["h"] = df["date_dt"].dt.hour
    hours = (df.groupby("h")["duree"].sum().reindex(range(24), fill_value=0) / 60).round(1)
    return {
        "title": {"text": "Par heure de la journée", "left": "center", "textStyle": {"color": COL_TEXT}},
        "tooltip": {"trigger": "axis", "formatter": "{b} : {c}h"},
        "backgroundColor": "transparent",
        "xAxis": {"type": "category", "data": [f"{h}h" for h in range(24)], "axisLabel": {"color": COL_MUTED}},
        "yAxis": {"type": "value", "name": "Heures", "axisLabel": {"color": COL_MUTED}, "splitLine": {"lineStyle": {"color": COL_SPLIT}}},
        "series": [{"data": list(hours.values), "type": "bar", "itemStyle": {"color": BAR_GRADIENT, "borderRadius": [4, 4, 0, 0]}}],
    }


def weekday_options(df: pd.DataFrame) -> dict[str, Any]:
    """Heures par jour de la semaine — barres citron."""
    if df.empty:
        return {}
    df = df.copy()
    jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    df["jsem"] = df["date_dt"].dt.weekday
    hours = (df.groupby("jsem")["duree"].sum().reindex(range(7), fill_value=0) / 60).round(1)
    return {
        "title": {"text": "Par jour de la semaine", "left": "center", "textStyle": {"color": COL_TEXT}},
        "tooltip": {"trigger": "axis", "formatter": "{b} : {c}h"},
        "backgroundColor": "transparent",
        "xAxis": {"type": "category", "data": jours, "axisLabel": {"color": COL_MUTED}},
        "yAxis": {"type": "value", "name": "Heures", "axisLabel": {"color": COL_MUTED}, "splitLine": {"lineStyle": {"color": COL_SPLIT}}},
        "series": [{"data": list(hours.values), "type": "bar", "itemStyle": {"color": COL_LIME, "borderRadius": [4, 4, 0, 0]}}],
    }


def release_year_options(df: pd.DataFrame) -> dict[str, Any]:
    """Heures par année de sortie — barres dégradé vert."""
    if df.empty:
        return {}
    df = df.dropna(subset=["annee"])
    if df.empty:
        return {}
    df = df.copy()
    df["annee"] = df["annee"].astype(int)
    hours = (df.groupby("annee")["duree"].sum() / 60).round(1).sort_index()
    return {
        "title": {"text": "Par année de sortie", "left": "center", "textStyle": {"color": COL_TEXT}},
        "tooltip": {"trigger": "axis", "formatter": "{b} : {c}h"},
        "backgroundColor": "transparent",
        "xAxis": {"type": "category", "data": list(hours.index.astype(str)), "axisLabel": {"color": COL_MUTED}},
        "yAxis": {"type": "value", "name": "Heures", "axisLabel": {"color": COL_MUTED}, "splitLine": {"lineStyle": {"color": COL_SPLIT}}},
        "series": [{"data": list(hours.values), "type": "bar", "itemStyle": {"color": BAR_GRADIENT, "borderRadius": [4, 4, 0, 0]}}],
    }


def dna_genres(df: pd.DataFrame) -> list[tuple[str, float]]:
    """Répartition des heures par genre (top 6) — double comptage assumé."""
    hours: dict[str, float] = {}
    for raw, duree in zip(df["genre"].astype(str), df["duree"]):
        for genre in raw.split(" · "):
            if genre and genre != "Inconnu":
                hours[genre] = hours.get(genre, 0) + (float(duree or 0) / 60)
    return sorted(hours.items(), key=lambda kv: -kv[1])[:6]


def dna_balances(df: pd.DataFrame, now: datetime) -> list[dict[str, Any]]:
    """Grands équilibres : films/séries, récent/ancien, courts/longs."""
    output: list[dict[str, Any]] = []
    if df.empty:
        return output
    film_hours = float(df.loc[df["type"] == "Film", "duree"].sum()) / 60
    ep_hours = float(df.loc[df["type"] == "Épisode", "duree"].sum()) / 60
    total = film_hours + ep_hours
    if total > 0:
        pct = film_hours / total
        output.append({"label": f"🎬 Films {round(pct * 100)}% ⇄ 📺 Séries {round((1 - pct) * 100)}%", "pct": pct})
    cutoff = now.year - 10
    df_year = df.dropna(subset=["annee"])
    if not df_year.empty:
        recent = float(df_year.loc[df_year["annee"] >= cutoff, "duree"].sum())
        old = float(df_year.loc[df_year["annee"] < cutoff, "duree"].sum())
        if recent + old > 0:
            pct = recent / (recent + old)
            output.append({"label": f"🆕 Récent (10 dernières années) {round(pct * 100)}% ⇄ 🕰️ Plus ancien {round((1 - pct) * 100)}%", "pct": pct})
    films = df.loc[df["type"] == "Film", "duree"]
    if not films.empty:
        court = float(films[(films > 0) & (films <= 100)].sum())
        long = float(films[films > 100].sum())
        if court + long > 0:
            pct = court / (court + long)
            output.append({"label": f"⚡ Films courts (≤ 1h40) {round(pct * 100)}% ⇄ 🐘 Films longs {round((1 - pct) * 100)}%", "pct": pct})
    return output


def studio_rank(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Heures cumulées par studio/réseau (séries) — top 6."""
    minutes: dict[str, float] = {}
    for studios, duree in zip(df["studios"], df["duree"]):
        if not isinstance(studios, list) or not studios:
            continue
        for studio in studios:
            minutes[str(studio)] = minutes.get(str(studio), 0) + float(duree or 0)
    top = sorted(minutes.items(), key=lambda kv: -kv[1])[:6]
    total_hours = sum(value for _, value in top) / 60 or 1.0
    output = []
    for name, value in top:
        hours = value / 60
        output.append({"name": name, "hours": hours, "pct": hours / total_hours})
    return output


def marathons(df: pd.DataFrame) -> pd.DataFrame:
    """Jours avec 4+ épisodes de la même série."""
    if df.empty:
        return pd.DataFrame()
    episodes = df[df["type"] == "Épisode"]
    if episodes.empty:
        return pd.DataFrame()
    episodes = episodes.copy()
    episodes["jour"] = episodes["date_dt"].dt.date
    grouped = episodes.groupby(["jour", "serie"]).size().reset_index(name="nb")
    grouped = grouped[grouped["nb"] >= 4].sort_values("nb", ascending=False)
    return grouped.head(5)


def evolution_options(df: pd.DataFrame) -> dict[str, Any] | None:
    """Évolution des goûts : 5 genres principaux, année par année (empilé)."""
    if df.empty:
        return None
    genre_years: dict[str, dict[int, float]] = {}
    for row in df.itertuples():
        duree = float(getattr(row, "duree") or 0) / 60
        year = row.date_dt.year
        for genre in str(row.genre).split(" · "):
            if genre and genre != "Inconnu":
                genre_years.setdefault(genre, {})
                genre_years[genre][year] = genre_years[genre].get(year, 0) + duree
    top5 = [
        genre
        for genre, _ in sorted(
            ((genre, sum(values.values())) for genre, values in genre_years.items()),
            key=lambda kv: -kv[1],
        )[:5]
    ]
    years = sorted({year for values in genre_years.values() for year in values})
    if len(years) < 2 or not top5:
        return None
    series = [
        {
            "name": genre,
            "type": "bar",
            "stack": "heures",
            "barMaxWidth": 44,
            "emphasis": {"focus": "series"},
            "valueFormatter": "{value} h",
            "data": [round(genre_years[genre].get(year, 0), 1) for year in years],
        }
        for genre in top5
    ]
    return {
        "backgroundColor": "transparent",
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}, "valueFormatter": "{value} h"},
        "legend": {"bottom": 0, "textStyle": {"color": COL_MUTED}},
        "xAxis": {"type": "category", "data": [str(year) for year in years], "axisLabel": {"color": COL_MUTED}},
        "yAxis": {"type": "value", "name": "Heures", "axisLabel": {"color": COL_MUTED}, "splitLine": {"lineStyle": {"color": COL_SPLIT}}},
        "series": series,
        "color": STACK_COLORS,
    }
