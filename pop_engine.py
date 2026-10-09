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
GROQ_BASE = "https://api.groq.com/openai/v1"
# Préférence Groq : petits modèles RAPIDES d'abord (les quotas gratuits sont
# par modèle : les petits sont les plus généreux — 2026).
GROQ_MODEL_PREFERENCE = [
    "openai/gpt-oss-20b",
    "llama-3.1-8b-instant",
    "openai/gpt-oss-120b",
    "llama-3.3-70b-versatile",
]
_GROQ_EXCLUDE = ("whisper", "guard", "embed", "tts", "vision", "compound", "distil-whisper")

# Suffixes de modèles inutilisables pour nos cas d'usage (image/audio/embedding).
_MODEL_EXCLUDE = ("-image", "-tts", "-live", "-native-audio", "-thinking", "-embedding", "aqa", "-vl")

# Cache des modèles résolus, PAR CLÉ (hashée — jamais la clé en clair), TTL 6 h.
_model_cache: dict[str, tuple[float, list[str]]] = {}
_MODEL_TTL = 6 * 3600.0
_groq_model_cache: dict[str, tuple[float, str]] = {}


def _cache_get(cache: dict, key: str, ttl: float):
    entry = cache.get(key)
    if entry and (_time.time() - entry[0]) < ttl:
        return entry[1]
    return None


def _cache_set(cache: dict, key: str, value) -> None:
    cache[key] = (_time.time(), value)
    if len(cache) > 40:  # garde-fou mémoire
        for old_key, _ in sorted(cache.items(), key=lambda kv: kv[1][0])[:15]:
            cache.pop(old_key, None)


def _ranked_flash_models(raw_names: list[str]) -> list[str]:
    """Classe les modèles Flash disponibles POUR TA CLÉ (V153).

    ORDRE : les FLASH-LITE d'abord — leur quota gratuit est largement plus
    généreux (les Flash « standard » récents peuvent être limités à
    quelques dizaines de requêtes/jour : retour utilisateur « je crois que
    je n'ai que 20 tokens par jour », 429 dès la première journée).
    Pour nos usages (anecdotes courtes, choix parmi 40 candidats), un
    flash-lite est largement suffisant.

    Détail : 1) alias gemini-flash-lite-latest ; 2) versions lite stables,
    plus haute d'abord ; 3) alias gemini-flash-latest ; 4) versions flash
    stables puis previews, plus hautes d'abord."""
    names = [
        str(n).removeprefix("models/") for n in raw_names
        if "flash" in str(n) and not any(x in str(n) for x in _MODEL_EXCLUDE)
    ]
    seen: set[str] = set()
    names = [n for n in names if not (n in seen or seen.add(n))]
    if not names:
        return [GEMINI_FALLBACK_MODEL]

    def _stable(name: str) -> bool:
        return "preview" not in name and "exp" not in name

    def _version(name: str) -> float:
        match = re.search(r"gemini-(\d+(?:\.\d+)?)", name)
        return float(match.group(1)) if match else -1.0

    lite_alias = [n for n in names if n == "gemini-flash-lite-latest"]
    lite_stable = sorted([n for n in names if "lite" in n and _stable(n) and n not in lite_alias],
                         key=_version, reverse=True)
    flash_alias = [n for n in names if n == GEMINI_FALLBACK_MODEL]
    flash_stable = sorted([n for n in names if "lite" not in n and _stable(n) and n not in flash_alias],
                          key=_version, reverse=True)
    previews = sorted([n for n in names if not _stable(n)], key=_version, reverse=True)
    ranked = lite_alias + lite_stable + flash_alias + flash_stable + previews
    return ranked or [GEMINI_FALLBACK_MODEL]


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
    return resolve_gemini_models_ranked(api_key, refresh=refresh)[0]


def resolve_gemini_models_ranked(api_key: str, refresh: bool = False) -> list[str]:
    """La liste ORDONNÉE des modèles à essayer (V153) : flash-lite d'abord
    (quota gratuit généreux), puis flash. Le premier est le choix par
    défaut ; les suivants servent de SECOURS en cas de 429 (quota du
    modèle épuisé) — cf. _gemini_post_json."""
    if not api_key:
        return [GEMINI_FALLBACK_MODEL]
    key_hash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:16]
    cached = None if refresh else _cache_get(_model_cache, key_hash, _MODEL_TTL)
    if cached:
        return cached
    try:
        names = list_gemini_models(api_key)
    except RuntimeError:
        return cached or [GEMINI_FALLBACK_MODEL]
    ranked = _ranked_flash_models(names) if names else [GEMINI_FALLBACK_MODEL]
    _cache_set(_model_cache, key_hash, ranked)
    return ranked


