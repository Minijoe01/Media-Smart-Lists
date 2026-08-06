"""Media Smart Lists — coque visuelle fournisseur-neutre.

Étape 3 : restauration du thème Aston Martin et de la navigation historique.
Aucun secret et aucun appel distant à ce stade.
"""

from __future__ import annotations

import os

import streamlit as st


APP_NAME = "Media Smart Lists"
APP_VERSION = "0.2.1-alpha"

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
        border-radius: 14px;
        color: var(--am-text);
        margin: .65rem 0 1rem;
        padding: .78rem 1rem;
    }
    .accent-callout strong {
        color: var(--am-lime);
        font-family: 'ManropeMSL', 'DejaVu Sans', sans-serif;
        font-weight: 900;
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
    div[data-testid="stDownloadButton"] > button:hover,
    div[data-testid="stFormSubmitButton"] > button:hover {
        background: rgba(8, 55, 50, 0.85) !important;
        border-color: rgba(0,163,146,0.50) !important;
        box-shadow: none !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--am-green), var(--am-green-aston)) !important;
        border: none !important;
        color: #fff !important;
        font-weight: 700 !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #00B8A5, #006058) !important;
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
    icon_col, title_col = st.columns([0.08, 0.92], vertical_alignment="center")
    with icon_col:
        if os.path.exists("logo.png"):
            st.image("logo.png", width=58)
        else:
            st.markdown("## 🎬")
    with title_col:
        st.markdown(
            '<div class="brand-kicker">Un seul tableau de bord · plusieurs sources</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="brand-title">Media Smart Lists</div>', unsafe_allow_html=True)
        st.markdown('<div class="brand-rule"></div>', unsafe_allow_html=True)
    st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)


def page_dashboard() -> None:
    st.subheader("🏠 Tableau de bord")
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
        if st.button("Préparer l'import ZIP Trakt", key="choose_zip"):
            st.session_state["pending_source"] = "trakt_zip"

    if st.session_state.get("pending_source") == "mdblist":
        st.markdown(
            '<div class="accent-callout"><strong>✓ MDBLIST SÉLECTIONNÉ</strong> · '
            'Le connecteur sera ajouté à l’étape suivante.</div>',
            unsafe_allow_html=True,
        )
    elif st.session_state.get("pending_source") == "trakt_zip":
        st.markdown(
            '<div class="accent-callout"><strong>✓ ZIP TRAKT SÉLECTIONNÉ</strong> · '
            'Le parseur sera ajouté progressivement.</div>',
            unsafe_allow_html=True,
        )

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
    st.subheader(page)
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


page = navigation()
header()
if page == "🏠 Tableau de bord":
    page_dashboard()
else:
    placeholder(page)

st.caption(f"{APP_NAME} · {APP_VERSION} · aucun accès Trakt requis")
