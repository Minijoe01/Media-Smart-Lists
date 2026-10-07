"""🍿 POP — « Tire-moi LA pépite » (V149).

Moteur de suggestion par HUMEUR, propulsé par Gemini (Google AI Studio) :

  1. CANDIDATS : tes contenus NON vus déjà présents dans ta Watchlist et tes
     listes — scorés localement (note TMDB, intention watchlist, un soupçon
     d'aléa pour varier les sessions) → top 40 envoyés à l'IA.
  2. GEMINI choisit LA pépite (une seule) pour l'humeur demandée et rédige
     2-3 phrases de justification — sans spoiler.
  3. Repli LOCAL si pas de clé / quota dépassé / erreur : le même top 40 est
     filtré par un mapping humeur → genres, sans aucun appel réseau.

CONFIDENTIALITÉ : seuls titre, année, type, genres, durée, note et source des
candidats sont envoyés à Google — jamais tes notes personnelles, ton
historique de visionnage ni aucune donnée de compte.

CLÉ : `GEMINI_API_KEY` dans les Secrets Streamlit. Les clés récentes
commencent par « AQ. » (nouveau format « Auth key », juin 2026), les anciennes
par « AIza » — les deux fonctionnent : on appelle l'ENDPOINT NATIF Gemini
(generativelanguage.googleapis.com, clé en paramètre `key`), pas un endpoint
compatible OpenAI (qui rejette les clés AQ.).
"""

from __future__ import annotations

import json
import random
import re
from typing import Any

import requests

# ── Humeurs proposées (libellé affiché, consigne IA, indices locaux) ─────────
# `genres` sert au REPLI LOCAL : genres boostés (prioritaires), `avoid`
# pénalisés. `retro` : bonus pour les contenus sortis avant 2000.
POP_MOODS: dict[str, dict[str, Any]] = {
    "🛋️ Cocooning": {
        "hint": "envie de douceur, de réconfort, d'une histoire qui fait du bien, sans tension",
        "genres": ["Comédie", "Famille", "Romance", "Animation", "Drame"],
        "avoid": ["Horreur", "Thriller", "Guerre"],
    },
    "😱 Grand frisson": {
        "hint": "envie d'avoir peur, de tension, d'atmosphère glacial et de frissons",
        "genres": ["Horreur", "Thriller", "Mystère"],
        "avoid": ["Comédie", "Famille", "Animation"],
    },
    "😂 Rire garanti": {
        "hint": "envie de rire, d'humour, de légèreté, de oublier la journée",
        "genres": ["Comédie", "Comédie musicale"],
        "avoid": ["Horreur", "Guerre", "Documentaire"],
    },
    "😭 Émotions fortes": {
        "hint": "envie d'être bouleversé, de pleurer, d'un drame puissant et humain",
        "genres": ["Drame", "Romance", "Histoire"],
        "avoid": ["Horreur", "Action"],
    },
    "💥 Adrénaline": {
        "hint": "envie de rythme, de spectacle, d'action effrénée et de poursuites",
        "genres": ["Action", "Aventure", "Thriller", "Crime"],
        "avoid": ["Documentaire", "Drame"],
    },
    "🧠 Cérébral": {
        "hint": "envie de se creuser la tête, de mystère, de science-fiction ou d'enquête ingénieuse",
        "genres": ["Science-Fiction", "Mystère", "Thriller", "Documentaire"],
        "avoid": ["Romance", "Famille"],
    },
    "✨ Nostalgie": {
        "hint": "envie d'un classique, d'un film d'époque, de charme rétro",
        "genres": [],
        "avoid": [],
        "retro": True,
    },
    "🎲 Surprise-moi": {
        "hint": "carte blanche : sors des sentiers battus, étonne-moi",
        "genres": [],
        "avoid": [],
    },
}

GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"


