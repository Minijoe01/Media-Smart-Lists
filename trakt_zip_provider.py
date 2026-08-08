"""Import ZIP Trakt en lecture seule — Media Smart Lists.

Produit exactement le même NormalizedDataset que MDBListProvider, à partir
d'un export ZIP Trakt (watched-history, ratings, watchlist, listes,
playback, dropped). Les protections ZIP du script de migration sont
conservées : zip-slip, zip bomb, tailles et nombre de fichiers.

Aucun accès à l'API Trakt, aucune écriture distante.
"""

from __future__ import annotations

import io
import json
import re
import zipfile
from datetime import datetime
from pathlib import PurePosixPath
from typing import Any, Iterable
from zoneinfo import ZoneInfo

from normalized_model import normalize_provider_dataset

MAX_TOTAL_UNCOMPRESSED = 300 * 1024 * 1024  # 300 Mo décompressés max
MAX_MEMBER_BYTES = 60 * 1024 * 1024         # 60 Mo par fichier max
MAX_MEMBERS = 6000                           # 6000 fichiers max
_PARIS = ZoneInfo("Europe/Paris")


class TraktZipError(RuntimeError):
    """Erreur d'import ZIP Trakt (format ou sécurité)."""


def _safe_member_name(name: str) -> bool:
    path = PurePosixPath(name.replace("\\", "/"))
    return not path.is_absolute() and ".." not in path.parts


def _public_ids(ids: Any, media: str) -> dict[str, Any]:
    if not isinstance(ids, dict):
        return {}
    allowed = ("imdb", "tmdb", "trakt", "mdblist", "kitsu")
    if media == "show":
        allowed = allowed + ("tvdb",)
    result: dict[str, Any] = {}
    for key in allowed:
        value = ids.get(key)
        if value in (None, "", 0, "0"):
            continue
        if key in {"tmdb", "trakt", "tvdb", "kitsu"}:
            try:
                value = int(value)
            except (TypeError, ValueError):
                continue
        result[key] = value
    return result


def _media_stub(obj: Any, media: str) -> dict[str, Any]:
    if not isinstance(obj, dict):
        return {}
    return {
        "title": obj.get("title") or obj.get("name"),
        "year": obj.get("year"),
        "ids": _public_ids(obj.get("ids") or {}, media),
    }


def _media_key(ids: dict[str, Any], media: str) -> str:
    priority = ("tmdb", "imdb", "tvdb", "trakt", "mdblist", "kitsu")
    for key in priority:
        value = ids.get(key)
        if value not in (None, "", 0, "0"):
            return f"{key}:{value}"
    return ""


def _mdb_item(ids: dict[str, Any], title: Any, year: Any, media: str) -> dict[str, Any]:
    """Item au format des listes MDBList (id à plat = id TMDB, ids, imdb_id)."""
    item: dict[str, Any] = {"ids": dict(ids or {}), "title": str(title or "?"), "year": year}
    tmdb = ids.get("tmdb") if isinstance(ids, dict) else None
    item["id"] = tmdb if tmdb is not None else (ids.get("trakt") or 0)
    item["imdb_id"] = ids.get("imdb") or ""
    item["mediatype"] = "movie" if media == "movie" else "show"
    item["release_year"] = year
    return item


class TraktZip:
    """Ouverture sécurisée d'un ZIP Trakt (file-like ou chemin)."""

    def __init__(self, source: Any) -> None:
        try:
            self.archive = zipfile.ZipFile(source, "r")
        except zipfile.BadZipFile as exc:
            raise TraktZipError("Ce fichier n'est pas un ZIP valide.") from exc
        infos = self.archive.infolist()
        if len(infos) > MAX_MEMBERS:
            self.archive.close()
            raise TraktZipError("Trop de fichiers dans l'archive.")
        total = sum(item.file_size for item in infos)
        if total > MAX_TOTAL_UNCOMPRESSED:
            self.archive.close()
            raise TraktZipError("Archive trop volumineuse après décompression.")
        for item in infos:
            if not _safe_member_name(item.filename):
                self.archive.close()
                raise TraktZipError(f"Chemin dangereux dans le ZIP : {item.filename}")
            if item.file_size > MAX_MEMBER_BYTES:
                self.archive.close()
                raise TraktZipError(f"Fichier trop volumineux dans le ZIP : {item.filename}")

    def close(self) -> None:
        try:
            self.archive.close()
        except Exception:
            pass

    def names(self) -> list[str]:
        return [item.filename for item in self.archive.infolist() if not item.is_dir()]

    def load(self, name: str, default: Any = None) -> Any:
        try:
            raw = self.archive.read(name)
        except KeyError:
            return default
        try:
            return json.loads(raw.decode("utf-8-sig"))
        except (ValueError, UnicodeDecodeError) as exc:
            raise TraktZipError(f"Fichier JSON illisible : {name}") from exc

    def load_matching(self, pattern: str) -> list[tuple[str, Any]]:
        regex = re.compile(pattern)

        def numeric_order(name: str) -> tuple[Any, ...]:
            return tuple(int(part) if part.isdigit() else part for part in re.split(r"(\d+)", name))

        return [
            (name, self.load(name, []))
            for name in sorted((n for n in self.names() if regex.fullmatch(n)), key=numeric_order)
        ]


