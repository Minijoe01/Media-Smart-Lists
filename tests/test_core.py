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


class TestRecommendationPresets(unittest.TestCase):
    """Presets « Que regarder ? » — nettoyage V111.

    Un preset doit COMBINER plusieurs critères (durée, type, note, profil…).
    Les entrées qui ne dupliquaient qu'un genre ou un style ont été
    supprimées : Envie de rire, Envie de frissons, Adrénaline, Polars &
    thrillers, Science-fiction, Romance, Documentaires, Soirée en famille.
    « Cinéma du monde » reste (pays ≠ USA + note = vraie combinaison).
    """

    def test_cleanup_v111(self):
        from recommendation_engine import PRESET_NAMES, preset_matches

        profile = {"genre_affinity": {}}
        # Les doublons genre/style sont bien partis…
        for gone in (
            "😄 Envie de rire", "😱 Envie de frissons", "💥 Adrénaline",
            "🕵️ Polars & thrillers", "🚀 Science-fiction", "❤️ Romance",
            "🎞️ Documentaires", "👨‍👩‍👧 Soirée en famille",
        ):
            self.assertNotIn(gone, PRESET_NAMES)
        # …les vraies combinaisons restent (chouchous + combos demandées).
        for kept in (
            "🌟 Acteur incontournable", "🏢 Studio préféré",
            "🎥 Réalisateur incontournable", "📚 Suite d'une saga entamée",
            "🌍 Cinéma du monde", "🧭 Hors de ta zone de confort",
            "🍿 Soirée cinéma — grand film bien noté",
        ):
            self.assertIn(kept, PRESET_NAMES)
        # Chaque preset restant a bien une branche de matching (l'appel ne
        # doit jamais retomber sur le « return True » par défaut) : on le
        # vérifie avec une ligne vide qui ne matche RIEN.
        empty_row = {"type": "Film", "runtime": 0, "note": 0.0, "year": 0}
        for name in PRESET_NAMES:
            if name != "Aucun preset":
                self.assertFalse(preset_matches(name, empty_row, profile),
                                 f"preset sans effet (matche tout) : {name}")

    def test_new_presets(self):
        from recommendation_engine import PRESET_NAMES, preset_matches

        profile = {"genre_affinity": {}}
        self.assertIn("🎬 Film marathon — 2h30 et plus", PRESET_NAMES)
        self.assertIn("🌙 Séries à épisodes courts (≤ 30 min)", PRESET_NAMES)
        self.assertIn("♾️ Séries interminables (100+ épisodes)", PRESET_NAMES)

        film_long = {"type": "Film", "runtime": 175, "note": 7.0, "genres": ["Action"]}
        self.assertTrue(preset_matches("🎬 Film marathon — 2h30 et plus", film_long, profile))
        self.assertFalse(preset_matches("🎬 Film marathon — 2h30 et plus",
                                        {"type": "Film", "runtime": 90, "genres": []}, profile))

        serie_courte = {"type": "Série", "runtime": 25, "genres": ["Comédie"]}
        self.assertTrue(preset_matches("🌙 Séries à épisodes courts (≤ 30 min)", serie_courte, profile))

        serie_longue = {"type": "Série", "runtime": 45, "genres": [], "total_episodes": 120}
        self.assertTrue(preset_matches("♾️ Séries interminables (100+ épisodes)", serie_longue, profile))


class TestScoringRatagesProportion(unittest.TestCase):
    """V114 — malus « Tes ratages ici » PROPORTIONNEL (plus de somme).

    Un grand fan d'un genre (3 navets sur 200 notés) ne doit plus être
    pénalisé ; le malus ne tombe que si les notes ≤ 3/10 sont fréquentes
    (≥ 2 ET ≥ 25 % des contenus notés du genre).
    """

    @staticmethod
    def _item():
        return {"kind": "movie", "type": "Film", "title": "Test", "year": 2020,
                "ids": {"tmdb": 1}, "genres": ["Comédie"], "runtime": 100}

    @staticmethod
    def _malus(disappointments, counts):
        from recommendation_engine import score_item
        profile = {"genre_affinity": {}, "personal_genre_ratings": {},
                   "genre_disappointments": disappointments,
                   "genre_rating_counts": counts}
        row = score_item(TestScoringRatagesProportion._item(), profile, source_name="t")
        return any("ratage" in str(s.get("label", "")).lower() for s in row["signals"])

    def test_fan_de_genre_pas_penalise(self):
        # 3 ratages sur 200 comédies notées (1,5 %) → AUCUN malus.
        self.assertFalse(self._malus({"Comédie": 3}, {"Comédie": 200}))

    def test_genre_vraiment_decu_penalise(self):
        # 40 % de très mauvaises notes → malus.
        self.assertTrue(self._malus({"Comédie": 4}, {"Comédie": 10}))
        self.assertTrue(self._malus({"Comédie": 2}, {"Comédie": 5}))

    def test_sous_le_seuil_pas_de_malus(self):
        # 15-20 % de ratages → toléré.
        self.assertFalse(self._malus({"Comédie": 3}, {"Comédie": 20}))
        self.assertFalse(self._malus({"Comédie": 2}, {"Comédie": 10}))

    def test_profil_ancien_sans_compteurs(self):
        # Un profil sans « genre_rating_counts » (ancien cache) ne crash pas.
        self.assertFalse(self._malus({"Comédie": 3}, None))


