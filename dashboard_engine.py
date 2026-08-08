"""Tableau de bord — calculs locaux (aucun appel API).

Reprend les widgets de l'ancienne application Trakt Smart Lists :
bilan du mois, rythme d'épisodes par semaine, compteurs à vie films/séries,
digest hebdomadaire et projection de la date de fin des séries en cours
(hors séries abandonnées).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

import pandas as pd

from history_engine import normalize_history
from stats_engine import build_frame

MOIS_NOMS = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
]


def _minutes_to_duree(minutes: float) -> str:
    """Durée lisible en français à partir de minutes."""
    minutes = max(int(round(minutes or 0)), 0)
    if minutes < 60:
        return f"{minutes} min"
    hours, minute_rest = divmod(minutes, 60)
    if hours < 24:
        return f"{hours} h {minute_rest:02d}" if minute_rest else f"{hours} h"
    days, hour_rest = divmod(hours, 24)
    if days < 365:
        months, day_rest = divmod(days, 30)
        parts = []
        if months:
            parts.append(f"{months} mois")
        if day_rest:
            parts.append(f"{day_rest} j")
        if hour_rest:
            parts.append(f"{hour_rest} h")
        return " ".join(parts) or "0 min"
    years, day_after = divmod(days, 365)
    months, day_rest = divmod(day_after, 30)
    parts = [f"{years} an" if years == 1 else f"{years} ans"]
    if months:
        parts.append(f"{months} mois")
    if day_rest:
        parts.append(f"{day_rest} j")
    if hour_rest:
        parts.append(f"{hour_rest} h")
    return " ".join(parts)


def compute_dashboard(
    dataset: dict[str, Any],
    timezone_name: str = "Europe/Paris",
) -> dict[str, Any]:
    """Calcule tous les indicateurs du tableau de bord.

    - compteurs à vie : heures séries / heures films, épisodes, films ;
    - digest 7 jours : épisodes, films, minutes ;
    - bilan du mois calendaire en cours ;
    - rythme : épisodes par semaine (fenêtre 90 jours) ;
    - projection : date de fin estimée des séries en cours, à partir du
      nombre d'épisodes restants (Up Next) et du rythme hebdomadaire ;
    - derniers visionnages (5) ;
    - séries en cours : nombre, épisodes restants, minutes restantes.
    """
    now = datetime.now()
    try:
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo(timezone_name))
    except Exception:
        pass

    rows = normalize_history(dataset, timezone_name=timezone_name)
    df = build_frame(rows)
    if df.empty:
        return {"empty": True, "now": now}

    # ── Compteurs à vie ──────────────────────────────────────────────────────
    h_films = float(df.loc[df["type"] == "Film", "duree"].sum()) / 60
    h_series = float(df.loc[df["type"] == "Épisode", "duree"].sum()) / 60
    nb_films = int(df.loc[df["type"] == "Film", "titre"].nunique())
    nb_series = int(df.loc[df["type"] == "Épisode", "titre"].nunique())
    nb_ep = int((df["type"] == "Épisode").sum())
    total_minutes = int(df["duree"].sum())
    total_h = total_minutes / 60

    # ── Digest 7 jours ───────────────────────────────────────────────────────
    seuil_7j = now - timedelta(days=7)
    df7 = df[df["date_dt"] >= seuil_7j]
    digest_films = int((df7["type"] == "Film").sum())
    digest_eps = int((df7["type"] == "Épisode").sum())
    digest_minutes = int(df7["duree"].sum())

    # ── Bilan du mois calendaire en cours ────────────────────────────────────
    b_films = int(((df["date_dt"].dt.year == now.year) & (df["date_dt"].dt.month == now.month) & (df["type"] == "Film")).sum())
    b_eps = int(((df["date_dt"].dt.year == now.year) & (df["date_dt"].dt.month == now.month) & (df["type"] == "Épisode")).sum())
    b_minutes = int(df[(df["date_dt"].dt.year == now.year) & (df["date_dt"].dt.month == now.month)]["duree"].sum())

    # ── Rythme : épisodes par semaine (90 jours) ─────────────────────────────
    seuil_90j = now - timedelta(days=90)
    eps_90 = int((df["type"] == "Épisode").sum() if df["date_dt"].min() >= seuil_90j else ((df["type"] == "Épisode") & (df["date_dt"] >= seuil_90j)).sum())
    eps_dates = sorted(df.loc[df["type"] == "Épisode", "date_dt"].tolist())
    if eps_dates:
        fenetre = min(90, max(1, (now - eps_dates[0]).days))
        eps_sem = eps_90 / (fenetre / 7)
    else:
        eps_sem = None

    # ── Séries en cours (Up Next) : épisodes restants, hors abandonnées ──────
    progress = dataset.get("progress") or []
    if not progress and isinstance(dataset.get("sections"), dict):
        try:
            from normalized_model import build_progress
            progress = build_progress(dataset["sections"])
        except Exception:
            progress = []
    reste_actives = 0
    series_actives = len(progress)
    for row in progress:
        if isinstance(row, dict):
            reste_actives += int(row.get("remaining_episodes") or 0)

    # ── Projection : date de fin estimée ─────────────────────────────────────
    projection = None
    if eps_sem and eps_sem >= 0.5 and reste_actives > 0:
        projection = now + timedelta(weeks=reste_actives / eps_sem)

    # ── Derniers visionnages ─────────────────────────────────────────────────
    derniers = []
    for row in sorted(df.to_dict("records"), key=lambda r: r["date_dt"], reverse=True)[:5]:
        derniers.append(
            {
                "date": row["date_dt"],
                "type": row["type"],
                "titre": row["titre"],
            }
        )

    return {
        "empty": False,
        "now": now,
        "compteurs": {
            "h_films": h_films,
            "h_series": h_series,
            "nb_films": nb_films,
            "nb_series": nb_series,
            "nb_ep": nb_ep,
        },
        "total_minutes": total_minutes,
        "total_h": total_h,
        "digest": {"films": digest_films, "eps": digest_eps, "minutes": digest_minutes},
        "bilan": {
            "mois": f"{MOIS_NOMS[now.month - 1]} {now.year}",
            "films": b_films,
            "eps": b_eps,
            "heures": b_minutes / 60,
        },
        "eps_sem": eps_sem,
        "series_actives": series_actives,
        "reste_actives": reste_actives,
        "projection": projection,
        "derniers": derniers,
    }
