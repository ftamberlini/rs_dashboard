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
            paper_bgcolor="#0a0a0f",
            plot_bgcolor="#0a0a0f",
            geo=dict(bgcolor="#0a0a0f"),
        )
        return fig

    fig = px.scatter_geo(
        map_data,
        lat="latitude",
        lon="longitude",
        size="movie_count",
        color="avg_imdb_rating",
        color_continuous_scale=[
            [0.0, "#2a2a3e"],
            [0.5, "#7b4fa0"],
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
        landcolor="#16161f",
        showocean=True,
        oceancolor="#0a0a0f",
        showlakes=False,
        showcountries=True,
        countrycolor="#2a2a3e",
        showframe=False,
        bgcolor="#0a0a0f",
    )

    fig.update_layout(
        paper_bgcolor="#0a0a0f",
        plot_bgcolor="#0a0a0f",
        font_color="#e8e8f0",
        margin=dict(l=0, r=0, t=0, b=0),
        coloraxis_colorbar=dict(
            title="IMDb Rating",
            tickfont=dict(color="#888"),
            titlefont=dict(color="#888"),
            bgcolor="#16161f",
            bordercolor="#2a2a3e",
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
                colorscale=[[0, "#2a2a3e"], [1, "#e8b86d"]],
                showscale=False,
            ),
            text=values,
            textposition="outside",
            textfont=dict(color="#888", size=11),
        )
    )
    fig.update_layout(
        title=dict(text=title, font=dict(color="#e8b86d", size=14, family="Bebas Neue")),
        paper_bgcolor="#16161f",
        plot_bgcolor="#16161f",
        font_color="#888",
        margin=dict(l=0, r=30, t=40, b=0),
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, categoryorder="total ascending"),
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
        line=dict(color="#2a2a3e", dash="dash"),
    )
    fig.update_layout(
        title=dict(text="IMDb vs MovieLens Rating", font=dict(color="#e8b86d", size=14, family="Bebas Neue")),
        paper_bgcolor="#16161f",
        plot_bgcolor="#16161f",
        font_color="#888",
        margin=dict(l=0, r=0, t=40, b=0),
        legend=dict(bgcolor="#0a0a0f", bordercolor="#2a2a3e", borderwidth=1),
        height=300,
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
    countries = filtered["country"].nunique() if total_films else 0

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

    # Film table
    st.markdown("---")
    st.markdown("#### 📋 Film List")

    search = st.text_input("🔍 Search by title", placeholder="Type a movie name…")
    display_df = repo.search_movies(search) if search else filtered

    table_cols = ["title", "year", "country", "continent", "language", "imdb_rating", "movielens_rating", "imdb_votes", "movielens_votes"]
    available_cols = [c for c in table_cols if c in display_df.columns]

    display_df = display_df[available_cols].rename(columns={
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
