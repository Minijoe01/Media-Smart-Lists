"""Audit local des listes Media Smart Lists.

Architecture inspirée du modèle Builder → Filters → Preview de Kometa, mais
appliquée au NormalizedDataset et sans dépendance à Plex ni appel réseau.
"""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

from normalized_model import media_type


AUDIT_ENGINE_VERSION = 1

ISSUE_OPTIONS = [
    "Déjà vus",
    "Présents dans plusieurs conteneurs",
    "Ajoutés depuis plus de 6 mois",
    "Ajoutés depuis plus d’un an",
    "Ajoutés depuis plus de deux ans",
    "Note communauté inférieure à 5/10",
]

SORT_OPTIONS = [
    "Priorité de nettoyage",
    "Ajout le plus ancien",
    "Ajout le plus récent",
    "Note la plus faible",
    "Plus grand nombre de conteneurs",
    "Titre A → Z",
    "Titre Z → A",
]

ADDITION_PERIOD_OPTIONS = [
    "Toutes les dates",
    "7 derniers jours",
    "30 derniers jours",
    "90 derniers jours",
    "Cette année",
    "Date inconnue",
]

ADDITION_SORT_OPTIONS = [
    "Ajouts les plus récents",
    "Ajouts les plus anciens",
    "Conteneur",
    "Titre A → Z",
]


def source_display_label(source: dict[str, Any]) -> str:
    """Libellé explicite conforme aux types de listes documentés par MDBList."""
    if source.get("kind") == "watchlist":
        return "Watchlist MDBList"
    if source.get("kind") == "aggregate":
        return str(source.get("label") or source.get("name") or "Vue combinée")
    name = str(source.get("name") or "Sans nom")
    prefix = {
        "static": "Liste statique",
        "dynamic": "Liste dynamique",
        "ai": "Liste IA",
        "feed": "Liste flux",
        "other": "Liste",
    }.get(str(source.get("type") or "").lower(), "Liste")
    return f"{prefix} : {name}"


def _nested_media(row: dict[str, Any], kind: str | None = None) -> dict[str, Any]:
    if kind == "movie" and isinstance(row.get("movie"), dict):
        return row["movie"]
    if kind == "show" and isinstance(row.get("show"), dict):
        return row["show"]
    for key in ("movie", "show"):
        if isinstance(row.get(key), dict):
            return row[key]
    return row


def _kind(item: dict[str, Any], fallback: str | None = None) -> str:
    value = media_type(item)
    if value in {"movie", "show"}:
        return value
    return fallback or "unknown"


def _identity(item: dict[str, Any], kind: str) -> str:
    media = _nested_media(item, kind)
    ids = media.get("ids") if isinstance(media.get("ids"), dict) else {}
    for provider in ("tmdb", "imdb", "tvdb", "trakt", "mdblist"):
        value = ids.get(provider)
        if value not in (None, "", 0, "0"):
            return f"{kind}:{provider}:{value}"
    value = media.get("id") or media.get("imdb_id")
    if value not in (None, "", 0, "0"):
        return f"{kind}:id:{value}"
    title = media.get("title") or media.get("name") or "?"
    year = media.get("release_year") or media.get("year") or "?"
    return f"{kind}:title:{str(title).casefold()}:{year}"


def _title(item: dict[str, Any], kind: str) -> str:
    media = _nested_media(item, kind)
    return str(media.get("title") or media.get("name") or "Titre inconnu")


def _year(item: dict[str, Any], kind: str) -> int | None:
    media = _nested_media(item, kind)
    value = media.get("release_year") or media.get("year")
    try:
        return int(value) if value else None
    except (TypeError, ValueError):
        return None


def _community_note(item: dict[str, Any], kind: str) -> float | None:
    media = _nested_media(item, kind)
    for value in (media.get("score"), media.get("score_average"), item.get("score"), item.get("score_average")):
        try:
            number = float(value)
            if number > 0:
                return max(0.0, min(number / 10, 10.0))
        except (TypeError, ValueError):
            pass
    ratings = media.get("ratings") or item.get("ratings") or []
    indexed = {
        str(value.get("source") or "").lower(): value
        for value in ratings if isinstance(value, dict)
    }
    for source in ("imdb", "tmdb", "trakt", "letterboxd"):
        value = indexed.get(source)
        if not value:
            continue
        raw = value.get("value") if value.get("value") is not None else value.get("rating")
        try:
            number = float(raw)
        except (TypeError, ValueError):
            continue
        if number > 10:
            number /= 10
        return max(0.0, min(number, 10.0))
    return None


