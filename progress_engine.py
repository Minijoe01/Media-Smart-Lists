"""Filtres et tris locaux de la progression, indépendants du fournisseur.

Ce module ne réalise volontairement aucun appel réseau. Il travaille uniquement
sur les lignes normalisées déjà présentes dans le dataset de session.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable


DEFAULT_PROGRESS_SORT = "🕘 Dernier visionnage — récent d’abord"

PROGRESS_SORT_OPTIONS = [
    DEFAULT_PROGRESS_SORT,
    "🕘 Dernier visionnage — ancien d’abord",
    "📈 Progression — plus avancée",
    "📉 Progression — moins avancée",
    "⏳ Temps restant — le plus court",
    "⏳ Temps restant — le plus long",
    "👀 Temps déjà vu — le plus élevé",
    "👀 Temps déjà vu — le plus faible",
    "🆕 Nouveauté — épisode disponible le plus récent",
    "🗓️ Nouveauté — épisode disponible le plus ancien",
    "🔤 Titre — A à Z",
    "🔤 Titre — Z à A",
]


def _genres_from_media(media: dict[str, Any]) -> list[str]:
    values = media.get("genres") or []
    output: set[str] = set()
    for value in values:
        if isinstance(value, dict):
            value = value.get("name") or value.get("title") or value.get("slug")
        if value:
            output.add(str(value).strip().title())
    return sorted(output, key=str.casefold)


def progress_genres(row: dict[str, Any]) -> list[str]:
    """Retourne les genres normalisés d'une ligne En cours."""
    values = row.get("genres")
    if isinstance(values, list) and values:
        return _genres_from_media({"genres": values})
    show = row.get("show") if isinstance(row.get("show"), dict) else {}
    return _genres_from_media(show)


def available_progress_genres(rows: Iterable[dict[str, Any]]) -> list[str]:
    values: set[str] = set()
    for row in rows:
        if isinstance(row, dict):
            values.update(progress_genres(row))
    return sorted(values, key=str.casefold)


def _title(row: dict[str, Any]) -> str:
    show = row.get("show") if isinstance(row.get("show"), dict) else {}
    return str(show.get("title") or show.get("name") or "").strip()


def _timestamp(value: Any) -> float | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        text = str(value).strip().replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).timestamp()
    except (TypeError, ValueError, OverflowError):
        return None


def _last_watched_timestamp(row: dict[str, Any]) -> float | None:
    show = row.get("show") if isinstance(row.get("show"), dict) else {}
    return _timestamp(
        row.get("last_watched_at")
        or row.get("watched_at")
        or show.get("last_watched_at")
        or show.get("watched_at")
    )


def _latest_available_timestamp(row: dict[str, Any]) -> float | None:
    show = row.get("show") if isinstance(row.get("show"), dict) else {}
    episode = row.get("next_episode") if isinstance(row.get("next_episode"), dict) else {}
    last_episode = show.get("last_episode_to_air") if isinstance(show.get("last_episode_to_air"), dict) else {}
    return _timestamp(
        row.get("latest_available_at")
        or row.get("last_air_date")
        or show.get("last_air_date")
        or show.get("last_aired_at")
        or show.get("last_episode_air_date")
        or last_episode.get("air_date")
        or episode.get("air_date")
        or episode.get("aired_at")
    )


def filter_progress_rows(
    rows: Iterable[dict[str, Any]],
    genre: str = "Tous les genres",
    search: str = "",
) -> list[dict[str, Any]]:
    """Filtre localement par genre et titre, sans requête distante."""
    query = str(search or "").strip().casefold()
    output = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        if query and query not in _title(row).casefold():
            continue
        if genre and genre != "Tous les genres" and genre not in progress_genres(row):
            continue
        output.append(row)
    return output


def _sort_numeric(
    rows: list[dict[str, Any]],
    getter,
    descending: bool,
) -> list[dict[str, Any]]:
    """Trie une valeur numérique en laissant toujours les métadonnées absentes à la fin."""
    indexed = list(enumerate(rows))

    def key(pair: tuple[int, dict[str, Any]]) -> tuple[bool, float, int]:
        index, row = pair
        value = getter(row)
        missing = value is None
        number = float(value or 0)
        return missing, (-number if descending else number), index

    return [row for _, row in sorted(indexed, key=key)]


def sort_progress_rows(rows: Iterable[dict[str, Any]], mode: str) -> list[dict[str, Any]]:
    """Trie les lignes localement. Le mode par défaut reproduit l'ordre Up Next MDBList."""
    values = [row for row in rows if isinstance(row, dict)]
    if mode == "🕘 Dernier visionnage — ancien d’abord":
        return _sort_numeric(values, _last_watched_timestamp, descending=False)
    if mode == "📈 Progression — plus avancée":
        return _sort_numeric(values, lambda row: row.get("percent"), descending=True)
    if mode == "📉 Progression — moins avancée":
        return _sort_numeric(values, lambda row: row.get("percent"), descending=False)
    if mode == "⏳ Temps restant — le plus court":
        return _sort_numeric(values, lambda row: row.get("remaining_minutes"), descending=False)
    if mode == "⏳ Temps restant — le plus long":
        return _sort_numeric(values, lambda row: row.get("remaining_minutes"), descending=True)
    if mode == "👀 Temps déjà vu — le plus élevé":
        return _sort_numeric(values, lambda row: row.get("watched_minutes"), descending=True)
    if mode == "👀 Temps déjà vu — le plus faible":
        return _sort_numeric(values, lambda row: row.get("watched_minutes"), descending=False)
    if mode == "🆕 Nouveauté — épisode disponible le plus récent":
        return _sort_numeric(values, _latest_available_timestamp, descending=True)
    if mode == "🗓️ Nouveauté — épisode disponible le plus ancien":
        return _sort_numeric(values, _latest_available_timestamp, descending=False)
    if mode == "🔤 Titre — A à Z":
        return sorted(values, key=lambda row: _title(row).casefold())
    if mode == "🔤 Titre — Z à A":
        return sorted(values, key=lambda row: _title(row).casefold(), reverse=True)
    return _sort_numeric(values, _last_watched_timestamp, descending=True)
