"""Tests unitaires de base pour Media Smart Lists.

Léger (unittest stdlib), sans réseau, sans secrets : teste les moteurs purs
(history, calendar, migration, stats) sur des données factices.

Lancer :  python -m unittest discover -s tests -v
"""

import io
import json
import unittest
import zipfile
from datetime import datetime, timezone


def make_zip(payloads: dict[str, list]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, rows in payloads.items():
            z.writestr(name, json.dumps(rows))
    return buf.getvalue()


class TestHistoryRuntimes(unittest.TestCase):
    """Durées d'épisode normalisées (jamais de durée cumulée)."""

    def test_episode_runtime_cumulated(self):
        from history_engine import normalize_history

        watched = {
            "movies": [],
            "episodes": [
                {
                    "episode": {"season": 1, "number": 1, "title": "E1",
                                "show": {"title": "Connasse", "ids": {"tmdb": 1},
                                         "runtime": 142, "total_episodes": 71,
                                         "genres": ["Comédie"]}},
                    "last_watched_at": "2026-08-01T20:00:00+02:00",
                    "plays": 1,
                }
            ],
            "shows": [],
        }
        rows = normalize_history({"sections": {"watched": watched}})
        self.assertEqual(rows[0]["runtime"], 2)  # 142 / 71

    def test_normal_runtime(self):
        from history_engine import normalize_history

        watched = {
            "movies": [],
            "episodes": [
                {"episode": {"season": 1, "number": 1, "show": {"title": "Série", "ids": {"tmdb": 2}, "runtime": 45}},
                 "last_watched_at": "2026-08-01T20:00:00+02:00", "plays": 1}
            ],
            "shows": [],
        }
        rows = normalize_history({"sections": {"watched": watched}})
        self.assertEqual(rows[0]["runtime"], 45)


class TestCalendar(unittest.TestCase):
    """Calendrier de secours : filtres d'horizon + dédup."""

    def test_build_local_events(self):
        from datetime import date, timedelta
        from calendar_engine import build_local_calendar_events

        today = date(2026, 8, 7)
        dataset = {
            "sections": {
                "upnext": [{"show": {"title": "Série A", "ids": {"tmdb": 1}},
                            "next_episode": {"air_date": "2026-08-12"}}],
            },
            "sources": [{
                "name": "Watchlist", "kind": "watchlist",
                "movies": [{"title": "Film 2027", "ids": {"imdb": "tt1"}, "premiere_date": "2027-05-21"}],
                "shows": [],
            }],
        }
        events = build_local_calendar_events(dataset, today, today + timedelta(days=365))
        self.assertEqual(len(events), 2)


class TestMigration(unittest.TestCase):
    """Plan de migration : vraies dates + sans correspondance."""

    def setUp(self):
        from trakt_zip_provider import load_trakt_zip
        import migration_engine as mig
        self.mig = mig
        zip_bytes = make_zip({
            "watched-history-1.json": [
                {"id": 1, "action": "watch", "type": "movie",
                 "movie": {"title": "Dune", "year": 2021, "ids": {"imdb": "tt1160419", "tmdb": 438631}},
                 "watched_at": "2026-08-01T20:00:00.000Z"},
                {"id": 2, "action": "watch", "type": "movie",
                 "movie": {"title": "Inconnu", "year": 2020, "ids": {"trakt": 999}},
                 "watched_at": "2026-08-02T20:00:00.000Z"},
                {"id": 3, "action": "watch", "type": "episode",
                 "show": {"title": "Silo", "year": 2023, "ids": {"imdb": "tt14688458", "tmdb": 100088}},
                 "episode": {"season": 1, "number": 1, "ids": {"tmdb": 4184664}},
                 "watched_at": "2026-08-02T22:00:00.000Z"},
            ],
            "lists-watchlist.json": [
                {"listed_at": "2026-07-01T10:00:00.000Z", "type": "movie",
                 "movie": {"title": "Avatar 3", "year": 2026, "ids": {"imdb": "tt1757678", "tmdb": 566525}}},
            ],
        })
        self.dataset = load_trakt_zip(zip_bytes)

    def test_plan_counts(self):
        plan = self.mig.build_migration_plan(self.dataset)
        self.assertEqual(plan["films_vus"], 1)          # Inconnu exclu
        self.assertEqual(plan["episodes_vus"], 1)
        self.assertEqual(len(plan["sans_correspondance"]), 1)

    def test_watched_payload_dates(self):
        plan = self.mig.build_migration_plan(self.dataset)
        payloads = self.mig.build_watched_payloads(plan)
        self.assertTrue(payloads["movies"][0]["watched_at"].startswith("2026-08-01"))
        self.assertTrue(payloads["shows"][0]["seasons"][0]["episodes"][0]["watched_at"].startswith("2026-08-02"))

    def test_report_excel(self):
        plan = self.mig.build_migration_plan(self.dataset)
        report = self.mig.generate_migration_report(plan, {"watched_movies_ok": 1, "errors": 0})
        self.assertEqual(report[:2], b"PK")  # xlsx valide


class TestStats(unittest.TestCase):
    """Statistiques : mois triés chronologiquement."""

    def test_monthly_order(self):
        from stats_engine import build_frame, monthly_options

        def row(days_ago, title):
            from datetime import timedelta
            now = datetime(2026, 8, 7, tzinfo=timezone.utc)
            return {
                "kind": "movie", "type": "Film", "title": title, "year": 2020,
                "watched_at": now - timedelta(days=days_ago),
                "runtime": 100, "plays": 1, "total_minutes": 100,
                "genres": ["Drame"], "personal_rating": 7.0, "ids": {}, "poster": "", "studios": [],
            }
        df = build_frame([row(15, "A"), row(400, "B"), row(430, "C")])
        mo = monthly_options(df)
        labels = mo["xAxis"]["data"]
        keys = [(int(m[3:]), int(m[:2])) for m in labels]
        self.assertEqual(keys, sorted(keys))


class TestDashboardWidgets(unittest.TestCase):
    """Widgets restaurés du tableau de bord (compute_widgets, 0 appel API)."""

    @staticmethod
    def _dataset(**overrides):
        from datetime import timedelta
        from normalized_model import build_sources

        now = datetime.now(timezone.utc)
        iso = lambda d: d.isoformat()
        years = lambda y: now - timedelta(days=int(365 * y))

        watched_movies = [
            # Dune vu 2 fois (2 lignes dans un ZIP Trakt) -> exclu du rewatch radar.
            {"movie": {"title": "Dune 2", "year": 2024, "ids": {"tmdb": 1001, "imdb": "tt1"}, "score_average": 84},
             "last_watched_at": iso(years(5)), "plays": 1},
            {"movie": {"title": "Dune 2", "year": 2024, "ids": {"tmdb": 1001, "imdb": "tt1"}, "score_average": 84},
             "last_watched_at": iso(now - timedelta(days=10)), "plays": 1},
            # Inception vu 1 seule fois il y a 4 ans, note publique 8.8 -> candidat.
            {"movie": {"title": "Inception", "year": 2010, "ids": {"tmdb": 1002, "imdb": "tt2"}, "score_average": 88},
             "last_watched_at": iso(years(4)), "plays": 1},
        ]
        watched_shows = [
            {"show": {"title": "Severance", "year": 2022, "ids": {"tmdb": 2001, "imdb": "tt4"}, "status": "returning"},
             "last_watched_at": iso(years(2.5))},           # pause longue
            {"show": {"title": "Breaking Bad", "year": 2008, "ids": {"tmdb": 2002, "imdb": "tt5"}, "status": "ended"},
             "last_watched_at": iso(years(3))},              # terminée -> exclue
            {"show": {"title": "The OA", "year": 2016, "ids": {"tmdb": 2003, "imdb": "tt6"}, "status": "returning"},
             "last_watched_at": iso(years(4))},              # abandonnée -> exclue
            {"show": {"title": "Silo", "year": 2023, "ids": {"tmdb": 2004, "imdb": "tt7"}, "status": "returning"},
             "last_watched_at": iso(now - timedelta(days=3))},
        ]
        episodes = []
        for i in range(5):
            episodes.append({"episode": {"season": 1, "number": i, "title": f"E{i}", "ids": {"tmdb": 90001 + i},
                                         "show": {"title": "Silo", "ids": {"tmdb": 2004}}},
                             "show": {"title": "Silo", "ids": {"tmdb": 2004}},
                             "last_watched_at": f"2024-07-12T{17 + i:02d}:00:00+00:00", "plays": 1, "runtime": 45})
        for i in range(2):
            episodes.append({"episode": {"season": 1, "number": i, "title": f"B{i}", "ids": {"tmdb": 91001 + i},
                                         "show": {"title": "The Bear", "ids": {"tmdb": 2005}}},
                             "show": {"title": "The Bear", "ids": {"tmdb": 2005}},
                             "last_watched_at": "2024-07-12T10:00:00+00:00", "plays": 1, "runtime": 30})

        sections = {
            "watched": {"movies": watched_movies, "shows": watched_shows, "episodes": episodes},
            "ratings": {"movies": [{"movie": {"title": "Dune 2", "year": 2024, "ids": {"tmdb": 1001, "imdb": "tt1"}}, "rating": 9}],
                        "shows": [], "episodes": []},
            "watchlist": {"movies": [{"title": "Interstellar", "year": 2014, "ids": {"tmdb": 3001, "imdb": "tt9"},
                                      "listed_at": iso(now - timedelta(days=800))}], "shows": []},
            "dropped": {"shows": [{"show": {"title": "The OA", "ids": {"tmdb": 2003, "imdb": "tt6"}}}]},
            "user_lists": [{"id": 5, "name": "Films à voir", "type": "static",
                            "movies": [{"title": "Titanic", "year": 1997, "ids": {"tmdb": 4001, "imdb": "tt10"},
                                        "released": (now + timedelta(days=3)).date().isoformat(), "score_average": 79}],
                            "shows": []}],
        }
        dataset = {"source": "mdblist", "sections": sections,
                   "sources": build_sources(sections), "loaded_at": iso(now)}
        dataset.update(overrides)
        return dataset

    def test_rewatch_dedupe_zip(self):
        from dashboard_engine import compute_widgets

        w = compute_widgets(self._dataset(), timezone_name="Europe/Paris")
        titres = [c["titre"] for c in w["rewatch"]]
        self.assertIn("Inception", titres)   # 1 seule vue, il y a 4 ans, pub 8.8
        self.assertNotIn("Dune 2", titres)   # vu 2 fois (ZIP) -> exclu

    def test_pause_longue_filters(self):
        from dashboard_engine import compute_widgets

        w = compute_widgets(self._dataset(), timezone_name="Europe/Paris")
        titres = [c["titre"] for c in w["pause_longue"]]
        self.assertEqual(titres, ["Severance"])          # seule non terminée / non abandonnée
        self.assertNotIn("Breaking Bad", titres)         # statut ended
        self.assertNotIn("The OA", titres)               # dropped

    def test_thermometre_nuance(self):
        from dashboard_engine import compute_widgets

        # Ma note 9 vs public 8.4 -> écart +0.6 : « UN PEU INDULGENT » (plus
        # l'étiquette « 😇 INDULGENT » dès ±0,5 pt de l'ancien site).
        w = compute_widgets(self._dataset(), timezone_name="Europe/Paris")
        sev = w["contre_courant"]["severite"]
        self.assertEqual(sev["label"], "UN PEU INDULGENT")

    def test_records_binge(self):
        from dashboard_engine import compute_widgets

        w = compute_widgets(self._dataset(), timezone_name="Europe/Paris")
        rec = w["records"]
        self.assertEqual(rec["jour"]["date"], datetime(2024, 7, 12).date())  # 5 ép. + 2, en heure de Paris
        self.assertEqual(rec["jour"]["nb"], 7)
        self.assertEqual(rec["mois"]["key"], (2024, 7))

    def test_creneau_prefere(self):
        from dashboard_engine import compute_widgets

        w = compute_widgets(self._dataset(), timezone_name="Europe/Paris")
        self.assertEqual(w["creneau"]["top"]["label"], "Soir")

    def test_sorties_dedupliquees(self):
        from dashboard_engine import compute_widgets

        w = compute_widgets(self._dataset(), timezone_name="Europe/Paris")
        self.assertEqual(len(w["sorties"]), 1)  # une seule fois malgré les sources agrégées


if __name__ == "__main__":
    unittest.main()
