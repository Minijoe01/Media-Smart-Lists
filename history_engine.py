"""Historique local des visionnages du NormalizedDataset."""

from __future__ import annotations

import csv
import io
import json
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Any, Iterable
from zoneinfo import ZoneInfo


HISTORY_ENGINE_VERSION = 1
HISTORY_PERIOD_OPTIONS = [
    "Tout l’historique",
    "7 derniers jours",
    "30 derniers jours",
    "90 derniers jours",
    "Cette année",
    "Période personnalisée",
]
HISTORY_SORT_OPTIONS = [
    "Plus récents d’abord",
    "Plus anciens d’abord",
    "Titre A → Z",
    "Durée la plus longue",
]


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _parse_datetime(value: Any, tz: ZoneInfo) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        parsed = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(tz)
    except (TypeError, ValueError):
        return None


def _ids(media: dict[str, Any]) -> dict[str, Any]:
    values = media.get("ids") if isinstance(media.get("ids"), dict) else {}
    return {key: value for key, value in values.items() if value not in (None, "")}


def _identity(kind: str, media: dict[str, Any]) -> str:
    ids = _ids(media)
    for provider in ("tmdb", "imdb", "tvdb", "trakt", "mdblist"):
        if provider in ids:
            return f"{kind}:{provider}:{ids[provider]}"
    value = media.get("id") or media.get("imdb_id")
    if value not in (None, ""):
        return f"{kind}:id:{value}"
    title = media.get("title") or media.get("name") or "?"
    year = media.get("year") or media.get("release_year") or "?"
    return f"{kind}:title:{str(title).casefold()}:{year}"


def _genres(media: dict[str, Any]) -> list[str]:
    output: dict[str, str] = {}
    for value in media.get("genres") or []:
        if isinstance(value, dict):
            value = value.get("name") or value.get("title") or value.get("slug")
        if value:
            text = str(value).strip().title()
            output.setdefault(text.casefold(), text)
    return sorted(output.values(), key=str.casefold)


def _runtime(*containers: dict[str, Any], default: int = 0) -> int:
    """Runtime d'un film, avec conversion prudente si une source renvoie des secondes."""
    for container in containers:
        try:
            value = int(round(float(container.get("runtime") or 0)))
        except (TypeError, ValueError):
            continue
        if 0 < value <= 600:
            return value
        if value > 600 and 5 <= value / 60 <= 600:
            return int(round(value / 60))
    return default


def _coerce_minutes(value: Any) -> int | None:
    """Convertit une durée en minutes, ou None si absente/invalide."""
    try:
        return int(round(float(value or 0)))
    except (TypeError, ValueError):
        return None


def _episode_count(show: dict[str, Any]) -> int:
    for key in (
        "total_aired_episodes",
        "aired_episodes",
        "total_episode_count",
        "total_episodes",
        "episode_count",
        "number_of_episodes",
        "number_episodes",
        "num_episodes",
    ):
        try:
            value = int(show.get(key) or 0)
            if value > 0:
                return value
        except (TypeError, ValueError):
            pass
    # Certaines réponses exposent un objet « episodes » au lieu d'un entier.
    episodes = show.get("episodes")
    if isinstance(episodes, dict):
        for key in ("count", "total", "aired"):
            try:
                value = int(episodes.get(key) or 0)
                if value > 0:
                    return value
            except (TypeError, ValueError):
                pass
    return 0


