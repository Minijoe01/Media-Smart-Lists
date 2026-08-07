"""Moteur de recommandation explicable, fournisseur-neutre et sans appel API.

Le moteur n'accède jamais au réseau. Il transforme le dataset déjà chargé en
profil de goûts et conserve le détail de chaque ajustement dans des infobulles.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from statistics import median
from typing import Any, Iterable

from normalized_model import media_key, media_type


ENGINE_VERSION = 2


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
            value = value.get("name") or value.get("title") or value.get("slug")
        if value:
            output.append(str(value).strip().title())
    return sorted(set(output), key=str.casefold)


def _runtime(item: dict[str, Any]) -> int:
    media = _nested_media(item)
    try:
        return max(int(round(float(media.get("runtime") or item.get("runtime") or 0))), 0)
    except (TypeError, ValueError):
        return 0


def _year(item: dict[str, Any]) -> int | None:
    media = _nested_media(item)
    value = media.get("year") or media.get("release_year") or item.get("release_year") or item.get("year")
    try:
        return int(value) if value else None
    except (TypeError, ValueError):
        return None


def _status(item: dict[str, Any]) -> str:
    media = _nested_media(item)
    return str(media.get("status") or item.get("status") or "").strip().lower()


def _country(item: dict[str, Any]) -> str:
    media = _nested_media(item)
    value = media.get("country") or item.get("country") or ""
    if isinstance(value, list):
        value = value[0] if value else ""
    if isinstance(value, dict):
        value = value.get("iso_3166_1") or value.get("code") or value.get("name") or ""
    return str(value).strip().lower()


def _certification(item: dict[str, Any]) -> str:
    media = _nested_media(item)
    return str(media.get("certification") or item.get("certification") or "").strip().upper()


def _ratings(item: dict[str, Any]) -> list[dict[str, Any]]:
    media = _nested_media(item)
    values = media.get("ratings") or item.get("ratings") or []
    return [value for value in values if isinstance(value, dict)]


def _community_note(item: dict[str, Any]) -> float | None:
    media = _nested_media(item)
    for value in (media.get("score"), media.get("score_average"), item.get("score"), item.get("score_average")):
        try:
            if value is not None and float(value) > 0:
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


def _names(values: Any) -> list[str]:
    if values in (None, ""):
        return []
    if not isinstance(values, list):
        values = [values]
    output: dict[str, str] = {}
    for value in values:
        if isinstance(value, dict):
            value = value.get("name") or value.get("title") or value.get("original_name")
        if not value:
            continue
        for part in str(value).split(","):
            name = part.strip()
            if name:
                output.setdefault(name.casefold(), name)
    return list(output.values())


def _studios(item: dict[str, Any]) -> list[str]:
    """Métadonnées opportunistes : aucune récupération distante."""
    media = _nested_media(item)
    output: dict[str, str] = {}
    for key in ("studios", "studio", "production_companies", "companies", "networks", "network"):
        for name in _names(media.get(key) or item.get(key)):
            output.setdefault(name.casefold(), name)
    return list(output.values())


def _people(item: dict[str, Any]) -> list[str]:
    """Acteurs principaux lorsqu'un fournisseur les a déjà placés dans le dataset."""
    media = _nested_media(item)
    values: list[Any] = []
    for key in ("actors", "cast"):
        raw = media.get(key) or item.get(key)
        if isinstance(raw, list):
            values.extend(raw)
    credits = media.get("credits") if isinstance(media.get("credits"), dict) else {}
    if isinstance(credits.get("cast"), list):
        values.extend(credits["cast"])
    ordered = []
    for value in values:
        if isinstance(value, dict):
            try:
                if int(value.get("order", 0)) >= 10:
                    continue
            except (TypeError, ValueError):
                pass
        ordered.extend(_names(value))
    unique: dict[str, str] = {}
    for name in ordered:
        unique.setdefault(name.casefold(), name)
    return list(unique.values())[:10]


def _episode_count(item: dict[str, Any]) -> int:
    media = _nested_media(item)
    for key in ("total_aired_episodes", "aired_episodes", "total_episodes", "episode_count", "number_of_episodes"):
        try:
            value = int(media.get(key) or item.get(key) or 0)
            if value > 0:
                return value
        except (TypeError, ValueError):
            pass
    return 0


