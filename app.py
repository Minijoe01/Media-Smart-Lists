"""Media Smart Lists — coque visuelle fournisseur-neutre.

Étape 3 : restauration du thème Aston Martin et de la navigation historique.
Aucun secret et aucun appel distant à ce stade.
"""

from __future__ import annotations

import os
import time
from html import escape

import streamlit as st
from streamlit_cookies_controller import CookieController

import mdblist_oauth as mdb_oauth
from mdblist_provider import MDBListProvider


APP_NAME = "Media Smart Lists"
APP_VERSION = "0.6.1-alpha"

PAGES = [
    "🏠 Tableau de bord",
    "▶️ En cours de lecture",
    "👻 Progression Fantôme",
    "🧹 Nettoyage des listes",
    "🔍 Recherche de doublons",
    "🎯 Que regarder ?",
    "📅 Calendrier des sorties",
    "📊 Statistiques",
    "🎬 Rendez-vous annuel",
    "🏆 Succès",
    "📤 Sauvegarde",
]

st.set_page_config(
    page_title=APP_NAME,
    page_icon=("logo.png" if os.path.exists("logo.png") else "🎬"),
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @font-face {
        font-family: 'ManropeMSL';
        src: url('app/static/fonts/Manrope-ExtraBold.ttf');
        font-weight: 800 900;
        font-display: swap;
    }

    :root {
        --am-green: #00A392;
        --am-green-aston: #00524B;
        --am-green-dark: #021412;
        --am-lime: #CEDC00;
        --am-yellow: #FFFF00;
        --am-mint: #00D084;
        --am-bg-card: rgba(8, 55, 50, 0.75);
        --am-bg-card-hover: rgba(12, 75, 68, 0.85);
        --am-border: rgba(18, 90, 84, 0.5);
        --am-text: #F0FAF8;
        --am-text-muted: #9DC5BF;
    }

    footer {visibility: hidden;}
    .block-container {
        max-width: 1240px;
        padding-top: 3.3rem !important;
        padding-bottom: 4rem !important;
    }

    /* Dégradé original : clair en haut-centre, plus sombre vers les bords et le bas. */
    .stApp {
        background: radial-gradient(
            ellipse 100% 85% at 50% 0%,
            #006B62 0%,
            #005951 28%,
            #00443E 55%,
            #002B28 80%,
            #011715 100%
        ) !important;
        background-attachment: fixed !important;
        min-height: 100vh;
    }

    header[data-testid="stHeader"] {
        background: rgba(2, 20, 18, 0.70) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border-bottom: 1px solid var(--am-border) !important;
        box-shadow: none !important;
    }

    section[data-testid="stSidebar"] {
        background: rgba(2, 20, 18, 0.96) !important;
        backdrop-filter: blur(22px) !important;
        border-right: 1px solid var(--am-border) !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label {
        padding: 12px 16px !important;
        border-radius: 12px !important;
        gap: 12px !important;
        transition: all 0.2s ease !important;
        color: var(--am-text-muted) !important;
        font-weight: 500 !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label:hover {
        background: rgba(0,163,146,0.10) !important;
        color: var(--am-text) !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label:has(input:checked) {
        background: linear-gradient(135deg, rgba(0,102,95,0.30), rgba(0,77,72,0.25)) !important;
        color: var(--am-text) !important;
        font-weight: 700 !important;
        border: 1px solid rgba(0,163,146,0.40) !important;
    }

    .section-menu-title {
        color: var(--am-green);
        font-size: .75rem;
        font-weight: 800;
        letter-spacing: 1.5px;
        margin: 20px 0 12px;
        text-transform: uppercase;
    }
    .sidebar-brand {
        color: var(--am-text-muted);
        font-size: .82rem;
        line-height: 1.4;
        padding: 10px 5px 0;
    }

    .brand-title {
        color: var(--am-lime);
        font-family: 'ManropeMSL', 'DejaVu Sans', sans-serif;
        font-size: clamp(1.75rem, 4vw, 2.55rem);
        font-weight: 900;
        line-height: 1;
        margin: .35rem 0 .3rem;
    }
    .brand-rule {
        background: linear-gradient(90deg, var(--am-green), var(--am-lime));
        border-radius: 2px;
        height: 3px;
        max-width: 330px;
    }
    .brand-kicker {
        color: var(--am-lime);
        font-family: 'ManropeMSL', 'DejaVu Sans', sans-serif;
        font-size: .80rem;
        font-weight: 900;
        letter-spacing: .16em;
        margin-bottom: .45rem;
        text-transform: uppercase;
    }

    .accent-callout {
        background: linear-gradient(135deg, rgba(206,220,0,.13), rgba(0,163,146,.08));
        border: 1px solid rgba(206,220,0,.42);
        border-left: 4px solid var(--am-lime);
        border-radius: 13px;
        color: var(--am-text);
        font-size: .88rem;
        line-height: 1.45;
        margin: .55rem 0 .9rem;
        padding: .62rem .85rem;
    }
    .accent-callout strong {
        color: var(--am-lime);
        font-family: 'ManropeMSL', 'DejaVu Sans', sans-serif;
        font-size: .76rem;
        font-weight: 800;
        letter-spacing: .09em;
    }

    .page-title {
        color: var(--am-text);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        font-size: 1.48rem;
        font-weight: 650;
        letter-spacing: -.025em;
        line-height: 1.25;
        margin: .15rem 0 .25rem;
    }
    .wordmark-wrap img {
        display: block;
        height: auto;
        margin: 0 0 .35rem 0;
        max-width: 100%;
        width: min(300px, 62vw);
    }

    .source-card, .placeholder-card {
        background: var(--am-bg-card);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid var(--am-border);
        border-radius: 16px;
        box-shadow: none !important;
        margin-bottom: .8rem;
        padding: 1.2rem 1.25rem;
    }
    .source-card { min-height: 185px; }
    .source-card h3 {
        color: var(--am-text);
        margin: .45rem 0 .5rem;
    }
    .placeholder-card h3 {
        color: var(--am-lime);
        font-family: 'ManropeMSL', 'DejaVu Sans', sans-serif;
        font-weight: 900;
        margin: .45rem 0 .5rem;
    }
    .source-card p, .placeholder-card p {
        color: var(--am-text-muted);
    }
    .media-list-card {
        align-items: center;
        background: rgba(8, 55, 50, .62);
        border: 1px solid var(--am-border);
        border-left: 3px solid var(--am-green);
        border-radius: 13px;
        color: var(--am-text);
        display: flex;
        gap: .82rem;
        margin: .45rem 0;
        min-height: 74px;
        padding: .68rem .82rem;
    }
    .media-list-card.upnext-card {
        border-left: 4px solid var(--am-lime);
    }
    .media-list-card img {
        border-radius: 8px;
        height: 76px;
        object-fit: cover;
        width: 52px;
    }
    .media-list-content {
        min-width: 0;
    }
    .media-list-card strong {
        color: var(--am-text);
        font-weight: 700;
    }
    .media-list-card span {
        color: var(--am-text-muted);
    }
    .media-list-card small {
        color: var(--am-text-muted);
        display: block;
        font-size: .78rem;
        margin-top: .28rem;
    }

    .source-badge {
        background: rgba(206,220,0,.12);
        border: 1px solid rgba(206,220,0,.42);
        border-radius: 999px;
        color: var(--am-lime);
        display: inline-block;
        font-size: .72rem;
        font-weight: 800;
        padding: .24rem .55rem;
    }

    /* Boutons historiques : verre vert, sans ombre. */
    .stButton > button,
    div[data-testid="stButton"] > button,
    div[data-testid="stDownloadButton"] > button,
    div[data-testid="stFormSubmitButton"] > button {
        background: rgba(5, 38, 34, 0.75) !important;
        border: 1px solid rgba(0,163,146,0.30) !important;
        border-radius: 16px !important;
        box-shadow: none !important;
        color: var(--am-text) !important;
        font-weight: 600 !important;
        min-height: 3rem;
        padding: .75em 1.3em !important;
        text-shadow: none !important;
        width: 100% !important;
    }
    .stButton > button:hover,
    div[data-testid="stButton"] > button:hover,
    div[data-testid="stDownloadButton"] > button:hover,
    div[data-testid="stFormSubmitButton"] > button:hover {
        background: rgba(8, 55, 50, 0.85) !important;
        border-color: rgba(0,163,146,0.50) !important;
        box-shadow: none !important;
    }
    .stButton > button[kind="primary"],
    div[data-testid="stButton"] > button[kind="primary"] {
        background: linear-gradient(135deg, var(--am-green), var(--am-green-aston)) !important;
        border: none !important;
        color: #fff !important;
        font-weight: 700 !important;
    }
    .stButton > button[kind="primary"]:hover,
    div[data-testid="stButton"] > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #00B8A5, #006058) !important;
    }

    div[data-testid="stMetric"] {
        background: var(--am-bg-card) !important;
        border: 1px solid var(--am-border) !important;
        border-radius: 16px !important;
        box-shadow: none !important;
        min-height: 112px;
        padding: 18px 15px !important;
    }
    div[data-testid="stMetricValue"] {
        color: var(--am-text) !important;
        font-size: 1.25rem !important;
        font-weight: 750 !important;
    }
    div[data-testid="stMetricLabel"] p {
        color: var(--am-text-muted) !important;
        font-size: .84rem !important;
    }

    div[data-testid="stAlert"] {
        background: rgba(8, 55, 50, .55) !important;
        border: 1px solid rgba(255,255,255,.08) !important;
        border-radius: 16px !important;
        box-shadow: none !important;
        color: var(--am-text) !important;
    }
    hr { border-color: var(--am-border) !important; }
    p, li, label { color: var(--am-text) !important; }
    .stCaption { color: var(--am-text-muted) !important; }

    @media (max-width: 768px) {
        .block-container { padding-top: 2.5rem !important; }
        .brand-title { font-size: 1.7rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# Une seule instance par session/app, comme dans Trakt Smart Lists.
cookies = CookieController()


def navigation() -> str:
    if "page_active" not in st.session_state:
        st.session_state["page_active"] = PAGES[0]
    with st.sidebar:
        st.markdown('<p class="section-menu-title">Menu</p>', unsafe_allow_html=True)
        page = st.radio(
            "Navigation",
            PAGES,
            index=PAGES.index(st.session_state["page_active"]),
            label_visibility="collapsed",
            key="nav",
        )
        st.markdown(
            '<div class="sidebar-brand">🍿 MDBList en temps réel<br>📦 Export ZIP Trakt en lecture seule</div>',
            unsafe_allow_html=True,
        )
    st.session_state["page_active"] = page
    return page


def header() -> None:
    wordmark_path = os.path.join("static", "wordmark.png")
    if os.path.exists(wordmark_path):
        # Même solution que l'app legacy : fichier statique servi directement,
        # sans redimensionnement raster de st.image (plus net sur PC et mobile).
        st.markdown(
            "<div class='wordmark-wrap'>"
            "<img src='app/static/wordmark.png' alt='Media Smart Lists'>"
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown('<div class="brand-title">Media Smart Lists</div>', unsafe_allow_html=True)
        st.markdown('<div class="brand-rule"></div>', unsafe_allow_html=True)
    st.markdown("<div style='height:.45rem'></div>", unsafe_allow_html=True)


def _render_connected_mdblist() -> None:
    account = mdb_oauth.account_summary()
    lists_summary = mdb_oauth.lists_summary()
    if not account:
        loaded, message = mdb_oauth.load_account_summary(cookies)
        if not loaded:
            st.markdown(
                f'<div class="accent-callout"><strong>CONNEXION ACTIVE</strong> · {escape(message)}</div>',
                unsafe_allow_html=True,
            )
            return
        account = mdb_oauth.account_summary()
        lists_summary = mdb_oauth.lists_summary()

    st.markdown(
        f'<div class="accent-callout"><strong>✓ CONNECTÉ À MDBLIST</strong> · '
        f'{escape(str(account.get("username") or "Compte MDBList"))}</div>',
        unsafe_allow_html=True,
    )
    cols = st.columns(4)
    cols[0].metric("Forfait", account.get("plan") or "—")
    remaining = account.get("rate_limit_remaining")
    limit = account.get("rate_limit")
    cols[1].metric(
        "Quota restant",
        f"{remaining}/{limit}" if remaining is not None and limit else "—",
    )
    cols[2].metric("Listes actuelles", lists_summary.get("total", 0))
    cols[3].metric("Limite de listes", account.get("list_limit") or "—")
    st.caption(
        f"Listes statiques : {lists_summary.get('static', 0)} · "
        f"dynamiques : {lists_summary.get('dynamic', 0)} · "
        "valeurs conservées pour une reconnexion instantanée"
    )
    refresh_col, disconnect_col = st.columns(2)
    with refresh_col:
        if st.button("Actualiser les compteurs", type="primary", key="refresh_mdblist_summary"): 
            with st.spinner("Actualisation MDBList…"):
                mdb_oauth.load_account_summary(cookies)
            st.rerun()
    with disconnect_col:
        if st.button("Se déconnecter de MDBList", type="primary", key="disconnect_mdblist"): 
            with st.spinner("Déconnexion et révocation MDBList…"):
                mdb_oauth.disconnect(cookies)
            st.session_state["pending_source"] = "mdblist"
            st.rerun()


def _render_device_flow(flow: dict) -> None:
    complete_url = str(flow.get("verification_uri_complete") or "")
    verification_uri = str(flow.get("verification_uri") or "https://mdblist.com/oauth/device/")
    user_code = str(flow.get("user_code") or "")
    safe_url = escape(complete_url, quote=True)
    safe_verification_uri = escape(verification_uri, quote=True)
    safe_code = escape(user_code)

    left, right = st.columns(2, gap="large")
    with left:
        st.markdown(
            f'<a href="{safe_url}" target="_blank" rel="noopener noreferrer" '
            'style="display:inline-block; background:linear-gradient(135deg,#00A392,#00524B); '
            'color:white; padding:.9em 1.7em; border-radius:12px; text-decoration:none; '
            'font-weight:700;">Autoriser l\'accès MDBList</a>',
            unsafe_allow_html=True,
        )
        st.caption("Sur ce navigateur ou n’importe quel autre appareil.")
        st.markdown(
            f'<div class="accent-callout"><strong>SANS SMARTPHONE</strong> · '
            f'Ouvre <a href="{safe_verification_uri}" target="_blank" rel="noopener noreferrer" '
            f'style="color:#CEDC00;font-weight:700;">{safe_verification_uri}</a> '
            'depuis un navigateur, puis saisis le code ci-dessous.</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="accent-callout"><strong>CODE MDBLIST</strong> · '
            f'<span style="color:#CEDC00;font-size:1.18rem;font-weight:800;letter-spacing:3px;">'
            f'{safe_code}</span></div>',
            unsafe_allow_html=True,
        )
    with right:
        if complete_url:
            st.image(mdb_oauth.qr_png(complete_url), width=160)
            st.caption("Ou scanne le QR code avec ton téléphone.")

    st.caption("La page vérifie automatiquement l’autorisation, comme Trakt Smart Lists.")
    status_box = st.empty()
    interval = max(int(flow.get("interval") or 5), 5)
    expires_at = int(flow.get("expires_at") or 0)

    with st.spinner("Attente de l’autorisation MDBList…"):
        while time.time() < expires_at:
            remaining = max(expires_at - int(time.time()), 0)
            status_box.caption(f"Code valable encore {remaining // 60}:{remaining % 60:02d}")
            time.sleep(interval)
            status, payload = mdb_oauth.poll_device_once(flow)
            if status == "success" and isinstance(payload, dict):
                mdb_oauth.save_tokens(cookies, payload)
                mdb_oauth.clear_flow()
                mdb_oauth.load_account_summary(cookies)
                st.rerun()
            if status == "slow_down":
                interval += 5
                continue
            if status in {"expired", "denied", "error"}:
                mdb_oauth.clear_flow()
                st.markdown(
                    f'<div class="accent-callout"><strong>CONNEXION NON TERMINÉE</strong> · '
                    f'{escape(str(payload))}</div>',
                    unsafe_allow_html=True,
                )
                return

    mdb_oauth.clear_flow()
    st.markdown(
        '<div class="accent-callout"><strong>CODE EXPIRÉ</strong> · Relance une nouvelle connexion.</div>',
        unsafe_allow_html=True,
    )


def render_mdblist_connector() -> None:
    configured, config_message = mdb_oauth.configured()
    if not configured:
        st.markdown(
            f'<div class="accent-callout"><strong>CONFIGURATION INCOMPLÈTE</strong> · '
            f'{escape(config_message)}</div>',
            unsafe_allow_html=True,
        )
        return

    if mdb_oauth.is_connected():
        _render_connected_mdblist()
        return

    flow = mdb_oauth.current_flow()
    if flow:
        _render_device_flow(flow)
        return

    st.markdown(
        '<div class="accent-callout"><strong>OAUTH DEVICE CODE</strong> · '
        'Aucune clé API à chercher ou à saisir. MDBList affichera la demande d’autorisation.</div>',
        unsafe_allow_html=True,
    )
    if st.button("Se connecter avec MDBList", type="primary", key="start_mdblist_oauth"):
        with st.spinner("Création du code MDBList…"):
            started, message = mdb_oauth.start_device_flow()
        if started:
            st.rerun()
        else:
            st.markdown(
                f'<div class="accent-callout"><strong>CONNEXION IMPOSSIBLE</strong> · '
                f'{escape(message)}</div>',
                unsafe_allow_html=True,
            )


def _dataset() -> dict:
    value = st.session_state.get("_normalized_dataset")
    return value if isinstance(value, dict) else {}


def _sections() -> dict:
    value = _dataset().get("sections")
    return value if isinstance(value, dict) else {}


def _media_title(item: dict) -> str:
    if not isinstance(item, dict):
        return "Titre inconnu"
    for key in ("title", "name"):
        if item.get(key):
            return str(item[key])
    for key in ("movie", "show", "episode"):
        nested = item.get(key)
        if isinstance(nested, dict):
            return str(nested.get("title") or nested.get("name") or "Titre inconnu")
    return "Titre inconnu"


def _media_year(item: dict) -> str:
    if not isinstance(item, dict):
        return ""
    value = item.get("release_year") or item.get("year")
    if value:
        return str(value)
    for key in ("movie", "show"):
        nested = item.get(key)
        if isinstance(nested, dict) and nested.get("year"):
            return str(nested["year"])
    return ""


def _genres(item: dict) -> list[str]:
    values = item.get("genres") if isinstance(item, dict) else []
    if not values:
        for key in ("movie", "show"):
            nested = item.get(key) if isinstance(item, dict) else None
            if isinstance(nested, dict) and nested.get("genres"):
                values = nested["genres"]
                break
    output = []
    for value in values or []:
        if isinstance(value, dict):
            value = value.get("name") or value.get("slug")
        if value:
            output.append(str(value).strip().title())
    return sorted(set(output))


def _poster_url(item: dict) -> str:
    if not isinstance(item, dict):
        return ""
    value = item.get("poster") or item.get("poster_path") or ""
    if not value:
        for key in ("movie", "show", "episode"):
            nested = item.get(key)
            if isinstance(nested, dict):
                value = nested.get("poster") or nested.get("poster_path") or ""
                if value:
                    break
    value = str(value or "").strip()
    if not value:
        return ""
    if value.startswith("http://") or value.startswith("https://"):
        return value
    if not value.startswith("/"):
        value = "/" + value
    return f"https://image.tmdb.org/t/p/w342{value}"


def _score(item: dict) -> str:
    if not isinstance(item, dict):
        return ""
    value = item.get("score") or item.get("score_average")
    try:
        return str(int(round(float(value)))) if value is not None else ""
    except (TypeError, ValueError):
        return ""


def load_mdblist_dataset() -> None:
    valid, message = mdb_oauth.ensure_valid_session(cookies)
    if not valid:
        st.markdown(
            f'<div class="accent-callout"><strong>SESSION INDISPONIBLE</strong> · '
            f'{escape(message or "Reconnecte MDBList.")}</div>',
            unsafe_allow_html=True,
        )
        return
    try:
        provider = MDBListProvider(mdb_oauth.access_token())
        data = provider.load_dataset()
    except Exception:
        st.markdown(
            '<div class="accent-callout"><strong>LECTURE IMPOSSIBLE</strong> · '
            'MDBList n’a pas pu charger les données pour le moment.</div>',
            unsafe_allow_html=True,
        )
        return
    st.session_state["_normalized_dataset"] = data
    account = mdb_oauth.account_summary()
    if data.get("rate_limit_remaining") is not None and account:
        account["rate_limit_remaining"] = data["rate_limit_remaining"]
        st.session_state[mdb_oauth.ACCOUNT_KEY] = account
        mdb_oauth.persist_cookie(cookies)


def render_data_loader() -> None:
    if not mdb_oauth.is_connected():
        return
    data = _dataset()
    label = "Actualiser mes données MDBList" if data else "Charger mes données MDBList"
    if st.button(label, type="primary", key="load_mdblist_dataset"):
        with st.spinner("Chargement MDBList en lecture seule…"):
            load_mdblist_dataset()
        st.rerun()
    if data:
        errors = data.get("errors") or []
        request_count = data.get("request_count", 0)
        loaded_at = str(data.get("loaded_at") or "").replace("T", " ").replace("Z", " UTC")
        st.caption(f"Données chargées : {loaded_at} · {request_count} requête(s) API")
        if errors:
            st.markdown(
                f'<div class="accent-callout"><strong>CHARGEMENT PARTIEL</strong> · '
                f'{len(errors)} section(s) indisponible(s). Les autres restent utilisables.</div>',
                unsafe_allow_html=True,
            )


def render_dataset_overview() -> None:
    sections = _sections()
    if not sections:
        return
    watched = sections.get("watched") or {}
    watchlist = sections.get("watchlist") or {}
    ratings = sections.get("ratings") or {}
    lists = sections.get("static_lists") or []
    playback = sections.get("playback") or []
    dropped = sections.get("dropped") or {}

    first = st.columns(4)
    first[0].metric("Films vus", len(watched.get("movies") or []))
    first[1].metric("Épisodes vus", len(watched.get("episodes") or []))
    first[2].metric(
        "Watchlist",
        len(watchlist.get("movies") or []) + len(watchlist.get("shows") or []),
    )
    first[3].metric("Listes statiques", len(lists))

    second = st.columns(4)
    second[0].metric(
        "Notes",
        sum(len(ratings.get(key) or []) for key in ("movies", "shows", "seasons", "episodes")),
    )
    second[1].metric("Reprises", len(playback))
    second[2].metric("Séries abandonnées", len(dropped.get("shows") or []))
    second[3].metric("Up Next", len(sections.get("upnext") or []))


def render_watchlist_page() -> None:
    st.markdown('<div class="page-title">🎯 Que regarder ?</div>', unsafe_allow_html=True)
    sections = _sections()
    base_watchlist = sections.get("watchlist") or {}
    base_items = list(base_watchlist.get("movies") or []) + list(base_watchlist.get("shows") or [])
    if not base_items:
        st.markdown(
            '<div class="accent-callout"><strong>WATCHLIST NON CHARGÉE</strong> · '
            'Connecte MDBList puis charge les données depuis le Tableau de bord.</div>',
            unsafe_allow_html=True,
        )
        return

    genre_records = sections.get("genres") or []
    genre_by_title = {
        str(item.get("title") or item.get("slug") or ""): str(item.get("slug") or "")
        for item in genre_records
        if isinstance(item, dict) and item.get("slug")
    }
    genre_titles = sorted([title for title in genre_by_title if title], key=str.casefold)

    filter_col, type_col, limit_col = st.columns(3)
    selected_genre = filter_col.selectbox("Genre", ["Tous"] + genre_titles, key="watchlist_genre")
    media_type = type_col.selectbox("Type", ["Tous", "Films", "Séries"], key="watchlist_type")
    display_limit = limit_col.selectbox("Afficher", [20, 50, 100], key="watchlist_limit")

    items = base_items
    api_extra = False
    if selected_genre != "Tous":
        slug = genre_by_title.get(selected_genre, selected_genre.lower())
        cache = st.session_state.setdefault("_watchlist_genre_cache", {})
        filtered_response = cache.get(slug)
        if not isinstance(filtered_response, dict):
            valid, message = mdb_oauth.ensure_valid_session(cookies)
            if not valid:
                st.markdown(
                    f'<div class="accent-callout"><strong>SESSION INDISPONIBLE</strong> · '
                    f'{escape(message or "Reconnecte MDBList.")}</div>',
                    unsafe_allow_html=True,
                )
                return
            try:
                provider = MDBListProvider(mdb_oauth.access_token())
                with st.spinner(f"Filtrage MDBList : {selected_genre}…"):
                    filtered_response = provider.watchlist(slug)
                cache[slug] = filtered_response
                st.session_state["_watchlist_genre_cache"] = cache
                account = mdb_oauth.account_summary()
                if provider.rate_limit_remaining is not None and account:
                    account["rate_limit_remaining"] = provider.rate_limit_remaining
                    st.session_state[mdb_oauth.ACCOUNT_KEY] = account
                    mdb_oauth.persist_cookie(cookies)
                api_extra = True
            except Exception:
                st.markdown(
                    '<div class="accent-callout"><strong>FILTRE INDISPONIBLE</strong> · '
                    'MDBList n’a pas pu filtrer cette Watchlist.</div>',
                    unsafe_allow_html=True,
                )
                return
        items = list(filtered_response.get("movies") or []) + list(filtered_response.get("shows") or [])

    filtered = []
    for item in items:
        item_type = str(item.get("mediatype") or "")
        if media_type == "Films" and item_type not in {"movie", "movies"}:
            continue
        if media_type == "Séries" and item_type not in {"show", "tv", "series"}:
            continue
        filtered.append(item)

    source_note = (
        "1 requête MDBList, résultat maintenant mémorisé pour cette session"
        if api_extra else
        ("résultat MDBList mémorisé pour cette session" if selected_genre != "Tous" else "aucun appel API supplémentaire")
    )
    st.markdown(
        f'<div class="accent-callout"><strong>{len(filtered)} RÉSULTAT(S)</strong> · '
        f'{escape(source_note)}.</div>',
        unsafe_allow_html=True,
    )

    columns = st.columns(2)
    for index, item in enumerate(filtered[:display_limit]):
        title = escape(_media_title(item))
        year = escape(_media_year(item))
        item_genres = _genres(item)
        genre_text = " · ".join(item_genres) if item_genres else (
            selected_genre if selected_genre != "Tous" else "Watchlist MDBList"
        )
        poster = escape(_poster_url(item), quote=True)
        image_html = f'<img src="{poster}" alt="" loading="lazy">' if poster else ""
        score = _score(item)
        score_html = f" · MDB Score {score}/100" if score else ""
        with columns[index % 2]:
            st.markdown(
                f'<div class="media-list-card">{image_html}<div class="media-list-content">'
                f'<strong>{title}</strong><span>{(" (" + year + ")") if year else ""}</span>'
                f'<small>{escape(genre_text)}{score_html}</small></div></div>',
                unsafe_allow_html=True,
            )
    if len(filtered) > display_limit:
        st.caption(f"{len(filtered) - display_limit} résultat(s) supplémentaire(s) masqué(s).")


def render_progress_page() -> None:
    st.markdown('<div class="page-title">▶️ En cours de lecture</div>', unsafe_allow_html=True)
    sections = _sections()
    playback = sections.get("playback") or []
    upnext = sections.get("upnext") or []
    dropped = (sections.get("dropped") or {}).get("shows") or []
    if not _dataset():
        st.markdown(
            '<div class="accent-callout"><strong>DONNÉES NON CHARGÉES</strong> · '
            'Charge MDBList depuis le Tableau de bord.</div>',
            unsafe_allow_html=True,
        )
        return
    cols = st.columns(3)
    cols[0].metric("Points de reprise", len(playback))
    cols[1].metric("Prochains épisodes", len(upnext))
    cols[2].metric("Séries abandonnées", len(dropped))

    st.markdown("### Prochains épisodes")
    if not upnext:
        st.caption("Aucun épisode Up Next disponible.")
    for item in upnext[:20]:
        show = item.get("show") or {}
        episode = item.get("next_episode") or {}
        title = escape(str(show.get("title") or "Série"))
        season = episode.get("season")
        number = episode.get("episode")
        ep_title = escape(str(episode.get("title") or ""))
        poster = escape(_poster_url(show), quote=True)
        image_html = f'<img src="{poster}" alt="" loading="lazy">' if poster else ""
        st.markdown(
            f'<div class="media-list-card upnext-card">{image_html}'
            f'<div class="media-list-content"><strong>{title}</strong>'
            f'<span> · S{int(season or 0):02d}E{int(number or 0):02d}</span><br>'
            f'<small>{ep_title}</small></div></div>',
            unsafe_allow_html=True,
        )

    if dropped:
        st.markdown("### Séries abandonnées")
        st.caption("Statut MDBList Dropped — lecture seule dans cette étape.")
        for item in dropped[:30]:
            st.markdown(
                f'<div class="media-list-card"><strong>{escape(_media_title(item))}</strong></div>',
                unsafe_allow_html=True,
            )


def render_static_lists_page() -> None:
    st.markdown('<div class="page-title">🧹 Nettoyage des listes</div>', unsafe_allow_html=True)
    lists = _sections().get("static_lists") or []
    if not lists:
        st.markdown(
            '<div class="accent-callout"><strong>LISTES NON CHARGÉES</strong> · '
            'Charge MDBList depuis le Tableau de bord.</div>',
            unsafe_allow_html=True,
        )
        return
    st.markdown(
        '<div class="accent-callout"><strong>LECTURE SEULE</strong> · '
        'Aucune suppression ou modification de liste à cette étape.</div>',
        unsafe_allow_html=True,
    )
    for item in lists:
        movies = item.get("movies") or []
        shows = item.get("shows") or []
        st.markdown(
            f'<div class="media-list-card"><strong>{escape(str(item.get("name") or "Liste"))}</strong>'
            f'<small>{len(movies)} film(s) · {len(shows)} série(s)</small></div>',
            unsafe_allow_html=True,
        )


def render_basic_stats_page() -> None:
    st.markdown('<div class="page-title">📊 Statistiques</div>', unsafe_allow_html=True)
    if not _dataset():
        st.markdown(
            '<div class="accent-callout"><strong>STATISTIQUES NON CHARGÉES</strong> · '
            'Charge MDBList depuis le Tableau de bord.</div>',
            unsafe_allow_html=True,
        )
        return
    render_dataset_overview()
    st.markdown(
        '<div class="accent-callout"><strong>PREMIÈRE BASE MDBLIST</strong> · '
        'Les graphiques, filtres temporels et statistiques legacy seront reconnectés progressivement.</div>',
        unsafe_allow_html=True,
    )


def page_dashboard() -> None:
    st.markdown('<div class="page-title">🏠 Tableau de bord</div>', unsafe_allow_html=True)
    if not st.session_state.get("pending_source") and not mdb_oauth.is_connected():
        st.markdown(
            '<div class="accent-callout"><strong>CHOISIS TA SOURCE</strong> · '
            'Aucun identifiant ni fichier n’est encore envoyé.</div>',
            unsafe_allow_html=True,
        )
    mdb_col, zip_col = st.columns(2, gap="large")
    with mdb_col:
        st.markdown(
            """
            <div class="source-card">
                <span class="source-badge">TEMPS RÉEL · LECTURE/ÉCRITURE</span>
                <h3>🔗 Connecter MDBList</h3>
                <p>Historique, Watchlist filtrable par genre, notes, listes, progression et séries abandonnées.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Préparer la connexion MDBList", type="primary", key="choose_mdblist"):
            st.session_state["pending_source"] = "mdblist"
    with zip_col:
        st.markdown(
            """
            <div class="source-card">
                <span class="source-badge">IMPORT LOCAL · LECTURE SEULE</span>
                <h3>📦 Importer un ZIP Trakt</h3>
                <p>Historique complet, rewatches, Watchlist, notes et listes, sans accès à l'API Trakt.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Préparer l'import ZIP Trakt", type="primary", key="choose_zip"):
            st.session_state["pending_source"] = "trakt_zip"

    if st.session_state.get("pending_source") == "mdblist":
        st.divider()
        st.markdown('<div class="page-title">🔐 Connexion MDBList</div>', unsafe_allow_html=True)
        render_mdblist_connector()
    elif st.session_state.get("pending_source") == "trakt_zip":
        st.markdown(
            '<div class="accent-callout"><strong>✓ ZIP TRAKT SÉLECTIONNÉ</strong> · '
            'Le parseur sécurisé sera ajouté à l’étape suivante.</div>',
            unsafe_allow_html=True,
        )

    if mdb_oauth.is_connected():
        st.divider()
        st.markdown('<div class="page-title">📥 Données MDBList</div>', unsafe_allow_html=True)
        render_data_loader()
        render_dataset_overview()

    st.divider()
    st.markdown("### Aperçu des possibilités conservées")
    cols = st.columns(4)
    for column, icon, title, text in (
        (cols[0], "📺", "Progression", "Séries en cours et épisodes suivants"),
        (cols[1], "🎯", "Recommandations", "Filtres, genres et choix du soir"),
        (cols[2], "📊", "Statistiques", "Habitudes, rythmes et Wrapped"),
        (cols[3], "🧹", "Listes", "Doublons et nettoyage prudent"),
    ):
        with column:
            st.markdown(f"#### {icon} {title}")
            st.caption(text)


def placeholder(page: str) -> None:
    st.markdown(f'<div class="page-title">{page}</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="placeholder-card">
            <h3>Module conservé dans la feuille de route</h3>
            <p>
                La mise en forme et l'entrée de menu sont déjà restaurées.
                Le calcul de ce module sera reconnecté au même modèle de données pour MDBList et ZIP Trakt.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="accent-callout"><strong>MODE SÛR</strong> · '
        'Aucune donnée distante n’est appelée à cette étape du refactor.</div>',
        unsafe_allow_html=True,
    )


restored, _restore_message = mdb_oauth.ensure_valid_session(cookies)
if restored:
    st.session_state["pending_source"] = "mdblist"
    if not mdb_oauth.account_summary():
        mdb_oauth.load_account_summary(cookies)

page = navigation()
header()
if page == "🏠 Tableau de bord":
    page_dashboard()
elif page == "▶️ En cours de lecture":
    render_progress_page()
elif page == "🧹 Nettoyage des listes":
    render_static_lists_page()
elif page == "🎯 Que regarder ?":
    render_watchlist_page()
elif page == "📊 Statistiques":
    render_basic_stats_page()
else:
    placeholder(page)

st.caption(f"{APP_NAME} · {APP_VERSION} · aucun accès Trakt requis")
