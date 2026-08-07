"""Normalisation et tri local des progressions de lecture MDBList/ZIP.

Aucun appel réseau : le module travaille sur la section playback déjà chargée.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable


PLAYBACK_ENGINE_VERSION = 1
DEFAULT_PLAYBACK_SORT = "🕒 Dernière activité — récente d’abord"

PLAYBACK_SORT_OPTIONS = [
    DEFAULT_PLAYBACK_SORT,
    "🕒 Dernière activité — ancienne d’abord",
    "⚡ Temps restant — le plus court",
    "⏳ Temps restant — le plus long",
    "📈 Progression — la plus avancée",
    "📉 Progression — la moins avancée",
    "🔤 Titre — A à Z",
    "🔤 Titre — Z à A",
]

PLAYBACK_PROGRESS_OPTIONS = [
    "Toutes les progressions",
    "Moins de 25 %",
    "25 à 49 %",
    "50 à 74 %",
    "75 % et plus",
]


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _timestamp(value: Any) -> float | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        parsed = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).timestamp()
    except (TypeError, ValueError, OverflowError):
        return None


def _poster(media: dict[str, Any]) -> str:
    return str(media.get("poster") or media.get("poster_path") or "")


def _episode_numbers(episode: dict[str, Any]) -> tuple[int, int]:
    season_value = episode.get("season_number")
    if season_value is None:
        season_value = episode.get("season")
    if isinstance(season_value, dict):
        season_value = season_value.get("number")
    episode_value = episode.get("episode_number")
    if episode_value is None:
        episode_value = episode.get("number") or episode.get("episode")
    if isinstance(episode_value, dict):
        episode_value = episode_value.get("number")
    return _int(season_value), _int(episode_value)


def normalize_playback(items: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        raw_type = str(item.get("type") or "").lower()
        movie = _dict(item.get("movie"))
        episode = _dict(item.get("episode"))
        show = _dict(item.get("show"))
        if not show and isinstance(episode.get("show"), dict):
            show = episode["show"]
        is_movie = raw_type == "movie" or (bool(movie) and not episode)
        media = movie if is_movie else show or episode
        title = str(media.get("title") or media.get("name") or "Titre inconnu")
        year = media.get("year") or media.get("release_year")
        try:
            year = int(year) if year else None
        except (TypeError, ValueError):
            year = None

        progress = _number(
            item.get("progress")
            if item.get("progress") is not None
            else item.get("progress_at_update")
        )
        progress = max(0.0, min(progress, 100.0))
        runtime = _int(
            item.get("runtime")
            or (movie.get("runtime") if is_movie else episode.get("runtime") or show.get("runtime"))
        )
        runtime = max(runtime, 0)
        remaining = int(round(runtime * max(100 - progress, 0) / 100)) if runtime else 0
        updated_at = (
            item.get("updated_at")
            or item.get("paused_at")
            or item.get("started_at")
        )
        updated_ts = _timestamp(item.get("updated_at_ts")) or _timestamp(updated_at)
        season, number = _episode_numbers(episode)
        episode_title = str(episode.get("title") or episode.get("name") or "")
        episode_label = ""
        if not is_movie:
            if season or number:
                episode_label = f"S{season:02d}E{number:02d}"
            if episode_title:
                episode_label = f"{episode_label} · {episode_title}" if episode_label else episode_title

        raw_id = item.get("id")
        key = f"playback:{raw_id}" if raw_id is not None else f"playback:{index}:{title}:{season}:{number}"
        ids = media.get("ids") if isinstance(media.get("ids"), dict) else {}
        output.append(
            {
                "key": key,
                "id": raw_id,
                "type": "Film" if is_movie else "Épisode",
                "kind": "movie" if is_movie else "episode",
                "media_kind": "movie" if is_movie else "show",
                "title": title,
                "year": year,
                "ids": ids,
                "episode_label": episode_label,
                "progress": round(progress, 1),
                "runtime": runtime,
                "remaining_minutes": remaining,
                "updated_at": updated_at,
                "updated_timestamp": updated_ts,
                "expires_at": item.get("expires_at"),
                "paused_at": item.get("paused_at"),
                "is_manual": bool(item.get("is_manual")),
                "poster": _poster(media),
                "item": item,
            }
        )
    return output


def normalize_now_playing(
    items: Iterable[dict[str, Any]],
    fetched_at: float,
    now_timestamp: float,
) -> list[dict[str, Any]]:
    """Estime localement la progression depuis le dernier appel ciblé.

    Le serveur fournit la progression au moment de la requête. Entre deux
    vérifications réseau, le pourcentage avance à partir du runtime : le rendu
    peut donc se rafraîchir sans consommer de quota MDBList.
    """
    rows = normalize_playback(items)
    elapsed_minutes = max(float(now_timestamp) - float(fetched_at), 0) / 60
    output = []
    for row in rows:
        value = dict(row)
        runtime = int(value.get("runtime") or 0)
        initial = float(value.get("progress") or 0)
        if runtime > 0 and not value.get("paused_at"):
            estimated = min(initial + elapsed_minutes / runtime * 100, 100.0)
            value["progress"] = round(estimated, 1)
            value["remaining_minutes"] = int(round(runtime * max(100 - estimated, 0) / 100))
        expires_timestamp = _timestamp(value.get("expires_at"))
        value["possibly_ended"] = bool(expires_timestamp and now_timestamp > expires_timestamp)
        value["live"] = True
        output.append(value)
    return output


def _identity_keys(kind: str, ids: dict[str, Any]) -> list[tuple[str, str, str]]:
    output = []
    for provider in ("tmdb", "imdb", "tvdb", "trakt", "mdblist"):
        value = ids.get(provider)
        if value not in (None, "", 0, "0"):
            output.append((kind, provider, str(value)))
    return output


def enrich_playback_posters(
    rows: Iterable[dict[str, Any]],
    dataset: dict[str, Any],
) -> list[dict[str, Any]]:
    """Complète les posters depuis les autres sections déjà en mémoire."""
    poster_by_id: dict[tuple[str, str, str], str] = {}
    poster_by_title: dict[tuple[str, str, int | None], str] = {}

    def remember(media: dict[str, Any], kind: str) -> None:
        if not isinstance(media, dict):
            return
        poster = _poster(media)
        if not poster:
            return
        ids = media.get("ids") if isinstance(media.get("ids"), dict) else {}
        for identity in _identity_keys(kind, ids):
            poster_by_id.setdefault(identity, poster)
        title = str(media.get("title") or media.get("name") or "").strip().casefold()
        year_value = media.get("year") or media.get("release_year")
        try:
            year = int(year_value) if year_value else None
        except (TypeError, ValueError):
            year = None
        if title:
            poster_by_title.setdefault((kind, title, year), poster)

    for source in dataset.get("sources") or []:
        if not isinstance(source, dict) or source.get("kind") == "aggregate":
            continue
        for item in source.get("movies") or []:
            remember(item, "movie")
        for item in source.get("shows") or []:
            remember(item, "show")
    for progress in dataset.get("progress") or []:
        if isinstance(progress, dict):
            remember(_dict(progress.get("show")), "show")
    watched = (dataset.get("sections") or {}).get("watched") or {}
    for item in watched.get("movies") or []:
        remember(_dict(item.get("movie")) or item, "movie")
    for item in watched.get("shows") or []:
        remember(_dict(item.get("show")) or item, "show")

    output = []
    for row in rows:
        value = dict(row)
        if not value.get("poster"):
            kind = str(value.get("media_kind") or "movie")
            ids = value.get("ids") if isinstance(value.get("ids"), dict) else {}
            poster = ""
            for identity in _identity_keys(kind, ids):
                if identity in poster_by_id:
                    poster = poster_by_id[identity]
                    break
            if not poster:
                poster = poster_by_title.get(
                    (kind, str(value.get("title") or "").casefold(), value.get("year")),
                    "",
                )
            value["poster"] = poster
            value["poster_from_cache"] = bool(poster)
        output.append(value)
    return output


def finishable_tonight(rows: Iterable[dict[str, Any]], limit: int = 3) -> list[dict[str, Any]]:
    candidates = [
        row for row in rows
        if row.get("remaining_minutes", 0) > 0 and 0 < row.get("progress", 0) < 95
    ]
    candidates.sort(key=lambda row: (row["remaining_minutes"], -row["progress"], row["title"].casefold()))
    return candidates[: max(int(limit), 0)]


def _progress_matches(value: float, selected: str) -> bool:
    if selected == "Moins de 25 %":
        return value < 25
    if selected == "25 à 49 %":
        return 25 <= value < 50
    if selected == "50 à 74 %":
        return 50 <= value < 75
    if selected == "75 % et plus":
        return value >= 75
    return True


def _sort_numeric(
    rows: list[dict[str, Any]],
    field: str,
    descending: bool,
    missing_zero: bool = False,
) -> list[dict[str, Any]]:
    indexed = list(enumerate(rows))

    def key(pair: tuple[int, dict[str, Any]]) -> tuple[bool, float, int]:
        index, row = pair
        value = row.get(field)
        missing = value is None or (not missing_zero and field == "remaining_minutes" and value == 0)
        number = _number(value)
        return missing, (-number if descending else number), index

    return [row for _, row in sorted(indexed, key=key)]


def filter_playback_rows(
    rows: Iterable[dict[str, Any]],
    media_filter: str = "Tous",
    progress_filter: str = "Toutes les progressions",
    search: str = "",
    sort_mode: str = DEFAULT_PLAYBACK_SORT,
) -> list[dict[str, Any]]:
    query = str(search or "").strip().casefold()
    output = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        if media_filter == "Films" and row.get("type") != "Film":
            continue
        if media_filter == "Épisodes" and row.get("type") != "Épisode":
            continue
        searchable = f"{row.get('title', '')} {row.get('episode_label', '')}".casefold()
        if query and query not in searchable:
            continue
        if not _progress_matches(_number(row.get("progress")), progress_filter):
            continue
        output.append(row)

    if sort_mode == "🕒 Dernière activité — ancienne d’abord":
        return _sort_numeric(output, "updated_timestamp", descending=False, missing_zero=True)
    if sort_mode == "⚡ Temps restant — le plus court":
        return _sort_numeric(output, "remaining_minutes", descending=False)
    if sort_mode == "⏳ Temps restant — le plus long":
        return _sort_numeric(output, "remaining_minutes", descending=True)
    if sort_mode == "📈 Progression — la plus avancée":
        return _sort_numeric(output, "progress", descending=True, missing_zero=True)
    if sort_mode == "📉 Progression — la moins avancée":
        return _sort_numeric(output, "progress", descending=False, missing_zero=True)
    if sort_mode == "🔤 Titre — A à Z":
        return sorted(output, key=lambda row: row["title"].casefold())
    if sort_mode == "🔤 Titre — Z à A":
        return sorted(output, key=lambda row: row["title"].casefold(), reverse=True)
    return _sort_numeric(output, "updated_timestamp", descending=True, missing_zero=True)
