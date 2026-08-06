"""Point d'entrée de Media Smart Lists.

Cette première version démarre sans Trakt et sans secret.
Les connecteurs MDBList et ZIP Trakt seront ajoutés progressivement.
"""

from __future__ import annotations

import os

import streamlit as st


APP_NAME = "Media Smart Lists"
APP_VERSION = "0.1.0-alpha"

st.set_page_config(
    page_title=APP_NAME,
    page_icon=("logo.png" if os.path.exists("logo.png") else "🎬"),
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .block-container {
        max-width: 1120px;
        padding-top: 2.2rem;
        padding-bottom: 4rem;
    }
    .msl-hero {
        text-align: center;
        padding: 1.4rem 1rem 1.8rem;
    }
    .msl-kicker {
        color: #CEDC00;
        font-size: .82rem;
        font-weight: 800;
        letter-spacing: .18em;
        text-transform: uppercase;
    }
    .msl-title {
        color: #F0FAF8;
        font-size: clamp(2.2rem, 6vw, 4.8rem);
        font-weight: 900;
        line-height: 1;
        margin: .45rem 0 .8rem;
    }
    .msl-subtitle {
        color: rgba(240, 250, 248, .76);
        font-size: 1.08rem;
        margin: 0 auto;
        max-width: 760px;
    }
    .msl-card {
        background: linear-gradient(145deg, rgba(8, 68, 63, .96), rgba(4, 46, 43, .9));
        border: 1px solid rgba(0, 163, 146, .35);
        border-radius: 18px;
        min-height: 210px;
        padding: 1.25rem 1.3rem;
        margin-bottom: .75rem;
        box-shadow: 0 14px 38px rgba(0, 0, 0, .18);
    }
    .msl-card h3 {
        color: #F0FAF8;
        margin: 0 0 .55rem;
    }
    .msl-card p {
        color: rgba(240, 250, 248, .72);
        margin-bottom: .45rem;
    }
    .msl-badge {
        display: inline-block;
        padding: .25rem .55rem;
        border-radius: 999px;
        background: rgba(206, 220, 0, .12);
        border: 1px solid rgba(206, 220, 0, .42);
        color: #CEDC00;
        font-size: .76rem;
        font-weight: 750;
    }
    .msl-footer {
        color: rgba(240, 250, 248, .52);
        font-size: .82rem;
        text-align: center;
        padding-top: 2.2rem;
    }
    div.stButton > button {
        border-radius: 12px;
        min-height: 3rem;
        font-weight: 750;
        width: 100%;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="msl-hero">
        <div class="msl-kicker">Un seul tableau de bord · plusieurs sources</div>
        <div class="msl-title">Media Smart Lists</div>
        <p class="msl-subtitle">
            Analyse tes films, séries, listes et habitudes avec la même interface,
            depuis MDBList en temps réel ou depuis un export ZIP Trakt.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

mdb_col, trakt_col = st.columns(2, gap="large")

with mdb_col:
    st.markdown(
        """
        <div class="msl-card">
            <span class="msl-badge">TEMPS RÉEL · LECTURE/ÉCRITURE</span>
            <h3>🔗 Connecter MDBList</h3>
            <p>Historique, Watchlist, notes, listes, progression et séries abandonnées.</p>
            <p>La connexion sécurisée sera ajoutée à la prochaine étape.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Préparer la connexion MDBList", type="primary", key="choose_mdblist"):
        st.session_state["pending_source"] = "mdblist"

with trakt_col:
    st.markdown(
        """
        <div class="msl-card">
            <span class="msl-badge">IMPORT LOCAL · LECTURE SEULE</span>
            <h3>📦 Importer un ZIP Trakt</h3>
            <p>Historique complet, rewatches, Watchlist, notes et listes, sans API Trakt.</p>
            <p>Le parseur sécurisé sera branché progressivement.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Préparer l'import ZIP Trakt", key="choose_trakt_zip"):
        st.session_state["pending_source"] = "trakt_zip"

pending = st.session_state.get("pending_source")
if pending == "mdblist":
    st.info("✅ Source MDBList sélectionnée. Aucun identifiant n'est encore demandé ni enregistré.")
elif pending == "trakt_zip":
    st.info("✅ Source ZIP Trakt sélectionnée. Aucun fichier n'est encore envoyé ou analysé.")

st.divider()
st.markdown("### Même expérience, quelle que soit la source")
feature_cols = st.columns(4)
for column, icon, title, text in (
    (feature_cols[0], "🏠", "Dashboard", "Vue d'ensemble et progression"),
    (feature_cols[1], "🎯", "Que regarder ?", "Filtres et recommandations"),
    (feature_cols[2], "📊", "Statistiques", "Habitudes, genres et rythmes"),
    (feature_cols[3], "🧹", "Listes", "Doublons et nettoyage prudent"),
):
    with column:
        st.markdown(f"#### {icon} {title}")
        st.caption(text)

st.markdown(
    f'<div class="msl-footer">{APP_NAME} · {APP_VERSION} · aucun accès Trakt requis</div>',
    unsafe_allow_html=True,
)