def _identity_keys(item: dict[str, Any], kind: str) -> set[tuple[str, str, str]]:
    media = _nested_media(item)
    ids = media.get("ids") if isinstance(media.get("ids"), dict) else {}
    output = set()
    for provider in ("tmdb", "imdb", "tvdb", "trakt", "mdblist"):
        value = ids.get(provider)
        if value not in (None, "", 0, "0"):
            output.add((kind, provider, str(value)))
    value = media.get("id") or media.get("imdb_id")
    if value not in (None, "", 0, "0"):
        output.add((kind, "id", str(value)))
    return output


def _event_date(row: dict[str, Any]) -> datetime | None:
    value = row.get("last_watched_at") or row.get("watched_at") or row.get("updated_at")
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except Exception:
        return None


def _recency_weight(row: dict[str, Any], now: datetime) -> float:
    parsed = _event_date(row)
    if not parsed:
        return 1.0
    days = max((now - parsed).days, 0)
    return 0.5 ** (days / 730)


def _normalize(values: dict[Any, float]) -> dict[Any, float]:
    maximum = max(values.values(), default=0)
    if maximum <= 0:
        return {}
    return {key: round(value / maximum * 100, 2) for key, value in values.items()}


def _percentile(values: list[int], ratio: float) -> int:
    if not values:
        return 0
    index = min(len(values) - 1, max(0, int((len(values) - 1) * ratio)))
    return values[index]


def _rating_media(row: dict[str, Any], section: str) -> tuple[dict[str, Any], str]:
    if section == "movies":
        value = row.get("movie") if isinstance(row.get("movie"), dict) else _nested_media(row)
        return value, "movie"
    if section == "shows":
        value = row.get("show") if isinstance(row.get("show"), dict) else _nested_media(row)
        return value, "show"
    nested = row.get("episode") if section == "episodes" else row.get("season")
    nested = nested if isinstance(nested, dict) else {}
    show = nested.get("show") if isinstance(nested.get("show"), dict) else {}
    return show or nested, "show"


