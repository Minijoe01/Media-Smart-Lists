"""Modèle commun Media Smart Lists, indépendant du fournisseur d'origine."""

from __future__ import annotations

from typing import Any


NORMALIZED_SCHEMA_VERSION = 4


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


def build_sources(sections: dict[str, Any], source_name: str = "mdblist") -> list[dict[str, Any]]:
    watchlist = sections.get("watchlist") or {}
    user_lists = sections.get("user_lists") or []
    is_zip = source_name == "trakt_zip"
    watchlist_label = "Watchlist Trakt (import ZIP)" if is_zip else "Watchlist MDBList"
    sources = [
        _source(
            "watchlist",
            watchlist_label,
            watchlist_label,
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
        raw_type = str(item.get("type") or "").strip().lower()
        list_type = raw_type if raw_type in {"static", "dynamic", "ai", "feed", "other"} else "static"
        key = f"list:{list_id}"
        name = str(item.get("name") or "Liste MDBList")
        type_labels = {
            "static": "Liste statique",
            "dynamic": "Liste dynamique",
            "ai": "Liste IA",
            "feed": "Liste flux",
            "other": "Liste",
        }
        label = f"{type_labels[list_type]} : {name}"
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
        if list_type == "dynamic":
            dynamic_keys.append(key)
        elif list_type == "static":
            static_keys.append(key)

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


def _id_keys(item: dict[str, Any]) -> set[str]:
    """Clés d'identité permettant de rapprocher deux représentations d'une série."""
    ids = item.get("ids") if isinstance(item.get("ids"), dict) else {}
    output = set()
    for provider in ("mdblist", "tmdb", "tvdb", "imdb", "trakt"):
        value = ids.get(provider)
        if value not in (None, "", 0, "0"):
            output.add(f"{provider}:{value}")
    return output


def _genre_names(item: dict[str, Any]) -> list[str]:
    values = item.get("genres") or []
    output = set()
    for value in values:
        if isinstance(value, dict):
            value = value.get("name") or value.get("title") or value.get("slug")
        if value:
            output.add(str(value).strip().title())
    return sorted(output, key=str.casefold)


def _last_air_date(item: dict[str, Any]) -> str | None:
    """Date exacte du dernier épisode disponible lorsqu'elle existe dans les données."""
    for key in ("last_air_date", "last_aired_at", "last_episode_air_date", "latest_air_date"):
        if item.get(key):
            return str(item[key])
    nested = item.get("last_episode_to_air")
    if isinstance(nested, dict) and (nested.get("air_date") or nested.get("aired_at")):
        return str(nested.get("air_date") or nested.get("aired_at"))
    return None


def _episode_runtime_local(episode: dict[str, Any], show: dict[str, Any], total: int = 0) -> int:
    """Durée réaliste d'un épisode (1 à 300 min).

    Si la valeur dépasse 300 min, elle est probablement cumulée (toute la
    série) ou en secondes : on la divise par le nombre d'épisodes connu, ou
    par 60 (conversion secondes → minutes), sinon on retombe sur 45.
    """
    raw = None
    try:
        if episode.get("runtime"):
            raw = int(round(float(episode["runtime"])))
    except (TypeError, ValueError):
        raw = None
    if raw is None:
        try:
            if show.get("runtime"):
                raw = int(round(float(show["runtime"])))
        except (TypeError, ValueError):
            raw = None
    if raw is None:
        return 45
    if 1 <= raw <= 300:
        return raw
    if total and total > 0:
        average = int(round(raw / total))
        if 1 <= average <= 300:
            return average
    seconds = int(round(raw / 60))
    if 1 <= seconds <= 300:
        return seconds
    return 45


def build_progress(sections: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalise Up Next et réutilise localement les métadonnées déjà chargées.

    `/upnext` donne l'ordre de dernier visionnage, la progression et l'épisode à
    voir. `/sync/watched`, déjà présent dans le même dataset, apporte notamment
    les genres. Leur rapprochement ne déclenche donc aucune requête API.
    """
    metadata_by_id: dict[str, dict[str, Any]] = {}
    watched_at_by_id: dict[str, str] = {}
    watched_section = sections.get("watched") or {}
    for row in watched_section.get("shows") or []:
        if not isinstance(row, dict):
            continue
        metadata = row.get("show") if isinstance(row.get("show"), dict) else row
        if not isinstance(metadata, dict):
            continue
        for identity in _id_keys(metadata):
            metadata_by_id[identity] = metadata
            if row.get("last_watched_at"):
                watched_at_by_id[identity] = str(row["last_watched_at"])

    output = []
    for item in sections.get("upnext") or []:
        if not isinstance(item, dict):
            continue
        upnext_show = item.get("show") if isinstance(item.get("show"), dict) else {}
        history_show: dict[str, Any] = {}
        history_watched_at: str | None = None
        for identity in _id_keys(upnext_show):
            if identity in metadata_by_id:
                history_show = metadata_by_id[identity]
                history_watched_at = watched_at_by_id.get(identity) or history_watched_at
                break

        # Les champs spécifiques Up Next (poster, titre, etc.) restent prioritaires,
        # tandis que l'historique complète genres, runtime et statut s'ils manquent.
        show = {**history_show, **upnext_show}
        history_ids = history_show.get("ids") if isinstance(history_show.get("ids"), dict) else {}
        upnext_ids = upnext_show.get("ids") if isinstance(upnext_show.get("ids"), dict) else {}
        if history_ids or upnext_ids:
            show["ids"] = {**history_ids, **upnext_ids}

        episode = item.get("next_episode") if isinstance(item.get("next_episode"), dict) else {}
        progress = item.get("progress") if isinstance(item.get("progress"), dict) else {}
        try:
            watched = int(progress.get("watched_episode_count") or 0)
            total = int(progress.get("total_episode_count") or 0)
        except (TypeError, ValueError):
            watched, total = 0, 0
        remaining = max(total - watched, 0)
        # Durée réelle d'un épisode : le `runtime` d'une série peut être la
        # durée CUMULÉE (ex. émissions quotidiennes) — on normalise comme dans
        # history_engine pour éviter des « 22 ans de visionnage » aberrants.
        runtime = _episode_runtime_local(episode, show, total)
        percent = round(watched / total * 100, 1) if total else 0.0

        exact_last_air = _last_air_date(item) or _last_air_date(show) or _last_air_date(progress)
        next_episode_air = episode.get("air_date") or episode.get("aired_at")
        latest_available_at = exact_last_air or next_episode_air
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
                "genres": _genre_names(show),
                "last_watched_at": item.get("last_watched_at") or history_watched_at,
                "latest_available_at": latest_available_at,
                "latest_available_is_fallback": bool(latest_available_at and not exact_last_air),
            }
        )
    return output


def _identity_keys(media: dict[str, Any]) -> set[str]:
    """Toutes les identités d'un média (clés `kind:provider:value`), depuis le
    bloc `ids` ET les champs à plat (`id`, `imdb_id`, `tvdb_id`, `tmdb_id`).
    Les items de Watchlist MDBList n'ont pas de bloc `ids` imbriqué."""
    kind = media_type(media)
    ids = media.get("ids") if isinstance(media.get("ids"), dict) else {}
    output: set[str] = set()
    for provider, value in (
        ("tmdb", ids.get("tmdb")),
        ("imdb", ids.get("imdb")),
        ("tvdb", ids.get("tvdb")),
        ("trakt", ids.get("trakt")),
        ("mdblist", ids.get("mdblist")),
    ):
        if value not in (None, "", 0, "0"):
            output.add(f"{kind}:{provider}:{value}")
    # Champs à plat (format Watchlist / playback MDBList).
    flat = {
        "tmdb": media.get("tmdb_id") or media.get("tmdbid") or media.get("tmdb"),
        "imdb": media.get("imdb_id") or media.get("imdb"),
        "tvdb": media.get("tvdb_id") or media.get("tvdb"),
    }
    for provider, value in flat.items():
        if value not in (None, "", 0, "0"):
            output.add(f"{kind}:{provider}:{value}")
    # L'id MDBList d'un média correspond à son id TMDb.
    raw_id = media.get("id")
    try:
        candidate = int(raw_id)
    except (TypeError, ValueError):
        candidate = None
    if candidate and candidate > 0:
        output.add(f"{kind}:tmdb:{candidate}")
    return output


def _genre_lookup(sections: dict[str, Any]) -> dict[str, list[str]]:
    """Indexe les genres connus par identité de média (tmdb/imdb/tvdb/…).

    Permet de compléter les contenus de la Watchlist dont le champ `genres`
    est absent (certaines réponses MDBList l'omettent), sans aucun appel API.
    """
    def unwrap(item: Any) -> dict[str, Any]:
        if not isinstance(item, dict):
            return {}
        for key in ("movie", "show", "episode"):
            nested = item.get(key)
            if isinstance(nested, dict):
                return nested
        return item

    lookup: dict[str, list[str]] = {}

    def add(item: Any) -> None:
        media = unwrap(item)
        if not media:
            return
        names = _genre_names(media)
        if not names:
            return
        for key in _identity_keys(media):
            lookup.setdefault(key, names)

    watched = sections.get("watched") or {}
    for row in watched.get("movies") or []:
        add(row)
    for row in watched.get("shows") or []:
        add(row)
    for row in watched.get("episodes") or []:
        episode = row.get("episode") if isinstance(row.get("episode"), dict) else {}
        add(episode.get("show") if isinstance(episode.get("show"), dict) else episode)
    ratings = sections.get("ratings") or {}
    for row in ratings.get("movies") or []:
        add(row)
    for row in ratings.get("shows") or []:
        add(row)
    for item in sections.get("user_lists") or []:
        if not isinstance(item, dict):
            continue
        for movie in item.get("movies") or []:
            add(movie)
        for show in item.get("shows") or []:
            add(show)
    for row in sections.get("upnext") or []:
        if isinstance(row, dict):
            add(row.get("show"))
    for row in sections.get("playback") or []:
        if isinstance(row, dict):
            add(row.get("movie"))
            add(row.get("show"))
            episode = row.get("episode") if isinstance(row.get("episode"), dict) else {}
            add(episode.get("show") if isinstance(episode.get("show"), dict) else episode)
    dropped = sections.get("dropped") or {}
    for show in dropped.get("shows") or []:
        add(show)
    return lookup


def _fill_watchlist_genres(sections: dict[str, Any]) -> None:
    """Complète les genres manquants des contenus de la Watchlist depuis les
    autres sections (historique, listes, notes, progression) — 0 appel API."""
    lookup = _genre_lookup(sections)
    watchlist = sections.get("watchlist") or {}
    for movie in watchlist.get("movies") or []:
        if not isinstance(movie, dict) or _genre_names(movie):
            continue
        names = _find_genre(lookup, movie)
        if names:
            movie["genres"] = names
    for show in watchlist.get("shows") or []:
        if not isinstance(show, dict) or _genre_names(show):
            continue
        names = _find_genre(lookup, show)
        if names:
            show["genres"] = names


def _find_genre(lookup: dict[str, list[str]], item: dict[str, Any]) -> list[str] | None:
    for key in _identity_keys(item):
        names = lookup.get(key)
        if names:
            return names
    return None


def normalize_provider_dataset(raw: dict[str, Any]) -> dict[str, Any]:
    sections = raw.get("sections") if isinstance(raw.get("sections"), dict) else {}
    source_name = str(raw.get("source") or "mdblist")
    _fill_watchlist_genres(sections)
    return {
        **raw,
        "schema_version": NORMALIZED_SCHEMA_VERSION,
        "sources": build_sources(sections, source_name=source_name),
        "progress": build_progress(sections),
    }
