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

MODÈLE (V151) — plus de nom en dur : les modèles Gemini sont retirés au fil
de l'eau (gemini-2.0-flash éteint en juin 2026, gemini-2.5-flash réservé aux
ANCIENS projets dès l'été 2026 → 404 pour toute clé neuve). Le moteur LISTE
donc les modèles disponibles POUR TA CLÉ (GET /v1beta/models, 0 quota) et
choisit automatiquement le meilleur Flash (alias gemini-flash-latest en
priorité, sinon le numéro de version le plus haut, stable avant preview,
flash avant flash-lite). Le choix est mis en cache 6 h par clé.
"""

from __future__ import annotations

import hashlib
import json
import random
import re
import time as _time
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

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_FALLBACK_MODEL = "gemini-flash-latest"  # alias Google : toujours le dernier Flash stable

# Suffixes de modèles inutilisables pour nos cas d'usage (image/audio/embedding).
_MODEL_EXCLUDE = ("-image", "-tts", "-live", "-native-audio", "-thinking", "-embedding", "aqa", "-vl")

# Cache du modèle résolu, PAR CLÉ (hashée — jamais la clé en clair), TTL 6 h.
_model_cache: dict[str, tuple[float, str]] = {}
_MODEL_TTL = 6 * 3600.0


def _pick_flash_model(raw_names: list[str]) -> str:
    """Choisit le meilleur modèle Flash dans la liste renvoyée par l'API :
    1. l'alias « gemini-flash-latest » (toujours à jour) s'il est présent ;
    2. sinon : STABLE avant preview (fiabilité), puis numéro de version le
       plus haut, puis « flash » avant « flash-lite ».
       Ex : 3.6-flash > 3.1-flash-lite > 2.5-flash > 3.8-flash-preview."""
    names = [
        str(n).removeprefix("models/") for n in raw_names
        if "flash" in str(n) and not any(x in str(n) for x in _MODEL_EXCLUDE)
    ]
    if not names:
        return GEMINI_FALLBACK_MODEL
    if GEMINI_FALLBACK_MODEL in names:
        return GEMINI_FALLBACK_MODEL

    def _rank(name: str):
        match = re.search(r"gemini-(\d+(?:\.\d+)?)", name)
        version = float(match.group(1)) if match else -1.0
        return ("preview" not in name and "exp" not in name, version, "lite" not in name)

    return sorted(names, key=_rank, reverse=True)[0]


def list_gemini_models(api_key: str) -> list[str]:
    """Liste les modèles disponibles POUR CETTE CLÉ (1 appel lecture seule,
    0 quota de génération). Lève RuntimeError (raison lisible) si échec."""
    if not api_key:
        raise RuntimeError("Clé Gemini absente")
    try:
        response = requests.get(
            f"{GEMINI_BASE}/models",
            params={"key": api_key, "pageSize": 100},
            timeout=15,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"Réseau indisponible ({exc.__class__.__name__})") from exc
    if response.status_code in (401, 403):
        raise RuntimeError("Clé refusée (401/403)")
    if response.status_code == 429:
        raise RuntimeError("Quota atteint (429)")
    if response.status_code != 200:
        raise RuntimeError(f"HTTP {response.status_code}")
    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError("Réponse illisible") from exc
    out = []
    for model in (payload.get("models") or []):
        if not isinstance(model, dict):
            continue
        name = str(model.get("name") or "")
        methods = [str(m) for m in (model.get("supportedGenerationMethods") or [])]
        if name and ("generateContent" in methods or not methods):
            out.append(name)
    return out


def resolve_gemini_model(api_key: str, refresh: bool = False) -> str:
    """Le modèle à utiliser POUR CETTE CLÉ (V151 — fini le nom en dur).

    Découverte dynamique + cache 6 h. En cas d'échec réseau : alias public
    « gemini-flash-latest » (ou le dernier choix connu)."""
    if not api_key:
        return GEMINI_FALLBACK_MODEL
    key_hash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:16]
    now = _time.time()
    cached = _model_cache.get(key_hash)
    if cached and not refresh and (now - cached[0]) < _MODEL_TTL:
        return cached[1]
    try:
        names = list_gemini_models(api_key)
    except RuntimeError:
        return cached[1] if cached else GEMINI_FALLBACK_MODEL
    model = _pick_flash_model(names) if names else GEMINI_FALLBACK_MODEL
    _model_cache[key_hash] = (now, model)
    return model


def _gemini_url(api_key: str) -> str:
    return f"{GEMINI_BASE}/models/{resolve_gemini_model(api_key)}:generateContent"


def pop_candidate_pool(dataset: dict, kind: str = "Peu importe", limit: int = 40) -> list[dict]:
    """Top `limit` contenus NON vus de ta Watchlist + listes, scorés localement.

    Score local (0-100+) : note publique ×10, +8 si dans la Watchlist
    (intention explicite), +10 si note ≥ 8 (coup de cœur du public), et un
    aléa ±12 pour que deux sessions ne proposent pas toujours le même top.
    """
    sections = dataset.get("sections") if isinstance(dataset.get("sections"), dict) else {}
    # V150 — clés TYPO-PRÉFIXÉES « movie:{id} » / « tv:{id} » : un film et
    # une série peuvent partager le même id TMDB (Days of Thunder &
    # Supercopter = 2119) — sans le préfixe, l'un masquait l'autre.
    watched: set[str] = set()
    for bucket, prefix in (("movies", "movie"), ("shows", "tv")):
        for row in (sections.get("watched") or {}).get(bucket) or []:
            ids = row.get("ids") if isinstance(row.get("ids"), dict) else {}
            try:
                if ids.get("tmdb"):
                    watched.add(f"{prefix}:{int(ids['tmdb'])}")
            except (TypeError, ValueError):
                pass

    pool: list[dict] = []
    seen_ids: set[str] = set()

    def _push(media: dict, source: str, kind_label: str) -> None:
        ids = media.get("ids") if isinstance(media.get("ids"), dict) else {}
        try:
            tmdb = int(ids.get("tmdb") or 0)
        except (TypeError, ValueError):
            tmdb = 0
        typed = f"{'tv' if kind_label == 'Série' else 'movie'}:{tmdb}"
        if not tmdb or typed in seen_ids or typed in watched:
            return
        title = str(media.get("title_fr") or media.get("title") or media.get("name") or "").strip()
        if not title:
            return
        seen_ids.add(typed)
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

    V150 — thinkingBudget: 0 : les modèles Gemini 2.5 « réfléchissent » par
    défaut et les tokens de réflexion SONT décomptés de maxOutputTokens —
    avec un petit budget, la réponse arrivait VIDE (finishReason
    MAX_TOKENS sans aucun texte) et POP basculait silencieusement en mode
    local (retour utilisateur : « · Local » malgré la clé détectée).
    """
    if not api_key:
        raise RuntimeError("Clé Gemini absente")
    model = resolve_gemini_model(api_key)
    body = {
        "contents": [{"parts": [{"text": _gemini_prompt(mood, candidates)}]}],
        "generationConfig": {
            "temperature": 0.9,
            "maxOutputTokens": 1200,
            "responseMimeType": "application/json",
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }
    try:
        response = requests.post(
            _gemini_url(api_key),
            params={"key": api_key},
            json=body,
            timeout=30,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"Réseau indisponible ({exc.__class__.__name__})") from exc
    if response.status_code in (401, 403):
        raise RuntimeError("Clé Gemini refusée (401/403) — vérifie GEMINI_API_KEY dans les Secrets")
    if response.status_code == 429:
        raise RuntimeError("Quota Gemini atteint (429) — réessaie plus tard")
    if response.status_code == 404:
        # V151 : le modèle choisi n'est pas disponible pour cette clé → on
        # purge le cache et on oriente vers le diagnostic (qui liste les
        # modèles réellement visibles par la clé).
        _model_cache.pop(hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:16], None)
        raise RuntimeError(
            f"Modèle {model} refusé (404) — ouvre « 🔧 Diagnostic de la clé Gemini » "
            "sur la page POP et donne le message à l'assistant"
        )
    if response.status_code != 200:
        raise RuntimeError(f"Gemini a répondu HTTP {response.status_code}")
    try:
        data = response.json()
    except ValueError as exc:
        raise RuntimeError("Réponse Gemini illisible (pas du JSON)") from exc
    try:
        candidate0 = (data.get("candidates") or [{}])[0]
        text = str((candidate0.get("content") or {}).get("parts", [{}])[0].get("text") or "")
    except (IndexError, KeyError, TypeError):
        text = ""
    if not text.strip():
        finish = str(candidate0.get("finishReason") or "?")
        raise RuntimeError(f"Réponse Gemini vide (finishReason: {finish})")
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
    return {"pick_id": pick_id, "reason": reason, "model": model}


