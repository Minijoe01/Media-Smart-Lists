"""Rendez-vous annuel (Wrapped) de Media Smart Lists.

Reprend la logique et le rendu de la page « Rendez-vous annuel » de l'ancienne
application Trakt Smart Lists : indicateurs annuels, tops, genres, heures par
mois et image PNG partageable façon Spotify Wrapped (1080×1350), aux couleurs
du thème Aston Martin F1 2026.
"""

from __future__ import annotations

import io
import os
from datetime import datetime
from typing import Any

import pandas as pd

from history_engine import normalize_history
from stats_engine import build_frame

# ── Constantes PNG (thème) ───────────────────────────────────────────────────
W_PNG, H_PNG = 1080, 1350
_P_GREEN = (0, 163, 146)
_P_LIME = (206, 220, 0)
_P_TEXT = (240, 250, 248)
_P_MUTED = (157, 197, 191)
_P_BG_TOP = (0, 107, 98)
_P_BG_BOT = (1, 23, 21)
_P_CARD = (8, 55, 50)
_P_BORDER = (18, 90, 84)
_BRAND = "M E D I A   S M A R T   L I S T S"
_SITE = "media-smart-lists.streamlit.app"

MOIS_NOMS = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
]
MOIS_COURTS = ["Janv.", "Fév.", "Mars", "Avr.", "Mai", "Juin",
               "Juil.", "Août", "Sept.", "Oct.", "Nov.", "Déc."]


def _png_police(taille: int, gras: bool = False):
    """Police DejaVu si dispo (fonts/ du dépôt), sinon fallback Pillow."""
    from PIL import ImageFont
    nom = "DejaVuSans-Bold.ttf" if gras else "DejaVuSans.ttf"
    try:
        base = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        base = os.getcwd()
    chemins = [
        os.path.join(base, "fonts", nom),
        os.path.join("fonts", nom),
        "/usr/share/fonts/truetype/dejavu/" + nom,
        nom,
    ]
    for chemin in chemins:
        try:
            return ImageFont.truetype(chemin, taille)
        except Exception:
            pass
    try:
        return ImageFont.load_default(size=taille)
    except Exception:
        return ImageFont.load_default()


def _png_centre(dr, txt: str, y: int, font, fill: tuple[int, int, int], w: int = W_PNG) -> None:
    tw = dr.textlength(txt, font=font)
    dr.text(((w - tw) / 2, y), txt, font=font, fill=fill)


def _png_tronque(dr, txt: str, font, max_w: int) -> str:
    if dr.textlength(txt, font=font) <= max_w:
        return txt
    while txt and dr.textlength(txt + "…", font=font) > max_w:
        txt = txt[:-1]
    return txt + "…"


def _png_font_ajuste(dr, txt: str, max_w: int, taille_max: int, taille_min: int = 40, gras: bool = True):
    taille = taille_max
    while taille > taille_min:
        font = _png_police(taille, gras)
        if dr.textlength(txt, font=font) <= max_w:
            return font
        taille -= 10
    return _png_police(taille_min, gras)