def _episode_runtime(
    episode: dict[str, Any],
    show: dict[str, Any],
    row: dict[str, Any],
    episode_count: int = 0,
) -> int:
    """Évite de confondre durée d'un épisode et durée cumulée de la série.

    Les formats courts (ex. « Connasse » : 71 épisodes d'environ 1 min) sont
    acceptés dès 1 minute. Une durée au-delà de 90 min n'est pas crédible pour
    un épisode classique : on la traite comme une durée cumulée de la série
    (divisée par le nombre d'épisodes) ou comme des secondes à convertir.
    """
    # 1. Durée explicite au niveau de l'épisode (1 à 90 min).
    for container in (episode, row):
        for key in ("runtime", "episode_runtime", "duration"):
            value = _coerce_minutes(container.get(key))
            if value is not None and 1 <= value <= 90:
                return value

    # 2. Durée explicite par épisode au niveau de la série.
    for key in ("episode_runtime", "runtime_per_episode", "average_runtime"):
        value = _coerce_minutes(show.get(key))
        if value is not None and 1 <= value <= 90:
            return value

    # 3. Runtime de la série s'il ressemble déjà à une durée d'épisode.
    show_runtime = _coerce_minutes(show.get("runtime"))
    if show_runtime is not None and 1 <= show_runtime <= 90:
        return show_runtime

    # 4. Durée cumulée de la série ou durée en secondes.
    if show_runtime is not None and show_runtime > 90:
        candidates: list[int] = []
        if episode_count > 0:
            candidates.append(int(round(show_runtime / episode_count)))
        candidates.append(int(round(show_runtime / 60)))
        for candidate in candidates:
            if 1 <= candidate <= 90:
                return candidate

    genres = {genre.casefold() for genre in _genres(show)}
    if genres & {"animation", "anime"}:
        return 20
    return 45


def _year(media: dict[str, Any]) -> int | None:
    value = media.get("year") or media.get("release_year")
    try:
        return int(value) if value else None
    except (TypeError, ValueError):
        return None


def _plays(row: dict[str, Any]) -> int:
    for key in ("plays", "play_count", "watch_count", "watched_count"):
        try:
            value = int(row.get(key) or 0)
            if value > 0:
                return value
        except (TypeError, ValueError):
            pass
    return 1


def _rating_value(row: dict[str, Any]) -> float | None:
    try:
        value = float(row.get("rating"))
        return value if value > 0 else None
    except (TypeError, ValueError):
        return None


def _episode_numbers(episode: dict[str, Any]) -> tuple[int, int]:
    season = episode.get("season_number")
    if season is None:
        season = episode.get("season")
    if isinstance(season, dict):
        season = season.get("number")
    number = episode.get("episode_number")
    if number is None:
        number = episode.get("number") or episode.get("episode")
    if isinstance(number, dict):
        number = number.get("number")
    try:
        season_int = int(season or 0)
    except (TypeError, ValueError):
        season_int = 0
    try:
        number_int = int(number or 0)
    except (TypeError, ValueError):
        number_int = 0
    return season_int, number_int