def _gemini_url(api_key: str, model: str | None = None) -> str:
    return f"{GEMINI_BASE}/models/{model or resolve_gemini_model(api_key)}:generateContent"


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


def _gemini_post_json(api_key: str, body: dict, what: str) -> dict:
    """POST generateContent — INFAILLIBLE (V153) :

      • 503 (Google surchargé) : 3 tentatives, pause 1 s puis 2,5 s ;
      • 429 (quota du MODÈLE épuisé) : bascule AUTOMATIQUE sur le modèle
        suivant de la liste ranked (flash-lite d'abord) — l'utilisateur
        n'a pas à y penser ;
      • 404 : modèle retiré → modèle suivant aussi ;
      • 401/403 : clé refusée (raison lisible).

    Le tout avec un timeout de 30 s par tentative."""
    if not api_key:
        raise RuntimeError("Clé Gemini absente")
    models = resolve_gemini_models_ranked(api_key)[:3] or [GEMINI_FALLBACK_MODEL]
    last_error = ""
    for model in models:
        for attempt in (1, 2, 3):
            try:
                response = requests.post(
                    _gemini_url(api_key, model),
                    params={"key": api_key},
                    json=body,
                    timeout=30,
                )
            except requests.RequestException as exc:
                last_error = f"Réseau indisponible ({exc.__class__.__name__})"
                if attempt < 3:
                    _time.sleep(1.0 if attempt == 1 else 2.5)
                    continue
                break  # modèle suivant
            if response.status_code == 503:
                last_error = "Google surchargé (503)"
                if attempt < 3:
                    _time.sleep(1.0 if attempt == 1 else 2.5)
                    continue
                break  # modèle suivant
            if response.status_code in (401, 403):
                raise RuntimeError("Clé Gemini refusée (401/403) — vérifie GEMINI_API_KEY dans les Secrets")
            if response.status_code == 429:
                # quota de CE modèle épuisé → modèle suivant (flash-lite…)
                last_error = f"Quota épuisé pour {model}"
                break
            if response.status_code == 404:
                last_error = f"Modèle {model} refusé (404)"
                break  # modèle suivant
            if response.status_code != 200:
                raise RuntimeError(f"Gemini a répondu HTTP {response.status_code}")
            return response
    # tous les modèles ont échoué
    key_hash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:16]
    _model_cache.pop(key_hash, None)
    if "Quota" in last_error:
        raise RuntimeError("Quota Gemini épuisé pour aujourd'hui (tous les modèles essayés)")
    raise RuntimeError(last_error or "Gemini indisponible")


def _gemini_json_body(prompt: str, temperature: float, max_tokens: int,
                      model: str = "", safe: bool = False) -> dict:
    """Corps de requête Gemini. V154 — deux garde-fous anti-HTTP 400 :
      • `safe=True` : corps MINIMAL (aucun thinkingConfig, budget relevé) —
        utilisé pour le retry automatique si un 400 survient ;
      • sinon, thinkingConfig ADAPTÉ AU MODÈLE : les Gemini 3.x rejettent
        `thinkingBudget: 0` avec un 400 (cause du bug V153 après le passage
        aux flash-lite 3.x) — on ne l'envoie qu'aux Gemini 2.x, qui l'acceptent."""
    body: dict = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": int(max_tokens * 1.5) if safe else max_tokens,
            "responseMimeType": "application/json",
        },
    }
    if not safe and model and "gemini-3" not in model:
        body["generationConfig"]["thinkingConfig"] = {"thinkingBudget": 0}
    return body


