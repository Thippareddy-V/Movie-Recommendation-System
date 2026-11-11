import pickle
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import streamlit as st
import requests
import os
from dotenv import load_dotenv

# 1. Path Setup
BASE_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"



load_dotenv()  # Reads .env from root

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
OMDB_API_KEY = os.getenv("OMDB_API_KEY", "trilogy")

# 2. Page Configuration
st.set_page_config(page_title="Movie Recommender System", layout="wide")
st.header("🎬 Movie Recommender System")

# 3. Load Artifacts (Cached in memory)
@st.cache_resource
def load_data():
    with open(ARTIFACTS_DIR / "movies.pkl", "rb") as f:
        movies = pickle.load(f)
    with open(ARTIFACTS_DIR / "similarity.pkl", "rb") as f:
        similarity = pickle.load(f)
    return movies, similarity

movies, similarity = load_data()

# 4. Cached Poster Fetcher with URL Encoding
@st.cache_data(show_spinner=False)
def fetch_poster(movie_id, title):
    # Attempt 1: Fetch via TMDB
    try:
        tmdb_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
        response = requests.get(tmdb_url, timeout=3)
        if response.status_code == 200:
            poster_path = response.json().get("poster_path")
            if poster_path:
                return f"https://image.tmdb.org/t/p/w500{poster_path}"
    except Exception:
        pass

    # Attempt 2: Fallback via OMDb with URL encoding
    try:
        encoded_title = urllib.parse.quote(title)
        omdb_url = f"http://www.omdbapi.com/?t={encoded_title}&apikey={OMDB_API_KEY}"
        res = requests.get(omdb_url, timeout=3)
        if res.status_code == 200:
            poster = res.json().get("Poster")
            if poster and poster != "N/A":
                return poster
    except Exception:
        pass

    return "https://via.placeholder.com/500x750?text=Poster+Not+Found"

# 5. Recommendation Logic (Parallel Poster Fetching)
def recommend(movie):
    index = movies[movies["title"] == movie].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    
    top_5 = distances[1:6]
    recommended_names = [movies.iloc[i[0]].title for i in top_5]
    recommended_ids = [movies.iloc[i[0]].movie_id for i in top_5]

    # Fetch all 5 posters in parallel
    with ThreadPoolExecutor(max_workers=5) as executor:
        recommended_posters = list(
            executor.map(fetch_poster, recommended_ids, recommended_names)
        )

    return recommended_names, recommended_posters

# 6. UI Controls and Render
movie_list = movies["title"].values
selected_movie = st.selectbox(
    "Type or select a movie from the dropdown",
    movie_list
)

if st.button("Show Recommendation", type="primary"):
    with st.spinner("Finding recommendations..."):
        names, posters = recommend(selected_movie)
    
    cols = st.columns(5)
    for col, name, poster in zip(cols, names, posters):
        with col:
            st.text(name)
            st.image(poster, use_container_width=True)