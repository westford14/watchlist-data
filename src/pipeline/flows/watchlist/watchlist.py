"""The watchlist flow."""

from prefect import flow, get_run_logger
from pydantic import BaseModel

from src.common.env import Settings
from src.pipeline.common import generate_flow_run_name
from src.pipeline.tasks.watchlist import (
    gather_pages,
    instantiate_letterboxd,
    watchlist_scrape,
    save_dataframe,
    enrich_data_tmdb,
    combine_into_dataframe,
)
from src.pipeline.common.splitter import split_list


class WatchlistParameters(BaseModel):
    username: str
    local: bool = True
    root: str = "./outputs"


@flow(flow_run_name=generate_flow_run_name)
def letterboxd_watchlist(watchlist_parameters: WatchlistParameters) -> None:
    """
    Flow to extract watchlist information from Letterboxd.

    Args:
        parameters: WatchlistParameters
    Returns:
        None
    """
    logger = get_run_logger()

    settings = Settings()
    settings.username = settings.validate_username(watchlist_parameters.username)
    settings.local = settings.validate_local(watchlist_parameters.local)
    logger.info(f"using settings: {settings}")

    logger.info("creating the scraper")
    scraper = instantiate_letterboxd(settings)

    logger.info("gathering the pages")
    pages = gather_pages(scraper)
    logger.info(f"found pages: {pages}")

    logger.info("splitting the list into a list of lists")
    page_sets = split_list(pages)

    logger.info("parsing the pages")
    scraped_movies = []
    for page_set in page_sets:
        logger.info(f"scraping page_set: {page_set} ...")
        movies = watchlist_scrape(scraper=scraper, pages=page_set)
        logger.info(f"page_set: {page_set} scraped")
        scraped_movies.extend(movies)

    logger.info("combining into a dataframe")
    frame = combine_into_dataframe(movies=scraped_movies)
    scraper.movies = frame

    logger.info("enriching the data")
    enrich_data_tmdb(scraper=scraper)

    logger.info("handling the saving of the pd.DataFrame")
    output_path = save_dataframe(scraper=scraper, root=watchlist_parameters.root)
    if output_path is not None:
        logger.info(f"movies saved to {output_path}")
    else:
        logger.info("movies saved to the backend DB")


if __name__ == "__main__":
    parameters = WatchlistParameters(username="westford14")
    letterboxd_watchlist.serve(
        name="letterboxd-watchlist", parameters={"watchlist_parameters": parameters}
    )
