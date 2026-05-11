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
    background: #ffffff; /* fundo bem claro */
    color: #2c2c34; /* texto escuro suave */
}

[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #d6d9e6;
}

[data-testid="stSidebar"] * {
    color: #1b1f25 !important;
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
    background: #ffffff;
    border: 1px solid #e0e3ef;
    border-radius: 2px;
    padding: 16px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.04);
}

[data-testid="stMetricValue"] {
    color: #1351B4 ;
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 2rem !important;
}

[data-testid="stMetricLabel"] {
    color: #1b1f25 ;
    font-weight: 700;
    font-size: 0.75rem !important;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* Text input (search) */
[data-testid="stTextInput"] input {
    background: #ffffff !important;
    color: #1b1f25 !important;
    border-color: #c8cdd6 !important;
}

/* Selectbox */
[data-testid="stSelectbox"] > div,
[data-testid="stSelectbox"] [data-baseweb="select"] > div {
    background: #ffffff !important;
    color: #1b1f25 !important;
    border-color: #c8cdd6 !important;
}

[data-testid="stSelectbox"] li[role="option"] {
    background: #ffffff !important;
    color: #1b1f25 !important;
}

[data-testid="stSelectbox"] li[role="option"]:hover {
    background: #f0f4fa !important;
}

/* Sidebar multiselect */
[data-testid="stSidebar"] [data-testid="stMultiSelect"] > div,
[data-testid="stSidebar"] [data-testid="stMultiSelect"] input,
[data-testid="stSidebar"] [data-testid="stMultiSelect"] span {
    background: #ffffff !important;
    color: #1b1f25 !important;
    border-color: #c8cdd6 !important;
}

[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] [data-baseweb="popover"] {
    background: #ffffff !important;
    color: #1b1f25 !important;
    border-color: #c8cdd6 !important;
}

[data-testid="stSidebar"] [data-baseweb="tag"] {
    background: #e8ecf4 !important;
    color: #1b1f25 !important;
}

[data-testid="stSidebar"] li[role="option"] {
    background: #ffffff !important;
    color: #1b1f25 !important;
}

[data-testid="stSidebar"] li[role="option"]:hover {
    background: #f0f4fa !important;
}

/* Divider */
hr { border-color: #e2e5f2; }

/* Sidebar header */
.sidebar-section-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 0.85rem;
    font-weight: 700;
    letter-spacing: 2px;
    color:  #1b1f25 ;
    text-transform: uppercase;
    margin-top: 12px;
    margin-bottom: 4px;
}

/* Badge */
.genre-badge {
    display: inline-block;
    background: #e8ecfb;
    border: 1px solid #cfd5f0;
    color: #4a4a6a;
    border-radius: 2px;
    padding: 3px 8px;
    font-size: 0.72rem;
    margin: 2px;
    font-family: 'Inter', sans-serif;
}

.tag-badge {
    display: inline-block;
    background: #fff4e6;
    border: 1px solid #ffe0c2;
    color: #1351B4;
    border-radius: 2px;
    padding: 3px 8px;
    font-size: 0.72rem;
    margin: 2px;
    font-family: 'Inter', sans-serif;
}

.person-card {
    background: #ffffff;
    border: 1px solid #e0e3ef;
    border-radius: 2px;
    padding: 12px 16px;
    margin-bottom: 8px;
}

.person-name {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.1rem;
    color: #1351B4;
    letter-spacing: 1px;
}

.person-detail {
    font-size: 0.78rem;
    color: #444455;
    margin-top: 4px;
}

/* Page title bar */
.page-header {
    background: linear-gradient(90deg, #e9ecfb 0%, #f7f8fd 100%);
    border-bottom: 2px solid #1351B4;
    padding: 12px 24px;
    margin-bottom: 24px;
    border-radius: 2px;
}

.page-header h1 {
    color: #1351B4;
    font-size: 2.2rem;
    margin: 0;
}

.page-header p {
    color: #444455;
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
        "color:#1351B4;letter-spacing:3px;padding-bottom:8px;border-bottom:"
        "1px solid #d6d9e6;margin-bottom:16px;'>🎬 MOVIE LENS</div>",
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
