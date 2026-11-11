import pickle
from pathlib import Path

# Locate artifacts path dynamically relative to this file
BASE_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"

def load_artifacts():
    with open(ARTIFACTS_DIR / "movies.pkl", "rb") as f:
        movies_df = pickle.load(f)
    with open(ARTIFACTS_DIR / "similarity.pkl", "rb") as f:
        similarity = pickle.load(f)
    return movies_df, similarity

def get_recommendations(movie_title, movies_df, similarity, top_n=5):
    try:
        index = movies_df[movies_df['title'] == movie_title].index[0]
    except IndexError:
        return []

    distances = similarity[index]
    # Sort by similarity score descending, skipping the movie itself at index 0
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:top_n + 1]

    recommendations = []
    for item in movies_list:
        movie_row = movies_df.iloc[item[0]]
        recommendations.append({
            "id": movie_row["movie_id"],
            "title": movie_row["title"]
        })
    return recommendations