class TestWrappedFilmsHomonymes(unittest.TestCase):
    """V115 — Mortal Kombat 1995 et 2024 : deux films DIFFÉRENTS.

    Signalé utilisateur : le Wrapped fusionnait les films homonymes (top
    « Mortal Kombat · 2 visionnages » mélangeant 1995 et 2024) et
    sous-comptait les films (titre unique). Désormais : comptage et tops
    par couple (titre, année) ; l'année n'est affichée que si le titre
    est ambigu.
    """

    def test_films_homonymes_separe(self):
        from wrapped_engine import compute_wrapped

        def movie(title, year, watched_at):
            return {"movie": {"title": title, "year": year, "ids": {"tmdb": 1},
                              "runtime": 110},
                    "last_watched_at": watched_at, "plays": 1}

        now = "2026-01-15T20:00:00+00:00"
        watched = {
            "movies": [
                movie("Mortal Kombat", 1995, now),
                movie("Mortal Kombat", 2024, now),
                movie("Film A", 2010, now),
                movie("Film A", 2010, "2026-02-15T20:00:00+00:00"),
                movie("Film sans année", None, now),
            ],
            "episodes": [], "shows": [],
        }
        d = compute_wrapped({"sections": {"watched": watched}}, 2026)
        self.assertEqual(d["films"], 4)  # MK95 + MK24 + Film A + Film sans année
        labels = [t for t, _ in d["top_films"]]
        self.assertIn("Mortal Kombat (1995)", labels)
        self.assertIn("Mortal Kombat (2024)", labels)
        self.assertNotIn("Mortal Kombat", labels)  # jamais sans année si ambigu
        self.assertIn(("Film A", 2), d["top_films"])  # même film : fusionné
        self.assertIn("Film sans année", labels)      # sans année : titre seul


class TestNowPlayingProgress(unittest.TestCase):
    """V117 — progression « lecture en cours » : fraction 0-1 reconnue,
    estimation depuis l'heure de DÉBUT quand le scrobbler ne rapporte pas
    la progression en continu (Kodi sans interval → progress=0 en plein
    milieu d'un film, rapporté par l'utilisateur)."""

    def test_estimation_depuis_debut(self):
        from datetime import datetime, timedelta, timezone
        from playback_engine import normalize_now_playing

        now = datetime(2026, 9, 5, 21, 0, 0, tzinfo=timezone.utc)
        started = (now - timedelta(minutes=55)).isoformat()
        items = [{
            "type": "movie",
            "movie": {"title": "Film", "year": 2024, "ids": {"tmdb": 1}, "runtime": 110},
            "progress": 0,
            "started_at": started,
        }]
        row = normalize_now_playing(items, fetched_at=now.timestamp(),
                                    now_timestamp=now.timestamp())[0]
        self.assertTrue(49 <= row["progress"] <= 51)
        self.assertTrue(row.get("progress_estimated_from_start"))

    def test_fraction_reconnue(self):
        from datetime import datetime, timezone
        from playback_engine import normalize_now_playing, normalize_playback

        items = [{
            "type": "movie",
            "movie": {"title": "F", "year": 2020, "ids": {"tmdb": 2}, "runtime": 100},
            "progress": 0.5,
        }]
        self.assertEqual(normalize_playback(items)[0]["progress"], 50.0)
        now = datetime(2026, 9, 5, tzinfo=timezone.utc)
        row = normalize_now_playing(items, fetched_at=now.timestamp(),
                                    now_timestamp=now.timestamp())[0]
        self.assertAlmostEqual(row["progress"], 50.0, delta=1)

    def test_vraie_progression_et_pause(self):
        from datetime import datetime, timedelta, timezone
        from playback_engine import normalize_now_playing

        now = datetime(2026, 9, 5, 21, 0, 0, tzinfo=timezone.utc)
        started = (now - timedelta(minutes=55)).isoformat()
        base = {"type": "movie",
                "movie": {"title": "F", "year": 2020, "ids": {"tmdb": 3}, "runtime": 100}}
        # Progression réelle rapportée : elle prime sur l'estimation.
        items = [dict(base, progress=40, started_at=started)]
        row = normalize_now_playing(items, fetched_at=now.timestamp(),
                                    now_timestamp=now.timestamp())[0]
        self.assertTrue(39 <= row["progress"] <= 41)
        # En pause : aucune estimation, la valeur rapportée reste intacte.
        items = [dict(base, progress=63, paused_at=started)]
        row = normalize_now_playing(items, fetched_at=now.timestamp(),
                                    now_timestamp=now.timestamp())[0]
        self.assertEqual(row["progress"], 63.0)