def normalize_history(
    dataset: dict[str, Any],
    timezone_name: str = "Europe/Paris",
) -> list[dict[str, Any]]:
    tz = ZoneInfo(timezone_name)
    sections = dataset.get("sections") or {}
    watched = sections.get("watched") or {}
    ratings = sections.get("ratings") or {}

    show_metadata: dict[str, dict[str, Any]] = {}
    for row in watched.get("shows") or []:
        if not isinstance(row, dict):
            continue
        show = _dict(row.get("show")) or row
        show_metadata[_identity("show", show)] = show

    def find_show(reference: dict[str, Any]) -> dict[str, Any]:
        identity = _identity("show", reference)
        if identity in show_metadata:
            return show_metadata[identity]
        ref_ids = _ids(reference)
        for show in show_metadata.values():
            show_ids = _ids(show)
            if any(str(ref_ids.get(key)) == str(show_ids.get(key)) for key in ref_ids if key in show_ids):
                return show
        return reference

    # Épisodes vus par série (utilisés si la métadonnée ne fournit pas de compte).
    show_watched_count: dict[str, set[tuple[int, int]]] = {}
    for row in watched.get("episodes") or []:
        if not isinstance(row, dict):
            continue
        episode = _dict(row.get("episode")) or row
        show_ref = _dict(episode.get("show")) or _dict(row.get("show"))
        show = find_show(show_ref)
        season, number = _episode_numbers(episode)
        show_watched_count.setdefault(_identity("show", show), set()).add((season, number))

    movie_ratings: dict[str, float] = {}
    show_ratings: dict[str, float] = {}
    episode_ratings: dict[str, float] = {}
    for row in ratings.get("movies") or []:
        if isinstance(row, dict):
            media = _dict(row.get("movie")) or row
            value = _rating_value(row)
            if value is not None:
                movie_ratings[_identity("movie", media)] = value
    for row in ratings.get("shows") or []:
        if isinstance(row, dict):
            media = _dict(row.get("show")) or row
            value = _rating_value(row)
            if value is not None:
                show_ratings[_identity("show", media)] = value
    for row in ratings.get("episodes") or []:
        if isinstance(row, dict):
            media = _dict(row.get("episode")) or row
            value = _rating_value(row)
            if value is not None:
                episode_ratings[_identity("episode", media)] = value

    output = []
    for index, row in enumerate(watched.get("movies") or []):
        if not isinstance(row, dict):
            continue
        movie = _dict(row.get("movie")) or row
        watched_at = _parse_datetime(row.get("last_watched_at") or row.get("watched_at"), tz)
        identity = _identity("movie", movie)
        runtime = _runtime(movie, row, default=100)
        plays = _plays(row)
        output.append(
            {
                "key": f"history:{identity}:{watched_at.isoformat() if watched_at else index}",
                "kind": "movie",
                "media_kind": "movie",
                "type": "Film",
                "title": str(movie.get("title") or movie.get("name") or "Film inconnu"),
                "year": _year(movie),
                "episode_label": "",
                "watched_at": watched_at,
                "runtime": runtime,
                "plays": plays,
                "total_minutes": runtime * plays,
                "genres": _genres(movie),
                "personal_rating": movie_ratings.get(identity),
                "ids": _ids(movie),
                "poster": str(movie.get("poster") or movie.get("poster_path") or ""),
            }
        )

    for index, row in enumerate(watched.get("episodes") or []):
        if not isinstance(row, dict):
            continue
        episode = _dict(row.get("episode")) or row
        show_ref = _dict(episode.get("show")) or _dict(row.get("show"))
        show = find_show(show_ref)
        watched_at = _parse_datetime(row.get("last_watched_at") or row.get("watched_at"), tz)
        season, number = _episode_numbers(episode)
        episode_title = str(episode.get("title") or episode.get("name") or "")
        episode_label = f"S{season:02d}E{number:02d}" if season or number else "Épisode"
        if episode_title:
            episode_label += f" · {episode_title}"
        identity = _identity("episode", episode)
        show_identity = _identity("show", show)
        # Nombre d'épisodes connu pour la série : aide à détecter une durée
        # cumulée (ex. format court) au lieu d'une durée par épisode.
        episode_count = _episode_count(show)
        if episode_count <= 0:
            episode_count = len(show_watched_count.get(show_identity) or ())
        runtime = _episode_runtime(episode, show, row, episode_count=episode_count)
        plays = _plays(row)
        output.append(
            {
                "key": f"history:{identity}:{watched_at.isoformat() if watched_at else index}",
                "kind": "episode",
                "media_kind": "show",
                "type": "Épisode",
                "title": str(show.get("title") or show.get("name") or show_ref.get("title") or "Série inconnue"),
                "year": _year(show),
                "episode_label": episode_label,
                "watched_at": watched_at,
                "runtime": runtime,
                "plays": plays,
                "total_minutes": runtime * plays,
                "genres": _genres(show),
                "personal_rating": episode_ratings.get(identity) or show_ratings.get(show_identity),
                "ids": _ids(show),
                "poster": str(show.get("poster") or show.get("poster_path") or ""),
            }
        )

    return sorted(
        output,
        key=lambda row: (
            row.get("watched_at") is None,
            -(row["watched_at"].timestamp()) if row.get("watched_at") else 0,
            row["title"].casefold(),
        ),
    )


def available_history_genres(rows: Iterable[dict[str, Any]]) -> list[str]:
    values = set()
    for row in rows:
        values.update(row.get("genres") or [])
    return sorted(values, key=str.casefold)


