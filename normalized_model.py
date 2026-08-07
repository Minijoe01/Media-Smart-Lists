"""Modèle commun Media Smart Lists, indépendant du fournisseur d'origine."""

from __future__ import annotations

from typing import Any


NORMALIZED_SCHEMA_VERSION = 3


def media_type(item: dict[str, Any]) -> str:
    value = str(item.get("mediatype") or item.get("type") or "").lower()
    if value in {"movie", "movies"}:
        return "movie"
    if value in {"show", "tv", "series", "tvshow"}:
        return "show"
    if isinstance(item.get("movie"), dict):
        return "movie"
    if isinstance(item.get("show"), dict):
        return "show"
    return value or "unknown"


def media_key(item: dict[str, Any]) -> str:
    kind = media_type(item)
    ids = item.get("ids") if isinstance(item.get("ids"), dict) else {}
    for key in ("tmdb", "imdb", "tvdb", "trakt", "mdblist"):
        value = ids.get(key)
        if value not in (None, "", 0, "0"):
            return f"{kind}:{key}:{value}"
    value = item.get("id") or item.get("imdb_id")
    if value not in (None, "", 0, "0"):
        return f"{kind}:id:{value}"
    return f"{kind}:title:{item.get('title')}:{item.get('release_year') or item.get('year')}"


def dedupe(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for item in items:
        if isinstance(item, dict):
            output.setdefault(media_key(item), item)
    return list(output.values())


def _source(
    key: str,
    label: str,
    name: str,
    kind: str,
    source_type: str,
    movies: list[dict[str, Any]],
    shows: list[dict[str, Any]],
    list_id: int | None = None,
    members: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "key": key,
        "label": label,
        "name": name,
        "kind": kind,
        "type": source_type,
        "id": list_id,
        "members": members or [key],
        "movies": dedupe(movies),
        "shows": dedupe(shows),
    }


def build_sources(sections: dict[str, Any]) -> list[dict[str, Any]]:
    watchlist = sections.get("watchlist") or {}
    user_lists = sections.get("user_lists") or []
    sources = [
        _source(
            "watchlist",
            "Watchlist MDBList",
            "Watchlist MDBList",
            "watchlist",
            "native",
            list(watchlist.get("movies") or []),
            list(watchlist.get("shows") or []),
        )
    ]

    static_keys: list[str] = []
    dynamic_keys: list[str] = []
    personal_keys: list[str] = []
    for item in user_lists:
        if not isinstance(item, dict) or item.get("id") is None:
            continue
        list_id = int(item["id"])
        list_type = "dynamic" if item.get("type") == "dynamic" else "static"
        key = f"list:{list_id}"
        name = str(item.get("name") or "Liste MDBList")
        label = f"{name} · {'Dynamique' if list_type == 'dynamic' else 'Statique'}"
        sources.append(
            _source(
                key,
                label,
                name,
                "list",
                list_type,
                list(item.get("movies") or []),
                list(item.get("shows") or []),
                list_id=list_id,
            )
        )
        personal_keys.append(key)
        (dynamic_keys if list_type == "dynamic" else static_keys).append(key)

    source_index = {source["key"]: source for source in sources}

    def aggregate(key: str, label: str, members: list[str], source_type: str) -> None:
        movies = []
        shows = []
        for member in members:
            source = source_index.get(member) or {}
            movies.extend(source.get("movies") or [])
            shows.extend(source.get("shows") or [])
        sources.append(
            _source(
                key,
                label,
                label,
                "aggregate",
                source_type,
                movies,
                shows,
                members=members,
            )
        )

    if static_keys:
        aggregate("aggregate:static", "Toutes les listes statiques", static_keys, "aggregate_static")
    if dynamic_keys:
        aggregate("aggregate:dynamic", "Toutes les listes dynamiques", dynamic_keys, "aggregate_dynamic")
    if personal_keys:
        aggregate("aggregate:personal", "Toutes les listes personnelles", personal_keys, "aggregate_personal")
        aggregate("aggregate:all", "Tout : Watchlist + toutes les listes", ["watchlist", *personal_keys], "aggregate_all")

    return sources


def build_progress(sections: dict[str, Any]) -> list[dict[str, Any]]:
    output = []
    for item in sections.get("upnext") or []:
        if not isinstance(item, dict):
            continue
        show = item.get("show") or {}
        episode = item.get("next_episode") or {}
        progress = item.get("progress") or {}
        try:
            watched = int(progress.get("watched_episode_count") or 0)
            total = int(progress.get("total_episode_count") or 0)
        except (TypeError, ValueError):
            watched, total = 0, 0
        remaining = max(total - watched, 0)
        try:
            runtime = int(episode.get("runtime") or show.get("runtime") or 45)
        except (TypeError, ValueError):
            runtime = 45
        percent = round(watched / total * 100, 1) if total else 0.0
        output.append(
            {
                "show": show,
                "next_episode": episode,
                "watched_episodes": watched,
                "total_episodes": total,
                "remaining_episodes": remaining,
                "runtime": runtime,
                "watched_minutes": watched * runtime,
                "remaining_minutes": remaining * runtime,
                "percent": percent,
            }
        )
    return output


def normalize_provider_dataset(raw: dict[str, Any]) -> dict[str, Any]:
    sections = raw.get("sections") if isinstance(raw.get("sections"), dict) else {}
    return {
        **raw,
        "schema_version": NORMALIZED_SCHEMA_VERSION,
        "sources": build_sources(sections),
        "progress": build_progress(sections),
    }
