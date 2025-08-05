"""Training runner."""

from ast import literal_eval
from typing import List, Optional

import pandas as pd
import torch

from src.recommender.similarity import SimilarityMeasure

GENRES = [
    "Animation",
    "Comedy",
    "Family",
    "Adventure",
    "Fantasy",
    "Romance",
    "Drama",
    "Action",
    "Crime",
    "Thriller",
    "Horror",
    "History",
    "Science Fiction",
    "Mystery",
    "War",
    "Foreign",
    "Music",
    "Documentary",
    "Western",
]


class Trainer(object):
    """Training class."""

    def __init__(
        self,
        movie_file: str,
        extra_data: Optional[pd.DataFrame] = None,
    ) -> None:
        """Instantiate the class."""
        torch.set_num_threads(1)
        self.movie_file = movie_file
        self.sim_model = SimilarityMeasure()
        self.extra_data = extra_data
        self.train_data = self.load_data(self.extra_data)

    def load_data(self, extra_data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Load the data."""

        movies = pd.read_csv(self.movie_file)
        movies = movies[["id", "original_title", "overview", "genres"]]
        movies = movies.rename(columns={"id": "movie_id", "original_title": "title"})

        movies["movie_id"] = pd.to_numeric(movies["movie_id"], errors="coerce")

        def cleaner(x: list, genres: list = GENRES) -> list:
            ret = []
            for y in x:
                if y in genres:
                    ret.append(y)
            return ret

        movies["genres"] = movies["genres"].apply(
            lambda x: [y["name"] for y in literal_eval(x)]
        )
        movies["genres"] = movies["genres"].apply(cleaner)
        movies["text"] = (
            movies["title"]
            + " "
            + movies["overview"]
            + " "
            + movies["genres"].apply(lambda x: " ".join(x))
        )

        movies = movies.reset_index(drop=True)
        train_data = movies[["movie_id", "text"]]
        train_data = train_data.dropna()
        train_data["movie_id"] = train_data["movie_id"].astype(int)

        if extra_data is not None:
            extra_data["movie_id"] = pd.to_numeric(
                extra_data["movie_id"], errors="coerce"
            )
            extra_data["movie_id"] = extra_data["movie_id"].astype(int)
            extra_data = extra_data.dropna()
            extra_data = extra_data[
                ~extra_data["movie_id"].isin(train_data["movie_id"].values.tolist())
            ]
            train_data = pd.concat([extra_data, train_data])
            train_data = train_data.reset_index(drop=True)

        train_data = train_data.dropna()
        return train_data

    def fit(self) -> None:
        """Fit the similarity model."""
        self.sim_model.fit(
            self.train_data["text"].values,
            ids=self.train_data["movie_id"].values.tolist(),
        )

    def predict(self, movie_text: str, top_k: int = 5) -> List[str]:
        """Predict the top k similar movies."""
        ids = self.sim_model.infer([movie_text], top_k=top_k)
        movies = [self.sim_model.index_to_id[i] for i in ids]  # type: ignore
        return movies

    def save(self, output_dir: str) -> None:
        """Save the model."""
        self.sim_model.save(output_dir)
