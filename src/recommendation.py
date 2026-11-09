import pickle
from pathlib import Path

# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Artifact paths
MOVIES_PATH = BASE_DIR / "artifacts" / "movies.pkl"
SIMILARITY_PATH = BASE_DIR / "artifacts" / "similarity.pkl"


# Load saved artifacts
with open(MOVIES_PATH, "rb") as file:
    movies_df = pickle.load(file)

with open(SIMILARITY_PATH, "rb") as file:
    similarity = pickle.load(file)


def recommend(movie):

    index = movies_df[movies_df["title"] == movie].index

    if len(index) == 0:
        return []

    index = index[0]

    distance = similarity[index]

    movies_list = sorted(
        enumerate(distance),
        reverse=True,
        key=lambda x: x[1]
    )[1:6]

    recommendations = []

    for i in movies_list:
        recommendations.append(
            movies_df.iloc[i[0]]["title"]
        )

    return recommendations