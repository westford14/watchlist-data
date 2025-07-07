"""Letterboxd scraper."""

import time
from dataclasses import dataclass
from typing import List, no_type_check

import chromedriver_binary
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from src.common.env import Settings
from src.common.logger import get_logger, LoggingContext


logger = get_logger(__name__)


@dataclass
class Movie:
    name: str
    id: int
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
        self.logger = logger
        self.settings = settings
        self.driver = self.__create_driver()
        self.watchlist_url = (
            f"https://letterboxd.com/{self.settings.username}/watchlist/"
        )

        with LoggingContext({"url": self.watchlist_url}):
            self.logger.info("getting the watchlist URL")

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

        driver_path = chromedriver_binary.chromedriver_filename

        with LoggingContext({"options": options}):
            self.logger.info("creating the headless driver")

        service = Service(executable_path=driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        return driver

    def get_watchlist_pages(self) -> List[int]:
        """Get the number of pages to paginate through.

        Returns:
            List[int] of the pages to scrape
        """
        self.logger.info("gathering the number of watchlist pages ...")
        self.driver.get(self.watchlist_url)

        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        pages = soup.find_all("li", class_="paginate-page")
        last_page = int(pages[-1].text)

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

        self.driver.get(f"{self.watchlist_url}/page/{page}/")
        time.sleep(0.5)

        self.logger.info("parsing the page ...")
        soup = BeautifulSoup(self.driver.page_source, "html.parser")

        self.logger.info("parsing the poster containers")
        films = soup.find_all("li", class_="poster-container")

        self.logger.info(f"found {len(films)} ... parsing ... ")

        movies = []
        for film in films:
            try:
                self.logger.info(
                    f"gathering the TMDB info for {film.div.attrs["data-film-slug"]}"
                )
                self.driver.get(
                    f"https://letterboxd.com/film/{film.div.attrs["data-film-slug"]}/"
                )
                time.sleep(0.5)

                soup = BeautifulSoup(self.driver.page_source, "html.parser")
                tmdb_id = int(soup.find("body")["data-tmdb-id"])

                movie = Movie(
                    name=film.div.attrs["data-film-slug"],
                    id=int(film.div.attrs["data-film-id"]),
                    url=film.div.attrs["data-film-link"],
                    tmdb_id=tmdb_id,
                )
                movies.append(movie)
            except Exception as e:
                self.logger.error(f"could not parse film due to: {e}")
        return movies
