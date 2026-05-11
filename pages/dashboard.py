"""
Dashboard page — world map + KPI metrics with sidebar filters.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

# Make the parent directory importable
sys.path.insert(0, str(Path(__file__).parent.parent))
from data_repository import MovieDataRepository


@st.cache_resource
def get_repo() -> MovieDataRepository:
    return MovieDataRepository()


# ── Sidebar filters ────────────────────────────────────────────────────────────
def _build_sidebar_filters(repo: MovieDataRepository):
    st.sidebar.markdown("---")
    st.sidebar.markdown("<div class='sidebar-section-title'>📍 Origin</div>", unsafe_allow_html=True)
    continents = st.sidebar.multiselect(
        "Continent",
        options=sorted(repo.movies["continent"].dropna().unique()),
        default=[],
        placeholder="All continents",
    )
    countries = st.sidebar.multiselect(
        "Country",
        options=repo.get_countries_for_continents(continents or None),
        default=[],
        placeholder="All countries",
    )
    languages = st.sidebar.multiselect(
        "Language",
        options=repo.get_unique_values("language"),
        default=[],
        placeholder="All languages",
    )

    st.sidebar.markdown("<div class='sidebar-section-title'>🎬 Director</div>", unsafe_allow_html=True)
    dir_genders = st.sidebar.multiselect(
        "Gender",
        options=repo.get_director_unique_values("gender"),
        default=[],
        placeholder="All genders",
        key="dir_gender",
    )
    dir_races = st.sidebar.multiselect(
        "Race",
        options=repo.get_director_unique_values("race"),
        default=[],
        placeholder="All races",
        key="dir_race",
    )
    dir_ethnicities = st.sidebar.multiselect(
        "Ethnicity",
        options=repo.get_director_unique_values("ethnicity"),
        default=[],
        placeholder="All ethnicities",
        key="dir_eth",
    )

    st.sidebar.markdown("<div class='sidebar-section-title'>✍️ Writer</div>", unsafe_allow_html=True)
    wr_genders = st.sidebar.multiselect(
        "Gender",
        options=repo.get_writer_unique_values("gender"),
        default=[],
        placeholder="All genders",
        key="wr_gender",
    )
    wr_races = st.sidebar.multiselect(
        "Race",
        options=repo.get_writer_unique_values("race"),
        default=[],
        placeholder="All races",
        key="wr_race",
    )
    wr_ethnicities = st.sidebar.multiselect(
        "Ethnicity",
        options=repo.get_writer_unique_values("ethnicity"),
        default=[],
        placeholder="All ethnicities",
        key="wr_eth",
    )

    return dict(
        continents=continents or None,
        countries=countries or None,
        languages=languages or None,
        director_genders=dir_genders or None,
        director_races=dir_races or None,
        director_ethnicities=dir_ethnicities or None,
        writer_genders=wr_genders or None,
        writer_races=wr_races or None,
        writer_ethnicities=wr_ethnicities or None,
    )


# ── Map ────────────────────────────────────────────────────────────────────────
def _build_map(map_data: pd.DataFrame) -> go.Figure:
    if map_data.empty:
        fig = go.Figure()
        fig.update_layout(
            paper_bgcolor="#f0f2f5",
            plot_bgcolor="#f0f2f5",
            geo=dict(bgcolor="#f0f2f5"),
        )
        return fig

    fig = px.scatter_geo(
        map_data,
        lat="latitude",
        lon="longitude",
        size="movie_count",
        color="avg_imdb_rating",
        color_continuous_scale=[
            [0.0, "#1a5276"],
            [0.5, "#5499c7"],
            [1.0, "#e8b86d"],
        ],
        hover_name="country",
        hover_data={
            "continent": True,
            "movie_count": True,
            "avg_imdb_rating": ":.2f",
            "avg_movielens_rating": ":.2f",
            "avg_imdb_votes": ":,.0f",
            "avg_movielens_votes": ":,.0f",
            "latitude": False,
            "longitude": False,
        },
        size_max=50,
        labels={
            "movie_count": "# Films",
            "avg_imdb_rating": "IMDb Rating",
            "avg_movielens_rating": "ML Rating",
            "avg_imdb_votes": "Avg IMDb Votes",
            "avg_movielens_votes": "Avg ML Votes",
            "continent": "Continent",
        },
        projection="natural earth",
    )

    fig.update_geos(
        showland=True,
        landcolor="#d8e4ee",
        showocean=True,
        oceancolor="#c0d4eb",
        showlakes=False,
        showcountries=True,
        countrycolor="#a0b4c8",
        showframe=False,
        bgcolor="#f0f2f5",
    )

    fig.update_layout(
        paper_bgcolor="#f0f2f5",
        plot_bgcolor="#f0f2f5",
        font_color="#333344",
        margin=dict(l=0, r=0, t=0, b=0),
        coloraxis_colorbar=dict(
            title="IMDb Rating",
            tickfont=dict(color="#1c2d3e"),
            bgcolor="#e8ecf0",
            bordercolor="#c0c8d0",
        ),
        height=520,
    )

    return fig


# ── Genre bar chart ────────────────────────────────────────────────────────────
def _build_genre_chart(filtered: pd.DataFrame, genre_col: str, title: str) -> go.Figure:
    from collections import Counter

    all_genres = []
    for cell in filtered[genre_col].dropna():
        all_genres.extend([g.strip() for g in str(cell).split("|") if g.strip()])

    if not all_genres:
        return go.Figure()

    counts = Counter(all_genres).most_common(10)
    genres, values = zip(*counts)

    fig = go.Figure(
        go.Bar(
            x=values,
            y=genres,
            orientation="h",
            marker=dict(
                color=values,
                colorscale=[[0, "#b8d4e8"], [1, "#1a5276"]],
                showscale=False,
            ),
            text=values,
            textposition="outside",
            textfont=dict(color="#2c2c44", size=11),
        )
    )
    fig.update_layout(
        title=dict(text=title, font=dict(color="#1351B4", size=14, family="Bebas Neue")),
        paper_bgcolor="#f0f2f5",
        plot_bgcolor="#f0f2f5",
        font_color="#2c2c44",
        margin=dict(l=0, r=30, t=40, b=0),
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, categoryorder="total ascending",
                   tickfont=dict(color="#1b1f25")),
        height=260,
    )
    return fig


# ── Rating scatter ─────────────────────────────────────────────────────────────
def _build_rating_scatter(filtered: pd.DataFrame) -> go.Figure:
    df = filtered.dropna(subset=["imdb_rating", "movielens_rating"])
    if df.empty:
        return go.Figure()

    fig = px.scatter(
        df,
        x="imdb_rating",
        y="movielens_rating",
        size="imdb_votes",
        color="continent",
        hover_name="title",
        hover_data={"year": True, "country": True, "imdb_votes": ":,.0f"},
        labels={"imdb_rating": "IMDb Rating", "movielens_rating": "MovieLens Rating"},
        color_discrete_sequence=px.colors.qualitative.Bold,
        size_max=30,
    )
    fig.add_shape(
        type="line",
        x0=0, y0=0, x1=10, y1=10,
        line=dict(color="#b0bec8", dash="dash"),
    )
    fig.update_layout(
        title=dict(text="IMDb vs MovieLens Rating", font=dict(color="#1351B4", size=14, family="Bebas Neue")),
        paper_bgcolor="#f0f2f5",
        plot_bgcolor="#e8ecf0",
        font_color="#2c2c44",
        margin=dict(l=0, r=0, t=40, b=0),
        legend=dict(bgcolor="#f0f2f5", bordercolor="#c0c8d0", borderwidth=1,
                    font=dict(color="#1b1f25")),
        xaxis=dict(tickfont=dict(color="#1b1f25"), title_font=dict(color="#1b1f25")),
        yaxis=dict(tickfont=dict(color="#1b1f25"), title_font=dict(color="#1b1f25")),
        height=300,
    )
    return fig


# ── Gender dominance chart ─────────────────────────────────────────────────────
_GENDER_COLORS = {
    "EM":  "#1a3a6b",
    "MM":  "#2e86c1",
    "MF":  "#e05c97",
    "EF":  "#8b1a4a",
    "UNK": "#6b7a8a",
}
_GENDER_ORDER = ["EM", "MM", "MF", "EF", "UNK"]

def _build_gender_dominance_chart(
    filtered: pd.DataFrame,
    dominance: "pd.Series[str]",
    title: str,
) -> go.Figure:
    df = filtered[["movieid", "continent"]].copy()
    df["dominance"] = df["movieid"].map(dominance).fillna("UNK")

    counts = (
        df.groupby(["continent", "dominance"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=_GENDER_ORDER, fill_value=0)
    )
    totals = counts.sum(axis=1)
    pct = counts.div(totals, axis=0).mul(100).round(1)
    continents = pct.index.tolist()

    fig = go.Figure()
    for cat in _GENDER_ORDER:
        fig.add_trace(go.Bar(
            name=cat,
            y=continents,
            x=pct[cat],
            orientation="h",
            marker_color=_GENDER_COLORS[cat],
            hovertemplate=f"<b>{cat}</b>: %{{x:.1f}}%<extra></extra>",
        ))

    fig.update_layout(
        barmode="stack",
        bargap=0.35,
        title=dict(text=title, font=dict(color="#1351B4", size=14, family="Bebas Neue")),
        paper_bgcolor="#f0f2f5",
        plot_bgcolor="#e8ecf0",
        font_color="#2c2c44",
        xaxis=dict(title="% of Films", ticksuffix="%", range=[0, 105], gridcolor="#c0c8d0",
                   tickfont=dict(color="#1b1f25"), title_font=dict(color="#1b1f25")),
        yaxis=dict(title="", gridcolor="#c0c8d0", tickfont=dict(color="#1b1f25")),
        legend=dict(bgcolor="#f0f2f5", bordercolor="#c0c8d0", borderwidth=1, orientation="h",
                    yanchor="bottom", y=1.02, xanchor="center", x=0.5,
                    font=dict(color="#1b1f25")),
        margin=dict(l=10, r=20, t=60, b=10),
        height=340,
    )
    return fig


# ── Main render ────────────────────────────────────────────────────────────────
def render():
    repo = get_repo()
    filters = _build_sidebar_filters(repo)
    filtered = repo.get_filtered_movies(**filters)
    map_data = repo.get_map_data(filtered)

    # Header
    st.markdown(
        "<div class='page-header'>"
        "<h1>🌍 WORLD MOVIE DASHBOARD</h1>"
        "<p>Explore cinema across the globe · MovieLens & IMDb data</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # KPI row
    total_films = len(filtered)
    avg_imdb = filtered["imdb_rating"].mean() if total_films else 0
    avg_ml = filtered["movielens_rating"].mean() if total_films else 0
    total_imdb_votes = filtered["imdb_votes"].sum() if total_films else 0
    total_ml_votes = filtered["movielens_votes"].sum() if total_films else 0
    countries = filtered["country"].dropna().str.split("|").explode().nunique() if total_films else 0

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("🎬 Films", f"{total_films:,}")
    c2.metric("🌎 Countries", f"{countries}")
    c3.metric("⭐ Avg IMDb", f"{avg_imdb:.2f}" if total_films else "—")
    c4.metric("🎯 Avg ML", f"{avg_ml:.2f}" if total_films else "—")
    c5.metric("👁 IMDb Votes", f"{total_imdb_votes:,.0f}")
    c6.metric("👥 ML Votes", f"{total_ml_votes:,.0f}")

    st.markdown("<br>", unsafe_allow_html=True)

    # World map
    st.markdown("#### 🗺️ Films by Country")
    st.plotly_chart(_build_map(map_data), use_container_width=True)

    # Bottom charts
    col_left, col_mid, col_right = st.columns([1, 1, 1])
    with col_left:
        st.plotly_chart(
            _build_genre_chart(filtered, "movielens_genres", "Top MovieLens Genres"),
            use_container_width=True,
        )
    with col_mid:
        st.plotly_chart(
            _build_genre_chart(filtered, "imdb_genres", "Top IMDb Genres"),
            use_container_width=True,
        )
    with col_right:
        st.plotly_chart(_build_rating_scatter(filtered), use_container_width=True)

    # Gender dominance charts
    st.markdown("---")
    st.markdown("#### 👥 Gender Dominance by Continent")
    dir_dominance = repo.get_director_gender_dominance()
    wrt_dominance = repo.get_writer_gender_dominance()
    gcol_left, gcol_right = st.columns(2)
    with gcol_left:
        st.plotly_chart(
            _build_gender_dominance_chart(filtered, dir_dominance, "Director Gender Dominance"),
            use_container_width=True,
        )
    with gcol_right:
        st.plotly_chart(
            _build_gender_dominance_chart(filtered, wrt_dominance, "Writer Gender Dominance"),
            use_container_width=True,
        )

    # Film table
    st.markdown("---")
    st.markdown("#### 📋 Film List")

    search = st.text_input("🔍 Search by title", placeholder="Type a movie name…")
    display_df = repo.search_movies(search) if search else filtered

    table_cols = ["title", "year", "country", "continent", "language", "imdb_rating", "movielens_rating", "imdb_votes", "movielens_votes"]
    available_cols = [c for c in table_cols if c in display_df.columns]

    display_df = display_df[available_cols].sort_values("imdb_votes", ascending=False).rename(columns={
        "title": "Title", "year": "Year", "country": "Country",
        "continent": "Continent", "language": "Language",
        "imdb_rating": "IMDb ⭐", "movielens_rating": "ML ⭐",
        "imdb_votes": "IMDb Votes", "movielens_votes": "ML Votes",
    })

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )

    # Navigate to detail
    st.markdown("---")
    movie_titles = filtered["title"].tolist()
    if movie_titles:
        selected_title = st.selectbox("Select a film to view details →", ["— choose —"] + movie_titles)
        if selected_title != "— choose —":
            mid = int(filtered[filtered["title"] == selected_title]["movie_id"].iloc[0])
            st.session_state["selected_movie_id"] = mid
            st.info(f"Switch to **🎬 Movie Detail** in the sidebar to see the full profile of **{selected_title}**.")
