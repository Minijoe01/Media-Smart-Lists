#!/usr/bin/env python3
"""
Migration locale d'un export ZIP Trakt vers MDBList.

Sécurité :
- mode simulation (dry-run) par défaut ; aucun appel réseau sans --apply ;
- aucune suppression distante ;
- clé API lue depuis MDBLIST_API_KEY ou demandée de façon masquée ;
- sauvegarde neutre locale de l'historique complet et des éléments non importables ;
- confirmation explicite avant écriture.

Dépendances : bibliothèque standard Python uniquement.

Exemples :
    # 1) Analyser sans toucher à MDBList
    python migrate_trakt_zip_to_mdblist.py trakt-export.zip

    # 2) Vérifier le compte et les quotas MDBList, sans écriture
    $env:MDBLIST_API_KEY="votre-cle"
    python migrate_trakt_zip_to_mdblist.py trakt-export.zip --check-api

    # 3) Importer (PowerShell)
    python migrate_trakt_zip_to_mdblist.py trakt-export.zip --apply

    # 3) Importer (Linux/macOS)
    MDBLIST_API_KEY="votre-cle" python3 migrate_trakt_zip_to_mdblist.py trakt-export.zip --apply

    # Vérifier l'organisation exclusive recommandée (aucun doublon de conteneur)
    python migrate_trakt_zip_to_mdblist.py trakt-export.zip --check-api \
        --list-layout exclusive-watchlist

    # Import partiel
    python migrate_trakt_zip_to_mdblist.py trakt-export.zip --apply \
        --sections watched,ratings,watchlist

Limitations MDBList importantes :
- MDBList conserve un état vu et une dernière date par média, pas l'ensemble des
  événements de rewatch Trakt. Tous les événements restent archivés localement.
- Les listes statiques MDBList acceptent surtout films et séries. Les saisons,
  épisodes et personnes sont archivés dans le rapport mais non ajoutés.
- L'API de création de liste ne permet pas de restaurer la description ni les
  dates d'ajout/rangs Trakt de façon garantie.
- Les points de reprise ne sont importés que si watched-playback.json en contient.
"""

from __future__ import annotations

import argparse
import csv
import getpass
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Iterator

VERSION = "0.2.0"
API_BASE = "https://api.mdblist.com"
USER_AGENT = f"Trakt-ZIP-to-MDBList/{VERSION}"
DEFAULT_SECTIONS = ("watched", "ratings", "watchlist", "collection", "lists")
VALID_SECTIONS = set(DEFAULT_SECTIONS)
MAX_MEMBER_BYTES = 512 * 1024 * 1024
MAX_TOTAL_UNCOMPRESSED = 1024 * 1024 * 1024
MAX_RETRIES = 5


# ---------------------------------------------------------------------------
# Utilitaires généraux
# ---------------------------------------------------------------------------


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_iso(value: Any) -> datetime:
    if not value:
        return datetime.min.replace(tzinfo=timezone.utc)
    text = str(value).strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except Exception:
        return datetime.min.replace(tzinfo=timezone.utc)


def latest_iso(first: Any, second: Any) -> str | None:
    if not first:
        return str(second) if second else None
    if not second:
        return str(first)
    return str(second) if parse_iso(second) > parse_iso(first) else str(first)


def safe_member_name(name: str) -> bool:
    path = PurePosixPath(name.replace("\\", "/"))
    return not path.is_absolute() and ".." not in path.parts


def sanitize_filename(value: str, fallback: str = "file") -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip("-._")
    return cleaned or fallback


def json_dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def chunks(values: list[Any], size: int) -> Iterator[list[Any]]:
    for index in range(0, len(values), size):
        yield values[index : index + size]


