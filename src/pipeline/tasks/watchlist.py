"""Watchlist flow tasks."""

import os
import time
from dataclasses import asdict
from typing import List, Optional

import pandas as pd
from prefect import task
from prefect.cache_policies import NO_CACHE
from prefect.logging import get_run_logger

from src.common.env import Settings
from src.scraper.letterboxd import LetterboxdScraper, Movie


@task(cache_policy=NO_CACHE)
def instantiate_letterboxd(settings: Settings) -> LetterboxdScraper:
    """Instantiate the Letterboxd scraper.

    Args:
        settings (Settings): the settings attached to the flow
    Returns:
        LetterboxdScraper
    """
    logger = get_run_logger()
    logger.info("instantiating the scraper")
    scraper = LetterboxdScraper(settings=settings)
    return scraper


@task(cache_policy=NO_CACHE)
def gather_pages(scraper: LetterboxdScraper) -> List[int]:
    """Gather the number of pages needed for watchlist scraping.

    Args:
       scraper (LetterboxdScraper): the instantiated Letterboxd scraper
    Returns:
        List[int] the pages to scrape
    """
    logger = get_run_logger()
    logger.info("gathering the watchlist pages")
    pages = scraper.get_watchlist_pages()
    return pages


@task(cache_policy=NO_CACHE)
def watchlist_scrape(scraper: LetterboxdScraper, pages: List[int]) -> List[Movie]:
    """Scrape the watchlist information.

    Args:
        scraper (LetterboxdScraper): the scraper
        pages (List[int]): the pages to scrape
    Returns:
        List[Movie]
    """
    logger = get_run_logger()
    logger.info(f"gathering the scraping data from watchlist pages: {pages}")

    movies = []
    for page in pages:
        output = scraper.scrape_watchlist(page)
        movies.extend(output)
    return movies


@task
def combine_into_dataframe(movies: List[Movie]) -> pd.DataFrame:
    """Combines the scraped movies into a dataframe.

    Args:
        movies (List[Movie]): the scraped movies
    Returns:
        pd.DataFrame
    """
    logger = get_run_logger()
    logger.info("creating the dataframe")

    return pd.DataFrame([asdict(x) for x in movies])


@task
def save_dataframe(frame: pd.DataFrame, settings: Settings) -> Optional[str]:
    """Handle the saving of the scraped movies.

    Args:
        frame (pd.DataFrame): the dataframe to save
        settings (Settings): information about where to save
    Returns:
        Optional[str]
    """
    logger = get_run_logger()
    logger.info("saving the dataframe ...")

    if settings.local:
        logger.info("saving locally")
        root = "./outputs"
        subdir = str(int(time.time()))
        if os.path.exists(os.path.join(root, "current.csv")):
            logger.info("current database exists")
            old_frame = pd.read_csv(os.path.join(root, "current.csv"))
            new_movies = frame[~frame["id"].isin(old_frame["id"].values.tolist())]
            updated = pd.concat([new_movies, old_frame])
        else:
            logger.info("current database does not exists")
            updated = frame.copy()
        try:
            logger.info(f"creating output directory: {root}/{subdir}")
            os.makedirs(os.path.join(root, subdir))
        except FileExistsError:
            logger.warning(f"output_path: {root}/{subdir} already exists")

        logger.info(f"saving dataframe to: {root}/{subdir}/current.csv")
        updated.to_csv(os.path.join(root, subdir, "current.csv"), index=False)
        logger.info(f"saving dataframe to: {root}/current.csv")
        updated.to_csv(os.path.join(root, "current.csv"), index=False)
        return os.path.join(root, subdir, "current.csv")
    else:
        logger.info("not covered yet ...")
        return None