def _added_datetime(item: dict[str, Any]) -> datetime | None:
    media = _nested_media(item)
    value = (
        item.get("watchlist_at")
        or item.get("added_at")
        or item.get("added")
        or item.get("created_at")
        or item.get("listed_at")
        or media.get("watchlist_at")
        or media.get("added_at")
        or media.get("added")
        or media.get("listed_at")
    )
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except Exception:
        return None


def _added_days(item: dict[str, Any], now: datetime) -> int | None:
    parsed = _added_datetime(item)
    return max((now - parsed).days, 0) if parsed else None


def auditable_sources(
    dataset: dict[str, Any],
    include_aggregates: bool = False,
) -> list[dict[str, Any]]:
    """Sources auditables, avec agrégats optionnels pour les aperçus combinés.

    Les calculs de doublons appellent cette fonction sans agrégats afin qu'une
    vue combinée ne soit jamais comptée comme un conteneur réel supplémentaire.
    """
    return [
        source for source in dataset.get("sources") or []
        if isinstance(source, dict)
        and (include_aggregates or source.get("kind") != "aggregate")
    ]


def watched_identities(dataset: dict[str, Any]) -> set[str]:
    watched = (dataset.get("sections") or {}).get("watched") or {}
    output = set()
    for section, kind in (("movies", "movie"), ("shows", "show")):
        for row in watched.get(section) or []:
            if isinstance(row, dict):
                output.add(_identity(row, kind))
    return output


def membership_index(dataset: dict[str, Any]) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for source in auditable_sources(dataset):
        source_key = str(source.get("key") or "")
        source_label = source_display_label(source)
        source_type = str(source.get("type") or "unknown")
        writable = source_type in {"native", "static"}
        for section, kind in (("movies", "movie"), ("shows", "show")):
            for item in source.get(section) or []:
                if not isinstance(item, dict):
                    continue
                identity = _identity(item, kind)
                record = output.setdefault(
                    identity,
                    {
                        "key": identity,
                        "type": "Film" if kind == "movie" else "Série",
                        "kind": kind,
                        "title": _title(item, kind),
                        "year": _year(item, kind),
                        "item": item,
                        "memberships": [],
                    },
                )
                if not any(member["key"] == source_key for member in record["memberships"]):
                    record["memberships"].append(
                        {
                            "key": source_key,
                            "label": source_label,
                            "type": source_type,
                            "writable": writable,
                        }
                    )
    return output


def duplicate_rows(dataset: dict[str, Any]) -> list[dict[str, Any]]:
    duplicates = []
    for record in membership_index(dataset).values():
        memberships = record["memberships"]
        if len(memberships) < 2:
            continue
        writable_count = sum(1 for member in memberships if member["writable"])
        dynamic_count = sum(1 for member in memberships if member["type"] == "dynamic")
        if writable_count >= 2:
            overlap_type = "Doublon entre conteneurs modifiables"
        elif dynamic_count:
            overlap_type = "Chevauchement avec liste dynamique"
        else:
            overlap_type = "Chevauchement informatif"
        duplicates.append(
            {
                **record,
                "container_count": len(memberships),
                "writable_count": writable_count,
                "dynamic_count": dynamic_count,
                "overlap_type": overlap_type,
                "containers": [member["label"] for member in memberships],
            }
        )
    return sorted(duplicates, key=lambda row: (-row["container_count"], row["title"].casefold()))