def gemini_key_check(api_key: str) -> tuple[bool, str]:
    """Diagnostic de la clé (V150) : 1 appel LECTURE seule (liste des
    modèles — ne consomme PAS de quota de génération). Renvoie
    (ok, message lisible) pour l'afficher sur la page POP.

    V151 : affiche aussi le MODÈLE qui sera utilisé par POP et les
    anecdotes (choisi automatiquement parmi les modèles de la clé)."""
    if not api_key:
        return False, "Aucune clé GEMINI_API_KEY dans les Secrets."
    try:
        names = list_gemini_models(api_key)
    except RuntimeError as exc:
        return False, f"{exc} — vérifie la valeur de GEMINI_API_KEY dans les Secrets Streamlit."
    model = _pick_flash_model(names) if names else GEMINI_FALLBACK_MODEL
    flash_models = [
        n.removeprefix("models/") for n in names
        if "flash" in n and not any(x in n for x in _MODEL_EXCLUDE)
    ]
    details = f"Clé valide ✅ · modèle retenu : {model}"
    if flash_models:
        details += f" · Flash disponibles : {', '.join(flash_models[:6])}"
    elif names:
        details += " (aucun modèle Flash visible — voici les modèles : " + ", ".join(n.removeprefix('models/') for n in names[:5]) + ")"
    return True, details


