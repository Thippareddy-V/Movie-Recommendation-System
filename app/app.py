# import sys
# import pickle
# from pathlib import Path
# import streamlit as st
# import requests

# # 1. Path Setup
# BASE_DIR = Path(__file__).resolve().parent.parent
# ARTIFACTS_DIR = BASE_DIR / "artifacts"

# # # 2. Page Configuration
# # st.set_page_config(page_title="Movie Recommender", layout="wide")
# # st.title("🎬 Movie Recommendation System")

# # # 3. Load Artifacts
# # @st.cache_resource
# # def load_data():
# #     with open(ARTIFACTS_DIR / "movies.pkl", "rb") as f:
# #         movies_df = pickle.load(f)
# #     with open(ARTIFACTS_DIR / "similarity.pkl", "rb") as f:
# #         similarity = pickle.load(f)
# #     return movies_df, similarity

# # movies_df, similarity = load_data()

# # # 4. Safe Poster Fetcher with Short Timeout
# # def fetch_poster(movie_id):
# #     api_key = "8265bd1679663a7ea12ac168da84d2e8"
# #     url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
# #     try:
# #         response = requests.get(url, timeout=2)
# #         if response.status_code == 200:
# #             data = response.json()
# #             poster_path = data.get("poster_path")
# #             if poster_path:
# #                 return f"https://image.tmdb.org/t/p/w500/{poster_path}"
# #     except Exception:
# #         pass
# #     # Fallback placeholder if TMDB is unreachable or blocked
# #     return "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=500&auto=format&fit=crop&q=60"


# # # 5. Recommendation Logic (Top 5)
# # def get_recommendations(movie_title, top_n=5):
# #     try:
# #         index = movies_df[movies_df['title'] == movie_title].index[0]
# #     except IndexError:
# #         return []

# #     distances = similarity[index]
# #     # Slices 1 to 6 to retrieve exactly the top 5 closest movies
# #     movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:top_n + 1]

# #     recommendations = []
# #     for item in movies_list:
# #         movie_row = movies_df.iloc[item[0]]
# #         recommendations.append({
# #             "id": movie_row["movie_id"],
# #             "title": movie_row["title"]
# #         })
# #     return recommendations

# # # 6. UI Controls
# # selected_movie = st.selectbox(
# #     "Select or search for a movie:",
# #     options=movies_df["title"].values
# # )

# # if st.button("Recommend", type="primary"):
# #     with st.spinner("Fetching recommendations..."):
# #         recs = get_recommendations(selected_movie, top_n=5)

# #     if not recs:
# #         st.error("No recommendations found.")
# #     else:
# #         # Create 5 columns
# #         cols = st.columns(len(recs))
# #         for col, movie in zip(cols, recs):
# #             with col:
# #                 st.subheader(movie["title"])
# #                 poster_url = fetch_poster(movie["id"])
# #                 st.image(poster_url)


# from pathlib import Path
# import pickle
# import streamlit as st
# import requests
# from concurrent.futures import ThreadPoolExecutor

# # 1. Define artifact paths relative to this file
# BASE_DIR = Path(__file__).resolve().parent.parent
# ARTIFACTS_DIR = BASE_DIR / "artifacts"

# # 2. Page Configuration
# st.set_page_config(page_title="Movie Recommender System", layout="wide")
# st.header("🎬 Movie Recommender System")

# # 3. Load artifacts safely (cached so they load once instead of on every click)
# @st.cache_resource
# def load_data():
#     with open(ARTIFACTS_DIR / "movies.pkl", "rb") as f:
#         movies = pickle.load(f)
#     with open(ARTIFACTS_DIR / "similarity.pkl", "rb") as f:
#         similarity = pickle.load(f)
#     return movies, similarity

# movies, similarity = load_data()

# # 4. Safe poster fetching with fallback for broken/blocked TMDB requests
# @st.cache_data(show_spinner=False)
# def fetch_poster(movie_id, title):
#     # Attempt 1: Fetch via TMDB
#     try:
#         url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=8265bd1679663a7ea12ac168da84d2e8&language=en-US"
#         response = requests.get(url, timeout=3)
#         if response.status_code == 200:
#             poster_path = response.json().get("poster_path")
#             if poster_path:
#                 return f"https://image.tmdb.org/t/p/w500/{poster_path}"
#     except Exception:
#         pass

#     # Attempt 2: Fallback via OMDb if TMDB is blocked/fails
#     try:
#         omdb_url = f"http://www.omdbapi.com/?t={title}&apikey=trilogy"
#         res = requests.get(omdb_url, timeout=3)
#         if res.status_code == 200:
#             poster = res.json().get("Poster")
#             if poster and poster != "N/A":
#                 return poster
#     except Exception:
#         pass

#     # Generic placeholder image if both fail
#     return "https://via.placeholder.com/500x750?text=Poster+Not+Found"

# # 5. Recommendation logic
# def recommend(movie):
#     index = movies[movies["title"] == movie].index[0]
#     distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    
#     top_5 = distances[1:6]
#     recommended_movie_names = [movies.iloc[i[0]].title for i in top_5]
#     movie_ids = [movies.iloc[i[0]].movie_id for i in top_5]

#     # Fetch all 5 posters concurrently in parallel
#     with ThreadPoolExecutor(max_workers=5) as executor:
#         recommended_movie_posters = list(
#             executor.map(fetch_poster, movie_ids, recommended_movie_names)
#         )

#     return recommended_movie_names, recommended_movie_posters

# # 6. UI Controls and 5-Column Display
# movie_list = movies["title"].values
# selected_movie = st.selectbox(
#     "Type or select a movie from the dropdown",
#     movie_list
# )

# if st.button("Show Recommendation", type="primary"):
#     with st.spinner("Finding recommendations..."):
#         names, posters = recommend(selected_movie)
    
#     # st.columns replaces deprecated st.beta_columns
#     cols = st.columns(5)
#     for col, name, poster in zip(cols, names, posters):
#         with col:
#             st.text(name)
#             st.image(poster, use_container_width=True)



import pickle
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import streamlit as st
import requests

# 1. Path Setup
BASE_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"

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
        tmdb_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=8265bd1679663a7ea12ac168da84d2e8&language=en-US"
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
        omdb_url = f"http://www.omdbapi.com/?t={encoded_title}&apikey=trilogy"
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