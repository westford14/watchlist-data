"""Letterboxd scraper."""

import json
import os
import time
from dataclasses import dataclass
from typing import List, Optional, no_type_check

import pandas as pd
import requests
from bs4 import BeautifulSoup
from ratelimit import limits
from selenium import webdriver
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sqlalchemy import create_engine
from sqlalchemy.sql import text as sa_text

from src.common.env import Settings
from src.common.logger import get_logger, LoggingContext


logger = get_logger(__name__)


@dataclass
class Movie:
    name: str
    letterboxd_id: int
    url: str
    tmdb_id: int


class LetterboxdScraper(object):
    """Class for scraping the letterboxd watchlist of a specific user.

    Args:
        settings (Settings): the settings object
    Returns:
        None
    Raises:
        None
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize the class.

        Args:

        Returns:

        Raises:
        """
        self.base_url = "https://api.themoviedb.org/3"
        self.logger = logger
        self.settings = settings
        self.watchlist_url = (
            f"https://letterboxd.com/{self.settings.username}/watchlist/"
        )

        with LoggingContext({"url": self.watchlist_url}):
            self.logger.info("getting the watchlist URL")
        self.movies: Optional[pd.DataFrame] = None
        self.enriched: Optional[pd.DataFrame] = None

    def __create_driver(self) -> WebDriver:
        """Create the selenium webdriver.

        Returns:
            An instantiated webdriver
        """
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")

        with LoggingContext({"options": options}):
            self.logger.info("creating the headless driver")

        driver = webdriver.Firefox(options=options)  # type: ignore[call-arg]  # noqa: E501
        return driver

    def get_watchlist_pages(self) -> List[int]:
        """Get the number of pages to paginate through.

        Returns:
            List[int] of the pages to scrape
        """
        self.logger.info("gathering the number of watchlist pages ...")
        driver = self.__create_driver()
        driver.get(self.watchlist_url)

        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.ID, "content-nav"))
            )
        except Exception as e:
            self.logger.error(f"could not find content-nav: {e}")

        soup = BeautifulSoup(driver.page_source, "html.parser")
        pages = soup.find_all("li", class_="paginate-page")
        last_page = int(pages[-1].text)
        driver.quit()

        self.logger.info(f"found {pages} to scrape through")
        return list(range(1, last_page + 1))

    @no_type_check
    def scrape_watchlist(self, page: int) -> List[Movie]:
        """Scrape the watchlist.

        Returns:
            List of the extracted Movie objects
        """
        with LoggingContext({"page": page}):
            self.logger.info(f"parsing watchlist page {page}")

        driver = self.__create_driver()
        driver.get(f"{self.watchlist_url}/page/{page}/")
        time.sleep(0.5)

        self.logger.info("parsing the page ...")
        soup = BeautifulSoup(driver.page_source, "html.parser")

        self.logger.info("parsing the poster containers")
        films = soup.find_all("li", class_="griditem")

        self.logger.info(f"found {len(films)} ... parsing ... ")
        driver.quit()

        film_driver = self.__create_driver()
        movies = []
        for film in films:
            try:
                self.logger.info(
                    f"gathering the TMDB info for {film.div.attrs["data-target-link"]}"
                )
                film_driver.get(
                    f"https://letterboxd.com/{film.div.attrs["data-target-link"]}/"
                )
                time.sleep(0.5)

                soup = BeautifulSoup(film_driver.page_source, "html.parser")
                tmdb_id = int(soup.find("body")["data-tmdb-id"])

                movie = Movie(
                    name=film.div.attrs["data-item-name"],
                    letterboxd_id=int(film.div.attrs["data-film-id"]),
                    url=film.div.attrs["data-target-link"],
                    tmdb_id=tmdb_id,
                )
                movies.append(movie)
            except Exception as e:
                self.logger.error(f"could not parse film due to: {e}")
        film_driver.quit()
        return movies

    @limits(calls=40, period=2)
    def enrich_movies(self) -> None:
        """Enrich the data from letterboxd with data from TMDB.

        Args:
            None
        Returns:
            None
        Raises:
            RuntimeError if self.movies is not set
        """
        if self.movies is None:
            raise RuntimeError(
                "self.movies has not been set -- please run self.scrape_watchlist() first"  # noqa: E501
            )

        extra_data = []
        tmdb_ids = self.movies["tmdb_id"]
        for tmdb_id in tmdb_ids:
            try:
                temp = {}
                headers = {
                    "accept": "application/json",
                    "Authorization": f"Bearer {self.settings.tmdb_access_token}",
                }
                response = requests.get(
                    f"{self.base_url}/movie/{tmdb_id}?language=en-US", headers=headers
                )
                if response.status_code != 200:
                    self.logger.error(f"request failed with {response.text}")
                    continue
                temp["tmdb_id"] = tmdb_id
                resp = json.loads(response.text)
                temp["runtime"] = resp["runtime"]
                temp["poster_path"] = resp["poster_path"]
                temp["vote_average"] = resp["vote_average"]
                extra_data.append(temp)
            except Exception as e:
                self.logger.error(f"failed parsing {tmdb_id} - {e}")

        extra_df = pd.DataFrame(extra_data)
        self.enriched = self.movies.merge(extra_df, on="tmdb_id", how="inner")

    def save_to_db(self, root: Optional[str] = None) -> pd.DataFrame:
        """Save the movies to the DB.

        Args:
            None
        Returns:
            pd.DataFrame
        """
        if self.enriched is None:
            raise RuntimeError(
                "self.enriched has not been set -- please run self.scrape_watchlist() first"  # noqa: E501
            )
        if self.settings.local and root is None:
            raise ValueError("running locally, but root has not been set")
        if self.settings.local:
            if root is None:
                root = "outputs"
            subdir = str(int(time.time()))
            if os.path.exists(os.path.join(root, "current.csv")):
                self.logger.info("current database exists")
            else:
                self.logger.info("current database does not exists")
            updated = self.enriched.copy()
            try:
                self.logger.info(f"creating output directory: {root}/{subdir}")
                os.makedirs(os.path.join(root, subdir))
            except FileExistsError:
                self.logger.warning(f"output_path: {root}/{subdir} already exists")

            updated["username"] = self.settings.username
            self.logger.info(f"saving dataframe to: {root}/{subdir}/current.csv")
            updated.to_csv(os.path.join(root, subdir, "current.csv"), index=False)
            self.logger.info(f"saving dataframe to: {root}/current.csv")
            updated.to_csv(os.path.join(root, "current.csv"), index=False)
        else:
            self.logger.info("creating the engine connection")
            engine = create_engine(self.settings.database_url)

            self.logger.info("querying the database")
            with engine.connect() as conn:
                old_frame = pd.read_sql(
                    f"SELECT * FROM movies WHERE username = '{self.settings.username}'",
                    con=conn,
                )

            if len(old_frame) != 0:
                self.logger.info("dropping the data from the old table")
                with engine.connect() as conn:
                    conn.execute(
                        sa_text(
                            f"DELETE FROM movies WHERE username = {self.settings.username};"  # noqa: E501
                        )
                    )
                    conn.commit()

            updated = self.enriched.copy()
            updated["username"] = self.settings.username
            self.logger.info("saving the new dataframe to the database")
            with engine.connect() as conn:
                updated.to_sql("movies", con=conn, if_exists="append", index=False)

        return updated
