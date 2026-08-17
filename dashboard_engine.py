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
                "episode": row.get("episode_label") or "",
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


# ── Widgets restaurés de Trakt Smart Lists ──────────────────────────────────


def _media_note_public(media: dict[str, Any]) -> float | None:
    """Note publique (communauté) d'un média : score_average, score, ou ratings."""
    if not isinstance(media, dict):
        return None
    for key in ("score_average", "score"):
        try:
            value = float(media.get(key) or 0)
            if value > 0:
                return max(0.0, min(value / 10.0, 10.0))
        except (TypeError, ValueError):
            pass
    ratings = media.get("ratings") if isinstance(media.get("ratings"), list) else []
    for rating in ratings:
        if not isinstance(rating, dict):
            continue
        source = str(rating.get("source") or "").lower()
        raw = rating.get("value")
        try:
            note = float(raw)
        except (TypeError, ValueError):
            continue
        if note > 0 and source in ("imdb", "tmdb", "trakt", "mdblist"):
            if note > 10:
                note = note / 10.0
            return max(0.0, min(note, 10.0))
    return None


def compute_widgets(dataset: dict[str, Any], timezone_name: str = "Europe/Paris") -> dict[str, Any]:
    """Calcule les widgets restaurés (0 appel API) : coups de cœur,
    thermomètre de sévérité, rewatch radar, sorties de la semaine,
    plus ancien de la watchlist."""
    from zoneinfo import ZoneInfo
    try:
        now = datetime.now(ZoneInfo(timezone_name))
    except Exception:
        now = datetime.now()
    sections = dataset.get("sections") or {}
    watched = sections.get("watched") or {}
    ratings = sections.get("ratings") or {}
    watchlist = sections.get("watchlist") or {}
    sources = dataset.get("sources") or []

    # ── Index médias (titre, année, note publique) depuis watched ──
    media_index: dict[str, dict[str, Any]] = {}

    def key_of(media: dict[str, Any]) -> str:
        ids = media.get("ids") if isinstance(media.get("ids"), dict) else {}
        return str(ids.get("tmdb") or ids.get("imdb") or media.get("title") or "?")

    for row in watched.get("movies") or []:
        if not isinstance(row, dict):
            continue
        media = row.get("movie") if isinstance(row.get("movie"), dict) else row
        k = key_of(media)
        media_index[k] = {"titre": media.get("title"), "annee": media.get("year"),
                          "pub": _media_note_public(media), "id": media.get("id"),
                          "ids": media.get("ids") if isinstance(media.get("ids"), dict) else {}}
    for row in watched.get("shows") or []:
        if not isinstance(row, dict):
            continue
        media = row.get("show") if isinstance(row.get("show"), dict) else row
        k = key_of(media)
        media_index[k] = {"titre": media.get("title"), "annee": media.get("year"),
                          "pub": _media_note_public(media), "id": media.get("id"),
                          "ids": media.get("ids") if isinstance(media.get("ids"), dict) else {}}

    # ── Mes notes perso (ratings) ──
    mes_notes: list[dict[str, Any]] = []
    for row in ratings.get("movies") or []:
        if not isinstance(row, dict):
            continue
        media = row.get("movie") if isinstance(row.get("movie"), dict) else row
        try:
            note = float(row.get("rating") or 0)
        except (TypeError, ValueError):
            continue
        if note <= 0:
            continue
        mes_notes.append({"type": "Film", "titre": media.get("title"), "annee": media.get("year"),
                          "note": note, "ids": media.get("ids") if isinstance(media.get("ids"), dict) else {},
                          "media": media})
    for row in ratings.get("shows") or []:
        if not isinstance(row, dict):
            continue
        media = row.get("show") if isinstance(row.get("show"), dict) else row
        try:
            note = float(row.get("rating") or 0)
        except (TypeError, ValueError):
            continue
        if note <= 0:
            continue
        mes_notes.append({"type": "Série", "titre": media.get("title"), "annee": media.get("year"),
                          "note": note, "ids": media.get("ids") if isinstance(media.get("ids"), dict) else {},
                          "media": media})

    # ── Coups de cœur (mes notes ≥ 9) ──
    coups_de_coeur = [m for m in mes_notes if m["note"] >= 9]
    coups_de_coeur.sort(key=lambda x: (-x["note"], str(x["titre"] or "").casefold()))
    # Fallback : note publique ≥ 9 si je n'ai rien noté
    if not coups_de_coeur:
        fallback = [v for v in media_index.values() if (v.get("pub") or 0) >= 9]
        fallback.sort(key=lambda x: -(x.get("pub") or 0))
        coups_de_coeur = [{"type": "Film" if not None else "Film", "titre": v["titre"],
                           "annee": v["annee"], "note": v["pub"], "ids": v["ids"], "fallback": True}
                          for v in fallback[:5]]
    coups_de_coeur = coups_de_coeur[:5]

    # ── Thermomètre de sévérité (comparatif mes notes vs public) ──
    deltas: list[float] = []
    ecarts: list[dict[str, Any]] = []
    for m in mes_notes:
        ids = m.get("ids") or {}
        k = str(ids.get("tmdb") or ids.get("imdb") or m.get("titre") or "?")
        info = media_index.get(k) or {}
        pub = info.get("pub") or 0
        if pub <= 0 or m["note"] <= 0:
            # tenter la note publique depuis le média lui-même (enrichi)
            pub = _media_note_public(m.get("media")) or 0
        if pub <= 0:
            continue
        d = m["note"] - pub
        deltas.append(d)
        if abs(d) >= 2.0:
            ecarts.append({"type": m["type"], "titre": m["titre"], "annee": m["annee"],
                           "note": m["note"], "pub": pub, "ecart": d, "ids": ids})
    ecarts.sort(key=lambda x: -abs(x["ecart"]))
    ecarts = ecarts[:5]
    severite = None
    if deltas:
        moy = sum(deltas) / len(deltas)
        if moy <= -0.5:
            severite = {"moy": moy, "label": "SÉVÈRE", "emoji": "😈",
                        "txt": "tu notes en moyenne plus dur que le public", "couleur": "#ED2224"}
        elif moy >= 0.5:
            severite = {"moy": moy, "label": "INDULGENT", "emoji": "😇",
                        "txt": "tu notes en moyenne plus gentiment que le public", "couleur": "#00D084"}
        else:
            severite = {"moy": moy, "label": "PILE DANS LA MOYENNE", "emoji": "🎯",
                        "txt": "tes notes collent bien à celles du public", "couleur": "#CEDC00"}

    # ── Rewatch radar : films vus 1 seule fois il y a ≥ 3 ans, notés ≥ 8 ──
    rewatch = []
    for row in watched.get("movies") or []:
        if not isinstance(row, dict):
            continue
        media = row.get("movie") if isinstance(row.get("movie"), dict) else row
        try:
            plays = int(row.get("plays") or 1)
        except (TypeError, ValueError):
            plays = 1
        if plays != 1:
            continue
        pub = _media_note_public(media) or 0
        if pub < 8:
            continue
        last = row.get("last_watched_at") or row.get("watched_at")
        try:
            d = datetime.fromisoformat(str(last).replace("Z", "+00:00"))
            if d.tzinfo is None:
                d = d.replace(tzinfo=timezone.utc)
            jours = (now - d.astimezone(now.tzinfo)).days
        except Exception:
            continue
        if jours < 1095:  # 3 ans
            continue
        rewatch.append({"titre": media.get("title"), "annee": media.get("year"),
                        "note": pub, "ans": jours // 365,
                        "ids": media.get("ids") if isinstance(media.get("ids"), dict) else {}})
    rewatch.sort(key=lambda x: (-x["note"], -x["ans"]))
    rewatch = rewatch[:3]

    # ── Sorties de la semaine (films des listes qui sortent ≤ 7 jours) ──
    sorties = []
    aujourdhui = now.date()
    for source in sources:
        if not isinstance(source, dict):
            continue
        for movie in source.get("movies") or []:
            if not isinstance(movie, dict):
                continue
            rel = movie.get("released") or movie.get("release_date") or movie.get("premiere_date")
            if not rel:
                continue
            try:
                ds = datetime.fromisoformat(str(rel)[:10]).date()
            except Exception:
                continue
            j = (ds - aujourdhui).days
            if 0 <= j <= 7:
                ids = movie.get("ids") if isinstance(movie.get("ids"), dict) else {}
                sorties.append({"j": j, "date": ds, "titre": movie.get("title"), "annee": movie.get("year"),
                                "note": _media_note_public(movie) or 0, "ids": ids})
    sorties.sort(key=lambda x: (x["j"], -x["note"]))
    sorties = sorties[:3]

    # ── Plus ancien de la watchlist (≥ 60 jours) ──
    plus_ancien = None
    ancien = None
    for item in (watchlist.get("movies") or []) + (watchlist.get("shows") or []):
        if not isinstance(item, dict):
            continue
        la = item.get("listed_at") or item.get("watchlist_at")
        if not la:
            continue
        try:
            dt_l = datetime.fromisoformat(str(la).replace("Z", "+00:00"))
            if dt_l.tzinfo is None:
                dt_l = dt_l.replace(tzinfo=timezone.utc)
            dt_l = dt_l.astimezone(now.tzinfo)
        except Exception:
            continue
        if ancien is None or dt_l < ancien[0]:
            ancien = (dt_l, item.get("title"), item.get("year"))
    if ancien:
        jours = (now - ancien[0]).days
        if jours >= 60:
            plus_ancien = {"titre": ancien[1], "annee": ancien[2], "jours": jours}

    return {
        "coups_de_coeur": coups_de_coeur,
        "contre_courant": {"severite": severite, "ecarts": ecarts, "nb": len(deltas)},
        "rewatch": rewatch,
        "sorties": sorties,
        "plus_ancien": plus_ancien,
    }
