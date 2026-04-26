"""
Data layer for the Movie Dashboard application.
Handles loading and querying movie data from CSV files or relational database.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict, Any
import os


class MovieDataRepository:
    """
    Repository class responsible for loading, caching, and querying
    movie data from CSV files or a relational database.
    """

    DATA_DIR = Path(__file__).parent / "data"


    def __init__(self, use_database: bool = False, db_connection_string: Optional[str] = None):
        """
        Initialize the repository.

        Args:
            use_database: If True, load data from a relational DB instead of CSVs.
            db_connection_string: SQLAlchemy connection string for the database.
        """
        self.use_database = use_database
        self.db_connection_string = db_connection_string
        self._country_ref: pd.DataFrame = pd.read_csv(self.DATA_DIR / "country.csv")
        self.continent_by_country: Dict[str, str] = dict(zip(self._country_ref["iso"], self._country_ref["continent"]))
        self.iso_by_name: Dict[str, str] = dict(zip(self._country_ref["country"], self._country_ref["iso"]))
        self.country_coords: Dict[str, Any] = self._load_coords_mapping()
        self._movies: Optional[pd.DataFrame] = None
        self._movies_country: Optional[pd.DataFrame] = None
        self._directors: Optional[pd.DataFrame] = None
        self._writers: Optional[pd.DataFrame] = None
        self._tags: Optional[pd.DataFrame] = None
        self._ratings: Optional[pd.DataFrame] = None

    # ------------------------------------------------------------------
    # Internal loaders
    # ------------------------------------------------------------------

    def get_countries_for_continents(self, continents: Optional[List[str]] = None) -> List[str]:
        df = self._country_ref
        if continents:
            df = df[df["continent"].isin(continents)]
        return sorted(df["country"].dropna().unique().tolist())

    def _load_continent_mapping(self) -> Dict[str, str]:
        path = self.DATA_DIR / "country.csv"
        df = pd.read_csv(path)
        return dict(zip(df["iso"], df["continent"]))

    def _load_coords_mapping(self) -> Dict[str, Any]:
        path = self.DATA_DIR / "country_coords.csv"
        df = pd.read_csv(path)
        return {row["iso"]: (row["latitude"], row["longitude"]) for _, row in df.iterrows()}

    def _load_csv(self, filename: str) -> pd.DataFrame:
        path = self.DATA_DIR / filename
        if not path.exists():
            raise FileNotFoundError(f"Data file not found: {path}")
        else:
            text = filename.split(".")[1]
            if text == 'tsv':
                df = pd.read_csv(path, sep='\t')
            else:
                df = pd.read_csv(path)
            df.columns = df.columns.str.lower()
            return df
            
    def _load_from_db(self, query: str) -> pd.DataFrame:
        from sqlalchemy import create_engine
        engine = create_engine(self.db_connection_string)
        with engine.connect() as conn:
            return pd.read_sql(query, conn)

    def _enrich_movies(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add computed columns to the movies dataframe."""
        df = df.copy()

        mc = self.movies_country
        country_str = mc.groupby("movieid")["country"].apply(lambda x: "|".join(x))
        primary_iso = mc.groupby("movieid")["country"].first()

        df["country"] = df["movieid"].map(country_str)
        iso = df["movieid"].map(primary_iso)
        df["continent"] = iso.map(self.continent_by_country).fillna("Unknown")
        coords = iso.map(self.country_coords)
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
                raw = self._load_csv("movies.tsv")
            self._movies = self._enrich_movies(raw)
        return self._movies

    @property
    def movies_country(self) -> pd.DataFrame:
        if self._movies_country is None:
            self._movies_country = self._load_csv("movies_country.csv")
        return self._movies_country

    @property
    def directors(self) -> pd.DataFrame:
        if self._directors is None:
            if self.use_database:
                self._directors = self._load_from_db("SELECT * FROM director")
            else:
                self._directors = self._load_csv("directors.tsv")
        return self._directors

    @property
    def writers(self) -> pd.DataFrame:
        if self._writers is None:
            if self.use_database:
                self._writers = self._load_from_db("SELECT * FROM writer")
            else:
                self._writers = self._load_csv("writers.tsv")
        return self._writers

    @property
    def tags(self) -> pd.DataFrame:
        if self._tags is None:
            if self.use_database:
                self._tags = self._load_from_db("SELECT * FROM tags")
            else:
                self._tags = self._load_csv("tags.tsv")
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

    def get_director_gender_dominance(self) -> "pd.Series[str]":
        counts = (
            self.directors
            .assign(gender=self.directors["gender"].str.upper())
            .groupby("movieid")["gender"]
            .value_counts()
            .unstack(fill_value=0)
        )
        male = counts.get("MALE", pd.Series(0, index=counts.index))
        female = counts.get("FEMALE", pd.Series(0, index=counts.index))

        def classify(m, f):
            if m == 0 and f == 0:
                return "UNK"
            if f == 0:
                return "EM"
            if m == 0:
                return "EF"
            if m >= f:
                return "MM"
            return "MF"

        return pd.Series(
            {mid: classify(int(male.get(mid, 0)), int(female.get(mid, 0))) for mid in counts.index},
            name="director_gender_dominance",
        )

    def get_writer_gender_dominance(self) -> "pd.Series[str]":
        counts = (
            self.writers
            .assign(gender=self.writers["gender"].str.upper())
            .groupby("movieid")["gender"]
            .value_counts()
            .unstack(fill_value=0)
        )
        male = counts.get("MALE", pd.Series(0, index=counts.index))
        female = counts.get("FEMALE", pd.Series(0, index=counts.index))

        def classify(m, f):
            if m == 0 and f == 0:
                return "UNK"
            if f == 0:
                return "EM"
            if m == 0:
                return "EF"
            if m >= f:
                return "MM"
            return "MF"

        return pd.Series(
            {mid: classify(int(male.get(mid, 0)), int(female.get(mid, 0))) for mid in counts.index},
            name="writer_gender_dominance",
        )

    def get_director_race_dominance(self) -> "pd.Series[str]":
        counts = (
            self.directors
            .assign(race=self.directors["race"].str.upper())
            .groupby("movieid")["race"]
            .value_counts()
            .unstack(fill_value=0)
        )

        def classify(row):
            total = row.sum()
            if total == 0:
                return "UNDEFINED"
            max_count = row.max()
            top = row[row == max_count]
            if len(top) > 1:
                return "MULTI-RACE"
            return top.index[0]

        return pd.Series(
            {mid: classify(counts.loc[mid]) for mid in counts.index},
            name="director_race_dominance",
        )

    def get_writer_race_dominance(self) -> "pd.Series[str]":
        counts = (
            self.writers
            .assign(race=self.writers["race"].str.upper())
            .groupby("movieid")["race"]
            .value_counts()
            .unstack(fill_value=0)
        )

        def classify(row):
            total = row.sum()
            if total == 0:
                return "UNDEFINED"
            max_count = row.max()
            top = row[row == max_count]
            if len(top) > 1:
                return "MULTI-RACE"
            return top.index[0]

        return pd.Series(
            {mid: classify(counts.loc[mid]) for mid in counts.index},
            name="writer_race_dominance",
        )

    def get_filtered_movies(
        self,
        continents: Optional[List[str]] = None,
        countries: Optional[List[str]] = None,
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

        if countries:
            selected_isos = set(self.iso_by_name.get(c, "") for c in countries) - {""}
            mask = df["country"].dropna().str.split("|").apply(lambda isos: bool(set(isos) & selected_isos))
            df = df[mask]

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
            valid_movie_ids = dir_df["movieid"].unique()
            df = df[df["movieid"].isin(valid_movie_ids)]

        # Writer filters
        if any([writer_genders, writer_races, writer_ethnicities]):
            wr_df = self.writers.copy()
            if writer_genders:
                wr_df = wr_df[wr_df["gender"].isin(writer_genders)]
            if writer_races:
                wr_df = wr_df[wr_df["race"].isin(writer_races)]
            if writer_ethnicities:
                wr_df = wr_df[wr_df["ethnicity"].isin(writer_ethnicities)]
            valid_movie_ids = wr_df["movieid"].unique()
            df = df[df["movieid"].isin(valid_movie_ids)]

        return df.reset_index(drop=True)

    def get_map_data(self, filtered_movies: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate filtered movies per country for choropleth/bubble map.
        """
        agg = (
            filtered_movies.groupby(["country", "continent", "latitude", "longitude"])
            .agg(
                movie_count=("movieid", "count"),
                avg_imdb_votes=("imdb_votes", "mean"),
                avg_movielens_votes=("movielens_votes", "mean"),
                avg_imdb_rating=("imdb_rating", "mean"),
                avg_movielens_rating=("movielens_rating", "mean"),
            )
            .reset_index()
        )
        return agg

    def get_movie_detail(self, movieid: int) -> Dict[str, Any]:
        """Return a full detail dict for one movie including people, tags, ratings."""
        movie_row = self.movies[self.movies["movieid"] == movieid]
        if movie_row.empty:
            return {}

        movie = movie_row.iloc[0].to_dict()

        # Directors
        dirs = self.directors[self.directors["movieid"] == movieid].to_dict("records")

        # Writers
        wrts = self.writers[self.writers["movieid"] == movieid].to_dict("records")

        # Tags with counts
        movie_tags = self.tags[self.tags["movieid"] == movieid]
        tag_counts = (
            movie_tags.groupby("tag")
            .size()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
            .to_dict("records")
        )

        # Ratings
        movie_ratings = self.ratings[self.ratings["movieid"] == movieid]
        movielens_ratings = movie_ratings[movie_ratings["source"] == "movielens"]

        return {
            "movie": movie,
            "directors": dirs,
            "writers": wrts,
            "tags": tag_counts,
            "user_ratings": movielens_ratings.to_dict("records"),
        }

    def get_movie_user_ratings_and_tags(self, movieid: int) -> Dict[str, Any]:
        """Return all user ratings and tags for a specific movie."""
        ratings = self.ratings[self.ratings["movieid"] == movieid].copy()
        tags = self.tags[self.tags["movieid"] == movieid].copy()

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
        self._movies_country = None
        self._directors = None
        self._writers = None
        self._tags = None
        self._ratings = None
