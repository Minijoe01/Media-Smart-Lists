"""Media Smart Lists — interface commune MDBList et exports locaux.

Le thème legacy, les calculs personnels et les contrôles En cours sont conservés.
Les secrets et jetons OAuth ne sont jamais intégrés au code source.
"""

from __future__ import annotations

import os
import random
import time
from datetime import date, datetime, timedelta
from html import escape
from urllib.parse import quote
from zoneinfo import ZoneInfo

import streamlit as st
from streamlit_cookies_controller import CookieController

import json

import pandas as pd

import mdblist_oauth as mdb_oauth
import achievements_engine as achievements_mod
import dashboard_engine as dashboard_mod
import excel_export as excel_mod
import stats_engine as stats_mod
import wrapped_engine as wrapped_mod
from calendar_engine import (
    CALENDAR_SORT_OPTIONS,
    CALENDAR_TIMING_OPTIONS,
    CALENDAR_TYPE_OPTIONS,
    build_local_calendar_events,
    filter_calendar_events,
    group_calendar_by_day,
    normalize_calendar_events,
    rows_to_csv as calendar_rows_to_csv,
    rows_to_ics,
)
from history_engine import (
    HISTORY_PERIOD_OPTIONS,
    HISTORY_SORT_OPTIONS,
    available_history_genres,
    filter_history,
    genre_minutes,
    normalize_history,
    rows_to_csv as history_rows_to_csv,
    rows_to_json as history_rows_to_json,
)
from list_audit_engine import (
    ADDITION_PERIOD_OPTIONS,
    ADDITION_SORT_OPTIONS,
    ISSUE_OPTIONS,
    SORT_OPTIONS as AUDIT_SORT_OPTIONS,
    addition_history,
    addition_rows_to_csv,
    audit_source,
    auditable_sources,
    filter_addition_history,
    filter_audit_rows,
    rows_to_csv,
    rows_to_json,
    source_display_label,
)
from mdblist_provider import MDBListProvider
from normalized_model import NORMALIZED_SCHEMA_VERSION, dedupe, normalize_provider_dataset
from playback_engine import (
    DEFAULT_PLAYBACK_SORT,
    PLAYBACK_PROGRESS_OPTIONS,
    PLAYBACK_SORT_OPTIONS,
    enrich_playback_posters,
    filter_playback_rows,
    finishable_tonight,
    normalize_now_playing,
    normalize_playback,
)
from progress_engine import (
    DEFAULT_PROGRESS_SORT,
    PROGRESS_SORT_OPTIONS,
    available_progress_genres,
    filter_progress_rows,
    progress_genres,
    sort_progress_rows,
)
from recommendation_engine import PRESET_NAMES, build_profile, preset_matches, score_item


APP_NAME = "Media Smart Lists"
APP_VERSION = "0.15.0-alpha"

