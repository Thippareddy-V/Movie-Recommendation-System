# import pickle
# import urllib.parse
# from concurrent.futures import ThreadPoolExecutor
# from pathlib import Path
# import streamlit as st
# import requests
# import os
# from dotenv import load_dotenv

# # 1. Path Setup
# BASE_DIR = Path(__file__).resolve().parent.parent
# ARTIFACTS_DIR = BASE_DIR / "artifacts"



# load_dotenv()  # Reads .env from root

# TMDB_API_KEY = os.getenv("TMDB_API_KEY")
# OMDB_API_KEY = os.getenv("OMDB_API_KEY", "trilogy")

# # 2. Page Configuration
# st.set_page_config(page_title="Movie Recommender System", layout="wide")
# st.header("🎬 Movie Recommender System")

# # 3. Load Artifacts (Cached in memory)
# @st.cache_resource
# def load_data():
#     with open(ARTIFACTS_DIR / "movies.pkl", "rb") as f:
#         movies = pickle.load(f)
#     with open(ARTIFACTS_DIR / "similarity.pkl", "rb") as f:
#         similarity = pickle.load(f)
#     return movies, similarity

# movies, similarity = load_data()

# # 4. Cached Poster Fetcher with URL Encoding
# @st.cache_data(show_spinner=False)
# def fetch_poster(movie_id, title):
#     # Attempt 1: Fetch via TMDB
#     try:
#         tmdb_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
#         response = requests.get(tmdb_url, timeout=3)
#         if response.status_code == 200:
#             poster_path = response.json().get("poster_path")
#             if poster_path:
#                 return f"https://image.tmdb.org/t/p/w500{poster_path}"
#     except Exception:
#         pass

#     # Attempt 2: Fallback via OMDb with URL encoding
#     try:
#         encoded_title = urllib.parse.quote(title)
#         omdb_url = f"http://www.omdbapi.com/?t={encoded_title}&apikey={OMDB_API_KEY}"
#         res = requests.get(omdb_url, timeout=3)
#         if res.status_code == 200:
#             poster = res.json().get("Poster")
#             if poster and poster != "N/A":
#                 return poster
#     except Exception:
#         pass

#     return "https://via.placeholder.com/500x750?text=Poster+Not+Found"

# # 5. Recommendation Logic (Parallel Poster Fetching)
# def recommend(movie):
#     index = movies[movies["title"] == movie].index[0]
#     distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    
#     top_5 = distances[1:6]
#     recommended_names = [movies.iloc[i[0]].title for i in top_5]
#     recommended_ids = [movies.iloc[i[0]].movie_id for i in top_5]

#     # Fetch all 5 posters in parallel
#     with ThreadPoolExecutor(max_workers=5) as executor:
#         recommended_posters = list(
#             executor.map(fetch_poster, recommended_ids, recommended_names)
#         )

#     return recommended_names, recommended_posters

# # 6. UI Controls and Render
# movie_list = movies["title"].values
# selected_movie = st.selectbox(
#     "Type or select a movie from the dropdown",
#     movie_list
# )

# if st.button("Show Recommendation", type="primary"):
#     with st.spinner("Finding recommendations..."):
#         names, posters = recommend(selected_movie)
    
#     cols = st.columns(5)
#     for col, name, poster in zip(cols, names, posters):
#         with col:
#             st.text(name)
#             st.image(poster, use_container_width=True)


import logging
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pickle
import requests
import streamlit as st
from dotenv import load_dotenv

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.recommendation import get_recommendations


# --------------------------------------------------
# 1. PATHS AND CONFIGURATION
# --------------------------------------------------


ARTIFACTS_DIR = BASE_DIR / "artifacts"

load_dotenv(BASE_DIR / ".ENV")

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
OMDB_API_KEY = os.getenv("OMDB_API_KEY")

TMDB_BASE_URL = "https://api.themoviedb.org/3/movie"
TMDB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"
PLACEHOLDER_URL = (
    "https://via.placeholder.com/500x750?text=Poster+Not+Found"
)

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

logger = logging.getLogger(__name__)


