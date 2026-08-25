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
import requests
from concurrent.futures import ThreadPoolExecutor

import mdblist_oauth as mdb_oauth
import achievements_engine as achievements_mod
import dashboard_engine as dashboard_mod
import excel_export as excel_mod
import stats_engine as stats_mod
import migration_engine as mig_mod
import trakt_zip_provider
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
    membership_index,
    rows_to_csv,
    rows_to_json,
    source_display_label,
)
from mdblist_provider import MDBListProvider
from genre_translations import translate_genre as _tr_genre
from normalized_model import NORMALIZED_SCHEMA_VERSION, dedupe, normalize_provider_dataset
from playback_engine import (
    DEFAULT_PLAYBACK_SORT,
    PLAYBACK_PROGRESS_OPTIONS,
    PLAYBACK_SORT_OPTIONS,
    enrich_playback_posters,
    filter_playback_rows,
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
    "📦 Migration Trakt → MDBList",
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
        --am-yellow: #FFE100;
        --am-bg-card: rgba(8, 55, 50, 0.75);
        --am-bg-card-hover: rgba(12, 75, 68, 0.85);
        --am-border: rgba(0, 163, 146, 0.45);
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
        background: rgba(0, 0, 0, 0.70) !important;
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
        color: var(--am-text);
        font-family: 'ManropeMSL', 'DejaVu Sans', sans-serif;
        font-size: clamp(1.75rem, 4vw, 2.55rem);
        font-weight: 900;
        line-height: 1;
        margin: .35rem 0 .3rem;
    }
    .brand-rule {
        background: linear-gradient(90deg, var(--am-green), var(--am-yellow));
        border-radius: 2px;
        height: 3px;
        max-width: 330px;
    }
    .brand-kicker {
        color: var(--am-yellow);
        font-family: 'ManropeMSL', 'DejaVu Sans', sans-serif;
        font-size: .80rem;
        font-weight: 900;
        letter-spacing: .16em;
        margin-bottom: .45rem;
        text-transform: uppercase;
    }

    .accent-callout {
        background: linear-gradient(135deg, rgba(0, 163, 146, .08), rgba(0, 0, 0, .55));
        border: 1px solid rgba(255, 225, 0, .55);
        border-left: 4px solid var(--am-yellow);
        border-radius: 13px;
        color: var(--am-text);
        font-size: .88rem;
        line-height: 1.45;
        margin: .55rem 0 .9rem;
        padding: .62rem .85rem;
    }
    .accent-callout strong {
        color: var(--am-yellow);
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
    .guide-step {
        background: linear-gradient(135deg, rgba(0, 163, 146, .08), rgba(0, 0, 0, .55));
        border: 1px solid rgba(255, 225, 0, .45);
        border-left: 3px solid var(--am-yellow);
        border-radius: 10px;
        color: var(--am-text) !important;
        font-size: .86rem;
        line-height: 1.4;
        margin: .25rem 0;
        padding: .45rem .7rem;
    }
    .guide-step strong { color: var(--am-text); }
    .guide-step a { color: var(--am-yellow); text-decoration: underline; }
    .source-card h3 {
        color: var(--am-text);
        margin: .45rem 0 .5rem;
    }
    .placeholder-card h3 {
        color: var(--am-green);
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
        border-left: 4px solid var(--am-yellow);
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
        border-left: 4px solid var(--am-yellow);
        min-height: 154px;
    }
    .score-badge {
        background: linear-gradient(135deg, rgba(0, 163, 146, .16), rgba(0, 0, 0, .50));
        border: 1px solid rgba(255, 225, 0, .55);
        border-radius: 10px;
        color: var(--am-yellow);
        display: inline-block;
        font-size: .82rem;
        font-weight: 800;
        margin-top: .4rem;
        padding: .28rem .5rem;
    }
    .score-badge[data-tooltip], .mc-note[data-tooltip], .mc-type[data-tooltip],
    .mc-year[data-tooltip], .media-list-pct[data-tooltip], .mc-inline-pct[data-tooltip],
    .mc-chip[data-tooltip] {
        position: relative; cursor: help;
    }
    .score-badge[data-tooltip]::after,
    .mc-note[data-tooltip]::after,
    .mc-type[data-tooltip]::after,
    .mc-year[data-tooltip]::after,
    .media-list-pct[data-tooltip]::after,
    .mc-inline-pct[data-tooltip]::after,
    .mc-chip[data-tooltip]::after {
        content: attr(data-tooltip);
        position: absolute;
        bottom: calc(100% + 8px);
        left: 50%;
        transform: translateX(-50%) translateY(4px);
        background: rgba(0, 0, 0, .95);
        border: 1px solid rgba(255, 225, 0, .50);
        border-radius: 10px;
        color: var(--am-text);
        font-size: .72rem;
        font-weight: 500;
        line-height: 1.4;
        max-width: 240px;
        min-width: 180px;
        width: max-content;
        padding: .45rem .55rem;
        opacity: 0;
        visibility: hidden;
        pointer-events: none;
        transition: opacity .15s ease, transform .15s ease;
        z-index: 9999;
        text-align: left;
        white-space: normal;
    }
    .score-badge[data-tooltip]:hover::after,
    .mc-note[data-tooltip]:hover::after,
    .mc-type[data-tooltip]:hover::after,
    .mc-year[data-tooltip]:hover::after,
    .media-list-pct[data-tooltip]:hover::after,
    .mc-inline-pct[data-tooltip]:hover::after,
    .mc-chip[data-tooltip]:hover::after {
        opacity: 1;
        visibility: visible;
        transform: translateX(-50%) translateY(0);
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
        background: rgba(255,225,0,.10);
        border: 1px solid rgba(255,225,0,.35);
        color: var(--am-yellow);
    }
    .info-pill:focus { outline: 2px solid var(--am-yellow); outline-offset: 2px; }
    .info-pill::after {
        background: rgba(0, 0, 0, .92);
        border: 1px solid rgba(0, 163, 146, .50);
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
        background: linear-gradient(90deg, #FFE100, #FFC400);
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
        background: linear-gradient(135deg, rgba(0, 163, 146, .18), rgba(0, 0, 0, .32));
        border: 1px solid rgba(255, 225, 0, .55);
        border-radius: 999px;
        color: var(--am-text);
        display: inline-block;
        font-size: .72rem;
        font-weight: 800;
        padding: .24rem .6rem;
    }
    /* Liens contenus : petits badges discrets, neutres, jaune au survol. */
    .link-pill {
        background: rgba(255, 255, 255, .05);
        border: 1px solid rgba(255, 255, 255, .22);
        border-radius: 999px;
        color: var(--am-text) !important;
        cursor: pointer;
        display: inline-block;
        font-size: .68rem;
        font-weight: 700;
        margin: .15rem .15rem 0 0;
        padding: .18rem .5rem;
        text-decoration: none !important;
        transition: background .15s ease, border-color .15s ease, color .15s ease;
    }
    .link-pill:hover {
        background: rgba(255, 225, 0, .08);
        border-color: var(--am-yellow);
        color: var(--am-yellow) !important;
    }

    /* Boutons historiques : verre vert, sans ombre.
       Sélecteurs universels : le data-testid est porté par le bouton
       lui-même (ou une div wrapper) selon la version de Streamlit. */
    .stButton > button,
    div[data-testid="stButton"] > button,
    [data-testid="stButton"] button,
    [data-testid="stBaseButton-secondary"],
    [data-testid="stBaseButton-primary"],
    [data-testid="baseButton-secondary"],
    [data-testid="baseButton-primary"],
    [data-testid="stDownloadButton"] button,
    [data-testid="stDownloadButton"] a,
    [data-testid="stFormSubmitButton"] button {
        background: rgba(5, 38, 34, 0.75) !important;
        border: 1px solid rgba(0,163,146,0.30) !important;
        border-radius: 16px !important;
        box-shadow: none !important;
        color: var(--am-text) !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
        font-weight: 600 !important;
        min-height: 3rem;
        padding: .75em 1.3em !important;
        text-shadow: none !important;
        width: 100% !important;
    }
    .stButton > button p,
    div[data-testid="stButton"] > button p,
    [data-testid="stButton"] button p {
        text-align: center !important;
        margin: 0 !important;
    }
    .stButton > button:hover,
    div[data-testid="stButton"] > button:hover,
    [data-testid="stButton"] button:hover,
    [data-testid="stBaseButton-secondary"]:hover,
    [data-testid="stBaseButton-primary"]:hover,
    [data-testid="baseButton-secondary"]:hover,
    [data-testid="baseButton-primary"]:hover,
    [data-testid="stDownloadButton"] button:hover,
    [data-testid="stDownloadButton"] a:hover,
    [data-testid="stFormSubmitButton"] button:hover {
        background: rgba(8, 55, 50, 0.85) !important;
        border-color: rgba(0,163,146,0.50) !important;
        box-shadow: none !important;
    }
    .stButton > button[kind="primary"],
    div[data-testid="stButton"] > button[kind="primary"],
    [data-testid="stBaseButton-primary"],
    [data-testid="baseButton-primary"],
    [data-testid="stDownloadButton"] button[kind="primary"],
    [data-testid="stDownloadButton"] button[data-testid="stBaseButton-primary"] {
        background: linear-gradient(135deg, var(--am-green), var(--am-green-aston)) !important;
        border: none !important;
        color: #fff !important;
        font-weight: 700 !important;
    }
    .stButton > button[kind="primary"]:hover,
    div[data-testid="stButton"] > button[kind="primary"]:hover,
    [data-testid="stBaseButton-primary"]:hover,
    [data-testid="baseButton-primary"]:hover,
    [data-testid="stDownloadButton"] button[kind="primary"]:hover,
    [data-testid="stDownloadButton"] button[data-testid="stBaseButton-primary"]:hover {
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

    /* Barres de progression : remplissage vert (pointe jaune), piste carbone. */
    div[data-testid="stProgress"] [role="progressbar"] > div > div,
    div[data-testid="stProgress"] [role="progressbar"] > div > div > div {
        background: linear-gradient(90deg, #00524B, #00A392) !important;
        border-radius: 999px;
    }
    div[data-testid="stProgress"] [role="progressbar"] > div,
    div[data-testid="stProgress"] > div > div > div {
        background: linear-gradient(90deg, #FFE100, #FFC400) !important;
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
    /* Espacement resserré entre les widgets du tableau de bord : séparateurs
       et expandeurs plus compacts (sans casser le reste de l'app). */
    hr { margin: .45rem 0 !important; }
    div[data-testid="stExpander"] {
        border: 1px solid rgba(18, 90, 84, .42) !important;
        border-radius: 12px !important;
        background: rgba(8, 55, 50, .28) !important;
        margin-bottom: .3rem !important;
    }
    div[data-testid="stExpander"] details { padding: .05rem .35rem !important; }
    div[data-testid="stExpander"] summary {
        padding: .5rem .6rem !important;
        min-height: 2.2rem;
    }
    p, li, label { color: var(--am-text) !important; }
    .stCaption { color: var(--am-text-muted) !important; }

    /* ══════════════════════════════════════════════════════════════════
       SKIN « PREVIEW-LOOK » (V52) — rubans déroulants, comet biseauté,
       grain, swoosh. Le thème reste compatible : si un élément déplaît,
       le backup V51 permet de revenir en arrière.
       ══════════════════════════════════════════════════════════════════ */

    /* Fondu en cascade (même courbe que le site sport-auto) */
    @keyframes msl-fadeUp {
        from { opacity: 0; transform: translateY(14px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    /* Comet biseauté sur la barre du haut : version précédente, fines
       rayures discrètes (vert + jaune subtil). */
    header[data-testid="stHeader"]::before {
        content: "";
        position: absolute; top: 0; bottom: 0; left: 0; right: 0;
        transform: translateX(-100%);
        -webkit-clip-path: polygon(21px 0, 100% 0, calc(100% - 21px) 100%, 0 100%);
                clip-path: polygon(21px 0, 100% 0, calc(100% - 21px) 100%, 0 100%);
        background: repeating-linear-gradient(115deg,
            rgba(0, 163, 146, .95) 0px, rgba(0, 163, 146, .95) 2px,
            rgba(255, 225, 0, .25) 2px, rgba(255, 225, 0, .25) 5px);
        -webkit-mask-image: linear-gradient(90deg, rgba(0,0,0,.16) 0%, rgba(0,0,0,.5) 55%, rgba(0,0,0,1) 100%);
                mask-image: linear-gradient(90deg, rgba(0,0,0,.16) 0%, rgba(0,0,0,.5) 55%, rgba(0,0,0,1) 100%);
        animation: msl-comet 8s linear infinite;
        pointer-events: none;
        z-index: 0;
        overflow: hidden;
    }
    @keyframes msl-comet { to { transform: translateX(100%); } }

    /* Grain subtil du fond (comme le site sport-auto) */
    .stApp::before {
        content: "";
        position: fixed; inset: 0; pointer-events: none; z-index: 0; opacity: .045;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='140' height='140'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='140' height='140' filter='url(%23n)'/%3E%3C/svg%3E");
    }

    /* Swoosh (trait dégradé) sous les titres de page */
    .page-title::after {
        content: "";
        display: block;
        width: clamp(180px, 26vw, 420px);
        height: 3px;
        margin-top: 10px;
        border-radius: 3px;
        background: linear-gradient(90deg, rgba(0,163,146,0) 0%, rgba(0,163,146,.95) 50%, rgba(0,163,146,0) 100%);
    }

    /* Ruban déroulant (widgets du tableau de bord) */
    details.msl-widget {
        background: rgba(255,255,255,.045);
        border: 1px solid rgba(0,163,146,.18);
        border-radius: 13px;
        margin-bottom: 9px;
        overflow: hidden;
        transition: transform .16s ease, background .16s ease, border-color .16s ease, box-shadow .16s ease;
        animation: msl-fadeUp .55s cubic-bezier(.22,1,.36,1) both;
    }
    details.msl-widget:hover {
        background: rgba(0,163,146,.16);
        border-color: rgba(0,163,146,.55);
        transform: translateY(-2px);
        box-shadow: 0 8px 22px rgba(0,163,146,.22);
    }
    details.msl-widget summary {
        display: flex; align-items: center; gap: 12px;
        padding: 11px 14px; cursor: pointer; list-style: none; user-select: none;
    }
    details.msl-widget summary::-webkit-details-marker { display: none; }
    details.msl-widget summary::marker { content: ""; }
    .msl-ic {
        width: 42px; height: 42px; flex: 0 0 auto; display: flex; align-items: center; justify-content: center;
        font-size: 20px; border-radius: 11px;
        background: linear-gradient(180deg, #0C2E28 0%, #041710 100%);
        box-shadow: inset 0 1px 0 rgba(255,255,255,.10), inset 0 0 0 1px rgba(0,163,146,.10),
                    0 10px 22px -12px rgba(0,0,0,.7);
        transition: background .18s ease, box-shadow .18s ease;
    }
    details.msl-widget:hover .msl-ic {
        background: linear-gradient(180deg, #00A392 0%, #00524B 100%);
        box-shadow: inset 0 1px 0 rgba(255,255,255,.18), 0 12px 26px -10px rgba(0,163,146,.6);
    }
    .msl-nm { flex: 1; font-size: 14.5px; font-weight: 700; color: var(--am-text); line-height: 1.25; min-width: 0; }
    .msl-nm .msl-meta { display: block; font-size: 12px; font-weight: 500; color: var(--am-text-muted); margin-top: 2px; }
    .msl-chev { color: var(--am-text-muted); font-size: 13px; flex: 0 0 auto; transition: transform .2s ease; }
    details.msl-widget[open] .msl-chev { transform: rotate(180deg); }
    .msl-body { padding: 6px 14px 14px; border-top: 1px solid rgba(0,163,146,.14); }
    .msl-body .msl-line { font-size: .9rem; color: var(--am-text); padding: 5px 0; line-height: 1.55; }
    .msl-body .msl-line .muted { color: var(--am-text-muted); }
    .msl-body .msl-note { font-size: .78rem; color: var(--am-text-muted); padding: 6px 0 0; line-height: 1.45; }
    .msl-grid2 { display: grid; grid-template-columns: 1.1fr .9fr; gap: 12px; }
    .msl-grid3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
    .msl-subcard {
        background: var(--am-bg-card); border: 1px solid var(--am-border); border-radius: 12px;
        padding: 12px 14px;
        transition: transform .16s ease, background .16s ease;
    }
    .msl-subcard:hover { background: rgba(12,75,68,.6); transform: translateY(-2px); }
    .msl-subcard .k { font-size: .74rem; letter-spacing: 1px; text-transform: uppercase; color: var(--am-text-muted); }
    .msl-subcard .v { font-size: 1.25rem; font-weight: 800; color: var(--am-text); margin-top: 3px; line-height: 1.15; }
    .msl-subcard .d { font-size: .78rem; color: var(--am-text-muted); margin-top: 2px; line-height: 1.4; }
    .msl-stats2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 4px; }
    .msl-bar {
        display: flex; height: 10px; border-radius: 999px; overflow: hidden;
        margin: 10px 0 12px; border: 1px solid rgba(0,163,146,.35);
    }
    .msl-bar span { display: block; }
    .msl-bar.jauge { height: 8px; }
    .msl-bar.jauge span { background: linear-gradient(90deg, #00524B, #00A392); }
    .msl-legend2 { font-size: .72rem; color: var(--am-text-muted); margin: 2px 0 10px; }
    .msl-legend { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; margin-top: 4px; }
    .msl-creneau {
        background: var(--am-bg-card); border: 1px solid var(--am-border); border-radius: 12px;
        padding: 10px 12px; text-align: center;
    }
    .msl-creneau .lb { font-size: 1.05rem; font-weight: 800; color: var(--am-text); }
    .msl-creneau .pl { font-size: .72rem; color: var(--am-text-muted); margin-top: 2px; }
    .msl-creneau .v { font-size: 1.5rem; font-weight: 800; color: var(--am-text); margin-top: 6px; }
    .msl-creneau .d { font-size: .78rem; color: var(--am-text-muted); margin-top: 2px; }
    .msl-cols { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 10px; }
    .msl-coup {
        background: var(--am-bg-card); border: 1px solid var(--am-border); border-radius: 12px;
        padding: 10px 12px; text-align: center;
        transition: transform .16s ease;
    }
    .msl-coup:hover { transform: translateY(-2px); }
    .msl-coup .emoji { font-size: 1.4rem; }
    .msl-coup .t { font-size: .84rem; font-weight: 700; color: var(--am-text); margin-top: 4px; }
    .msl-coup .s { font-size: .74rem; color: var(--am-yellow); margin-top: 2px; }

    /* Bandeau de métriques moderne (skin V53) : cartes k/v/d avec icône,
       fondu en cascade, surbrillance au survol — comme preview-look.html. */
    .msl-metrics {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(155px, 1fr));
        gap: 12px;
        margin: 14px 0;
    }
    .msl-mcard {
        background: rgba(255,255,255,.045);
        border: 1px solid rgba(0,163,146,.18);
        border-radius: 13px;
        padding: 12px 14px;
        position: relative;
        transition: transform .16s ease, background .16s ease, border-color .16s ease, box-shadow .16s ease;
        animation: msl-fadeUp .55s cubic-bezier(.22,1,.36,1) both;
    }
    .msl-mcard:hover {
        background: rgba(0,163,146,.14);
        border-color: rgba(0,163,146,.55);
        transform: translateY(-3px);
        box-shadow: 0 10px 26px rgba(0,163,146,.22);
    }
    .msl-mcard .ic { position: absolute; top: 10px; right: 12px; font-size: 1.15rem; opacity: .85; }
    .msl-mcard .k {
        font-size: .72rem; letter-spacing: .6px; text-transform: uppercase;
        color: var(--am-text-muted); padding-right: 26px; line-height: 1.25;
    }
    .msl-mcard .v { font-size: 1.35rem; font-weight: 800; color: var(--am-text); margin-top: 4px; line-height: 1.1; }
    .msl-mcard .d { font-size: .74rem; color: var(--am-text-muted); margin-top: 3px; line-height: 1.35; }

    /* Expandeurs natifs des autres pages : habillage « ruban » cohérent */
    div[data-testid="stExpander"] {
        background: rgba(8,55,50,.35) !important;
        border: 1px solid rgba(0,163,146,.22) !important;
        border-radius: 13px !important;
        box-shadow: none !important;
    }
    div[data-testid="stExpander"] summary {
        font-weight: 700 !important;
        color: var(--am-text) !important;
    }

    /* Survol léger des cartes contenus (skin V55) : soulèvement + lueur,
       comme les rubans — sans rien casser (posters, liens, infos). */
    .media-list-card {
        transition: transform .16s ease, background .16s ease, border-color .16s ease, box-shadow .16s ease;
    }
    .media-list-card:hover {
        background: rgba(0, 163, 146, .12);
        border-color: rgba(0, 163, 146, .55);
        border-left-color: var(--am-yellow);
        transform: translateY(-2px);
        box-shadow: 0 8px 22px rgba(0, 163, 146, .18);
    }

    /* Cartes contenus premium (V56) : posters liserés, en-tête chip/note,
       badges type et note publique uniformes sur toutes les pages. */
    .media-list-card img {
        border-radius: 10px;
        border: 1px solid rgba(0, 163, 146, .35);
        box-shadow: 0 4px 14px rgba(0, 0, 0, .35), inset 0 0 0 1px rgba(255, 255, 255, .04);
    }
    .media-list-card strong { font-size: 1.02rem; }
    .mc-head {
        display: flex; align-items: center; flex-wrap: wrap; gap: 8px;
        margin-bottom: 4px;
    }
    .mc-head strong { flex: 1 1 auto; min-width: 0; }
    .mc-year {
        display: inline-block;
        color: var(--am-yellow);
        background: linear-gradient(135deg, rgba(0, 163, 146, .16), rgba(0, 0, 0, .50));
        border: 1px solid rgba(255, 225, 0, .45);
        border-radius: 999px;
        padding: .05rem .5rem;
        font-size: .72rem;
        font-weight: 700;
        white-space: nowrap;
    }
    .mc-type {
        display: inline-flex; align-items: center;
        color: var(--am-text-muted);
        font-size: .64rem; font-weight: 800;
        letter-spacing: .08em; text-transform: uppercase;
        white-space: nowrap;
    }
    .mc-chip {
        display: inline-block;
        font-size: .68rem; font-weight: 800; letter-spacing: .4px;
        color: var(--am-text);
        background: rgba(0, 163, 146, .16);
        border: 1px solid rgba(0, 163, 146, .4);
        border-radius: 999px;
        padding: 2px 9px;
    }
    .mc-note {
        display: inline-block;
        font-size: .68rem; font-weight: 800;
        color: var(--am-yellow);
        background: linear-gradient(135deg, rgba(0, 163, 146, .16), rgba(0, 0, 0, .50));
        border: 1px solid rgba(255, 225, 0, .50);
        border-radius: 999px;
        padding: 2px 9px;
    }
    .mc-outside {
        display: inline-block;
        font-size: .68rem; font-weight: 800; color: #fff;
        background: linear-gradient(135deg, rgba(45, 156, 219, .30), rgba(0, 0, 0, .55));
        border: 1px solid rgba(45, 156, 219, .65);
        border-radius: 999px; padding: 2px 9px;
    }
    .mc-outside[data-tooltip] { position: relative; cursor: help; }
    .mc-outside[data-tooltip]::after {
        content: attr(data-tooltip); position: absolute;
        bottom: calc(100% + 8px); left: 50%;
        transform: translateX(-50%) translateY(4px);
        background: rgba(0, 0, 0, .95);
        border: 1px solid rgba(45, 156, 219, .50);
        border-radius: 10px; color: var(--am-text);
        font-size: .72rem; font-weight: 500; line-height: 1.4;
        max-width: 240px; min-width: 180px; width: max-content;
        padding: .45rem .55rem; opacity: 0; visibility: hidden;
        pointer-events: none; transition: opacity .15s ease, transform .15s ease;
        z-index: 9999; text-align: left; white-space: normal;
    }
    .mc-outside[data-tooltip]:hover::after {
        opacity: 1; visibility: visible; transform: translateX(-50%) translateY(0);
    }

    /* Tuile fallback quand un poster est absent (fantômes, reprises) :
       emoji sur fond dégradé, mêmes dimensions qu'un poster — la carte
       n'est plus jamais vide. */
    .msl-poster-fallback {
        display: flex; align-items: center; justify-content: center;
        height: 132px; width: 88px; flex: 0 0 auto;
        font-size: 30px; border-radius: 10px;
        background: linear-gradient(180deg, #0C2E28 0%, #041710 100%);
        box-shadow: inset 0 1px 0 rgba(255,255,255,.08), inset 0 0 0 1px rgba(0,163,146,.14);
    }
    .media-list-card.upnext-card .msl-poster-fallback { height: 150px; width: 100px; }

    /* ── Cartes contenus compactes (V57) : hauteur proche du poster,
       métrique (%, score, horaire) recentrée verticalement à droite. ── */
    .media-list-card {
        padding: .5rem .6rem;
        gap: .7rem;
    }
    .media-list-content { line-height: 1.4; }
    .media-list-content small { margin-top: .14rem; }
    .media-list-pct {
        align-self: stretch;
        align-items: center;
        border-left: 1px solid rgba(0, 163, 146, .20);
        color: var(--am-yellow);
        display: flex;
        flex: 0 0 auto;
        flex-direction: column;
        font-size: 1.3rem;
        font-weight: 800;
        justify-content: center;
        min-width: 78px;
        padding: .25rem .55rem;
        text-align: center;
    }
    .media-list-pct .sub {
        color: var(--am-text-muted);
        display: block;
        font-size: .6rem;
        font-weight: 600;
        letter-spacing: .05em;
        margin-top: 2px;
        text-transform: uppercase;
    }
    .mc-inline-pct {
        display: none;
        color: var(--am-yellow);
        font-weight: 800;
        background: linear-gradient(135deg, rgba(0, 163, 146, .16), rgba(0, 0, 0, .50));
        border: 1px solid rgba(255, 225, 0, .50);
        border-radius: 999px;
        padding: .12rem .5rem;
        font-size: .75rem;
        white-space: nowrap;
    }
    .links-spacer { margin-left: auto; display: inline-flex; align-items: center; }
    .gsm-only { display: none; }
    .only-gsm { display: none; }
    details.pills-details { margin-top: .35rem; }
    details.pills-details summary {
        cursor: pointer;
        color: var(--am-yellow);
        font-size: .72rem;
        font-weight: 700;
    }
    details.pills-details .reason-pill,
    details.pills-details .warning-pill { margin-top: .2rem; }

    @media (max-width: 768px) {
        .msl-grid2 { grid-template-columns: 1fr; }
        .msl-grid3 { grid-template-columns: 1fr; }
        /* Espace sous le bandeau du haut sur mobile : le wordmark respire. */
        .block-container { padding-top: 3.6rem !important; }
        .brand-title { font-size: 1.7rem; margin-top: .9rem; }
        .media-list-card img {
            height: 114px;
            width: 76px;
        }
        .media-list-card.upnext-card img {
            height: 126px;
            width: 84px;
        }
        .msl-poster-fallback { height: 114px; width: 76px; }
        .media-list-card.upnext-card .msl-poster-fallback { height: 126px; width: 84px; }
        /* Sur mobile, la métrique (%, score, horaire) s'affiche en ligne
           dans le texte : plus de colonne dédiée, aucun espace perdu. */
        .media-list-pct { display: none !important; }
        .mc-inline-pct { display: inline-block !important; }
        .gsm-only { display: inline-block !important; margin-left: auto; }
        .only-gsm { display: inline-block !important; }
        details.only-gsm { display: block !important; }
        .only-pc { display: none !important; }
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
            st.markdown("<div style='height:1.2rem;'></div>", unsafe_allow_html=True)
            if st.button("🔌 Se déconnecter de MDBList", key="logout_sidebar", use_container_width=True):
                mdb_oauth.disconnect(cookies)
                try:
                    cookies.remove("msl_mdblist_data_loaded")
                except Exception:
                    pass
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
    remaining = account.get("rate_limit_remaining")
    limit = account.get("rate_limit")
    st.markdown(
        _metric_cards([
            {"emoji": "🎫", "k": "Forfait", "v": account.get("plan") or "—", "d": "compte MDBList"},
            {"emoji": "🧮", "k": "Quota restant",
             "v": f"{remaining}/{limit}" if remaining is not None and limit else "—", "d": "requêtes API"},
            {"emoji": "🗂️", "k": "Listes actuelles", "v": lists_summary.get("total", 0), "d": "créées"},
            {"emoji": "🔒", "k": "Limite de listes", "v": account.get("list_limit") or "—", "d": "selon le forfait"},
        ]),
        unsafe_allow_html=True,
    )
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
        # Lien direct : la page s'ouvre avec le code déjà pré-rempli.
        direct_url = complete_url or verification_uri
        st.markdown(
            f'<div class="accent-callout"><strong>SANS SMARTPHONE</strong> · '
            f'Ouvre le lien direct ci-dessous, le code sera déjà saisi :<br>'
            f'<a href="{escape(direct_url, quote=True)}" target="_blank" rel="noopener noreferrer" '
            f'style="color:#FFE100;font-weight:700;word-break:break-all;">{escape(direct_url)}</a></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="accent-callout"><strong>CODE MDBLIST</strong> · '
            f'<span style="color:#FFE100;font-size:1.18rem;font-weight:800;letter-spacing:3px;">'
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
        # Déjà connecté : ne PAS réafficher le ruban compte/quota (il est
        # affiché dans la section « Vos données MDBList » du dashboard).
        account = mdb_oauth.account_summary() or {}
        st.markdown(
            f'<div class="accent-callout"><strong>✓ CONNECTÉ À MDBLIST</strong> · '
            f'{escape(str(account.get("username") or "Compte MDBList"))} — '
            'tu peux charger tes données dans la section « Vos données MDBList » ci-dessous.</div>',
            unsafe_allow_html=True,
        )
        return

    # Démarrage automatique : dès qu'on arrive sur cet écran, on lance le flux
    # OAuth et on affiche directement le QR code (plus de clic intermédiaire).
    flow = mdb_oauth.current_flow()
    if not flow:
        started, message = mdb_oauth.start_device_flow()
        if not started:
            st.markdown(
                f'<div class="accent-callout"><strong>CONNEXION IMPOSSIBLE</strong> · '
                f'{escape(message)}</div>',
                unsafe_allow_html=True,
            )
            return
        flow = mdb_oauth.current_flow()

    if flow:
        _render_device_flow(flow)


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


def _enrich_zip_dataset() -> tuple[bool, str]:
    """Enrichit un dataset issu d'un ZIP Trakt avec les métadonnées MDBList
    (genres, posters, durées, notes) via appels groupés, sans écrire sur
    aucun compte. Nécessite une session MDBList (lecture seule)."""
    dataset = _dataset()
    if not dataset or str(dataset.get("source") or "") != "trakt_zip":
        return False, "Enrichissement réservé aux données issues d'un ZIP Trakt."
    valid, message = mdb_oauth.ensure_valid_session(cookies)
    if not valid:
        return False, message or "Connecte MDBList pour enrichir (lecture seule)."
    sections = dataset.get("sections") or {}

    # Collecte des identifiants TMDb et IMDb (films et séries).
    tmdb_ids: list[int] = []
    imdb_ids: list[str] = []
    seen_tmdb: set[int] = set()
    seen_imdb: set[str] = set()

    def push(media: Any) -> None:
        if not isinstance(media, dict):
            return
        ids = media.get("ids") if isinstance(media.get("ids"), dict) else {}
        raw = ids.get("tmdb")
        try:
            media_id = int(raw)
        except (TypeError, ValueError):
            media_id = None
        if media_id and media_id > 0 and media_id not in seen_tmdb:
            seen_tmdb.add(media_id)
            tmdb_ids.append(media_id)
        imdb = str(ids.get("imdb") or "").strip()
        if imdb and imdb not in seen_imdb:
            seen_imdb.add(imdb)
            imdb_ids.append(imdb)

    watched = sections.get("watched") or {}
    for row in watched.get("movies") or []:
        push(row.get("movie") if isinstance(row.get("movie"), dict) else row)
    for row in watched.get("shows") or []:
        push(row.get("show") if isinstance(row.get("show"), dict) else row)
    for row in watched.get("episodes") or []:
        show = (row.get("episode") or {}).get("show") if isinstance(row.get("episode"), dict) else row.get("show")
        push(show or row)
    watchlist = sections.get("watchlist") or {}
    for movie in watchlist.get("movies") or []:
        push(movie)
    for show in watchlist.get("shows") or []:
        push(show)
    for item in sections.get("user_lists") or []:
        if not isinstance(item, dict):
            continue
        for movie in item.get("movies") or []:
            push(movie)
        for show in item.get("shows") or []:
            push(show)
    # Séries en cours et reprises en pause : leurs médias doivent aussi être enrichis.
    for row in sections.get("upnext") or []:
        if isinstance(row, dict):
            push(row.get("show"))
    for row in sections.get("playback") or []:
        if not isinstance(row, dict):
            continue
        push(row.get("movie"))
        push(row.get("show"))
        episode_obj = row.get("episode")
        if isinstance(episode_obj, dict):
            push(episode_obj.get("show"))
            push(episode_obj)

    if not tmdb_ids and not imdb_ids:
        return False, "Aucun identifiant TMDb ou IMDb trouvé dans le ZIP pour l'enrichissement."

    # Enrichir TOUS les contenus : les appels groupés acceptent 200 ids max.
    # Le nombre d'appels reste raisonnable (1 appel par tranche de 200).
    try:
        provider = MDBListProvider(mdb_oauth.access_token())
    except Exception as exc:
        return False, f"MDBList n'a pas pu être interrogé : {exc}"

    metadata: list[dict[str, Any]] = []
    for index in range(0, max(len(tmdb_ids), len(imdb_ids), 1), 200):
        tchunk = tmdb_ids[index:index + 200]
        ichunk = imdb_ids[index:index + 200]
        try:
            metadata.extend(provider.media_info_batch(tmdb_ids=tchunk or None, imdb_ids=ichunk or None))
        except Exception as exc:
            return False, f"MDBList a interrompu l'enrichissement (lot {index // 200 + 1}) : {exc}"

    by_tmdb: dict[int, dict[str, Any]] = {}
    by_imdb: dict[str, dict[str, Any]] = {}
    for item in metadata:
        if not isinstance(item, dict):
            continue
        ids = item.get("ids") if isinstance(item.get("ids"), dict) else {}
        raw = ids.get("tmdb")
        try:
            media_id = int(raw)
        except (TypeError, ValueError):
            media_id = None
        if media_id and media_id > 0:
            by_tmdb[media_id] = item
        raw_imdb = ids.get("imdb")
        if raw_imdb:
            by_imdb[str(raw_imdb).strip()] = item

    def _titles_coherent(expected: str, candidate: Any) -> bool:
        """Vérifie que la fiche reçue correspond au titre attendu (anti-mauvais
        poster quand un identifiant du ZIP est erroné, ex. The Middle ↔ The
        Departed). Comparaison souple : mots significatifs en commun."""
        candidate_title = ""
        if isinstance(candidate, dict):
            candidate_title = str(candidate.get("title") or candidate.get("name") or "")
        if not candidate_title:
            return True  # pas de fiche exploitable → on n'applique rien
        import unicodedata
        def norm(text: str) -> str:
            return "".join(c for c in unicodedata.normalize("NFD", text.lower()) if not unicodedata.combining(c))
        words_a = {w for w in norm(str(expected)).split() if len(w) > 3}
        words_b = {w for w in norm(candidate_title).split() if len(w) > 3}
        if not words_a or not words_b:
            return True  # titres trop courts → ne pas bloquer
        return bool(words_a & words_b)

    def apply(media: Any) -> None:
        if not isinstance(media, dict):
            return
        ids = media.get("ids") if isinstance(media.get("ids"), dict) else {}
        meta = None
        expected_title = str(media.get("title") or media.get("name") or "")
        try:
            media_id = int(ids.get("tmdb"))
        except (TypeError, ValueError):
            media_id = None
        if media_id:
            meta = by_tmdb.get(media_id)
            if meta is not None and not _titles_coherent(expected_title, meta):
                meta = None  # id TMDb probablement faux → on ignore
        if meta is None:
            imdb = str(ids.get("imdb") or "").strip()
            if imdb:
                meta = by_imdb.get(imdb)
                if meta is not None and not _titles_coherent(expected_title, meta):
                    meta = None
        if not meta:
            return
        if not media.get("genres") and meta.get("genres"):
            genres = meta["genres"]
            names = [g.get("name") or g.get("title") or str(g) for g in genres if isinstance(g, (dict, str))]
            media["genres"] = [n for n in names if n]
        if not media.get("poster") and meta.get("poster"):
            media["poster"] = meta["poster"]
        if not media.get("runtime") and meta.get("runtime"):
            media["runtime"] = meta["runtime"]
        if meta.get("score_average") is not None and media.get("score_average") is None:
            media["score_average"] = meta["score_average"]
        if meta.get("score") is not None and media.get("score") is None:
            media["score"] = meta["score"]
        # Métadonnées qui alimentent les signaux de recommandation :
        # votes (👥 Apprécié du public, 💎 Pépite), pays (🌍 Cinéma),
        # certification (👨‍👩‍👧 Famille), statut (✅ Terminée), studios (🏢).
        if not media.get("ratings") and meta.get("ratings"):
            media["ratings"] = meta["ratings"]
        if not media.get("country") and meta.get("country"):
            media["country"] = meta["country"]
        if not media.get("certification") and meta.get("certification"):
            media["certification"] = meta["certification"]
        if not media.get("status") and meta.get("status"):
            media["status"] = meta["status"]
        if not media.get("network") and meta.get("network"):
            media["network"] = meta["network"]
        if not media.get("studios") and meta.get("studios"):
            media["studios"] = meta["studios"]
        if not media.get("year") and meta.get("year"):
            media["year"] = meta["year"]
        # Date de sortie : alimente le widget « 📅 Sorties de la semaine »
        # pour les données issues d'un ZIP Trakt enrichi.
        for date_key in ("released", "release_date", "premiere_date", "first_aired"):
            if not media.get(date_key) and meta.get(date_key):
                media[date_key] = meta[date_key]

    def apply_row_media(row: Any, key: str, nested_show: str | None = None) -> None:
        """Applique les métadonnées au média d'une ligne, en suivant le show
        imbriqué le cas échéant (ex. episode.show, upnext.show)."""
        if not isinstance(row, dict):
            return
        media = row.get(key) if isinstance(row.get(key), dict) else row
        if nested_show and isinstance(media, dict):
            child = media.get(nested_show)
            if isinstance(child, dict):
                apply(child)
        apply(media)

    for row in watched.get("movies") or []:
        apply_row_media(row, "movie")
    for row in watched.get("shows") or []:
        apply_row_media(row, "show")
    for row in watched.get("episodes") or []:
        apply_row_media(row, "episode", nested_show="show")
        # Le show parent de l'épisode est aussi enrichi.
        if isinstance(row.get("episode"), dict) and isinstance(row["episode"].get("show"), dict):
            apply(row["episode"]["show"])
    for row in sections.get("upnext") or []:
        apply_row_media(row, "show")
    for row in sections.get("playback") or []:
        apply_row_media(row, "movie")
        apply_row_media(row, "episode", nested_show="show")
        apply_row_media(row, "show")
    for movie in watchlist.get("movies") or []:
        apply(movie)
    for show in watchlist.get("shows") or []:
        apply(show)
    for item in sections.get("user_lists") or []:
        if not isinstance(item, dict):
            continue
        for movie in item.get("movies") or []:
            apply(movie)
        for show in item.get("shows") or []:
            apply(show)

    # Re-normaliser pour reconstruire sources et progressions enrichies.
    raw = {"sections": sections, "source": "trakt_zip",
           "loaded_at": datetime.now(PARIS_TZ).isoformat(), "request_count": provider.request_count}
    enriched = normalize_provider_dataset(raw)
    st.session_state["_normalized_dataset"] = enriched
    st.session_state.pop("_source_genre_cache", None)
    st.session_state.pop("_mdblist_playback_poster_cache", None)
    account = mdb_oauth.account_summary()
    if provider.rate_limit_remaining is not None and account:
        account["rate_limit_remaining"] = provider.rate_limit_remaining
        st.session_state[mdb_oauth.ACCOUNT_KEY] = account
        mdb_oauth.persist_cookie(cookies)
    return True, f"{len(by_tmdb)} fiche(s) MDBList fusionnée(s) : genres, posters, durées et notes ajoutés."


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


def _poster_html(poster: str, media_type: str = "") -> str:
    """Poster de la carte contenus, ou tuile fallback élégante (emoji sur
    fond dégradé) quand le poster est absent — la carte n'est plus jamais
    vide, comme dans preview-look."""
    if poster:
        return f'<img src="{poster}" alt="" loading="lazy">'
    kind = str(media_type or "").strip().lower()
    emoji = "🎬" if kind in {"film", "movie", "movies"} else "📺"
    return f'<div class="msl-poster-fallback">{emoji}</div>'


def _type_chip(kind: str) -> str:
    """Type de contenu compact, intégré à la ligne de titre (uniforme)."""
    k = str(kind or "").strip().casefold()
    if k in {"film", "movie", "movies"}:
        return '<span class="mc-type" data-tooltip="Type de contenu">🎬 Film</span>'
    if k in {"épisode", "episode", "ep"}:
        return '<span class="mc-type" data-tooltip="Type de contenu">📺 Épisode</span>'
    if k in {"série", "serie", "show", "shows"}:
        return '<span class="mc-type" data-tooltip="Type de contenu">📺 Série</span>'
    if k:
        return f'<span class="mc-type" data-tooltip="Type de contenu">{escape(k)}</span>'
    return '<span class="mc-type" data-tooltip="Type de contenu">📺</span>'


def _public_note(item: Any) -> float | None:
    """Note publique (communauté) d'un média, sur 10, si disponible."""
    if not isinstance(item, dict):
        return None
    for key in ("score_average", "score"):
        try:
            value = float(item.get(key) or 0)
        except (TypeError, ValueError):
            continue
        if value > 0:
            if value > 10:
                value = value / 10.0
            return max(0.0, min(value, 10.0))
    return None


def _public_note_html(item: Any) -> str:
    note = _public_note(item)
    if note is None:
        return ""
    tip = "Note moyenne de la communauté (sur 10)."
    return f'<span class="mc-note" data-tooltip="{escape(tip, quote=True)}">⭐ {note:.1f}/10</span>'


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


def _sane_episode_runtime(runtime: object, total_episodes: int = 0) -> int:
    """Durée réaliste d'un épisode (10 à 100 min) ou 0 (inconnue).

    Un épisode de série dépasse quasiment JAMAIS 100 min. Les valeurs
    énormes (ex. 232, 246, 208 min) renvoyées par MDBList sont des durées
    cumulées/erronées : on les divise par le nombre d'épisodes. Les valeurs
    < 10 min sont aussi fausses → inconnue. Ce filet de sécurité agit au
    rendu, MÊME si l'enrichissement TMDB ne s'est pas appliqué à la série.
    """
    try:
        raw = int(round(float(runtime or 0)))
    except (TypeError, ValueError):
        return 0
    if raw <= 0:
        return 0
    if 10 <= raw <= 100:
        return raw
    if total_episodes and total_episodes >= 2:
        average = int(round(raw / total_episodes))
        if 10 <= average <= 100:
            return average
    return 0


def _media_seasons(item: dict) -> int:
    """Nombre de saisons d'une série (depuis number_of_seasons / seasons)."""
    if not isinstance(item, dict):
        return 0
    media = item
    for key in ("movie", "show"):
        nested = item.get(key)
        if isinstance(nested, dict):
            media = nested
    for key in ("number_of_seasons", "season_count", "seasons_count", "total_seasons"):
        try:
            value = int(media.get(key) or 0)
        except (TypeError, ValueError):
            value = 0
        if value > 0:
            return value
    seasons = media.get("seasons")
    if isinstance(seasons, list):
        return len(seasons)
    return 0


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


def _mdblist_cache_key(access_token: str) -> str:
    """Clé de cache stable par utilisateur (jamais le token en clair)."""
    import hashlib
    return hashlib.sha256((access_token or "").encode("utf-8")).hexdigest()[:16]


def _media_tmdb_id(item: dict) -> int | None:
    """Identifiant TMDB d'un média, depuis ids / tmdb_id / tmdbid / id (formats variés)."""
    ids = item.get("ids") if isinstance(item.get("ids"), dict) else {}
    tmdb = ids.get("tmdb") or item.get("tmdb_id") or item.get("tmdbid")
    if tmdb in (None, ""):
        raw_id = item.get("id")
        try:
            tmdb = int(raw_id) if raw_id not in (None, "", 0, "0") else None
        except (TypeError, ValueError):
            tmdb = None
    try:
        return int(tmdb) if tmdb not in (None, "", 0, "0") else None
    except (TypeError, ValueError):
        return None


def _unwrap_media(item: Any) -> dict:
    """Désimbrique movie/show/episode pour obtenir le dictionnaire média."""
    if not isinstance(item, dict):
        return {}
    for key in ("movie", "show", "episode"):
        nested = item.get(key)
        if isinstance(nested, dict):
            return nested
    return item


def _kind_of(item: Any, fallback: str = "movie") -> str:
    """Type (movie/tv) d'un média, depuis mediatype/type ou l'imbrication."""
    if not isinstance(item, dict):
        return fallback
    value = str(item.get("mediatype") or item.get("type") or "").lower()
    if value in {"movie", "movies"}:
        return "movie"
    if value in {"show", "shows", "tv", "series", "tvshow"}:
        return "tv"
    if isinstance(item.get("movie"), dict):
        return "movie"
    if isinstance(item.get("show"), dict):
        return "tv"
    return fallback


def _history_media(dataset: dict) -> list[tuple[dict, str]]:
    """Médias (media, kind) de l'historique et des notes — pour les favoris."""
    seen: set = set()
    out: list[tuple[dict, str]] = []
    sections = dataset.get("sections") if isinstance(dataset.get("sections"), dict) else {}

    def add(item: Any, fallback: str) -> None:
        media = _unwrap_media(item)
        if not media:
            return
        tmdb = _media_tmdb_id(media)
        key = tmdb if tmdb else id(media)
        if key in seen:
            return
        seen.add(key)
        out.append((media, _kind_of(item, fallback)))

    watched = sections.get("watched") or {}
    for row in watched.get("movies") or []:
        add(row, "movie")
    for row in watched.get("shows") or []:
        add(row, "tv")
    for row in watched.get("episodes") or []:
        episode = row.get("episode") if isinstance(row.get("episode"), dict) else {}
        add(episode.get("show") if isinstance(episode.get("show"), dict) else episode, "tv")
    ratings = sections.get("ratings") or {}
    for section in ("movies", "shows", "episodes"):
        fallback = "tv" if section in {"shows", "episodes"} else "movie"
        for row in ratings.get(section) or []:
            add(row, fallback)
    return out


def _all_media(dataset: dict) -> list[tuple[dict, str]]:
    """Tous les médias du dataset (historique, notes, watchlist, listes)."""
    seen: set = set()
    out: list[tuple[dict, str]] = []
    sections = dataset.get("sections") if isinstance(dataset.get("sections"), dict) else {}

    def add(item: Any, fallback: str) -> None:
        media = _unwrap_media(item)
        if not media:
            return
        tmdb = _media_tmdb_id(media)
        key = tmdb if tmdb else id(media)
        if key in seen:
            return
        seen.add(key)
        out.append((media, _kind_of(item, fallback)))

    for media, kind in _history_media(dataset):
        add(media, kind)
    watchlist = sections.get("watchlist") or {}
    for item in (watchlist.get("movies") or []):
        add(item, "movie")
    for item in (watchlist.get("shows") or []):
        add(item, "tv")
    for lst in sections.get("user_lists") or []:
        if not isinstance(lst, dict):
            continue
        for item in (lst.get("movies") or []):
            add(item, "movie")
        for item in (lst.get("shows") or []):
            add(item, "tv")
    return out


def _collect_people_stats(dataset: dict, tmdb_whitelist: set | None = None) -> list[dict]:
    """Acteurs triés par nombre d'apparitions (photo + id TMDB).

    `tmdb_whitelist` (facultatif) restreint le calcul aux médias présents
    dans une sélection filtrée (pour suivre les slicers des statistiques)."""
    counts: dict[str, int] = {}
    meta: dict[str, dict] = {}
    for media, _kind in _history_media(dataset):
        if tmdb_whitelist is not None:
            tmdb = _media_tmdb_id(media)
            if tmdb is None or str(tmdb) not in tmdb_whitelist:
                continue
        for actor in media.get("actors") or []:
            if not isinstance(actor, dict):
                continue
            name = str(actor.get("name") or "").strip()
            if not name:
                continue
            key = name.casefold()
            counts[key] = counts.get(key, 0) + 1
            meta.setdefault(key, {
                "name": name,
                "id": actor.get("id"),
                "profile_path": actor.get("profile_path") or "",
            })
    stats = [
        {"name": meta[key]["name"], "id": meta[key]["id"],
         "profile_path": meta[key]["profile_path"], "count": counts[key]}
        for key in counts
    ]
    stats.sort(key=lambda row: (-row["count"], row["name"].casefold()))
    return stats


def _collect_studio_stats(dataset: dict, tmdb_whitelist: set | None = None) -> list[dict]:
    """Studios triés par nombre d'apparitions dans l'historique."""
    counts: dict[str, int] = {}
    meta: dict[str, dict] = {}
    for media, _kind in _history_media(dataset):
        if tmdb_whitelist is not None:
            tmdb = _media_tmdb_id(media)
            if tmdb is None or str(tmdb) not in tmdb_whitelist:
                continue
        for studio in media.get("studios") or []:
            if not isinstance(studio, dict):
                continue
            name = str(studio.get("name") or "").strip()
            if not name:
                continue
            key = name.casefold()
            counts[key] = counts.get(key, 0) + 1
            meta.setdefault(key, {"name": name, "id": studio.get("id")})
    stats = [{"name": meta[key]["name"], "id": meta[key]["id"], "count": counts[key]} for key in counts]
    stats.sort(key=lambda row: (-row["count"], row["name"].casefold()))
    return stats


def _collect_director_stats(dataset: dict, tmdb_whitelist: set | None = None) -> list[dict]:
    """Réalisateurs/créateurs triés par nombre d'apparitions (photo + id TMDB).

    Suit les slicers des statistiques via `tmdb_whitelist` (comme les acteurs).
    """
    counts: dict[str, int] = {}
    meta: dict[str, dict] = {}
    for media, _kind in _history_media(dataset):
        if tmdb_whitelist is not None:
            tmdb = _media_tmdb_id(media)
            if tmdb is None or str(tmdb) not in tmdb_whitelist:
                continue
        for director in media.get("directors") or []:
            if not isinstance(director, dict):
                continue
            name = str(director.get("name") or "").strip()
            if not name:
                continue
            key = name.casefold()
            counts[key] = counts.get(key, 0) + 1
            meta.setdefault(key, {
                "name": name,
                "id": director.get("id"),
                "profile_path": director.get("profile_path") or "",
            })
    stats = [
        {"name": meta[key]["name"], "id": meta[key]["id"],
         "profile_path": meta[key]["profile_path"], "count": counts[key]}
        for key in counts
    ]
    stats.sort(key=lambda row: (-row["count"], row["name"].casefold()))
    return stats


def _tmdb_image_url(path: str, size: str = "w185") -> str:
    return f"https://image.tmdb.org/t/p/{size}{path}" if path else ""


def _tmdb_person_url(person_id: Any) -> str:
    return f"https://www.themoviedb.org/person/{person_id}" if person_id else ""


def _tmdb_company_url(company_id: Any) -> str:
    return f"https://www.themoviedb.org/company/{company_id}" if company_id else ""


def _render_people_cards(people: list[dict], limit: int = 8, fallback_emoji: str = "🎭") -> str:
    """Cartes acteurs/réalisateurs (photo + lien TMDB), compactes et alignées sur le thème."""
    if not people:
        return ""
    cards = []
    for person in people[:limit]:
        photo = _tmdb_image_url(str(person.get("profile_path") or ""))
        url = _tmdb_person_url(person.get("id"))
        name = escape(str(person.get("name") or ""))
        count = int(person.get("count") or 0)
        if photo:
            img = (f'<img src="{photo}" alt="" loading="lazy" '
                   f'style="width:44px;height:44px;border-radius:10px;object-fit:cover;'
                   f'border:1px solid rgba(255,225,0,.45);">')
        else:
            img = (f'<div style="width:44px;height:44px;border-radius:10px;display:flex;'
                   'align-items:center;justify-content:center;font-size:20px;'
                   'background:linear-gradient(180deg,#0C2E28,#041710);'
                   f'border:1px solid rgba(0,163,146,.35);">{fallback_emoji}</div>')
        link = (f'<a class="link-pill" href="{url}" target="_blank" rel="noopener noreferrer" '
                f'title="Fiche TMDB">TMDB</a>') if url else ""
        cards.append(
            f'<div style="display:flex;align-items:center;gap:.6rem;background:rgba(8,55,50,.62);'
            f'border:1px solid rgba(0,163,146,.35);border-radius:12px;padding:.5rem .6rem;">'
            f'{img}<div style="min-width:0;flex:1;"><div style="font-weight:700;font-size:.85rem;'
            f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{name}</div>'
            f'<div style="color:#9DC5BF;font-size:.74rem;">{count} titre(s)</div></div>{link}</div>'
        )
    return ('<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));'
            'gap:.5rem;margin:.4rem 0;">' + "".join(cards) + '</div>')


def _render_studio_chips(studios: list[dict], limit: int = 10) -> str:
    """Chips studios (lien TMDB), compactes."""
    if not studios:
        return ""
    chips = []
    for studio in studios[:limit]:
        name = escape(str(studio.get("name") or ""))
        count = int(studio.get("count") or 0)
        url = _tmdb_company_url(studio.get("id"))
        label = f"{name} · {count}"
        if url:
            chips.append(f'<a class="link-pill" href="{url}" target="_blank" rel="noopener noreferrer" '
                         f'title="Fiche TMDB">🏢 {label}</a>')
        else:
            chips.append(f'<span class="mc-chip">🏢 {label}</span>')
    return ('<div style="margin:.4rem 0;display:flex;flex-wrap:wrap;gap:.35rem;">'
            + "".join(chips) + '</div>')




def _tmdb_api_key() -> str:
    """Clé TMDB (optionnelle) depuis les Secrets Streamlit."""
    try:
        return str(st.secrets.get("TMDB_API_KEY") or "").strip()
    except Exception:
        return ""


@st.cache_data(ttl=2592000, show_spinner=False)  # 30 jours : mémoire TMDB par contenu
def _fetch_tmdb_item(kind: str, tmdb: int, key: str) -> dict | None:
    """Un appel TMDB (genres + studios + casting) — mis en cache PAR CONTENU.

    Chaque fiche (film/série) est mémorisée 30 jours : un rechargement ne
    refait JAMAIS les appels TMDB déjà effectués. Seuls les contenus NOUVEAUX
    (ajoutés à une liste, vus depuis le dernier enrichissement) déclenchent de
    nouveaux appels → enrichissement réellement incrémental, sans repartir de
    zéro.

    · 200 + JSON valide → réponse mise en cache (succès).
    · 404 (inexistant)  → dict vide mis en cache (rien à récupérer : on ne
      réessaie pas, le bon identifiant n'existe pas côté TMDB).
    · 5xx / réseau / JSON cassé → on lève une exception (NON mise en cache) :
      l'item sera réessayé au prochain enrichissement, une fois le réseau
      rétabli. Ainsi une micro-coupure ne « fige » jamais un contenu.
    """
    try:
        response = requests.get(
            f"https://api.themoviedb.org/3/{kind}/{tmdb}",
            params={"api_key": key, "language": "en-US", "append_to_response": "credits"},
            timeout=8,
        )
    except requests.RequestException:
        raise  # réseau indisponible : non mis en cache (réessayé plus tard)
    if response.status_code == 404:
        return {}  # contenu inexistant : mis en cache (rien à récupérer)
    if response.status_code != 200:
        raise RuntimeError(f"TMDB {kind}/{tmdb} a répondu HTTP {response.status_code}")
    try:
        return response.json()
    except ValueError:
        raise  # JSON illisible : non mis en cache


def _apply_tmdb_payload(media: dict, payload: dict) -> None:
    """Remplit genres, studios et acteurs d'un média depuis une réponse TMDB."""
    # Genres (uniquement si absents).
    if not media.get("genres"):
        genres = payload.get("genres") or []
        names = sorted(
            {str(g.get("name") or "").strip().title() for g in genres if isinstance(g, dict) and g.get("name")},
            key=str.casefold,
        )
        if names:
            media["genres"] = names
    # Studios (production_companies + networks).
    studios: list[dict] = []
    seen_studios: set[str] = set()
    for company in (payload.get("production_companies") or []) + (payload.get("networks") or []):
        if not isinstance(company, dict):
            continue
        name = str(company.get("name") or "").strip()
        if not name or name in seen_studios:
            continue
        seen_studios.add(name)
        studios.append({"name": name, "id": company.get("id")})
    if studios:
        media["studios"] = studios
    # Acteurs principaux (top 10).
    credits = payload.get("credits") if isinstance(payload.get("credits"), dict) else {}
    actors: list[dict] = []
    for person in credits.get("cast") or []:
        if not isinstance(person, dict):
            continue
        raw_order = person.get("order")
        try:
            order = int(raw_order) if raw_order is not None else 99
        except (TypeError, ValueError):
            order = 99
        if order >= 10:
            continue
        name = str(person.get("name") or "").strip()
        if not name:
            continue
        actors.append({"name": name, "id": person.get("id"),
                       "profile_path": person.get("profile_path") or "", "order": order})
    if actors:
        media["actors"] = actors
    # Compteurs de série (saisons / épisodes) — alimentent la carte
    # « Que regarder ? » (infos succinctes série).
    if not media.get("number_of_seasons") and payload.get("number_of_seasons"):
        try:
            media["number_of_seasons"] = int(payload["number_of_seasons"])
        except (TypeError, ValueError):
            pass
    if not media.get("number_of_episodes") and payload.get("number_of_episodes"):
        try:
            media["number_of_episodes"] = int(payload["number_of_episodes"])
        except (TypeError, ValueError):
            pass
    # Runtime AUTORITAIRE depuis TMDB. Le champ `runtime` de MDBList est peu
    # fiable pour les séries (durée cumulée, durée d'un film, 9 min…). TMDB
    # expose `episode_run_time` (durée moyenne d'un épisode) pour les séries
    # et `runtime` pour les films : on s'y fie (cf. doc TMDB).
    episode_rt = payload.get("episode_run_time")
    if isinstance(episode_rt, list) and episode_rt:
        value = next((int(x) for x in episode_rt if isinstance(x, (int, float)) and 0 < x <= 300), 0)
        if value:
            media["runtime"] = value
    else:
        try:
            value = int(payload.get("runtime") or 0)
        except (TypeError, ValueError):
            value = 0
        if 0 < value <= 600:
            media["runtime"] = value
    # Réalisateurs (films : credits.crew job==Director) / créateurs (séries :
    # created_by). Top 5, avec photo TMDB pour les statistiques.
    directors: list[dict] = []
    seen_directors: set[str] = set()
    for person in (credits.get("crew") or []):
        if isinstance(person, dict) and str(person.get("job") or "") == "Director":
            name = str(person.get("name") or "").strip()
            if name and name.casefold() not in seen_directors:
                seen_directors.add(name.casefold())
                directors.append({"name": name, "id": person.get("id"),
                                  "profile_path": person.get("profile_path") or ""})
    for person in (payload.get("created_by") or []):
        if isinstance(person, dict):
            name = str(person.get("name") or "").strip()
            if name and name.casefold() not in seen_directors:
                seen_directors.add(name.casefold())
                directors.append({"name": name, "id": person.get("id"),
                                  "profile_path": person.get("profile_path") or ""})
    if directors:
        media["directors"] = directors[:5]
    # Saga/franchise (films) : belongs_to_collection. Permet de détecter les
    # suites d'une saga entamée (« tu as vu le 1 → on boost le 2 »).
    btc = payload.get("belongs_to_collection")
    if isinstance(btc, dict) and btc.get("id") and not media.get("collection"):
        media["collection"] = {"id": btc["id"], "name": str(btc.get("name") or "").strip()}


def _enrich_tmdb_metadata(data: dict) -> None:
    """Complète genres, studios et acteurs via l'API TMDB (0 appel MDBList).

    Couverture COMPLÈTE de l'historique :
      • tout média manquant de genres, studios OU acteurs est enrichi ;
      • les gros consommateurs (bibliothèques étendues, milliers d'épisodes)
        sont couverts : budget porté à 6000 contenus.
    Résultat : tous tes acteurs et studios de tout ton historique sont
    détectés (page Statistiques + Que regarder ?).

    MÉMOIRE INCRÉMENTALE : chaque fiche TMDB est mise en cache 30 jours
    (`_fetch_tmdb_item`). Un rechargement ne refait donc QUE les contenus
    NOUVEAUX (ajoutés à une liste, vus depuis le dernier passage) → fini les
    40 s à chaque fois : seuls les changements récents sont interrogés.
    """
    key = _tmdb_api_key()
    if not key:
        return
    all_media = _all_media(data)
    # Couverture complète : enrichir tout média incomplet (genres, studios OU
    # acteurs). `_fetch_tmdb_item` étant mis en cache par contenu, les médias
    # déjà enrichis ne déclenchent AUCUN appel réseau : la boucle est quasi
    # gratuite sur les rechargements, et n'interroge que les nouveautés.
    need_enrich = [
        (m, k) for m, k in all_media
        if (not m.get("genres")) or (not m.get("studios")) or (not m.get("actors"))
    ]

    budget = 6000  # sécurité pour les très grosses bibliothèques
    targets: list[tuple[dict, str]] = []
    seen: set = set()
    for m, k in need_enrich:
        uid = _media_tmdb_id(m) or id(m)
        if uid in seen:
            continue
        seen.add(uid)
        targets.append((m, k))
        if len(targets) >= budget:
            break

    def work(item: tuple[dict, str]) -> None:
        m, k = item
        tmdb = _media_tmdb_id(m)
        if not tmdb:
            return
        try:
            payload = _fetch_tmdb_item(k, tmdb, key)
        except Exception:
            # Échec transitoire (réseau, 5xx) : NON mis en cache → l'item sera
            # réessayé au prochain enrichissement, sans rien « figer ».
            return
        if payload:
            _apply_tmdb_payload(m, payload)

    with ThreadPoolExecutor(max_workers=20) as executor:
        list(executor.map(work, targets))


@st.cache_data(ttl=604800, show_spinner=False)  # 7 jours : cache serveur partagé (PC + GSM)
def _load_mdblist_cached(cache_key: str, access_token: str) -> dict[str, Any]:
    """Charge le dataset MDBList avec un cache persistant (1 h).

    La clé de cache (`cache_key`) est un hash SHA-256 dérivé du token : chaque
    utilisateur a sa propre entrée, le token n'est jamais utilisé comme clé ni
    stocké en clair dans le cache. Un simple rechargement de page (F5) ne
    rejoue donc pas les appels API. Le bouton « Actualiser » vide ce cache.
    """
    provider = MDBListProvider(access_token)
    raw_data = provider.load_dataset()
    _enrich_tmdb_metadata(raw_data)
    data = normalize_provider_dataset(raw_data)
    data["_cached"] = True
    return data


def load_mdblist_dataset() -> None:
    valid, message = mdb_oauth.ensure_valid_session(cookies)
    if not valid:
        st.markdown(
            f'<div class="accent-callout"><strong>SESSION INDISPONIBLE</strong> · '
            f'{escape(message or "Reconnecte MDBList.")}</div>',
            unsafe_allow_html=True,
        )
        return
    token = mdb_oauth.access_token()
    try:
        key = _mdblist_cache_key(token)
        data = _load_mdblist_cached(key, token)
    except Exception:
        st.markdown(
            '<div class="accent-callout"><strong>LECTURE IMPOSSIBLE</strong> · '
            'MDBList n’a pas pu charger les données pour le moment.</div>',
            unsafe_allow_html=True,
        )
        return
    # Session révoquée/expirée : SEULEMENT si la majorité des sections
    # échouent avec une erreur d'authentification (un 401 ponctuel sur une
    # section n'est pas une session expirée).
    errors = data.get("errors") or []
    auth_errors = [
        error for error in errors
        if isinstance(error, dict)
        and (
            "expirée" in str(error.get("error") or "").lower()
            or "révoquée" in str(error.get("error") or "").lower()
            or "401" in str(error.get("error") or "")
        )
    ]
    total_sections = 8  # watched, watchlist, genres, user_lists, ratings, playback, upnext, dropped
    session_expired = len(auth_errors) >= max(2, total_sections // 2)
    if session_expired:
        # Expiration (pas un logout volontaire) : on efface la session et le
        # cookie SANS poser le marqueur ?msl_logged_out=1.
        mdb_oauth.expire_local_session(cookies)
        _load_mdblist_cached.clear()
        st.session_state.pop("_normalized_dataset", None)
        st.markdown(
            '<div class="accent-callout"><strong>SESSION EXPIRÉE</strong> · '
            'La connexion MDBList n’est plus valide. Reconnecte-toi depuis le Tableau de bord.</div>',
            unsafe_allow_html=True,
        )
        return
    st.session_state["_normalized_dataset"] = data
    # Marqueur cookie : permet de recharger depuis le cache après un F5.
    try:
        cookies.set("msl_mdblist_data_loaded", "1", expires=datetime.now() + timedelta(days=30))
    except Exception:
        pass
    account = mdb_oauth.account_summary()
    if data.get("rate_limit_remaining") is not None and account:
        account["rate_limit_remaining"] = data["rate_limit_remaining"]
        st.session_state[mdb_oauth.ACCOUNT_KEY] = account
        mdb_oauth.persist_cookie(cookies)


def render_data_loader() -> None:
    if not mdb_oauth.is_connected():
        return
    data = _dataset()
    # Si les données ZIP Trakt sont actuellement affichées, prévenir du remplacement.
    if data and str(data.get("source") or "") == "trakt_zip":
        st.markdown(
            '<div class="accent-callout"><strong>⚠️ REMPLACEMENT</strong> · '
            'Charger les données MDBList remplacera les données Trakt (import ZIP) '
            'actuellement affichées. Utilise « 🚪 Quitter les données ZIP Trakt » '
            'pour les retirer d’abord.</div>',
            unsafe_allow_html=True,
        )
    is_mdblist_data = bool(data and str(data.get("source") or "mdblist") == "mdblist")
    cached = bool(is_mdblist_data and data.get("_cached"))
    if is_mdblist_data:
        # Données déjà chargées : plus de bouton ici (évite un appel API
        # involontaire). L'actualisation est disponible en bas du tableau de bord.
        errors = data.get("errors") or []
        request_count = data.get("request_count", 0)
        loaded_at = str(data.get("loaded_at") or "").replace("T", " ").replace("Z", " UTC")
        source_txt = " (cache)" if cached else ""
        age_txt = ""
        try:
            loaded_dt = datetime.fromisoformat(str(data.get("loaded_at") or "").replace("Z", "+00:00"))
            age_days = max((datetime.now(loaded_dt.tzinfo) - loaded_dt).days, 0)
            age_txt = " · aujourd'hui" if age_days == 0 else f" · il y a {age_days} j"
        except Exception:
            pass
        # Date affichée sans l'heure UTC (problème de fuseau : l'app peut être
        # utilisée depuis n'importe quel pays). L'indicateur relatif « il y a X j »
        # est, lui, toujours juste (calculé en temps absolu).
        st.caption(f"Données MDBList{source_txt} : {_format_date(data.get('loaded_at'))}{age_txt} · {request_count} requête(s) API")
        if cached:
            st.caption(
                "♻️ Servies depuis le cache (valide 7 jours) : un F5 ou un changement de page "
                "ne consomme AUCUN appel MDBList — l'app sait que tes données sont encore fraîches. "
                "Utilise « Actualiser » en bas de page pour forcer la recharge."
            )
        if errors:
            st.markdown(
                f'<div class="accent-callout"><strong>CHARGEMENT PARTIEL</strong> · '
                f'{len(errors)} section(s) indisponible(s). Les autres restent utilisables.</div>',
                unsafe_allow_html=True,
            )
        return
    # Pas encore de données : bouton de chargement initial.
    st.caption("Un chargement complet (historique, Watchlist, listes, notes, progression).")
    if st.button("📥 Charger mes données MDBList", type="primary", key="load_mdblist_dataset", use_container_width=True):
        with st.spinner("Chargement MDBList en lecture seule…"):
            _load_mdblist_cached.clear()
            load_mdblist_dataset()
        st.rerun()


def _distinct_series_count(watched: dict) -> int:
    """Nombre de séries distinctes vues (depuis les épisodes ET les shows)."""
    seen: set = set()
    for row in (watched.get("episodes") or []):
        show = (row.get("episode") or {}).get("show") if isinstance(row.get("episode"), dict) else row.get("show")
        if isinstance(show, dict):
            ids = show.get("ids") if isinstance(show.get("ids"), dict) else {}
            key = ids.get("tmdb") or show.get("title")
            if key:
                seen.add(key)
    for row in (watched.get("shows") or []):
        show = row.get("show") if isinstance(row.get("show"), dict) else row
        if isinstance(show, dict):
            ids = show.get("ids") if isinstance(show.get("ids"), dict) else {}
            key = ids.get("tmdb") or show.get("title")
            if key:
                seen.add(key)
    return len(seen)


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

    watchlist_total = len(watchlist.get("movies") or []) + len(watchlist.get("shows") or [])
    # Contenus au total dans les listes personnelles (somme de chaque liste).
    list_contents = sum(
        len(item.get("movies") or []) + len(item.get("shows") or [])
        for item in lists if isinstance(item, dict)
    )

    # Bandeau de métriques moderne (skin V53) : cartes k/v/d avec icône,
    # fondu en cascade et surbrillance au survol (0 appel API).
    cards: list[dict[str, Any]] = [
        {"emoji": "🎬", "k": "Films vus", "v": len(watched.get("movies") or []), "d": "au compteur"},
        {"emoji": "📺", "k": "Séries vues", "v": _distinct_series_count(watched), "d": "séries distinctes"},
        {"emoji": "🎞️", "k": "Épisodes vus", "v": len(watched.get("episodes") or []), "d": "au compteur"},
        {"emoji": "⭐", "k": "Watchlist", "v": watchlist_total, "d": "contenus dans ma watchlist"},
        {"emoji": "🗂️", "k": "Listes personnelles", "v": len(lists), "d": "créées sur MDBList"},
        {"emoji": "📦", "k": "Contenus en listes", "v": list_contents, "d": "au total des listes"},
        {"emoji": "💬", "k": "Notes", "v": sum(len(ratings.get(key) or []) for key in ("movies", "shows", "seasons", "episodes")),
         "d": "films, séries, épisodes"},
        {"emoji": "⏸️", "k": "Reprises", "v": len(playback), "d": "en cours de reprise"},
        {"emoji": "🚫", "k": "Séries abandonnées", "v": len(dropped.get("shows") or []), "d": "statut abandonnée"},
        {"emoji": "📺", "k": "Up Next", "v": len(sections.get("upnext") or []), "d": "prochains épisodes"},
    ]

    # Temps de visionnage (à vie) — calcul local depuis l'historique.
    # « Temps séries » et « Temps films » sont déjà détaillés dans le ruban
    # « Ton rythme de visionnage » (compteurs à vie) : on ne les répète pas.
    try:
        dash = dashboard_mod.compute_dashboard(_dataset(), timezone_name="Europe/Paris")
        if not dash.get("empty"):
            cards += [
                {"emoji": "⏱️", "k": "Temps total", "v": dashboard_mod._minutes_to_duree(dash["total_minutes"]), "d": "à vie"},
                {"emoji": "🏃", "k": "Épisodes/semaine", "v": f"{dash['eps_sem']:.1f}".replace(".", ",") if dash["eps_sem"] else "—",
                 "d": "rythme moyen"},
            ]
    except Exception:
        pass

    st.markdown(_metric_cards(cards), unsafe_allow_html=True)

    # Détail par liste (nombre de contenus) — complète le total ci-dessus.
    list_detail = [
        f"{item.get('name') or 'Liste'} ({len(item.get('movies') or []) + len(item.get('shows') or [])})"
        for item in lists if isinstance(item, dict)
    ]
    if list_detail:
        st.caption("Détail par liste : " + " · ".join(escape(x) for x in list_detail[:12]))

    # ── Couverture TMDB : certitude visible que les acteurs/studios sont
    # bien présents pour TOUT l'historique + les listes. X/Y = couverture
    # complète si X == Y (sinon, TMDB n'avait pas la fiche, ou pas d'id TMDb).
    try:
        all_media = _all_media(_dataset())
        total_titles = len(all_media)
        with_actors = sum(1 for m, _ in all_media if m.get("actors"))
        with_studios = sum(1 for m, _ in all_media if m.get("studios"))
        if total_titles:
            full = with_actors == total_titles and with_studios == total_titles
            st.caption(
                f"🎭 Acteurs TMDB : {with_actors}/{total_titles} titre(s) · "
                f"🏢 Studios : {with_studios}/{total_titles} titre(s)"
                + (" ✅ couverture complète de ton historique et de tes listes" if full else
                   " — les titres manquants n'ont pas de fiche TMDB ou d'identifiant TMDb")
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
        "qr_genres": [],
        "qr_genre_mode": "Au moins un (OU)",
        "qr_genres_exclude": [],
        "qr_countries_exclude": [],
        "qr_countries_include": [],
        "qr_duration_min": "Aucune",
        "qr_year_range": (1950, 2025),
        "qr_actors": [],
        "qr_directors": [],
        "qr_studios": [],
        "qr_cast_mode": "Au moins un (OU)",
    }
    for key, value in defaults.items():
        st.session_state[key] = value
    st.session_state.pop("_roulette_result", None)


def _justwatch_url(title: str) -> str:
    return "https://www.justwatch.com/fr/recherche?q=" + quote(str(title or ""))


def _content_links_html(ids: dict, title: str, is_show: bool = False, prefix: str = "", suffix: str = "") -> str:
    """Liens discrets, uniformisés en petits badges avec info-bulle, vers :
    JustWatch (où regarder), TMDB (fiche) et MDBList (fiche)."""
    if not isinstance(ids, dict):
        ids = {}
    title_text = quote(str(title or ""))
    justwatch = f"https://www.justwatch.com/fr/recherche?q={title_text}"
    links = [
        f'<a class="link-pill" href="{justwatch}" target="_blank" rel="noopener noreferrer" '
        f'title="Où regarder sur JustWatch">🔎 Où regarder</a>'
    ]
    tmdb = ids.get("tmdb")
    if tmdb:
        base = "tv" if is_show else "movie"
        links.append(
            f'<a class="link-pill" href="https://www.themoviedb.org/{base}/{int(tmdb)}" '
            f'target="_blank" rel="noopener noreferrer" title="Lien vers la fiche TMDB">TMDB</a>'
        )
    imdb = ids.get("imdb")
    if imdb:
        base = "show" if is_show else "movie"
        links.append(
            f'<a class="link-pill" href="https://mdblist.com/{base}/{str(imdb)}" '
            f'target="_blank" rel="noopener noreferrer" title="Lien vers la fiche MDBList">MDBL</a>'
        )
    spacer = f'<span class="links-spacer">{suffix}</span>' if suffix else ""
    return (
        f'<div style="margin-top:.35rem; display:flex; flex-wrap:wrap; align-items:center; gap:.2rem;">'
        f'{prefix}{" ".join(links)}{spacer}</div>'
    )


def _signal_pill(signal: dict) -> str:
    label = str(signal.get("label") or "Information")
    tooltip = str(signal.get("tooltip") or label)
    css_class = "warning-pill" if signal.get("warning") else "reason-pill"
    return (
        f'<span class="{css_class} info-pill" tabindex="0" '
        f'data-tooltip="{escape(tooltip, quote=True)}" title="{escape(tooltip, quote=True)}">'
        f'{escape(label)}</span>'
    )


def _meta_chip(emoji: str, values: list, label: str, tip_kind: str) -> str:
    """Pastille LABEL compact (uniforme PC/GSM) : seul le libellé est affiché,
    la liste complète est dans l'info-bulle. Maximum de place économisé, fini
    les renvois à la ligne."""
    if not values:
        return ""
    full = " · ".join(str(v) for v in values)
    tip = f"{tip_kind} : {full}"
    return f'<span class="mc-chip" data-tooltip="{escape(tip, quote=True)}">{escape(emoji + " " + label)}</span>'


def _raw_chip(label: str, tooltip: str = "") -> str:
    """Pastille compacte à partir d'un libellé déjà construit."""
    tip = f' data-tooltip="{escape(tooltip, quote=True)}"' if tooltip else ""
    return f'<span class="mc-chip"{tip}>{escape(label)}</span>'


def _render_recommendation_card(row: dict, highlighted: bool = False) -> None:
    item = row.get("item") or {}
    raw_title = _media_title(item)
    title = escape(raw_title)
    year = escape(_media_year(item))
    poster = escape(_poster_url(item), quote=True)
    image_html = _poster_html(poster, row.get("type") or "")
    metadata = []
    if row.get("genres"):
        metadata.append(_meta_chip("🎭", row["genres"], "Genres", "Genres"))
    if row.get("studios"):
        metadata.append(_meta_chip("🏢", row["studios"], "Studio", "Studios"))
    if row.get("people"):
        metadata.append(_meta_chip("👥", row["people"], "Acteurs", "Acteurs"))
    if row.get("directors"):
        metadata.append(_meta_chip("🎬", row["directors"], "Réal.", "Réalisateur"))
    if int(row.get("saga_seen") or 0):
        coll_name = (row.get("collection") or {}).get("name") or "saga"
        metadata.append(_raw_chip(
            "🔗 Saga",
            f"Suite d'une saga entamée ({coll_name}) — tu as déjà vu {row['saga_seen']} film(s) de cette saga",
        ))
    if row.get("_outside"):
        metadata.append('<span class="mc-outside" data-tooltip="Découverte TMDB — pas dans tes listes">🌐 Hors de tes listes</span>')
    else:
        source_name = str(row.get("source") or "MDBList")
        metadata.append(_raw_chip(f"📂 {source_name}", "Provenance : la liste ou la source où se trouve ce contenu"))

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
    # Liens uniformisés (mêmes badges que En cours / Fantôme / Calendrier).
    item_ids = item.get("ids") if isinstance(item.get("ids"), dict) else {}
    # Pastille principale (à gauche du groupe droit) : durée du film, ou pastille
    # série (saisons/épisodes) qui remplace la durée pour les séries.
    lead_pill = ""
    if row.get("type") == "Série":
        total_ep = int(row.get("total_episodes") or 0)
        seasons = _media_seasons(item)
        ep_runtime = _sane_episode_runtime(row.get("runtime"), total_ep)
        total_time = ep_runtime * total_ep if (ep_runtime and total_ep) else 0
        parts = []
        if seasons:
            parts.append(f"{seasons} saison{'s' if seasons > 1 else ''}")
        if total_ep:
            parts.append(f"{total_ep} épisode(s)")
        if ep_runtime:
            parts.append(f"environ {ep_runtime} min/ép.")
        if total_time:
            parts.append(f"tout voir : {_format_minutes(total_time)}")
        slabel = f"📺 {seasons or '?'}S · {total_ep or '?'}ép" if (seasons or total_ep) else "📺 Série"
        stip = " · ".join(parts) if parts else "Durée inconnue"
        lead_pill = f'<span class="mc-year" data-tooltip="{escape(stip, quote=True)}">{escape(slabel)}</span>'
    elif row.get("runtime"):
        try:
            lead_pill = f'<span class="mc-year" data-tooltip="Durée">{_format_minutes(int(row["runtime"]))}</span>'
        except (TypeError, ValueError):
            lead_pill = ""
    note_pill = (
        f'<span class="mc-note" data-tooltip="Note communauté (sur 10)">⭐ {row["note"]:.1f}</span>'
        if row.get("note") is not None else ""
    )
    year_pill = f'<span class="mc-year" data-tooltip="Année de sortie">{year}</span>' if year else ""
    head = (
        f'<div class="mc-head">'
        f'{_type_chip(str(row.get("type") or ""))}'
        f'<strong>{title}</strong>'
        f'<span style="display:inline-flex;gap:6px;flex-shrink:0;flex-wrap:wrap;justify-content:flex-end;">'
        f'{lead_pill}{note_pill}{year_pill}</span>'
        f'</div>'
    )
    score_val = int(round(row.get("score", 0)))
    friction_val = int(row.get("friction", 0))
    friction_tip = "Facilité de lancement (durée courte, peu d'épisodes). Plus le score est élevé, plus c'est facile à commencer."
    score_tip = "Score personnel : adéquation estimée avec tes goûts, calculée sur ton appareil. Plus il est haut, mieux le contenu te correspond."
    score_col = (
        f'<div class="media-list-pct" data-tooltip="{escape(score_tip, quote=True)}">{score_val}'
        f'<span class="sub">score /100</span></div>'
    )
    score_inline = f'<span class="score-badge gsm-only" data-tooltip="{escape(score_tip, quote=True)}">{score_val}/100</span>'
    links_html = _content_links_html(item_ids, raw_title, is_show=(row.get("type") == "Série"))
    st.markdown(
        f'<div class="media-list-card poster-card">{image_html}<div class="media-list-content" style="width:100%;">'
        f'{roulette_badge}{head}'
        f'<small>{" · ".join(metadata)}</small>{links_html}'
        f'<div style="display:flex;flex-wrap:wrap;align-items:center;gap:.4rem;">'
        f'<span class="score-badge" data-tooltip="{escape(friction_tip, quote=True)}">Friction {friction_val}/100</span>{score_inline}'
        f'</div>'
        f'<div class="progress-bar-container"><div class="progress-bar-fill" '
        f'style="width:{max(0,min(float(row.get("score",0)),100))}%;"></div></div>'
        + (f'<details class="pills-details"><summary>ℹ️ Pourquoi ce score ?</summary>{pills}</details>' if pills else "")
        + f'</div>{score_col}</div>',
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

        # ── Bloc « Tes studios / acteurs préférés » (données TMDB) ──
        people_stats = _collect_people_stats(_dataset())
        studio_stats = _collect_studio_stats(_dataset())
        director_stats = _collect_director_stats(_dataset())
        if director_stats:
            st.markdown("**🎬 Tes réalisateurs récurrents**")
            st.markdown(_render_people_cards(director_stats, fallback_emoji="🎬"), unsafe_allow_html=True)
        if people_stats:
            st.markdown("**🎭 Tes acteurs récurrents**")
            st.markdown(_render_people_cards(people_stats), unsafe_allow_html=True)
        if studio_stats:
            st.markdown("**🏢 Tes studios récurrents**")
            st.markdown(_render_studio_chips(studio_stats), unsafe_allow_html=True)
        if not people_stats and not studio_stats:
            st.caption(
                "🏢🎭 Studios et acteurs seront détectés automatiquement dès que la clé "
                "TMDB_API_KEY sera renseignée dans les Secrets Streamlit."
            )


COUNTRY_FR = {
    "us": "États-Unis", "fr": "France", "gb": "Royaume-Uni", "kr": "Corée du Sud",
    "jp": "Japon", "de": "Allemagne", "es": "Espagne", "it": "Italie",
    "ca": "Canada", "cn": "Chine", "in": "Inde", "au": "Australie",
    "be": "Belgique", "mx": "Mexique", "br": "Brésil", "dk": "Danemark",
    "se": "Suède", "no": "Norvège", "nl": "Pays-Bas", "ie": "Irlande",
    "ar": "Argentine", "ru": "Russie", "tr": "Turquie", "pl": "Pologne",
    "hk": "Hong Kong", "tw": "Taïwan", "pt": "Portugal", "ch": "Suisse",
    "at": "Autriche", "fi": "Finlande", "is": "Islande", "nz": "Nouvelle-Zélande",
    "ir": "Iran", "il": "Israël", "za": "Afrique du Sud", "th": "Thaïlande",
    "co": "Colombie", "cl": "Chili", "cz": "Tchéquie", "hu": "Hongrie",
    "gr": "Grèce", "ua": "Ukraine", "ma": "Maroc", "dz": "Algérie",
    "tn": "Tunisie", "lb": "Liban",
}

def _flag_emoji(code):
    c = str(code or "").upper()
    if len(c) != 2:
        return ""
    return chr(0x1F1E6 + ord(c[0]) - 65) + chr(0x1F1E6 + ord(c[1]) - 65)

def _country_display(code):
    c = str(code or "").strip().lower()
    name = COUNTRY_FR.get(c, c.upper())
    flag = _flag_emoji(c)
    return f"{flag} {name}" if flag else name

GENRE_FR_TO_TMDB = {
    "Action": 28, "Aventure": 12, "Animation": 16, "Comédie": 35, "Crime": 80,
    "Documentaire": 99, "Drame": 18, "Familial": 10751, "Fantastique": 14,
    "Histoire": 36, "Horreur": 27, "Musique": 10402, "Mystère": 9648,
    "Romance": 10749, "Science-Fiction": 878, "Thriller": 53, "Guerre": 10752,
    "Western": 37,
}
GENRE_TMDB_TO_FR = {v: k for k, v in GENRE_FR_TO_TMDB.items()}

GENRE_FR_TO_TMDB_TV = {
    "Action": 10759, "Aventure": 10759,
    "Animation": 16, "Comédie": 35, "Crime": 80,
    "Documentaire": 99, "Drame": 18, "Familial": 10751,
    "Fantastique": 10765, "Science-Fiction": 10765,
    "Mystère": 9648, "Guerre": 10768, "Western": 37,
}


def _build_item_from_tmdb(tmdb_id: int, kind: str, payload: dict) -> dict:
    """Construit un item scoreable depuis une fiche TMDB complète."""
    media: dict[str, Any] = {"ids": {"tmdb": tmdb_id}, "mediatype": kind}
    media["title"] = payload.get("title") or payload.get("name") or "?"
    if payload.get("imdb_id"):
        media["ids"]["imdb"] = payload["imdb_id"]
    _apply_tmdb_payload(media, payload)
    if media.get("genres"):
        media["genres"] = [_tr_genre(g) for g in media["genres"]]
    va = payload.get("vote_average")
    vc = payload.get("vote_count")
    if va:
        media["score_average"] = float(va) * 10
    if vc:
        media["ratings"] = [{"source": "tmdb", "value": float(va) if va else 0, "votes": vc}]
    date = payload.get("release_date") or payload.get("first_air_date")
    if date and len(date) >= 4:
        try:
            media["year"] = int(date[:4])
        except ValueError:
            pass
    if payload.get("poster_path"):
        media["poster"] = payload["poster_path"]
    if payload.get("status"):
        media["status"] = str(payload["status"]).lower()
    pcs = payload.get("production_countries") or []
    if pcs and isinstance(pcs[0], dict):
        media["country"] = pcs[0].get("iso_3166_1", "")
    return media


def _perfect_recommendation(
    profile: dict, dataset: dict, selected_type: str, selected_genres: list,
    note_min: float, api_key: str, excluded_genres: list | None = None,
    included_countries: set | None = None, excluded_countries: set | None = None,
    selected_actors: list | None = None, selected_directors: list | None = None,
    selected_studios: list | None = None, year_range: tuple | None = None,
) -> list[dict]:
    """Reco HYBRIDE :
    - FILMS : TMDB Discover avec with_cast/with_crew (supportés).
    - SÉRIES + acteur : /person/{id}/tv_credits (Discover ne supporte pas
      with_cast pour TV).
    - Filtrage client post-scoring pour studios, pays, époque (safety net)."""
    # IDs des acteurs/réalisateurs depuis le filtre
    people_stats = _collect_people_stats(dataset)
    director_stats = _collect_director_stats(dataset)
    filter_actor_ids = []
    filter_director_ids = []
    if selected_actors:
        sel_cf = {a.casefold() for a in selected_actors}
        filter_actor_ids = [str(s["id"]) for s in people_stats if s.get("id") and s["name"].casefold() in sel_cf][:5]
    if selected_directors:
        sel_cf = {d.casefold() for d in selected_directors}
        filter_director_ids = [str(s["id"]) for s in director_stats if s.get("id") and s["name"].casefold() in sel_cf][:3]

    # Genres : uniquement si l'utilisateur en a choisi, OU si pas de filtre acteur
    if selected_genres:
        genre_names = selected_genres
    elif filter_actor_ids or filter_director_ids:
        genre_names = []  # Acteur sans genre → TOUT son filmo
    else:
        affinities = profile.get("genre_affinity", {})
        genre_names = [g for g, _ in sorted(affinities.items(), key=lambda x: x[1], reverse=True)[:5]]

    if selected_type == "Films": types = ["movie"]
    elif selected_type == "Séries": types = ["tv"]
    else: types = ["movie", "tv"]

    seen_tmdb: set[str] = set()
    for media, _kind in _all_media(dataset):
        tmdb = _media_tmdb_id(media)
        if tmdb: seen_tmdb.add(str(tmdb))

    candidates: list[dict] = []
    for media_type in types:
        genre_map = GENRE_FR_TO_TMDB_TV if media_type == "tv" else GENRE_FR_TO_TMDB
        gids = [str(genre_map[g]) for g in genre_names if g in genre_map]

        if media_type == "tv" and (filter_actor_ids or filter_director_ids):
            # TV + acteur/réal : /person/{id}/tv_credits (Discover ne supporte
            # pas with_cast pour TV).
            person_ids = filter_actor_ids + filter_director_ids
            for pid in person_ids:
                try:
                    resp = requests.get(
                        f"https://api.themoviedb.org/3/person/{pid}/tv_credits",
                        params={"api_key": api_key, "language": "fr-FR"},
                        timeout=10,
                    )
                    if resp.status_code == 200:
                        for item in (resp.json().get("cast") or []) + (resp.json().get("crew") or []):
                            tid = str(item.get("id"))
                            if tid not in seen_tmdb and item.get("poster_path"):
                                candidates.append({"tmdb": item["id"], "kind": "tv"})
                                seen_tmdb.add(tid)
                except Exception:
                    pass
        else:
            # FILMS : Discover avec with_cast/with_crew (supportés)
            # TV sans acteur : Discover par genres
            params = {
                "api_key": api_key, "language": "fr-FR",
                "sort_by": "popularity.desc", "vote_count.gte": 500,
                "vote_average.gte": max(note_min, 7.0),
            }
            if gids:
                params["with_genres"] = "|".join(gids)
            # with_cast/with_crew uniquement pour les FILMS
            if media_type == "movie":
                if filter_actor_ids:
                    params["with_cast"] = "|".join(filter_actor_ids)
                if filter_director_ids:
                    params["with_crew"] = "|".join(filter_director_ids)
            if included_countries:
                params["with_origin_country"] = ",".join(c.upper() for c in included_countries)
            if excluded_genres:
                without = [str(genre_map[g]) for g in excluded_genres if g in genre_map]
                if without:
                    params["without_genres"] = ",".join(without)
            if year_range:
                date_field = "primary_release_date" if media_type == "movie" else "first_air_date"
                params[f"{date_field}.gte"] = f"{year_range[0]}-01-01"
                params[f"{date_field}.lte"] = f"{year_range[1]}-12-31"
            for _page in (1, 2):
                params["page"] = _page
                try:
                    resp = requests.get(f"https://api.themoviedb.org/3/discover/{media_type}", params=params, timeout=12)
                    if resp.status_code != 200:
                        break
                    for item in (resp.json().get("results") or []):
                        tid = str(item.get("id"))
                        if tid not in seen_tmdb:
                            candidates.append({"tmdb": item.get("id"), "kind": media_type})
                            seen_tmdb.add(tid)
                except Exception:
                    pass

    # Enrichir + scorer
    def enrich(cand):
        try:
            payload = _fetch_tmdb_item(cand["kind"], cand["tmdb"], api_key)
        except Exception:
            return None
        return _build_item_from_tmdb(cand["tmdb"], cand["kind"], payload) if payload else None

    with ThreadPoolExecutor(max_workers=10) as executor:
        items = [i for i in executor.map(enrich, candidates) if i]
    scored = []
    for item in items:
        row = score_item(item, profile, source_name="🌐 Hors de tes listes")
        row["_outside"] = True
        scored.append(row)

    # Filtrage CLIENT (safety net — fiable pour films ET séries)
    if selected_studios:
        sel_cf = {s.casefold() for s in selected_studios}
        scored = [r for r in scored if any(s.casefold() in sel_cf for s in r.get("studios", []))]
    if excluded_countries:
        scored = [r for r in scored if str(r.get("country") or "").lower() not in excluded_countries]
    if year_range:
        scored = [r for r in scored if year_range[0] <= (r.get("year") or 0) <= year_range[1]]

    scored.sort(key=lambda r: r["score"], reverse=True)
    return scored[:20]


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
    # ── 🗂️ Sélection : source, genres, type, acteurs, studios ──────────────
    with st.expander("🗂️ Sélection de contenu", expanded=True):
        source_col, type_col = st.columns(2)
        selected_label = source_col.selectbox("Source", list(source_by_label), key="qr_source")
        source = source_by_label[selected_label]

        genre_records = sections.get("genres") or []
        if genre_records:
            genre_by_title = {
                str(item.get("title") or item.get("slug") or ""): str(item.get("slug") or "")
                for item in genre_records
                if isinstance(item, dict) and item.get("slug")
            }
            genre_titles = sorted([title for title in genre_by_title if title], key=str.casefold)
        else:
            # Import ZIP Trakt : construire la liste des genres depuis les contenus.
            genre_by_title = {}
            seen: set[str] = set()
            for src in sources:
                for item in (src.get("movies") or []) + (src.get("shows") or []):
                    for genre in item.get("genres") or []:
                        name = genre.get("name") if isinstance(genre, dict) else str(genre)
                        if name and name not in seen:
                            seen.add(name)
                            genre_by_title[str(name)] = str(name)
            genre_titles = sorted(seen, key=str.casefold)
        selected_type = type_col.selectbox("Type", ["Tous", "Films", "Séries"], key="watchlist_type")
        # Genres : le multiselect est juste au-dessus de son mode ET/OU (regroupé).
        selected_genres = st.multiselect(
            "Genres (recherche intégrée)",
            genre_titles,
            key="qr_genres",
            placeholder="Choisis 1+ genres…",
        )
        genre_mode = st.radio(
            "Genres : correspondance",
            ["Au moins un (OU)", "Tous (ET)"],
            key="qr_genre_mode",
            horizontal=True,
        )
        excluded_genres = st.multiselect(
            "🚫 Genres à exclure",
            genre_titles,
            key="qr_genres_exclude",
            placeholder="Aucun genre exclu",
        )
        country_codes = sorted({
            str(m.get("country") or "").strip().lower()
            for m, _k in _all_media(_dataset())
            if m.get("country") and str(m["country"]).strip()
        })
        country_opts = sorted({_country_display(c) for c in country_codes if c})
        incl_country_col, excl_country_col = st.columns(2)
        with incl_country_col:
            included_countries_disp = st.multiselect(
                "🌍 Pays d'origine à inclure",
                country_opts,
                key="qr_countries_include",
                placeholder="Tous les pays",
            )
        with excl_country_col:
            excluded_countries_disp = st.multiselect(
                "🌍 Pays d'origine à exclure",
                country_opts,
                key="qr_countries_exclude",
                placeholder="Aucun pays exclu",
            )
        included_countries = set()
        excluded_countries = set()
        for c in country_codes:
            disp = _country_display(c)
            if disp in included_countries_disp:
                included_countries.add(c)
            if disp in excluded_countries_disp:
                excluded_countries.add(c)

        # Acteurs / réalisateurs / studios (0 appel API : liste GLOBALE).
        all_actors = sorted({
            str(a["name"]).strip()
            for m, _k in _all_media(_dataset())
            for a in (m.get("actors") or []) if isinstance(a, dict) and a.get("name")
        }, key=str.casefold)
        all_directors = sorted({
            str(d["name"]).strip()
            for m, _k in _all_media(_dataset())
            for d in (m.get("directors") or []) if isinstance(d, dict) and d.get("name")
        }, key=str.casefold)
        all_studios = sorted({
            str(st_["name"]).strip()
            for m, _k in _all_media(_dataset())
            for st_ in (m.get("studios") or []) if isinstance(st_, dict) and st_.get("name")
        }, key=str.casefold)
        actor_col, director_col, studio_col = st.columns(3)
        selected_actors = actor_col.multiselect(
            "Acteurs",
            all_actors,
            key="qr_actors",
            placeholder="Acteur…",
        )
        selected_directors = director_col.multiselect(
            "Réalisateur",
            all_directors,
            key="qr_directors",
            placeholder="Réalisateur…",
        )
        selected_studios = studio_col.multiselect(
            "Studios",
            all_studios,
            key="qr_studios",
            placeholder="Studio…",
        )
        # Acteurs : le mode ET/OU est regroupé juste en dessous du multiselect.
        cast_mode = st.radio(
            "Acteurs : correspondance",
            ["Au moins un (OU)", "Tous (ET)"],
            key="qr_cast_mode",
            horizontal=True,
        )
        st.caption(
            "🎭 Genres : « Tous (ET) » = TOUS les genres choisis · « Au moins un (OU) » = n'importe lequel. "
            "🎬 Acteurs : même logique ET/OU. 🏢 Studios : toujours « au moins un »."
        )

    # ── 🔍 Filtres ────────────────────────────────────────────────────────
    # Replié par défaut : un nouvel utilisateur voit d'abord ses résultats
    # (tri recommandé), puis ouvre ce menu pour affiner. Les valeurs par
    # défaut s'appliquent même replié (aucun filtre actif au départ).
    with st.expander("🔍 Filtres", expanded=False):
        # Temps max + Durée minimum : paire complémentaire (un « entre » de
        # durée), réunie en premier comme demandé. Les autres filtres suivent.
        f1, f2, f3 = st.columns(3)
        duration_min = f1.selectbox(
            "Durée minimum",
            ["Aucune", "≥ 1h", "≥ 1h30", "≥ 2h", "≥ 2h30", "≥ 3h"],
            key="qr_duration_min",
        )
        time_filter = f2.selectbox(
            "Temps max",
            ["Aucune limite", "Moins d'1h30", "Moins de 2h", "Moins de 3h", "Soirée (< 10h)", "Week-end (< 24h)"],
            key="qr_time",
        )
        year_lo, year_hi = f3.slider(
            "Années de sortie",
            min_value=1950, max_value=2025, value=(1950, 2025),
            key="qr_year_range",
        )
        f4, f5, f6 = st.columns(3)
        search = f3.text_input("Recherche", key="qr_search", placeholder="Titre…")
        note_min = f4.select_slider(
            "Note minimum",
            options=[0.0, 5.0, 6.0, 7.0, 7.5, 8.0, 8.5, 9.0],
            key="qr_note_min",
        )
        status_filter = f5.selectbox(
            "Statut",
            ["Tous les statuts", "Séries terminées", "Séries en cours", "Séries annulées"],
            key="qr_status",
        )

    # ── 🔃 Tri & affichage ────────────────────────────────────────────────
    # Replié par défaut (même logique que Filtres) : le tri recommandé
    # « ✨ Pour moi » s'applique sans ouvrir ce menu.
    with st.expander("🔃 Tri & affichage", expanded=False):
        p1, p2, p3 = st.columns([0.44, 0.34, 0.22])
        preset = p1.selectbox("Preset rapide", PRESET_NAMES, key="qr_preset")
        sort_mode = p2.selectbox(
            "Trier par",
            [
                "✨ Pour moi (recommandé)",
                "⭐ Meilleures notes",
                "⭐ Notes les plus basses",
                "⏱️ Plus rapide",
                "⏱️ Plus long d'abord",
                "🔥 Populaires",
                "🔥 Moins populaires",
                "📥 Ajouté récemment",
                "📥 Ajouté le plus ancien",
                "🆕 Nouveautés",
                "🆒 Plus anciens d'abord",
                "🚪 Zéro effort",
                "🚪 Le plus exigeant",
                "🎬 Films d'abord",
                "📺 Séries d'abord",
                "🙅 Pas pour moi",
            ],
            key="qr_sort",
        )
        display_limit = p3.selectbox("Afficher", [20, 50, 100], key="watchlist_limit")


    search = st.text_input("🔎 Rechercher un titre", key="qr_search", placeholder="Tape un titre…")
    st.button("🔄 Réinitialiser tous les filtres", on_click=_reset_recommendation_filters, key="reset_qr", type="primary", use_container_width=True)

    items = list(source["movies"]) + list(source["shows"])
    api_calls_extra = 0
    if selected_genres:
        # Filtrage LOCAL : les items ont DÉJÀ tous leurs genres grâce à
        # l'enrichissement TMDB. Plus d'appel API MDBList → économise le quota
        # ET préserve les genres complets + les scores (plus de troncage, plus
        # de pastilles qui disparaissent au filtrage).
        wanted = {str(g).casefold() for g in selected_genres}

        def _match_genre(media):
            names = set()
            for genre in (media.get("genres") or []):
                if isinstance(genre, dict):
                    genre = genre.get("name") or genre.get("slug")
                if genre:
                    names.add(str(genre).casefold())
            if genre_mode == "Tous (ET)":
                return wanted.issubset(names)
            return bool(names & wanted)

        items = [item for item in items if _match_genre(item)]

    scored = [
        score_item(item, profile, source_name=source["name"])
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
        if excluded_genres:
            excluded_set = {str(g).casefold() for g in excluded_genres}
            if {str(g).casefold() for g in (row.get("genres") or [])} & excluded_set:
                continue
        if excluded_countries:
            if str(row.get("country") or "").lower() in excluded_countries:
                continue
        if included_countries and str(row.get("country") or "").lower() not in included_countries:
            continue
        if search and search.casefold() not in _media_title(row["item"]).casefold():
            continue
        if note_min and (row.get("note") or 0) < note_min:
            continue
        if not time_ok(row):
            continue
        if duration_min != "Aucune":
            minutes = row.get("runtime") or 0
            minimums = {"≥ 1h": 60, "≥ 1h30": 90, "≥ 2h": 120, "≥ 2h30": 150, "≥ 3h": 180}
            if not minutes or minutes < minimums[duration_min]:
                continue
        if year_lo > 1950 or year_hi < 2025:
            if not (year_lo <= (row.get("year") or 0) <= year_hi):
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
        if selected_actors or selected_studios or selected_directors:
            row_actors = {str(a).casefold() for a in (row.get("people") or [])}
            row_studios = {str(st_).casefold() for st_ in (row.get("studios") or [])}
            row_directors = {str(d).casefold() for d in (row.get("directors") or [])}
            wanted_actors = {str(a).casefold() for a in selected_actors}
            wanted_studios = {str(st_).casefold() for st_ in selected_studios}
            wanted_directors = {str(d).casefold() for d in selected_directors}
            ok = True
            if wanted_actors:
                if cast_mode == "Tous (ET)":
                    ok = ok and wanted_actors.issubset(row_actors)
                else:
                    ok = ok and bool(row_actors & wanted_actors)
            if wanted_studios:
                # Studios : toujours « au moins un » (OU).
                ok = ok and bool(row_studios & wanted_studios)
            if wanted_directors:
                # Réalisateurs : toujours « au moins un » (OU).
                ok = ok and bool(row_directors & wanted_directors)
            if not ok:
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
    elif sort_mode.startswith("⭐ Notes"):
        display_rows.sort(key=lambda row: ((row.get("note") or 0), -row["score"]))
    elif sort_mode.startswith("⭐"):
        display_rows.sort(key=lambda row: (-(row.get("note") or 0), -row["score"]))
    elif sort_mode.startswith("⏱️ Plus long"):
        display_rows.sort(key=lambda row: (-(needed_minutes(row) or 10**9), -row["score"]))
    elif sort_mode.startswith("⏱️"):
        display_rows.sort(key=lambda row: (needed_minutes(row) or 10**9, -row["score"]))
    elif sort_mode.startswith("🔥 Moins"):
        display_rows.sort(key=lambda row: ((row.get("votes") or 0), -row["score"]))
    elif sort_mode.startswith("🔥"):
        display_rows.sort(key=lambda row: (-(row.get("votes") or 0), -row["score"]))
    elif sort_mode.startswith("📥 Ajouté le plus ancien"):
        display_rows.sort(key=lambda row: (row.get("added_days") is None, -(row.get("added_days") or 0), -row["score"]))
    elif sort_mode.startswith("📥"):
        display_rows.sort(key=lambda row: (row.get("added_days") is None, row.get("added_days") or 0, -row["score"]))
    elif sort_mode.startswith("🆒"):
        display_rows.sort(key=lambda row: ((row.get("year") or 0), -row["score"]))
    elif sort_mode.startswith("🆕"):
        display_rows.sort(key=lambda row: (-(row.get("year") or 0), -row["score"]))
    elif sort_mode.startswith("🚪 Le plus exigeant"):
        display_rows.sort(key=lambda row: ((row["friction"]), -row["score"]))
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
        ("filtre déjà mémorisé pour cette session" if selected_genres else "analyse locale · quota MDBList préservé")
    )
    st.markdown(
        f'<div class="accent-callout"><strong>{len(display_rows)} RÉSULTAT(S)</strong> · '
        f'{escape(source_note)}.</div>',
        unsafe_allow_html=True,
    )

    roulette_col, discovery_col, perfect_col = st.columns(3)
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

    _perfect_results = None
    with perfect_col:
        if _tmdb_api_key() and st.button("🎯 Hors de mes listes", type="primary", key="perfect_reco_btn"):
            with st.spinner("🔍 Recherche de perles hors de tes listes…"):
                _perfect_results = _perfect_recommendation(
                    profile, _dataset(), selected_type, selected_genres, note_min, _tmdb_api_key(),
                    excluded_genres=excluded_genres,
                    included_countries=included_countries if included_countries else None,
                    excluded_countries=excluded_countries if excluded_countries else None,
                    selected_actors=selected_actors if selected_actors else None,
                    selected_directors=selected_directors if selected_directors else None,
                    selected_studios=selected_studios if selected_studios else None,
                    year_range=(year_lo, year_hi) if (year_lo > 1950 or year_hi < 2025) else None,
                )

    roulette = st.session_state.get("_roulette_result")
    if roulette and any(row["key"] == roulette.get("key") for row in filtered):
        st.markdown("### Le hasard a choisi")
        _render_recommendation_card(roulette, highlighted=True)

    if _perfect_results:
        st.markdown(f"### 🎯 Hors de mes listes ({len(_perfect_results)})")
        st.caption("Contenus correspondant à ton profil, que tu n'as pas encore dans tes listes. 🌐 = découverte TMDB.")
        for result in _perfect_results:
            _render_recommendation_card(result)

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
    st.markdown(
        _metric_cards([
            {"emoji": "⏸️", "k": "Points de reprise", "v": len(playback), "d": "reprises en cours"},
            {"emoji": "📺", "k": "Séries en cours", "v": len(progress_rows), "d": "Up Next"},
            {"emoji": "🚫", "k": "Séries abandonnées", "v": len(dropped), "d": "statut abandonnée"},
        ]),
        unsafe_allow_html=True,
    )

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
            image_html = _poster_html(poster, row.get("type") or "")
            watched = int(row.get("watched_episodes") or 0)
            total = int(row.get("total_episodes") or 0)
            remaining = int(row.get("remaining_episodes") or 0)
            percent = float(row.get("percent") or 0)
            watched_time = _format_minutes(int(row.get("watched_minutes") or 0))
            remaining_time = _format_minutes(int(row.get("remaining_minutes") or 0))
            genres = progress_genres(row)
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
            show_ref = row.get("show") if isinstance(row.get("show"), dict) else {}
            show_ids = show_ref.get("ids") if isinstance(show_ref.get("ids"), dict) else {}
            raw_show_title = str(show_ref.get("title") or row.get("title") or "")
            pct_col = f'<div class="media-list-pct" data-tooltip="Pourcentage de la série déjà visionné">{percent:.0f}%<span class="sub">vu</span></div>'
            pct_inline = f'<span class="mc-inline-pct" data-tooltip="Pourcentage de la série déjà visionné">{percent:.0f}%</span>'
            links_html = _content_links_html(show_ids, raw_show_title, is_show=True, suffix=pct_inline)
            # Progression connue (MDBList) ou inconnue (ZIP Trakt sans métadonnées).
            if total and number:
                progress_line = (
                    f"📊 {watched}/{total} épisode(s) vu(s) · il en reste {remaining} · "
                    f"▶️ Prochain : S{int(season or 0):02d}E{int(number or 0):02d}"
                )
                time_line = f"⏱️ {watched_time} de visionnage · reste {remaining_time}"
                bar_html = (
                    f'<div class="progress-bar-container"><div class="progress-bar-fill" '
                    f'style="width:{max(0,min(percent,100))}%;"></div></div>'
                )
            else:
                progress_line = f"📊 {watched} épisode(s) vu(s) (progression totale inconnue sans MDBList)"
                time_line = f"⏱️ {watched_time} de visionnage"
                bar_html = ""
            # Informations regroupées en un seul bloc compact (toutes conservées) ;
            # le % de finition part à droite, centré verticalement sur la carte.
            info_parts = []
            if genres:
                info_parts.append(f'🎭 {escape(" · ".join(genres))}')
            if dates:
                info_parts.append(f'🗓️ {escape(" · ".join(dates))}')
            info_parts.append(progress_line)
            info_parts.append(time_line)
            info_html = '<small>' + '<br>'.join(info_parts) + '</small>'
            note_html = _public_note_html(show)
            head = (
                f'<div class="mc-head">'
                f'<strong style="font-size:1.05rem;">{title}</strong>'
                f'{note_html}'
                f'</div>'
            )
            st.markdown(
                f'<div class="media-list-card upnext-card">{image_html}'
                f'<div class="media-list-content" style="width:100%;">'
                f'{head}'
                f'{info_html}'
                f'{bar_html}'
                f'{links_html}'
                f'</div>{pct_col}</div>',
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
        image_html = _poster_html(poster, row.get("type") or "")
        title = escape(str(row.get("title") or "Titre inconnu"))
        year = f" ({int(row['year'])})" if row.get("year") else ""
        episode_label = escape(str(row.get("episode_label") or ""))
        progress = float(row.get("progress") or 0)
        runtime = int(row.get("runtime") or 0)
        remaining = int(row.get("remaining_minutes") or 0)
        details = []
        if runtime:
            details.append(f"reste environ {_format_minutes(remaining)}")
        if row.get("is_manual"):
            details.append("check-in manuel")
        else:
            details.append("scrobble actif")
        if row.get("possibly_ended"):
            details.append("nouveau contrôle conseillé")
        info_parts = []
        if episode_label:
            info_parts.append(f"▶️ {episode_label}")
        if details:
            info_parts.append(escape(" · ".join(details)))
        info_html = f'<small>{"<br>".join(info_parts)}</small>' if info_parts else ""
        pct_col = f'<div class="media-list-pct" data-tooltip="Progression visionnée">{progress:.0f}%<span class="sub">vu</span></div>'
        pct_inline = f'<span class="mc-inline-pct" data-tooltip="Progression visionnée">{progress:.0f}%</span>'
        head = (
            f'<div class="mc-head">'
            f'{_type_chip(str(row.get("type") or ""))}'
            f'<strong>{title}{year}</strong>'
            f'{pct_inline}'
            f'<span class="source-badge">EN COURS MAINTENANT</span>'
            f'</div>'
        )
        st.markdown(
            f'<div class="media-list-card upnext-card">{image_html}'
            f'<div class="media-list-content" style="width:100%;">'
            f'{head}'
            f'{info_html}'
            f'<div class="progress-bar-container"><div class="progress-bar-fill" '
            f'style="width:{max(0,min(progress,100))}%;"></div></div>'
            f'</div>{pct_col}</div>',
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
    st.markdown(
        _metric_cards([
            {"emoji": "👻", "k": "Progressions", "v": len(rows), "d": "reprises en pause"},
            {"emoji": "🎬", "k": "Films", "v": sum(row.get("type") == "Film" for row in rows), "d": "reprises"},
            {"emoji": "📺", "k": "Épisodes", "v": sum(row.get("type") == "Épisode" for row in rows), "d": "reprises"},
            {"emoji": "⏱️", "k": "Temps restant connu", "v": _format_minutes(known_remaining) if known_remaining else "—", "d": "à terminer"},
        ]),
        unsafe_allow_html=True,
    )

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
        image_html = _poster_html(poster, row.get("type") or "")
        title = escape(str(row.get("title") or "Titre inconnu"))
        year = f" ({int(row['year'])})" if row.get("year") else ""
        episode_label = escape(str(row.get("episode_label") or ""))
        progress = float(row.get("progress") or 0)
        runtime = int(row.get("runtime") or 0)
        remaining = int(row.get("remaining_minutes") or 0)
        updated = _format_date(row.get("updated_at"))
        details = []
        if runtime:
            details.append(f"durée {_format_minutes(runtime)}")
            details.append(f"reste environ {_format_minutes(remaining)}")
        else:
            details.append("temps restant inconnu")
        if updated:
            details.append(f"dernière activité {updated}")
        if row.get("is_manual"):
            details.append("progression manuelle")
        info_parts = []
        if episode_label:
            info_parts.append(f"▶️ {episode_label}")
        if details:
            info_parts.append(escape(" · ".join(details)))
        info_html = f'<small>{"<br>".join(info_parts)}</small>' if info_parts else ""
        pct_col = f'<div class="media-list-pct" data-tooltip="Progression visionnée">{progress:.0f}%<span class="sub">vu</span></div>'
        pct_inline = f'<span class="mc-inline-pct" data-tooltip="Progression visionnée">{progress:.0f}%</span>'
        row_ids = row.get("ids") if isinstance(row.get("ids"), dict) else {}
        links_html = _content_links_html(row_ids, str(row.get("title") or ""), is_show=(row.get("type") != "Film"), suffix=pct_inline)
        head = (
            f'<div class="mc-head">'
            f'{_type_chip(str(row.get("type") or ""))}'
            f'<strong>{title}{year}</strong>'
            f'{_public_note_html(row)}'
            f'</div>'
        )
        st.markdown(
            f'<div class="media-list-card upnext-card">{image_html}'
            f'<div class="media-list-content" style="width:100%;">'
            f'{head}'
            f'{info_html}'
            f'<div class="progress-bar-container"><div class="progress-bar-fill" '
            f'style="width:{max(0,min(progress,100))}%;"></div></div>'
            f'{links_html}'
            f'</div>{pct_col}</div>',
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

    st.markdown(
        _metric_cards([
            {"emoji": "📦", "k": "Contenus", "v": len(all_rows), "d": "dans le conteneur"},
            {"emoji": "🚩", "k": "Avec signal", "v": sum(bool(row.get("issues")) for row in all_rows), "d": "à examiner"},
            {"emoji": "👀", "k": "Déjà vus", "v": sum(bool(row.get("watched")) for row in all_rows), "d": "dans les listes"},
            {"emoji": "🔁", "k": "Multi-conteneurs", "v": sum(bool(row.get("duplicate")) for row in all_rows), "d": "doublons entre listes"},
        ]),
        unsafe_allow_html=True,
    )

    nb_revoir = sum(bool(row.get("added_after_watch")) for row in all_rows if row.get("watched"))
    nb_retirer = sum(bool(row.get("watched")) and not row.get("added_after_watch") for row in all_rows)
    st.caption(
        f"📌 **Vu · à retirer** ({nb_retirer}) : déjà vu, ajouté à la liste AVANT son visionnage "
        f"(oublié de l'enlever). "
        f"🔄 **Vu · à revoir** ({nb_revoir}) : déjà vu, ajouté APRÈS son visionnage "
        "(remis exprès pour le revoir)."
    )

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

    # ── Suppression sécurisée (listes statiques / Watchlist uniquement) ──────
    writable_type = str(selected_source.get("type") or "")
    is_writable = writable_type in {"native", "static"}
    if is_writable and mdb_oauth.is_connected():
        st.divider()
        conteneur_label = str(selected_source.get("label") or selected_label)
        st.markdown(f"#### 🗑️ Suppression sécurisée — « {escape(conteneur_label)} »")
        st.caption(
            "Cette liste correspond au « Conteneur à auditer » choisi en haut de la page. "
            "Coche un contenu ci-dessous : des **actions intelligentes** s'affichent "
            "selon les listes où il se trouve (retirer d'une liste précise, de la "
            "Watchlist, ou partout). Une **sauvegarde de sécurité** est téléchargeable "
            "avant chaque confirmation. Les écritures se font une à une."
        )

        # Lignes réellement présentes dans ce conteneur (pas les vues combinées),
        # triées par priorité de nettoyage décroissante (les plus urgentes d'abord).
        writable_rows = sorted(
            (
                row for row in all_rows
                if row.get("source_key") == selected_source.get("key")
            ),
            key=lambda row: (-(row.get("priority") or 0), str(row.get("title") or "").casefold()),
        )
        if not writable_rows:
            st.caption("Aucun contenu individuel supprimable dans cette vue (vue combinée ou liste vide).")
        else:
            # Index des appartenances par contenu (quelles listes le contiennent).
            members = membership_index(dataset)
            # Sélection par cases à cocher (une action à la fois, comme demandé).
            checked = st.multiselect(
                "Cocher le contenu à traiter",
                [f"{row.get('type')} — {row.get('title')} ({row.get('year') or '?'})" for row in writable_rows],
                key="audit_remove_check",
                placeholder="Choisis UN contenu à la fois",
            )
            if len(checked) > 1:
                st.caption("⚠️ Une seule action à la fois : ne coche qu'un contenu, puis traite les autres un par un.")
            if len(checked) == 1:
                label = checked[0]
                target = next((row for row in writable_rows if f"{row.get('type')} — {row.get('title')} ({row.get('year') or '?'})" == label), None)
                if target is None:
                    st.caption("Contenu introuvable.")
                else:
                    target_kind = "movie" if target.get("kind") == "movie" else "show"
                    identity = target.get("key") or ""
                    record = members.get(identity) or {}
                    member_sources = record.get("memberships") or []
                    target_item = target.get("item") or {}
                    # Actions intelligentes : les conteneurs où le contenu existe.
                    writable_members = [
                        m for m in member_sources
                        if m.get("type") in {"native", "static"} and m.get("writable")
                    ]
                    st.markdown(
                        f"**Aperçu** : « {escape(str(target.get('title')))} » ({target.get('year') or '?'}) "
                        f"est présent dans **{len(member_sources)}** conteneur(s) : "
                        + (" · ".join(escape(m["label"]) for m in member_sources) if member_sources else selected_label)
                        + "."
                    )
                    action_options = []
                    action_map = {}
                    for m in writable_members:
                        action_options.append(f"Retirer de « {m['label']} »")
                        action_map[f"Retirer de « {m['label']} »"] = m
                    if len(writable_members) >= 2:
                        action_options.append("Retirer de TOUS les conteneurs (cette action en fera plusieurs)")
                        action_map["Retirer de TOUS les conteneurs (cette action en fera plusieurs)"] = "all"
                    if not action_options:
                        action_options.append("Aucune action possible (conteneurs non modifiables)")
                        action_map["Aucune action possible (conteneurs non modifiables)"] = None
                    chosen_action = st.selectbox("Action à effectuer", action_options, key="audit_remove_action")
                    st.caption(
                        "💡 Exemple : si « Titanic » est dans « Gros films » ET la Watchlist, "
                        "tu peux le retirer des « Gros films » seulement, ou des deux."
                    )
                    backup_payload = {
                        "action": "remove_content",
                        "content": {
                            "type": target.get("type"),
                            "title": target.get("title"),
                            "year": target.get("year"),
                            "item": target_item,
                        },
                        "targets": [
                            {
                                "kind": "watchlist" if m.get("key", "").startswith("watchlist") else "list",
                                "list_key": m.get("key"),
                                "list_label": m.get("label"),
                            }
                            for m in (writable_members if chosen_action != "Retirer de TOUS les conteneurs (cette action en fera plusieurs)" else writable_members)
                        ] if chosen_action and chosen_action != "Aucune action possible (conteneurs non modifiables)" else [],
                        "export_date": datetime.now(PARIS_TZ).isoformat(),
                    }
                    if st.button("💾 Télécharger la sauvegarde de sécurité (JSON)", key="audit_remove_backup"):
                        st.download_button(
                            "⬇️ Enregistrer le fichier de sauvegarde",
                            data=json.dumps(backup_payload, ensure_ascii=False, default=str, indent=2),
                            file_name=f"sauvegarde-avant-retrait-{datetime.now(PARIS_TZ).strftime('%Y%m%d-%H%M%S')}.json",
                            mime="application/json",
                            key="audit_remove_backup_dl",
                            type="primary",
                        )
                        st.caption("Conserve ce fichier : il permet de ré-ajouter le contenu si besoin.")
                    confirm = st.checkbox(
                        "✅ Je confirme : je veux exécuter cette action (réversible via la sauvegarde)",
                        key="audit_remove_confirm",
                    )
                    if confirm and chosen_action and chosen_action != "Aucune action possible (conteneurs non modifiables)":
                        if st.button("🗑️ Exécuter la suppression", type="primary", key="audit_remove_go"):
                            targets = writable_members if chosen_action == "Retirer de TOUS les conteneurs (cette action en fera plusieurs)" else [action_map[chosen_action]]
                            done = []
                            with st.spinner("Écriture MDBList…"):
                                try:
                                    provider = MDBListProvider(mdb_oauth.access_token())
                                    for m in targets:
                                        is_watchlist = str(m.get("key") or "").startswith("watchlist") or m.get("type") == "native"
                                        if is_watchlist:
                                            if target_kind == "movie":
                                                provider.remove_watchlist_items(movies=[target_item])
                                            else:
                                                provider.remove_watchlist_items(shows=[target_item])
                                        else:
                                            list_id = None
                                            # retrouver l'id de la liste via les sources
                                            for source in sources:
                                                if source.get("key") == m.get("key") and source.get("id") is not None:
                                                    list_id = source.get("id")
                                                    break
                                            if list_id is not None:
                                                if target_kind == "movie":
                                                    provider.remove_list_items(int(list_id), movies=[target_item])
                                                else:
                                                    provider.remove_list_items(int(list_id), shows=[target_item])
                                            else:
                                                st.warning(f"Liste {m.get('label')} sans identifiant : ignorée.")
                                        done.append(m.get("label"))
                                except Exception as exc:
                                    st.error(f"Écriture impossible : {exc}")
                                    done = []
                            if done:
                                st.markdown(
                                    f'<div class="accent-callout"><strong>✓ RETIRÉ</strong> · '
                                    f'« {escape(str(target.get("title")))} » a été retiré de : '
                                    f'{escape(" · ".join(done))}. '
                                    f'Recharge tes données (Actualiser) pour voir les listes à jour.</div>',
                                    unsafe_allow_html=True,
                                )

    # ── Marquer vu / non-vu (listes statiques / Watchlist) ───────────────────
    if is_writable and mdb_oauth.is_connected():
        st.divider()
        conteneur_label = str(selected_source.get("label") or selected_label)
        st.markdown(f"#### ✍️ Marquer vu / non-vu — « {escape(conteneur_label)} »")
        st.caption(
            "Choisis un contenu, une action, puis confirme. "
            "Ces opérations sont réversibles à tout moment."
        )
        all_writable = writable_rows
        if all_writable:
            # Recherche par frappe (comme la suppression sécurisée) : on tape
            # des lettres et la liste se filtre instantanément.
            f_type = st.selectbox(
                "Type",
                ["Tous", "Films", "Séries"],
                key="audit_manage_type",
            )
            available = []
            for row in all_writable:
                if f_type != "Tous":
                    wanted = "Film" if f_type == "Films" else "Série"
                    if row.get("type") != wanted:
                        continue
                available.append(row)
            if not available:
                st.caption("Aucun contenu de ce type dans cette liste.")
            else:
                label_opts = [
                    f"{row.get('type')} — {row.get('title')} ({row.get('year') or '?'})"
                    for row in available
                ]
                chosen_op = st.multiselect(
                    "Contenu à gérer (tape pour filtrer)",
                    label_opts,
                    max_selections=1,
                    key="audit_manage_choice",
                    placeholder="Choisis UN contenu à la fois…",
                )
                if len(chosen_op) != 1:
                    st.caption("Sélectionne un contenu pour voir les actions.")
                else:
                    target_op = available[label_opts.index(chosen_op[0])]
                    target_item = target_op.get("item") or {}
                    target_kind = "movie" if target_op.get("kind") == "movie" else "show"
                    st.markdown(
                        f"**Aperçu** : « {escape(str(target_op.get('title')))} » "
                        f"({target_op.get('year') or '?'}) — {escape(str(target_op.get('type')))}."
                    )
                    # Choix de l'action AVANT la confirmation.
                    action_opts = ["✅ Marquer vu", "🔄 Marquer non-vu"]
                    if target_kind == "show":
                        action_opts.append("🚫 Marquer abandonnée")
                    chosen_action = st.radio(
                        "Action à effectuer",
                        action_opts,
                        horizontal=True,
                        key="audit_manage_action",
                    )
                    confirm_op = st.checkbox(
                        "✅ Je confirme l'action choisie ci-dessus",
                        key="audit_manage_confirm",
                    )
                    if confirm_op and st.button("⚡ Exécuter l'action", type="primary", key="audit_manage_go"):
                        with st.spinner("Écriture MDBList…"):
                            try:
                                provider = MDBListProvider(mdb_oauth.access_token())
                                if chosen_action.startswith("✅"):
                                    if target_kind == "movie":
                                        provider.set_watched(movies=[target_item], watched=True)
                                    else:
                                        provider.set_watched(shows=[target_item], watched=True)
                                    message = "MARQUÉ VU"
                                    detail = "est maintenant vu"
                                elif chosen_action.startswith("🔄"):
                                    if target_kind == "movie":
                                        provider.set_watched(movies=[target_item], watched=False)
                                    else:
                                        provider.set_watched(shows=[target_item], watched=False)
                                    message = "MARQUÉ NON-VU"
                                    detail = "n'est plus marqué vu (l'historique reste conservé)"
                                else:
                                    provider.set_dropped(shows=[target_item], dropped=True)
                                    message = "MARQUÉE ABANDONNÉE"
                                    detail = "est maintenant marquée abandonnée"
                                st.markdown(
                                    f'<div class="accent-callout"><strong>✓ {message}</strong> · '
                                    f'« {escape(str(target_op.get("title")))} » {detail}. '
                                    f'Actualise tes données pour voir le changement.</div>',
                                    unsafe_allow_html=True,
                                )
                            except Exception as exc:
                                st.error(f"Écriture impossible : {exc}")
        else:
            st.caption("Aucun contenu individuel dans cette vue.")

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
        st.markdown(
            _metric_cards([
                {"emoji": "🆕", "k": "Ajouts", "v": len(visible_additions), "d": "dans l'historique"},
                {"emoji": "✅", "k": "Dates connues", "v": known_dates, "d": "ajouts datés"},
                {"emoji": "⚠️", "k": "Dates non fournies", "v": len(visible_additions) - known_dates, "d": "sans date"},
            ]),
            unsafe_allow_html=True,
        )
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
    if not valid and not _dataset():
        return False, message or "Session MDBList indisponible."
    start_date = datetime.now(PARIS_TZ).date()
    horizon = max(1, min(int(horizon_days), 545))
    end_date = start_date + timedelta(days=horizon)
    mode = "mdblist"
    events: list[dict[str, Any]] = []
    calendar_error: str | None = None
    provider: MDBListProvider | None = None
    if valid:
        try:
            provider = MDBListProvider(mdb_oauth.access_token())
        except Exception as exc:
            valid = False
            calendar_error = str(exc)
    if valid and provider is not None:
        try:
            # L'endpoint MDBList limite chaque appel à 120 jours : les horizons
            # plus longs sont découpés en tranches successives puis fusionnés.
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
        # Pas d'exception mais zéro événement : le service a répondu autre chose.
        if not events and calendar_error is None:
            calendar_error = getattr(provider, "calendar_error", None)
        if not events and calendar_error is None:
            calendar_error = (
                "Le service calendrier MDBList a répondu mais n'a renvoyé aucun événement "
                "sur cet horizon (réponse vide ou hors plage)."
            )
    else:
        mode = "local"
        calendar_error = calendar_error or (
            "Aucune session MDBList : calendrier construit uniquement depuis vos données."
        )

    dataset = _dataset()
    # Les dates déjà chargées (Up Next et listes) alimentent un calendrier de
    # secours, sans limite de 120 jours puisque aucune requête supplémentaire.
    local_events = build_local_calendar_events(dataset, start_date, end_date)
    # Enrichissement par appels groupés officiels : dates futures des films et
    # premières de séries présents dans vos listes et votre Watchlist.
    enriched: list[dict[str, Any]] = []
    enrich_diag: dict[str, Any] = {}
    if provider is not None:
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
        "request_count": provider.request_count if provider is not None else 0,
        "mode": mode,
        "event_counts": {
            "mdblist": len(events),
            "local": len(local_events),
            "enriched": len(enriched),
        },
        "enrich_diag": enrich_diag,
        "calendar_error": calendar_error,
    }
    if provider is not None:
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
    if not mdb_oauth.is_connected() and not _dataset():
        st.markdown(
            '<div class="accent-callout"><strong>CONNEXION NÉCESSAIRE</strong> · '
            'Connectez MDBList depuis le Tableau de bord (ou importez un ZIP Trakt) '
            'pour consulter votre calendrier personnel.</div>',
            unsafe_allow_html=True,
        )
        return

    st.caption(
        "Films, premières de séries et prochains épisodes liés à vos données "
        "(MDBList ou ZIP Trakt). Un horizon complet est chargé puis filtré localement."
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
    st.markdown(
        _metric_cards([
            {"emoji": "🗓️", "k": "Événements", "v": len(rows), "d": "sur l'horizon choisi"},
            {"emoji": "🎬", "k": "Films", "v": sum(row.get("type") == "Film" for row in rows), "d": "sorties"},
            {"emoji": "📺", "k": "Épisodes", "v": sum(row.get("type") == "Épisode" for row in rows), "d": "diffusions"},
            {"emoji": "⏭️", "k": "Prochaine date", "v": min(row["datetime"] for row in dated).strftime("%d/%m") if dated else "—", "d": "premier événement"},
        ]),
        unsafe_allow_html=True,
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
        erreur_texte = f" — {cache['calendar_error']}" if cache.get("calendar_error") else ""
        st.caption(
            f"Calendrier de secours construit le {checked} depuis les dates déjà disponibles "
            f"(Up Next et vos listes) sur tout l'horizon choisi{extra_text}. "
            f"Le service calendrier MDBList n'a pas répondu{erreur_texte}, mais les filtres et exports restent utilisables."
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
                image_html = _poster_html(poster, row.get("type") or "")
                title = escape(str(row.get("title") or "Titre inconnu"))
                year = f" ({int(row['year'])})" if row.get("year") else ""
                episode = escape(str(row.get("episode_label") or ""))
                event_datetime = row.get("datetime")
                time_text = event_datetime.strftime("%H:%M") if event_datetime and any((event_datetime.hour, event_datetime.minute)) else ""
                meta = []
                if row.get("genres"):
                    meta.append("🎭 " + " · ".join(row["genres"]))
                if row.get("source") and row.get("source") != "Calendrier MDBList":
                    meta.append(str(row["source"]))
                info_parts = []
                if episode:
                    info_parts.append(f"▶️ {episode}")
                if meta:
                    info_parts.append(escape(" · ".join(meta)))
                inline_time = f'<span class="mc-inline-pct" data-tooltip="Horaire de diffusion">🕒 {escape(time_text)}</span>' if time_text else ''
                info_html = f'<small>{"<br>".join(info_parts)}</small>' if info_parts else ""
                row_ids = row.get("ids") if isinstance(row.get("ids"), dict) else {}
                links_html = _content_links_html(row_ids, str(row.get("title") or ""), is_show=(row.get("type") != "Film"), suffix=inline_time)
                head = (
                    f'<div class="mc-head">'
                    f'{_type_chip(str(row.get("type") or ""))}'
                    f'<strong>{title}{year}</strong>'
                    f'{_public_note_html(row)}'
                    f'</div>'
                )
                time_pct = (
                    f'<div class="media-list-pct" data-tooltip="Horaire de diffusion">{escape(time_text)}'
                    f'<span class="sub">horaire</span></div>'
                    if time_text else ""
                )
                st.markdown(
                    f'<div class="media-list-card poster-card">{image_html}'
                    f'<div class="media-list-content" style="width:100%;">'
                    f'{head}'
                    f'{info_html}{links_html}'
                    f'</div>{time_pct}</div>',
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


def render_detailed_stats_page(filtered: "pd.DataFrame", period_label: str) -> None:
    """Statistiques détaillées — reçoit le DataFrame DÉJÀ filtré par les
    slicers uniques de la page, plus aucun filtre ni tableau dupliqué."""
    if filtered.empty:
        st.warning("Aucun résultat pour ces filtres.")
        return

    st.divider()
    st.markdown('<div class="page-title">📊 Statistiques détaillées</div>', unsafe_allow_html=True)
    st.caption(
        f"Graphiques et analyses sur la sélection filtrée ({period_label}). "
        "Les valeurs sont exprimées en **heures** sauf indication contraire. "
        "Note : un contenu avec plusieurs genres est compté dans chaque genre."
    )

    total_lectures = int(filtered["lectures"].sum())
    total_minutes = int(filtered["duree"].sum())
    notes = filtered.loc[filtered["note"] > 0, "note"]
    note_moyenne = notes.mean()
    nb_jours = max((filtered["date_dt"].max() - filtered["date_dt"].min()).days + 1, 1)
    daily = filtered.groupby(filtered["date_dt"].dt.date)["lectures"].sum()
    record_jour = int(daily.max()) if not daily.empty else 0

    st.markdown(
        _metric_cards([
            {"emoji": "🎬", "k": "Visionnages", "v": total_lectures, "d": "films + épisodes"},
            {"emoji": "⏱️", "k": "Temps visionné", "v": _format_minutes(total_minutes) if total_minutes else "—", "d": "sur la sélection"},
            {"emoji": "🌡️", "k": "Note moyenne", "v": f"{note_moyenne:.1f}" if pd.notna(note_moyenne) else "—", "d": "sur 10"},
            {"emoji": "📅", "k": "Moyenne / jour", "v": f"{total_lectures / nb_jours:.1f}", "d": "visionnages par jour"},
            {"emoji": "🏆", "k": "Record en 1 jour", "v": record_jour, "d": "pic d'activité"},
        ]),
        unsafe_allow_html=True,
    )

    # ── Heatmap d'activité (suit les filtres) ────────────────────────────────
    st.divider()
    st.markdown("#### 🗓️ Ton activité en un coup d'œil")
    st.caption(
        "Chaque case = un jour de la période filtrée (52 dernières semaines si « Tout »). "
        "Survole une case : date + visionnages du jour."
    )
    heat_html = stats_mod.heatmap_html(filtered)
    if heat_html:
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

    # ── Vue d'ensemble : ALL-TIME (non filtrée par les slicers) ──────────────
    render_dataset_overview()
    st.caption(
        "👆 La vue d'ensemble ci-dessus est **non filtrée** (toutes périodes confondues). "
        "Les slicers ci-dessous s'appliquent à l'historique, aux graphiques et aux analyses."
    )

    rows = normalize_history(dataset, timezone_name="Europe/Paris")
    if not rows:
        st.caption("Aucun visionnage n’est disponible dans le dataset actuel.")
        return
    df = stats_mod.build_frame(rows)
    if df.empty:
        st.caption("Aucune donnée datée pour les statistiques.")
        return

    # ── Slicers UNIQUES (appliqués à toute la page) ──────────────────────────
    dated_values = [row["watched_at"].date() for row in rows if row.get("watched_at")]
    earliest = min(dated_values) if dated_values else datetime.now(PARIS_TZ).date()
    latest = max(dated_values) if dated_values else datetime.now(PARIS_TZ).date()

    period_col, type_col, genre_col = st.columns([0.32, 0.22, 0.46])
    period = period_col.selectbox("Période", stats_mod.PERIOD_OPTIONS, key="stats_period")
    media_filter = type_col.selectbox("Type", stats_mod.TYPE_OPTIONS, key="stats_type")
    all_genres = sorted(
        {genre for raw in df["genre"].astype(str) for genre in raw.split(" · ") if genre != "Inconnu"},
        key=str.casefold,
    )
    genre_choice = genre_col.selectbox("Genre", ["Tous"] + all_genres, key="stats_genre")

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
    if media_filter != "Tous":
        wanted = "Film" if media_filter == "Films" else "Épisode"
        filtered = filtered[filtered["type"] == wanted]
    filtered = stats_mod.apply_period(filtered, period, datetime.now(PARIS_TZ), custom_start, custom_end)
    if genre_choice != "Tous":
        filtered = filtered[filtered["genre"].str.contains(genre_choice, na=False)]

    period_label = period if period != "Période personnalisée" else f"Période personnalisée {custom_start} → {custom_end}"
    st.caption(f"🎯 Filtres appliqués : **{media_filter}** · **{genre_choice}** · **{period_label}** — {len(filtered)} visionnage(s).")

    # ── Acteurs & studios préférés — suit les slicers (période, type, genre) ──
    filtered_tmdb: set[str] = set()
    for ids in filtered.get("ids", []):
        if isinstance(ids, dict):
            value = ids.get("tmdb")
            if value not in (None, "", 0, "0"):
                filtered_tmdb.add(str(value))
    people_stats = _collect_people_stats(dataset, tmdb_whitelist=filtered_tmdb)
    studio_stats = _collect_studio_stats(dataset, tmdb_whitelist=filtered_tmdb)
    director_stats = _collect_director_stats(dataset, tmdb_whitelist=filtered_tmdb)
    st.divider()
    st.markdown("#### 🎬🎭 Tes réalisateurs, acteurs & studios préférés")
    if people_stats or studio_stats or director_stats:
        st.caption(
            "Détectés automatiquement sur la sélection filtrée ci-dessus "
            f"({period_label}). Clique sur une carte pour ouvrir la fiche TMDB."
        )
        if director_stats:
            st.markdown("**🎬 Réalisateurs récurrents**")
            st.markdown(_render_people_cards(director_stats, limit=10, fallback_emoji="🎬"), unsafe_allow_html=True)
        if people_stats:
            st.markdown("**🎭 Acteurs récurrents**")
            st.markdown(_render_people_cards(people_stats, limit=10), unsafe_allow_html=True)
        if studio_stats:
            st.markdown("**🏢 Studios récurrents**")
            st.markdown(_render_studio_chips(studio_stats, limit=12), unsafe_allow_html=True)
    else:
        st.caption(
            "Aucun acteur ou studio détecté sur cette sélection. "
            "Vérifie que la clé TMDB_API_KEY est renseignée dans les Secrets Streamlit."
        )

    # ── Historique des vues (filtré, UNE seule fois) ─────────────────────────
    with st.expander("📜 Historique des vues", expanded=False):
        st.caption(
            "Films et épisodes de la sélection filtrée ci-dessus, avec recherche et export CSV/JSON."
        )
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
        query = str(search or "").strip().casefold()
        visible = [
            row for row in rows
            if row.get("type") in (("Film", "Épisode") if media_filter == "Tous" else ("Film",) if media_filter == "Films" else ("Épisode",))
            and (not query or query in f"{row.get('title', '')} {row.get('episode_label', '')}".casefold())
            and (genre_choice == "Tous" or genre_choice in (row.get("genres") or []))
        ]
        # Appliquer la période sur les rows (via les dates)
        from history_engine import filter_history as _fh
        visible = _fh(
            rows,
            period=period,
            media_filter="Tous",
            genre_filter="Tous les genres",
            search=search,
            sort_mode="Plus récents d’abord",
            start_date=custom_start,
            end_date=custom_end,
            now=datetime.now(PARIS_TZ),
        )
        if media_filter != "Tous":
            wanted = "Film" if media_filter == "Films" else "Épisode"
            visible = [r for r in visible if r.get("type") == wanted]
        if genre_choice != "Tous":
            visible = [r for r in visible if genre_choice in (r.get("genres") or [])]

        total_plays = sum(int(row.get("plays") or 1) for row in visible)
        total_minutes = sum(int(row.get("total_minutes") or 0) for row in visible)
        st.markdown(
            _metric_cards([
                {"emoji": "📥", "k": "Entrées", "v": len(visible), "d": "dans l'export"},
                {"emoji": "🔁", "k": "Lectures connues", "v": total_plays, "d": "au total"},
                {"emoji": "⏱️", "k": "Temps estimé", "v": _format_minutes(total_minutes) if total_minutes else "—", "d": "de visionnage"},
            ]),
            unsafe_allow_html=True,
        )

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
            st.dataframe(table, width="stretch", hide_index=True)
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

    # ── Analyses détaillées (mêmes slicers) ──────────────────────────────────
    render_detailed_stats_page(filtered, period_label)


def _ruban(emoji: str, titre: str, meta: str, body: str, delay: int = 0) -> str:
    """Ruban déroulant (skin preview-look) : icône en tuile, titre, méta, chevron."""
    delay_css = f" style='animation-delay:{delay}ms'" if delay else ""
    return (
        f'<details class="msl-widget"{delay_css}><summary>'
        f'<span class="msl-ic">{emoji}</span>'
        f'<span class="msl-nm">{escape(titre)}<span class="msl-meta">{escape(meta)}</span></span>'
        f'<span class="msl-chev">▾</span></summary>'
        f'<div class="msl-body">{body}</div></details>'
    )


def _rythme_body(dash: dict[str, Any]) -> str:
    """Corps du ruban « Ton rythme de visionnage » (2 sous-cartes + digest)."""
    bilan = dash["bilan"]
    duree_mois = dashboard_mod._minutes_to_duree(int(bilan["heures"] * 60))
    gauche = [
        f"🗓️ <b>{escape(bilan['mois'])}</b> : <b>{escape(duree_mois)}</b> · "
        f"<b>{bilan['eps']}</b> épisode(s) · <b>{bilan['films']}</b> film(s)",
    ]
    if dash["eps_sem"]:
        rythme_txt = f"{dash['eps_sem']:.1f}".replace(".", ",")
        gauche.append(f"🏃 Ton rythme : <b>{escape(rythme_txt)} ép./semaine</b>")
    if dash["projection"]:
        p = dash["projection"]
        gauche.append(
            f"🏁 Au rythme actuel, tes <b>{dash['series_actives']} série(s) en cours</b> "
            f"({dash['reste_actives']} épisode(s) restant(s)) seront finies vers le "
            f"<b>{p.day} {dashboard_mod.MOIS_NOMS[p.month - 1]} {p.year}</b> "
            f"(hors nouvelles saisons… et nouvelles envies) 😉"
        )
        gauche.append('<div class="msl-note">🚫 Les séries abandonnées (statut « dropped ») sont exclues de ce calcul.</div>')
    elif dash["reste_actives"] > 0:
        gauche.append('<div class="msl-note">🏁 Regarde encore quelques épisodes et j’estimerai ta date de fin.</div>')
    else:
        gauche.append('<div class="msl-note">🏁 Aucune série en cours ou en pause : rien à projeter pour l’instant.</div>')

    c = dash["compteurs"]
    compteurs = (
        f'<div class="msl-stats2">'
        f'<div><div class="k">📺 Séries</div><div class="v">{escape(dashboard_mod._minutes_to_duree(int(c["h_series"] * 60)))}</div>'
        f'<div class="d">{c["nb_ep"]} épisodes</div></div>'
        f'<div><div class="k">🎬 Films</div><div class="v">{escape(dashboard_mod._minutes_to_duree(int(c["h_films"] * 60)))}</div>'
        f'<div class="d">{c["nb_films"]} films</div></div>'
        f'</div>'
    )

    digest = dash["digest"]
    digest_html = ""
    if digest["films"] or digest["eps"]:
        digest_html = (
            '<div class="msl-line">🍿 <b>Cette semaine</b> : '
            f'{digest["eps"]} épisode(s), {digest["films"]} film(s) — soit <b>'
            f'{escape(dashboard_mod._minutes_to_duree(digest["minutes"]))}</b> de visionnage.</div>'
        )

    gauche_html = "".join(f'<div class="msl-line">{l}</div>' for l in gauche)
    return (
        f'<div class="msl-grid2">'
        f'<div class="msl-subcard">{gauche_html}</div>'
        f'<div class="msl-subcard"><div class="k" style="margin-bottom:4px;">📼 Compteurs à vie</div>{compteurs}</div>'
        f'</div>{digest_html}'
    )


def _derniers_body(derniers: list[dict[str, Any]]) -> str:
    lignes = []
    for item in derniers:
        ep = f" · {escape(str(item.get('episode') or ''))}" if item.get("episode") else ""
        lignes.append(
            f'📅 <span class="muted">{escape(item["date"].strftime("%d/%m/%Y %H:%M"))}</span> · '
            f'{escape(str(item.get("type") or ""))} · <b>{escape(str(item["titre"]))}</b>{ep}'
        )
    return "".join(f'<div class="msl-line">{l}</div>' for l in lignes)


def _sorties_body(sorties: list[dict[str, Any]]) -> str:
    lignes = []
    for c in sorties:
        an = f" ({c.get('annee')})" if c.get("annee") else ""
        note_txt = f' · <span class="muted">⭐ {c.get("note", 0):.1f}/10</span>' if c.get("note") else ""
        jtxt = "aujourd'hui" if c.get("j") == 0 else f"dans {c.get('j')} j"
        lignes.append(
            f'🎬 <b>{escape(str(c.get("titre")))}</b>{escape(an)} · {jtxt} '
            f'({c["date"]:%d/%m}){note_txt}'
        )
    return "".join(f'<div class="msl-line">{l}</div>' for l in lignes)


def _plus_ancien_body(pa: dict[str, Any]) -> str:
    jours = pa.get("jours") or 0
    if jours >= 365:
        age = f"{jours // 365} an" + ("s" if jours >= 730 else "")
    else:
        age = f"{jours // 30} mois"
    an = f" ({pa.get('annee')})" if pa.get("annee") else ""
    return (
        f'<div class="msl-line">⏳ <b>{escape(str(pa.get("titre")))}</b>{escape(an)} '
        f'— ajouté il y a <b>{age}</b>. Encore envie de le voir ?</div>'
    )


def _pause_body(pause: list[dict[str, Any]]) -> str:
    lignes = []
    for c in pause:
        an = f" ({c.get('annee')})" if c.get("annee") else ""
        ans = (c.get("jours") or 0) // 365
        pl = "s" if ans > 1 else ""
        note_txt = f' · <span class="muted">⭐ {c.get("pub", 0):.1f}/10</span>' if c.get("pub") else ""
        lignes.append(
            f'🚦 <b>{escape(str(c.get("titre")))}</b>{escape(an)} — dernier épisode vu il y a '
            f'<b>{ans} an{pl}</b>{note_txt}'
        )
    return "".join(f'<div class="msl-line">{l}</div>' for l in lignes)


def _records_body(rec: dict[str, Any]) -> str:
    j = rec["jour"]
    counts = j.get("counts") or {}
    top_key = max(counts, key=counts.get) if counts else None
    top_titre = (j.get("shows") or {}).get(top_key)
    extra = f" — surtout <b>{escape(str(top_titre))}</b>" if top_titre else ""
    m = rec["mois"]
    mois_nom = dashboard_mod.MOIS_NOMS[m["key"][1] - 1]
    s = rec["serie"]
    return (
        '<div class="msl-grid3">'
        f'<div class="msl-subcard"><div class="k">📅 Jour record</div><div class="v">{j["nb"]} ép.</div>'
        f'<div class="d">{j["date"]:%d/%m/%Y}{extra}</div></div>'
        f'<div class="msl-subcard"><div class="k">🗓️ Mois record</div><div class="v">{m["nb"]} ép.</div>'
        f'<div class="d">{mois_nom} {m["key"][0]}</div></div>'
        f'<div class="msl-subcard"><div class="k">📺 Série avalée</div>'
        f'<div class="v">{escape(dashboard_mod._minutes_to_duree(int(s.get("min", 0))))}</div>'
        f'<div class="d">{escape(str(s.get("titre")))} · {s.get("nb")} ép.</div></div>'
        '</div>'
    )


def _creneau_body(cr: dict[str, Any]) -> str:
    items = cr.get("items") or []
    HORAIRES = {"Matin": "6 h → 12 h", "Après-midi": "12 h → 18 h", "Soir": "18 h → 22 h", "Nuit": "22 h → 6 h"}
    COULEURS = {"Matin": "#00201C", "Après-midi": "#00524B", "Soir": "#00A392", "Nuit": "#007C6E"}
    segments = []
    cases = []
    for it in items:
        pct = it["pct"]
        # Barre colorée (4 segments distincts, lisible d'un coup d'œil).
        segments.append(
            f'<span style="width:{pct:.0f}%; background:{COULEURS.get(it["label"], "#00A392")};"></span>'
        )
        # Étiquette grande + horaires affichés directement (plus d'info-bulle).
        plage = HORAIRES.get(it["label"], "")
        pl = f'<div class="pl">{escape(plage)}</div>' if plage else ""
        cases.append(
            f'<div class="msl-creneau">'
            f'<div class="lb">{it["emoji"]} {escape(it["label"])}</div>'
            f'{pl}'
            f'<div class="v">{pct:.0f}%</div>'
            f'<div class="d">{escape(dashboard_mod._minutes_to_duree(int(it["min"])))}</div></div>'
        )
    top = cr.get("top") or {}
    top_txt = (
        f'<div class="msl-note">🏆 Ton moment préféré : {top["emoji"]} <b>{escape(top["label"])}</b> '
        f'({top["pct"]:.0f}% de ton temps).</div>'
        if top else ""
    )
    return (
        f'<div class="msl-bar">{"".join(segments)}</div>'
        f'<div class="msl-legend">{"".join(cases)}</div>{top_txt}'
    )


def _coups_body(coups: list[dict[str, Any]]) -> str:
    items = []
    for c in coups:
        ic = "🎬" if c.get("type") == "Film" else "📺"
        an = f" ({c.get('annee')})" if c.get("annee") else ""
        src_txt = " (communauté)" if c.get("fallback") else ""
        items.append(
            f'<div class="msl-coup"><div class="emoji">{ic}</div>'
            f'<div class="t">{escape(str(c.get("titre")))}{escape(an)}</div>'
            f'<div class="s">⭐ {c.get("note", 0):.1f}/10{escape(src_txt)}</div></div>'
        )
    return f'<div class="msl-cols">{"".join(items)}</div>'


def _contre_courant_body(cc: dict[str, Any]) -> str:
    sev = cc.get("severite")
    if not sev:
        return (
            f'<div class="msl-line">Aucun écart notable : tes notes suivent sagement celles du public '
            f'({cc.get("nb", 0)} contenus comparés). 🤝</div>'
        )
    top = cc.get("ecarts") or []
    jauge = max(0.0, min(1.0, (sev["moy"] + 3) / 6))
    lignes = [
        f'🌡️ <b>Thermomètre de sévérité</b> — sur <b>{cc.get("nb", 0)}</b> contenus notés, tu es : '
        f'<span style="color:{sev["couleur"]}; font-weight:800;">{sev["emoji"]} {sev["label"]}</span> '
        f'(écart moyen <b>{sev["moy"]:+.1f} pt /10</b>, {sev["txt"]}).',
    ]
    barre = (
        f'<div class="msl-bar jauge"><span style="width:{jauge * 100:.0f}%;"></span></div>'
        '<div class="msl-legend2">😈 Très sévère · 😠 Plutôt sévère · 🎯 Moyenne · 🙂 Plutôt indulgent · 😇 Très indulgent</div>'
    )
    for c in top:
        ic = "🎬" if c.get("type") == "Film" else "📺"
        an = f" ({c.get('annee')})" if c.get("annee") else ""
        sens = "💎 Tu as adoré ce que le public a boudé" if c.get("ecart", 0) > 0 else "🙃 Tu as boudé ce que le public a adoré"
        lignes.append(
            f'{ic} <b>{escape(str(c.get("titre")))}</b>{escape(an)} — Toi <b>{c.get("note", 0):.1f}/10</b> · '
            f'Public <b>{c.get("pub", 0):.1f}/10</b> · écart <b>{c.get("ecart", 0):+.1f}</b><br>'
            f'<span class="muted">{sens}</span>'
        )
    return "".join(f'<div class="msl-line">{l}</div>' for l in lignes) + barre


def _rewatch_body(rewatch: list[dict[str, Any]]) -> str:
    lignes = []
    for c in rewatch:
        an = f" ({c.get('annee')})" if c.get("annee") else ""
        pl = "s" if c.get("ans", 1) > 1 else ""
        lignes.append(
            f'🔁 <b>{escape(str(c.get("titre")))}</b>{escape(an)} · il y a <b>{c.get("ans")} an{pl}</b> · '
            f'<span class="muted">⭐ {c.get("note", 0):.1f}/10</span>'
        )
    return "".join(f'<div class="msl-line">{l}</div>' for l in lignes)


def _metric_cards(cards: list[dict[str, Any]], start_delay: int = 0) -> str:
    """Bandeau de métriques moderne (skin V53) : cartes k/v/d avec icône,
    fondu en cascade, surbrillance au survol. Utilisé sur le tableau de
    bord, En cours de lecture, Statistiques et Migration."""
    out = []
    delay = start_delay
    for card in cards:
        emoji = str(card.get("emoji") or "")
        k = escape(str(card.get("k") or ""))
        v = escape(str(card.get("v") if card.get("v") is not None else "—"))
        d = escape(str(card.get("d") or ""))
        out.append(
            f'<div class="msl-mcard" style="animation-delay:{delay}ms">'
            f'<span class="ic">{emoji}</span>'
            f'<div class="k">{k}</div>'
            f'<div class="v">{v}</div>'
            f'<div class="d">{d}</div></div>'
        )
        delay += 40
    return f'<div class="msl-metrics">{"".join(out)}</div>'


def render_dashboard_widgets() -> None:
    """Widgets du tableau de bord en rubans déroulants (skin preview-look) :
    rythme, derniers visionnages, sorties, plus ancien, pauses longues,
    records, créneau, coups de cœur, à contre-courant, rewatch radar.
    0 appel API : tout est calculé sur les données déjà chargées."""
    dataset = _dataset()
    if not dataset:
        return
    dash = dashboard_mod.compute_dashboard(dataset, timezone_name="Europe/Paris")
    if dash.get("empty"):
        return
    w = dashboard_mod.compute_widgets(dataset, timezone_name="Europe/Paris")

    rubans: list[str] = []
    delay = 0

    rubans.append(
        _ruban("⏱️", "Ton rythme de visionnage",
               "récap du mois · épisodes/semaine · date de fin projetée",
               _rythme_body(dash), delay)
    )
    delay += 50

    if dash.get("derniers"):
        rubans.append(
            _ruban("🕘", "Derniers visionnages",
                   f"les {len(dash['derniers'])} derniers films et épisodes regardés",
                   _derniers_body(dash["derniers"]), delay)
        )
        delay += 50

    if w.get("sorties"):
        rubans.append(
            _ruban("📅", f"Sorties de la semaine ({len(w['sorties'])})",
                   "des films de tes listes qui sortent dans les 7 prochains jours",
                   _sorties_body(w["sorties"]), delay)
        )
        delay += 50

    pa = w.get("plus_ancien")
    if pa:
        rubans.append(
            _ruban("⏳", "Le plus ancien de ta Watchlist",
                   "le contenu ajouté depuis le plus longtemps",
                   _plus_ancien_body(pa), delay)
        )
        delay += 50

    if w.get("pause_longue"):
        rubans.append(
            _ruban("🚦", f"Séries en pause longue ({len(w['pause_longue'])})",
                   "2 ans+ sans épisode, alors qu'il reste des épisodes à voir",
                   _pause_body(w["pause_longue"]), delay)
        )
        delay += 50

    if w.get("records"):
        rubans.append(
            _ruban("🔥", "Tes records de binge",
                   "jour record · mois record · série la plus avalée",
                   _records_body(w["records"]), delay)
        )
        delay += 50

    if w.get("creneau"):
        rubans.append(
            _ruban("🕰️", "Ton créneau préféré",
                   "où regardes-tu le plus ? (horaires affichés sous chaque créneau)",
                   _creneau_body(w["creneau"]), delay)
        )
        delay += 50

    if w.get("coups_de_coeur"):
        rubans.append(
            _ruban("⭐", f"Mes coups de cœur ({len(w['coups_de_coeur'])})",
                   "tes contenus notés 9/10 ou plus — de bons candidats à revoir",
                   _coups_body(w["coups_de_coeur"]), delay)
        )
        delay += 50

    cc = w.get("contre_courant") or {}
    if cc.get("severite") or cc.get("nb"):
        label = "À contre-courant"
        if cc.get("severite"):
            label += f" {cc['severite']['emoji']}"
        top_nb = len(cc.get("ecarts") or [])
        meta = "thermomètre : tes notes vs le public" + (f" · {top_nb} écart(s) notable(s)" if top_nb else "")
        rubans.append(_ruban("🧭", label, meta, _contre_courant_body(cc), delay))
        delay += 50

    if w.get("rewatch"):
        rubans.append(
            _ruban("🔁", f"Rewatch radar ({len(w['rewatch'])})",
                   "vus une seule fois il y a 3 ans+, très bien notés",
                   _rewatch_body(w["rewatch"]), delay)
        )
        delay += 50

    if rubans:
        st.markdown("\n".join(rubans), unsafe_allow_html=True)



def pending_source_now() -> bool:
    return bool(st.session_state.get("pending_source"))


def _handle_source_action(action: str) -> None:
    """Actions de la barre de statut : changer de source ou se déconnecter."""
    if action == "_action_switch_zip":
        # Ouvre l'écran d'import ZIP Trakt (sans toucher aux données actuelles).
        st.session_state["pending_source"] = "trakt_zip"
        st.rerun()
    elif action == "_action_switch_mdblist":
        # Revenir à MDBList : retire les données affichées puis charge le compte.
        st.session_state.pop("_normalized_dataset", None)
        st.session_state.pop("_source_genre_cache", None)
        st.session_state.pop("_mdblist_playback_poster_cache", None)
        st.session_state["pending_source"] = "mdblist"
        st.rerun()
    elif action == "_action_disconnect":
        mdb_oauth.disconnect(cookies)
        try:
            cookies.remove("msl_mdblist_data_loaded")
        except Exception:
            pass
        for key in (
            "_normalized_dataset",
            "_source_genre_cache",
            "_mdblist_now_playing_live",
            "_mdblist_playback_poster_cache",
            "_mdblist_calendar_cache",
        ):
            st.session_state.pop(key, None)
        st.session_state.pop("pending_source", None)
        st.rerun()


def _render_source_status(connected: bool, has_data: bool, source: str) -> None:
    """Barre compacte : source active + compte connecté + switch + déconnexion.

    Remplace l'ancien grand bandeau « bienvenue / choisir une source » : une
    fois connecté (ou des données chargées), on ne montre plus qu'une ligne
    discrète avec les actions utiles.
    """
    badges = []
    if connected:
        account = mdb_oauth.account_summary() or {}
        badges.append(
            f'<span class="source-badge">✓ {escape(str(account.get("username") or "MDBList"))}</span>'
        )
    if has_data:
        if source == "trakt_zip":
            badges.append('<span class="source-badge">🟢 TRAKT ZIP · LECTURE SEULE</span>')
        else:
            badges.append('<span class="source-badge">🔵 MDBLIST · TEMPS RÉEL</span>')
    else:
        badges.append('<span class="source-badge" style="opacity:.6;">⏳ AUCUNE DONNÉE</span>')

    badge_col, action_col = st.columns([0.62, 0.38])
    with badge_col:
        st.markdown(
            '<div style="display:flex;flex-wrap:wrap;gap:.45rem;align-items:center;'
            'min-height:2.75rem;">' + "".join(badges) + '</div>',
            unsafe_allow_html=True,
        )

    actions: list[tuple[str, str]] = []
    if connected:
        if has_data and source == "trakt_zip":
            actions.append(("🔵 Revenir à MDBList", "_action_switch_mdblist"))
        else:
            actions.append(("📦 Utiliser un ZIP Trakt", "_action_switch_zip"))
        actions.append(("🔌 Se déconnecter", "_action_disconnect"))
    elif has_data and source == "trakt_zip":
        actions.append(("🔵 Connecter MDBList", "_action_switch_mdblist"))

    with action_col:
        if actions:
            cols = st.columns(len(actions))
            for index, (label, key) in enumerate(actions):
                with cols[index]:
                    if st.button(label, key=key, type="primary", use_container_width=True):
                        _handle_source_action(key)


def _render_welcome_cards() -> None:
    """Écran d'accueil : deux cartes claires pour choisir sa source de données."""
    st.markdown(
        '<div class="accent-callout"><strong>👋 BIENVENUE</strong> · '
        'Choisis <strong>une source de données</strong> pour commencer : '
        '🔵 MDBList (en direct) ou 🟢 ton export ZIP Trakt (lecture seule). '
        'Tu pourras changer de source à tout moment.</div>',
        unsafe_allow_html=True,
    )
    mdb_col, zip_col = st.columns(2, gap="large")
    with mdb_col:
        st.markdown(
            """
            <div class="source-card">
                <span class="source-badge">🔵 EN DIRECT · LECTURE/ÉCRITURE</span>
                <h3>🔗 Connecter MDBList</h3>
                <p>Historique, Watchlist, notes, listes, progression et statistiques,
                synchronisés avec ton compte. <strong>Recommandé</strong> si tu utilises MDBList.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("🔗 Connecter MDBList", type="primary", key="choose_mdblist", use_container_width=True):
            st.session_state["pending_source"] = "mdblist"
            st.rerun()
    with zip_col:
        st.markdown(
            """
            <div class="source-card">
                <span class="source-badge">🟢 IMPORT LOCAL · LECTURE SEULE</span>
                <h3>📦 Importer un ZIP Trakt</h3>
                <p>Ton export Trakt complet (historique, rewatches, Watchlist, notes,
                listes) en lecture seule : parfait pour faire le ménage ou préparer
                une migration vers MDBList.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("📦 Importer un ZIP Trakt", type="primary", key="choose_zip", use_container_width=True):
            st.session_state["pending_source"] = "trakt_zip"
            st.rerun()
    st.caption(
        "💡 Sur mobile, les deux cartes s'affichent l'une sous l'autre : "
        "il suffit d'en choisir une. Les données affichées correspondent "
        "toujours à la source choisie (badge en haut de page)."
    )


def _render_zip_import_screen() -> None:
    """Écran dédié d'import ZIP Trakt (lecture seule)."""
    st.markdown('<div class="page-title">📦 Import ZIP Trakt</div>', unsafe_allow_html=True)
    st.caption(
        "Dépose ton export ZIP Trakt ci-dessous. "
        "Lecture seule, aucune écriture sur aucun compte. Les protections ZIP sont actives."
    )
    with st.expander("❓ Comment obtenir mon ZIP Trakt ? (guide pas à pas)", expanded=False):
        st.markdown(
            """
            <div class="guide-step"><strong>1 · OBTENIR L'EXPORT</strong> — Va sur
            <a href="https://app.trakt.tv/settings/data?mode=media" target="_blank" rel="noopener noreferrer">app.trakt.tv/settings/data?mode=media</a>
            et connecte-toi avec ton compte Trakt.</div>
            <div class="guide-step"><strong>2 · EXPORTER</strong> — Scrolle jusqu'à la section
            « Export » puis clique sur « Exporter maintenant ».</div>
            <div class="guide-step"><strong>3 · ATTENDRE</strong> — Trakt prépare ton export :
            ça peut prendre quelques minutes.</div>
            <div class="guide-step"><strong>4 · TÉLÉCHARGER</strong> — Une fois prêt, Trakt te
            donne un lien de téléchargement (<code>export-trakt-*.zip</code>).</div>
            <div class="guide-step"><strong>5 · IMPORTER ICI</strong> — Reviens sur cette page,
            dépose le ZIP ci-dessous puis clique sur « 📥 Importer et charger mes données ».</div>
            <div class="accent-callout"><strong>🔒 LECTURE SEULE</strong> ·
            Tes données Trakt ne sont jamais modifiées, et le ZIP n'est pas conservé après la session.</div>
            """,
            unsafe_allow_html=True,
        )
    zip_file = st.file_uploader("Choisis le fichier ZIP Trakt", type=["zip"], key="trakt_zip_uploader")
    if zip_file is not None:
        st.caption(f"Fichier : **{zip_file.name}** · {zip_file.size // 1024} Ko")
        if st.button("📥 Importer et charger mes données", type="primary", key="import_trakt_zip"):
            with st.spinner("Analyse sécurisée du ZIP Trakt…"):
                try:
                    raw_bytes = zip_file.getvalue()
                    data = trakt_zip_provider.load_trakt_zip(raw_bytes)
                except trakt_zip_provider.TraktZipError as exc:
                    st.error(f"Import impossible : {exc}")
                    data = None
                except Exception as exc:
                    st.error(f"Erreur inattendue pendant l'analyse : {exc}")
                    data = None
            if data:
                st.session_state["_normalized_dataset"] = data
                st.session_state.pop("_source_genre_cache", None)
                st.session_state.pop("_mdblist_playback_poster_cache", None)
                counts = trakt_zip_provider.summarize(data)
                enrich_msg = ""
                if mdb_oauth.is_connected():
                    with st.spinner("Enrichissement automatique avec MDBList…"):
                        ok_enrich, enrich_msg = _enrich_zip_dataset()
                    if not ok_enrich:
                        enrich_msg = f" (enrichissement : {enrich_msg})"
                st.markdown(
                    f'<div class="accent-callout"><strong>✓ ZIP TRAKT IMPORTÉ</strong> · '
                    f'{counts["films_vus"]} film(s) vu(s) · {counts["episodes_vus"]} épisode(s) vu(s) · '
                    f'{counts["series_vues"]} série(s) · {counts["notes"]} note(s) · '
                    f'{counts["watchlist"]} contenu(s) en watchlist · {counts["listes"]} liste(s).'
                    f'{enrich_msg}</div>',
                    unsafe_allow_html=True,
                )
                st.session_state.pop("pending_source", None)
                st.rerun()
    if st.button("← Annuler et revenir au tableau de bord", type="primary", key="cancel_zip_import"):
        st.session_state.pop("pending_source", None)
        st.rerun()


def page_dashboard() -> None:
    st.markdown('<div class="page-title">🏠 Tableau de bord</div>', unsafe_allow_html=True)

    loaded = _dataset()
    has_data = bool(loaded and isinstance(loaded, dict) and loaded.get("sections"))
    source = str(loaded.get("source") or "mdblist") if has_data else "none"
    connected = mdb_oauth.is_connected()

    # ── Auto-chargement : connecté + aucune donnée → on charge tout seul.
    # Le cache d'une heure (st.cache_data) évite de rejouer les appels API
    # après un F5 : le rechargement est alors instantané, sans toucher au
    # quota MDBList (limite ~1000 appels/jour).

    # ── Écrans dédiés de connexion / import (quand une action est en attente).
    pending = st.session_state.get("pending_source")
    if pending == "mdblist" and not connected:
        st.markdown('<div class="page-title">🔐 Connexion MDBList</div>', unsafe_allow_html=True)
        render_mdblist_connector()
        if st.button("← Retour au tableau de bord", type="primary", key="cancel_mdblist_login"):
            st.session_state.pop("pending_source", None)
            st.rerun()
        return
    if pending == "trakt_zip":
        _render_zip_import_screen()
        return
    if pending == "mdblist" and connected:
        # Déjà connecté : on nettoie simplement le marqueur d'action.
        st.session_state.pop("pending_source", None)

    # ── Barre de statut compacte (source + switch + déconnexion).
    if connected or has_data:
        _render_source_status(connected, has_data, source)

    # ── Écran d'accueil : uniquement quand rien n'est choisi ni chargé.
    if not has_data and not connected:
        _render_welcome_cards()
        return

    # ── Connecté à MDBList, données pas encore chargées → chargement auto.
    if not has_data and connected:
        if not st.session_state.get("_auto_load_done"):
            st.session_state["_auto_load_done"] = True
            try:
                # Sert le cache st.cache_data : 0 appel API après un F5 à chaud.
                # Spinner visible uniquement lors du premier chargement (lourd).
                with st.spinner("Chargement et enrichissement de vos données (acteurs, studios)…"):
                    load_mdblist_dataset()
            except Exception:
                pass
            st.rerun()
        # L'auto-chargement a déjà été tenté (échec) : bouton manuel de secours.
        st.divider()
        st.markdown('<div class="page-title">📥 Charger mes données MDBList</div>', unsafe_allow_html=True)
        render_data_loader()
        st.markdown(
            '<div class="accent-callout"><strong>PAS ENCORE CHARGÉ</strong> · '
            'Clique « Charger mes données MDBList » ci-dessus pour afficher '
            'ton analyse (films, séries, statistiques…).</div>',
            unsafe_allow_html=True,
        )
        return

    # ── Données ZIP Trakt affichées ──────────────────────────────────────────
    if source == "trakt_zip":
        st.divider()
        st.markdown('<div class="page-title">📥 Vos données Trakt (import ZIP)</div>', unsafe_allow_html=True)
        st.caption("Lecture seule · aucune écriture. Toutes les pages utilisent ces données.")
        if st.button("🚪 Quitter les données ZIP Trakt", type="primary", key="leave_zip_data"):
            st.session_state.pop("_normalized_dataset", None)
            st.session_state.pop("_source_genre_cache", None)
            st.session_state.pop("_mdblist_playback_poster_cache", None)
            st.rerun()
        if connected:
            st.caption("Connecté à MDBList (lecture seule) : enrichis ces données avec les métadonnées MDBList.")
            st.caption("Quelques appels groupés (200 identifiants max par appel). Aucune écriture.")
            if st.button(
                "✨ Enrichir avec MDBList (genres, posters, durées, notes)",
                type="primary",
                key="enrich_zip",
                use_container_width=True,
            ):
                with st.spinner("Fusion des métadonnées MDBList…"):
                    ok, message = _enrich_zip_dataset()
                st.caption(("✓ " if ok else "⚠️ ") + message)
                if ok:
                    st.rerun()
        else:
            st.caption(
                "Connecte MDBList (lecture seule) puis clique « Enrichir » : "
                "genres, posters, durées et notes apparaîtront."
            )
        render_dataset_overview()
        render_dashboard_widgets()
        return

    # ── Données MDBList affichées ────────────────────────────────────────────
    st.divider()
    st.markdown('<div class="page-title">📥 Vos données MDBList</div>', unsafe_allow_html=True)
    render_data_loader()
    # Compte/quota replié (discret) : disponible sans encombrer l'écran.
    with st.expander("🎫 Compte MDBList & quota", expanded=False):
        try:
            _render_connected_mdblist()
        except Exception:
            pass
    render_dataset_overview()
    render_dashboard_widgets()
    # Actualisation discrète, en bas de page : uniquement quand les données
    # sont déjà chargées (pas d'appel API involontaire en haut de page).
    st.divider()
    st.caption(
        "🔄 « Actualiser MDBList » recharge tes données depuis l'API (quota ~1000 appels/jour). "
        "Les données TMDB (acteurs, studios) sont mémorisées 30 jours par contenu et se mettent "
        "à jour toutes seules sur tes nouveautés. « Actualiser acteurs & studios » force une mise "
        "à jour TMDB complète (≈30 s, facultatif) si tu veux des données fraîches entre deux rafraîchissements."
    )
    _refresh_m, _refresh_t = st.columns(2)
    with _refresh_m:
        if st.button("🔄 Actualiser les données MDBList", type="primary", key="refresh_mdblist_bottom", use_container_width=True):
            with st.spinner("Actualisation MDBList…"):
                _load_mdblist_cached.clear()
                load_mdblist_dataset()
            st.rerun()
    with _refresh_t:
        # Bouton FACULTATIF : force un re-fetch TMDB complet (acteurs + studios).
        # N'apparaît que si une clé TMDB est configurée. Vide le cache TMDB par
        # contenu (30 j) puis recharge : tous les titres sont ré-interrogés.
        if _tmdb_api_key() and st.button(
            "🎭 Actualiser acteurs & studios (TMDB)",
            type="primary", key="refresh_tmdb_bottom", use_container_width=True,
        ):
            with st.spinner("Actualisation des données TMDB (acteurs, studios)… ≈30 s"):
                _fetch_tmdb_item.clear()
                _load_mdblist_cached.clear()
                load_mdblist_dataset()
            st.rerun()


def render_migration_page() -> None:
    """📦 Migration ZIP Trakt → MDBList — assistant web sécurisé.

    Étapes : déposer le ZIP → aperçu (quantités + sans correspondance) →
    choix des sections → sauvegarde JSON → confirmation → écriture par lots
    → rapport Excel. Mode simulation (dry-run) disponible : aucun POST.
    """
    st.markdown('<div class="page-title">📦 Migration Trakt → MDBList</div>', unsafe_allow_html=True)
    st.caption(
        "Importe tes données d'un export ZIP Trakt vers ton compte MDBList : "
        "historique (avec les vraies dates), notes, Watchlist et listes. "
        "Écritures par lots, avec aperçu, sauvegarde et confirmation — "
        "rien n'est écrit sans ton accord."
    )

    if not mdb_oauth.is_connected():
        st.markdown(
            '<div class="accent-callout"><strong>CONNEXION NÉCESSAIRE</strong> · '
            'Connecte MDBList depuis le Tableau de bord avant de migrer (les écritures '
            'se font sur ton compte MDBList).</div>',
            unsafe_allow_html=True,
        )
        return

    # ── Étape 1 : déposer le ZIP ──
    st.divider()
    st.markdown("#### 1 · Déposer ton export ZIP Trakt")
    zip_file = st.file_uploader(
        "Choisis le fichier ZIP Trakt (Settings → Your data → Export)",
        type=["zip"],
        key="migration_zip",
    )
    if zip_file is None:
        st.info("Dépose ton ZIP pour commencer. Rien n'est écrit tant que tu n'as pas confirmé.")
        return
    st.caption(f"Fichier : **{zip_file.name}** · {zip_file.size // 1024} Ko")

    # Analyser le ZIP (lecture seule, comme l'import local)
    try:
        raw_bytes = zip_file.getvalue()
        dataset = trakt_zip_provider.load_trakt_zip(raw_bytes)
    except trakt_zip_provider.TraktZipError as exc:
        st.error(f"Import impossible : {exc}")
        return
    except Exception as exc:
        st.error(f"Erreur pendant l'analyse : {exc}")
        return

    plan = mig_mod.build_migration_plan(dataset)

    # ── Étape 2 : aperçu ──
    st.divider()
    st.markdown("#### 2 · Aperçu de ce qui sera migré")
    st.markdown(
        _metric_cards([
            {"emoji": "🎬", "k": "Films vus", "v": plan["films_vus"], "d": "à migrer"},
            {"emoji": "📺", "k": "Épisodes vus", "v": plan["episodes_vus"], "d": "à migrer"},
            {"emoji": "🗂️", "k": "Séries concernées", "v": plan["series_vues"], "d": "séries touchées"},
            {"emoji": "⚠️", "k": "Sans correspondance", "v": len(plan["sans_correspondance"]), "d": "exclus de la migration"},
        ]),
        unsafe_allow_html=True,
    )
    if plan["rewatches"]:
        st.caption(f"🔁 {plan['rewatches']} rewatch(es) détecté(s) : MDBList ne conserve que la dernière date par contenu.")
    if plan["sans_correspondance"]:
        with st.expander(f"⚠️ Contenus sans correspondance ({len(plan['sans_correspondance'])})"):
            st.caption("Ces contenus n'ont pas d'identifiant TMDb/IMDb utilisable par MDBList : ils ne seront pas migrés.")
            for item in plan["sans_correspondance"][:100]:
                st.markdown(f"- {escape(str(item.get('type')))} : **{escape(str(item.get('title')))}** ({item.get('year') or '?'})")

    # Choix des sections
    st.markdown("##### Sections à migrer")
    do_history = st.checkbox("📜 Historique (films + épisodes avec dates)", value=True, key="mig_hist")
    do_ratings = st.checkbox("⭐ Notes", value=True, key="mig_ratings")
    do_watchlist = st.checkbox("📌 Watchlist", value=True, key="mig_wl")
    do_lists = st.checkbox("🗂️ Listes (créées si absentes)", value=True, key="mig_lists")

    # Mode simulation
    st.markdown("##### Mode")
    simu = st.radio(
        "Mode d'exécution",
        ["Simulation (dry-run, aucun POST)", "Écriture réelle"],
        index=0,
        key="mig_mode",
        help="En simulation, le rapport est généré mais RIEN n'est écrit sur MDBList.",
    )

    # ── Étape 3 : sauvegarde + rapport d'aperçu ──
    st.divider()
    st.markdown("#### 3 · Sauvegarde de sécurité & rapport")
    backup_payload = {
        "action": "migration_trakt_to_mdblist",
        "export_date": datetime.now(PARIS_TZ).isoformat(),
        "plan": {
            "films_vus": plan["films_vus"],
            "episodes_vus": plan["episodes_vus"],
            "sans_correspondance": plan["sans_correspondance"][:500],
        },
        "dataset": dataset,
    }
    st.download_button(
        "💾 Télécharger la sauvegarde de sécurité (JSON)",
        data=json.dumps(backup_payload, ensure_ascii=False, default=str, indent=2),
        file_name=f"migration-sauvegarde-{datetime.now(PARIS_TZ).strftime('%Y%m%d-%H%M%S')}.json",
        mime="application/json",
        key="migration_backup",
        type="primary",
    )
    st.download_button(
        "📊 Télécharger le rapport Excel (aperçu)",
        data=mig_mod.generate_migration_report(plan),
        file_name=f"migration-rapport-{datetime.now(PARIS_TZ).strftime('%Y%m%d-%H%M%S')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="migration_report",
        type="primary",
    )

    # ── Étape 4 : confirmation + exécution ──
    st.divider()
    st.markdown("#### 4 · Confirmation et exécution")
    confirm = st.checkbox(
        "✅ Je confirme : je veux exécuter la migration selon les sections cochées "
        "(réversible via la sauvegarde, par lots)",
        key="mig_confirm",
    )
    if confirm:
        if st.button("🚀 Exécuter la migration", type="primary", key="mig_go"):
            results: dict[str, Any] = {"watched_movies_ok": 0, "watched_episodes_ok": 0,
                                       "errors": 0, "errors_list": []}
            if simu.startswith("Simulation"):
                results = {"watched_movies_ok": plan["films_vus"], "watched_episodes_ok": plan["episodes_vus"],
                           "errors": 0, "errors_list": [], "simulated": True}
                st.markdown(
                    '<div class="accent-callout"><strong>✅ SIMULATION TERMINÉE</strong> · '
                    "Aucune écriture n'a été faite. Télécharge le rapport ci-dessus " 
                    'pour voir ce qui aurait été migré.</div>',
                    unsafe_allow_html=True,
                )
            else:
                with st.spinner("Écriture par lots sur MDBList…"):
                    try:
                        provider = MDBListProvider(mdb_oauth.access_token())
                        # Historique (par lots de 100)
                        if do_history:
                            payloads = mig_mod.build_watched_payloads(plan)
                            for i in range(0, len(payloads["movies"]), 100):
                                chunk = payloads["movies"][i:i + 100]
                                try:
                                    provider.raw_post("/sync/watched", {"movies": chunk})
                                    results["watched_movies_ok"] += len(chunk)
                                except Exception as exc:
                                    results["errors"] += len(chunk)
                                    results["errors_list"].append({"section": "watched_movies", "detail": str(exc)})
                            for i in range(0, len(payloads["shows"]), 100):
                                chunk = payloads["shows"][i:i + 100]
                                try:
                                    provider.raw_post("/sync/watched", {"shows": chunk})
                                    results["watched_episodes_ok"] += sum(len(s["seasons"]) for s in chunk)
                                except Exception as exc:
                                    results["errors"] += 1
                                    results["errors_list"].append({"section": "watched_shows", "detail": str(exc)})
                        # Notes
                        if do_ratings:
                            rat = mig_mod.build_ratings_payloads(plan, dataset)
                            try:
                                provider.raw_post("/sync/ratings", rat)
                            except Exception as exc:
                                results["errors"] += 1
                                results["errors_list"].append({"section": "ratings", "detail": str(exc)})
                        # Watchlist
                        if do_watchlist:
                            wl = mig_mod.build_watchlist_payloads(dataset)
                            try:
                                provider.add_watchlist_items(movies=wl["movies"], shows=wl["shows"])
                            except Exception as exc:
                                results["errors"] += 1
                                results["errors_list"].append({"section": "watchlist", "detail": str(exc)})
                        # Listes
                        if do_lists:
                            for lplan in mig_mod.build_lists_plans(dataset):
                                try:
                                    resp = provider.create_list(lplan["name"])
                                    list_id = (resp.get("id") if isinstance(resp, dict) else None)
                                    if list_id:
                                        provider.add_list_items(int(list_id), movies=lplan["movies"], shows=lplan["shows"])
                                    else:
                                        results["errors_list"].append({"section": "list_create", "detail": f"liste {lplan['name']} : pas d'id retourné"})
                                except Exception as exc:
                                    results["errors"] += 1
                                    results["errors_list"].append({"section": "list", "detail": str(exc)})
                    except Exception as exc:
                        st.error(f"Échec de la migration : {exc}")
                st.markdown(
                    f'<div class="accent-callout"><strong>✅ MIGRATION TERMINÉE</strong> · '
                    f'{results["watched_movies_ok"]} films · {results["watched_episodes_ok"]} épisodes '
                    f'· {results["errors"]} erreur(s). Télécharge le rapport final ci-dessous.</div>',
                    unsafe_allow_html=True,
                )
                st.download_button(
                    "📊 Télécharger le rapport Excel final",
                    data=mig_mod.generate_migration_report(plan, results),
                    file_name=f"migration-rapport-final-{datetime.now(PARIS_TZ).strftime('%Y%m%d-%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="migration_report_final",
                    type="primary",
                )


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
            <div style="font-size:1em; color:#FFE100; text-transform:uppercase; letter-spacing:3px; font-weight:700;">
                TON ANNÉE {annee}</div>
            <div style="font-size:3.2em; font-weight:900; color:#fff; margin:10px 0;">
                {wrapped_mod.format_duree_fr(int(round(d['total_h'] * 60)))}</div>
            <div style="font-size:1.1em; color:#9DC5BF;">de visionnage cette année</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    wrapped_cards = [
        {"emoji": "🎬", "k": "Films uniques", "v": d["films"], "d": "vus cette année"},
        {"emoji": "📺", "k": "Séries suivies", "v": d["series"], "d": "cette année"},
        {"emoji": "🎞️", "k": "Épisodes", "v": d["episodes"], "d": "vus cette année"},
        {"emoji": "⭐", "k": "Note moyenne", "v": f"{d['note_moy']:.1f}/10" if d["note_moy"] else "—", "d": "sur tes notes"},
        {"emoji": "🏆", "k": "Record en 1 jour",
         "v": f"{d['nb_peak']} visionnages" if d["jour_peak"] is not None else "—",
         "d": d["jour_peak"].strftime("%d/%m") if d["jour_peak"] is not None else ""},
        {"emoji": "📅", "k": "Ton plus gros mois",
         "v": wrapped_mod.MOIS_NOMS[d["mois_peak"] - 1] if d["mois_peak"] else "—", "d": "le plus actif"},
    ]
    st.markdown(_metric_cards(wrapped_cards), unsafe_allow_html=True)

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
        st.markdown(
            _metric_cards([
                {"emoji": "🎭", "k": genre, "v": n, "d": "visionnages"}
                for genre, n in d["top_genres"]
            ]),
            unsafe_allow_html=True,
        )
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
                    "itemStyle": {"color": "#FFE100", "borderRadius": [4, 4, 0, 0]},
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
        "Exporte tes données (MDBList ou ZIP Trakt) au format JSON neutre ou en rapport "
        "Excel multi-onglets. Aucun secret ni jeton n'est jamais inclus."
    )
    dataset = _dataset()

    # ── Restauration : disponible même sans données chargées ni connexion ────
    st.markdown("#### 📥 Restaurer une sauvegarde")
    st.caption(
        "Importe ton fichier de sauvegarde JSON pour recharger l'application "
        "sans nouvelle analyse ni connexion MDBList."
    )
    uploaded = st.file_uploader("Choisis un fichier JSON", type=["json"], key="backup_restore")
    if uploaded is not None:
        try:
            data = json.load(uploaded)
        except Exception:
            st.error("Fichier JSON invalide.")
            data = None
        if data:
            saved = data.get("dataset") if isinstance(data, dict) else None
            if isinstance(saved, dict) and isinstance(saved.get("sections"), dict):
                st.markdown(
                    f'<div class="accent-callout"><strong>✅ SAUVEGARDE VALIDE</strong> · '
                    f'Export du {str(data.get("export_date") or "?").replace("T", " ")[:16]}.</div>',
                    unsafe_allow_html=True,
                )
                if st.button("🔄 Restaurer dans l'application", type="primary", key="restore_backup"):
                    st.session_state["_normalized_dataset"] = saved
                    st.session_state.pop("_source_genre_cache", None)
                    st.session_state.pop("_mdblist_playback_poster_cache", None)
                    st.rerun()
            else:
                st.error("Format de sauvegarde non reconnu (dataset manquant).")

    st.divider()

    if not dataset:
        st.markdown(
            '<div class="accent-callout"><strong>DONNÉES NON CHARGÉES</strong> · '
            'Charge MDBList depuis le Tableau de bord ou restaure une sauvegarde '
            'ci-dessus avant d’exporter.</div>',
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
        "Un classeur avec un onglet par analyse : Résumé, Historique, Mes contenus (Watchlist + listes), "
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

        # Mes contenus dans mes listes : tous les contenus de la Watchlist et
        # de chaque liste (statique, dynamique, IA, flux), avec leur conteneur.
        contents_values = []
        for source in dataset.get("sources") or []:
            if not isinstance(source, dict) or source.get("kind") == "aggregate":
                continue
            container = str(source.get("name") or source.get("label") or "?")
            if source.get("kind") == "watchlist" or container == "Watchlist MDBList":
                container = "Watchlist"
            for movie in source.get("movies") or []:
                contents_values.append(
                    {
                        "Liste": container,
                        "Type": "Film",
                        "Titre": movie.get("title") or movie.get("name") or "?",
                        "Année": movie.get("release_year") or movie.get("year") or "—",
                    }
                )
            for show in source.get("shows") or []:
                contents_values.append(
                    {
                        "Liste": container,
                        "Type": "Série",
                        "Titre": show.get("title") or show.get("name") or "?",
                        "Année": show.get("release_year") or show.get("year") or "—",
                    }
                )
        contents_df = pd.DataFrame(contents_values)

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
            summary_rows, history_df, contents_df, lists_df, stats_df, achievements_df
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
    # N'écrase un choix explicite de source (ex. « Importer un ZIP Trakt »)
    # que si l'utilisateur n'a rien choisi dans cette session.
    if not st.session_state.get("pending_source"):
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
elif page == "📦 Migration Trakt → MDBList":
    render_migration_page()
else:
    placeholder(page)

st.caption(f"{APP_NAME} · {APP_VERSION} · aucun accès Trakt requis")