def audit_source(
    dataset: dict[str, Any],
    source_key: str,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    now = now or datetime.now(timezone.utc)
    source = next(
        (
            value for value in auditable_sources(dataset, include_aggregates=True)
            if value.get("key") == source_key
        ),
        None,
    )
    if not source:
        return []
    watched = watched_identities(dataset)
    memberships = membership_index(dataset)
    rows = []
    for section, kind in (("movies", "movie"), ("shows", "show")):
        for item in source.get(section) or []:
            if not isinstance(item, dict):
                continue
            identity = _identity(item, kind)
            member_record = memberships.get(identity) or {"memberships": []}
            containers = [member["label"] for member in member_record["memberships"]]
            added_at = _added_datetime(item)
            days = _added_days(item, now)
            note = _community_note(item, kind)
            is_watched = identity in watched
            is_duplicate = len(containers) > 1
            issue_keys = []
            issue_labels = []
            if is_watched:
                issue_keys.append("watched")
                issue_labels.append("Déjà vu")
            if is_duplicate:
                issue_keys.append("duplicate")
                issue_labels.append(f"{len(containers)} conteneurs")
            if days is not None and days > 180:
                issue_keys.append("old_180")
                issue_labels.append("Ajout > 6 mois")
            if days is not None and days > 365:
                issue_keys.append("old_365")
                issue_labels.append("Ajout > 1 an")
            if days is not None and days > 730:
                issue_keys.append("old_730")
                issue_labels.append("Ajout > 2 ans")
            if note is not None and note < 5:
                issue_keys.append("low_rating")
                issue_labels.append("Note < 5")
            priority = (
                (30 if is_watched else 0)
                + (20 if is_duplicate else 0)
                + (25 if days is not None and days > 730 else 15 if days is not None and days > 365 else 8 if days is not None and days > 180 else 0)
                + (12 if note is not None and note < 5 else 0)
            )
            rows.append(
                {
                    "key": identity,
                    "type": "Film" if kind == "movie" else "Série",
                    "kind": kind,
                    "title": _title(item, kind),
                    "year": _year(item, kind),
                    "note": note,
                    "added_at": added_at.isoformat() if added_at else None,
                    "added_days": days,
                    "watched": is_watched,
                    "duplicate": is_duplicate,
                    "container_count": len(containers),
                    "containers": containers,
                    "issues": issue_keys,
                    "issue_labels": issue_labels,
                    "priority": priority,
                    "source_key": source_key,
                    "source_label": source_display_label(source),
                    "source_type": str(source.get("type") or "unknown"),
                    "writable": str(source.get("type") or "") in {"native", "static"},
                }
            )
    return rows


def _issue_key(label: str) -> str:
    return {
        "Déjà vus": "watched",
        "Présents dans plusieurs conteneurs": "duplicate",
        "Ajoutés depuis plus de 6 mois": "old_180",
        "Ajoutés depuis plus d’un an": "old_365",
        "Ajoutés depuis plus de deux ans": "old_730",
        "Note communauté inférieure à 5/10": "low_rating",
    }.get(label, "")


def filter_audit_rows(
    rows: Iterable[dict[str, Any]],
    selected_issues: list[str] | None = None,
    match_all: bool = False,
    media_filter: str = "Tous",
    search: str = "",
    sort_mode: str = "Priorité de nettoyage",
) -> list[dict[str, Any]]:
    query = str(search or "").strip().casefold()
    wanted = [_issue_key(label) for label in (selected_issues or []) if _issue_key(label)]
    output = []
    for row in rows:
        if media_filter == "Films" and row.get("type") != "Film":
            continue
        if media_filter == "Séries" and row.get("type") != "Série":
            continue
        if query and query not in str(row.get("title") or "").casefold():
            continue
        if wanted:
            checks = [key in (row.get("issues") or []) for key in wanted]
            if match_all and not all(checks):
                continue
            if not match_all and not any(checks):
                continue
        output.append(row)

    if sort_mode == "Ajout le plus ancien":
        output.sort(key=lambda row: (row.get("added_days") is None, -(row.get("added_days") or 0), row["title"].casefold()))
    elif sort_mode == "Ajout le plus récent":
        output.sort(key=lambda row: (row.get("added_days") is None, row.get("added_days") or 0, row["title"].casefold()))
    elif sort_mode == "Note la plus faible":
        output.sort(key=lambda row: (row.get("note") is None, row.get("note") or 0, row["title"].casefold()))
    elif sort_mode == "Plus grand nombre de conteneurs":
        output.sort(key=lambda row: (-int(row.get("container_count") or 0), row["title"].casefold()))
    elif sort_mode == "Titre A → Z":
        output.sort(key=lambda row: row["title"].casefold())
    elif sort_mode == "Titre Z → A":
        output.sort(key=lambda row: row["title"].casefold(), reverse=True)
    else:
        output.sort(key=lambda row: (-int(row.get("priority") or 0), row["title"].casefold()))
    return output


def addition_history(dataset: dict[str, Any]) -> list[dict[str, Any]]:
    """Une ligne par appartenance réelle à une Watchlist/liste personnelle."""
    output = []
    for source in auditable_sources(dataset):
        source_label = source_display_label(source)
        source_type = str(source.get("type") or "unknown")
        for section, kind in (("movies", "movie"), ("shows", "show")):
            for item in source.get(section) or []:
                if not isinstance(item, dict):
                    continue
                added_at = _added_datetime(item)
                output.append(
                    {
                        "key": f"addition:{source.get('key')}:{_identity(item, kind)}",
                        "type": "Film" if kind == "movie" else "Série",
                        "title": _title(item, kind),
                        "year": _year(item, kind),
                        "added_at": added_at,
                        "container": source_label,
                        "container_type": source_type,
                    }
                )
    return sorted(
        output,
        key=lambda row: (
            row.get("added_at") is None,
            -(row["added_at"].timestamp()) if row.get("added_at") else 0,
            row["title"].casefold(),
        ),
    )


def filter_addition_history(
    rows: Iterable[dict[str, Any]],
    container: str = "Tous les conteneurs",
    media_filter: str = "Tous",
    period: str = "Toutes les dates",
    search: str = "",
    sort_mode: str = "Ajouts les plus récents",
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    now = now or datetime.now(timezone.utc)
    query = str(search or "").strip().casefold()
    threshold = None
    if period == "7 derniers jours":
        threshold = now - timedelta(days=7)
    elif period == "30 derniers jours":
        threshold = now - timedelta(days=30)
    elif period == "90 derniers jours":
        threshold = now - timedelta(days=90)
    elif period == "Cette année":
        threshold = datetime(now.year, 1, 1, tzinfo=timezone.utc)

    output = []
    for row in rows:
        if container != "Tous les conteneurs" and row.get("container") != container:
            continue
        if media_filter == "Films" and row.get("type") != "Film":
            continue
        if media_filter == "Séries" and row.get("type") != "Série":
            continue
        if query and query not in str(row.get("title") or "").casefold():
            continue
        added_at = row.get("added_at")
        if period == "Date inconnue" and added_at is not None:
            continue
        if period != "Date inconnue" and threshold and (added_at is None or added_at < threshold):
            continue
        output.append(row)

    if sort_mode == "Ajouts les plus anciens":
        return sorted(output, key=lambda row: (row.get("added_at") is None, row.get("added_at") or datetime.max.replace(tzinfo=timezone.utc)))
    if sort_mode == "Conteneur":
        return sorted(output, key=lambda row: (row["container"].casefold(), row.get("added_at") is None, -(row["added_at"].timestamp()) if row.get("added_at") else 0))
    if sort_mode == "Titre A → Z":
        return sorted(output, key=lambda row: (row["title"].casefold(), row.get("added_at") is None))
    return sorted(output, key=lambda row: (row.get("added_at") is None, -(row["added_at"].timestamp()) if row.get("added_at") else 0))


def addition_rows_to_csv(rows: Iterable[dict[str, Any]]) -> str:
    values = []
    for row in rows:
        added_at = row.get("added_at")
        values.append(
            {
                "date_ajout": added_at.isoformat() if isinstance(added_at, datetime) else "",
                "type": row.get("type"),
                "titre": row.get("title"),
                "annee": row.get("year"),
                "conteneur": row.get("container"),
                "type_conteneur": row.get("container_type"),
            }
        )
    if not values:
        return ""
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=list(values[0]))
    writer.writeheader()
    writer.writerows(values)
    return stream.getvalue()


def export_rows(rows: Iterable[dict[str, Any]], report_type: str) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        base = {
            "type": row.get("type"),
            "titre": row.get("title"),
            "annee": row.get("year"),
        }
        if report_type == "duplicates":
            base.update(
                {
                    "classification": row.get("overlap_type"),
                    "nombre_conteneurs": row.get("container_count"),
                    "conteneurs": " | ".join(row.get("containers") or []),
                }
            )
        else:
            base.update(
                {
                    "note": row.get("note"),
                    "date_ajout": row.get("added_at"),
                    "anciennete_jours": row.get("added_days"),
                    "deja_vu": row.get("watched"),
                    "nombre_conteneurs": row.get("container_count"),
                    "signaux": " | ".join(row.get("issue_labels") or []),
                    "source": row.get("source_label"),
                    "source_modifiable": row.get("writable"),
                }
            )
        output.append(base)
    return output


def rows_to_csv(rows: Iterable[dict[str, Any]], report_type: str) -> str:
    values = export_rows(rows, report_type)
    if not values:
        return ""
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=list(values[0]))
    writer.writeheader()
    writer.writerows(values)
    return stream.getvalue()


def rows_to_json(rows: Iterable[dict[str, Any]], report_type: str) -> str:
    return json.dumps(
        {
            "engine": "media-smart-lists-list-audit",
            "version": AUDIT_ENGINE_VERSION,
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "report_type": report_type,
            "rows": export_rows(rows, report_type),
        },
        ensure_ascii=False,
        indent=2,
    )
