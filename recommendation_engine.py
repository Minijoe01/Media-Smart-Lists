"""Moteur de recommandation explicable, fournisseur-neutre et sans appel API."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from statistics import median
from typing import Any

from normalized_model import media_key, media_type


ENGINE_VERSION = 1


def _nested_media(row: dict[str, Any]) -> dict[str, Any]:
    for key in ("movie", "show"):
        value = row.get(key)
        if isinstance(value, dict):
            return value
    return row


def _genres(item: dict[str, Any]) -> list[str]:
    media = _nested_media(item)
    values = media.get("genres") or item.get("genres") or []
    output = []
    for value in values:
        if isinstance(value, dict):
            value = value.get("name") or value.get("slug")
        if value:
            output.append(str(value).strip().title())
    return sorted(set(output))


def _runtime(item: dict[str, Any]) -> int:
    media = _nested_media(item)
    try:
        return max(int(round(float(media.get("runtime") or item.get("runtime") or 0))), 0)
    except (TypeError, ValueError):
        return 0


def _year(item: dict[str, Any]) -> int | None:
    media = _nested_media(item)
    value = media.get("year") or item.get("release_year") or item.get("year")
    try:
        return int(value) if value else None
    except (TypeError, ValueError):
        return None


def _status(item: dict[str, Any]) -> str:
    media = _nested_media(item)
    return str(media.get("status") or item.get("status") or "").strip().lower()


def _ratings(item: dict[str, Any]) -> list[dict[str, Any]]:
    media = _nested_media(item)
    values = media.get("ratings") or item.get("ratings") or []
    return [value for value in values if isinstance(value, dict)]


def _community_note(item: dict[str, Any]) -> float | None:
    # MDB Score est déjà sur 100.
    for value in (item.get("score"), item.get("score_average")):
        try:
            if value is not None:
                return max(0.0, min(float(value) / 10.0, 10.0))
        except (TypeError, ValueError):
            pass
    indexed = {
        str(value.get("source") or "").lower(): value
        for value in _ratings(item)
    }
    for source in ("imdb", "tmdb", "trakt", "letterboxd"):
        value = indexed.get(source)
        if not value:
            continue
        raw = value.get("value") if value.get("value") is not None else value.get("rating")
        try:
            note = float(raw)
        except (TypeError, ValueError):
            continue
        if note > 10:
            note /= 10
        return max(0.0, min(note, 10.0))
    return None


def _votes(item: dict[str, Any]) -> int:
    best = 0
    for value in _ratings(item):
        try:
            best = max(best, int(value.get("votes") or 0))
        except (TypeError, ValueError):
            pass
    return best


def _added_days(item: dict[str, Any], now: datetime) -> int | None:
    value = item.get("watchlist_at") or item.get("added_at") or item.get("added") or item.get("created_at")
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return max((now - parsed.astimezone(timezone.utc)).days, 0)
    except Exception:
        return None


def build_profile(dataset: dict[str, Any]) -> dict[str, Any]:
    sections = dataset.get("sections") or {}
    watched = sections.get("watched") or {}
    ratings = sections.get("ratings") or {}
    genre_counts: Counter[str] = Counter()
    decades: Counter[int] = Counter()
    movie_runtimes: list[int] = []
    metadata_by_key: dict[str, dict[str, Any]] = {}

    history_items = list(watched.get("movies") or []) + list(watched.get("shows") or [])
    for row in history_items:
        media = _nested_media(row)
        metadata_by_key[media_key(media)] = media
        for genre in _genres(media):
            genre_counts[genre] += 1
        year = _year(media)
        if year:
            decades[(year // 10) * 10] += 1
        if media_type(media) == "movie":
            runtime = _runtime(media)
            if runtime:
                movie_runtimes.append(runtime)

    total_genres = sum(genre_counts.values()) or 1
    genre_affinity = {
        genre: round(count / total_genres * 100, 2)
        for genre, count in genre_counts.items()
    }

    genre_rating_values: dict[str, list[float]] = defaultdict(list)
    personal_ratings = []
    for section in ("movies", "shows", "seasons", "episodes"):
        for row in ratings.get(section) or []:
            try:
                rating = float(row.get("rating"))
            except (TypeError, ValueError):
                continue
            personal_ratings.append(rating)
            media = _nested_media(row)
            genres = _genres(media)
            if not genres:
                genres = _genres(metadata_by_key.get(media_key(media), {}))
            for genre in genres:
                genre_rating_values[genre].append(rating)

    personal_genre_ratings = {
        genre: sum(values) / len(values)
        for genre, values in genre_rating_values.items() if values
    }
    progress_by_tmdb = {}
    for row in dataset.get("progress") or []:
        ids = (row.get("show") or {}).get("ids") or {}
        if ids.get("tmdb") is not None:
            progress_by_tmdb[str(ids["tmdb"])] = row

    return {
        "genre_affinity": genre_affinity,
        "personal_genre_ratings": personal_genre_ratings,
        "favorite_decades": decades,
        "preferred_runtime": int(median(movie_runtimes)) if movie_runtimes else 105,
        "average_personal_rating": (
            sum(personal_ratings) / len(personal_ratings) if personal_ratings else None
        ),
        "history_count": len(watched.get("movies") or []) + len(watched.get("episodes") or []),
        "ratings_count": len(personal_ratings),
        "progress_by_tmdb": progress_by_tmdb,
    }


def _friction(kind: str, runtime: int, total_episodes: int, started: bool) -> int:
    if kind == "movie":
        duration = runtime or 120
        value = 100 if duration <= 100 else 90 if duration <= 120 else 75 if duration <= 140 else 60 if duration <= 160 else 45 if duration <= 190 else 30
    else:
        count = total_episodes or 50
        value = 100 if count <= 8 else 90 if count <= 20 else 75 if count <= 40 else 55 if count <= 80 else 40 if count <= 150 else 25
    if started:
        value += 12
    return max(0, min(value, 100))


def score_item(
    item: dict[str, Any],
    profile: dict[str, Any],
    source_name: str,
    known_genre: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    kind = media_type(item)
    genres = _genres(item)
    if known_genre and known_genre != "Tous" and known_genre not in genres:
        genres.append(known_genre)
    genres = sorted(set(genres))
    runtime = _runtime(item)
    year = _year(item)
    note = _community_note(item)
    votes = _votes(item)
    status = _status(item)
    added_days = _added_days(item, now)
    ids = item.get("ids") if isinstance(item.get("ids"), dict) else {}
    tmdb_id = ids.get("tmdb") or item.get("id")
    progress = profile.get("progress_by_tmdb", {}).get(str(tmdb_id), {})
    total_episodes = int(progress.get("total_episodes") or 0)
    watched_episodes = int(progress.get("watched_episodes") or 0)
    started = bool(total_episodes and watched_episodes)

    score = 20.0
    reasons: list[str] = []
    warnings: list[str] = []
    tags: list[str] = []

    affinities = profile.get("genre_affinity", {})
    if genres and affinities:
        affinity = sum(affinities.get(genre, 0) for genre in genres) / len(genres)
        bonus = min(affinity * 0.6, 30)
        score += bonus
        if bonus >= 12:
            reasons.append(f"Proche de tes genres habituels (+{round(bonus)})")
            tags.append("❤️ Tes genres")
        elif bonus <= 2:
            warnings.append("Genre peu présent dans ton historique")

    personal_genres = profile.get("personal_genre_ratings", {})
    own_values = [personal_genres[genre] for genre in genres if genre in personal_genres]
    if own_values:
        own_average = sum(own_values) / len(own_values)
        if own_average >= 8:
            score += 8
            reasons.append("Genre que tu notes très bien (+8)")
            tags.append("🫶 Bien noté par toi")
        elif own_average <= 5:
            score -= 6
            warnings.append("Genre que tu notes plutôt bas (-6)")

    if note is not None:
        note_bonus = min(note / 10 * 25, 25)
        score += note_bonus
        if note >= 8.5:
            reasons.append(f"Très bien noté ({note:.1f}/10)")
            tags.append("💎 Pépite critique")
        elif note < 5:
            warnings.append(f"Note communauté faible ({note:.1f}/10)")

    if votes >= 100000:
        score += 4
        reasons.append("Très populaire (+4)")
        tags.append("🔥 Populaire")

    if year:
        age = now.year - year
        if age <= 2:
            score += 15
            reasons.append("Sortie récente (+15)")
            tags.append("🆕 Récent")
        elif age <= 10:
            score += 7
        elif age >= 25 and note is not None and note >= 8:
            score += 8
            reasons.append("Classique très bien noté (+8)")
            tags.append("🏆 Classique")

    if kind == "movie" and runtime:
        preferred = int(profile.get("preferred_runtime") or 105)
        distance = abs(runtime - preferred)
        if distance <= 15:
            score += 10
            reasons.append("Durée idéale pour toi (+10)")
            tags.append("⏱️ Durée idéale")
        elif runtime >= 190:
            score -= 8
            warnings.append("Film très long (-8)")
        elif runtime >= 160:
            score -= 3
            warnings.append("Film plus long que la moyenne (-3)")

    if kind == "show":
        if total_episodes and total_episodes <= 8:
            score += 10
            reasons.append("Mini-série rapide (+10)")
            tags.append("🎯 Mini-série")
        if started:
            score += 8
            remaining = max(total_episodes - watched_episodes, 0)
            reasons.append(f"Série déjà commencée, reste {remaining} épisode(s) (+8)")
            tags.append("▶️ À continuer")
        if status == "ended":
            tags.append("✅ Terminée")
        elif status == "canceled":
            warnings.append("Série annulée")

    if added_days is not None:
        if added_days <= 14:
            score += 10
            reasons.append("Ajout récent dans ta liste (+10)")
            tags.append("📥 Ajout récent")
        elif added_days > 730:
            score -= 20
            warnings.append("Dans ta liste depuis plus de deux ans (-20)")
        elif added_days > 365:
            score -= 12
            warnings.append("Dans ta liste depuis plus d’un an (-12)")

    friction = _friction(kind, runtime, total_episodes, started)
    if friction >= 90:
        tags.append("🚪 Zéro effort")
    if now.hour >= 22 or now.hour < 5:
        if (kind == "movie" and runtime and runtime <= 105) or (kind == "show" and 0 < total_episodes <= 8):
            score += 7
            reasons.append("Parfait pour une fin de soirée (+7)")
            tags.append("🌙 Fin de soirée")

    score = max(0, min(round(score, 1), 100))
    return {
        "key": media_key(item),
        "item": item,
        "type": "Film" if kind == "movie" else "Série",
        "genres": genres,
        "runtime": runtime,
        "year": year,
        "note": note,
        "votes": votes,
        "status": status,
        "added_days": added_days,
        "total_episodes": total_episodes,
        "watched_episodes": watched_episodes,
        "score": score,
        "friction": friction,
        "reasons": reasons,
        "warnings": warnings,
        "tags": list(dict.fromkeys(tags)),
        "source": source_name,
    }


PRESET_NAMES = [
    "Aucun preset",
    "⚡ Rapide — film < 1h30",
    "🍿 Soirée cinéma — grand film bien noté",
    "📺 Binge express — mini-série terminée (≤ 8 ép.)",
    "💎 Pépites confidentielles",
    "🧠 Exigeant — note ≥ 8.5",
    "🔥 Indémodables — 100k+ votes",
    "⏳ Ça traîne — ajouté il y a 3 ans ou +",
    "▶️ Continuer ce que tu as commencé",
    "👨‍👩‍👧 Soirée en famille",
    "😄 Envie de rire",
    "😱 Envie de frissons",
    "💥 Adrénaline",
    "🎯 Presque finies — séries ≥ 80%",
    "🆕 Fraîchement ajoutés (15 jours)",
    "🏆 Classiques cultes (25 ans et +)",
    "🧭 Hors de ta zone de confort",
    "✨ Récent & acclamé",
    "🗳️ Plébiscite critique + public",
    "🚪 Zéro effort ce soir",
    "🌍 Cinéma du monde",
]


def preset_matches(name: str, row: dict[str, Any], profile: dict[str, Any]) -> bool:
    if name == "Aucun preset":
        return True
    genres = {genre.lower() for genre in row.get("genres") or []}
    note = row.get("note") or 0
    runtime = row.get("runtime") or 0
    year = row.get("year") or 0
    if name.startswith("⚡"):
        return row["type"] == "Film" and 0 < runtime <= 90
    if name.startswith("🍿"):
        return row["type"] == "Film" and runtime >= 120 and note >= 7.5
    if name.startswith("📺"):
        return row["type"] == "Série" and row.get("status") == "ended" and 0 < row.get("total_episodes", 0) <= 8
    if name.startswith("💎"):
        return note >= 7.8 and row.get("votes", 0) < 30000
    if name.startswith("🧠"):
        return note >= 8.5
    if name.startswith("🔥"):
        return row.get("votes", 0) >= 100000
    if name.startswith("⏳"):
        return (row.get("added_days") or 0) >= 1095
    if name.startswith("▶️"):
        return row.get("watched_episodes", 0) > 0
    if name.startswith("👨‍👩‍👧"):
        return "family" in genres or "animation" in genres
    if name.startswith("😄"):
        return bool(genres & {"comedy", "animation"})
    if name.startswith("😱"):
        return bool(genres & {"horror", "thriller", "mystery"})
    if name.startswith("💥"):
        return bool(genres & {"action", "adventure"})
    if name.startswith("🎯"):
        total = row.get("total_episodes") or 0
        watched = row.get("watched_episodes") or 0
        return row["type"] == "Série" and total > watched >= 0.8 * total
    if name.startswith("🆕"):
        return row.get("added_days") is not None and row["added_days"] <= 15
    if name.startswith("🏆"):
        return note >= 8 and year and year <= datetime.now(timezone.utc).year - 25
    if name.startswith("🧭"):
        affinities = profile.get("genre_affinity", {})
        return bool(row.get("genres")) and all(affinities.get(genre, 0) < 5 for genre in row["genres"]) and note >= 7.5
    if name.startswith("✨"):
        return note >= 7.5 and year >= datetime.now(timezone.utc).year - 2
    if name.startswith("🗳️"):
        return note >= 8 and row.get("votes", 0) >= 50000
    if name.startswith("🚪"):
        return row.get("friction", 0) >= 90
    if name.startswith("🌍"):
        country = str(row.get("item", {}).get("country") or "").lower()
        return bool(country and country != "us" and note >= 7)
    return True