def generer_image_wrapped(d: dict[str, Any]) -> bytes:
    """Image PNG 1080×1350 façon Spotify Wrapped, aux couleurs de l'app."""
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (W_PNG, H_PNG), _P_BG_BOT)
    dr = ImageDraw.Draw(img, "RGB")

    # Fond : dégradé vertical comme l'app.
    bandes = 140
    for i in range(bandes):
        t = i / (bandes - 1)
        r = int(_P_BG_TOP[0] + (_P_BG_BOT[0] - _P_BG_TOP[0]) * t)
        g = int(_P_BG_TOP[1] + (_P_BG_BOT[1] - _P_BG_TOP[1]) * t)
        b = int(_P_BG_TOP[2] + (_P_BG_BOT[2] - _P_BG_TOP[2]) * t)
        dr.rectangle([0, int(i * H_PNG / bandes), W_PNG, int((i + 1) * H_PNG / bandes) + 1], fill=(r, g, b))
    dr.rectangle([0, 0, W_PNG, 10], fill=_P_LIME)

    f_xs = _png_police(28)
    f_s = _png_police(34)
    f_s_b = _png_police(34, True)
    f_m_b = _png_police(44, True)
    f_l_b = _png_police(58, True)

    M = 70
    col_w = W_PNG - 2 * M

    y = 55
    _png_centre(dr, _BRAND, y, f_xs, _P_MUTED)
    y += 58
    _png_centre(dr, f"MON ANNÉE {d['annee']}", y, f_l_b, _P_LIME)

    # Hero : temps total (taille auto-ajustée).
    y += 115
    total_txt = str(d["total"])
    f_hero = _png_font_ajuste(dr, total_txt, col_w, 260, 90)
    _png_centre(dr, total_txt, y, f_hero, _P_TEXT)
    y += int(getattr(f_hero, "size", 200) * 0.80) + 36
    _png_centre(dr, "de films & séries regardés", y, f_s, _P_MUTED)

    # 3 stat cards.
    y += 56
    gap = 24
    cw = (col_w - 2 * gap) // 3
    ch = 140
    for i, (lbl, val) in enumerate([("FILMS", d["films"]), ("SÉRIES", d["series"]), ("ÉPISODES", d["episodes"])]):
        x0 = M + i * (cw + gap)
        dr.rounded_rectangle([x0, y, x0 + cw, y + ch], radius=24, fill=_P_CARD, outline=_P_BORDER, width=2)
        cx = x0 + cw // 2
        tw = dr.textlength(lbl, font=f_xs)
        dr.text((cx - tw / 2, y + 22), lbl, font=f_xs, fill=_P_MUTED)
        tw = dr.textlength(str(val), font=f_l_b)
        dr.text((cx - tw / 2, y + 58), str(val), font=f_l_b, fill=_P_LIME)

    # Tops 2 colonnes.
    y += ch + 48
    col2 = (col_w - gap) // 2
    bloc_h = 380

    def bloc_top(x0: int, titre: str, items: list[tuple[str, int]], footer: str) -> None:
        dr.rounded_rectangle([x0, y, x0 + col2, y + bloc_h], radius=24, fill=_P_CARD, outline=_P_BORDER, width=2)
        dr.text((x0 + 30, y + 24), titre, font=f_m_b, fill=_P_GREEN)
        yy = y + 88
        for i, (t, n) in enumerate(items[:5], 1):
            label = f"{i}. "
            phrase = f"{n}×"
            dr.text((x0 + 30, yy), label, font=f_s_b, fill=_P_LIME)
            lw = dr.textlength(label, font=f_s_b)
            t_aff = _png_tronque(dr, t, f_s, col2 - 60 - lw - 78)
            dr.text((x0 + 30 + lw, yy), t_aff, font=f_s, fill=_P_TEXT)
            pw = dr.textlength(phrase, font=f_s)
            dr.text((x0 + col2 - 30 - pw, yy), phrase, font=f_s, fill=_P_MUTED)
            yy += 45
        dr.rectangle([x0 + 30, y + bloc_h - 56, x0 + col2 - 30, y + bloc_h - 54], fill=_P_BORDER)
        dr.text((x0 + 30, y + bloc_h - 42), footer, font=f_xs, fill=_P_MUTED)

    bloc_top(M, "TOP FILMS", d["top_films"] or [("—", 0)], f"note moyenne {d['note_moy']}/10")
    bloc_top(M + col2 + gap, "TOP SÉRIES", d["top_series"] or [("—", 0)], f"record : {d['record_txt']}")

    # Genres (clampé pour rester au-dessus du pied de page).
    y += bloc_h + 40
    y = min(y, H_PNG - 176)
    genres_txt = "  ·  ".join(g.upper() for g, _ in (d["top_genres"] or [])[:3]) or "CINÉMA & SÉRIES"
    f_genres = _png_font_ajuste(dr, genres_txt, col_w, 44, 28)
    _png_centre(dr, genres_txt, y, f_genres, _P_LIME)

    # Footer.
    dr.rectangle([M, H_PNG - 92, W_PNG - M, H_PNG - 88], fill=_P_BORDER)
    _png_centre(dr, f"{_SITE}  ·  généré le {d['date_gen']}", H_PNG - 70, f_xs, _P_MUTED)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def format_duree_fr(minutes: int) -> str:
    """Durée compacte en français (heures) : « 142 h », « 3 j 4 h »…"""
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


def _annee_str(series_annee: "pd.Series") -> "pd.Series":
    """Colonne année en texte sûr pour regrouper ('1995', '?')."""
    return series_annee.apply(lambda v: str(int(v)) if pd.notna(v) else "?")