def dedupe_dicts(values: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    output: list[dict[str, Any]] = []
    for value in values:
        marker = json.dumps(value, sort_keys=True, ensure_ascii=False)
        if marker in seen:
            continue
        seen.add(marker)
        output.append(value)
    return output


def public_ids(ids: Any, media: str) -> dict[str, Any]:
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


def media_key(ids: dict[str, Any], media: str) -> str:
    priority = ("tmdb", "imdb", "tvdb", "trakt", "mdblist", "kitsu")
    for key in priority:
        if key in ids and ids[key] not in (None, ""):
            return f"{media}:{key}:{ids[key]}"
    return ""


def media_stub(obj: Any, media: str) -> dict[str, Any]:
    if not isinstance(obj, dict):
        return {}
    ids = public_ids(obj.get("ids"), media)
    result: dict[str, Any] = {"ids": ids}
    if obj.get("title") is not None:
        result["title"] = obj.get("title")
    if obj.get("year") is not None:
        result["year"] = obj.get("year")
    return result


# ---------------------------------------------------------------------------
# Lecture ZIP sécurisée
# ---------------------------------------------------------------------------


class TraktZip:
    def __init__(self, path: Path):
        self.path = path
        self.archive = zipfile.ZipFile(path, "r")
        total = sum(item.file_size for item in self.archive.infolist())
        if total > MAX_TOTAL_UNCOMPRESSED:
            raise ValueError("Archive trop volumineuse après décompression")
        for item in self.archive.infolist():
            if not safe_member_name(item.filename):
                raise ValueError(f"Chemin dangereux dans le ZIP : {item.filename}")
            if item.file_size > MAX_MEMBER_BYTES:
                raise ValueError(f"Fichier trop volumineux dans le ZIP : {item.filename}")

    def close(self) -> None:
        self.archive.close()

    def names(self) -> list[str]:
        return [item.filename for item in self.archive.infolist() if not item.is_dir()]

    def load(self, name: str, default: Any = None) -> Any:
        try:
            raw = self.archive.read(name)
        except KeyError:
            return default
        return json.loads(raw.decode("utf-8-sig"))

    def load_matching(self, pattern: str) -> list[tuple[str, Any]]:
        regex = re.compile(pattern)
        matched = [name for name in self.names() if regex.fullmatch(name)]

        def numeric_order(name: str) -> tuple[Any, ...]:
            return tuple(int(part) if part.isdigit() else part for part in re.split(r"(\d+)", name))

        return [(name, self.load(name, [])) for name in sorted(matched, key=numeric_order)]


# ---------------------------------------------------------------------------
# Plan de migration
# ---------------------------------------------------------------------------


@dataclass
class MigrationPlan:
    archive_name: str
    archive_sha256: str
    history_events: list[dict[str, Any]] = field(default_factory=list)
    latest_movies: dict[str, dict[str, Any]] = field(default_factory=dict)
    latest_episodes: dict[str, dict[str, Any]] = field(default_factory=dict)
    movie_ratings: list[dict[str, Any]] = field(default_factory=list)
    show_ratings: dict[str, dict[str, Any]] = field(default_factory=dict)
    watchlist_movies: list[dict[str, Any]] = field(default_factory=list)
    watchlist_shows: list[dict[str, Any]] = field(default_factory=list)
    collection_movies: list[dict[str, Any]] = field(default_factory=list)
    collection_shows: list[dict[str, Any]] = field(default_factory=list)
    personal_lists: list[dict[str, Any]] = field(default_factory=list)
    playback: list[dict[str, Any]] = field(default_factory=list)
    liked_lists: list[dict[str, Any]] = field(default_factory=list)
    unsupported: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    list_layout: str = "original"
    overlap_audit: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        rewatch_events = len(self.history_events) - len(self.latest_movies) - len(self.latest_episodes)
        static_lists = [
            {
                "name": str(item.get("name") or "Liste"),
                "movies": len(item.get("movies", [])),
                "shows": len(item.get("shows", [])),
                "total": len(item.get("movies", [])) + len(item.get("shows", [])),
            }
            for item in self.personal_lists
        ]
        return {
            "archive_name": self.archive_name,
            "archive_sha256": self.archive_sha256,
            "list_layout": self.list_layout,
            "history_events_total": len(self.history_events),
            "history_unique_movies": len(self.latest_movies),
            "history_unique_episodes": len(self.latest_episodes),
            "history_extra_rewatch_events": max(rewatch_events, 0),
            "ratings_movies": len(self.movie_ratings),
            "ratings_shows_with_show_or_episode_ratings": len(self.show_ratings),
            "watchlist_movies": len(self.watchlist_movies),
            "watchlist_shows": len(self.watchlist_shows),
            "collection_movies": len(self.collection_movies),
            "collection_shows": len(self.collection_shows),
            "personal_lists": len(self.personal_lists),
            "personal_list_items": sum(len(item.get("movies", [])) + len(item.get("shows", [])) for item in self.personal_lists),
            "static_lists": static_lists,
            "overlap_audit": self.overlap_audit,
            "playback_sessions": len(self.playback),
            "liked_lists_metadata": len(self.liked_lists),
            "unsupported_items": len(self.unsupported),
            "warnings": self.warnings,
        }


def build_plan(zip_path: Path) -> MigrationPlan:
    digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    plan = MigrationPlan(zip_path.name, digest)
    source = TraktZip(zip_path)
    try:
        parse_history(source, plan)
        parse_ratings(source, plan)
        parse_watchlist(source, plan)
        parse_collection(source, plan)
        parse_lists(source, plan)
        parse_liked_lists(source, plan)
        parse_playback(source, plan)
    finally:
        source.close()
    return plan


def parse_history(source: TraktZip, plan: MigrationPlan) -> None:
    # Historique événementiel complet, incluant les rewatches.
    for filename, rows in source.load_matching(r"watched-history-\d+\.json"):
        if not isinstance(rows, list):
            plan.warnings.append(f"{filename}: tableau attendu")
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            watched_at = row.get("watched_at")
            if isinstance(row.get("movie"), dict):
                movie = media_stub(row["movie"], "movie")
                key = media_key(movie.get("ids", {}), "movie")
                if not key:
                    plan.unsupported.append({"section": "history", "reason": "movie_without_supported_id", "source_file": filename})
                    continue
                event = {
                    "type": "movie",
                    "watched_at": watched_at,
                    "ids": movie.get("ids", {}),
                    "title": movie.get("title"),
                    "year": movie.get("year"),
                    "trakt_history_id": row.get("id"),
                    "action": row.get("action"),
                }
                plan.history_events.append(event)
                previous = plan.latest_movies.get(key)
                if previous is None or parse_iso(watched_at) > parse_iso(previous.get("watched_at")):
                    plan.latest_movies[key] = event
                continue

            if isinstance(row.get("episode"), dict) and isinstance(row.get("show"), dict):
                episode = row["episode"]
                show = media_stub(row["show"], "show")
                show_key = media_key(show.get("ids", {}), "show")
                season = episode.get("season")
                number = episode.get("number")
                if not show_key or season is None or number is None:
                    plan.unsupported.append({"section": "history", "reason": "episode_without_show_id_or_number", "source_file": filename})
                    continue
                key = f"{show_key}:s{season}:e{number}"
                event = {
                    "type": "episode",
                    "watched_at": watched_at,
                    "show_ids": show.get("ids", {}),
                    "show_title": show.get("title"),
                    "show_year": show.get("year"),
                    "season": int(season),
                    "episode": int(number),
                    "episode_ids": public_ids(episode.get("ids"), "episode"),
                    "episode_title": episode.get("title"),
                    "trakt_history_id": row.get("id"),
                    "action": row.get("action"),
                }
                plan.history_events.append(event)
                previous = plan.latest_episodes.get(key)
                if previous is None or parse_iso(watched_at) > parse_iso(previous.get("watched_at")):
                    plan.latest_episodes[key] = event
                continue

            plan.unsupported.append({"section": "history", "reason": "unknown_history_row", "source_file": filename})

    # Filet de sécurité pour les films vus absents de l'historique événementiel.
    for filename, rows in source.load_matching(r"watched-movies-\d+\.json"):
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("movie"), dict):
                continue
            movie = media_stub(row["movie"], "movie")
            key = media_key(movie.get("ids", {}), "movie")
            if not key or key in plan.latest_movies:
                continue
            event = {
                "type": "movie",
                "watched_at": row.get("last_watched_at"),
                "ids": movie.get("ids", {}),
                "title": movie.get("title"),
                "year": movie.get("year"),
                "plays_from_summary": row.get("plays"),
                "source": filename,
            }
            plan.latest_movies[key] = event
            plan.warnings.append(f"Film ajouté depuis {filename}, absent de watched-history")


def get_or_create_show_rating(plan: MigrationPlan, show: dict[str, Any]) -> tuple[str, dict[str, Any]] | tuple[None, None]:
    show_data = media_stub(show, "show")
    key = media_key(show_data.get("ids", {}), "show")
    if not key:
        return None, None
    target = plan.show_ratings.setdefault(
        key,
        {
            "ids": show_data.get("ids", {}),
            "title": show_data.get("title"),
            "year": show_data.get("year"),
            "seasons": {},
        },
    )
    return key, target


def parse_ratings(source: TraktZip, plan: MigrationPlan) -> None:
    rows = source.load("ratings-movies.json", [])
    if isinstance(rows, list):
        for row in rows:
            movie = media_stub(row.get("movie"), "movie") if isinstance(row, dict) else {}
            if not media_key(movie.get("ids", {}), "movie"):
                plan.unsupported.append({"section": "ratings", "reason": "movie_rating_without_id"})
                continue
            plan.movie_ratings.append(
                {
                    "ids": movie.get("ids", {}),
                    "rating": row.get("rating"),
                    "rated_at": row.get("rated_at"),
                    "title": movie.get("title"),
                    "year": movie.get("year"),
                }
            )

    rows = source.load("ratings-shows.json", [])
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict):
                continue
            _, target = get_or_create_show_rating(plan, row.get("show") or {})
            if target is None:
                plan.unsupported.append({"section": "ratings", "reason": "show_rating_without_id"})
                continue
            target["rating"] = row.get("rating")
            target["rated_at"] = row.get("rated_at")

    rows = source.load("ratings-seasons.json", [])
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict):
                continue
            _, target = get_or_create_show_rating(plan, row.get("show") or {})
            season = row.get("season") or {}
            number = season.get("number")
            if target is None or number is None:
                plan.unsupported.append({"section": "ratings", "reason": "season_rating_without_show_or_number"})
                continue
            season_target = target["seasons"].setdefault(int(number), {"number": int(number), "episodes": {}})
            season_target["rating"] = row.get("rating")
            season_target["rated_at"] = row.get("rated_at")

    rows = source.load("ratings-episodes.json", [])
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict):
                continue
            _, target = get_or_create_show_rating(plan, row.get("show") or {})
            episode = row.get("episode") or {}
            season_number = episode.get("season")
            episode_number = episode.get("number")
            if target is None or season_number is None or episode_number is None:
                plan.unsupported.append({"section": "ratings", "reason": "episode_rating_without_show_or_number"})
                continue
            season_target = target["seasons"].setdefault(int(season_number), {"number": int(season_number), "episodes": {}})
            season_target["episodes"][int(episode_number)] = {
                "number": int(episode_number),
                "rating": row.get("rating"),
                "rated_at": row.get("rated_at"),
            }


