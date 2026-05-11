"""
Movie Detail page — full profile of a single film.
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from data_repository import MovieDataRepository


@st.cache_resource
def get_repo() -> MovieDataRepository:
    return MovieDataRepository()


# ── Helpers ────────────────────────────────────────────────────────────────────

def _badge(text: str, kind: str = "genre") -> str:
    css_class = "genre-badge" if kind == "genre" else "tag-badge"
    return f"<span class='{css_class}'>{text}</span>"


def _badges_from_pipe_string(value: str, kind: str = "genre") -> str:
    parts = [p.strip() for p in str(value).split("|") if p.strip()]
    return " ".join(_badge(p, kind) for p in parts)


def _format_currency(value) -> str:
    try:
        v = float(value)
        if v >= 1_000_000:
            return f"${v/1_000_000:.1f}M"
        if v >= 1_000:
            return f"${v/1_000:.0f}K"
        return f"${v:,.0f}"
    except (TypeError, ValueError):
        return "—"


def _person_card(person: dict, role: str) -> str:
    name = person.get("name", "Unknown")
    birth = person.get("birth_year", "—")
    gender = person.get("gender", "—")
    race = person.get("race", "—")
    ethnicity = person.get("ethnicity", "—")
    religion = person.get("religion", "—")
    birth_place = person.get("birth_place", "—")
    return f"""
    <div class='person-card'>
        <div class='person-name'>{name}</div>
        <div class='person-detail'>
            <b>Birth Year:</b> {birth} &nbsp;|&nbsp;
            <b>Gender:</b> {gender} &nbsp;|&nbsp;
            <b>Race:</b> {race} &nbsp;|&nbsp;
            <b>Ethnicity:</b> {ethnicity} &nbsp;|&nbsp;
            <b>Religion:</b> {religion} &nbsp;|&nbsp;
            <b>Born in:</b> {birth_place}
        </div>
    </div>
    """


# ── User Ratings & Tags modal (expander) ──────────────────────────────────────

def _show_user_data(repo: MovieDataRepository, movie_id: int):
    data = repo.get_movie_user_ratings_and_tags(movie_id)
    ratings = data["ratings"]
    tags = data["tags"]

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### 👥 User Ratings (MovieLens)")
        if ratings:
            import pandas as pd
            df = pd.DataFrame(ratings)[["user_id", "rating", "date"]].rename(
                columns={"user_id": "User ID", "rating": "Rating ⭐", "date": "Date"}
            )
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.caption("No ratings available.")

    with col2:
        st.markdown("##### 🏷️ User Tags (MovieLens)")
        if tags:
            import pandas as pd
            df = pd.DataFrame(tags)[["user_id", "tag", "date"]].rename(
                columns={"user_id": "User ID", "tag": "Tag", "date": "Date"}
            )
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.caption("No tags available.")


# ── Main render ────────────────────────────────────────────────────────────────

def render():
    repo = get_repo()

    # Header
    st.markdown(
        "<div class='page-header'>"
        "<h1>🎬 MOVIE DETAIL</h1>"
        "<p>Full profile · cast · ratings · community tags</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # Movie selector
    all_movies = repo.movies[["movie_id", "title", "year"]].sort_values("title")
    options = {f"{row.title} ({row.year})": row.movie_id for row in all_movies.itertuples()}

    preselected_id = st.session_state.get("selected_movie_id")
    preselected_label = None
    if preselected_id:
        row = repo.movies[repo.movies["movie_id"] == preselected_id]
        if not row.empty:
            r = row.iloc[0]
            preselected_label = f"{r['title']} ({r['year']})"

    default_index = list(options.keys()).index(preselected_label) if preselected_label in options else 0

    selected_label = st.selectbox(
        "Select a film",
        list(options.keys()),
        index=default_index,
    )
    movie_id = options[selected_label]
    detail = repo.get_movie_detail(movie_id)

    if not detail:
        st.error("Movie not found.")
        return

    movie = detail["movie"]
    directors = detail["directors"]
    writers = detail["writers"]
    tags = detail["tags"]

    # ── Top section: poster + core info ──────────────────────────────────────
    col_img, col_info = st.columns([1, 2], gap="large")

    with col_img:
        img_url = movie.get("image_url", "")
        if img_url and str(img_url).startswith("http"):
            st.image(img_url, use_container_width=True)
        else:
            st.markdown(
                "<div style='background:#16161f;border:1px solid #2a2a3e;"
                "border-radius:8px;height:320px;display:flex;align-items:center;"
                "justify-content:center;color:#444;font-size:3rem;'>🎬</div>",
                unsafe_allow_html=True,
            )

    with col_info:
        st.markdown(
            f"<h2 style='font-family:Bebas Neue,sans-serif;color:#e8b86d;"
            f"font-size:2.4rem;letter-spacing:3px;margin-bottom:4px;'>"
            f"{movie.get('title','')}</h2>",
            unsafe_allow_html=True,
        )

        meta_col1, meta_col2, meta_col3 = st.columns(3)
        meta_col1.metric("Year", str(movie.get("year", "—")))
        meta_col2.metric("Budget", _format_currency(movie.get("budget")))
        meta_col3.metric("Gross", _format_currency(movie.get("gross")))

        st.markdown("<br>", unsafe_allow_html=True)

        lang_val = movie.get("language", "—")
        st.markdown(f"**🗣 Language:** {lang_val}")

        st.markdown("**📖 Synopsis:**")
        st.markdown(
            f"<p style='color:#2c2c44;line-height:1.6;font-size:0.9rem;'>"
            f"{movie.get('synopsis','—')}</p>",
            unsafe_allow_html=True,
        )

        # Genres
        ml_genres = _badges_from_pipe_string(movie.get("movielens_genres", ""))
        imdb_genres = _badges_from_pipe_string(movie.get("imdb_genres", ""))
        st.markdown(f"**🎭 MovieLens Genres:** {ml_genres}", unsafe_allow_html=True)
        st.markdown(f"**🎬 IMDb Genres:** {imdb_genres}", unsafe_allow_html=True)

        # Tags
        if tags:
            tag_html = " ".join(
                _badge(f"{t['tag']} ×{t['count']}", "tag") for t in tags
            )
            st.markdown(f"**🏷️ Community Tags:** {tag_html}", unsafe_allow_html=True)

    st.markdown("---")

    # ── Ratings ───────────────────────────────────────────────────────────────
    st.markdown("### 📊 Ratings & Votes")
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("⭐ IMDb Rating", f"{movie.get('imdb_rating', 0):.1f} / 10")
    r2.metric("🎯 ML Rating", f"{movie.get('movielens_rating', 0):.1f} / 10")
    r3.metric("👁 IMDb Votes", f"{int(movie.get('imdb_votes', 0)):,}")
    r4.metric("👥 ML Votes", f"{int(movie.get('movielens_votes', 0)):,}")

    # IMDb progress bar (visual)
    imdb_r = float(movie.get("imdb_rating", 0))
    ml_r = float(movie.get("movielens_rating", 0))
    ml_r_10 = ml_r * 2  # ML is /5, convert to /10 for comparison

    st.markdown(
        f"""
        <div style='margin-top:12px;'>
          <div style='display:flex;align-items:center;gap:12px;margin-bottom:6px;'>
            <span style='width:100px;font-size:0.78rem;color:#444455;'>IMDb</span>
            <div style='flex:1;background:#d0d8e4;border-radius:4px;height:10px;'>
              <div style='width:{imdb_r*10}%;background:#e8b86d;border-radius:4px;height:10px;'></div>
            </div>
            <span style='width:36px;text-align:right;color:#e8b86d;font-size:0.85rem;'>{imdb_r:.1f}</span>
          </div>
          <div style='display:flex;align-items:center;gap:12px;'>
            <span style='width:100px;font-size:0.78rem;color:#444455;'>MovieLens</span>
            <div style='flex:1;background:#d0d8e4;border-radius:4px;height:10px;'>
              <div style='width:{ml_r_10*10}%;background:#2e86c1;border-radius:4px;height:10px;'></div>
            </div>
            <span style='width:36px;text-align:right;color:#1a5276;font-size:0.85rem;'>{ml_r:.1f}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # ── Directors ─────────────────────────────────────────────────────────────
    st.markdown("### 🎬 Director(s)")
    if directors:
        for d in directors:
            st.markdown(_person_card(d, "Director"), unsafe_allow_html=True)
    else:
        st.caption("No director data available.")

    # ── Writers ───────────────────────────────────────────────────────────────
    st.markdown("### ✍️ Writer(s)")
    if writers:
        for w in writers:
            st.markdown(_person_card(w, "Writer"), unsafe_allow_html=True)
    else:
        st.caption("No writer data available.")

    st.markdown("---")

    # ── Community data link / expander ────────────────────────────────────────
    with st.expander("👥 View all user ratings & tags for this film", expanded=False):
        _show_user_data(repo, movie_id)