# ── Parsers ──────────────────────────────────────────────────────────────────


def _parse_watched(source: TraktZip) -> dict[str, Any]:
    movies: list[dict[str, Any]] = []
    episodes: list[dict[str, Any]] = []
    shows: dict[str, dict[str, Any]] = {}

    def add_show(show_stub: dict[str, Any], watched_at: Any) -> None:
        key = _media_key(show_stub.get("ids") or {}, "show")
        if not key:
            return
        previous = shows.get(key)
        if previous is None:
            shows[key] = {"show": show_stub, "last_watched_at": watched_at}
        else:
            previous["last_watched_at"] = watched_at

    # Historique événementiel complet (rewatches inclus).
    for filename, rows in source.load_matching(r"watched-history-\d+\.json"):
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            watched_at = row.get("watched_at")
            if isinstance(row.get("movie"), dict):
                movie = _media_stub(row["movie"], "movie")
                if not _media_key(movie.get("ids") or {}, "movie"):
                    continue
                movies.append(
                    {
                        "movie": movie,
                        "last_watched_at": watched_at,
                        "plays": 1,
                    }
                )
                continue
            if isinstance(row.get("episode"), dict) and isinstance(row.get("show"), dict):
                show_stub = _media_stub(row["show"], "show")
                episode = row["episode"]
                try:
                    season = int(episode.get("season"))
                    number = int(episode.get("number"))
                except (TypeError, ValueError):
                    continue
                if not _media_key(show_stub.get("ids") or {}, "show"):
                    continue
                episodes.append(
                    {
                        "episode": {
                            "title": episode.get("title"),
                            "season": season,
                            "number": number,
                            "ids": _public_ids(episode.get("ids") or {}, "episode"),
                            "show": show_stub,
                        },
                        "show": show_stub,
                        "last_watched_at": watched_at,
                        "plays": 1,
                    }
                )
                add_show(show_stub, watched_at)
                continue

    # Filet de sécurité : films vus présents dans le sommaire mais absents de
    # l'historique événementiel.
    for filename, rows in source.load_matching(r"watched-movies-\d+\.json"):
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("movie"), dict):
                continue
            movie = _media_stub(row["movie"], "movie")
            key = _media_key(movie.get("ids") or {}, "movie")
            if not key:
                continue
            already = any(
                _media_key(item.get("movie", {}).get("ids") or {}, "movie") == key for item in movies
            )
            if already:
                continue
            try:
                plays = int(row.get("plays") or 1)
            except (TypeError, ValueError):
                plays = 1
            movies.append(
                {
                    "movie": movie,
                    "last_watched_at": row.get("last_watched_at"),
                    "plays": plays,
                }
            )

    return {
        "movies": movies,
        "episodes": episodes,
        "shows": list(shows.values()),
    }


def _parse_ratings(source: TraktZip) -> dict[str, Any]:
    movies: list[dict[str, Any]] = []
    shows: list[dict[str, Any]] = []
    episodes: list[dict[str, Any]] = []
    for filename, rows in source.load_matching(r"ratings-\d+\.json"):
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            try:
                rating = float(row.get("rating"))
            except (TypeError, ValueError):
                continue
            if isinstance(row.get("movie"), dict):
                movie = _media_stub(row["movie"], "movie")
                if _media_key(movie.get("ids") or {}, "movie"):
                    movies.append({"movie": movie, "rating": rating, "rated_at": row.get("rated_at")})
                continue
            if isinstance(row.get("show"), dict):
                show = _media_stub(row["show"], "show")
                if _media_key(show.get("ids") or {}, "show"):
                    shows.append({"show": show, "rating": rating, "rated_at": row.get("rated_at")})
                continue
            if isinstance(row.get("episode"), dict):
                episode = _media_stub(row["episode"], "episode")
                show = _media_stub(row.get("show"), "show")
                if episode.get("ids"):
                    episodes.append({"episode": episode, "show": show, "rating": rating, "rated_at": row.get("rated_at")})
                continue
    return {"movies": movies, "shows": shows, "episodes": episodes}


def _parse_watchlist(source: TraktZip) -> dict[str, Any]:
    movies: list[dict[str, Any]] = []
    shows: list[dict[str, Any]] = []
    rows = source.load("lists-watchlist.json", [])
    if not isinstance(rows, list):
        rows = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        if isinstance(row.get("movie"), dict):
            movie = _media_stub(row["movie"], "movie")
            if _media_key(movie.get("ids") or {}, "movie"):
                movies.append(_mdb_item(movie.get("ids") or {}, movie.get("title"), movie.get("year"), "movie"))
            continue
        if isinstance(row.get("show"), dict):
            show = _media_stub(row["show"], "show")
            if _media_key(show.get("ids") or {}, "show"):
                shows.append(_mdb_item(show.get("ids") or {}, show.get("title"), show.get("year"), "show"))
            continue
        if isinstance(row.get("episode"), dict) and isinstance(row.get("show"), dict):
            show = _media_stub(row["show"], "show")
            if _media_key(show.get("ids") or {}, "show"):
                shows.append(_mdb_item(show.get("ids") or {}, show.get("title"), show.get("year"), "show"))
    return {"movies": movies, "shows": shows}