def pop_candidate_pool(dataset: dict, kind: str = "Peu importe", limit: int = 40) -> list[dict]:
    """Top `limit` contenus NON vus de ta Watchlist + listes, scorés localement.

    Score local (0-100+) : note publique ×10, +8 si dans la Watchlist
    (intention explicite), +10 si note ≥ 8 (coup de cœur du public), et un
    aléa ±12 pour que deux sessions ne proposent pas toujours le même top.
    """
    sections = dataset.get("sections") if isinstance(dataset.get("sections"), dict) else {}
    watched: set[int] = set()
    for row in (sections.get("watched") or {}).get("movies") or []:
        ids = row.get("ids") if isinstance(row.get("ids"), dict) else {}
        try:
            if ids.get("tmdb"):
                watched.add(int(ids["tmdb"]))
        except (TypeError, ValueError):
            pass
    for row in (sections.get("watched") or {}).get("shows") or []:
        ids = row.get("ids") if isinstance(row.get("ids"), dict) else {}
        try:
            if ids.get("tmdb"):
                watched.add(int(ids["tmdb"]))
        except (TypeError, ValueError):
            pass

    pool: list[dict] = []
    seen_ids: set[int] = set()

    def _push(media: dict, source: str, kind_label: str) -> None:
        ids = media.get("ids") if isinstance(media.get("ids"), dict) else {}
        try:
            tmdb = int(ids.get("tmdb") or 0)
        except (TypeError, ValueError):
            tmdb = 0
        if not tmdb or tmdb in seen_ids or tmdb in watched:
            return
        title = str(media.get("title_fr") or media.get("title") or media.get("name") or "").strip()
        if not title:
            return
        seen_ids.add(tmdb)
        date = str(media.get("release_date") or media.get("first_air_date") or "")
        year = date[:4] if len(date) >= 4 else ""
        try:
            note = float(media.get("score") or 0) / 10.0
        except (TypeError, ValueError):
            note = 0.0
        try:
            runtime = int(media.get("runtime") or 0)
        except (TypeError, ValueError):
            runtime = 0
        genres = [str(g) for g in (media.get("genres") or []) if g][:4]
        score = note * 10
        if source == "Watchlist":
            score += 8
        if note >= 8:
            score += 10
        score += random.uniform(-12, 12)
        pool.append({
            "id": tmdb, "title": title, "kind": kind_label, "year": year,
            "genres": genres, "runtime": runtime, "note": round(note, 1),
            "source": source, "score": score,
            "poster": str(media.get("poster_fr") or media.get("poster") or ""),
        })

    watchlist = sections.get("watchlist") or {}
    if kind in ("Peu importe", "Film"):
        for media in watchlist.get("movies") or []:
            _push(media, "Watchlist", "Film")
    if kind in ("Peu importe", "Série"):
        for media in watchlist.get("shows") or []:
            _push(media, "Watchlist", "Série")
    for user_list in sections.get("user_lists") or []:
        if not isinstance(user_list, dict):
            continue
        name = str(user_list.get("name") or "Liste")
        if kind in ("Peu importe", "Film"):
            for media in user_list.get("movies") or []:
                _push(media, name, "Film")
        if kind in ("Peu importe", "Série"):
            for media in user_list.get("shows") or []:
                _push(media, name, "Série")

    pool.sort(key=lambda row: -row["score"])
    return pool[:limit]


def _gemini_prompt(mood: str, candidates: list[dict]) -> str:
    mood_cfg = POP_MOODS.get(mood) or POP_MOODS["🎲 Surprise-moi"]
    payload = [
        {"i": c["id"], "t": c["title"], "k": c["kind"], "y": c["year"],
         "g": c["genres"], "d": c["runtime"], "r": c["note"], "s": c["source"]}
        for c in candidates
    ]
    return (
        "Tu es un conseiller cinéma et séries francophone, chaleureux, concis, "
        "avec un goût prononcé pour les pépites.\n"
        f"L'humeur du moment de l'utilisateur : « {mood} » — {mood_cfg['hint']}.\n"
        "Voici les contenus disponibles dans SES listes (JSON) :\n"
        f"{json.dumps(payload, ensure_ascii=False)}\n\n"
        "Choisis LE contenu qui correspond le mieux à cette humeur, en privilégiant :\n"
        "1. l'accord émotionnel avec l'humeur demandée (critère n°1) ;\n"
        "2. les pépites un peu méconnues plutôt que les blockbusters ultra-connus ;\n"
        "3. la qualité (note) et la facilité (durée raisonnable).\n"
        "Réponds STRICTEMENT en JSON, sans aucun texte autour :\n"
        '{"pick_id": <le champ i du contenu choisi>, "reason": "<2 à 3 phrases '
        "en français, ton enthousiaste et personnel, SANS SPOILER, qui explique "
        'pourquoi ce contenu colle parfaitement à cette humeur>"}'
    )