# --------------------------------------------------
# 2. STREAMLIT CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Movie Recommender System",
    layout="wide"
)

st.header("🎬 Movie Recommender System")


# --------------------------------------------------
# 3. LOAD ML ARTIFACTS
# --------------------------------------------------

@st.cache_resource
def load_data():

    try:
        movies_path = ARTIFACTS_DIR / "movies.pkl"
        similarity_path = ARTIFACTS_DIR / "similarity.pkl"

        if not movies_path.exists():
            raise FileNotFoundError(f"Missing artifact: {movies_path}")

        if not similarity_path.exists():
            raise FileNotFoundError(f"Missing artifact: {similarity_path}")

        with open(movies_path, "rb") as file:
            movies = pickle.load(file)

        with open(similarity_path, "rb") as file:
            similarity = pickle.load(file)

        # Basic artifact validation
        required_columns = {"title", "movie_id"}

        if not required_columns.issubset(movies.columns):
            raise ValueError("Movies artifact is missing required columns.")

        if similarity.shape[0] != len(movies):
            raise ValueError(
                "Similarity matrix and movies dataset have mismatched sizes."
            )

        if similarity.shape[1] != len(movies):
            raise ValueError("Similarity matrix must be square.")

        logger.info("ML artifacts loaded successfully.")

        return movies, similarity

    except Exception:
        logger.exception("Failed to load ML artifacts.")
        raise


try:
    movies, similarity = load_data()

except Exception:
    st.error(
        "Unable to load the recommendation system. "
        "Please try again later."
    )
    st.stop()


# --------------------------------------------------
# 4. POSTER FETCHING
# --------------------------------------------------

@st.cache_data(ttl=86400, max_entries=1000, show_spinner=False)
def fetch_poster(movie_id, title):

    # Attempt 1: TMDB
    if TMDB_API_KEY:

        try:
            response = requests.get(
                f"{TMDB_BASE_URL}/{movie_id}",
                params={
                    "api_key": TMDB_API_KEY,
                    "language": "en-US"
                },
                timeout=3
            )

            response.raise_for_status()

            poster_path = response.json().get("poster_path")

            if poster_path:
                return f"{TMDB_IMAGE_URL}{poster_path}"

        except (requests.RequestException, ValueError):
            logger.warning(
                "TMDB poster retrieval failed for movie ID %s",
                movie_id
            )

    # Attempt 2: OMDb fallback
    if OMDB_API_KEY:

        try:
            response = requests.get(
                "https://www.omdbapi.com/",
                params={
                    "t": title,
                    "apikey": OMDB_API_KEY
                },
                timeout=3
            )

            response.raise_for_status()

            poster = response.json().get("Poster")

            if poster and poster != "N/A":
                return poster

        except (requests.RequestException, ValueError):
            logger.warning(
                "OMDb poster retrieval failed for movie: %s",
                title
            )

    return PLACEHOLDER_URL


# --------------------------------------------------
# 5. USER INTERFACE
# --------------------------------------------------

movie_list = movies["title"].dropna().tolist()

selected_movie = st.selectbox(
    "Type or select a movie from the dropdown",
    movie_list
)


# --------------------------------------------------
# 6. RECOMMENDATION AND POSTER RETRIEVAL
# --------------------------------------------------

if st.button("Show Recommendation", type="primary"):

    with st.spinner("Finding recommendations..."):

        try:

            recommendations = get_recommendations(
                selected_movie,
                movies,
                similarity,
                top_n=5
            )

            if not recommendations:
                st.warning("No recommendations found.")

            else:

                with ThreadPoolExecutor(max_workers=5) as executor:

                    posters = list(
                        executor.map(
                            lambda item: fetch_poster(
                                item["id"],
                                item["title"]
                            ),
                            recommendations
                        )
                    )

                cols = st.columns(len(recommendations))

                for col, movie, poster in zip(
                    cols,
                    recommendations,
                    posters
                ):

                    with col:
                        st.text(movie["title"])
                        st.image(
                            poster,
                            use_container_width=True
                        )

        except Exception:
            logger.exception("Recommendation request failed.")
            st.error(
                "Something went wrong while generating recommendations."
            )