def _gemini_post_json(api_key: str, body: dict, what: str, model: str = "") -> dict:
    """POST generateContent Gemini — INFAILLIBLE (V154) :

      • 400 (requête refusée, ex. thinkingConfig non supporté par un modèle
        neuf) → RETRY immédiat en mode « safe » : corps minimal sans
        thinkingConfig et budget de tokens relevé ;
      • 503 → 3 tentatives (pause 1 s puis 2,5 s) ;
      • 429 (quota du modèle) → bascule sur le modèle suivant de la liste
        ranked (flash-lite d'abord, quota gratuit plus large) ;
      • 404 → modèle retiré → modèle suivant aussi."""
    models = resolve_gemini_models_ranked(api_key)[:3] or [GEMINI_FALLBACK_MODEL]
    if model and model in models:
        models = [model] + [m for m in models if m != model]
    last_error = ""
    safe_tried = False
    for current in models[:3]:
        for attempt in (1, 2, 3):
            try:
                response = requests.post(
                    _gemini_url(api_key, current),
                    params={"key": api_key},
                    json=body,
                    timeout=30,
                )
            except requests.RequestException as exc:
                last_error = f"Réseau indisponible ({exc.__class__.__name__})"
                if attempt < 3:
                    _time.sleep(1.0 if attempt == 1 else 2.5)
                    continue
                break  # modèle suivant
            if response.status_code == 400:
                # V154 — UNE fois par appel : corps MINIMAL (sans
                # thinkingConfig, budget relevé). Cause typique du 400 :
                # thinkingBudget refusé par les Gemini 3.x.
                if not safe_tried:
                    safe_tried = True
                    temp0 = (body.get("generationConfig") or {}).get("temperature", 0.9)
                    body = _gemini_json_body(_LAST_PROMPT[0], temp0, 1400, safe=True)
                    continue
                last_error = "Requête refusée (400) même en mode simplifié"
                break  # modèle suivant
            if response.status_code == 503:
                last_error = "Google surchargé (503)"
                if attempt < 3:
                    _time.sleep(1.0 if attempt == 1 else 2.5)
                    continue
                break
            if response.status_code in (401, 403):
                raise RuntimeError("Clé Gemini refusée (401/403) — vérifie GEMINI_API_KEY dans les Secrets")
            if response.status_code == 429:
                last_error = f"Quota épuisé pour {current}"
                break  # modèle suivant
            if response.status_code == 404:
                last_error = f"Modèle {current} refusé (404)"
                break
            if response.status_code != 200:
                raise RuntimeError(f"Gemini a répondu HTTP {response.status_code}")
            return response
    key_hash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:16]
    _model_cache.pop(key_hash, None)
    if "Quota" in last_error:
        raise RuntimeError("Quota Gemini épuisé pour aujourd'hui (tous les modèles essayés)")
    raise RuntimeError(last_error or "Gemini indisponible")


# Le prompt courant (pour reconstruire un corps « safe » après un 400).
_LAST_PROMPT: list[str] = [""]


def _gemini_text(response: dict) -> str:
    """Extrait le texte d'une réponse Gemini (candidates[0].content.parts[0])."""
    try:
        candidate0 = (response.json().get("candidates") or [{}])[0]
        return str((candidate0.get("content") or {}).get("parts", [{}])[0].get("text") or "")
    except (ValueError, IndexError, KeyError, TypeError):
        return ""


def groq_list_models(groq_key: str) -> list[str]:
    """Modèles de chat disponibles POUR CETTE CLÉ Groq (1 appel lecture
    seule, 0 quota). Lève RuntimeError (raison lisible)."""
    if not groq_key:
        raise RuntimeError("Clé Groq absente")
    try:
        response = requests.get(
            f"{GROQ_BASE}/models",
            headers={"Authorization": f"Bearer {groq_key}"},
            timeout=15,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"Réseau indisponible ({exc.__class__.__name__})") from exc
    if response.status_code in (401, 403):
        raise RuntimeError("Clé Groq refusée (401/403)")
    if response.status_code == 429:
        raise RuntimeError("Quota Groq atteint (429)")
    if response.status_code != 200:
        raise RuntimeError(f"HTTP {response.status_code}")
    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError("Réponse illisible") from exc
    out = []
    for model in (payload.get("data") or []):
        if not isinstance(model, dict):
            continue
        mid = str(model.get("id") or "")
        if mid and not any(x in mid for x in _GROQ_EXCLUDE):
            out.append(mid)
    return out