def parse_watchlist(source: TraktZip, plan: MigrationPlan) -> None:
    rows = source.load("lists-watchlist.json", [])
    if not isinstance(rows, list):
        return
    for row in rows:
        if not isinstance(row, dict):
            continue
        if isinstance(row.get("movie"), dict):
            movie = media_stub(row["movie"], "movie")
            if media_key(movie.get("ids", {}), "movie"):
                plan.watchlist_movies.append({"ids": movie["ids"], "title": movie.get("title"), "year": movie.get("year"), "listed_at": row.get("listed_at")})
            continue
        if isinstance(row.get("show"), dict):
            show = media_stub(row["show"], "show")
            if media_key(show.get("ids", {}), "show"):
                plan.watchlist_shows.append({"ids": show["ids"], "title": show.get("title"), "year": show.get("year"), "listed_at": row.get("listed_at")})
            continue
        if isinstance(row.get("episode"), dict) and isinstance(row.get("show"), dict):
            # MDBList Watchlist est film/série : conversion en série parente.
            show = media_stub(row["show"], "show")
            if media_key(show.get("ids", {}), "show"):
                plan.watchlist_shows.append({"ids": show["ids"], "title": show.get("title"), "year": show.get("year"), "listed_at": row.get("listed_at"), "converted_from_episode": True})
                plan.warnings.append("Un épisode de watchlist a été converti en série parente")
            else:
                plan.unsupported.append({"section": "watchlist", "reason": "episode_without_parent_show_id"})
            continue
        plan.unsupported.append({"section": "watchlist", "reason": "unsupported_watchlist_type"})

    plan.watchlist_movies = dedupe_by_media(plan.watchlist_movies, "movie")
    plan.watchlist_shows = dedupe_by_media(plan.watchlist_shows, "show")