PAGES = [
    "🏠 Tableau de bord",
    "▶️ En cours de lecture",
    "👻 Progression Fantôme",
    "🧹 Nettoyage des listes",
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
        border-radius: 10px;
        height: 132px;
        object-fit: cover;
        width: 88px;
    }
    .media-list-card.upnext-card img {
        height: 150px;
        width: 100px;
    }
    .media-list-card.poster-card {
        border-left: 4px solid var(--am-lime);
        min-height: 154px;
    }
    .score-badge {
        background: linear-gradient(135deg, rgba(206,220,0,.18), rgba(0,163,146,.18));
        border: 1px solid rgba(206,220,0,.48);
        border-radius: 10px;
        color: var(--am-lime);
        display: inline-block;
        font-size: .82rem;
        font-weight: 800;
        margin-top: .4rem;
        padding: .28rem .5rem;
    }
    .reason-pill, .warning-pill {
        border-radius: 999px;
        cursor: help;
        display: inline-block;
        font-size: .70rem;
        margin: .25rem .25rem 0 0;
        padding: .20rem .48rem;
        position: relative;
    }
    .reason-pill {
        background: rgba(0,163,146,.14);
        border: 1px solid rgba(0,163,146,.35);
        color: var(--am-text);
    }
    .warning-pill {
        background: rgba(206,220,0,.10);
        border: 1px solid rgba(206,220,0,.35);
        color: var(--am-lime);
    }
    .info-pill:focus { outline: 2px solid var(--am-lime); outline-offset: 2px; }
    .info-pill::after {
        background: rgba(2, 20, 18, .98);
        border: 1px solid rgba(206,220,0,.42);
        border-radius: 10px;
        bottom: calc(100% + 8px);
        color: var(--am-text);
        content: attr(data-tooltip);
        font-size: .74rem;
        font-weight: 500;
        left: 50%;
        line-height: 1.35;
        max-width: min(330px, 72vw);
        min-width: 220px;
        opacity: 0;
        padding: .48rem .58rem;
        pointer-events: none;
        position: absolute;
        text-align: left;
        transform: translate(-50%, 5px);
        transition: opacity .15s ease, transform .15s ease;
        visibility: hidden;
        white-space: normal;
        z-index: 9999;
    }
    .info-pill:hover::after, .info-pill:focus::after {
        opacity: 1;
        transform: translate(-50%, 0);
        visibility: visible;
    }
    .media-list-content {
        min-width: 0;
    }
    .progress-bar-container {
        background: linear-gradient(90deg, var(--am-lime), var(--am-yellow));
        border-radius: 8px;
        height: 12px;
        margin: .58rem 0;
        overflow: hidden;
        width: 100%;
    }
    .progress-bar-fill {
        background: var(--am-green);
        border-radius: 8px;
        height: 100%;
        transition: width .6s cubic-bezier(.4,0,.2,1);
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
    div[data-testid="stDownloadButton"] button,
    div[data-testid="stDownloadButton"] a,
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
    div[data-testid="stDownloadButton"] button:hover,
    div[data-testid="stDownloadButton"] a:hover,
    div[data-testid="stFormSubmitButton"] > button:hover {
        background: rgba(8, 55, 50, 0.85) !important;
        border-color: rgba(0,163,146,0.50) !important;
        box-shadow: none !important;
    }
    .stButton > button[kind="primary"],
    div[data-testid="stButton"] > button[kind="primary"],
    div[data-testid="stDownloadButton"] button[kind="primary"],
    div[data-testid="stDownloadButton"] button[data-testid="stBaseButton-primary"] {
        background: linear-gradient(135deg, var(--am-green), var(--am-green-aston)) !important;
        border: none !important;
        color: #fff !important;
        font-weight: 700 !important;
    }
    .stButton > button[kind="primary"]:hover,
    div[data-testid="stButton"] > button[kind="primary"]:hover,
    div[data-testid="stDownloadButton"] button[kind="primary"]:hover,
    div[data-testid="stDownloadButton"] button[data-testid="stBaseButton-primary"]:hover {
        background: linear-gradient(135deg, #00B8A5, #006058) !important;
    }

    /* Badges Succès — même style que l'ancienne application. */
    .badge-obtenu {
        background: linear-gradient(135deg, rgba(0,163,146,0.25) 0%, rgba(0,82,75,0.45) 100%) !important;
        border: 1px solid rgba(0,163,146,0.5) !important;
        backdrop-filter: blur(14px);
        border-radius: 16px;
        padding: 20px 16px;
        text-align: center;
        box-shadow: none !important;
        transition: transform 0.25s ease;
        margin-bottom: 12px;
    }
    .badge-obtenu:hover { transform: translateY(-4px); }
    .badge-obtenu .emoji { font-size: 2.5em; margin-bottom: 8px; }
    .badge-obtenu .titre { font-size: 1.05em; font-weight: 700; color: #F0FAF8; margin-bottom: 6px; }
    .badge-obtenu .desc { font-size: 0.82em; color: #9DC5BF; line-height: 1.4; }
    .badge-lock {
        background: rgba(4, 25, 22, 0.55) !important;
        border: 1px solid rgba(60, 80, 76, 0.4) !important;
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 18px 14px;
        text-align: center;
        opacity: 0.65;
        filter: grayscale(0.7);
        transition: all 0.25s ease;
        margin-bottom: 12px;
    }
    .badge-lock:hover { opacity: 0.9; filter: grayscale(0.2); transform: translateY(-2px); }
    .badge-lock .emoji { font-size: 2.2em; margin-bottom: 8px; filter: grayscale(1); opacity: 0.7; }
    .badge-lock .titre { font-size: 1em; font-weight: 600; color: #7EA8A0; margin-bottom: 6px; }
    .badge-lock .desc { font-size: 0.8em; color: #6B928C; line-height: 1.4; }
    .badge-lock .prog-badge {
        height: 6px;
        background: rgba(0,0,0,0.3);
        border-radius: 3px;
        margin-top: 10px;
        overflow: hidden;
    }
    .badge-lock .prog-badge-fill {
        height: 100%;
        background: linear-gradient(90deg, #00524B, #00A392);
        border-radius: 3px;
    }

    /* Barres de progression : remplissage vert → citron, fond vert translucide
       (comme les barres des cartes « En cours de lecture »). */
    div[data-testid="stProgress"] [role="progressbar"] > div > div,
    div[data-testid="stProgress"] [role="progressbar"] > div > div > div {
        background: linear-gradient(90deg, var(--am-green), var(--am-lime)) !important;
        border-radius: 999px;
    }
    div[data-testid="stProgress"] [role="progressbar"] > div,
    div[data-testid="stProgress"] > div > div > div {
        background: rgba(0, 163, 146, 0.22) !important;
        border: 1px solid rgba(0, 163, 146, 0.28) !important;
        border-radius: 999px;
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
        .media-list-card img {
            height: 114px;
            width: 76px;
        }
        .media-list-card.upnext-card img {
            height: 126px;
            width: 84px;
        }
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
        # Déconnexion discrète, accessible depuis toutes les pages (sidebar).
        if mdb_oauth.is_connected():
            if st.button("🔌 Se déconnecter de MDBList", key="logout_sidebar", use_container_width=True):
                mdb_oauth.disconnect(cookies)
                st.session_state.pop("_normalized_dataset", None)
                st.session_state.pop("_source_genre_cache", None)
                st.rerun()
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
            for key in (
                "_normalized_dataset",
                "_source_genre_cache",
                "_mdblist_now_playing_live",
                "_mdblist_playback_poster_cache",
                "_mdblist_calendar_cache",
            ):
                st.session_state.pop(key, None)
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
    if not isinstance(value, dict):
        return {}
    if value.get("schema_version") != NORMALIZED_SCHEMA_VERSION:
        # Évite de conserver en mémoire le schéma d'une étape précédente après redéploiement.
        st.session_state.pop("_normalized_dataset", None)
        st.session_state.pop("_source_genre_cache", None)
        return {}
    return value


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
    return f"https://image.tmdb.org/t/p/w500{value}"


def _score(item: dict) -> str:
    if not isinstance(item, dict):
        return ""
    value = item.get("score") or item.get("score_average")
    try:
        return str(int(round(float(value)))) if value is not None else ""
    except (TypeError, ValueError):
        return ""


def _format_minutes(minutes: int) -> str:
    """Durée compacte et lisible, de quelques minutes à plusieurs années.

    Sous 24 h : format court « 2h35 ». Au-delà, les heures et minutes sont
    conservées pour rester précis : « 7 mois 15 j, 2 h 35 min ».
    """
    minutes = max(int(round(minutes or 0)), 0)
    if minutes < 60:
        return f"{minutes} min"

    hours, minute_rest = divmod(minutes, 60)
    if hours < 24:
        return f"{hours}h{minute_rest:02d}" if minute_rest else f"{hours}h"

    days, hour_rest = divmod(hours, 24)
    years, day_after_years = divmod(days, 365)
    months, day_rest = divmod(day_after_years, 30)

    big = []
    if years:
        big.append(f"{years} an" if years == 1 else f"{years} ans")
    if months:
        big.append(f"{months} mois")
    if day_rest:
        big.append(f"{day_rest} j")

    tail = None
    if hour_rest and minute_rest:
        tail = f"{hour_rest} h {minute_rest} min"
    elif hour_rest:
        tail = f"{hour_rest} h"
    elif minute_rest:
        tail = f"{minute_rest} min"

    if not big and tail:
        return tail
    if big and tail:
        if len(big) >= 2:
            return " ".join(big) + ", " + tail
        return big[0] + ", " + tail
    return " ".join(big) if big else "0 min"


def _render_echarts(option: dict, height: str = "400px") -> None:
    """Affiche un graphique Apache ECharts.

    Remplace le paquet `streamlit-echarts`, incompatible avec Streamlit 1.60 :
    il utilise l'API st.iframe + le CDN ECharts (même rendu, sans dépendance).
    """
    try:
        payload = json.dumps(option, ensure_ascii=False)
    except (TypeError, ValueError):
        return
    numeric = int(str(height).replace("px", "") or 400)
    html = f"""<!DOCTYPE html><html><head>
<meta charset="utf-8">
<style>
html,body{{width:100%;height:{numeric}px;margin:0;padding:0;overflow:hidden;background:transparent;}}
#chart{{width:100%;height:100%;}}
</style>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
</head><body><div id="chart"></div>
<script>
(function() {{
  var option = {payload};
  function draw() {{
    var el = document.getElementById('chart');
    var chart = echarts.getInstanceByDom(el) || echarts.init(el);
    chart.setOption(option);
    chart.resize();
  }}
  if (document.readyState === 'complete' || document.readyState === 'interactive') {{
    setTimeout(draw, 50);
  }} else {{
    window.addEventListener('load', function() {{ setTimeout(draw, 50); }});
  }}
  window.addEventListener('resize', function() {{
    var el = document.getElementById('chart');
    var chart = echarts.getInstanceByDom(el);
    if (chart) {{ chart.resize(); }}
  }});
}})();
</script></body></html>"""
    try:
        st.iframe("data:text/html;charset=utf-8," + quote(html), width="stretch", height=numeric)
        return
    except Exception:
        pass
    try:
        st.components.v1.html(html, height=numeric, scrolling=False)
    except Exception:
        # Repli discret si le contexte composant n'est pas disponible.
        pass


def _format_date(value: object) -> str:
    if value in (None, ""):
        return ""
    try:
        parsed = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
        return parsed.strftime("%d/%m/%Y")
    except (TypeError, ValueError):
        return str(value)[:10]


def _format_datetime(value: object) -> str:
    if value in (None, ""):
        return ""
    try:
        parsed = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=ZoneInfo("UTC"))
        return parsed.astimezone(ZoneInfo("Europe/Paris")).strftime("%d/%m/%Y %H:%M")
    except (TypeError, ValueError):
        return str(value)[:16]


def _runtime_text(item: dict) -> str:
    if not isinstance(item, dict):
        return ""
    value = item.get("runtime")
    try:
        minutes = int(round(float(value)))
    except (TypeError, ValueError):
        return ""
    if minutes <= 0:
        return ""
    return _format_minutes(minutes)


def _rating_text(item: dict) -> str:
    values = item.get("ratings") if isinstance(item, dict) else []
    if not isinstance(values, list):
        return ""
    preferred = ("imdb", "tmdb", "trakt", "letterboxd")
    indexed = {
        str(value.get("source") or value.get("name") or "").lower(): value
        for value in values if isinstance(value, dict)
    }
    for source in preferred:
        value = indexed.get(source)
        if not value:
            continue
        rating = value.get("value") if value.get("value") is not None else value.get("rating")
        if rating is not None:
            return f"{source.upper()} {rating}"
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
        raw_data = provider.load_dataset()
        data = normalize_provider_dataset(raw_data)
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
    lists = sections.get("user_lists") or []
    playback = sections.get("playback") or []
    dropped = sections.get("dropped") or {}

    first = st.columns(4)
    first[0].metric("Films vus", len(watched.get("movies") or []))
    first[1].metric("Épisodes vus", len(watched.get("episodes") or []))
    first[2].metric(
        "Contenus dans votre Watchlist",
        len(watchlist.get("movies") or []) + len(watchlist.get("shows") or []),
    )
    first[3].metric("Listes personnelles", len(lists))

    second = st.columns(4)
    second[0].metric(
        "Notes",
        sum(len(ratings.get(key) or []) for key in ("movies", "shows", "seasons", "episodes")),
    )
    second[1].metric("Reprises", len(playback))
    second[2].metric("Séries abandonnées", len(dropped.get("shows") or []))
    second[3].metric("Up Next", len(sections.get("upnext") or []))

    # Temps de visionnage (à vie) — calcul local depuis l'historique.
    try:
        dash = dashboard_mod.compute_dashboard(_dataset(), timezone_name="Europe/Paris")
        if not dash.get("empty"):
            c = dash["compteurs"]
            third = st.columns(4)
            third[0].metric("⏱️ Temps total", dashboard_mod._minutes_to_duree(dash["total_minutes"]))
            third[1].metric("📺 Temps séries", dashboard_mod._minutes_to_duree(int(c["h_series"] * 60)))
            third[2].metric("🎬 Temps films", dashboard_mod._minutes_to_duree(int(c["h_films"] * 60)))
            third[3].metric(
                "🏃 Épisodes/semaine",
                f"{dash['eps_sem']:.1f}".replace(".", ",") if dash["eps_sem"] else "—",
            )
    except Exception:
        pass


def _reset_recommendation_filters() -> None:
    defaults = {
        "qr_search": "",
        "qr_note_min": 0.0,
        "qr_time": "Aucune limite",
        "qr_status": "Tous les statuts",
        "qr_sort": "✨ Pour moi (recommandé)",
        "qr_preset": "Aucun preset",
    }
    for key, value in defaults.items():
        st.session_state[key] = value
    st.session_state.pop("_roulette_result", None)


def _justwatch_url(title: str) -> str:
    return "https://www.justwatch.com/fr/recherche?q=" + quote(str(title or ""))


def _content_links_html(ids: dict, title: str, is_show: bool = False) -> str:
    """Liens discrets vers le contenu : JustWatch (où regarder), TMDB (fiche)
    et MDBList (fiche) quand les identifiants sont connus."""
    title_text = quote(str(title or ""))
    justwatch = f"https://www.justwatch.com/fr/recherche?q={title_text}"
    links = [f'<a href="{justwatch}" target="_blank" rel="noopener noreferrer" style="color:#CEDC00;text-decoration:none;">🔎 Où regarder</a>']
    tmdb = ids.get("tmdb") if isinstance(ids, dict) else None
    if tmdb:
        base = "tv" if is_show else "movie"
        links.append(
            f'<a href="https://www.themoviedb.org/{base}/{int(tmdb)}" target="_blank" rel="noopener noreferrer" '
            f'style="color:#9DC5BF;text-decoration:none;">TMDB</a>'
        )
    imdb = ids.get("imdb") if isinstance(ids, dict) else None
    if imdb:
        base = "show" if is_show else "m"
        links.append(
            f'<a href="https://mdblist.com/{base}/{str(imdb)}" target="_blank" rel="noopener noreferrer" '
            f'style="color:#9DC5BF;text-decoration:none;">MDBList</a>'
        )
    return f'<small style="margin-top:.3rem;">{" · ".join(links)}</small>'


def _signal_pill(signal: dict) -> str:
    label = str(signal.get("label") or "Information")
    tooltip = str(signal.get("tooltip") or label)
    css_class = "warning-pill" if signal.get("warning") else "reason-pill"
    return (
        f'<span class="{css_class} info-pill" tabindex="0" '
        f'data-tooltip="{escape(tooltip, quote=True)}" title="{escape(tooltip, quote=True)}">'
        f'{escape(label)}</span>'
    )


def _render_recommendation_card(row: dict, highlighted: bool = False) -> None:
    item = row.get("item") or {}
    raw_title = _media_title(item)
    title = escape(raw_title)
    year = escape(_media_year(item))
    poster = escape(_poster_url(item), quote=True)
    image_html = f'<img src="{poster}" alt="" loading="lazy">' if poster else ""
    metadata = []
    if row.get("genres"):
        metadata.append(" · ".join(row["genres"]))
    if row.get("runtime"):
        suffix = "/ép." if row.get("type") == "Série" else ""
        metadata.append(f"⏱️ {_format_minutes(row['runtime'])}{suffix}")
    if row.get("note") is not None:
        metadata.append(f"⭐ {row['note']:.1f}/10")
    if row.get("studios"):
        metadata.append("🏢 " + " · ".join(row["studios"][:2]))
    if row.get("people"):
        metadata.append("🎭 " + " · ".join(row["people"][:2]))
    metadata.append(str(row.get("source") or "MDBList"))

    signals = row.get("signals") or []
    if signals:
        pills = "".join(_signal_pill(signal) for signal in signals)
    else:
        # Compatibilité avec un résultat mémorisé par une version antérieure.
        legacy = [
            {"label": reason.split(" (+")[0], "tooltip": reason, "warning": False}
            for reason in (row.get("reasons") or [])[:5]
        ] + [
            {"label": "⚠️ " + warning.split(" (-")[0], "tooltip": warning, "warning": True}
            for warning in (row.get("warnings") or [])[:4]
        ]
        pills = "".join(_signal_pill(signal) for signal in legacy)

    roulette_badge = '<span class="source-badge">CHOIX DE LA ROULETTE</span><br>' if highlighted else ""
    justwatch = escape(_justwatch_url(raw_title), quote=True)
    links_html = (
        f'<small><a href="{justwatch}" target="_blank" rel="noopener noreferrer" '
        'style="color:#CEDC00;text-decoration:none;">🔎 Où regarder ?</a></small>'
    )
    st.markdown(
        f'<div class="media-list-card poster-card">{image_html}<div class="media-list-content" style="width:100%;">'
        f'{roulette_badge}<strong>{row.get("type")} — {title}</strong>'
        f'<span>{(" (" + year + ")") if year else ""}</span>'
        f'<small>{escape(" · ".join(metadata))}</small>{links_html}'
        f'<span class="score-badge">Score personnel {int(round(row.get("score", 0)))}/100 · '
        f'Friction {int(row.get("friction", 0))}/100</span>'
        f'<div class="progress-bar-container"><div class="progress-bar-fill" '
        f'style="width:{max(0,min(float(row.get("score",0)),100))}%;"></div></div>'
        f'<div>{pills}</div></div></div>',
        unsafe_allow_html=True,
    )


def _render_taste_profile(profile: dict) -> None:
    with st.expander("🧠 Comprendre mon profil de goûts"):
        affinities = profile.get("genre_affinity") or {}
        top_genres = sorted(affinities.items(), key=lambda value: value[1], reverse=True)[:6]
        personal = profile.get("personal_genre_ratings") or {}
        top_ratings = sorted(personal.items(), key=lambda value: value[1], reverse=True)[:5]
        if top_genres:
            st.markdown(
                "**Genres les plus présents :** "
                + " · ".join(escape(str(name)) for name, _ in top_genres),
                unsafe_allow_html=True,
            )
        if top_ratings:
            st.markdown(
                "**Genres les mieux notés par toi :** "
                + " · ".join(f"{escape(str(name))} ({value:.1f}/10)" for name, value in top_ratings),
                unsafe_allow_html=True,
            )
        st.caption(
            f"Durée de film centrale : environ {profile.get('preferred_runtime', 105)} min · "
            "les vues récentes pèsent davantage que les anciennes."
        )

        studio_count = int(profile.get("studio_metadata_count") or 0)
        people_count = int(profile.get("people_metadata_count") or 0)
        favorite_studios = profile.get("favorite_studios") or set()
        favorite_people = profile.get("favorite_people") or set()
        studio_display = profile.get("studio_display") or {}
        people_display = profile.get("people_display") or {}
        if studio_count:
            names = [studio_display.get(key, key) for key in sorted(favorite_studios)]
            st.caption(
                f"🏢 Métadonnées studio/réseau disponibles sur {studio_count} titre(s)"
                + (" · favoris détectés : " + ", ".join(names[:8]) if names else "")
            )
        if people_count:
            names = [people_display.get(key, key) for key in sorted(favorite_people)]
            st.caption(
                f"🎭 Métadonnées acteurs disponibles sur {people_count} titre(s)"
                + (" · visages familiers : " + ", ".join(names[:8]) if names else "")
            )
        if not studio_count and not people_count:
            st.caption(
                "🏢🎭 MDBList ne fournit actuellement ni studio de film ni casting dans les réponses "
                "de listes utilisées ici. Ces bonus restent désactivés plutôt que de lancer une requête par contenu."
            )


def render_watchlist_page() -> None:
    st.markdown('<div class="page-title">🎯 Que regarder ?</div>', unsafe_allow_html=True)
    sections = _sections()
    sources = _dataset().get("sources") or []
    if not any(source["movies"] or source["shows"] for source in sources):
        st.markdown(
            '<div class="accent-callout"><strong>LISTES NON CHARGÉES</strong> · '
            'Connecte MDBList puis charge les données depuis le Tableau de bord.</div>',
            unsafe_allow_html=True,
        )
        return

    profile = build_profile(_dataset())
    st.caption(
        f"🧠 Profil établi à partir de {profile.get('history_count', 0)} visionnage(s) "
        f"et {profile.get('ratings_count', 0)} note(s) personnelle(s). "
        "Scores, tris, presets et roulettes sont calculés sur l’appareil et préservent votre quota MDBList."
    )
    st.caption(
        "ℹ️ Survole une pastille — ou sélectionne-la au clavier — pour voir son explication "
        "et son influence exacte sur le score. Les points restent volontairement cachés sur la carte."
    )
    _render_taste_profile(profile)

    source_by_label = {source_display_label(source): source for source in sources}
    source_by_key = {source["key"]: source for source in sources}
    source_col, genre_col, type_col = st.columns(3)
    selected_label = source_col.selectbox("Source", list(source_by_label), key="qr_source")
    source = source_by_label[selected_label]

    genre_records = sections.get("genres") or []
    genre_by_title = {
        str(item.get("title") or item.get("slug") or ""): str(item.get("slug") or "")
        for item in genre_records
        if isinstance(item, dict) and item.get("slug")
    }
    genre_titles = sorted([title for title in genre_by_title if title], key=str.casefold)
    selected_genre = genre_col.selectbox("Genre", ["Tous"] + genre_titles, key="watchlist_genre")
    selected_type = type_col.selectbox("Type", ["Tous", "Films", "Séries"], key="watchlist_type")

    f1, f2, f3, f4 = st.columns(4)
    search = f1.text_input("Recherche", key="qr_search", placeholder="Titre…")
    note_min = f2.select_slider(
        "Note minimum",
        options=[0.0, 5.0, 6.0, 7.0, 7.5, 8.0, 8.5, 9.0],
        key="qr_note_min",
    )
    time_filter = f3.selectbox(
        "Temps max",
        ["Aucune limite", "Moins d'1h30", "Moins de 2h", "Moins de 3h", "Soirée (< 10h)", "Week-end (< 24h)"],
        key="qr_time",
    )
    status_filter = f4.selectbox(
        "Statut",
        ["Tous les statuts", "Séries terminées", "Séries en cours", "Séries annulées"],
        key="qr_status",
    )

    p1, p2, p3 = st.columns([0.44, 0.34, 0.22])
    preset = p1.selectbox("Preset rapide", PRESET_NAMES, key="qr_preset")
    sort_mode = p2.selectbox(
        "Trier par",
        [
            "✨ Pour moi (recommandé)",
            "⭐ Meilleures notes",
            "⏱️ Plus rapide",
            "🔥 Populaires",
            "📥 Ajouté récemment",
            "🆕 Nouveautés",
            "🚪 Zéro effort",
            "🎬 Films d’abord",
            "📺 Séries d’abord",
            "🙅 Pas pour moi",
        ],
        key="qr_sort",
    )
    display_limit = p3.selectbox("Afficher", [20, 50, 100], key="watchlist_limit")
    st.button("Réinitialiser les filtres", on_click=_reset_recommendation_filters, key="reset_qr")

    items = list(source["movies"]) + list(source["shows"])
    api_calls_extra = 0
    if selected_genre != "Tous":
        slug = genre_by_title.get(selected_genre, selected_genre.lower())
        cache = st.session_state.setdefault("_source_genre_cache", {})
        member_keys = source.get("members") or [source["key"]]
        combined_movies = []
        combined_shows = []
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
                for member_key in member_keys:
                    member = source_by_key.get(member_key)
                    if not member:
                        continue
                    cache_key = f"{member_key}:{slug}"
                    response = cache.get(cache_key)
                    if not isinstance(response, dict):
                        if member["kind"] == "watchlist":
                            response = provider.watchlist(slug)
                        else:
                            response = provider.list_items(int(member["id"]), slug)
                        cache[cache_key] = response
                        api_calls_extra += 1
                    combined_movies.extend(response.get("movies") or [])
                    combined_shows.extend(response.get("shows") or [])
            st.session_state["_source_genre_cache"] = cache
            account = mdb_oauth.account_summary()
            if provider.rate_limit_remaining is not None and account:
                account["rate_limit_remaining"] = provider.rate_limit_remaining
                st.session_state[mdb_oauth.ACCOUNT_KEY] = account
                mdb_oauth.persist_cookie(cookies)
        except Exception:
            st.markdown(
                '<div class="accent-callout"><strong>FILTRE INDISPONIBLE</strong> · '
                'MDBList n’a pas pu filtrer cette source.</div>',
                unsafe_allow_html=True,
            )
            return
        items = dedupe(combined_movies) + dedupe(combined_shows)

    scored = [
        score_item(
            item,
            profile,
            source_name=source["name"],
            known_genre=(selected_genre if selected_genre != "Tous" else None),
        )
        for item in items
    ]

    def time_ok(row: dict) -> bool:
        if time_filter == "Aucune limite":
            return True
        minutes = row.get("runtime") or 0
        if row["type"] == "Série":
            minutes *= row.get("total_episodes") or 1
        limits = {
            "Moins d'1h30": 90,
            "Moins de 2h": 120,
            "Moins de 3h": 180,
            "Soirée (< 10h)": 600,
            "Week-end (< 24h)": 1440,
        }
        return bool(minutes and minutes <= limits[time_filter])

    filtered = []
    for row in scored:
        if selected_type == "Films" and row["type"] != "Film":
            continue
        if selected_type == "Séries" and row["type"] != "Série":
            continue
        if search and search.casefold() not in _media_title(row["item"]).casefold():
            continue
        if note_min and (row.get("note") or 0) < note_min:
            continue
        if not time_ok(row):
            continue
        if status_filter != "Tous les statuts":
            if row["type"] != "Série":
                continue
            status = row.get("status") or ""
            if status_filter == "Séries terminées" and status != "ended":
                continue
            if status_filter == "Séries annulées" and status != "canceled":
                continue
            if status_filter == "Séries en cours" and status in {"ended", "canceled"}:
                continue
        if not preset_matches(preset, row, profile):
            continue
        filtered.append(row)

    def needed_minutes(row: dict) -> int:
        runtime = int(row.get("runtime") or 0)
        if row.get("type") == "Série":
            return runtime * int(row.get("total_episodes") or 1)
        return runtime

    display_rows = list(filtered)
    if sort_mode.startswith("✨"):
        display_rows.sort(key=lambda row: (-row["score"], -row["friction"]))
    elif sort_mode.startswith("⭐"):
        display_rows.sort(key=lambda row: (-(row.get("note") or 0), -row["score"]))
    elif sort_mode.startswith("⏱️"):
        display_rows.sort(key=lambda row: (needed_minutes(row) or 10**9, -row["score"]))
    elif sort_mode.startswith("🔥"):
        display_rows.sort(key=lambda row: (-(row.get("votes") or 0), -row["score"]))
    elif sort_mode.startswith("📥"):
        display_rows.sort(key=lambda row: (row.get("added_days") is None, row.get("added_days") or 0, -row["score"]))
    elif sort_mode.startswith("🆕"):
        display_rows.sort(key=lambda row: (-(row.get("year") or 0), -row["score"]))
    elif sort_mode.startswith("🚪"):
        display_rows.sort(key=lambda row: (-row["friction"], -row["score"]))
    elif sort_mode.startswith("🎬"):
        display_rows.sort(key=lambda row: (row.get("type") != "Film", -row["score"]))
    elif sort_mode.startswith("📺"):
        display_rows.sort(key=lambda row: (row.get("type") != "Série", -row["score"]))
    else:
        display_rows = sorted(
            [row for row in display_rows if row.get("not_for_me")],
            key=lambda row: (row["score"], -len(row.get("warnings") or [])),
        )

    source_note = (
        f"filtre MDBList actualisé ({api_calls_extra} appel(s)), puis mémorisé pour cette session"
        if api_calls_extra else
        ("filtre déjà mémorisé pour cette session" if selected_genre != "Tous" else "analyse locale · quota MDBList préservé")
    )
    st.markdown(
        f'<div class="accent-callout"><strong>{len(display_rows)} RÉSULTAT(S)</strong> · '
        f'{escape(source_note)}.</div>',
        unsafe_allow_html=True,
    )

    roulette_col, discovery_col = st.columns(2)
    with roulette_col:
        if st.button("🎲 Roulette — choisir pour moi", type="primary", key="roulette_classic"):
            pool = [row for row in filtered if row["score"] >= 70 and not row.get("not_for_me")]
            if not pool:
                pool = sorted(
                    [row for row in filtered if not row.get("not_for_me")],
                    key=lambda row: -row["score"],
                )[:10]
            if pool:
                st.session_state["_roulette_result"] = random.choices(
                    pool,
                    weights=[max(row["score"], 1) for row in pool],
                    k=1,
                )[0]
    with discovery_col:
        if st.button("🧭 Roulette découverte", type="primary", key="roulette_discovery"):
            discovery = [
                row for row in filtered
                if not row.get("not_for_me")
                and preset_matches("🧭 Hors de ta zone de confort", row, profile)
            ]
            if discovery:
                st.session_state["_roulette_result"] = random.choice(discovery)

    roulette = st.session_state.get("_roulette_result")
    if roulette and any(row["key"] == roulette.get("key") for row in filtered):
        st.markdown("### Le hasard a choisi")
        _render_recommendation_card(roulette, highlighted=True)

    if sort_mode.startswith("✨"):
        recommended = [row for row in display_rows if row["score"] >= 50 and not row.get("not_for_me")]
        maybe = [row for row in display_rows if row["score"] < 50 and not row.get("not_for_me")]
        unsuitable = sorted(
            [row for row in display_rows if row.get("not_for_me")],
            key=lambda row: row["score"],
        )
        result_sections = [
            ("✨ Recommandations personnalisées", recommended),
            ("🤔 Pourquoi pas", maybe),
            ("🙅 Ne correspond pas à mon profil", unsuitable),
        ]
    else:
        section_title = "Résultats"
        for prefix, title in (
            ("⭐", "⭐ Par note décroissante"),
            ("⏱", "⏱️ Du plus rapide au plus long"),
            ("🔥", "🔥 Les plus populaires"),
            ("📥", "📥 Derniers ajouts dans la liste"),
            ("🆕", "🆕 Sorties les plus récentes"),
            ("🚪", "🚪 Les plus faciles à lancer"),
            ("🎬", "🎬 Films d’abord"),
            ("📺", "📺 Séries d’abord"),
            ("🙅", "🙅 Contenus qui correspondent le moins à mon profil"),
        ):
            if sort_mode.startswith(prefix):
                section_title = title
                break
        result_sections = [(section_title, display_rows)]

    remaining_slots = int(display_limit)
    rendered = 0
    for section_title, group in result_sections:
        if not group or remaining_slots <= 0:
            continue
        st.markdown(f"### {section_title} ({len(group)})")
        visible = group[:remaining_slots]
        # Une carte sous l'autre (comme « En cours de lecture ») : lecture
        # plus aérée, sans décalage de largeur entre colonnes.
        for row in visible:
            _render_recommendation_card(row)
        rendered += len(visible)
        remaining_slots -= len(visible)

    if not display_rows:
        st.caption("Aucun contenu ne correspond à cette sélection.")
    elif len(display_rows) > rendered:
        st.caption(f"{len(display_rows) - rendered} résultat(s) supplémentaire(s) masqué(s).")


def render_progress_page() -> None:
    st.markdown('<div class="page-title">▶️ En cours de lecture</div>', unsafe_allow_html=True)
    sections = _sections()
    playback = sections.get("playback") or []
    progress_rows = _dataset().get("progress") or []
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
    cols[1].metric("Séries en cours", len(progress_rows))
    cols[2].metric("Séries abandonnées", len(dropped))

    st.markdown("### Où en suis-je dans mes séries ?")
    if not progress_rows:
        st.caption("Aucune série Up Next disponible.")
    else:
        st.markdown(
            '<div class="accent-callout"><strong>FILTRES ET TRIS INSTANTANÉS</strong> · '
            'Genre, progression, durées, dernier visionnage et nouveauté utilisent les données '
            'déjà disponibles et préservent votre quota MDBList.</div>',
            unsafe_allow_html=True,
        )
        search_col, genre_col, sort_col, limit_col = st.columns([0.22, 0.20, 0.40, 0.18])
        progress_search = search_col.text_input(
            "Rechercher",
            key="progress_search",
            placeholder="Titre de série…",
        )
        genre_options = ["Tous les genres", *available_progress_genres(progress_rows)]
        selected_genre = genre_col.selectbox(
            "Genre",
            genre_options,
            key="progress_genre",
        )
        sort_mode = sort_col.selectbox(
            "Trier par",
            PROGRESS_SORT_OPTIONS,
            index=PROGRESS_SORT_OPTIONS.index(DEFAULT_PROGRESS_SORT),
            key="progress_sort",
        )
        display_choice = limit_col.selectbox(
            "Afficher",
            [30, 60, 100, "Toutes"],
            key="progress_limit",
        )

        filtered_rows = filter_progress_rows(
            progress_rows,
            genre=selected_genre,
            search=progress_search,
        )
        filtered_rows = sort_progress_rows(filtered_rows, sort_mode)
        st.caption(
            f"{len(filtered_rows)} série(s) affichable(s) sur {len(progress_rows)} · "
            f"tri actif : {sort_mode}"
        )
        display_limit = len(filtered_rows) if display_choice == "Toutes" else int(display_choice)

        for row in filtered_rows[:display_limit]:
            show = row.get("show") or {}
            episode = row.get("next_episode") or {}
            title = escape(str(show.get("title") or "Série"))
            season = episode.get("season")
            number = episode.get("episode")
            ep_title = escape(str(episode.get("title") or ""))
            poster = escape(_poster_url(show), quote=True)
            image_html = f'<img src="{poster}" alt="" loading="lazy">' if poster else ""
            watched = int(row.get("watched_episodes") or 0)
            total = int(row.get("total_episodes") or 0)
            remaining = int(row.get("remaining_episodes") or 0)
            percent = float(row.get("percent") or 0)
            watched_time = _format_minutes(int(row.get("watched_minutes") or 0))
            remaining_time = _format_minutes(int(row.get("remaining_minutes") or 0))
            genres = progress_genres(row)
            genres_html = (
                f'<small>🎭 {escape(" · ".join(genres))}</small>' if genres else ""
            )
            dates = []
            last_watched = _format_date(row.get("last_watched_at"))
            if last_watched:
                dates.append(f"Dernier visionnage : {last_watched}")
            latest_available = _format_date(row.get("latest_available_at"))
            if latest_available:
                if row.get("latest_available_is_fallback"):
                    dates.append(f"Épisode à voir sorti le {latest_available}")
                else:
                    dates.append(f"Dernier épisode disponible : {latest_available}")
            dates_html = f'<small>🗓️ {escape(" · ".join(dates))}</small>' if dates else ""
            show_ref = row.get("show") if isinstance(row.get("show"), dict) else {}
            show_ids = show_ref.get("ids") if isinstance(show_ref.get("ids"), dict) else {}
            raw_show_title = str(show_ref.get("title") or row.get("title") or "")
            links_html = _content_links_html(show_ids, raw_show_title, is_show=True)
            st.markdown(
                f'<div class="media-list-card upnext-card">{image_html}'
                f'<div class="media-list-content" style="width:100%;">'
                f'<strong style="font-size:1.05rem;">{title}</strong>'
                f'{genres_html}'
                f'<div style="margin:.35rem 0;">{dates_html}</div>'
                f'<div style="margin:.15rem 0;"><small>▶️ Prochain : S{int(season or 0):02d}E{int(number or 0):02d} · {ep_title}</small></div>'
                f'<div style="margin:.15rem 0;"><small>📊 {watched}/{total} épisode(s) vu(s) · {percent:.1f}% · il en reste {remaining}</small></div>'
                f'<div style="margin:.15rem 0;"><small>⏱️ {watched_time} de visionnage · reste {remaining_time}</small></div>'
                f'<div class="progress-bar-container"><div class="progress-bar-fill" '
                f'style="width:{max(0,min(percent,100))}%;"></div></div>'
                f'{links_html}'
                f'</div></div>',
                unsafe_allow_html=True,
            )

        if len(filtered_rows) > display_limit:
            st.caption(
                f"{len(filtered_rows) - display_limit} série(s) supplémentaire(s) masquée(s). "
                "Augmente la limite « Afficher » pour les voir."
            )
        if not filtered_rows:
            st.markdown(
                '<div class="accent-callout"><strong>AUCUN RÉSULTAT</strong> · '
                'Aucune série ne correspond à ces filtres.</div>',
                unsafe_allow_html=True,
            )

    if dropped:
        st.markdown("### Séries abandonnées")
        st.caption("Ces séries sont marquées « Abandonnée » dans MDBList. Aucune modification n’est proposée ici.")
        for item in dropped[:30]:
            st.markdown(
                f'<div class="media-list-card"><div class="media-list-content">'
                f'<strong>{escape(_media_title(item))}</strong></div></div>',
                unsafe_allow_html=True,
            )


NOW_PLAYING_CACHE_KEY = "_mdblist_now_playing_live"
PLAYBACK_POSTER_CACHE_KEY = "_mdblist_playback_poster_cache"
NOW_PLAYING_AUTO_SECONDS = 300


def _apply_playback_poster_cache(rows: list[dict]) -> list[dict]:
    cache = st.session_state.get(PLAYBACK_POSTER_CACHE_KEY)
    cache = cache if isinstance(cache, dict) else {}
    output = []
    for row in rows:
        value = dict(row)
        ids = value.get("ids") if isinstance(value.get("ids"), dict) else {}
        tmdb_id = ids.get("tmdb")
        if not value.get("poster") and tmdb_id is not None and str(tmdb_id) in cache:
            value["poster"] = cache[str(tmdb_id)]
        output.append(value)
    return output


def _refresh_missing_playback_posters(rows: list[dict]) -> tuple[bool, str]:
    tmdb_ids: list[int] = []
    for row in rows:
        ids = row.get("ids") if isinstance(row.get("ids"), dict) else {}
        value = ids.get("tmdb")
        if not row.get("poster") and value is not None:
            try:
                media_id = int(value)
            except (TypeError, ValueError):
                continue
            if media_id > 0 and media_id not in tmdb_ids:
                tmdb_ids.append(media_id)
    tmdb_ids = tmdb_ids[:200]
    if not tmdb_ids:
        return False, "Aucun identifiant TMDb disponible pour compléter ces posters."
    valid, message = mdb_oauth.ensure_valid_session(cookies)
    if not valid:
        return False, message or "Session MDBList indisponible."
    try:
        provider = MDBListProvider(mdb_oauth.access_token())
        metadata = provider.media_info_batch(tmdb_ids=tmdb_ids)
    except Exception:
        return False, "MDBList n’a pas pu compléter les posters pour le moment."
    cache = st.session_state.get(PLAYBACK_POSTER_CACHE_KEY)
    cache = dict(cache) if isinstance(cache, dict) else {}
    added = 0
    for item in metadata:
        ids = item.get("ids") if isinstance(item.get("ids"), dict) else {}
        tmdb_id = ids.get("tmdb")
        poster = item.get("poster") or item.get("poster_path")
        if tmdb_id is not None and poster:
            cache[str(tmdb_id)] = str(poster)
            added += 1
    st.session_state[PLAYBACK_POSTER_CACHE_KEY] = cache
    account = mdb_oauth.account_summary()
    if provider.rate_limit_remaining is not None and account:
        account["rate_limit_remaining"] = provider.rate_limit_remaining
        st.session_state[mdb_oauth.ACCOUNT_KEY] = account
        mdb_oauth.persist_cookie(cookies)
    return True, f"{added} poster(s) complété(s) avec un appel groupé."


def _refresh_now_playing() -> tuple[bool, str]:
    """Un unique appel ciblé, sans recharger les onze sections du dataset."""
    valid, message = mdb_oauth.ensure_valid_session(cookies)
    if not valid:
        return False, message or "Session MDBList indisponible."
    try:
        provider = MDBListProvider(mdb_oauth.access_token())
        items = provider.now_playing()
    except Exception:
        return False, "MDBList n’a pas pu lire /sync/now-playing pour le moment."
    st.session_state[NOW_PLAYING_CACHE_KEY] = {
        "items": items,
        "fetched_at": time.time(),
        "request_count": provider.request_count,
    }
    account = mdb_oauth.account_summary()
    if provider.rate_limit_remaining is not None and account:
        account["rate_limit_remaining"] = provider.rate_limit_remaining
        st.session_state[mdb_oauth.ACCOUNT_KEY] = account
        mdb_oauth.persist_cookie(cookies)
    return True, "Lecture en cours actualisée."


def _render_live_now_playing_rows(rows: list[dict], fetched_at: float) -> None:
    if not rows:
        st.markdown(
            '<div class="accent-callout"><strong>AUCUNE LECTURE ACTIVE</strong> · '
            'Aucun scrobble actif n’était présent lors du dernier contrôle ciblé.</div>',
            unsafe_allow_html=True,
        )
        return
    for row in rows:
        poster = escape(_poster_url({"poster": row.get("poster")}), quote=True)
        image_html = f'<img src="{poster}" alt="" loading="lazy">' if poster else ""
        title = escape(str(row.get("title") or "Titre inconnu"))
        year = f" ({int(row['year'])})" if row.get("year") else ""
        episode_label = escape(str(row.get("episode_label") or ""))
        progress = float(row.get("progress") or 0)
        runtime = int(row.get("runtime") or 0)
        remaining = int(row.get("remaining_minutes") or 0)
        details = [f"progression estimée {progress:.1f}%"]
        if runtime:
            details.append(f"reste environ {_format_minutes(remaining)}")
        if row.get("is_manual"):
            details.append("check-in manuel")
        else:
            details.append("scrobble actif")
        if row.get("possibly_ended"):
            details.append("nouveau contrôle conseillé")
        episode_html = f'<small>▶️ {episode_label}</small>' if episode_label else ""
        st.markdown(
            f'<div class="media-list-card upnext-card">{image_html}'
            f'<div class="media-list-content" style="width:100%;">'
            f'<span class="source-badge">EN COURS MAINTENANT</span><br>'
            f'<strong>{escape(str(row.get("type") or "Lecture"))} — {title}{year}</strong>'
            f'{episode_html}<small>{escape(" · ".join(details))}</small>'
            f'<div class="progress-bar-container"><div class="progress-bar-fill" '
            f'style="width:{max(0,min(progress,100))}%;"></div></div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )
    checked = datetime.fromtimestamp(float(fetched_at)).strftime("%H:%M:%S")
    st.caption(
        f"Dernier contrôle réseau : {checked} · progression ensuite estimée localement chaque minute."
    )


@st.fragment(run_every=60)
def _now_playing_fragment() -> None:
    cache = st.session_state.get(NOW_PLAYING_CACHE_KEY)
    auto_refresh = bool(st.session_state.get("ghost_live_auto"))
    cache_age = time.time() - float((cache or {}).get("fetched_at") or 0)
    if auto_refresh and (not isinstance(cache, dict) or cache_age >= NOW_PLAYING_AUTO_SECONDS):
        ok, message = _refresh_now_playing()
        if not ok:
            st.caption(f"⚠️ {message}")
        cache = st.session_state.get(NOW_PLAYING_CACHE_KEY)
    if not isinstance(cache, dict):
        st.caption(
            "La vérification de la lecture active est facultative : elle utilise un seul appel MDBList "
            "lorsque vous cliquez sur « Actualiser la lecture en cours »."
        )
        return
    rows = normalize_now_playing(
        cache.get("items") or [],
        fetched_at=float(cache.get("fetched_at") or time.time()),
        now_timestamp=time.time(),
    )
    rows = enrich_playback_posters(rows, _dataset())
    rows = _apply_playback_poster_cache(rows)
    _render_live_now_playing_rows(rows, float(cache.get("fetched_at") or time.time()))


def render_ghost_page() -> None:
    st.markdown('<div class="page-title">👻 Progression Fantôme</div>', unsafe_allow_html=True)
    dataset = _dataset()
    if not dataset:
        st.markdown(
            '<div class="accent-callout"><strong>DONNÉES NON CHARGÉES</strong> · '
            'Charge MDBList depuis le Tableau de bord.</div>',
            unsafe_allow_html=True,
        )
        return

    st.markdown("### 🔴 Lecture en cours maintenant")
    refresh_col, auto_col = st.columns([0.58, 0.42])
    with refresh_col:
        if st.button(
            "Actualiser la lecture en cours · 1 appel",
            type="primary",
            key="refresh_now_playing",
        ):
            with st.spinner("Vérification de la lecture en cours…"):
                ok, message = _refresh_now_playing()
            if not ok:
                st.caption(f"⚠️ {message}")
    with auto_col:
        st.toggle(
            "Auto toutes les 5 minutes",
            value=False,
            key="ghost_live_auto",
            help=(
                "Option désactivée par défaut. Tant que cette page reste ouverte, "
                "elle coûte au maximum environ 12 appels MDBList par heure."
            ),
        )
    if st.session_state.get("ghost_live_auto"):
        st.caption("Actualisation automatique active · environ 12 appels/heure maximum sur cette page.")
    else:
        st.caption("Actualisation manuelle · votre quota reste inchangé tant que vous n’actualisez pas.")
    _now_playing_fragment()

    st.divider()
    st.markdown("### ⏸️ Reprises mises en pause")
    playback_items = (_sections().get("playback") or [])
    rows = enrich_playback_posters(normalize_playback(playback_items), dataset)
    rows = _apply_playback_poster_cache(rows)
    known_remaining = sum(int(row.get("remaining_minutes") or 0) for row in rows)
    metrics = st.columns(4)
    metrics[0].metric("Progressions", len(rows))
    metrics[1].metric("Films", sum(row.get("type") == "Film" for row in rows))
    metrics[2].metric("Épisodes", sum(row.get("type") == "Épisode" for row in rows))
    metrics[3].metric("Temps restant connu", _format_minutes(known_remaining) if known_remaining else "—")

    st.markdown(
        '<div class="accent-callout"><strong>REPRISES DISPONIBLES</strong> · '
        'Les filtres et calculs utilisent les données déjà chargées et préservent votre quota. '
        'Aucune progression n’est modifiée.</div>',
        unsafe_allow_html=True,
    )

    missing_with_tmdb = [
        row for row in rows
        if not row.get("poster")
        and isinstance(row.get("ids"), dict)
        and row["ids"].get("tmdb") is not None
    ]
    if missing_with_tmdb:
        if st.button(
            f"Compléter {min(len(missing_with_tmdb), 200)} poster(s) · 1 appel groupé",
            type="primary",
            key="complete_playback_posters",
            help="MDBList accepte jusqu’à 200 identifiants dans une seule requête groupée.",
        ):
            with st.spinner("Récupération groupée des posters…"):
                ok, message = _refresh_missing_playback_posters(rows)
            st.caption(("✓ " if ok else "⚠️ ") + message)
            if ok:
                rows = _apply_playback_poster_cache(rows)

    if not rows:
        st.markdown(
            '<div class="accent-callout"><strong>✓ AUCUNE PROGRESSION FANTÔME</strong> · '
            'Aucun film ou épisode n’est actuellement enregistré pour une reprise.</div>',
            unsafe_allow_html=True,
        )
        return

    tonight = finishable_tonight(rows, limit=3)
    if tonight:
        st.markdown("### ⚡ Tu peux finir ça ce soir")
        st.caption("Du temps restant connu le plus court au plus long.")
        tonight_cols = st.columns(len(tonight))
        for column, row in zip(tonight_cols, tonight):
            with column:
                label = row.get("episode_label") or row.get("type")
                st.markdown(f"**{escape(str(row.get('title') or 'Titre'))}**")
                st.caption(
                    f"{escape(str(label))} · reste environ "
                    f"{_format_minutes(int(row.get('remaining_minutes') or 0))} · "
                    f"{float(row.get('progress') or 0):.1f}% vu"
                )

    st.divider()
    type_col, progress_col, sort_col, limit_col = st.columns([0.18, 0.24, 0.40, 0.18])
    media_filter = type_col.selectbox(
        "Type",
        ["Tous", "Films", "Épisodes"],
        key="ghost_type",
    )
    progress_filter = progress_col.selectbox(
        "Progression",
        PLAYBACK_PROGRESS_OPTIONS,
        key="ghost_progress",
    )
    sort_mode = sort_col.selectbox(
        "Trier par",
        PLAYBACK_SORT_OPTIONS,
        index=PLAYBACK_SORT_OPTIONS.index(DEFAULT_PLAYBACK_SORT),
        key="ghost_sort",
    )
    display_choice = limit_col.selectbox(
        "Afficher",
        [30, 60, "Toutes"],
        key="ghost_limit",
    )
    search = st.text_input(
        "Recherche locale",
        key="ghost_search",
        placeholder="Film, série ou épisode…",
    )
    visible = filter_playback_rows(
        rows,
        media_filter=media_filter,
        progress_filter=progress_filter,
        search=search,
        sort_mode=sort_mode,
    )
    display_limit = len(visible) if display_choice == "Toutes" else int(display_choice)
    st.caption(f"{len(visible)} progression(s) correspondent aux filtres.")

    for row in visible[:display_limit]:
        poster = escape(_poster_url({"poster": row.get("poster")}), quote=True)
        image_html = f'<img src="{poster}" alt="" loading="lazy">' if poster else ""
        title = escape(str(row.get("title") or "Titre inconnu"))
        year = f" ({int(row['year'])})" if row.get("year") else ""
        episode_label = escape(str(row.get("episode_label") or ""))
        progress = float(row.get("progress") or 0)
        runtime = int(row.get("runtime") or 0)
        remaining = int(row.get("remaining_minutes") or 0)
        updated = _format_date(row.get("updated_at"))
        details = [f"{progress:.1f}% visionné"]
        if runtime:
            details.append(f"durée {_format_minutes(runtime)}")
            details.append(f"reste environ {_format_minutes(remaining)}")
        else:
            details.append("temps restant inconnu")
        if updated:
            details.append(f"dernière activité {updated}")
        if row.get("is_manual"):
            details.append("progression manuelle")
        episode_html = f'<small>▶️ {episode_label}</small>' if episode_label else ""
        row_ids = row.get("ids") if isinstance(row.get("ids"), dict) else {}
        links_html = _content_links_html(row_ids, str(row.get("title") or ""), is_show=(row.get("type") != "Film"))
        st.markdown(
            f'<div class="media-list-card upnext-card">{image_html}'
            f'<div class="media-list-content" style="width:100%;">'
            f'<strong>{escape(str(row.get("type") or "Lecture"))} — {title}{year}</strong>'
            f'{episode_html}<small>{escape(" · ".join(details))}</small>'
            f'<div class="progress-bar-container"><div class="progress-bar-fill" '
            f'style="width:{max(0,min(progress,100))}%;"></div></div>'
            f'{links_html}'
            f'</div></div>',
            unsafe_allow_html=True,
        )

    if len(visible) > display_limit:
        st.caption(f"{len(visible) - display_limit} progression(s) supplémentaire(s) masquée(s).")
    if not visible:
        st.caption("Aucune progression ne correspond à ces filtres.")
    st.caption("Vos reprises restent intactes : aucune suppression n’est proposée sur cette page.")


def render_static_lists_page() -> None:
    st.markdown('<div class="page-title">🧹 Nettoyage des listes</div>', unsafe_allow_html=True)
    dataset = _dataset()
    sources = auditable_sources(dataset, include_aggregates=True)
    if not dataset or not sources:
        st.markdown(
            '<div class="accent-callout"><strong>LISTES NON CHARGÉES</strong> · '
            'Charge MDBList depuis le Tableau de bord.</div>',
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        '<div class="accent-callout"><strong>ANALYSE AVANT ACTION</strong> · '
        'Choisissez un conteneur et vos critères pour obtenir un aperçu. '
        'L’analyse ne modifie pas vos listes et préserve votre quota MDBList.</div>',
        unsafe_allow_html=True,
    )

    source_by_label = {source_display_label(source): source for source in sources}
    source_col, type_col, sort_col = st.columns([0.38, 0.22, 0.40])
    selected_label = source_col.selectbox(
        "Conteneur à auditer",
        list(source_by_label),
        key="audit_source",
    )
    selected_source = source_by_label[selected_label]
    media_filter = type_col.selectbox(
        "Type",
        ["Tous", "Films", "Séries"],
        key="audit_media_type",
    )
    sort_mode = sort_col.selectbox(
        "Trier par",
        AUDIT_SORT_OPTIONS,
        key="audit_sort",
    )

    selected_issues = st.multiselect(
        "Signaux à rechercher",
        ISSUE_OPTIONS,
        key="audit_issues",
        placeholder="Aucun signal sélectionné = afficher tous les contenus",
    )
    if len(selected_issues) >= 2:
        match_mode = st.radio(
            "Comment combiner les signaux sélectionnés ?",
            ["Au moins un", "Tous les signaux"],
            horizontal=True,
            key="audit_match_mode",
            help=(
                "Au moins un : le contenu correspond à n’importe lequel des signaux. "
                "Tous les signaux : le contenu doit correspondre à chacun d’eux."
            ),
        )
    else:
        match_mode = "Au moins un"
        if selected_issues:
            st.caption("Un seul signal sélectionné : aucune combinaison n’est nécessaire.")
        else:
            st.caption("Aucun signal sélectionné : tous les contenus du conteneur sont affichés.")
    search = st.text_input(
        "Recherche locale",
        key="audit_search",
        placeholder="Titre…",
    )

    all_rows = audit_source(dataset, str(selected_source.get("key") or ""))
    filtered = filter_audit_rows(
        all_rows,
        selected_issues=selected_issues,
        match_all=match_mode == "Tous les signaux",
        media_filter=media_filter,
        search=search,
        sort_mode=sort_mode,
    )

    metrics = st.columns(4)
    metrics[0].metric("Contenus", len(all_rows))
    metrics[1].metric("Avec signal", sum(bool(row.get("issues")) for row in all_rows))
    metrics[2].metric("Déjà vus", sum(bool(row.get("watched")) for row in all_rows))
    metrics[3].metric("Multi-conteneurs", sum(bool(row.get("duplicate")) for row in all_rows))

    if selected_source.get("type") == "dynamic":
        st.caption(
            "ℹ️ Cette liste est dynamique : les chevauchements sont informatifs. "
            "MDBList régénère son contenu à partir de ses propres règles."
        )
    elif selected_source.get("kind") == "aggregate":
        st.caption(
            "ℹ️ Vue combinée : l’audit fusionne et déduplique les conteneurs sélectionnés. "
            "Cette vue n’est pas elle-même une liste modifiable."
        )

    st.markdown(f"### Aperçu ({len(filtered)})")
    table = [
        {
            "Type": row.get("type"),
            "Titre": row.get("title"),
            "Année": f"{row['year']}" if row.get("year") else "—",
            "Note": f"{row['note']:.1f}/10" if row.get("note") is not None else "—",
            "Ajouté le": _format_datetime(row.get("added_at")) or "—",
            "Ancienneté": f"{row['added_days']} j" if row.get("added_days") is not None else "—",
            "Présent dans": " | ".join(row.get("containers") or []) or selected_label,
            "Signaux": " · ".join(row.get("issue_labels") or []) or "Aucun",
        }
        for row in filtered
    ]
    if table:
        st.dataframe(table, use_container_width=True, hide_index=True)
    else:
        st.caption("Aucun contenu ne correspond à ces règles.")

    slug = str(selected_source.get("key") or "source").replace(":", "-")
    csv_col, json_col = st.columns(2)
    with csv_col:
        st.download_button(
            "⬇️ Télécharger l’audit CSV",
            data="\ufeff" + rows_to_csv(filtered, "audit"),
            file_name=f"media-smart-lists-audit-{slug}.csv",
            mime="text/csv",
            type="primary",
            key="download_audit_csv",
        )
    with json_col:
        st.download_button(
            "⬇️ Télécharger l’audit JSON",
            data=rows_to_json(filtered, "audit"),
            file_name=f"media-smart-lists-audit-{slug}.json",
            mime="application/json",
            type="primary",
            key="download_audit_json",
        )
    st.caption(
        "Aperçu uniquement : rien n’est supprimé et les rapports ne contiennent aucune donnée de connexion."
    )

    with st.expander("🕒 Historique des ajouts aux listes", expanded=False):
        additions = addition_history(dataset)
        containers = sorted({row["container"] for row in additions}, key=str.casefold)
        container_col, period_col, type_add_col = st.columns([0.42, 0.36, 0.22])
        container_filter = container_col.selectbox(
            "Conteneur",
            ["Tous les conteneurs", *containers],
            key="addition_container",
        )
        addition_period = period_col.selectbox(
            "Date d’ajout",
            ADDITION_PERIOD_OPTIONS,
            key="addition_period",
        )
        addition_type = type_add_col.selectbox(
            "Type",
            ["Tous", "Films", "Séries"],
            key="addition_type",
        )
        search_col, sort_add_col, limit_add_col = st.columns([0.46, 0.36, 0.18])
        addition_search = search_col.text_input(
            "Recherche",
            key="addition_search",
            placeholder="Titre…",
        )
        addition_sort = sort_add_col.selectbox(
            "Trier par",
            ADDITION_SORT_OPTIONS,
            key="addition_sort",
        )
        addition_limit = limit_add_col.selectbox(
            "Afficher",
            [100, 500, "Tout"],
            key="addition_limit",
        )
        visible_additions = filter_addition_history(
            additions,
            container=container_filter,
            media_filter=addition_type,
            period=addition_period,
            search=addition_search,
            sort_mode=addition_sort,
            now=datetime.now(PARIS_TZ),
        )
        known_dates = sum(row.get("added_at") is not None for row in visible_additions)
        add_metrics = st.columns(3)
        add_metrics[0].metric("Ajouts", len(visible_additions))
        add_metrics[1].metric("Dates connues", known_dates)
        add_metrics[2].metric("Dates non fournies", len(visible_additions) - known_dates)
        max_additions = len(visible_additions) if addition_limit == "Tout" else int(addition_limit)
        additions_table = [
            {
                "Ajouté le": row["added_at"].astimezone(PARIS_TZ).strftime("%d/%m/%Y %H:%M") if row.get("added_at") else "Date non fournie",
                "Type": row.get("type"),
                "Titre": row.get("title"),
                "Année": f"{row['year']}" if row.get("year") else "—",
                "Conteneur": row.get("container"),
            }
            for row in visible_additions[:max_additions]
        ]
        if additions_table:
            st.dataframe(additions_table, use_container_width=True, hide_index=True)
        else:
            st.caption("Aucun ajout ne correspond à ces filtres.")
        if len(visible_additions) > max_additions:
            st.caption(f"{len(visible_additions) - max_additions} ajout(s) supplémentaire(s) masqué(s).")
        st.download_button(
            "⬇️ Télécharger l’historique des ajouts",
            data="\ufeff" + addition_rows_to_csv(visible_additions),
            file_name="media-smart-lists-ajouts-listes.csv",
            mime="text/csv",
            type="primary",
            key="download_addition_history",
        )
        st.caption(
            "Les dates dépendent des champs fournis par MDBList. Les listes dynamiques peuvent ne pas exposer une date d’ajout par élément."
        )


CALENDAR_CACHE_KEY = "_mdblist_calendar_cache"
PARIS_TZ = ZoneInfo("Europe/Paris")


CALENDAR_API_MAX_DAYS = 120  # Limite documentée de l'endpoint /calendar/events MDBList.


def _calendar_call_count(horizon_days: int) -> int:
    """Nombre d'appels MDBList nécessaires pour couvrir l'horizon demandé."""
    horizon = max(1, int(horizon_days))
    return max(1, -(-horizon // CALENDAR_API_MAX_DAYS))


def _calendar_batch_count() -> int:
    """Nombre d'appels groupés (tmdb + imdb, 200 identifiants max) pour enrichir."""
    info = _calendar_media_ids(_dataset())
    count = 0
    if info["tmdb_ids"]:
        count += 1
    if info["imdb_ids"]:
        count += 1
    return min(3, count)


def _extract_media_ids(media: Any) -> tuple[int | None, str | None]:
    """Extrait (id_tmdb, id_imdb) d'un objet média MDBList, quel que soit le format.

    MDBList expose les identifiants sous plusieurs formes :
    - bloc nested `ids` : {"tmdb": 123, "imdb": "tt…", "mdblist": "m…"}
    - champs à plat : `tmdb_id`, `tmdbid`, `imdb_id`
    - `id` à plat : pour un média, l'id MDBList EST l'id TMDb (ex. id 917496 = tmdb 917496)
    - item imbriqué : {"movie": {...}} ou {"show": {...}}
    """
    if not isinstance(media, dict):
        return None, None
    # Désimbrication des contenus listés sous "movie"/"show".
    for nested in ("movie", "show", "media"):
        child = media.get(nested)
        if isinstance(child, dict):
            return _extract_media_ids(child)
    ids = media.get("ids") if isinstance(media.get("ids"), dict) else {}

    tmdb: int | None = None
    imdb: str | None = None
    for key in ("tmdb", "tmdbid", "tmdb_id"):
        if ids.get(key) is not None:
            try:
                tmdb = int(ids[key])
                break
            except (TypeError, ValueError):
                pass
    if tmdb is None:
        for key in ("tmdb_id", "tmdbid"):
            if media.get(key) is not None:
                try:
                    tmdb = int(media[key])
                    break
                except (TypeError, ValueError):
                    pass
    if tmdb is None:
        raw_id = media.get("id")
        try:
            candidate = int(raw_id)
            if candidate > 0:
                tmdb = candidate
        except (TypeError, ValueError):
            pass

    for key in ("imdb", "imdb_id"):
        if ids.get(key):
            imdb = str(ids[key]).strip()
            break
    if imdb is None:
        raw_imdb = media.get("imdb_id") or media.get("imdb")
        if raw_imdb:
            imdb = str(raw_imdb).strip()
    if imdb and not imdb.startswith("tt"):
        imdb = ""
    return tmdb, imdb


def _calendar_media_ids(dataset: dict[str, Any]) -> dict[str, Any]:
    """Identifiants des contenus personnels, par ordre de priorité
    (séries en cours d'abord, puis Watchlist, puis listes), avec compteurs
    pour les diagnostics affichés dans l'interface."""
    tmdb_ids: list[int] = []
    imdb_ids: list[str] = []
    seen_tmdb: set[int] = set()
    seen_imdb: set[str] = set()
    scanned = 0
    sections = dataset.get("sections") if isinstance(dataset.get("sections"), dict) else {}

    def scan(media: Any) -> None:
        nonlocal scanned
        if not isinstance(media, dict):
            return
        scanned += 1
        tmdb, imdb = _extract_media_ids(media)
        if tmdb is not None and tmdb > 0 and tmdb not in seen_tmdb:
            seen_tmdb.add(tmdb)
            tmdb_ids.append(tmdb)
        if imdb and imdb not in seen_imdb:
            seen_imdb.add(imdb)
            imdb_ids.append(imdb)

    for row in sections.get("upnext") or []:
        if isinstance(row, dict):
            scan(row.get("show"))
    watchlist = sections.get("watchlist") or {}
    for movie in watchlist.get("movies") or []:
        scan(movie)
    for show in watchlist.get("shows") or []:
        scan(show)
    for item in sections.get("user_lists") or []:
        if not isinstance(item, dict):
            continue
        for movie in item.get("movies") or []:
            scan(movie)
        for show in item.get("shows") or []:
            scan(show)
    # Secours : les sources normalisées du dataset.
    for source in dataset.get("sources") or []:
        if not isinstance(source, dict) or source.get("kind") == "aggregate":
            continue
        for movie in source.get("movies") or []:
            scan(movie)
        for show in source.get("shows") or []:
            scan(show)
    return {
        "tmdb_ids": tmdb_ids,
        "imdb_ids": imdb_ids,
        "scanned": scanned,
    }


def _parse_date_only(value: Any) -> date | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    try:
        if len(text) == 10:
            return date.fromisoformat(text)
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return parsed.date()
    except (TypeError, ValueError):
        return None


def _event_date_value(event: dict[str, Any]) -> Any:
    return event.get("first_aired") or event.get("release_date") or event.get("date")


def _enrich_calendar_metadata(
    provider: MDBListProvider,
    dataset: dict[str, Any],
    start_date: date,
    end_date: date,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Complète le calendrier avec les dates futures connues de MDBList/TMDb
    (films à sortir, premières de séries) via les appels groupés officiels
    POST /tmdb/any et POST /imdb/any.

    Retourne (événements, diagnostics) : les diagnostics permettent d'afficher
    dans l'interface pourquoi certains contenus n'apparaissent pas.
    """
    info = _calendar_media_ids(dataset)
    diag: dict[str, Any] = {
        "contenus_scannés": info["scanned"],
        "ids_tmdb": len(info["tmdb_ids"]),
        "ids_imdb": len(info["imdb_ids"]),
        "items_reçus": 0,
        "événements_candidats": 0,
        "erreurs": [],
    }
    output: list[dict[str, Any]] = []

    items: list[dict[str, Any]] = []
    if info["tmdb_ids"]:
        try:
            items.extend(provider.media_info_batch(tmdb_ids=info["tmdb_ids"][:200]))
        except Exception as exc:
            diag["erreurs"].append(f"lot TMDb : {exc}")
    if info["imdb_ids"]:
        try:
            items.extend(provider.media_info_batch(imdb_ids=info["imdb_ids"][:200]))
        except Exception as exc:
            diag["erreurs"].append(f"lot IMDb : {exc}")
    diag["items_reçus"] = len(items)

    for item in items:
        if not isinstance(item, dict):
            continue
        mediatype = str(
            item.get("mediatype") or item.get("media_type") or item.get("type") or ""
        ).casefold()
        is_movie = "movie" in mediatype or "film" in mediatype
        if is_movie:
            value = None
            for key in (
                "release_date", "released", "released_at", "theatrical_date",
                "premiere_date", "released_digital", "digital_release_date",
                "digital_date", "dvd_date", "dvd_release_date",
                "physical_release_date", "bluray_date",
            ):
                if item.get(key):
                    value = item[key]
                    break
            if value is None:
                continue
            parsed = _parse_date_only(value)
            if parsed is None or not (start_date <= parsed <= end_date):
                continue
            diag["événements_candidats"] += 1
            output.append(
                {
                    "type": "movie",
                    "release_date": value,
                    "movie": item,
                    "source": "Vos listes — date à venir",
                }
            )
        else:
            # Séries : MDBList expose la date de première diffusion (`released`).
            # L'épisode suivant d'une série en cours vient de l'Up Next (déjà
            # fusionné dans le calendrier de secours) lorsque MDBList le connaît.
            value = None
            for key in ("first_air_date", "premiere_date", "next_air_date", "released"):
                if item.get(key):
                    value = item[key]
                    break
            if value is None:
                continue
            parsed = _parse_date_only(value)
            if parsed is None or not (start_date <= parsed <= end_date):
                continue
            diag["événements_candidats"] += 1
            output.append(
                {"type": "show", "date": value, "show": item, "source": "Vos listes — date à venir"}
            )

    return output, diag


def _refresh_calendar(horizon_days: int, include_favorite_cast: bool) -> tuple[bool, str]:
    valid, message = mdb_oauth.ensure_valid_session(cookies)
    if not valid:
        return False, message or "Session MDBList indisponible."
    start_date = datetime.now(PARIS_TZ).date()
    horizon = max(1, min(int(horizon_days), 545))
    end_date = start_date + timedelta(days=horizon)
    provider = MDBListProvider(mdb_oauth.access_token())
    mode = "mdblist"
    events: list[dict[str, Any]] = []
    calendar_error: str | None = None
    try:
        # L'endpoint MDBList limite chaque appel à 120 jours : les horizons plus
        # longs sont découpés en tranches successives puis fusionnés.
        calls = _calendar_call_count(horizon)
        for index in range(calls):
            segment_start = start_date + timedelta(days=index * CALENDAR_API_MAX_DAYS)
            segment_end = min(end_date, segment_start + timedelta(days=CALENDAR_API_MAX_DAYS))
            segment = provider.calendar_events(
                segment_start.isoformat(),
                segment_end.isoformat(),
                include_favorite_cast=include_favorite_cast,
            )
            events.extend(segment)
    except Exception as exc:
        events = []
        mode = "local"
        calendar_error = str(getattr(provider, "calendar_error", None) or exc)

    dataset = _dataset()
    # Les dates déjà chargées (Up Next et listes) alimentent un calendrier de
    # secours, sans limite de 120 jours puisque aucune requête supplémentaire.
    local_events = build_local_calendar_events(dataset, start_date, end_date)
    # Enrichissement par appels groupés officiels : dates futures des films et
    # premières de séries présents dans vos listes et votre Watchlist.
    enriched: list[dict[str, Any]] = []
    enrich_diag: dict[str, Any] = {}
    try:
        enriched, enrich_diag = _enrich_calendar_metadata(provider, dataset, start_date, end_date)
    except Exception as exc:
        enrich_diag = {"erreurs": [f"enrichissement : {exc}"]}

    all_events = events + local_events + enriched
    if events:
        mode = "mdblist"
    elif all_events:
        mode = "local"

    st.session_state[CALENDAR_CACHE_KEY] = {
        "events": all_events,
        "fetched_at": time.time(),
        "start": start_date.isoformat(),
        "end": end_date.isoformat(),
        "horizon": horizon,
        "favorite_cast": bool(include_favorite_cast),
        "request_count": provider.request_count,
        "mode": mode,
        "event_counts": {
            "mdblist": len(events),
            "local": len(local_events),
            "enriched": len(enriched),
        },
        "enrich_diag": enrich_diag,
        "calendar_error": calendar_error,
    }
    account = mdb_oauth.account_summary()
    if provider.rate_limit_remaining is not None and account:
        account["rate_limit_remaining"] = provider.rate_limit_remaining
        st.session_state[mdb_oauth.ACCOUNT_KEY] = account
        mdb_oauth.persist_cookie(cookies)
    if mode == "local":
        return True, (
            f"Calendrier de secours prêt avec {len(all_events)} événement(s) : "
            f"{len(local_events)} depuis vos données, {len(enriched)} date(s) à venir complétée(s) par les appels groupés."
        )
    details = []
    if local_events:
        details.append(f"{len(local_events)} de vos données")
    if enriched:
        details.append(f"{len(enriched)} date(s) à venir complétée(s)")
    suffix = f" ({', '.join(details)})" if details else ""
    return True, f"{len(all_events)} événement(s) reçu(s) de MDBList{suffix}."


def _calendar_day_title(day: date | None) -> str:
    if day is None:
        return "Date à confirmer"
    today = datetime.now(PARIS_TZ).date()
    names = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    if day == today:
        return f"Aujourd’hui · {day.strftime('%d/%m/%Y')}"
    if day == today + timedelta(days=1):
        return f"Demain · {day.strftime('%d/%m/%Y')}"
    return f"{names[day.weekday()]} {day.strftime('%d/%m/%Y')}"


def render_calendar_page() -> None:
    st.markdown('<div class="page-title">📅 Calendrier des sorties</div>', unsafe_allow_html=True)
    if not mdb_oauth.is_connected():
        st.markdown(
            '<div class="accent-callout"><strong>CONNEXION NÉCESSAIRE</strong> · '
            'Connectez MDBList depuis le Tableau de bord pour consulter votre calendrier personnel.</div>',
            unsafe_allow_html=True,
        )
        return

    st.caption(
        "Films, premières de séries et prochains épisodes liés à votre compte MDBList. "
        "Un horizon complet est chargé (segments de 120 jours maximum) puis filtré localement."
    )
    horizon_col, cast_col, button_col = st.columns([0.30, 0.32, 0.38])
    horizon = horizon_col.selectbox(
        "Horizon",
        [7, 14, 30, 60, 90, 120, 180, 365, 545],
        index=2,
        format_func=lambda value: {
            7: "7 jours",
            14: "14 jours",
            30: "30 jours",
            60: "60 jours",
            90: "90 jours",
            120: "120 jours",
            180: "6 mois",
            365: "1 an",
            545: "1 an et demi (jusqu'à fin 2027)",
        }.get(value, f"{value} jours"),
        key="calendar_horizon",
    )
    include_cast = cast_col.toggle(
        "Inclure les personnes favorites",
        value=True,
        key="calendar_favorite_cast",
        help="Inclut les sorties liées aux acteurs et membres d’équipe marqués comme favoris dans MDBList.",
    )
    cache = st.session_state.get(CALENDAR_CACHE_KEY)
    today_iso = datetime.now(PARIS_TZ).date().isoformat()
    cache_matches = bool(
        isinstance(cache, dict)
        and cache.get("horizon") == horizon
        and cache.get("favorite_cast") == include_cast
        and cache.get("start") == today_iso
    )
    call_count = _calendar_call_count(horizon) + _calendar_batch_count()
    call_text = "1 appel" if call_count <= 1 else f"{call_count} appels"
    button_label = f"Actualiser mon calendrier · {call_text}" if cache_matches else f"Charger mon calendrier · {call_text}"
    with button_col:
        if st.button(button_label, type="primary", key="load_calendar"):
            with st.spinner("Préparation de votre calendrier…"):
                ok, message = _refresh_calendar(horizon, include_cast)
            st.caption(("✓ " if ok else "⚠️ ") + message)
            cache = st.session_state.get(CALENDAR_CACHE_KEY)
            cache_matches = bool(ok)

    if not cache_matches or not isinstance(cache, dict):
        st.markdown(
            '<div class="accent-callout"><strong>CALENDRIER À CHARGER</strong> · '
            'Choisissez votre horizon puis utilisez le bouton ci-dessus. Le résultat sera mémorisé pour la session.</div>',
            unsafe_allow_html=True,
        )
        return

    rows = normalize_calendar_events(cache.get("events") or [], now=datetime.now(PARIS_TZ))
    rows = enrich_playback_posters(rows, _dataset())
    rows = _apply_playback_poster_cache(rows)
    dated = [row for row in rows if row.get("datetime")]
    metrics = st.columns(4)
    metrics[0].metric("Événements", len(rows))
    metrics[1].metric("Films", sum(row.get("type") == "Film" for row in rows))
    metrics[2].metric("Épisodes", sum(row.get("type") == "Épisode" for row in rows))
    metrics[3].metric(
        "Prochaine date",
        min(row["datetime"] for row in dated).strftime("%d/%m") if dated else "—",
    )
    checked = datetime.fromtimestamp(float(cache.get("fetched_at") or time.time()), PARIS_TZ).strftime("%d/%m à %H:%M")
    counts = cache.get("event_counts") or {}
    extra = []
    if counts.get("local"):
        extra.append(f"{counts['local']} depuis vos données")
    if counts.get("enriched"):
        extra.append(f"{counts['enriched']} date(s) à venir complétée(s)")
    extra_text = (" · " + " · ".join(extra)) if extra else ""
    if cache.get("mode") == "local":
        st.caption(
            f"Calendrier de secours construit le {checked} depuis les dates déjà disponibles "
            f"(Up Next et vos listes) sur tout l'horizon choisi{extra_text}. "
            "Le service calendrier MDBList n'a pas répondu, mais les filtres et exports restent utilisables."
        )
    else:
        st.caption(
            f"Calendrier MDBList actualisé le {checked}{extra_text} · "
            "les filtres ci-dessous préservent votre quota."
        )

    enrich_diag = cache.get("enrich_diag") or {}
    if isinstance(enrich_diag, dict) and enrich_diag:
        with st.expander("🔍 Pourquoi ce calendrier contient-il ce qu'il contient ?"):
            st.caption(
                "Détail de l'enrichissement : les contenus de vos listes sont interrogés par lots "
                "pour trouver leurs dates de sortie à venir."
            )
            if cache.get("calendar_error"):
                st.markdown(
                    f"⚠️ **Calendrier officiel MDBList** : {escape(str(cache['calendar_error']))}"
                )
            if enrich_diag.get("erreurs"):
                for error in enrich_diag["erreurs"]:
                    st.markdown(f"⚠️ {escape(str(error))}")
            rows_diag = [
                ("Contenus scannés dans vos données", enrich_diag.get("contenus_scannés")),
                ("Identifiants TMDb trouvés", enrich_diag.get("ids_tmdb")),
                ("Identifiants IMDb trouvés", enrich_diag.get("ids_imdb")),
                ("Fiches reçues de MDBList", enrich_diag.get("items_reçus")),
                ("Dates à venir dans l'horizon", enrich_diag.get("événements_candidats")),
            ]
            for label, value in rows_diag:
                st.markdown(f"**{label}** : {value if value is not None else '—'}")
            st.caption(
                "Une série en pause dont la date de reprise n'est pas encore annoncée publiquement "
                "n'apparaît pas : la date n'existe nulle part. Elle apparaîtra dès sa publication."
            )

    filter_col, timing_col, sort_col, limit_col = st.columns([0.18, 0.27, 0.37, 0.18])
    type_filter = filter_col.selectbox("Type", CALENDAR_TYPE_OPTIONS, key="calendar_type")
    timing_filter = timing_col.selectbox("Période", CALENDAR_TIMING_OPTIONS, key="calendar_timing")
    sort_mode = sort_col.selectbox("Trier par", CALENDAR_SORT_OPTIONS, key="calendar_sort")
    display_choice = limit_col.selectbox("Afficher", [50, 100, "Tout"], key="calendar_limit")
    search = st.text_input("Recherche", key="calendar_search", placeholder="Film, série ou épisode…")
    visible = filter_calendar_events(rows, type_filter, timing_filter, search, sort_mode)

    missing_with_tmdb = [
        row for row in visible
        if not row.get("poster") and isinstance(row.get("ids"), dict) and row["ids"].get("tmdb") is not None
    ]
    if missing_with_tmdb:
        if st.button(
            f"Compléter {min(len(missing_with_tmdb), 200)} poster(s) · 1 appel groupé",
            type="primary",
            key="complete_calendar_posters",
        ):
            with st.spinner("Récupération groupée des posters…"):
                ok, message = _refresh_missing_playback_posters(visible)
            st.caption(("✓ " if ok else "⚠️ ") + message)
            if ok:
                visible = _apply_playback_poster_cache(visible)

    st.markdown(f"### Votre calendrier ({len(visible)})")
    display_limit = len(visible) if display_choice == "Tout" else int(display_choice)
    remaining = display_limit
    for day, group in group_calendar_by_day(visible):
        if remaining <= 0:
            break
        shown = group[:remaining]
        if not shown:
            continue
        st.markdown(f"#### {_calendar_day_title(day)} ({len(group)})")
        columns = st.columns(2)
        for index, row in enumerate(shown):
            with columns[index % 2]:
                poster = escape(_poster_url({"poster": row.get("poster")}), quote=True)
                image_html = f'<img src="{poster}" alt="" loading="lazy">' if poster else ""
                title = escape(str(row.get("title") or "Titre inconnu"))
                year = f" ({int(row['year'])})" if row.get("year") else ""
                episode = escape(str(row.get("episode_label") or ""))
                event_datetime = row.get("datetime")
                time_text = event_datetime.strftime("%H:%M") if event_datetime and any((event_datetime.hour, event_datetime.minute)) else ""
                meta = []
                if time_text:
                    meta.append(f"🕒 {time_text}")
                if row.get("genres"):
                    meta.append("🎭 " + " · ".join(row["genres"]))
                if row.get("source") and row.get("source") != "Calendrier MDBList":
                    meta.append(str(row["source"]))
                episode_html = f'<small>▶️ {episode}</small>' if episode else ""
                meta_html = f'<small>{escape(" · ".join(meta))}</small>' if meta else ""
                row_ids = row.get("ids") if isinstance(row.get("ids"), dict) else {}
                links_html = _content_links_html(row_ids, str(row.get("title") or ""), is_show=(row.get("type") != "Film"))
                st.markdown(
                    f'<div class="media-list-card poster-card">{image_html}'
                    f'<div class="media-list-content" style="width:100%;">'
                    f'<span class="source-badge">{escape(str(row.get("type") or "SORTIE").upper())}</span><br>'
                    f'<strong>{title}{year}</strong>{episode_html}{meta_html}{links_html}'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )
        remaining -= len(shown)

    rendered = min(len(visible), display_limit)
    if not visible:
        st.caption("Aucune sortie ne correspond à ces filtres.")
    elif len(visible) > rendered:
        st.caption(f"{len(visible) - rendered} événement(s) supplémentaire(s) masqué(s).")

    csv_col, ics_col = st.columns(2)
    with csv_col:
        st.download_button(
            "⬇️ Télécharger le calendrier CSV",
            data="\ufeff" + calendar_rows_to_csv(visible),
            file_name="media-smart-lists-calendrier.csv",
            mime="text/csv",
            type="primary",
            key="download_calendar_csv",
        )
    with ics_col:
        st.download_button(
            "📲 Ajouter à mon agenda (.ics)",
            data=rows_to_ics(visible),
            file_name="media-smart-lists-calendrier.ics",
            mime="text/calendar",
            type="primary",
            key="download_calendar_ics",
        )


def render_detailed_stats_page(dataset: dict[str, Any]) -> None:
    """Statistiques détaillées — même disposition et mêmes couleurs que la page
    Statistiques de l'ancienne application Trakt Smart Lists."""
    rows = normalize_history(dataset, timezone_name="Europe/Paris")
    if not rows:
        st.caption("Aucun visionnage disponible pour les statistiques détaillées.")
        return
    df = stats_mod.build_frame(rows)
    if df.empty:
        st.caption("Aucune donnée datée pour les statistiques détaillées.")
        return

    st.divider()
    st.markdown('<div class="page-title">📊 Statistiques détaillées</div>', unsafe_allow_html=True)
    st.caption(
        "Toutes vos données de visionnage. Les valeurs sont exprimées en **heures** sauf indication contraire. "
        "Note : un contenu avec plusieurs genres est compté dans chaque genre, la somme peut donc être supérieure au total."
    )

    f1, f2, f3 = st.columns(3)
    type_choice = f1.selectbox("Type de contenu", stats_mod.TYPE_OPTIONS, key="stats_type")
    period = f2.selectbox("Période", stats_mod.PERIOD_OPTIONS, index=0, key="stats_period")
    all_genres = sorted(
        {genre for raw in df["genre"].astype(str) for genre in raw.split(" · ") if genre != "Inconnu"},
        key=str.casefold,
    )
    genre_choice = f3.selectbox("Genre", ["Tous"] + all_genres, key="stats_genre")

    custom_start = custom_end = None
    if period == "Période personnalisée":
        months = stats_mod.available_months(df)
        if len(months) >= 2:
            pair = st.select_slider(
                "Sélectionne la période (mois)",
                options=months,
                value=(months[0], months[-1]),
                key="stats_months",
            )
            custom_start = datetime.strptime(pair[0], "%m-%Y").replace(tzinfo=PARIS_TZ).date()
            custom_end = (
                datetime.strptime(pair[1], "%m-%Y").replace(day=28) + timedelta(days=4)
            ).replace(tzinfo=PARIS_TZ).date()
        else:
            custom_start = df["date_dt"].min().date()
            custom_end = df["date_dt"].max().date()

    filtered = df.copy()
    if type_choice != "Tous":
        wanted = "Film" if type_choice == "Films" else "Épisode"
        filtered = filtered[filtered["type"] == wanted]
    filtered = stats_mod.apply_period(filtered, period, datetime.now(PARIS_TZ), custom_start, custom_end)
    if genre_choice != "Tous":
        filtered = filtered[filtered["genre"].str.contains(genre_choice, na=False)]
    if filtered.empty:
        st.warning("Aucun résultat pour ces filtres.")
        return

    total_lectures = int(filtered["lectures"].sum())
    total_minutes = int(filtered["duree"].sum())
    notes = filtered.loc[filtered["note"] > 0, "note"]
    note_moyenne = notes.mean()
    nb_jours = max((filtered["date_dt"].max() - filtered["date_dt"].min()).days + 1, 1)
    daily = filtered.groupby(filtered["date_dt"].dt.date)["lectures"].sum()
    record_jour = int(daily.max()) if not daily.empty else 0

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Nombre de visionnages", total_lectures)
    m2.metric("Temps de visionnage", _format_minutes(total_minutes) if total_minutes else "—")
    m3.metric("Note moyenne /10", f"{note_moyenne:.1f}" if pd.notna(note_moyenne) else "—")
    m4.metric("Moyenne par jour", f"{total_lectures / nb_jours:.1f}")
    m5.metric("Record en 1 jour", record_jour)

    # ── Heatmap d'activité (suit les filtres) ────────────────────────────────
    st.divider()
    st.markdown("#### 🗓️ Ton activité en un coup d'œil")
    st.caption(
        "Chaque case = un jour de la période filtrée (52 dernières semaines si « Tout »). "
        "Survole une case : date + visionnages du jour."
    )
    heat_html = stats_mod.heatmap_html(filtered)
    if heat_html:
        # Markdown unsafe : les info-bulles natives (title) fonctionnent comme
        # dans l'ancienne application.
        st.markdown(heat_html, unsafe_allow_html=True)
        nb_jours_actifs = int((daily > 0).sum())
        st.caption(
            f"📅 du {filtered['date_dt'].min().date():%d/%m/%Y} au {filtered['date_dt'].max().date():%d/%m/%Y} · "
            f"{nb_jours_actifs} jour(s) de visionnage · record : {record_jour}/jour"
        )

    # ── Heures par mois ──────────────────────────────────────────────────────
    st.divider()
    monthly = stats_mod.monthly_options(filtered)
    if monthly:
        _render_echarts(monthly, height="350px")

    g1, g2 = st.columns(2)
    with g1:
        pie = stats_mod.genre_pie_options(filtered)
        if pie:
            _render_echarts(pie, height="400px")
    with g2:
        hourly = stats_mod.hourly_options(filtered)
        if hourly:
            _render_echarts(hourly, height="400px")

    g3, g4 = st.columns(2)
    with g3:
        weekday = stats_mod.weekday_options(filtered)
        if weekday:
            _render_echarts(weekday, height="400px")
    with g4:
        years = stats_mod.release_year_options(filtered)
        if years:
            _render_echarts(years, height="400px")

    # ── ADN cinéphile ────────────────────────────────────────────────────────
    st.divider()
    st.markdown("#### 🧬 Ton ADN cinéphile")
    st.caption("La composition de tes visionnages sur la sélection filtrée ci-dessus.")
    dna1, dna2 = st.columns([0.52, 0.48])
    with dna1:
        st.markdown("**🎭 Répartition par genre (heures)**")
        genre_hours = stats_mod.dna_genres(filtered)
        total_genre_hours = sum(hours for _, hours in genre_hours) or 1
        for genre, hours in genre_hours:
            st.markdown(f"**{escape(genre)}** — {round(hours / total_genre_hours * 100)}%")
            st.progress(min(hours / total_genre_hours, 1.0))
    with dna2:
        st.markdown("**🧭 Tes grands équilibres**")
        for item in stats_mod.dna_balances(filtered, datetime.now(PARIS_TZ)):
            st.markdown(item["label"])
            st.progress(min(item["pct"], 1.0))

    # ── Studios préférés (séries) ────────────────────────────────────────────
    studios = stats_mod.studio_rank(filtered)
    if studios:
        st.divider()
        with st.container(border=True):
            st.markdown("#### 🏢 Tes studios préférés (séries)")
            st.caption(
                "Heures cumulées par **studio/chaîne**. Les films ne sont pas comptés : "
                "MDBList ne fournit pas toujours leur studio."
            )
            for studio in studios:
                st.markdown(
                    f"**{escape(studio['name'])}** — {_format_minutes(int(round(studio['hours'] * 60)))} · "
                    f"**{round(studio['pct'] * 100)}%** de tes heures"
                )
                st.progress(min(studio["pct"], 1.0))

    # ── Marathons ────────────────────────────────────────────────────────────
    marathons_df = stats_mod.marathons(filtered)
    if not marathons_df.empty:
        st.divider()
        with st.container(border=True):
            st.markdown("#### 🏆 Marathons (4+ épisodes en 1 jour)")
            for row in marathons_df.itertuples():
                st.write(f"📅 **{row.jour:%d/%m/%Y}** : {row.nb} épisodes de **{escape(row.serie)}**")

    # ── Évolution des goûts ──────────────────────────────────────────────────
    st.divider()
    st.markdown("#### 📈 L'évolution de tes goûts")
    st.caption("Tes 5 genres principaux, année par année (en heures). Suit la période et le type filtrés ci-dessus.")
    evolution = stats_mod.evolution_options(filtered)
    if evolution:
        _render_echarts(evolution, height="380px")
    else:
        st.caption("La période filtrée couvre moins de 2 années — élargis la période (« Tout ») pour voir l'évolution.")

    # ── Détail des visionnages ───────────────────────────────────────────────
    with st.expander("📋 Détail des visionnages"):
        table = []
        for row in filtered.itertuples():
            table.append(
                {
                    "Date": row.date_dt.strftime("%d/%m/%Y %H:%M"),
                    "Type": row.type,
                    "Titre": row.titre,
                    "Année": f"{int(row.annee)}" if pd.notna(row.annee) else "—",
                    "Genres": row.genre,
                    "Durée": _format_minutes(int(row.duree)),
                    "Note": f"{row.note:.1f}/10" if row.note > 0 else "—",
                }
            )
        st.dataframe(table, width="stretch", hide_index=True)


def render_basic_stats_page() -> None:
    st.markdown('<div class="page-title">📊 Statistiques</div>', unsafe_allow_html=True)
    dataset = _dataset()
    if not dataset:
        st.markdown(
            '<div class="accent-callout"><strong>STATISTIQUES NON CHARGÉES</strong> · '
            'Charge MDBList depuis le Tableau de bord.</div>',
            unsafe_allow_html=True,
        )
        return
    render_dataset_overview()

    with st.expander("📜 Historique des vues", expanded=False):
        st.caption(
            "Films et épisodes connus de MDBList, avec filtres temporels, genres, durées et notes personnelles. "
            "Toute l’analyse ci-dessous utilise les données déjà chargées."
        )
        rows = normalize_history(dataset, timezone_name="Europe/Paris")
        if not rows:
            st.caption("Aucun visionnage n’est disponible dans le dataset actuel.")
            return

        dated_values = [row["watched_at"].date() for row in rows if row.get("watched_at")]
        earliest = min(dated_values) if dated_values else datetime.now(PARIS_TZ).date()
        latest = max(dated_values) if dated_values else datetime.now(PARIS_TZ).date()
        period_col, type_col, genre_col, sort_col = st.columns([0.25, 0.18, 0.25, 0.32])
        period = period_col.selectbox("Période", HISTORY_PERIOD_OPTIONS, key="history_period")
        media_filter = type_col.selectbox("Type", ["Tous", "Films", "Épisodes"], key="history_type")
        genre_filter = genre_col.selectbox(
            "Genre",
            ["Tous les genres", *available_history_genres(rows)],
            key="history_genre",
        )
        sort_mode = sort_col.selectbox("Trier par", HISTORY_SORT_OPTIONS, key="history_sort")

        custom_start = custom_end = None
        if period == "Période personnalisée":
            start_col, end_col = st.columns(2)
            custom_start = start_col.date_input(
                "Du",
                value=max(earliest, latest - timedelta(days=30)),
                min_value=earliest,
                max_value=latest,
                key="history_start",
            )
            custom_end = end_col.date_input(
                "Au",
                value=latest,
                min_value=earliest,
                max_value=latest,
                key="history_end",
            )
            if custom_start > custom_end:
                custom_start, custom_end = custom_end, custom_start

        search_col, limit_col = st.columns([0.75, 0.25])
        search = search_col.text_input(
            "Recherche",
            key="history_search",
            placeholder="Film, série ou épisode…",
        )
        display_choice = limit_col.selectbox(
            "Afficher",
            [100, 500, 1000, "Tout"],
            key="history_limit",
        )
        visible = filter_history(
            rows,
            period=period,
            media_filter=media_filter,
            genre_filter=genre_filter,
            search=search,
            sort_mode=sort_mode,
            start_date=custom_start,
            end_date=custom_end,
            now=datetime.now(PARIS_TZ),
        )

        total_plays = sum(int(row.get("plays") or 1) for row in visible)
        total_minutes = sum(int(row.get("total_minutes") or 0) for row in visible)
        metrics = st.columns(4)
        metrics[0].metric("Entrées", len(visible))
        metrics[1].metric("Lectures connues", total_plays)
        metrics[2].metric("Films", sum(row.get("type") == "Film" for row in visible))
        metrics[3].metric("Temps estimé", _format_minutes(total_minutes) if total_minutes else "—")

        top_genres = genre_minutes(visible)[:6]
        if top_genres:
            st.markdown("#### Vos genres les plus regardés")
            total_genre_minutes = sum(minutes for _, minutes in top_genres) or 1
            genre_columns = st.columns(2)
            for index, (genre, minutes) in enumerate(top_genres):
                with genre_columns[index % 2]:
                    fraction = minutes / total_genre_minutes
                    st.markdown(f"**{escape(genre)}** · {_format_minutes(minutes)}")
                    st.progress(min(fraction, 1.0))

        display_limit = len(visible) if display_choice == "Tout" else int(display_choice)
        table = []
        for row in visible[:display_limit]:
            watched_at = row.get("watched_at")
            table.append(
                {
                    "Date": watched_at.strftime("%d/%m/%Y %H:%M") if watched_at else "—",
                    "Type": row.get("type"),
                    "Titre": row.get("title"),
                    "Épisode": row.get("episode_label") or "—",
                    "Année": f"{row['year']}" if row.get("year") else "—",
                    "Genres": " · ".join(row.get("genres") or []) or "—",
                    "Durée": _format_minutes(int(row.get("runtime") or 0)),
                    "Lectures": row.get("plays") or 1,
                    "Ma note": f"{row['personal_rating']:.1f}/10" if row.get("personal_rating") else "—",
                }
            )
        st.markdown(f"#### Détail des visionnages ({len(visible)})")
        if table:
            st.dataframe(table, use_container_width=True, hide_index=True)
        else:
            st.caption("Aucun visionnage ne correspond à ces filtres.")
        if len(visible) > display_limit:
            st.caption(f"{len(visible) - display_limit} entrée(s) supplémentaire(s) masquée(s).")

        csv_col, json_col = st.columns(2)
        with csv_col:
            st.download_button(
                "⬇️ Télécharger l’historique CSV",
                data="\ufeff" + history_rows_to_csv(visible),
                file_name="media-smart-lists-historique.csv",
                mime="text/csv",
                type="primary",
                key="download_history_csv",
            )
        with json_col:
            st.download_button(
                "⬇️ Télécharger l’historique JSON",
                data=history_rows_to_json(visible),
                file_name="media-smart-lists-historique.json",
                mime="application/json",
                type="primary",
                key="download_history_json",
            )

        st.caption(
            "MDBList fournit principalement la dernière date connue par film ou épisode. "
            "Les événements de revisionnage détaillés seront disponibles avec le futur import ZIP Trakt."
        )

    render_detailed_stats_page(dataset)


def render_dashboard_widgets() -> None:
    """Widgets du tableau de bord — rythme, compteurs à vie, projection de fin
    (copie les widgets de l'ancienne application Trakt Smart Lists)."""
    dataset = _dataset()
    if not dataset:
        return
    dash = dashboard_mod.compute_dashboard(dataset, timezone_name="Europe/Paris")
    if dash.get("empty"):
        return

    st.divider()
    st.markdown("### ⏱️ Ton rythme de visionnage")
    bilan = dash["bilan"]
    c1, c2 = st.columns([0.55, 0.45])
    with c1:
        with st.container(border=True):
            st.markdown(
                f"🗓️ **{bilan['mois']}** : **{dashboard_mod._minutes_to_duree(int(bilan['heures'] * 60))}** "
                f"· **{bilan['eps']}** épisode(s) · **{bilan['films']}** film(s)"
            )
            if dash["eps_sem"]:
                rythme_txt = f"{dash['eps_sem']:.1f}".replace(".", ",")
                st.markdown(f"🏃 Ton rythme : **{rythme_txt} ép./semaine**")
            if dash["projection"]:
                p = dash["projection"]
                st.markdown(
                    f"🏁 Au rythme actuel, tes **{dash['series_actives']} série(s) en cours** "
                    f"({dash['reste_actives']} épisode(s) restant(s)) seront finies vers le "
                    f"**{p.day} {dashboard_mod.MOIS_NOMS[p.month - 1]} {p.year}** "
                    f"*(hors nouvelles saisons… et nouvelles envies)* 😉"
                )
                st.caption("🚫 Les séries abandonnées (statut « dropped ») sont exclues de ce calcul.")
            elif dash["reste_actives"] > 0:
                st.caption("🏁 Regarde encore quelques épisodes et j'estimerai ta date de fin.")
            else:
                st.caption("🏁 Aucune série en cours ou en pause : rien à projeter pour l'instant.")
    with c2:
        with st.container(border=True):
            st.markdown("📼 **Compteurs à vie**")
            c = dash["compteurs"]
            st.caption(f"📺 Séries : **{dashboard_mod._minutes_to_duree(int(c['h_series'] * 60))}** ({c['nb_ep']} ép.)")
            st.caption(f"🎬 Films : **{dashboard_mod._minutes_to_duree(int(c['h_films'] * 60))}** ({c['nb_films']} films)")

    digest = dash["digest"]
    if digest["films"] or digest["eps"]:
        st.markdown(
            f"🍿 **Cette semaine** : {digest['eps']} épisode(s), {digest['films']} film(s) — "
            f"soit **{dashboard_mod._minutes_to_duree(digest['minutes'])}** de visionnage."
        )

    if dash["derniers"]:
        st.markdown("#### 🕘 Derniers visionnages")
        for item in dash["derniers"]:
            st.markdown(
                f"📅 **{item['date'].strftime('%d/%m/%Y %H:%M')}** · {item['type']} · **{escape(str(item['titre']))}**"
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
        render_dashboard_widgets()


def render_achievements_page() -> None:
    """Succès (badges) — mêmes badges et même présentation que l'ancienne
    application Trakt Smart Lists, branchés sur le modèle normalisé."""
    st.markdown('<div class="page-title">🏆 Succès</div>', unsafe_allow_html=True)
    st.caption(
        "Tes badges de grand fan de cinéma et de séries. Tu débloques des badges "
        "automatiquement au fil de ton visionnage."
    )
    dataset = _dataset()
    if not dataset:
        st.markdown(
            '<div class="accent-callout"><strong>DONNÉES NON CHARGÉES</strong> · '
            'Charge MDBList depuis le Tableau de bord.</div>',
            unsafe_allow_html=True,
        )
        return
    rows = normalize_history(dataset, timezone_name="Europe/Paris")
    if not rows:
        st.caption("Aucun visionnage n’est disponible pour le moment.")
        return
    df = stats_mod.build_frame(rows)
    if df.empty:
        st.caption("Aucune donnée datée pour les succès.")
        return

    result = achievements_mod.compute_achievements(df)
    obtenus = result["obtenus"]
    locks = result["locks"]

    st.markdown(f"#### 🎖️ Badges obtenus ({result['obtenu_count']}/{result['total']})")
    if obtenus:
        cols = st.columns(min(4, len(obtenus)))
        for i, (_badge_id, emoji, titre, desc, _cond, _prog) in enumerate(obtenus):
            with cols[i % 4]:
                st.markdown(
                    f"""
                    <div class="badge-obtenu">
                        <div class="emoji">{emoji}</div>
                        <div class="titre">{escape(str(titre))}</div>
                        <div class="desc">{escape(str(desc))}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        st.markdown(
            """
            <div style="background: rgba(8,55,50,0.45); border:1px solid rgba(255,255,255,0.07);
                        border-radius:14px; padding:18px; color:#F0FAF8; text-align:center;">
            Continue de regarder des contenus pour gagner tes premiers badges !
            </div>
            """,
            unsafe_allow_html=True,
        )

    if locks:
        st.divider()
        st.markdown(f"#### 🔒 Prochains badges à décrocher ({len(locks)})")
        st.caption("Voici les badges que tu n'as pas encore, triés avec les plus proches en premier.")
        cols = st.columns(min(4, len(locks)))
        for i, (_badge_id, emoji, titre, desc, _cond, prog) in enumerate(locks):
            with cols[i % 4]:
                st.markdown(
                    f"""
                    <div class="badge-lock">
                        <div class="emoji">{emoji}</div>
                        <div class="titre">{escape(str(titre))}</div>
                        <div class="desc">{escape(str(desc))}</div>
                        <div class="prog-badge"><div class="prog-badge-fill" style="width:{round(prog, 1)}%"></div></div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def render_annual_page() -> None:
    """Rendez-vous annuel (Wrapped) — même logique et même rendu que la page
    de l'ancienne application Trakt Smart Lists."""
    st.markdown('<div class="page-title">🎬 Rendez-vous annuel</div>', unsafe_allow_html=True)
    st.caption(
        "Ton récapitulatif annuel façon Wrapped. Sélectionne une année pour revivre ton année de visionnage."
    )
    dataset = _dataset()
    if not dataset:
        st.markdown(
            '<div class="accent-callout"><strong>DONNÉES NON CHARGÉES</strong> · '
            'Charge MDBList depuis le Tableau de bord.</div>',
            unsafe_allow_html=True,
        )
        return

    rows = normalize_history(dataset, timezone_name="Europe/Paris")
    if not rows:
        st.caption("Aucun visionnage n’est disponible pour le moment.")
        return
    df = stats_mod.build_frame(rows)
    if df.empty:
        st.caption("Aucune donnée datée pour le rendez-vous annuel.")
        return

    annees = sorted({d.year for d in df["date_dt"]}, reverse=True)
    if not annees:
        st.caption("Aucune année disponible.")
        return
    annee = st.selectbox("📅 Choisis une année", annees, index=0, key="wrapped_year")

    d = wrapped_mod.compute_wrapped(dataset, int(annee))
    if not d:
        st.info("Aucune donnée pour cette année.")
        return

    # Hero card.
    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, rgba(0,163,146,0.35) 0%, rgba(0,82,75,0.6) 100%);
                    border:1px solid rgba(0,163,146,0.5); border-radius:24px; padding:32px;
                    text-align:center; margin:20px 0;">
            <div style="font-size:1em; color:#CEDC00; text-transform:uppercase; letter-spacing:3px; font-weight:700;">
                TON ANNÉE {annee}</div>
            <div style="font-size:3.2em; font-weight:900; color:#fff; margin:10px 0;">
                {wrapped_mod.format_duree_fr(int(round(d['total_h'] * 60)))}</div>
            <div style="font-size:1.1em; color:#9DC5BF;">de visionnage cette année</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🎬 Films uniques", d["films"])
    c2.metric("📺 Séries suivies", d["series"])
    c3.metric("🎞️ Épisodes", d["episodes"])
    c4.metric("⭐ Note moyenne", f"{d['note_moy']:.1f}/10" if d["note_moy"] else "—")

    c5, c6 = st.columns(2)
    if d["jour_peak"] is not None:
        c5.metric("🏆 Record en 1 jour", f"{d['nb_peak']} visionnages", delta=d["jour_peak"].strftime("%d/%m"))
    else:
        c5.metric("🏆 Record en 1 jour", "—")
    c6.metric("📅 Ton plus gros mois", wrapped_mod.MOIS_NOMS[d["mois_peak"] - 1] if d["mois_peak"] else "—")

    # Top films.
    st.divider()
    st.markdown(f"### 🎬 Tes films les plus vus en {annee}")
    if d["top_films"]:
        for i, (titre, n) in enumerate(d["top_films"], 1):
            st.markdown(f"**#{i} — {escape(str(titre))}**  ·  {n} visionnage{'s' if n > 1 else ''}")
    else:
        st.caption("Aucun film vu cette année.")

    # Top séries.
    st.divider()
    st.markdown(f"### 📺 Tes séries les plus suivies en {annee}")
    if d["top_series"]:
        for i, (titre, n) in enumerate(d["top_series"], 1):
            st.markdown(f"**#{i} — {escape(str(titre))}**  ·  {n} épisodes")
    else:
        st.caption("Aucune série vue cette année.")

    # Top genres.
    st.divider()
    st.markdown(f"### 🎭 Tes genres préférés en {annee}")
    if d["top_genres"]:
        cols = st.columns(min(5, len(d["top_genres"])))
        for i, (genre, n) in enumerate(d["top_genres"]):
            cols[i].metric(genre, n)
    else:
        st.caption("Aucun genre identifié cette année.")

    # Heures par mois.
    st.divider()
    st.markdown(f"### 📊 Heures de visionnage par mois — {annee}")
    heures = d["heures_mois"]
    if heures.sum() > 0:
        monthly = {
            "title": {
                "text": f"Heures par mois en {annee}",
                "textStyle": {"color": "#F0FAF8"},
                "left": "center",
            },
            "tooltip": {"trigger": "axis", "formatter": "{b} : {c}h"},
            "backgroundColor": "transparent",
            "textStyle": {"color": "#F0FAF8"},
            "xAxis": {
                "type": "category",
                "data": wrapped_mod.MOIS_COURTS,
                "axisLabel": {"color": "#9DC5BF", "interval": 0},
            },
            "yAxis": {
                "type": "value",
                "name": "Heures",
                "axisLabel": {"color": "#9DC5BF"},
                "splitLine": {"lineStyle": {"color": "rgba(18,90,84,0.4)"}},
            },
            "series": [
                {
                    "data": [float(value) for value in heures],
                    "type": "bar",
                    "itemStyle": {"color": "#CEDC00", "borderRadius": [4, 4, 0, 0]},
                }
            ],
        }
        _render_echarts(monthly, height="350px")
    else:
        st.caption("Aucune heure de visionnage relevée cette année.")

    # Image Wrapped partageable.
    st.divider()
    st.markdown("### 🖼️ Ton image Wrapped à partager")
    st.caption("Un récap visuel de ton année, façon Spotify Wrapped, prêt à partager sur Insta, X ou Reddit ✨")
    if st.button("✨ Générer mon image Wrapped", key="btn_wrapped_png", type="primary"):
        with st.spinner("Création de ton image..."):
            data_img = {
                "annee": annee,
                "total": wrapped_mod.format_duree_fr(int(round(d["total_h"] * 60))),
                "films": d["films"],
                "series": d["series"],
                "episodes": d["episodes"],
                "note_moy": str(round(d["note_moy"], 1)).replace(".", ",") if d["note_moy"] else "?",
                "top_films": d["top_films"],
                "top_series": d["top_series"],
                "top_genres": d["top_genres"],
                "record_txt": (
                    f"{d['nb_peak']} vues le {d['jour_peak'].strftime('%d/%m')}"
                    if d["jour_peak"] is not None
                    else "—"
                ),
                "date_gen": datetime.now(PARIS_TZ).strftime("%d/%m/%Y"),
            }
            st.session_state["_wrapped_png"] = wrapped_mod.generer_image_wrapped(data_img)
            st.session_state["_wrapped_png_annee"] = annee
    if st.session_state.get("_wrapped_png") and st.session_state.get("_wrapped_png_annee") == annee:
        c_img = st.columns([1, 2, 1])[1]
        with c_img:
            st.image(st.session_state["_wrapped_png"], width=420)
            st.download_button(
                "💾 Télécharger le PNG",
                data=st.session_state["_wrapped_png"],
                file_name=f"wrapped_{annee}.png",
                mime="image/png",
                key="download_wrapped_png",
                type="primary",
            )


def render_backup_page() -> None:
    """Sauvegarde et restauration — export JSON neutre du dataset normalisé +
    rapport Excel multi-onglets, sans aucun secret."""
    st.markdown('<div class="page-title">📤 Sauvegarde</div>', unsafe_allow_html=True)
    st.caption(
        "Exporte tes données MDBList (historique, Watchlist, listes, statistiques, badges) "
        "au format JSON neutre ou en rapport Excel multi-onglets. Aucun secret ni jeton n'est jamais inclus."
    )
    dataset = _dataset()
    if not dataset:
        st.markdown(
            '<div class="accent-callout"><strong>DONNÉES NON CHARGÉES</strong> · '
            'Charge MDBList depuis le Tableau de bord avant d’exporter.</div>',
            unsafe_allow_html=True,
        )
        return

    # ── Export JSON (sauvegarde neutre et versionnée) ────────────────────────
    st.markdown("#### 📦 Sauvegarde JSON (restaurable)")
    st.caption(
        "Fichier neutre et versionné du dataset normalisé : historique, Watchlist, "
        "listes, notes et progressions. Utilisable pour recharger l'application sans nouvelle analyse."
    )
    payload = {
        "app": "media-smart-lists",
        "version": int(NORMALIZED_SCHEMA_VERSION),
        "export_date": datetime.now(PARIS_TZ).isoformat(),
        "dataset": dataset,
    }
    try:
        json_bytes = json.dumps(payload, ensure_ascii=False, default=str, indent=2).encode("utf-8")
    except (TypeError, ValueError):
        json_bytes = b"{}"
    date_str = datetime.now(PARIS_TZ).strftime("%Y-%m-%d")
    st.download_button(
        "💾 Télécharger la sauvegarde JSON",
        data=json_bytes,
        file_name=f"media-smart-lists-sauvegarde-{date_str}.json",
        mime="application/json",
        type="primary",
        key="download_backup_json",
    )

    st.divider()

    # ── Export Excel multi-onglets ───────────────────────────────────────────
    st.markdown("#### 📊 Rapport Excel (tous les onglets)")
    st.caption(
        "Un classeur avec un onglet par analyse : Résumé, Historique, Watchlist, "
        "Listes, Statistiques et Badges."
    )
    try:
        rows = normalize_history(dataset, timezone_name="Europe/Paris")
        df = stats_mod.build_frame(rows)
        dash = dashboard_mod.compute_dashboard(dataset, timezone_name="Europe/Paris")

        # Résumé
        if not dash.get("empty"):
            summary_rows = [
                ("Comptes", "MDBList"),
                ("Films", dash["compteurs"]["nb_films"]),
                ("Séries", dash["compteurs"]["nb_series"]),
                ("Épisodes", dash["compteurs"]["nb_ep"]),
                ("Temps total", dashboard_mod._minutes_to_duree(dash["total_minutes"])),
                ("Temps séries", dashboard_mod._minutes_to_duree(int(dash["compteurs"]["h_series"] * 60))),
                ("Temps films", dashboard_mod._minutes_to_duree(int(dash["compteurs"]["h_films"] * 60))),
                ("Séries en cours", dash["series_actives"]),
                ("Épisodes restants", dash["reste_actives"]),
            ]
        else:
            summary_rows = [("Comptes", "MDBList"), ("Données", "Aucune")]

        # Historique
        history_values = []
        for row in sorted(rows, key=lambda r: r.get("watched_at") or datetime.min.replace(tzinfo=PARIS_TZ), reverse=True):
            watched_at = row.get("watched_at")
            history_values.append(
                {
                    "Date": watched_at.strftime("%d/%m/%Y %H:%M") if watched_at else "—",
                    "Type": row.get("type"),
                    "Titre": row.get("title"),
                    "Épisode": row.get("episode_label") or "—",
                    "Année": row.get("year") or "—",
                    "Genres": " · ".join(row.get("genres") or []),
                    "Durée (min)": row.get("runtime") or 0,
                    "Lectures": row.get("plays") or 1,
                    "Note": f"{row['personal_rating']:.1f}/10" if row.get("personal_rating") else "—",
                }
            )
        history_df = pd.DataFrame(history_values)

        # Watchlist
        watchlist_values = []
        sections = dataset.get("sections") or {}
        watchlist = sections.get("watchlist") or {}
        for movie in watchlist.get("movies") or []:
            watchlist_values.append({"Type": "Film", "Titre": movie.get("title") or "?", "Année": movie.get("release_year") or movie.get("year") or "—"})
        for show in watchlist.get("shows") or []:
            watchlist_values.append({"Type": "Série", "Titre": show.get("title") or "?", "Année": show.get("release_year") or show.get("year") or "—"})
        watchlist_df = pd.DataFrame(watchlist_values)

        # Listes
        lists_values = []
        for source in dataset.get("sources") or []:
            if not isinstance(source, dict) or source.get("kind") == "aggregate":
                continue
            movies = source.get("movies") or []
            shows = source.get("shows") or []
            lists_values.append(
                {
                    "Liste": source.get("name") or source.get("label") or "?",
                    "Films": len(movies),
                    "Séries": len(shows),
                    "Total": len(movies) + len(shows),
                }
            )
        lists_df = pd.DataFrame(lists_values)

        # Statistiques (genres + heures)
        stats_values = []
        if not df.empty:
            genre_hours = stats_mod.dna_genres(df)
            total_hours = sum(hours for _, hours in genre_hours) or 1
            for genre, hours in genre_hours:
                stats_values.append(
                    {
                        "Genre": genre,
                        "Heures": round(hours, 1),
                        "%": round(hours / total_hours * 100, 1),
                    }
                )
        stats_df = pd.DataFrame(stats_values)

        # Badges
        achievements_values = []
        if not df.empty:
            result = achievements_mod.compute_achievements(df)
            for _bid, emoji, titre, desc, _cond, _prog in result["badges"]:
                achievements_values.append(
                    {
                        "Badge": f"{emoji} {titre}",
                        "Description": desc,
                        "Obtenu": "Oui" if _cond else "Non",
                        "Progression %": round(_prog, 1),
                    }
                )
        achievements_df = pd.DataFrame(achievements_values)

        excel_bytes = excel_mod.build_excel(
            summary_rows, history_df, watchlist_df, lists_df, stats_df, achievements_df
        )
        st.download_button(
            "📥 Télécharger le rapport Excel",
            data=excel_bytes,
            file_name=f"media-smart-lists-rapport-{date_str}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            key="download_backup_excel",
        )
    except Exception as exc:
        st.warning(f"Impossible de générer le rapport Excel pour le moment : {exc}")

    st.divider()

    # ── Restauration ─────────────────────────────────────────────────────────
    st.markdown("#### 📥 Restaurer une sauvegarde")
    st.caption(
        "L'import ne modifie rien sur MDBList : il recharge simplement les données "
        "dans l'application pour éviter une nouvelle analyse."
    )
    uploaded = st.file_uploader("Choisis un fichier JSON", type=["json"], key="backup_restore")
    if uploaded is not None:
        try:
            data = json.load(uploaded)
        except Exception:
            st.error("Fichier JSON invalide.")
            data = None
        if data:
            saved = data.get("dataset")
            if isinstance(saved, dict) and saved.get("sections"):
                st.markdown(
                    f'<div class="accent-callout"><strong>✅ SAUVEGARDE VALIDE</strong> · '
                    f'Export du {str(data.get("export_date") or "?").replace("T", " ")[:16]}.</div>',
                    unsafe_allow_html=True,
                )
                if st.button("🔄 Restaurer dans l'application", type="primary", key="restore_backup"):
                    st.session_state["_normalized_dataset"] = saved
                    st.session_state.pop("_source_genre_cache", None)
                    st.rerun()
            else:
                st.error("Format de sauvegarde non reconnu (dataset manquant).")


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
elif page == "👻 Progression Fantôme":
    render_ghost_page()
elif page == "🧹 Nettoyage des listes":
    render_static_lists_page()
elif page == "🎯 Que regarder ?":
    render_watchlist_page()
elif page == "📅 Calendrier des sorties":
    render_calendar_page()
elif page == "📊 Statistiques":
    render_basic_stats_page()
elif page == "🎬 Rendez-vous annuel":
    render_annual_page()
elif page == "🏆 Succès":
    render_achievements_page()
elif page == "📤 Sauvegarde":
    render_backup_page()
else:
    placeholder(page)

st.caption(f"{APP_NAME} · {APP_VERSION} · aucun accès Trakt requis")