def resolve_groq_model(groq_key: str, refresh: bool = False) -> str:
    """Le modèle Groq à utiliser (cache 6 h) : premier de la liste de
    préférence présent pour ta clé, sinon le premier modèle de chat dispo."""
    if not groq_key:
        return ""
    key_hash = hashlib.sha256(groq_key.encode("utf-8")).hexdigest()[:16]
    cached = None if refresh else _cache_get(_groq_model_cache, key_hash, _MODEL_TTL)
    if cached:
        return cached
    try:
        names = groq_list_models(groq_key)
    except RuntimeError:
        return cached or ""
    model = next((m for m in GROQ_MODEL_PREFERENCE if m in names), "")
    if not model and names:
        model = names[0]
    if model:
        _cache_set(_groq_model_cache, key_hash, model)
    return model


def _groq_chat(groq_key: str, prompt: str, temperature: float,
               max_tokens: int, what: str) -> str:
    """Un appel Groq (API compatible OpenAI) → le texte de la réponse.
    JSON strict via response_format. Retry 503/timeout ×2, 429 explicite."""
    model = resolve_groq_model(groq_key)
    if not model:
        raise RuntimeError("Aucun modèle Groq disponible pour cette clé")
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }
    last_error = ""
    for attempt in (1, 2):
        try:
            response = requests.post(
                f"{GROQ_BASE}/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}"},
                json=body,
                timeout=30,
            )
        except requests.RequestException as exc:
            last_error = f"Réseau indisponible ({exc.__class__.__name__})"
            if attempt == 1:
                _time.sleep(1.0)
                continue
            raise RuntimeError(last_error)
        if response.status_code == 503 and attempt == 1:
            last_error = "Groq surchargé (503)"
            _time.sleep(1.0)
            continue
        if response.status_code in (401, 403):
            raise RuntimeError("Clé Groq refusée (401/403) — vérifie GROQ_API_KEY")
        if response.status_code == 429:
            raise RuntimeError("Quota Groq atteint (429) — réessaie plus tard")
        if response.status_code == 404:
            _groq_model_cache.pop(hashlib.sha256(groq_key.encode("utf-8")).hexdigest()[:16], None)
            raise RuntimeError(f"Modèle Groq {model} refusé (404)")
        if response.status_code != 200:
            raise RuntimeError(f"Groq a répondu HTTP {response.status_code}")
        try:
            return str(response.json()["choices"][0]["message"]["content"] or "")
        except (ValueError, KeyError, IndexError, TypeError):
            raise RuntimeError("Réponse Groq illisible")
    raise RuntimeError(last_error or "Groq indisponible")


def ia_complete(gemini_key: str, groq_key: str, prompt: str,
                temperature: float, max_tokens: int, what: str) -> str:
    """LE point d'entrée unique de l'IA (V154) — provider + secours croisé :

      • si une clé GROQ_API_KEY est posée → Groq D'ABORD (très rapide,
        quotas gratuits généreux) ;
      • si l'appel échoue (quota, surcharge…) → bascule sur Gemini
        (si sa clé est là) — et réciproquement ;
      • chaque provider a déjà ses propres retries/bascules de modèle.

    Renvoie le TEXTE de la réponse (JSON strict attendu)."""
    errors: list[str] = []
    if groq_key:
        try:
            return _groq_chat(groq_key, prompt, temperature, max_tokens, what)
        except RuntimeError as exc:
            errors.append(f"Groq : {exc}")
    if gemini_key:
        try:
            _LAST_PROMPT[0] = prompt
            model = resolve_gemini_model(gemini_key)
            body = _gemini_json_body(prompt, temperature, max_tokens, model=model)
            response = _gemini_post_json(gemini_key, body, what, model=model)
            return _gemini_text(response)
        except RuntimeError as exc:
            errors.append(f"Gemini : {exc}")
    raise RuntimeError(" · ".join(errors) or "Aucune clé IA configurée")


def pop_ask_ai(gemini_key: str, groq_key: str, mood: str, candidates: list[dict]) -> dict:
    """Appelle Gemini (endpoint NATIF, compatible clés AQ. et AIza).

    Renvoie {"pick_id": int, "reason": str, "model": str} ou lève
    `RuntimeError(raison lisible)` — l'app affiche alors le mode local.

    V150 — thinkingBudget: 0 : les modèles Gemini 2.5 « réfléchissent » par
    défaut et les tokens de réflexion SONT décomptés de maxOutputTokens —
    avec un petit budget, la réponse arrivait VIDE (finishReason
    MAX_TOKENS sans aucun texte) et POP basculait silencieusement en mode
    local (retour utilisateur : « · Local » malgré la clé détectée).
    """
    if not gemini_key and not groq_key:
        raise RuntimeError("Aucune clé IA configurée")
    text = ia_complete(gemini_key, groq_key, _gemini_prompt(mood, candidates), 0.9, 1200, "pop")
    if not text.strip():
        raise RuntimeError("Réponse IA vide — relance")
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
    return {"pick_id": pick_id, "reason": reason, "model": "ia"}


