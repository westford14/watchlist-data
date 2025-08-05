"""The watchlist flow."""

from prefect import flow, get_run_logger
from pydantic import BaseModel

from src.common.env import Settings
from src.pipeline.common import generate_flow_run_name
from src.pipeline.tasks.recommender import (
    instantiate_recommender,
    train_recommender,
    save_recommender,
)
from src.pipeline.tasks.watchlist import (
    gather_pages,
    instantiate_letterboxd,
    watchlist_scrape,
    save_dataframe,
    enrich_data_tmdb,
    combine_into_dataframe,
    extra_watchlist_data,
)


class RecommenderParameters(BaseModel):
    movie_file: str
    local: bool = True
    root: str = "./outputs"


class WatchlistParameters(BaseModel):
    username: str
    local: bool = True
    root: str = "./outputs"


@flow(flow_run_name=generate_flow_run_name)
def letterboxd_watchlist(
    watchlist_parameters: WatchlistParameters,
    recommender_parameters: RecommenderParameters,
) -> None:
    """
    Flow to extract watchlist information from Letterboxd.

    Args:
        parameters: WatchlistParameters
    Returns:
        None
    """
    logger = get_run_logger()
    logger.info("starting the watchlist scraping")
    settings = Settings()
    settings.username = settings.validate_username(watchlist_parameters.username)
    settings.local = settings.validate_local(watchlist_parameters.local)
    logger.info(f"using settings: {settings}")

    logger.info("creating the scraper")
    scraper = instantiate_letterboxd(settings)

    logger.info("gathering the pages")
    pages = gather_pages(scraper)
    logger.info(f"found pages: {pages}")

    logger.info("parsing the pages")
    scraped_movies = []
    for page in pages:
        logger.info(f"scraping page: {page} ...")
        movies = watchlist_scrape(scraper=scraper, page=page)
        logger.info(f"page: {page} scraped")
        scraped_movies.extend(movies)

    logger.info("combining into a dataframe")
    frame = combine_into_dataframe(movies=scraped_movies)
    scraper.movies = frame

    logger.info("enriching the data")
    enrich_data_tmdb(scraper=scraper)

    logger.info("handling the saving of the pd.DataFrame")
    watchlist_data = save_dataframe(scraper=scraper, root=watchlist_parameters.root)

    logger.info("gathering extra data from the watchlist")
    extra_data = extra_watchlist_data(watchlist_df=watchlist_data, settings=settings)

    logger.info("creating the trainer object")

    trainer = instantiate_recommender(
        movie_file=recommender_parameters.movie_file,
        extra_data=extra_data,
    )

    logger.info("training the recommender")
    trainer = train_recommender(trainer=trainer)

    logger.info("saving the recommender")
    save_recommender(trainer, recommender_parameters.root)


if __name__ == "__main__":
    boxd_parameters = WatchlistParameters(username="westford14")
    rec_parameters = RecommenderParameters(movie_file="./data/movies_metadata.csv")
    letterboxd_watchlist.serve(
        name="letterboxd-watchlist",
        parameters={
            "watchlist_parameters": boxd_parameters,
            "recommender_parameters": rec_parameters,
        },
    )