class TestDashboardWidgets(unittest.TestCase):
    """Widgets restaurés du tableau de bord (compute_widgets, 0 appel API)."""

    @staticmethod
    def _dataset(**overrides):
        from datetime import timedelta
        from normalized_model import build_progress, build_sources

        now = datetime.now(timezone.utc)
        iso = lambda d: d.isoformat()
        years = lambda y: now - timedelta(days=int(365 * y))

        watched_movies = [
            # Dune vu 2 fois (2 lignes dans un ZIP Trakt) -> exclu du rewatch radar.
            # Heures fixes (20:00 UTC = 22 h à Paris) pour un créneau déterministe.
            {"movie": {"title": "Dune 2", "year": 2024, "ids": {"tmdb": 1001, "imdb": "tt1"}, "score_average": 84},
             "last_watched_at": "2026-08-07T18:00:00+00:00", "plays": 1},
            {"movie": {"title": "Dune 2", "year": 2024, "ids": {"tmdb": 1001, "imdb": "tt1"}, "score_average": 84},
             "last_watched_at": "2021-08-17T18:00:00+00:00", "plays": 1},
            # Inception vu 1 seule fois il y a 4 ans, note publique 8.8 -> candidat.
            {"movie": {"title": "Inception", "year": 2010, "ids": {"tmdb": 1002, "imdb": "tt2"}, "score_average": 88},
             "last_watched_at": "2022-08-18T18:00:00+00:00", "plays": 1},
        ]
        watched_shows = [
            {"show": {"title": "Severance", "year": 2022, "ids": {"tmdb": 2001, "imdb": "tt4"}, "status": "returning"},
             "last_watched_at": iso(years(2.5))},           # pause longue
            {"show": {"title": "Breaking Bad", "year": 2008, "ids": {"tmdb": 2002, "imdb": "tt5"}, "status": "ended"},
             "last_watched_at": iso(years(3))},              # terminée -> exclue
            {"show": {"title": "The OA", "year": 2016, "ids": {"tmdb": 2003, "imdb": "tt6"}, "status": "returning"},
             "last_watched_at": iso(years(4))},              # abandonnée -> exclue
            {"show": {"title": "Lupin", "year": 2021, "ids": {"tmdb": 2006, "imdb": "tt11"}, "status": "returning"},
             "last_watched_at": iso(years(3))},              # vue EN ENTIER, absente d'Up Next -> exclue
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
            # Up Next : Severance et Silo ont encore des épisodes à voir ;
            # Lupin (vue en entier) n'y figure pas -> exclue de la pause longue.
            "upnext": [
                {"show": {"title": "Severance", "ids": {"tmdb": 2001, "imdb": "tt4"}},
                 "next_episode": {"season": 2, "number": 1, "air_date": "2026-09-01"},
                 "progress": {"watched_episode_count": 9, "total_episode_count": 10}},
                {"show": {"title": "Silo", "ids": {"tmdb": 2004, "imdb": "tt7"}},
                 "next_episode": {"season": 2, "number": 5, "air_date": "2026-08-20"},
                 "progress": {"watched_episode_count": 9, "total_episode_count": 10}},
            ],
            "user_lists": [{"id": 5, "name": "Films à voir", "type": "static",
                            "movies": [{"title": "Titanic", "year": 1997, "ids": {"tmdb": 4001, "imdb": "tt10"},
                                        "released": (now + timedelta(days=3)).date().isoformat(), "score_average": 79}],
                            "shows": []}],
        }
        dataset = {"source": "mdblist", "sections": sections,
                   "sources": build_sources(sections),
                   "progress": build_progress(sections), "loaded_at": iso(now)}
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

        # Ma note 9 vs public 8.4 -> écart +0.6 : « PLUTÔT INDULGENT » (plus
        # l'étiquette « 😇 INDULGENT » dès ±0,5 pt de l'ancien site).
        w = compute_widgets(self._dataset(), timezone_name="Europe/Paris")
        sev = w["contre_courant"]["severite"]
        self.assertEqual(sev["label"], "PLUTÔT INDULGENT")

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