def ai_key_check(gemini_key: str, groq_key: str) -> tuple[bool, str]:
    """Diagnostic des clés IA (V154) : 1 appel LECTURE seule par provider
    (liste des modèles — 0 quota de génération). Indique le provider ACTIF
    (Groq si sa clé est posée, sinon Gemini), le modèle retenu et les
    secours. Copie-colle le message à l'assistant en cas de souci."""
    parts: list[str] = []
    ok = False
    if groq_key:
        try:
            names = groq_list_models(groq_key)
            model = next((m for m in GROQ_MODEL_PREFERENCE if m in names), names[0] if names else "")
            parts.append(f"Groq (ACTIF) : clé valide ✅ · modèle : {model}"
                         + (f" · {len(names)} modèle(s) visible(s)" if names else ""))
            ok = True
        except RuntimeError as exc:
            parts.append(f"Groq (ACTIF) : ❌ {exc}")
    if gemini_key:
        try:
            names = list_gemini_models(gemini_key)
            ranked = _ranked_flash_models(names) if names else [GEMINI_FALLBACK_MODEL]
            role = "secours" if groq_key else "ACTIF"
            parts.append(f"Gemini ({role}) : clé valide ✅ · modèle : {ranked[0]} (lite d'abord)"
                         + (f" · secours : {', '.join(ranked[1:4])}" if len(ranked) > 1 else ""))
            ok = ok or not groq_key
        except RuntimeError as exc:
            parts.append(f"Gemini ({'secours' if groq_key else 'ACTIF'}) : ❌ {exc}")
    if not parts:
        return False, "Aucune clé IA : ajoute GEMINI_API_KEY et/ou GROQ_API_KEY dans les Secrets."
    return ok, " · ".join(parts)

def coulisses_ask_ai(gemini_key: str, groq_key: str, subject: str, hint: str = "") -> dict:
    """🎲 L'INFO DES COULISSES (V152) — un SEUL appel Gemini pour :
      • une ANECDOTE de tournage/casting (zéro spoiler) ;
      • 2-3 POINTS FORTS et 2-3 POINTS DE VIGILANCE « côté spectateurs »
        (ce que les gens aiment / reprochent — ex. « rythme lent », « 3 h
        de longueur ») : des infos qu'on ne trouve PAS sur TMDB
        (demande utilisateur).

    Retourne {"anecdote": str, "pros": [..], "cons": [..]}. Lève
    RuntimeError (raison lisible). Retry 503/timeout inclus.
    """
    if not gemini_key and not groq_key:
        raise RuntimeError("Aucune clé IA configurée")
    prompt = (
        "Tu es un passionné de cinéma et de séries qui connaît les coulisses de "
        "tournage ET le sentiment du public. À propos de "
        f"{subject}" + (f" ({hint})" if hint else "") + ", produis :\n"
        "1. UNE anecdote SURPRENANTE et VÉRIFIÉE (tournage, casting, coulisses, "
        "record) — 2 à 4 phrases, en FRANÇAIS, ton complice ;\n"
        "2. Deux à trois POINTS FORTS tels que les spectateurs les décrivent "
        "(ex : photographie somptueuse, casting au sommet, bande originale) ;\n"
        "3. Deux à trois POINTS DE VIGILANCE honnêtes, ceux que les spectateurs "
        "les moins conquis reprochent (ex : rythme lent, durée, fin divisive) — "
        "sois franc, pas complaisant.\n"
        "Règles strictes :\n"
        "- AUCUN SPOILER de l'intrigue ni de la fin, nulle part ;\n"
        "- VARIE les sujets : ne raconte pas systématiquement l'anecdote la "
        "plus célèbre liée à son rôle le plus iconique — pioche dans toute "
        "sa carrière (débuts, autres œuvres, coulisses, rencontres) ;\n"
        "- points forts et vigilance : des expressions COURTES (max 8 mots), "
        "pas des phrases ;\n"
        "- si un doute existe sur un fait précis, préfère une anecdote plus "
        "générale mais EXACTE ;\n"
        "- tout en français, varie à chaque appel.\n"
        'Réponds STRICTEMENT en JSON : {"anecdote": "…", "pros": ["…", "…"], '
        '"cons": ["…", "…"]}'
    )
    text = ia_complete(gemini_key, groq_key, prompt, 1.1, 1400, "coulisses")
    if not text.strip():
        raise RuntimeError("Réponse IA vide — relance")
    try:
        parsed = json.loads(text)
    except ValueError:
        raise RuntimeError("Réponse illisible — relance")
    anecdote = str(parsed.get("anecdote") or "").strip()
    pros = [str(x).strip() for x in (parsed.get("pros") or []) if str(x).strip()][:3]
    cons = [str(x).strip() for x in (parsed.get("cons") or []) if str(x).strip()][:3]
    if len(anecdote) < 30:
        raise RuntimeError("Réponse incomplète — relance")
    return {"anecdote": anecdote, "pros": pros, "cons": cons}


