"""Lecture fournisseur-neutre des données MDBList.

Aucune écriture. Les réponses restent uniquement dans st.session_state via app.py.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests


API_BASE = "https://api.mdblist.com"
USER_AGENT = "Media-Smart-Lists/0.7"
TIMEOUT = 35
PAGE_LIMIT = 5000


class MDBListReadError(RuntimeError):
    pass


class MDBListProvider:
    def __init__(self, access_token: str):
        if not access_token:
            raise ValueError("Access token MDBList absent")
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        }
        self.request_count = 0
        self.rate_limit_remaining: int | None = None

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        try:
            response = requests.get(
                f"{API_BASE}{path}",
                params=params or {},
                headers=self.headers,
                timeout=TIMEOUT,
            )
        except requests.RequestException as exc:
            raise MDBListReadError(f"Réseau indisponible pour {path}") from exc
        self.request_count += 1
        remaining = response.headers.get("X-RateLimit-Remaining") or response.headers.get("X-Rate-Limit-Remaining")
        if remaining and str(remaining).isdigit():
            self.rate_limit_remaining = int(remaining)
        if response.status_code == 401:
            raise MDBListReadError("Session MDBList expirée ou révoquée")
        if response.status_code >= 400:
            raise MDBListReadError(f"MDBList a répondu HTTP {response.status_code} pour {path}")
        try:
            return response.json()
        except ValueError as exc:
            raise MDBListReadError(f"Réponse JSON invalide pour {path}") from exc

    def _paged_dict(
        self,
        path: str,
        keys: tuple[str, ...],
        extra_params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        merged = {key: [] for key in keys}
        offset = 0
        pages = 0
        last_pagination: dict[str, Any] = {}
        while True:
            params = {"limit": PAGE_LIMIT, "offset": offset}
            params.update(extra_params or {})
            response = self._get(path, params)
            if not isinstance(response, dict):
                raise MDBListReadError(f"Format paginé inattendu pour {path}")
            pages += 1
            for key in keys:
                values = response.get(key) or []
                if isinstance(values, list):
                    merged[key].extend(values)
            pagination = response.get("pagination") or {}
            last_pagination = pagination if isinstance(pagination, dict) else {}
            if not last_pagination.get("has_more"):
                break
            offset += PAGE_LIMIT
            if pages >= 100:
                raise MDBListReadError(f"Pagination anormalement longue pour {path}")
        merged["pagination"] = last_pagination
        merged["pages"] = pages
        return merged

    def watched(self) -> dict[str, Any]:
        return self._paged_dict(
            "/sync/watched",
            ("movies", "shows", "seasons", "episodes"),
        )

    def ratings(self) -> dict[str, Any]:
        return self._paged_dict(
            "/sync/ratings",
            ("movies", "shows", "seasons", "episodes"),
        )

    def watchlist(self, filter_genre: str | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {
            "append_to_response": "genres,poster,description,ratings",
            "unified": "false",
        }
        if filter_genre:
            params["filter_genre"] = filter_genre
        return self._paged_dict(
            "/watchlist/items",
            ("movies", "shows"),
            params,
        )

    def genres(self) -> list[dict[str, str]]:
        response = self._get("/genres")
        values = response if isinstance(response, list) else (
            response.get("genres") if isinstance(response, dict) else []
        )
        output: list[dict[str, str]] = []
        for value in values or []:
            if isinstance(value, str):
                slug = value.strip().lower()
                title = value.strip().title()
            elif isinstance(value, dict):
                slug = str(value.get("slug") or value.get("name") or "").strip().lower()
                title = str(value.get("title") or value.get("name") or slug).strip().title()
            else:
                continue
            if slug:
                output.append({"slug": slug, "title": title or slug.title()})
        unique = {item["slug"]: item for item in output}
        return sorted(unique.values(), key=lambda item: item["title"].casefold())

    def dropped(self) -> dict[str, Any]:
        return self._paged_dict(
            "/sync/dropped",
            ("shows",),
        )

    def playback(self) -> list[dict[str, Any]]:
        response = self._get("/sync/playback")
        if isinstance(response, list):
            return response
        if isinstance(response, dict):
            values = response.get("items") or response.get("playback") or []
            return values if isinstance(values, list) else []
        return []

    def upnext(self) -> list[dict[str, Any]]:
        all_items: list[dict[str, Any]] = []
        offset = 0
        while True:
            response = self._get("/upnext", {"limit": 100, "offset": offset})
            if not isinstance(response, dict):
                break
            values = response.get("items") or []
            if isinstance(values, list):
                all_items.extend(values)
            if not response.get("has_more"):
                break
            offset += 100
            if offset >= 10000:
                break
        return all_items

    def list_items(self, list_id: int, filter_genre: str | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {
            "append_to_response": "genres,poster,description,ratings",
            "unified": "false",
        }
        if filter_genre:
            params["filter_genre"] = filter_genre
        return self._paged_dict(
            f"/lists/{list_id}/items",
            ("movies", "shows"),
            params,
        )

    def user_lists(self) -> list[dict[str, Any]]:
        """Charge les listes personnelles statiques ET dynamiques."""
        response = self._get("/lists/user", {"unified": "false"})
        if not isinstance(response, list):
            raise MDBListReadError("Format des listes utilisateur inattendu")
        personal = [item for item in response if isinstance(item, dict)]
        output: list[dict[str, Any]] = []
        for metadata in personal:
            list_id = metadata.get("id")
            if list_id is None:
                continue
            items = self.list_items(int(list_id))
            list_type = "dynamic" if (
                metadata.get("type") == "dynamic" or metadata.get("dynamic") is True
            ) else "static"
            output.append(
                {
                    "id": int(list_id),
                    "name": metadata.get("name") or "Liste MDBList",
                    "private": metadata.get("private"),
                    "type": list_type,
                    "movies": items["movies"],
                    "shows": items["shows"],
                    "pages": items["pages"],
                }
            )
        return output

    def load_dataset(self) -> dict[str, Any]:
        sections: dict[str, Any] = {}
        errors: list[dict[str, str]] = []
        loaders = (
            ("watched", self.watched),
            ("watchlist", self.watchlist),
            ("genres", self.genres),
            ("user_lists", self.user_lists),
            ("ratings", self.ratings),
            ("playback", self.playback),
            ("upnext", self.upnext),
            ("dropped", self.dropped),
        )
        for name, loader in loaders:
            try:
                sections[name] = loader()
            except MDBListReadError as exc:
                errors.append({"section": name, "error": str(exc)})
                sections[name] = [] if name in {"genres", "user_lists", "playback", "upnext"} else {}
        return {
            "provider": "mdblist",
            "mode": "realtime",
            "loaded_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "sections": sections,
            "errors": errors,
            "request_count": self.request_count,
            "rate_limit_remaining": self.rate_limit_remaining,
        }