def anecdote_ask_gemini(api_key: str, subject: str, hint: str = "") -> str:
    """🎲 UNE anecdote générée par Gemini sur un sujet (film ou personne) —
    V150, demande utilisateur : « des anecdotes dans les fiches film et
    acteur qui se rafraîchiraient à chaque fois ».

    • température 1.2 → varie à chaque appel (pas toujours la même) ;
    • thinkingBudget 0 → réponse rapide, budget non mangé par la réflexion ;
    • consigne STRICTE : aucune intrigue révélée (zéro spoiler), fait précis
      de tournage/casting/coulisses, 2 à 4 phrases en français.

    `subject` : « le film « Blade Runner 2049 » (2017) » ou
    « la carrière de l'acteur Ryan Gosling ». `hint` : précision libre
    (réalisateur, genre, série…). Lève RuntimeError (raison lisible).
    """
    if not api_key:
        raise RuntimeError("Clé Gemini absente")
    prompt = (
        "Tu es un passionné de cinéma et de séries qui connaît mille anecdotes "
        "de tournage. Raconte UNE SEULE anecdote SURPRENANTE sur "
        f"{subject}" + (f" ({hint})" if hint else "") + ".\n"
        "Consignes strictes :\n"
        "- 2 à 4 phrases, en FRANÇAIS, ton complice et vivant ;\n"
        "- AUCUN SPOILER : ne révèle RIEN de l'intrigue ni de la fin ;\n"
        "- un fait PRÉCIS et vérifiable (tournage, casting, coulisses, record,\n"
        "  accueil du public) — pas de généralité ni d'invention ;\n"
        "- si tu n'es pas certain d'un fait précis sur ce sujet, raconte une\n"
        "  anecdote plus générale mais EXACTE à son sujet ;\n"
        "- change d'anecdote à chaque appel — jamais deux fois la même.\n"
        'Réponds STRICTEMENT en JSON : {"anecdote": "<le texte de l\'anecdote>"}'
    )
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 1.2,
            "maxOutputTokens": 800,
            "responseMimeType": "application/json",
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }
    try:
        response = requests.post(
            _gemini_url(api_key),
            params={"key": api_key},
            json=body,
            timeout=30,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"Réseau indisponible ({exc.__class__.__name__})") from exc
    if response.status_code in (401, 403):
        raise RuntimeError("Clé refusée (401/403)")
    if response.status_code == 429:
        raise RuntimeError("Quota atteint (429)")
    if response.status_code != 200:
        raise RuntimeError(f"HTTP {response.status_code}")
    try:
        data = response.json()
        candidate0 = (data.get("candidates") or [{}])[0]
        text = str((candidate0.get("content") or {}).get("parts", [{}])[0].get("text") or "")
    except (ValueError, IndexError, KeyError, TypeError):
        text = ""
    if not text.strip():
        raise RuntimeError(f"Réponse vide (finishReason: {candidate0.get('finishReason') or '?'})")
    try:
        parsed = json.loads(text)
        anecdote = str(parsed.get("anecdote") or "").strip()
    except ValueError:
        anecdote = (re.sub(r'^[{}\s"]+|[}\s"]+$', "", text) or "").strip()
    if len(anecdote) < 30:
        raise RuntimeError("Anecdote trop courte — relance")
    return anecdote


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