def freeform_ask_ai(gemini_key: str, groq_key: str, wish: str, candidates: list[dict]) -> dict:
    """✍️ POP LIBRE (V152) : l'utilisateur décrit son envie en une phrase
    (« un film d'amour sur un bateau »). Un SEUL appel Gemini :

      • "in_list"  : le meilleur candidat PARMI ses listes (id fourni) ;
      • "outside"  : UNE œuvre réelle hors de ses listes qui colle aussi
        à l'envie (titre + année + type) — l'app la retrouve ensuite sur
        TMDB (recherche par titre).

    Retourne {"in_list_id": int, "outside": {"title","year","kind"},
    "reason": str}."""
    if not gemini_key and not groq_key:
        raise RuntimeError("Aucune clé IA configurée")
    wish = str(wish or "").strip()
    if len(wish) < 3:
        raise RuntimeError("Décris ton envie en quelques mots")
    payload = [
        {"i": c["id"], "t": c["title"], "k": c["kind"], "y": c["year"],
         "g": c["genres"], "d": c["runtime"], "r": c["note"], "s": c["source"]}
        for c in candidates
    ]
    json_shape = (
        '{"in_list_id": <champ i du contenu choisi>, '
        '"outside": {"title": "<titre>", "year": <année int>, "kind": "Film"|"Série"}, '
        '"reason": "<2 à 3 phrases en français, ton enthousiaste et personnel, '
        'sans spoiler, qui explique les deux choix au regard de ton envie>"}'
    )
    prompt = (
        "Tu es un conseiller cinéma et séries francophone. L'envie du moment de "
        f"l'utilisateur : « {wish} ».\n"
        "Voici les contenus disponibles dans SES listes (JSON) :\n"
        f"{json.dumps(payload, ensure_ascii=False)}\n\n"
        "Choisis :\n"
        "1. LE meilleur contenu DE SA LISTE qui correspond à l'envie (champ i) ;\n"
        "2. UNE AUTRE œuvre, RÉELLE et reconnue, qui n'est PAS dans cette liste "
        "et qui colle encore mieux à l'envie — titre exact, année, Film ou Série. "
        "Pour une série très connue, son titre français usuel convient.\n"
        "Réponds STRICTEMENT en JSON, sans texte autour :\n"
        f"{json_shape}"
    )
    text = ia_complete(gemini_key, groq_key, prompt, 0.9, 1200, "pop-libre")
    if not text.strip():
        raise RuntimeError("Réponse IA vide — relance")
    try:
        parsed = json.loads(text)
    except ValueError:
        raise RuntimeError("Réponse illisible — relance")
    try:
        in_list_id = int(parsed.get("in_list_id") or 0)
    except (TypeError, ValueError):
        in_list_id = 0
    outside = parsed.get("outside") if isinstance(parsed.get("outside"), dict) else {}
    reason = str(parsed.get("reason") or "").strip()
    if not in_list_id or not reason:
        raise RuntimeError("Réponse incomplète — relance")
    try:
        year = int(outside.get("year") or 0) or None
    except (TypeError, ValueError):
        year = None
    return {
        "in_list_id": in_list_id,
        "outside": {
            "title": str(outside.get("title") or "").strip(),
            "year": year,
            "kind": "Série" if str(outside.get("kind") or "").strip().lower() in ("série", "serie", "tv") else "Film",
        },
        "reason": reason,
    }

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