def _nb_contenus_distincts(part: "pd.DataFrame") -> int:
    """Contenus DISTINCTS = couples (titre, année) — V115.

    Compter les titres uniques fusionnait deux films homonymes : Mortal
    Kombat 1995 + Mortal Kombat 2024 = « 1 film » vu (et 2 visionnages
    sur la même ligne du top). La paire titre+année les sépare.
    """
    if part is None or part.empty:
        return 0
    key = part["titre"].astype(str) + "||" + _annee_str(part["annee"])
    return int(key.nunique())


def _top_contenus(part: "pd.DataFrame", n: int = 5) -> list[tuple[str, int]]:
    """Top contenus V115 : regroupés par titre ET année de sortie.

    Deux films homonymes (ex. Mortal Kombat 1995 / 2024) ne sont plus
    fusionnés (signalé utilisateur). L'année n'est AFFICHÉE que si le
    titre revient sur plusieurs années différentes — les autres libellés
    restent strictement inchangés (aucun « (2021) » parasite sur tous
    les tops).
    """
    if part is None or part.empty:
        return []
    df = part.copy()
    df["annee_s"] = _annee_str(df["annee"])
    tailles = df.groupby(["titre", "annee_s"]).size().sort_values(ascending=False)
    annees_par_titre = df.groupby("titre")["annee_s"].nunique()
    out: list[tuple[str, int]] = []
    for (titre, annee_s), taille in tailles.head(n).items():
        ambigu = int(annees_par_titre.get(titre, 1)) > 1
        label = f"{titre} ({annee_s})" if ambigu and annee_s != "?" else str(titre)
        out.append((label, int(taille)))
    return out


def compute_wrapped(dataset: dict[str, Any], year: int, timezone_name: str = "Europe/Paris") -> dict[str, Any]:
    """Calcule tous les indicateurs annuels pour une année donnée."""
    rows = normalize_history(dataset, timezone_name=timezone_name)
    df = build_frame(rows)
    if df.empty:
        return {}
    df = df.copy()
    df["annee_vue"] = df["date_dt"].dt.year
    df["mois_vue"] = df["date_dt"].dt.month
    df["duree_h"] = df["duree"].fillna(0) / 60
    df_y = df[df["annee_vue"] == year].copy()
    if df_y.empty:
        return {}

    total_h = float(df_y["duree_h"].sum())
    films_df = df_y[df_y["type"] == "Film"]
    eps_df = df_y[df_y["type"] == "Épisode"]
    # V115 : films/séries distincts comptés par (titre, année) — deux films
    # homonymes sont bien DEUX contenus différents.
    nb_films = _nb_contenus_distincts(films_df)
    nb_eps = int(len(eps_df))
    nb_series = _nb_contenus_distincts(eps_df)
    notes = df_y.loc[df_y["note"] > 0, "note"]
    note_moy = float(notes.mean()) if not notes.empty else 0.0

    par_jour = df_y.groupby(df_y["date_dt"].dt.date).size()
    jour_peak = par_jour.idxmax() if not par_jour.empty else None
    nb_peak = int(par_jour.max()) if not par_jour.empty else 0
    mois_peak = int(df_y.groupby("mois_vue").size().idxmax()) if not df_y.empty else 0

    # V115 : tops par (titre, année) — plus de fusion Mortal Kombat 1995/2024.
    top_films = _top_contenus(films_df)
    top_series = _top_contenus(eps_df)

    genres_n: dict[str, int] = {}
    for raw in df_y["genre"].fillna("").astype(str).str.split(" · "):
        for genre in raw:
            if genre and genre != "Inconnu":
                genres_n[genre] = genres_n.get(genre, 0) + 1
    top_genres = sorted(genres_n.items(), key=lambda kv: -kv[1])[:5]

    heures_mois = (
        df_y.groupby("mois_vue")["duree_h"].sum().reindex(range(1, 13), fill_value=0).round(1)
    )

    return {
        "year": year,
        "total_h": total_h,
        "films": nb_films,
        "series": nb_series,
        "episodes": nb_eps,
        "note_moy": note_moy,
        "jour_peak": jour_peak,
        "nb_peak": nb_peak,
        "mois_peak": mois_peak,
        "top_films": top_films,
        "top_series": top_series,
        "top_genres": top_genres,
        "heures_mois": heures_mois,
    }