def dedupe_by_media(rows: list[dict[str, Any]], media: str) -> list[dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = media_key(row.get("ids", {}), media)
        if not key:
            continue
        if key not in output:
            output[key] = row
        elif parse_iso(row.get("listed_at")) < parse_iso(output[key].get("listed_at")):
            output[key] = row
    return list(output.values())


def parse_collection(source: TraktZip, plan: MigrationPlan) -> None:
    for filename, media, target_name in (
        ("collection-movies.json", "movie", "collection_movies"),
        ("collection-shows.json", "show", "collection_shows"),
    ):
        rows = source.load(filename, [])
        target: list[dict[str, Any]] = getattr(plan, target_name)
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            obj = row.get(media) or row.get(f"{media}s")
            item = media_stub(obj, media)
            if not media_key(item.get("ids", {}), media):
                plan.unsupported.append({"section": "collection", "reason": f"{media}_without_id"})
                continue
            target.append({"ids": item["ids"], "title": item.get("title"), "year": item.get("year"), "collected_at": row.get("collected_at")})


def parse_lists(source: TraktZip, plan: MigrationPlan) -> None:
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

    for filename, rows in source.load_matching(r"lists-list-\d+-.+\.json"):
        match = re.match(r"lists-list-(\d+)-(.+)\.json", filename)
        if not match:
            continue
        list_id, fallback_slug = match.groups()
        meta = metadata_by_id.get(list_id, {})
        name = meta.get("name") or fallback_slug.replace("-", " ").strip().title()
        privacy = str(meta.get("privacy") or "private").lower()
        target: dict[str, Any] = {
            "trakt_list_id": list_id,
            "name": name,
            "description": meta.get("description") or "",
            "privacy": privacy,
            "private": privacy != "public",
            "sort_by": meta.get("sort_by"),
            "sort_how": meta.get("sort_how"),
            "created_at": meta.get("created_at"),
            "updated_at": meta.get("updated_at"),
            "movies": [],
            "shows": [],
            "unsupported": [],
            "source_file": filename,
        }
        if not isinstance(rows, list):
            rows = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            if isinstance(row.get("movie"), dict):
                movie = media_stub(row["movie"], "movie")
                if media_key(movie.get("ids", {}), "movie"):
                    target["movies"].append({"ids": movie["ids"], "title": movie.get("title"), "year": movie.get("year"), "rank": row.get("rank"), "listed_at": row.get("listed_at")})
                else:
                    target["unsupported"].append({"reason": "movie_without_id"})
                continue
            if isinstance(row.get("show"), dict):
                show = media_stub(row["show"], "show")
                if media_key(show.get("ids", {}), "show"):
                    target["shows"].append({"ids": show["ids"], "title": show.get("title"), "year": show.get("year"), "rank": row.get("rank"), "listed_at": row.get("listed_at")})
                else:
                    target["unsupported"].append({"reason": "show_without_id"})
                continue
            target["unsupported"].append({"reason": "static_list_supports_movies_and_shows_only", "type": row.get("type")})
        target["movies"].sort(key=lambda item: item.get("rank") if isinstance(item.get("rank"), int) else 10**12)
        target["shows"].sort(key=lambda item: item.get("rank") if isinstance(item.get("rank"), int) else 10**12)
        plan.personal_lists.append(target)

    missing = sorted(set(metadata_by_id) - {item["trakt_list_id"] for item in plan.personal_lists})
    for list_id in missing:
        meta = metadata_by_id[list_id]
        plan.warnings.append(f"Liste sans fichier d'éléments dans le ZIP : {meta.get('name') or list_id}")


def compact_lists_to_three(plan: MigrationPlan, *, add_warning: bool = True) -> None:
    """Regroupe les listes en Séries, Films familiaux et Autres films.

    Règles :
    - tous les éléments séries vont dans « Séries » ;
    - les films provenant d'une liste dont le nom contient famille/family vont
      dans « Films familiaux » ;
    - tous les autres films vont dans « Autres films » ;
    - les doublons sont fusionnés, avec conservation locale des listes sources.
    """

    groups: dict[str, dict[str, Any]] = {
        "series": {
            "name": "Séries",
            "description": "Regroupement des listes Trakt de séries.",
            "privacy": "private",
            "private": False,
            "movies": [],
            "shows": [],
            "unsupported": [],
            "source_lists": [],
        },
        "family": {
            "name": "Films familiaux",
            "description": "Regroupement de la liste Trakt de films familiaux.",
            "privacy": "private",
            "private": False,
            "movies": [],
            "shows": [],
            "unsupported": [],
            "source_lists": [],
        },
        "other": {
            "name": "Autres films",
            "description": "Regroupement des autres listes Trakt de films.",
            "privacy": "private",
            "private": False,
            "movies": [],
            "shows": [],
            "unsupported": [],
            "source_lists": [],
        },
    }

    def is_family_name(value: str) -> bool:
        normalized = value.casefold()
        return any(token in normalized for token in ("famille", "familial", "familiaux", "family"))

    for user_list in plan.personal_lists:
        source_name = str(user_list.get("name") or "Liste Trakt")
        private = bool(user_list.get("private", True))

        if user_list.get("shows"):
            groups["series"]["source_lists"].append(source_name)
            groups["series"]["private"] = groups["series"]["private"] or private
            for item in user_list.get("shows", []):
                copied = dict(item)
                copied["source_lists"] = sorted(set(copied.get("source_lists", []) + [source_name]))
                groups["series"]["shows"].append(copied)

        if user_list.get("movies"):
            destination = groups["family"] if is_family_name(source_name) else groups["other"]
            destination["source_lists"].append(source_name)
            destination["private"] = destination["private"] or private
            for item in user_list.get("movies", []):
                copied = dict(item)
                copied["source_lists"] = sorted(set(copied.get("source_lists", []) + [source_name]))
                destination["movies"].append(copied)

        for unsupported in user_list.get("unsupported", []):
            groups["other"]["unsupported"].append({**unsupported, "source_list": source_name})

    def merge_media(items: list[dict[str, Any]], media: str) -> list[dict[str, Any]]:
        merged: dict[str, dict[str, Any]] = {}
        for item in items:
            key = media_key(item.get("ids", {}), media)
            if not key:
                continue
            if key not in merged:
                merged[key] = dict(item)
                merged[key]["source_lists"] = list(item.get("source_lists", []))
                continue
            current = merged[key]
            current["source_lists"] = sorted(
                set(current.get("source_lists", []) + item.get("source_lists", []))
            )
            # Conserver le rang le plus petit comme ordre de repli.
            ranks = [value for value in (current.get("rank"), item.get("rank")) if isinstance(value, int)]
            if ranks:
                current["rank"] = min(ranks)
            current["listed_at"] = latest_iso(current.get("listed_at"), item.get("listed_at"))
        return sorted(
            merged.values(),
            key=lambda item: (
                item.get("rank") if isinstance(item.get("rank"), int) else 10**12,
                str(item.get("title") or "").casefold(),
            ),
        )

    compacted: list[dict[str, Any]] = []
    for key in ("series", "family", "other"):
        group = groups[key]
        group["shows"] = merge_media(group["shows"], "show")
        group["movies"] = merge_media(group["movies"], "movie")
        group["source_lists"] = sorted(set(group["source_lists"]))
        group["privacy"] = "private" if group["private"] else "public"
        if group["movies"] or group["shows"]:
            compacted.append(group)

    plan.personal_lists = compacted
    if add_warning:
        plan.warnings.append(
            "Les listes Trakt ont été regroupées selon le profil compact-3 ; "
            "les appartenances d'origine restent dans personal_lists_original_backup.json."
        )


def media_identity_tokens(item: dict[str, Any], media: str) -> set[str]:
    """Retourne tous les identifiants utilisables pour vérifier les recouvrements."""
    ids = item.get("ids", {}) if isinstance(item, dict) else {}
    if not isinstance(ids, dict):
        return set()
    allowed = ("tmdb", "imdb", "trakt", "mdblist", "kitsu")
    if media == "show":
        allowed = allowed + ("tvdb",)
    return {
        f"{media}:{key}:{ids[key]}"
        for key in allowed
        if ids.get(key) not in (None, "", 0, "0")
    }


def merge_media_with_sources(items: list[dict[str, Any]], media: str) -> list[dict[str, Any]]:
    """Dédoublonne tout en conservant les appartenances Trakt d'origine."""
    merged: list[dict[str, Any]] = []
    token_to_index: dict[str, int] = {}

    for item in items:
        tokens = media_identity_tokens(item, media)
        matching = sorted({token_to_index[token] for token in tokens if token in token_to_index})
        if not matching:
            copied = dict(item)
            copied["source_lists"] = sorted(set(copied.get("source_lists", [])))
            index = len(merged)
            merged.append(copied)
            for token in tokens:
                token_to_index[token] = index
            continue

        index = matching[0]
        current = merged[index]
        current["source_lists"] = sorted(
            set(current.get("source_lists", []) + item.get("source_lists", []))
        )
        current["listed_at"] = latest_iso(current.get("listed_at"), item.get("listed_at"))
        for token in tokens | media_identity_tokens(current, media):
            token_to_index[token] = index

    return sorted(merged, key=lambda item: str(item.get("title") or "").casefold())


def apply_exclusive_watchlist_layout(plan: MigrationPlan) -> None:
    """Organisation exclusive demandée : un média n'a qu'un conteneur MDBList.

    Priorités :
    1. toute série -> liste statique « Séries », jamais la Watchlist ;
    2. tout film familial -> liste statique « Films familiaux », jamais la Watchlist ;
    3. films horreur/comédie/gros films -> Watchlist, sans liste statique doublon ;
    4. ancienne Watchlist Trakt -> Watchlist, sauf règles 1 et 2.

    Si un même film appartenait à une liste familiale ET à une liste thématique,
    la catégorie familiale gagne. Les appartenances Trakt restent sauvegardées
    dans personal_lists_original_backup.json.
    """
    original_watchlist_movies = [dict(item) for item in plan.watchlist_movies]
    original_watchlist_shows = [dict(item) for item in plan.watchlist_shows]
    compact_lists_to_three(plan, add_warning=False)

    series_list = next((item for item in plan.personal_lists if item.get("name") == "Séries"), None)
    family_list = next((item for item in plan.personal_lists if item.get("name") == "Films familiaux"), None)
    other_movies_list = next((item for item in plan.personal_lists if item.get("name") == "Autres films"), None)

    if series_list is None and original_watchlist_shows:
        series_list = {
            "name": "Séries",
            "description": "Séries Trakt, y compris celles de l'ancienne Watchlist.",
            "privacy": "private",
            "private": True,
            "movies": [],
            "shows": [],
            "unsupported": [],
            "source_lists": [],
        }

    if series_list is not None:
        copied_watchlist_shows: list[dict[str, Any]] = []
        for item in original_watchlist_shows:
            copied = dict(item)
            copied["source_lists"] = sorted(
                set(copied.get("source_lists", []) + ["Trakt Watchlist"])
            )
            copied_watchlist_shows.append(copied)
        series_list["movies"] = []
        series_list["shows"] = merge_media_with_sources(
            list(series_list.get("shows", [])) + copied_watchlist_shows,
            "show",
        )
        series_list["source_lists"] = sorted(
            set(series_list.get("source_lists", []) + (["Trakt Watchlist"] if original_watchlist_shows else []))
        )

    if family_list is not None:
        family_list["shows"] = []
        family_list["movies"] = merge_media_with_sources(
            list(family_list.get("movies", [])), "movie"
        )

    family_tokens = {
        token
        for item in (family_list.get("movies", []) if family_list else [])
        for token in media_identity_tokens(item, "movie")
    }

    def is_family_movie(item: dict[str, Any]) -> bool:
        return bool(media_identity_tokens(item, "movie") & family_tokens)

    thematic_candidates = list(other_movies_list.get("movies", [])) if other_movies_list else []
    thematic_routed_to_family = sum(1 for item in thematic_candidates if is_family_movie(item))
    thematic_movies = [item for item in thematic_candidates if not is_family_movie(item)]
    original_family_removed = sum(1 for item in original_watchlist_movies if is_family_movie(item))
    original_non_family = [item for item in original_watchlist_movies if not is_family_movie(item)]

    watchlist_additions: list[dict[str, Any]] = []
    for item in thematic_movies:
        copied = {
            "ids": item.get("ids", {}),
            "title": item.get("title"),
            "year": item.get("year"),
            "listed_at": item.get("listed_at"),
            "source_lists": list(item.get("source_lists", [])),
            "added_from_trakt_thematic_lists": True,
        }
        watchlist_additions.append(copied)

    plan.watchlist_movies = merge_media_with_sources(
        original_non_family + watchlist_additions, "movie"
    )
    plan.watchlist_shows = []
    plan.personal_lists = [
        item for item in (series_list, family_list)
        if item is not None and (item.get("movies") or item.get("shows"))
    ]

    watchlist_movie_tokens = {
        token
        for item in plan.watchlist_movies
        for token in media_identity_tokens(item, "movie")
    }
    series_show_tokens = {
        token
        for item in (series_list.get("shows", []) if series_list else [])
        for token in media_identity_tokens(item, "show")
    }
    family_movie_tokens = {
        token
        for item in (family_list.get("movies", []) if family_list else [])
        for token in media_identity_tokens(item, "movie")
    }
    overlap_watchlist_family = watchlist_movie_tokens & family_movie_tokens

    plan.overlap_audit = {
        "policy": "exclusive-containers",
        "watchlist_shows": len(plan.watchlist_shows),
        "watchlist_movies_also_in_family_list": len(overlap_watchlist_family),
        "series_watchlist_duplicates": 0,
        "cross_container_duplicates_total": len(overlap_watchlist_family),
        "thematic_movies_routed_to_family_by_priority": thematic_routed_to_family,
        "original_watchlist_family_movies_removed": original_family_removed,
        "series_unique_identity_tokens": len(series_show_tokens),
        "status": "PASS" if not overlap_watchlist_family and not plan.watchlist_shows else "FAIL",
    }
    if plan.overlap_audit["status"] != "PASS":
        raise RuntimeError("L'audit d'exclusivité a détecté un doublon entre Watchlist et listes statiques")

    plan.warnings.append(
        "Profil exclusive-watchlist appliqué : aucune série en Watchlist ; "
        "aucun film familial en Watchlist ; films thématiques uniquement en Watchlist."
    )
    if thematic_routed_to_family:
        plan.warnings.append(
            f"Priorité famille : {thematic_routed_to_family} film(s) présent(s) aussi dans une liste "
            "thématique ont été conservés uniquement dans Films familiaux."
        )
    if original_family_removed:
        plan.warnings.append(
            f"{original_family_removed} film(s) familial(aux) de l'ancienne Watchlist Trakt ont été "
            "retirés de la Watchlist MDBList et conservés uniquement dans Films familiaux."
        )


# Ancien nom conservé comme alias sûr : il applique désormais la politique
# exclusive, et non l'ancienne politique qui créait des doublons de conteneur.
def apply_hybrid_watchlist_layout(plan: MigrationPlan) -> None:
    apply_exclusive_watchlist_layout(plan)


def parse_liked_lists(source: TraktZip, plan: MigrationPlan) -> None:
    rows = source.load("likes-lists.json", [])
    if not isinstance(rows, list):
        return
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("list"), dict):
            continue
        item = row["list"]
        plan.liked_lists.append(
            {
                "name": item.get("name"),
                "share_link": item.get("share_link"),
                "privacy": item.get("privacy"),
                "item_count": item.get("item_count"),
                "liked_at": row.get("liked_at"),
                "owner": (item.get("user") or {}).get("username"),
            }
        )