def filter_history(
    rows: Iterable[dict[str, Any]],
    period: str = "Tout l’historique",
    media_filter: str = "Tous",
    genre_filter: str = "Tous les genres",
    search: str = "",
    sort_mode: str = "Plus récents d’abord",
    start_date: date | None = None,
    end_date: date | None = None,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    now = now or datetime.now(timezone.utc)
    query = str(search or "").strip().casefold()
    if period == "7 derniers jours":
        start_date = (now - timedelta(days=7)).date()
    elif period == "30 derniers jours":
        start_date = (now - timedelta(days=30)).date()
    elif period == "90 derniers jours":
        start_date = (now - timedelta(days=90)).date()
    elif period == "Cette année":
        start_date = date(now.year, 1, 1)
        end_date = date(now.year, 12, 31)
    elif period != "Période personnalisée":
        start_date = end_date = None

    output = []
    for row in rows:
        if media_filter == "Films" and row.get("type") != "Film":
            continue
        if media_filter == "Épisodes" and row.get("type") != "Épisode":
            continue
        if genre_filter != "Tous les genres" and genre_filter not in (row.get("genres") or []):
            continue
        searchable = f"{row.get('title', '')} {row.get('episode_label', '')}".casefold()
        if query and query not in searchable:
            continue
        watched_at = row.get("watched_at")
        watched_date = watched_at.date() if isinstance(watched_at, datetime) else None
        if start_date and (watched_date is None or watched_date < start_date):
            continue
        if end_date and (watched_date is None or watched_date > end_date):
            continue
        output.append(row)

    if sort_mode == "Plus anciens d’abord":
        return sorted(output, key=lambda row: (row.get("watched_at") is None, row.get("watched_at") or datetime.max.replace(tzinfo=timezone.utc)))
    if sort_mode == "Titre A → Z":
        return sorted(output, key=lambda row: (row["title"].casefold(), -(row["watched_at"].timestamp()) if row.get("watched_at") else 0))
    if sort_mode == "Durée la plus longue":
        return sorted(output, key=lambda row: (-int(row.get("total_minutes") or 0), -(row["watched_at"].timestamp()) if row.get("watched_at") else 0))
    return sorted(output, key=lambda row: (row.get("watched_at") is None, -(row["watched_at"].timestamp()) if row.get("watched_at") else 0))


def genre_minutes(rows: Iterable[dict[str, Any]]) -> list[tuple[str, int]]:
    values: defaultdict[str, int] = defaultdict(int)
    for row in rows:
        genres = row.get("genres") or []
        minutes = int(row.get("total_minutes") or 0)
        for genre in genres:
            values[str(genre)] += minutes
    return sorted(values.items(), key=lambda value: (-value[1], value[0].casefold()))


def rows_to_csv(rows: Iterable[dict[str, Any]]) -> str:
    values = []
    for row in rows:
        watched_at = row.get("watched_at")
        values.append(
            {
                "date": watched_at.isoformat() if isinstance(watched_at, datetime) else "",
                "type": row.get("type"),
                "titre": row.get("title"),
                "annee": row.get("year"),
                "episode": row.get("episode_label"),
                "genres": " | ".join(row.get("genres") or []),
                "duree_minutes": row.get("runtime"),
                "lectures": row.get("plays"),
                "temps_total_minutes": row.get("total_minutes"),
                "note_personnelle": row.get("personal_rating"),
            }
        )
    if not values:
        return ""
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=list(values[0]))
    writer.writeheader()
    writer.writerows(values)
    return stream.getvalue()


def rows_to_json(rows: Iterable[dict[str, Any]]) -> str:
    values = []
    for row in rows:
        value = {key: item for key, item in row.items() if key not in {"watched_at"}}
        value["watched_at"] = row["watched_at"].isoformat() if isinstance(row.get("watched_at"), datetime) else None
        values.append(value)
    return json.dumps(
        {
            "engine": "media-smart-lists-history",
            "version": HISTORY_ENGINE_VERSION,
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "rows": values,
        },
        ensure_ascii=False,
        indent=2,
    )