def build_profile(dataset: dict[str, Any], now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    sections = dataset.get("sections") or {}
    watched = sections.get("watched") or {}
    ratings = sections.get("ratings") or {}

    metadata_index: dict[tuple[str, str, str], dict[str, Any]] = {}
    unique_metadata: list[tuple[str, dict[str, Any]]] = []
    for section, kind in (("movies", "movie"), ("shows", "show")):
        for row in watched.get(section) or []:
            if not isinstance(row, dict):
                continue
            media = row.get("movie" if kind == "movie" else "show")
            media = media if isinstance(media, dict) else _nested_media(row)
            unique_metadata.append((kind, media))
            for identity in _identity_keys(media, kind):
                metadata_index[identity] = media

    def lookup(media: dict[str, Any], kind: str) -> dict[str, Any]:
        for identity in _identity_keys(media, kind):
            if identity in metadata_index:
                return metadata_index[identity]
        return media

    genre_weights: defaultdict[str, float] = defaultdict(float)
    country_weights: defaultdict[str, float] = defaultdict(float)
    decade_weights: defaultdict[int, float] = defaultdict(float)
    recent_events: list[tuple[datetime, list[str]]] = []
    movie_runtimes: list[int] = []

    for row in watched.get("movies") or []:
        if not isinstance(row, dict):
            continue
        media = row.get("movie") if isinstance(row.get("movie"), dict) else _nested_media(row)
        runtime = _runtime(media) or 100
        weight = runtime * _recency_weight(row, now)
        genres = _genres(media)
        for genre in genres:
            genre_weights[genre] += weight
        country = _country(media)
        if country:
            country_weights[country] += weight
        year = _year(media)
        if year:
            decade_weights[(year // 10) * 10] += weight
        if _runtime(media):
            movie_runtimes.append(_runtime(media))
        event_date = _event_date(row)
        if event_date:
            recent_events.append((event_date, genres))

    episode_rows = list(watched.get("episodes") or [])
    if episode_rows:
        for row in episode_rows:
            if not isinstance(row, dict):
                continue
            episode = row.get("episode") if isinstance(row.get("episode"), dict) else {}
            show_ref = episode.get("show") if isinstance(episode.get("show"), dict) else {}
            media = lookup(show_ref, "show")
            runtime = _runtime(episode) or _runtime(media) or 45
            weight = runtime * _recency_weight(row, now)
            genres = _genres(media)
            for genre in genres:
                genre_weights[genre] += weight
            country = _country(media)
            if country:
                country_weights[country] += weight
            year = _year(media)
            if year:
                decade_weights[(year // 10) * 10] += weight
            event_date = _event_date(row)
            if event_date:
                recent_events.append((event_date, genres))
    else:
        for row in watched.get("shows") or []:
            if not isinstance(row, dict):
                continue
            media = row.get("show") if isinstance(row.get("show"), dict) else _nested_media(row)
            runtime = _runtime(media) or 45
            weight = runtime * _recency_weight(row, now)
            genres = _genres(media)
            for genre in genres:
                genre_weights[genre] += weight
            country = _country(media)
            if country:
                country_weights[country] += weight
            year = _year(media)
            if year:
                decade_weights[(year // 10) * 10] += weight
            event_date = _event_date(row)
            if event_date:
                recent_events.append((event_date, genres))

    recent_genres: Counter[str] = Counter()
    for _, genres in sorted(recent_events, key=lambda value: value[0], reverse=True)[:6]:
        recent_genres.update(genres)

    genre_rating_values: defaultdict[str, list[float]] = defaultdict(list)
    studio_rating_values: defaultdict[str, list[float]] = defaultdict(list)
    people_rating_values: defaultdict[str, list[float]] = defaultdict(list)
    personal_ratings: list[float] = []
    disappointments: Counter[str] = Counter()
    for section in ("movies", "shows", "seasons", "episodes"):
        for row in ratings.get(section) or []:
            if not isinstance(row, dict):
                continue
            try:
                rating = float(row.get("rating"))
            except (TypeError, ValueError):
                continue
            media_ref, kind = _rating_media(row, section)
            media = lookup(media_ref, kind)
            personal_ratings.append(rating)
            genres = _genres(media)
            for genre in genres:
                genre_rating_values[genre].append(rating)
                if rating <= 3:
                    disappointments[genre] += 1
            for studio in _studios(media):
                studio_rating_values[studio].append(rating)
            for person in _people(media):
                people_rating_values[person].append(rating)

    studio_titles: Counter[str] = Counter()
    people_titles: Counter[str] = Counter()
    studio_display: dict[str, str] = {}
    people_display: dict[str, str] = {}
    studio_metadata_count = 0
    people_metadata_count = 0
    for _, media in unique_metadata:
        studios = _studios(media)
        people = _people(media)
        if studios:
            studio_metadata_count += 1
        if people:
            people_metadata_count += 1
        for studio in studios:
            key = studio.casefold()
            studio_titles[key] += 1
            studio_display.setdefault(key, studio)
        for person in people:
            key = person.casefold()
            people_titles[key] += 1
            people_display.setdefault(key, person)

    studio_ratings_by_key = {
        name.casefold(): (sum(values) / len(values), len(values))
        for name, values in studio_rating_values.items() if values
    }
    people_ratings_by_key = {
        name.casefold(): (sum(values) / len(values), len(values))
        for name, values in people_rating_values.items() if values
    }
    favorite_studios = {
        key for key, count in studio_titles.items()
        if count >= 3 and (key not in studio_ratings_by_key or studio_ratings_by_key[key][0] >= 7.5)
    }
    favorite_people = {
        key for key, count in people_titles.items()
        if count >= 3 and (key not in people_ratings_by_key or people_ratings_by_key[key][0] >= 7.5)
    }

    sorted_runtimes = sorted(movie_runtimes)
    runtime_band = None
    if len(sorted_runtimes) >= 10:
        runtime_band = (
            _percentile(sorted_runtimes, 0.10),
            _percentile(sorted_runtimes, 0.25),
            _percentile(sorted_runtimes, 0.75),
            _percentile(sorted_runtimes, 0.90),
        )

    progress_by_tmdb = {}
    for row in dataset.get("progress") or []:
        ids = (row.get("show") or {}).get("ids") or {}
        if ids.get("tmdb") is not None:
            progress_by_tmdb[str(ids["tmdb"])] = row

    return {
        "genre_affinity": _normalize(dict(genre_weights)),
        "personal_genre_ratings": {
            genre: sum(values) / len(values)
            for genre, values in genre_rating_values.items() if values
        },
        "genre_disappointments": dict(disappointments),
        "favorite_decades": _normalize(dict(decade_weights)),
        "country_affinity": _normalize(dict(country_weights)),
        "recent_genres": dict(recent_genres),
        "preferred_runtime": int(median(sorted_runtimes)) if sorted_runtimes else 105,
        "runtime_band": runtime_band,
        "average_personal_rating": (
            sum(personal_ratings) / len(personal_ratings) if personal_ratings else None
        ),
        "history_count": len(watched.get("movies") or []) + len(watched.get("episodes") or []),
        "ratings_count": len(personal_ratings),
        "progress_by_tmdb": progress_by_tmdb,
        "favorite_studios": favorite_studios,
        "favorite_people": favorite_people,
        "studio_title_counts": dict(studio_titles),
        "people_title_counts": dict(people_titles),
        "studio_display": studio_display,
        "people_display": people_display,
        "studio_metadata_count": studio_metadata_count,
        "people_metadata_count": people_metadata_count,
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


def _points_text(points: float | None) -> str:
    if points is None:
        return ""
    rounded = float(round(points, 1))
    value = str(int(rounded)) if rounded.is_integer() else str(rounded).replace(".", ",")
    return f"+{value} pts" if rounded > 0 else f"−{value.lstrip('-')} pts" if rounded < 0 else "0 pt"


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
    genres = sorted(set(genres), key=str.casefold)
    runtime = _runtime(item)
    year = _year(item)
    note = _community_note(item)
    votes = _votes(item)
    status = _status(item)
    country = _country(item)
    certification = _certification(item)
    studios = _studios(item)
    people = _people(item)
    added_days = _added_days(item, now)
    ids = item.get("ids") if isinstance(item.get("ids"), dict) else {}
    tmdb_id = ids.get("tmdb") or item.get("id")
    progress = profile.get("progress_by_tmdb", {}).get(str(tmdb_id), {})
    total_episodes = int(progress.get("total_episodes") or _episode_count(item) or 0)
    watched_episodes = int(progress.get("watched_episodes") or 0)
    started = bool(total_episodes and watched_episodes)

    score = 20.0
    reasons: list[str] = []
    warnings: list[str] = []
    signals: list[dict[str, Any]] = []
    breakdown: list[dict[str, Any]] = [{"label": "Base équilibrée", "points": 20.0}]

    def adjust(points: float, label: str = "", detail: str = "", warning: bool = False) -> None:
        nonlocal score
        score += points
        breakdown.append({"label": label or detail, "points": round(points, 2)})
        if label:
            tooltip = detail.strip()
            point_text = _points_text(points)
            if point_text:
                tooltip = f"{tooltip} · {point_text}" if tooltip else point_text
            signals.append({"label": label, "tooltip": tooltip, "warning": warning or points < 0})
        text = detail or label
        if text:
            (warnings if warning or points < 0 else reasons).append(text)

    def info(label: str, detail: str, warning: bool = False) -> None:
        signals.append({"label": label, "tooltip": detail, "warning": warning})
        if warning:
            warnings.append(detail)

    affinities = profile.get("genre_affinity", {})
    if genres and affinities:
        affinity = sum(affinities.get(genre, 0) for genre in genres) / len(genres)
        bonus = min(affinity * 0.4, 40)
        if bonus >= 4:
            label = "❤️ Tes genres" if any(affinities.get(genre, 0) >= 60 for genre in genres) else "🎭 Affinité genre"
            adjust(bonus, label, "Proche de tes genres préférés actuels")
        else:
            score += bonus
            breakdown.append({"label": "Affinité genre", "points": round(bonus, 2)})
            info("🧭 Genre peu habituel", "Genre encore peu présent dans ton historique", warning=True)

    personal_genres = profile.get("personal_genre_ratings", {})
    own_values = [personal_genres[genre] for genre in genres if genre in personal_genres]
    if own_values:
        own_average = sum(own_values) / len(own_values)
        if own_average >= 8:
            adjust(8, "🫶 Bien noté par toi", f"Ta moyenne personnelle dans ces genres est de {own_average:.1f}/10")
        elif own_average <= 5:
            adjust(-6, "👎 Tu notes ce genre bas", f"Ta moyenne personnelle dans ces genres est de {own_average:.1f}/10", warning=True)

    disappointments = profile.get("genre_disappointments", {})
    miss_count = max((int(disappointments.get(genre, 0)) for genre in genres), default=0)
    if miss_count >= 2:
        adjust(-5, "👎 Tes ratages ici", f"Tu as déjà donné 3/10 ou moins à {miss_count} contenu(s) de ce genre", warning=True)

    if note is not None:
        note_bonus = min(note / 10 * 25, 25)
        label = "💎 Pépite critique" if note >= 9 else "⭐ Très bien noté" if note >= 8 else "⭐ Note communauté"
        adjust(note_bonus, label, f"Note moyenne de la communauté : {note:.1f}/10")
        if note < 5:
            info("⚠️ Note faible", f"La note communauté est seulement de {note:.1f}/10", warning=True)

    if votes >= 100000:
        adjust(4, "🔥 Populaire", f"Très largement évalué par la communauté ({votes:,} votes)".replace(",", " "))
    elif votes >= 10000:
        info("👥 Apprécié du public", f"Déjà évalué par {votes:,} personnes".replace(",", " "))

    studio_matches = [studio for studio in studios if studio.casefold() in profile.get("favorite_studios", set())]
    if studio_matches:
        studio = studio_matches[0]
        count = profile.get("studio_title_counts", {}).get(studio.casefold(), 0)
        adjust(4, "🏢 Studio fétiche", f"Tu as déjà regardé au moins {count} titre(s) lié(s) à {studio}")

    people_matches = [person for person in people if person.casefold() in profile.get("favorite_people", set())]
    if people_matches:
        person = people_matches[0]
        count = profile.get("people_title_counts", {}).get(person.casefold(), 0)
        adjust(4, "🎭 Visage familier", f"{person} apparaît dans au moins {count} contenu(s) déjà regardé(s)")

    recent = profile.get("recent_genres", {})
    if genres and recent:
        overlap = sum(int(recent.get(genre, 0)) for genre in genres)
        top_genre, top_count = max(recent.items(), key=lambda value: value[1])
        if overlap == 0 and top_count >= 4:
            adjust(3, "🔄 Varier un peu", f"Tes dernières vues étaient très « {top_genre} »")

    if country and country != "us":
        country_score = profile.get("country_affinity", {}).get(country, 0)
        country_label = country.upper()
        if country_score >= 50:
            adjust(4, f"🌍 Cinéma {country_label}", f"Tu regardes régulièrement des productions de ce pays")
        else:
            info(f"🌍 Cinéma {country_label}", "Une production hors États-Unis pour varier")

    if year:
        age = now.year - year
        if age <= 1:
            adjust(18, "🆕 Toute récente", f"Sortie en {year}")
        elif age <= 2:
            adjust(15, "🆕 Récente", f"Sortie en {year}")
        elif age <= 10:
            score += 8
            breakdown.append({"label": "Sortie moderne", "points": 8})
        elif age >= 40:
            decade = (year // 10) * 10
            if profile.get("favorite_decades", {}).get(decade, 0) > 50:
                adjust(12, "🏆 Classique pour toi", f"Un classique de {year}, dans une décennie que tu regardes souvent")
            else:
                score += 1
                breakdown.append({"label": "Classique", "points": 1})
        if age >= 30 and note is not None and note >= 7.5:
            info("🏆 Classique culte", f"Sorti en {year} et toujours très bien noté")

    if kind == "movie" and runtime:
        band = profile.get("runtime_band")
        if band:
            p10, p25, p75, p90 = band
            if p25 <= runtime <= p75:
                adjust(10, "⏱️ Durée idéale", f"{runtime} min, au cœur de tes durées habituelles")
            elif p10 <= runtime <= p90:
                adjust(5, "⏱️ Dans tes habitudes", f"{runtime} min, proche de tes durées habituelles")
            elif runtime > max(p90, 160):
                adjust(-4, "⏱️ Plus long pour toi", f"{runtime} min, au-delà de tes habitudes", warning=True)
        elif runtime <= 90:
            adjust(12, "⏱️ Film court", f"Seulement {runtime} min")
        elif runtime <= 100:
            adjust(10, "⏱️ Film rapide", f"Seulement {runtime} min")
        elif runtime <= 120:
            score += 5
            breakdown.append({"label": "Durée accessible", "points": 5})
        elif runtime >= 200:
            adjust(-8, "⏱️ Film très long", f"Engagement de {runtime} min", warning=True)
        elif runtime >= 160:
            adjust(-3, "⏱️ Film long", f"Engagement de {runtime} min", warning=True)

    if kind == "show":
        if 0 < total_episodes <= 6:
            adjust(10, "🎯 Mini-série", f"Seulement {total_episodes} épisode(s)")
        elif total_episodes <= 13 and total_episodes > 0:
            adjust(7, "📦 Saison courte", f"Seulement {total_episodes} épisode(s)")
        elif total_episodes <= 25 and total_episodes > 0:
            score += 5
            breakdown.append({"label": "Série courte", "points": 5})
        elif total_episodes >= 300:
            adjust(-12, "🐘 Gros engagement", f"La série compte environ {total_episodes} épisodes", warning=True)
        elif total_episodes >= 150:
            adjust(-6, "📚 Série longue", f"La série compte environ {total_episodes} épisodes", warning=True)
        if started:
            remaining = max(total_episodes - watched_episodes, 0)
            adjust(8, "▶️ À continuer", f"Déjà commencée : il reste {remaining} épisode(s)")
            if total_episodes and watched_episodes >= 0.8 * total_episodes:
                info("🏁 Presque finie", f"Plus que {remaining} épisode(s) avant la fin")
        if status == "ended":
            info("✅ Terminée", "Toutes les saisons sont disponibles, pas d’attente")
        elif status == "canceled":
            info("⚠️ Série annulée", "La série a été annulée", warning=True)

    if certification in {"G", "PG", "TV-Y", "TV-Y7", "TV-G"}:
        info("👨‍👩‍👧 Famille", f"Certification {certification} : adaptée à un visionnage familial")

    if note is not None and 0 < votes < 30000 and note >= 7.8:
        adjust(5, "💎 Pépite confidentielle", f"Très bien notée ({note:.1f}/10) mais encore peu connue ({votes} votes)")

    if added_days is not None:
        if added_days <= 7:
            adjust(12, "📥 Tout juste ajouté", f"Ajouté dans cette liste il y a {added_days} jour(s)")
        elif added_days <= 14:
            adjust(10, "📥 Ajout récent", f"Ajouté dans cette liste il y a {added_days} jour(s)")
        elif added_days > 730:
            adjust(-25, "🕸️ Oublié dans la liste", f"Présent dans cette liste depuis plus de deux ans", warning=True)
        elif added_days > 365:
            adjust(-20, "⌛ En liste depuis longtemps", f"Présent dans cette liste depuis plus d’un an", warning=True)
        elif added_days > 180:
            adjust(-10, "⌛ Ajout ancien", f"Présent dans cette liste depuis plus de six mois", warning=True)

    friction = _friction(kind, runtime, total_episodes, started)
    if friction >= 95:
        info("🚪 Zéro effort", f"Facilité de lancement : {friction}/100")
    if now.hour >= 22 or now.hour < 5:
        if (kind == "movie" and runtime and runtime <= 105) or (kind == "show" and 0 < total_episodes <= 8):
            adjust(7, "🌙 Fin de soirée", f"Un format court adapté à l’heure actuelle ({now.hour} h)")

    raw_score = round(score, 1)
    final_score = max(0, min(raw_score, 100))
    negative_signals = sum(1 for signal in signals if signal.get("warning"))
    not_for_me = raw_score < 35 or negative_signals >= 2
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
        "country": country,
        "certification": certification,
        "studios": studios,
        "people": people,
        "added_days": added_days,
        "total_episodes": total_episodes,
        "watched_episodes": watched_episodes,
        "score": final_score,
        "friction": friction,
        "reasons": list(dict.fromkeys(reasons)),
        "warnings": list(dict.fromkeys(warnings)),
        "signals": signals,
        "tags": [signal["label"] for signal in signals],
        "score_breakdown": breakdown,
        "not_for_me": not_for_me,
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
        return row.get("certification") in {"G", "PG", "TV-Y", "TV-Y7", "TV-G"} or bool(genres & {"family", "animation"})
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
        return bool(row.get("genres")) and all(affinities.get(genre, 0) < 30 for genre in row["genres"]) and note >= 7.5
    if name.startswith("✨"):
        return note >= 7.5 and year >= datetime.now(timezone.utc).year - 2
    if name.startswith("🗳️"):
        return note >= 8 and row.get("votes", 0) >= 50000
    if name.startswith("🚪"):
        return row.get("friction", 0) >= 90
    if name.startswith("🌍"):
        return bool(row.get("country") and row["country"] != "us" and note >= 7)
    return True