def pop_ask_gemini(api_key: str, mood: str, candidates: list[dict]) -> dict:
    """Appelle Gemini (endpoint NATIF, compatible clés AQ. et AIza).

    Renvoie {"pick_id": int, "reason": str, "model": str} ou lève
    `RuntimeError(raison lisible)` — l'app affiche alors le mode local.
    """
    if not api_key:
        raise RuntimeError("Clé Gemini absente")
    body = {
        "contents": [{"parts": [{"text": _gemini_prompt(mood, candidates)}]}],
        "generationConfig": {
            "temperature": 0.9,
            "maxOutputTokens": 400,
            "responseMimeType": "application/json",
        },
    }
    try:
        response = requests.post(
            GEMINI_URL,
            params={"key": api_key},
            json=body,
            timeout=25,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"Réseau indisponible ({exc.__class__.__name__})") from exc
    if response.status_code in (401, 403):
        raise RuntimeError("Clé Gemini refusée (401/403) — vérifie GEMINI_API_KEY dans les Secrets")
    if response.status_code == 429:
        raise RuntimeError("Quota Gemini atteint (429) — réessaie plus tard")
    if response.status_code != 200:
        raise RuntimeError(f"Gemini a répondu HTTP {response.status_code}")
    try:
        data = response.json()
        text = str((data.get("candidates") or [{}])[0]
                   .get("content", {}).get("parts", [{}])[0].get("text") or "")
    except (ValueError, IndexError, KeyError, TypeError) as exc:
        raise RuntimeError("Réponse Gemini illisible") from exc
    try:
        parsed = json.loads(text)
    except ValueError:
        match = re.search(r'"pick_id"\s*:\s*(\d+)', text)
        if not match:
            raise RuntimeError("Réponse Gemini sans choix exploitable")
        parsed = {"pick_id": int(match.group(1)),
                  "reason": (re.sub(r'^[{}\s"]+|[}\s"]+$', "", text) or "").strip()}
    try:
        pick_id = int(parsed.get("pick_id") or 0)
    except (TypeError, ValueError):
        pick_id = 0
    reason = str(parsed.get("reason") or "").strip()
    if not pick_id or not reason:
        raise RuntimeError("Réponse Gemini incomplète")
    return {"pick_id": pick_id, "reason": reason, "model": GEMINI_MODEL}


def pop_pick_local(mood: str, candidates: list[dict], exclude_ids: set[int] | None = None) -> dict | None:
    """Repli SANS IA : mapping humeur → genres sur le même top de candidats."""
    if not candidates:
        return None
    exclude_ids = exclude_ids or set()
    mood_cfg = POP_MOODS.get(mood) or POP_MOODS["🎲 Surprise-moi"]
    wanted = {str(g).casefold() for g in mood_cfg.get("genres") or []}
    avoid = {str(g).casefold() for g in mood_cfg.get("avoid") or []}

    def _mood_score(candidate: dict) -> float:
        genres = {str(g).casefold() for g in candidate.get("genres") or []}
        score = float(candidate.get("score") or 0)
        if wanted:
            score += 25 * len(genres & wanted)
        if avoid:
            score -= 20 * len(genres & avoid)
        if mood_cfg.get("retro"):
            try:
                if candidate.get("year") and int(candidate["year"]) < 2000:
                    score += 25
            except (TypeError, ValueError):
                pass
        return score

    pool = [c for c in candidates if c["id"] not in exclude_ids] or list(candidates)
    pool.sort(key=lambda c: -_mood_score(c))
    best = pool[0]
    genres_txt = ", ".join(best.get("genres") or []) or "un mélange atypique"
    year_txt = f" ({best['year']})" if best.get("year") else ""
    reason = (
        f"Sélection locale (sans IA) : {best['title']}{year_txt} sort en tête "
        f"pour l'humeur « {mood} » grâce à ses genres ({genres_txt}) et sa "
        "note. Ajoute ta clé Gemini dans les Secrets pour des justifications "
        "sur mesure !"
    )
    return {"pick_id": best["id"], "reason": reason, "model": "local"}
