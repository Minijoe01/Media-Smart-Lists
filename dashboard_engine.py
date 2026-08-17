"""Tableau de bord — calculs locaux (aucun appel API).

Reprend les widgets de l'ancienne application Trakt Smart Lists :
bilan du mois, rythme d'épisodes par semaine, compteurs à vie films/séries,
digest hebdomadaire et projection de la date de fin des séries en cours
(hors séries abandonnées).
"""

from __future__ import annotations

from collections import defaultdict
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
    # Paliers affinés : ±0,5 pt = « un peu », ±1,5 pt = « très » (l'ancien
    # site classait dès ±0,5 pt, ce qui étiquetait « indulgent » un écart
    # quasi nul).
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
        if moy <= -1.5:
            severite = {"moy": moy, "label": "TRÈS SÉVÈRE", "emoji": "😈",
                        "txt": "tu notes beaucoup plus dur que le public", "couleur": "#ED2224"}
        elif moy <= -0.5:
            severite = {"moy": moy, "label": "PLUTÔT SÉVÈRE", "emoji": "😠",
                        "txt": "tu notes plutôt plus dur que le public", "couleur": "#ED8B24"}
        elif moy < 0.5:
            severite = {"moy": moy, "label": "DANS LA MOYENNE", "emoji": "🎯",
                        "txt": "tes notes collent bien à celles du public", "couleur": "#CEDC00"}
        elif moy < 1.5:
            severite = {"moy": moy, "label": "PLUTÔT INDULGENT", "emoji": "🙂",
                        "txt": "tu notes plutôt plus gentiment que le public", "couleur": "#00A392"}
        else:
            severite = {"moy": moy, "label": "TRÈS INDULGENT", "emoji": "😇",
                        "txt": "tu notes beaucoup plus gentiment que le public", "couleur": "#00D084"}

    # ── Rewatch radar : films vus 1 seule fois il y a ≥ 3 ans, notés ≥ 8 ──
    # Agrégation par film : dans un ZIP Trakt chaque visionnage est une ligne
    # séparée → sans regroupement, un film revu apparaîtrait plusieurs fois.
    movie_stats: dict[str, dict[str, Any]] = {}
    for row in watched.get("movies") or []:
        if not isinstance(row, dict):
            continue
        media = row.get("movie") if isinstance(row.get("movie"), dict) else row
        k = key_of(media)
        if not k or k == "?":
            continue
        try:
            plays = int(row.get("plays") or 1)
        except (TypeError, ValueError):
            plays = 1
        last = row.get("last_watched_at") or row.get("watched_at")
        entry = movie_stats.setdefault(
            k,
            {"plays": 0, "last": None, "media": media, "pub": _media_note_public(media) or 0},
        )
        entry["plays"] += plays
        if last and (entry["last"] is None or str(last) > str(entry["last"])):
            entry["last"] = last

    rewatch = []
    for k, entry in movie_stats.items():
        if entry["plays"] != 1:
            continue
        pub = entry.get("pub") or 0
        if pub < 8:
            continue
        media = entry["media"]
        last = entry.get("last")
        try:
            d = datetime.fromisoformat(str(last).replace("Z", "+00:00"))
            if d.tzinfo is None:
                d = d.replace(tzinfo=timezone.utc)
            jours = (now - d.astimezone(now.tzinfo)).days
        except Exception:
            continue
        if jours < 1095:  # 3 ans
            continue
        ids = media.get("ids") if isinstance(media.get("ids"), dict) else {}
        rewatch.append({"titre": media.get("title"), "annee": media.get("year"),
                        "note": pub, "ans": jours // 365,
                        "ids": ids})
    rewatch.sort(key=lambda x: (-x["note"], -x["ans"]))
    rewatch = rewatch[:3]

    # ── Séries en pause longue : dernier épisode vu il y a ≥ 2 ans ──
    # On exclut :
    #  - les séries abandonnées (dropped) ;
    #  - les séries terminées/annulées (statut connu) ;
    #  - les séries vues EN ENTIER : quand MDBList fournit la progression
    #    (Up Next non vide), une série absente d'Up Next n'a plus aucun
    #    épisode à voir — on ne peut pas « reprendre » un contenu fini.
    dropped_ids: set[str] = set()
    for row in (sections.get("dropped") or {}).get("shows") or []:
        if not isinstance(row, dict):
            continue
        media = row.get("show") if isinstance(row.get("show"), dict) else row
        ids = media.get("ids") if isinstance(media.get("ids"), dict) else {}
        dropped_ids.add(str(ids.get("tmdb") or ids.get("imdb") or media.get("title") or "").casefold())

    progress_rows = dataset.get("progress") or []
    progress_keys: set[str] = set()
    for row in progress_rows:
        if not isinstance(row, dict):
            continue
        show = row.get("show") if isinstance(row.get("show"), dict) else {}
        ids = show.get("ids") if isinstance(show.get("ids"), dict) else {}
        progress_keys.add(str(ids.get("tmdb") or ids.get("imdb") or show.get("title") or "").casefold())
    # ZIP Trakt sans métadonnées : Up Next vide → on ne peut pas détecter la
    # complétude, on garde le comportement précédent (statut seul).
    progression_disponible = bool(progress_keys)

    pause = []
    for row in watched.get("shows") or []:
        if not isinstance(row, dict):
            continue
        media = row.get("show") if isinstance(row.get("show"), dict) else row
        ids = media.get("ids") if isinstance(media.get("ids"), dict) else {}
        k = str(ids.get("tmdb") or ids.get("imdb") or media.get("title") or "?").casefold()
        if not k or k == "?" or k in dropped_ids:
            continue
        status = str(media.get("status") or "").strip().lower()
        if status in {"ended", "canceled", "end", "finished", "terminée", "annulée"}:
            continue
        if progression_disponible and k not in progress_keys:
            continue  # tout est vu : plus aucun épisode à reprendre
        last = row.get("last_watched_at") or row.get("watched_at") or media.get("last_watched_at")
        try:
            d = datetime.fromisoformat(str(last).replace("Z", "+00:00"))
            if d.tzinfo is None:
                d = d.replace(tzinfo=timezone.utc)
            jours = (now - d.astimezone(now.tzinfo)).days
        except Exception:
            continue
        if jours < 730:  # 2 ans
            continue
        pause.append({"titre": media.get("title"), "annee": media.get("year"),
                      "jours": jours, "ids": ids, "pub": _media_note_public(media) or 0})
    pause.sort(key=lambda x: -x["jours"])
    pause = pause[:3]

    # ── Records de binge + créneau préféré (depuis l'historique horodaté) ──
    # normalize_history est un calcul local sur les données déjà chargées :
    # aucun appel API supplémentaire.
    records = None
    creneau = None
    hist = normalize_history(dataset, timezone_name=timezone_name)
    ep_rows = [r for r in hist if r.get("type") == "Épisode" and isinstance(r.get("watched_at"), datetime)]
    if ep_rows:
        by_day: dict[date, dict[str, Any]] = {}
        by_month: dict[tuple[int, int], dict[str, Any]] = {}
        by_show: dict[str, dict[str, Any]] = {}
        for r in ep_rows:
            dt = r["watched_at"]
            day = dt.date()
            dd = by_day.setdefault(day, {"nb": 0, "min": 0.0, "shows": defaultdict(int), "titles": {}})
            dd["nb"] += 1
            dd["min"] += float(r.get("total_minutes") or 0)
            ids = r.get("ids") or {}
            show_key = str(ids.get("tmdb") or ids.get("imdb") or r.get("title") or "?")
            dd["shows"][show_key] += 1
            dd["titles"][show_key] = r.get("title")
            mk = (dt.year, dt.month)
            mm = by_month.setdefault(mk, {"nb": 0, "min": 0.0})
            mm["nb"] += 1
            mm["min"] += float(r.get("total_minutes") or 0)
            sm = by_show.setdefault(show_key, {"min": 0.0, "nb": 0, "titre": r.get("title"), "ids": ids})
            sm["min"] += float(r.get("total_minutes") or 0)
            sm["nb"] += 1
        jour_record = max(by_day.items(), key=lambda kv: (kv[1]["nb"], kv[1]["min"]))
        mois_record = max(by_month.items(), key=lambda kv: (kv[1]["nb"], kv[1]["min"]))
        serie_aval = max(by_show.values(), key=lambda v: (v["min"], v["nb"]))
        records = {
            "jour": {"date": jour_record[0], "nb": jour_record[1]["nb"], "min": jour_record[1]["min"],
                     "shows": jour_record[1]["titles"], "counts": dict(jour_record[1]["shows"])},
            "mois": {"key": mois_record[0], "nb": mois_record[1]["nb"], "min": mois_record[1]["min"]},
            "serie": {"titre": serie_aval["titre"], "nb": serie_aval["nb"],
                      "min": serie_aval["min"], "ids": serie_aval["ids"]},
        }

    if hist:
        bucket_min = {"Matin": 0.0, "Après-midi": 0.0, "Soir": 0.0, "Nuit": 0.0}
        for r in hist:
            dt = r.get("watched_at")
            if not isinstance(dt, datetime):
                continue
            minutes = float(r.get("total_minutes") or 0)
            hour = dt.hour
            if 6 <= hour < 12:
                bucket_min["Matin"] += minutes
            elif 12 <= hour < 18:
                bucket_min["Après-midi"] += minutes
            elif 18 <= hour < 22:
                bucket_min["Soir"] += minutes
            else:
                bucket_min["Nuit"] += minutes
        total = sum(bucket_min.values())
        if total > 0:
            emojis = {"Matin": "🌅", "Après-midi": "☀️", "Soir": "🌆", "Nuit": "🌙"}
            items = [{"label": label, "emoji": emojis[label], "min": minutes,
                      "pct": minutes / total * 100}
                     for label, minutes in bucket_min.items()]
            items.sort(key=lambda x: -x["min"])
            creneau = {"items": items, "top": items[0]}

    # ── Sorties de la semaine (films des listes qui sortent ≤ 7 jours) ──
    # Déduplication par identifiant : un film apparaît dans sa liste ET dans
    # les sources agrégées (statiques, personnelles, toutes) — on ne le garde
    # qu'une fois, à sa date la plus proche / meilleure note.
    sorties_map: dict[str, dict[str, Any]] = {}
    aujourdhui = now.date()
    for source in sources:
        if not isinstance(source, dict):
            continue
        for movie in source.get("movies") or []:
            if not isinstance(movie, dict):
                continue
            rel = movie.get("released") or movie.get("release_date") or movie.get("premiere_date") or movie.get("first_aired")
            if not rel:
                continue
            try:
                ds = datetime.fromisoformat(str(rel)[:10]).date()
            except Exception:
                continue
            j = (ds - aujourdhui).days
            if not (0 <= j <= 7):
                continue
            ids = movie.get("ids") if isinstance(movie.get("ids"), dict) else {}
            key = str(ids.get("tmdb") or ids.get("imdb") or str(movie.get("title") or "").casefold())
            note = _media_note_public(movie) or 0
            candidate = {"j": j, "date": ds, "titre": movie.get("title"), "annee": movie.get("year"),
                         "note": note, "ids": ids}
            existing = sorties_map.get(key)
            if existing is None or (j, -note) < (existing["j"], -existing.get("note", 0)):
                sorties_map[key] = candidate
    sorties = sorted(sorties_map.values(), key=lambda x: (x["j"], -x["note"]))
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
        "pause_longue": pause,
        "records": records,
        "creneau": creneau,
    }