def _parse_lists(source: TraktZip) -> list[dict[str, Any]]:
    metadata = source.load("lists-lists.json", [])
    if not isinstance(metadata, list):
        metadata = []
    metadata_by_id: dict[str, dict[str, Any]] = {}
    for item in metadata:
        if not isinstance(item, dict):
            continue
        list_id = (item.get("ids") or {}).get("trakt")
        if list_id is not None:
            metadata_by_id[str(list_id)] = item

    output: list[dict[str, Any]] = []
    for filename, rows in source.load_matching(r"lists-list-\d+-.+\.json"):
        match = re.match(r"lists-list-(\d+)-(.+)\.json", filename)
        if not match:
            continue
        list_id, fallback_slug = match.groups()
        meta = metadata_by_id.get(list_id, {})
        name = meta.get("name") or fallback_slug.replace("-", " ").strip().title()
        movies: list[dict[str, Any]] = []
        shows: list[dict[str, Any]] = []
        if not isinstance(rows, list):
            rows = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            if isinstance(row.get("movie"), dict):
                movie = _media_stub(row["movie"], "movie")
                if _media_key(movie.get("ids") or {}, "movie"):
                    movies.append(_mdb_item(movie.get("ids") or {}, movie.get("title"), movie.get("year"), "movie"))
                continue
            if isinstance(row.get("show"), dict):
                show = _media_stub(row["show"], "show")
                if _media_key(show.get("ids") or {}, "show"):
                    shows.append(_mdb_item(show.get("ids") or {}, show.get("title"), show.get("year"), "show"))
                continue
        output.append(
            {
                "id": int(list_id) if list_id.isdigit() else list_id,
                "name": name,
                "type": "static",
                "description": meta.get("description") or "",
                "movies": movies,
                "shows": shows,
            }
        )
    return output


def _parse_playback(source: TraktZip) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for filename, rows in source.load_matching(r"playback-\d+\.json"):
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            item: dict[str, Any] = {
                "id": row.get("id"),
                "progress": row.get("progress"),
                "paused_at": row.get("paused_at"),
                "type": row.get("type"),
            }
            if isinstance(row.get("movie"), dict):
                item["movie"] = _media_stub(row["movie"], "movie")
                output.append(item)
                continue
            if isinstance(row.get("episode"), dict):
                episode = row["episode"]
                show = _media_stub(row.get("show"), "show")
                item["episode"] = {
                    "title": episode.get("title"),
                    "season": episode.get("season"),
                    "number": episode.get("number"),
                    "ids": _public_ids(episode.get("ids") or {}, "episode"),
                    "show": show,
                }
                item["show"] = show
                output.append(item)
                continue
            if isinstance(row.get("show"), dict):
                item["show"] = _media_stub(row["show"], "show")
                output.append(item)
    return output


def _parse_dropped(source: TraktZip) -> dict[str, Any]:
    shows: list[dict[str, Any]] = []
    for filename, rows in source.load_matching(r"dropped-\d+\.json"):
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            if isinstance(row.get("show"), dict):
                show = _media_stub(row["show"], "show")
                if _media_key(show.get("ids") or {}, "show"):
                    shows.append({"show": show, "dropped_at": row.get("dropped_at")})
    return {"shows": shows}


# ── API publique ─────────────────────────────────────────────────────────────


def load_trakt_zip(zip_bytes: bytes) -> dict[str, Any]:
    """Parse un ZIP Trakt et retourne un NormalizedDataset (comme MDBList)."""
    if not zip_bytes:
        raise TraktZipError("Fichier vide.")
    source = TraktZip(io.BytesIO(zip_bytes))
    try:
        sections: dict[str, Any] = {
            "watched": _parse_watched(source),
            "ratings": _parse_ratings(source),
            "watchlist": _parse_watchlist(source),
            "user_lists": _parse_lists(source),
            "playback": _parse_playback(source),
            "dropped": _parse_dropped(source),
            "upnext": [],
            "genres": [],
        }
    finally:
        source.close()

    raw = {
        "sections": sections,
        "source": "trakt_zip",
        "loaded_at": datetime.now(_PARIS).isoformat(),
        "request_count": 0,
    }
    return normalize_provider_dataset(raw)


def summarize(dataset: dict[str, Any]) -> dict[str, int]:
    """Petits compteurs pour le message d'import."""
    sections = dataset.get("sections") or {}
    watched = sections.get("watched") or {}
    ratings = sections.get("ratings") or {}
    watchlist = sections.get("watchlist") or {}
    return {
        "films_vus": len(watched.get("movies") or []),
        "episodes_vus": len(watched.get("episodes") or []),
        "series_vues": len(watched.get("shows") or []),
        "notes": sum(len(ratings.get(key) or []) for key in ("movies", "shows", "episodes")),
        "watchlist": len(watchlist.get("movies") or []) + len(watchlist.get("shows") or []),
        "listes": len(sections.get("user_lists") or []),
    }
