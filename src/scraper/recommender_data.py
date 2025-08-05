"""Gathering extra data from TMDB API."""

import json

import pandas as pd
import requests
from ratelimit import limits

from src.common.env import Settings
from src.common.logger import get_logger

logger = get_logger(__name__)

BASE_URL = "https://api.themoviedb.org/3"


@limits(calls=40, period=2)
def enrich_movies(
    watchlist_dataframe: pd.DataFrame, settings: Settings
) -> pd.DataFrame:
    """Enrich the data from letterboxd with data from TMDB.

    Args:
        None
    Returns:
        None
    Raises:
        RuntimeError if self.movies is not set
    """
    extra_data = []
    tmdb_ids = watchlist_dataframe["tmdb_id"]
    for tmdb_id in tmdb_ids:
        try:
            temp = {}
            headers = {
                "accept": "application/json",
                "Authorization": f"Bearer {settings.tmdb_access_token}",
            }
            response = requests.get(
                f"{BASE_URL}/movie/{tmdb_id}?language=en-US", headers=headers
            )
            if response.status_code != 200:
                logger.error(f"request failed with {response.text}")
                continue
            temp["movie_id"] = tmdb_id
            resp = json.loads(response.text)
            genres = resp["genres"]
            genres = [x["name"] for x in genres]
            original_title = resp["original_title"]
            overview = resp["overview"]
            temp["text"] = original_title + " " + overview + " " + " ".join(genres)
            extra_data.append(temp)
        except Exception as e:
            logger.error(f"failed parsing {tmdb_id} - {e}")

    return pd.DataFrame(extra_data)
