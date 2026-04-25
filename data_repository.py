"""
Data layer for the Movie Dashboard application.
Handles loading and querying movie data from CSV files or relational database.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import os


class MovieDataRepository:
    """
    Repository class responsible for loading, caching, and querying
    movie data from CSV files or a relational database.
    """

    DATA_DIR = Path(__file__).parent / "data"

    # Country → (latitude, longitude) mapping for map visualization
    COUNTRY_COORDS: Dict[str, Tuple[float, float]] = {
        "USA": (37.0902, -95.7129),
        "UK": (55.3781, -3.4360),
        "France": (46.2276, 2.2137),
        "Germany": (51.1657, 10.4515),
        "Italy": (41.8719, 12.5674),
        "Spain": (40.4637, -3.7492),
        "Japan": (36.2048, 138.2529),
        "South Korea": (35.9078, 127.7669),
        "China": (35.8617, 104.1954),
        "India": (20.5937, 78.9629),
        "Brazil": (-14.2350, -51.9253),
        "Mexico": (23.6345, -102.5528),
        "Argentina": (-38.4161, -63.6167),
        "Australia": (-25.2744, 133.7751),
        "Canada": (56.1304, -106.3468),
        "Russia": (61.5240, 105.3188),
        "Sweden": (60.1282, 18.6435),
        "Norway": (60.4720, 8.4689),
        "Denmark": (56.2639, 9.5018),
        "Poland": (51.9194, 19.1451),
        "Portugal": (39.3999, -8.2245),
        "Iran": (32.4279, 53.6880),
        "Turkey": (38.9637, 35.2433),
        "South Africa": (-30.5595, 22.9375),
        "Nigeria": (9.0820, 8.6753),
        "Egypt": (26.8206, 30.8025),
        "Taiwan": (23.6978, 120.9605),
        "Hong Kong": (22.3193, 114.1694),
        "Thailand": (15.8700, 100.9925),
        "Colombia": (4.5709, -74.2973),
    }

    CONTINENT_BY_COUNTRY: Dict[str, str] = {
        "USA": "North America", "Canada": "North America", "Mexico": "North America",
        "UK": "Europe", "France": "Europe", "Germany": "Europe", "Italy": "Europe",
        "Spain": "Europe", "Portugal": "Europe", "Sweden": "Europe", "Norway": "Europe",
        "Denmark": "Europe", "Poland": "Europe", "Russia": "Europe",
        "Japan": "Asia", "South Korea": "Asia", "China": "Asia", "India": "Asia",
        "Taiwan": "Asia", "Hong Kong": "Asia", "Thailand": "Asia", "Iran": "Asia",
        "Turkey": "Asia",
        "Brazil": "South America", "Argentina": "South America", "Colombia": "South America",
        "Australia": "Oceania",
        "South Africa": "Africa", "Nigeria": "Africa", "Egypt": "Africa",
    }

    def __init__(self, use_database: bool = False, db_connection_string: Optional[str] = None):
        """
        Initialize the repository.

        Args:
            use_database: If True, load data from a relational DB instead of CSVs.
            db_connection_string: SQLAlchemy connection string for the database.
        """
        self.use_database = use_database
        self.db_connection_string = db_connection_string
        self._movies: Optional[pd.DataFrame] = None
        self._directors: Optional[pd.DataFrame] = None
        self._writers: Optional[pd.DataFrame] = None
        self._tags: Optional[pd.DataFrame] = None
        self._ratings: Optional[pd.DataFrame] = None

    # ------------------------------------------------------------------
    # Internal loaders
    # ------------------------------------------------------------------

    def _load_csv(self, filename: str) -> pd.DataFrame:
        path = self.DATA_DIR / filename
        if not path.exists():
            raise FileNotFoundError(f"Data file not found: {path}")
        return pd.read_csv(path)

    def _load_from_db(self, query: str) -> pd.DataFrame:
        from sqlalchemy import create_engine
        engine = create_engine(self.db_connection_string)
        with engine.connect() as conn:
            return pd.read_sql(query, conn)

    def _enrich_movies(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add computed columns to the movies dataframe."""
        df = df.copy()
        df["continent"] = df["country"].map(self.CONTINENT_BY_COUNTRY).fillna("Unknown")
        coords = df["country"].map(self.COUNTRY_COORDS)
        df["latitude"] = coords.apply(lambda c: c[0] if isinstance(c, tuple) else np.nan)
        df["longitude"] = coords.apply(lambda c: c[1] if isinstance(c, tuple) else np.nan)

        # Normalise list-like columns
        for col in ["language", "movielens_genres", "imdb_genres"]:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str)
        return df

    # ------------------------------------------------------------------
    # Public data accessors (lazy-loaded + cached)
    # ------------------------------------------------------------------

    @property
    def movies(self) -> pd.DataFrame:
        if self._movies is None:
            if self.use_database:
                raw = self._load_from_db("SELECT * FROM movie")
            else:
                raw = self._load_csv("movies.csv")
            self._movies = self._enrich_movies(raw)
        return self._movies

    @property
    def directors(self) -> pd.DataFrame:
        if self._directors is None:
            if self.use_database:
                self._directors = self._load_from_db("SELECT * FROM director")
            else:
                self._directors = self._load_csv("directors.csv")
        return self._directors

    @property
    def writers(self) -> pd.DataFrame:
        if self._writers is None:
            if self.use_database:
                self._writers = self._load_from_db("SELECT * FROM writer")
            else:
                self._writers = self._load_csv("writers.csv")
        return self._writers

    @property
    def tags(self) -> pd.DataFrame:
        if self._tags is None:
            if self.use_database:
                self._tags = self._load_from_db("SELECT * FROM tags")
            else:
                self._tags = self._load_csv("tags.csv")
        return self._tags

    @property
    def ratings(self) -> pd.DataFrame:
        if self._ratings is None:
            if self.use_database:
                self._ratings = self._load_from_db("SELECT * FROM ratings")
            else:
                self._ratings = self._load_csv("ratings.csv")
        return self._ratings

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def get_unique_values(self, column: str) -> List[str]:
        """Return sorted unique non-null values for a column in movies."""
        values = set()
        for cell in self.movies[column].dropna():
            for part in str(cell).split("|"):
                v = part.strip()
                if v:
                    values.add(v)
        return sorted(values)

    def get_director_unique_values(self, column: str) -> List[str]:
        return sorted(self.directors[column].dropna().unique().tolist())

    def get_writer_unique_values(self, column: str) -> List[str]:
        return sorted(self.writers[column].dropna().unique().tolist())

    def get_filtered_movies(
        self,
        continents: Optional[List[str]] = None,
        languages: Optional[List[str]] = None,
        director_genders: Optional[List[str]] = None,
        director_races: Optional[List[str]] = None,
        director_ethnicities: Optional[List[str]] = None,
        writer_genders: Optional[List[str]] = None,
        writer_races: Optional[List[str]] = None,
        writer_ethnicities: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Return movies filtered by the supplied qualitative criteria.
        All filter arguments are lists of allowed values; None means "no filter".
        """
        df = self.movies.copy()

        if continents:
            df = df[df["continent"].isin(continents)]

        if languages:
            mask = df["language"].apply(
                lambda x: any(lang in x for lang in languages)
            )
            df = df[mask]

        # Director filters
        if any([director_genders, director_races, director_ethnicities]):
            dir_df = self.directors.copy()
            if director_genders:
                dir_df = dir_df[dir_df["gender"].isin(director_genders)]
            if director_races:
                dir_df = dir_df[dir_df["race"].isin(director_races)]
            if director_ethnicities:
                dir_df = dir_df[dir_df["ethnicity"].isin(director_ethnicities)]
            valid_movie_ids = dir_df["movie_id"].unique()
            df = df[df["movie_id"].isin(valid_movie_ids)]

        # Writer filters
        if any([writer_genders, writer_races, writer_ethnicities]):
            wr_df = self.writers.copy()
            if writer_genders:
                wr_df = wr_df[wr_df["gender"].isin(writer_genders)]
            if writer_races:
                wr_df = wr_df[wr_df["race"].isin(writer_races)]
            if writer_ethnicities:
                wr_df = wr_df[wr_df["ethnicity"].isin(writer_ethnicities)]
            valid_movie_ids = wr_df["movie_id"].unique()
            df = df[df["movie_id"].isin(valid_movie_ids)]

        return df.reset_index(drop=True)

    def get_map_data(self, filtered_movies: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate filtered movies per country for choropleth/bubble map.
        """
        agg = (
            filtered_movies.groupby(["country", "continent", "latitude", "longitude"])
            .agg(
                movie_count=("movie_id", "count"),
                avg_imdb_votes=("imdb_votes", "mean"),
                avg_movielens_votes=("movielens_votes", "mean"),
                avg_imdb_rating=("imdb_rating", "mean"),
                avg_movielens_rating=("movielens_rating", "mean"),
            )
            .reset_index()
        )
        return agg

    def get_movie_detail(self, movie_id: int) -> Dict[str, Any]:
        """Return a full detail dict for one movie including people, tags, ratings."""
        movie_row = self.movies[self.movies["movie_id"] == movie_id]
        if movie_row.empty:
            return {}

        movie = movie_row.iloc[0].to_dict()

        # Directors
        dirs = self.directors[self.directors["movie_id"] == movie_id].to_dict("records")

        # Writers
        wrts = self.writers[self.writers["movie_id"] == movie_id].to_dict("records")

        # Tags with counts
        movie_tags = self.tags[self.tags["movie_id"] == movie_id]
        tag_counts = (
            movie_tags.groupby("tag")
            .size()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
            .to_dict("records")
        )

        # Ratings
        movie_ratings = self.ratings[self.ratings["movie_id"] == movie_id]
        movielens_ratings = movie_ratings[movie_ratings["source"] == "movielens"]

        return {
            "movie": movie,
            "directors": dirs,
            "writers": wrts,
            "tags": tag_counts,
            "user_ratings": movielens_ratings.to_dict("records"),
        }

    def get_movie_user_ratings_and_tags(self, movie_id: int) -> Dict[str, Any]:
        """Return all user ratings and tags for a specific movie."""
        ratings = self.ratings[self.ratings["movie_id"] == movie_id].copy()
        tags = self.tags[self.tags["movie_id"] == movie_id].copy()

        if "timestamp" in ratings.columns:
            ratings["date"] = pd.to_datetime(ratings["timestamp"], unit="s").dt.strftime("%Y-%m-%d")
        if "timestamp" in tags.columns:
            tags["date"] = pd.to_datetime(tags["timestamp"], unit="s").dt.strftime("%Y-%m-%d")

        return {
            "ratings": ratings.to_dict("records"),
            "tags": tags.to_dict("records"),
        }

    def search_movies(self, query: str) -> pd.DataFrame:
        """Full-text search on movie title."""
        if not query:
            return self.movies
        q = query.lower()
        return self.movies[self.movies["title"].str.lower().str.contains(q, na=False)]

    def invalidate_cache(self):
        """Force reload of all data on next access."""
        self._movies = None
        self._directors = None
        self._writers = None
        self._tags = None
        self._ratings = None