def parse_playback(source: TraktZip, plan: MigrationPlan) -> None:
    rows = source.load("watched-playback.json", [])
    if not isinstance(rows, list):
        return
    for row in rows:
        if not isinstance(row, dict):
            continue
        progress = row.get("progress")
        if isinstance(row.get("movie"), dict):
            movie = media_stub(row["movie"], "movie")
            if media_key(movie.get("ids", {}), "movie"):
                plan.playback.append({"type": "movie", "ids": movie["ids"], "progress": progress})
            continue
        if isinstance(row.get("episode"), dict) and isinstance(row.get("show"), dict):
            show = media_stub(row["show"], "show")
            episode = row["episode"]
            if media_key(show.get("ids", {}), "show") and episode.get("season") is not None and episode.get("number") is not None:
                plan.playback.append({"type": "episode", "show_ids": show["ids"], "season": int(episode["season"]), "episode": int(episode["number"]), "progress": progress})
            continue
        plan.unsupported.append({"section": "playback", "reason": "unsupported_playback_row"})


# ---------------------------------------------------------------------------
# Sorties locales
# ---------------------------------------------------------------------------


def write_local_backups(plan: MigrationPlan, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_dump(output_dir / "migration_summary.json", plan.summary())
    json_dump(output_dir / "full_history_all_events.json", plan.history_events)

    occurrences: Counter[str] = Counter()
    for event in plan.history_events:
        if event["type"] == "movie":
            key = media_key(event.get("ids", {}), "movie")
        else:
            base = media_key(event.get("show_ids", {}), "show")
            key = f"{base}:s{event.get('season')}:e{event.get('episode')}"
        if key:
            occurrences[key] += 1
    rewatch_keys = {key for key, count in occurrences.items() if count > 1}
    rewatches: list[dict[str, Any]] = []
    for event in plan.history_events:
        if event["type"] == "movie":
            key = media_key(event.get("ids", {}), "movie")
        else:
            base = media_key(event.get("show_ids", {}), "show")
            key = f"{base}:s{event.get('season')}:e{event.get('episode')}"
        if key in rewatch_keys:
            rewatches.append(event)
    json_dump(output_dir / "rewatches_all_dates.json", rewatches)
    json_dump(output_dir / "unsupported_items.json", plan.unsupported)
    json_dump(output_dir / "personal_lists_backup.json", plan.personal_lists)
    json_dump(output_dir / "playback_backup.json", plan.playback)

    with (output_dir / "liked_lists_links.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("name", "share_link", "owner", "privacy", "item_count", "liked_at"))
        writer.writeheader()
        for item in plan.liked_lists:
            writer.writerow(item)


# ---------------------------------------------------------------------------
# Client API MDBList
# ---------------------------------------------------------------------------


class ApiError(RuntimeError):
    def __init__(self, status: int, message: str, body: Any = None):
        super().__init__(f"HTTP {status}: {message}")
        self.status = status
        self.body = body


class MDBListClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.request_count = 0
        self.rate_limit_remaining: int | None = None

    def request(self, method: str, path: str, payload: Any = None, query: dict[str, Any] | None = None) -> Any:
        query = dict(query or {})
        query["apikey"] = self.api_key
        url = f"{API_BASE}{path}?{urllib.parse.urlencode(query)}"
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
        if data is not None:
            headers["Content-Type"] = "application/json"

        for attempt in range(MAX_RETRIES):
            request = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
            try:
                with urllib.request.urlopen(request, timeout=45) as response:
                    self.request_count += 1
                    remaining = response.headers.get("X-RateLimit-Remaining") or response.headers.get("X-Rate-Limit-Remaining")
                    if remaining and str(remaining).isdigit():
                        self.rate_limit_remaining = int(remaining)
                    raw = response.read()
                    if not raw:
                        return {}
                    return json.loads(raw.decode("utf-8"))
            except urllib.error.HTTPError as exc:
                self.request_count += 1
                raw = exc.read().decode("utf-8", errors="replace")
                try:
                    body = json.loads(raw)
                except Exception:
                    body = raw[:1000]
                if exc.code == 429 or 500 <= exc.code <= 504:
                    if attempt + 1 < MAX_RETRIES:
                        retry_after = exc.headers.get("Retry-After")
                        delay = int(retry_after) if retry_after and retry_after.isdigit() else min(2**attempt, 30)
                        print(f"  Réponse {exc.code}, nouvel essai dans {delay}s…", file=sys.stderr)
                        time.sleep(delay)
                        continue
                raise ApiError(exc.code, str(exc.reason), body) from None
            except urllib.error.URLError as exc:
                if attempt + 1 < MAX_RETRIES:
                    delay = min(2**attempt, 30)
                    print(f"  Erreur réseau, nouvel essai dans {delay}s…", file=sys.stderr)
                    time.sleep(delay)
                    continue
                raise RuntimeError(f"Erreur réseau : {exc.reason}") from None
        raise RuntimeError("Nombre maximal de tentatives atteint")

    def get(self, path: str, query: dict[str, Any] | None = None) -> Any:
        return self.request("GET", path, query=query)

    def post(self, path: str, payload: Any) -> Any:
        return self.request("POST", path, payload=payload)


# ---------------------------------------------------------------------------
# Conversion des payloads MDBList
# ---------------------------------------------------------------------------


def movie_sync_item(item: dict[str, Any], date_field: str | None = None) -> dict[str, Any]:
    output: dict[str, Any] = {"ids": item.get("ids", {})}
    if item.get("title") is not None:
        output["title"] = item.get("title")
    if item.get("year") is not None:
        output["year"] = item.get("year")
    if date_field and item.get(date_field):
        output[date_field] = item.get(date_field)
    return output


def build_watched_show_payloads(plan: MigrationPlan) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for item in plan.latest_episodes.values():
        ids = item.get("show_ids", {})
        key = media_key(ids, "show")
        if not key:
            continue
        show = grouped.setdefault(
            key,
            {
                "ids": ids,
                "title": item.get("show_title"),
                "year": item.get("show_year"),
                "seasons": defaultdict(list),
            },
        )
        show["seasons"][int(item["season"])].append({"number": int(item["episode"]), "watched_at": item.get("watched_at")})

    payloads: list[dict[str, Any]] = []
    for show in grouped.values():
        payloads.append(
            {
                "ids": show["ids"],
                "title": show.get("title"),
                "year": show.get("year"),
                "seasons": [
                    {"number": season, "episodes": sorted(episodes, key=lambda value: value["number"])}
                    for season, episodes in sorted(show["seasons"].items())
                ],
            }
        )
    return payloads


def build_rating_show_payloads(plan: MigrationPlan) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for show in plan.show_ratings.values():
        output: dict[str, Any] = {"ids": show.get("ids", {})}
        if show.get("title") is not None:
            output["title"] = show.get("title")
        if show.get("year") is not None:
            output["year"] = show.get("year")
        if show.get("rating") is not None:
            output["rating"] = show.get("rating")
            output["rated_at"] = show.get("rated_at")
        seasons: list[dict[str, Any]] = []
        for season_number, season in sorted(show.get("seasons", {}).items()):
            season_out: dict[str, Any] = {"number": int(season_number)}
            if season.get("rating") is not None:
                season_out["rating"] = season.get("rating")
                season_out["rated_at"] = season.get("rated_at")
            episodes = list(season.get("episodes", {}).values())
            if episodes:
                season_out["episodes"] = sorted(episodes, key=lambda value: value["number"])
            seasons.append(season_out)
        if seasons:
            output["seasons"] = seasons
        result.append(output)
    return result


def list_api_items(items: list[dict[str, Any]], media: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for item in items:
        ids = item.get("ids", {})
        output: dict[str, Any] = {}
        for key in ("tmdb", "imdb"):
            if ids.get(key) not in (None, ""):
                output[key] = ids[key]
        # Les endpoints Watchlist/Listes documentent TMDb et IMDb. Les IDs
        # Trakt seuls ne sont pas envoyés ici afin d'éviter un rejet du payload.
        if output:
            result.append(output)
    return result


# ---------------------------------------------------------------------------
# Application du plan
# ---------------------------------------------------------------------------


def preflight(client: MDBListClient, plan: MigrationPlan, sections: set[str]) -> dict[str, Any]:
    user = client.get("/user")
    lists = client.get("/lists/user", {"unified": "false"}) if "lists" in sections else []
    if not isinstance(lists, list):
        lists = []
    static_lists = [item for item in lists if isinstance(item, dict) and (item.get("type") == "static" or item.get("dynamic") is False)]
    existing_names = {str(item.get("name") or "").casefold() for item in static_lists}
    new_lists = [item for item in plan.personal_lists if str(item.get("name") or "").casefold() not in existing_names]
    list_limit = ((user.get("limits") or {}).get("lists") if isinstance(user, dict) else None)
    if "lists" in sections and isinstance(list_limit, int) and len(static_lists) + len(new_lists) > list_limit:
        raise RuntimeError(
            f"Limite de listes MDBList dépassée : {len(static_lists)} existante(s) + "
            f"{len(new_lists)} à créer > limite {list_limit}. "
            "Passez temporairement au forfait MDBList Basic ou excluez la section lists."
        )
    return {"user": user, "existing_lists": lists, "static_lists": static_lists, "new_lists": len(new_lists)}


def pagination_counts(response: Any) -> dict[str, int]:
    """Extrait uniquement des compteurs non sensibles d'une réponse paginée."""
    if not isinstance(response, dict):
        return {}
    pagination = response.get("pagination")
    if not isinstance(pagination, dict):
        return {}
    counts: dict[str, int] = {}
    for key, value in pagination.items():
        if key.startswith("total_") and isinstance(value, int):
            counts[key] = value
    return counts


def api_readonly_check(
    client: MDBListClient,
    plan: MigrationPlan,
    sections: set[str],
    output_dir: Path,
) -> dict[str, Any]:
    """Préflight distant : exclusivement des GET, aucune modification."""
    report: dict[str, Any] = {
        "checked_at": iso_now(),
        "version": VERSION,
        "archive_sha256": plan.archive_sha256,
        "sections": sorted(sections),
        "read_only": True,
        "checks": {},
        "errors": [],
    }

    def get_safely(name: str, path: str, query: dict[str, Any] | None = None) -> Any:
        try:
            return client.get(path, query)
        except Exception as exc:
            body = exc.body if isinstance(exc, ApiError) else None
            report["errors"].append({"check": name, "error": str(exc), "body": body})
            return None

    user = get_safely("user", "/user")
    lists = get_safely("lists", "/lists/user", {"unified": "false"}) if "lists" in sections else []
    watched = get_safely("watched", "/sync/watched", {"limit": 1, "offset": 0}) if "watched" in sections else None
    ratings = get_safely("ratings", "/sync/ratings", {"limit": 1, "offset": 0}) if "ratings" in sections else None
    watchlist = get_safely("watchlist", "/watchlist/items", {"limit": 1, "page": 1}) if "watchlist" in sections else None
    collection = get_safely("collection", "/sync/collection", {"limit": 1, "offset": 0}) if "collection" in sections else None

    if not isinstance(lists, list):
        lists = []
    static_lists = [
        item for item in lists
        if isinstance(item, dict) and (item.get("type") == "static" or item.get("dynamic") is False)
    ]
    dynamic_lists = [
        item for item in lists
        if isinstance(item, dict) and (item.get("type") == "dynamic" or item.get("dynamic") is True)
    ]
    existing_names = {str(item.get("name") or "").casefold() for item in static_lists}
    new_lists = [
        item for item in plan.personal_lists
        if str(item.get("name") or "").casefold() not in existing_names
    ]
    list_limit = ((user.get("limits") or {}).get("lists") if isinstance(user, dict) else None)

    report["checks"]["account"] = {
        "plan": user.get("plan") if isinstance(user, dict) else None,
        "is_supporter": user.get("is_supporter") if isinstance(user, dict) else None,
        "limits": user.get("limits") if isinstance(user, dict) else None,
        "rate_limit": user.get("rate_limit") if isinstance(user, dict) else None,
        "rate_limit_remaining": user.get("rate_limit_remaining") if isinstance(user, dict) else None,
    }
    report["checks"]["lists"] = {
        "existing_static": len(static_lists),
        "existing_dynamic": len(dynamic_lists),
        "existing_other": max(len(lists) - len(static_lists) - len(dynamic_lists), 0),
        "new_static_needed": len(new_lists),
        "reported_list_limit": list_limit,
        "all_personal_lists_fit": (
            len(static_lists) + len(new_lists) <= list_limit
            if isinstance(list_limit, int)
            else None
        ),
    }
    report["checks"]["existing_watched"] = pagination_counts(watched)
    report["checks"]["existing_ratings"] = pagination_counts(ratings)
    report["checks"]["existing_watchlist"] = pagination_counts(watchlist)
    report["checks"]["existing_collection"] = pagination_counts(collection)
    report["request_count"] = client.request_count
    report["rate_limit_remaining_after"] = client.rate_limit_remaining
    json_dump(output_dir / "api_preflight.json", report)
    return report


def apply_plan(client: MDBListClient, plan: MigrationPlan, sections: set[str], output_dir: Path) -> dict[str, Any]:
    report: dict[str, Any] = {
        "started_at": iso_now(),
        "version": VERSION,
        "archive_sha256": plan.archive_sha256,
        "sections": sorted(sections),
        "responses": defaultdict(list),
        "errors": [],
    }
    state = preflight(client, plan, sections)
    report["preflight"] = {
        "username": (state["user"] or {}).get("username"),
        "plan": (state["user"] or {}).get("plan"),
        "limits": (state["user"] or {}).get("limits"),
        "rate_limit_remaining": (state["user"] or {}).get("rate_limit_remaining"),
        "existing_static_lists": len(state["static_lists"]),
        "new_static_lists": state["new_lists"],
    }

    if "watched" in sections:
        print("Import de l'historique vu…")
        movies = [movie_sync_item(item, "watched_at") for item in plan.latest_movies.values()]
        for batch in chunks(movies, 200):
            run_api_step(report, "watched_movies", lambda batch=batch: client.post("/sync/watched", {"movies": batch}))
        shows = build_watched_show_payloads(plan)
        # Petits lots : certaines séries peuvent contenir des centaines
        # d'épisodes et produire un payload volumineux.
        for batch in chunks(shows, 5):
            run_api_step(report, "watched_episodes", lambda batch=batch: client.post("/sync/watched", {"shows": batch}))

    if "ratings" in sections:
        print("Import des notes…")
        movies = []
        for item in plan.movie_ratings:
            output = movie_sync_item(item)
            output["rating"] = item.get("rating")
            output["rated_at"] = item.get("rated_at")
            movies.append(output)
        for batch in chunks(movies, 200):
            run_api_step(report, "rating_movies", lambda batch=batch: client.post("/sync/ratings", {"movies": batch}))
        shows = build_rating_show_payloads(plan)
        for batch in chunks(shows, 25):
            run_api_step(report, "rating_shows", lambda batch=batch: client.post("/sync/ratings", {"shows": batch}))

    if "watchlist" in sections:
        print("Import de la watchlist…")
        movies = list_api_items(plan.watchlist_movies, "movie")
        shows = list_api_items(plan.watchlist_shows, "show")
        for movie_batch, show_batch in zip_longest_chunks(movies, shows, 250):
            payload: dict[str, Any] = {}
            if movie_batch:
                payload["movies"] = movie_batch
            if show_batch:
                payload["shows"] = show_batch
            if payload:
                run_api_step(report, "watchlist", lambda payload=payload: client.post("/watchlist/items/add", payload))

    if "collection" in sections and (plan.collection_movies or plan.collection_shows):
        print("Import de la collection…")
        movies = [movie_sync_item(item, "collected_at") for item in plan.collection_movies]
        shows = [movie_sync_item(item, "collected_at") for item in plan.collection_shows]
        for movie_batch, show_batch in zip_longest_chunks(movies, shows, 100):
            payload = {}
            if movie_batch:
                payload["movies"] = movie_batch
            if show_batch:
                payload["shows"] = show_batch
            if payload:
                run_api_step(report, "collection", lambda payload=payload: client.post("/sync/collection", payload))

    if "lists" in sections:
        print("Import des listes statiques…")
        existing_by_name = {
            str(item.get("name") or "").casefold(): item
            for item in state["static_lists"]
            if isinstance(item, dict)
        }
        for user_list in plan.personal_lists:
            name = str(user_list.get("name") or "Liste Trakt")
            existing = existing_by_name.get(name.casefold())
            if existing:
                list_id = existing.get("id")
                report["responses"]["lists_reused"].append({"name": name, "id": list_id})
            else:
                created = run_api_step(
                    report,
                    "lists_created",
                    lambda name=name, user_list=user_list: client.post("/lists/user/add", {"name": name, "private": bool(user_list.get("private", True))}),
                    return_response=True,
                )
                if not isinstance(created, dict) or not created.get("id"):
                    report["errors"].append({"section": "lists", "name": name, "error": "list_creation_failed"})
                    continue
                list_id = created["id"]
                existing_by_name[name.casefold()] = {"id": list_id, "name": name, "type": "static"}

            movies = list_api_items(user_list.get("movies", []), "movie")
            shows = list_api_items(user_list.get("shows", []), "show")
            for movie_batch, show_batch in zip_longest_chunks(movies, shows, 250):
                payload = {}
                if movie_batch:
                    payload["movies"] = movie_batch
                if show_batch:
                    payload["shows"] = show_batch
                if payload:
                    run_api_step(
                        report,
                        "list_items",
                        lambda list_id=list_id, payload=payload: client.post(f"/lists/{list_id}/items/add", payload),
                        context={"name": name, "list_id": list_id},
                    )

    # Le manifeste indique actuellement 0 session ; le code reste prévu pour un futur export.
    if plan.playback:
        print("Import des points de reprise…")
        for item in plan.playback:
            if item.get("type") == "movie":
                payload = {"movie": {"ids": item.get("ids", {})}, "progress": item.get("progress")}
            else:
                payload = {
                    "show": {
                        "ids": item.get("show_ids", {}),
                        "season": {"number": item.get("season"), "episode": {"number": item.get("episode")}},
                    },
                    "progress": item.get("progress"),
                }
            run_api_step(report, "playback", lambda payload=payload: client.post("/scrobble/pause", payload))

    report["request_count"] = client.request_count
    report["rate_limit_remaining"] = client.rate_limit_remaining
    report["finished_at"] = iso_now()
    report["responses"] = dict(report["responses"])
    json_dump(output_dir / "apply_report.json", report)
    return report


def zip_longest_chunks(first: list[Any], second: list[Any], size: int) -> Iterator[tuple[list[Any], list[Any]]]:
    first_batches = list(chunks(first, size))
    second_batches = list(chunks(second, size))
    total = max(len(first_batches), len(second_batches))
    for index in range(total):
        yield (
            first_batches[index] if index < len(first_batches) else [],
            second_batches[index] if index < len(second_batches) else [],
        )


def run_api_step(
    report: dict[str, Any],
    section: str,
    action,
    context: dict[str, Any] | None = None,
    return_response: bool = False,
) -> Any:
    try:
        response = action()
        record = {"context": context or {}, "response": response}
        report["responses"][section].append(record)
        return response if return_response else True
    except Exception as exc:
        body = exc.body if isinstance(exc, ApiError) else None
        error = {"section": section, "context": context or {}, "error": str(exc), "body": body}
        report["errors"].append(error)
        print(f"  ERREUR [{section}] : {exc}", file=sys.stderr)
        return None if return_response else False


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def print_summary(summary: dict[str, Any]) -> None:
    print("\n=== PLAN DE MIGRATION ===")
    labels = (
        ("Événements d'historique Trakt", "history_events_total"),
        ("Films uniques vus", "history_unique_movies"),
        ("Épisodes uniques vus", "history_unique_episodes"),
        ("Événements de rewatch supplémentaires", "history_extra_rewatch_events"),
        ("Notes de films", "ratings_movies"),
        ("Séries avec notes série/saison/épisode", "ratings_shows_with_show_or_episode_ratings"),
        ("Films en watchlist", "watchlist_movies"),
        ("Séries en watchlist", "watchlist_shows"),
        ("Films en collection", "collection_movies"),
        ("Séries en collection", "collection_shows"),
        ("Listes personnelles", "personal_lists"),
        ("Éléments dans les listes", "personal_list_items"),
        ("Sessions de reprise", "playback_sessions"),
        ("Listes aimées (métadonnées/liens)", "liked_lists_metadata"),
        ("Éléments non importables", "unsupported_items"),
    )
    width = max(len(label) for label, _ in labels)
    print(f"{'Organisation':<{width}} : {summary.get('list_layout', 'original')}")
    for label, key in labels:
        print(f"{label:<{width}} : {summary.get(key, 0)}")
    for item in summary.get("static_lists", []):
        print(
            f"  - {item.get('name')} : {item.get('movies', 0)} film(s), "
            f"{item.get('shows', 0)} série(s)"
        )
    audit = summary.get("overlap_audit") or {}
    if audit:
        print(
            f"{'Audit absence de doublons':<{width}} : "
            f"{audit.get('status')} ({audit.get('cross_container_duplicates_total', 0)})"
        )
    if summary.get("warnings"):
        print(f"{'Avertissements':<{width}} : {len(summary['warnings'])}")


def parse_sections(value: str) -> set[str]:
    sections = {item.strip().lower() for item in value.split(",") if item.strip()}
    unknown = sections - VALID_SECTIONS
    if unknown:
        raise argparse.ArgumentTypeError(f"Sections inconnues : {', '.join(sorted(unknown))}")
    return sections


def main() -> int:
    parser = argparse.ArgumentParser(description="Migre localement un ZIP Trakt vers MDBList (simulation par défaut).")
    parser.add_argument("zip_path", type=Path, help="Export ZIP Trakt original")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="Écrit réellement dans MDBList (sinon dry-run local)")
    mode.add_argument(
        "--check-api",
        action="store_true",
        help="Teste la clé, les quotas et l'état MDBList avec des GET uniquement ; aucune écriture",
    )
    parser.add_argument(
        "--sections",
        type=parse_sections,
        default=set(DEFAULT_SECTIONS),
        help="Sections séparées par virgules : watched,ratings,watchlist,collection,lists",
    )
    parser.add_argument(
        "--list-layout",
        choices=("original", "compact-3", "exclusive-watchlist", "hybrid-watchlist"),
        default="original",
        help=(
            "original = conserver les listes Trakt ; compact-3 = regrouper en 3 listes ; "
            "exclusive-watchlist = séries uniquement dans Séries, films familiaux uniquement "
            "dans Films familiaux, autres films uniquement en Watchlist ; "
            "hybrid-watchlist = ancien alias de exclusive-watchlist"
        ),
    )
    parser.add_argument("--output-dir", type=Path, default=Path("trakt_mdblist_migration"), help="Dossier des rapports locaux")
    args = parser.parse_args()

    if not args.zip_path.is_file() or not zipfile.is_zipfile(args.zip_path):
        print("Erreur : export ZIP Trakt introuvable ou invalide.", file=sys.stderr)
        return 2

    print("Lecture locale du ZIP Trakt…")
    try:
        plan = build_plan(args.zip_path)
        plan.list_layout = (
            "exclusive-watchlist"
            if args.list_layout == "hybrid-watchlist"
            else args.list_layout
        )
        if args.list_layout in {"compact-3", "exclusive-watchlist", "hybrid-watchlist"}:
            # Sauvegarde des cinq listes et de leurs appartenances avant fusion.
            json_dump(
                args.output_dir / "personal_lists_original_backup.json",
                plan.personal_lists,
            )
            if args.list_layout == "compact-3":
                compact_lists_to_three(plan)
            else:
                apply_exclusive_watchlist_layout(plan)
        write_local_backups(plan, args.output_dir)
    except Exception as exc:
        print(f"Erreur pendant l'analyse : {type(exc).__name__}: {exc}", file=sys.stderr)
        return 3

    summary = plan.summary()
    print_summary(summary)
    print(f"\nSauvegardes et rapports : {args.output_dir.resolve()}")

    if not args.apply and not args.check_api:
        print("\nDRY-RUN terminé : aucun appel réseau, aucune modification MDBList.")
        print("Étape suivante recommandée : relancer avec --check-api (GET uniquement).")
        return 0

    key = os.environ.get("MDBLIST_API_KEY", "").strip()
    if not key:
        key = getpass.getpass("Clé API MDBList (saisie masquée) : ").strip()
    if not key:
        print("Erreur : clé API absente.", file=sys.stderr)
        return 4

    client = MDBListClient(key)

    if args.check_api:
        print("\nVérification MDBList en lecture seule (aucune écriture)…")
        report = api_readonly_check(client, plan, args.sections, args.output_dir)
        print(f"Requêtes GET : {report.get('request_count')}")
        print(f"Erreurs : {len(report.get('errors', []))}")
        print(f"Rapport : {(args.output_dir / 'api_preflight.json').resolve()}")
        print("Aucune donnée MDBList n'a été modifiée.")
        return 0 if not report.get("errors") else 7

    print("\nÉCRITURES PRÉVUES : " + ", ".join(sorted(args.sections)))
    print("Aucune donnée ne sera supprimée, mais les états existants pourront être mis à jour.")
    confirmation = input("Tapez exactement IMPORTER pour continuer : ").strip()
    if confirmation != "IMPORTER":
        print("Annulé. Aucune modification MDBList.")
        return 0

    try:
        report = apply_plan(client, plan, args.sections, args.output_dir)
    except Exception as exc:
        print(f"Erreur avant/pendant l'import : {type(exc).__name__}: {exc}", file=sys.stderr)
        return 5

    print("\n=== IMPORT TERMINÉ ===")
    print(f"Requêtes API : {report.get('request_count')}")
    print(f"Erreurs : {len(report.get('errors', []))}")
    print(f"Rapport : {(args.output_dir / 'apply_report.json').resolve()}")
    if report.get("errors"):
        print("Certaines opérations ont échoué : ne relancez pas aveuglément ; transmettez apply_report.json après vérification.")
        return 6
    print("Vérifiez maintenant les compteurs dans MDBList/Reeel avant toute suppression côté Trakt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
