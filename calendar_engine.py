"""Calendrier fournisseur-neutre Media Smart Lists.

Normalise les événements MDBList, applique les filtres localement et produit
des exports CSV/ICS sans nouvelle requête réseau.
"""

from __future__ import annotations

import csv
import io
from datetime import date, datetime, timezone
from typing import Any, Iterable


CALENDAR_ENGINE_VERSION = 1
CALENDAR_TYPE_OPTIONS = ["Tous", "Films", "Séries", "Épisodes"]
CALENDAR_TIMING_OPTIONS = [
    "Tout l’horizon",
    "Aujourd’hui",
    "7 prochains jours",
    "30 prochains jours",
    "90 prochains jours",
]
CALENDAR_SORT_OPTIONS = [
    "Date — proche d’abord",
    "Date — lointaine d’abord",
    "Titre A → Z",
    "Type",
]


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _parse_datetime(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    try:
        parsed = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except (TypeError, ValueError):
        return None


def _first_date(*containers: dict[str, Any]) -> datetime | None:
    keys = (
        "datetime",
        "date",
        "air_date",
        "first_aired",
        "release_date",
        "released",
        "released_at",
        "released_digital",
        "digital_release_date",
        "next_air_date",
        "starts_at",
        "start",
        "_calendar_date",
    )
    for container in containers:
        for key in keys:
            parsed = _parse_datetime(container.get(key))
            if parsed:
                return parsed
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


def _genres(*containers: dict[str, Any]) -> list[str]:
    output: dict[str, str] = {}
    for container in containers:
        for value in container.get("genres") or []:
            if isinstance(value, dict):
                value = value.get("name") or value.get("title") or value.get("slug")
            if value:
                text = str(value).strip().title()
                output.setdefault(text.casefold(), text)
    return sorted(output.values(), key=str.casefold)


def _poster(*containers: dict[str, Any]) -> str:
    for container in containers:
        value = container.get("poster") or container.get("poster_path")
        if value:
            return str(value)
    return ""


def _ids(*containers: dict[str, Any]) -> dict[str, Any]:
    output = {}
    for container in containers:
        values = container.get("ids") if isinstance(container.get("ids"), dict) else {}
        output.update({key: value for key, value in values.items() if value not in (None, "")})
    return output


def build_local_calendar_events(
    dataset: dict[str, Any],
    start_date: date,
    end_date: date,
) -> list[dict[str, Any]]:
    """Calendrier de secours depuis les dates déjà présentes dans le dataset."""
    output: list[dict[str, Any]] = []
    seen: set[str] = set()

    def in_range(value: Any) -> bool:
        parsed = _parse_datetime(value)
        return bool(parsed and start_date <= parsed.date() <= end_date)

    def add(event: dict[str, Any], kind: str, media: dict[str, Any], value: Any) -> None:
        parsed = _parse_datetime(value)
        if not parsed or not in_range(value):
            return
        ids = media.get("ids") if isinstance(media.get("ids"), dict) else {}
        marker_id = ids.get("tmdb") or ids.get("imdb") or ids.get("mdblist") or media.get("title")
        marker = f"{kind}:{marker_id}:{parsed.isoformat()}"
        if marker in seen:
            return
        seen.add(marker)
        output.append(event)

    sections = dataset.get("sections") or {}
    for row in sections.get("upnext") or []:
        if not isinstance(row, dict):
            continue
        show = _dict(row.get("show"))
        episode = _dict(row.get("next_episode"))
        value = episode.get("air_date") or episode.get("first_aired")
        add(
            {
                "event_type": "episode",
                "first_aired": value,
                "show": show,
                "episode": episode,
                "source": "Vos séries en cours",
            },
            "episode",
            show,
            value,
        )

    for source in dataset.get("sources") or []:
        if not isinstance(source, dict) or source.get("kind") == "aggregate":
            continue
        source_name = str(source.get("name") or source.get("label") or "Vos listes")
        for movie in source.get("movies") or []:
            if not isinstance(movie, dict):
                continue
            value = (
                movie.get("release_date")
                or movie.get("released")
                or movie.get("released_digital")
                or movie.get("digital_release_date")
            )
            add(
                {"type": "movie", "release_date": value, "movie": movie, "source": source_name},
                "movie",
                movie,
                value,
            )
        for show in source.get("shows") or []:
            if not isinstance(show, dict):
                continue
            value = show.get("release_date") or show.get("released") or show.get("first_air_date") or show.get("next_air_date")
            add(
                {"type": "show", "date": value, "show": show, "source": source_name},
                "show",
                show,
                value,
            )
    return output


def normalize_calendar_events(
    events: Iterable[dict[str, Any]],
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    now = now or datetime.now(timezone.utc)
    output = []
    seen = set()
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            continue
        movie = _dict(event.get("movie"))
        show = _dict(event.get("show"))
        episode = _dict(event.get("episode"))
        media = _dict(event.get("media"))
        if not movie and str(media.get("type") or media.get("mediatype") or "").lower() == "movie":
            movie = media
        if not show and str(media.get("type") or media.get("mediatype") or "").lower() in {"show", "tv", "series"}:
            show = media
        if not show and isinstance(episode.get("show"), dict):
            show = episode["show"]

        raw_type = str(event.get("event_type") or event.get("type") or event.get("_calendar_bucket") or "").lower()
        if movie or "movie" in raw_type or "film" in raw_type:
            kind = "movie"
            type_label = "Film"
            primary = movie or media or event
        elif episode or "episode" in raw_type:
            kind = "episode"
            type_label = "Épisode"
            primary = show or media or episode or event
        else:
            kind = "show"
            type_label = "Série"
            primary = show or media or event

        title = str(primary.get("title") or primary.get("name") or event.get("title") or "Titre inconnu")
        year_value = primary.get("year") or primary.get("release_year") or event.get("year")
        try:
            year = int(year_value) if year_value else None
        except (TypeError, ValueError):
            year = None
        event_datetime = _first_date(event, episode, movie, show, media)
        if event_datetime and now.tzinfo:
            event_datetime = event_datetime.astimezone(now.tzinfo)
        days_until = (event_datetime.date() - now.date()).days if event_datetime else None
        season, number = _episode_numbers(episode)
        episode_title = str(episode.get("title") or episode.get("name") or "")
        episode_label = ""
        if kind == "episode":
            if season or number:
                episode_label = f"S{season:02d}E{number:02d}"
            if episode_title:
                episode_label = f"{episode_label} · {episode_title}" if episode_label else episode_title

        description = str(
            event.get("description")
            or primary.get("description")
            or primary.get("overview")
            or episode.get("description")
            or ""
        )
        source = str(event.get("source") or event.get("reason") or event.get("calendar_source") or "Calendrier MDBList")
        ids = _ids(primary, show, movie, media)
        key_id = ids.get("tmdb") or ids.get("imdb") or ids.get("mdblist") or index
        marker = (kind, str(key_id), event_datetime.isoformat() if event_datetime else str(index))
        if marker in seen:
            continue
        seen.add(marker)
        output.append(
            {
                "key": f"calendar:{kind}:{key_id}:{event_datetime.isoformat() if event_datetime else index}",
                "kind": kind,
                "media_kind": "movie" if kind == "movie" else "show",
                "type": type_label,
                "title": title,
                "year": year,
                "datetime": event_datetime,
                "days_until": days_until,
                "episode_label": episode_label,
                "genres": _genres(primary, show, movie, media),
                "poster": _poster(event, primary, episode, show, movie, media),
                "ids": ids,
                "description": description,
                "source": source,
                "raw": event,
            }
        )
    return sorted(
        output,
        key=lambda row: (
            row.get("datetime") is None,
            row.get("datetime") or datetime.max.replace(tzinfo=timezone.utc),
            row["title"].casefold(),
        ),
    )


def filter_calendar_events(
    rows: Iterable[dict[str, Any]],
    type_filter: str = "Tous",
    timing_filter: str = "Tout l’horizon",
    search: str = "",
    sort_mode: str = "Date — proche d’abord",
) -> list[dict[str, Any]]:
    query = str(search or "").strip().casefold()
    output = []
    for row in rows:
        if type_filter == "Films" and row.get("type") != "Film":
            continue
        if type_filter == "Séries" and row.get("type") != "Série":
            continue
        if type_filter == "Épisodes" and row.get("type") != "Épisode":
            continue
        searchable = f"{row.get('title', '')} {row.get('episode_label', '')}".casefold()
        if query and query not in searchable:
            continue
        days = row.get("days_until")
        if timing_filter == "Aujourd’hui" and days != 0:
            continue
        if timing_filter == "7 prochains jours" and (days is None or not 0 <= days <= 7):
            continue
        if timing_filter == "30 prochains jours" and (days is None or not 0 <= days <= 30):
            continue
        if timing_filter == "90 prochains jours" and (days is None or not 0 <= days <= 90):
            continue
        output.append(row)

    if sort_mode == "Date — lointaine d’abord":
        return sorted(output, key=lambda row: (row.get("datetime") is None, row.get("datetime") or datetime.min.replace(tzinfo=timezone.utc)), reverse=True)
    if sort_mode == "Titre A → Z":
        return sorted(output, key=lambda row: row["title"].casefold())
    if sort_mode == "Type":
        return sorted(output, key=lambda row: (row["type"], row.get("datetime") is None, row.get("datetime") or datetime.max.replace(tzinfo=timezone.utc)))
    return sorted(output, key=lambda row: (row.get("datetime") is None, row.get("datetime") or datetime.max.replace(tzinfo=timezone.utc)))


def group_calendar_by_day(rows: Iterable[dict[str, Any]]) -> list[tuple[date | None, list[dict[str, Any]]]]:
    groups: dict[date | None, list[dict[str, Any]]] = {}
    for row in rows:
        event_datetime = row.get("datetime")
        day = event_datetime.date() if isinstance(event_datetime, datetime) else None
        groups.setdefault(day, []).append(row)
    keys = sorted((key for key in groups if key is not None))
    if None in groups:
        keys.append(None)
    return [(key, groups[key]) for key in keys]


def rows_to_csv(rows: Iterable[dict[str, Any]]) -> str:
    values = []
    for row in rows:
        event_datetime = row.get("datetime")
        values.append(
            {
                "date": event_datetime.isoformat() if isinstance(event_datetime, datetime) else "",
                "type": row.get("type"),
                "titre": row.get("title"),
                "annee": row.get("year"),
                "episode": row.get("episode_label"),
                "genres": " | ".join(row.get("genres") or []),
                "source": row.get("source"),
            }
        )
    if not values:
        return ""
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=list(values[0]))
    writer.writeheader()
    writer.writerows(values)
    return stream.getvalue()


def _ics_escape(value: Any) -> str:
    return str(value or "").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def rows_to_ics(rows: Iterable[dict[str, Any]]) -> str:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Media Smart Lists//Calendar//FR",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for row in rows:
        event_datetime = row.get("datetime")
        if not isinstance(event_datetime, datetime):
            continue
        utc_value = event_datetime.astimezone(timezone.utc)
        has_time = any((utc_value.hour, utc_value.minute, utc_value.second))
        if has_time:
            dtstart = f"DTSTART:{utc_value.strftime('%Y%m%dT%H%M%SZ')}"
        else:
            dtstart = f"DTSTART;VALUE=DATE:{utc_value.strftime('%Y%m%d')}"
        episode = f" — {row['episode_label']}" if row.get("episode_label") else ""
        summary = f"{row.get('type')} — {row.get('title')}{episode}"
        description = row.get("description") or f"Source : {row.get('source')}"
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{_ics_escape(row.get('key'))}@media-smart-lists",
                f"DTSTAMP:{stamp}",
                dtstart,
                f"SUMMARY:{_ics_escape(summary)}",
                f"DESCRIPTION:{_ics_escape(description)}",
                "END:VEVENT",
            ]
        )
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"
