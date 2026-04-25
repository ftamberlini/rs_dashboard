"""
Movie Dashboard — Main entry point.
Run with: streamlit run app.py
"""

import streamlit as st

st.set_page_config(
    page_title="🎬 World Movie Dashboard",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "World Movie Dashboard powered by MovieLens & IMDb data",
    },
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@300;400;500;600&display=swap');

    /* Background */
    [data-testid="stAppViewContainer"] {
        background: #0a0a0f;
        color: #e8e8f0;
    }
    [data-testid="stSidebar"] {
        background: #111118;
        border-right: 1px solid #1e1e2e;
    }

    /* Typography */
    h1, h2, h3 {
        font-family: 'Bebas Neue', sans-serif !important;
        letter-spacing: 2px;
    }
    body, p, div, span, label {
        font-family: 'Inter', sans-serif !important;
    }

    /* Metric cards */
    [data-testid="stMetric"] {
        background: #16161f;
        border: 1px solid #2a2a3e;
        border-radius: 8px;
        padding: 16px;
    }
    [data-testid="stMetricValue"] {
        color: #e8b86d !important;
        font-family: 'Bebas Neue', sans-serif !important;
        font-size: 2rem !important;
    }
    [data-testid="stMetricLabel"] {
        color: #888 !important;
        font-size: 0.75rem !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Sidebar multiselect */
    [data-testid="stMultiSelect"] > div {
        background: #16161f;
        border-color: #2a2a3e;
        border-radius: 6px;
    }

    /* Divider */
    hr { border-color: #2a2a3e; }

    /* Sidebar header */
    .sidebar-section-title {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 0.85rem;
        letter-spacing: 2px;
        color: #e8b86d;
        text-transform: uppercase;
        margin-top: 12px;
        margin-bottom: 4px;
    }

    /* Badge */
    .genre-badge {
        display: inline-block;
        background: #1e1e2e;
        border: 1px solid #3a3a5e;
        color: #c8c8e8;
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 0.72rem;
        margin: 2px;
        font-family: 'Inter', sans-serif;
    }
    .tag-badge {
        display: inline-block;
        background: #1a1a10;
        border: 1px solid #4a4a20;
        color: #e8e0a0;
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 0.72rem;
        margin: 2px;
        font-family: 'Inter', sans-serif;
    }
    .person-card {
        background: #16161f;
        border: 1px solid #2a2a3e;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 8px;
    }
    .person-name {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.1rem;
        color: #e8b86d;
        letter-spacing: 1px;
    }
    .person-detail {
        font-size: 0.78rem;
        color: #aaa;
        margin-top: 4px;
    }

    /* Page title bar */
    .page-header {
        background: linear-gradient(90deg, #1a0a2e 0%, #0a0a0f 60%);
        border-bottom: 2px solid #e8b86d;
        padding: 12px 24px;
        margin-bottom: 24px;
        border-radius: 8px;
    }
    .page-header h1 {
        color: #e8b86d;
        font-size: 2.2rem;
        margin: 0;
    }
    .page-header p {
        color: #888;
        margin: 0;
        font-size: 0.85rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Navigation ─────────────────────────────────────────────────────────────────
PAGES = {
    "🌍 World Dashboard": "pages/dashboard.py",
    "🎬 Movie Detail": "pages/movie_detail.py",
}

with st.sidebar:
    st.markdown(
        "<div style='font-family:Bebas Neue,sans-serif;font-size:1.8rem;"
        "color:#e8b86d;letter-spacing:3px;padding-bottom:8px;border-bottom:"
        "1px solid #2a2a3e;margin-bottom:16px;'>🎬 MOVIE LENS</div>",
        unsafe_allow_html=True,
    )
    page = st.radio(
        "Navigate",
        list(PAGES.keys()),
        label_visibility="collapsed",
    )

# ── Load selected page ─────────────────────────────────────────────────────────
if page == "🌍 World Dashboard":
    from pages import dashboard
    dashboard.render()
else:
    from pages import movie_detail
    movie_detail.render()
