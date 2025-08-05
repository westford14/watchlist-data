"""Recommender flow tasks."""

import os
from typing import Optional

import pandas as pd
from prefect import task
from prefect.cache_policies import NO_CACHE
from prefect.logging import get_run_logger

from src.recommender.trainer import Trainer


@task(cache_policy=NO_CACHE)
def instantiate_recommender(
    movie_file: str,
    extra_data: Optional[pd.DataFrame] = None,
) -> Trainer:
    """Instantiate the trainer.

    Args:
        movie_file (str): input data
    Returns:
        Trainer
    """
    logger = get_run_logger()
    logger.info("instantiating the trainer")

    return Trainer(movie_file=movie_file, extra_data=extra_data)


@task(cache_policy=NO_CACHE)
def train_recommender(trainer: Trainer) -> Trainer:
    """Train the recommendation engine.

    Args:
        trainer (Trainer): the instantiated trainer object
    Returns:
        Trainer
    """
    logger = get_run_logger()
    logger.info("fitting the trainer")

    trainer.fit()
    return trainer


@task(cache_policy=NO_CACHE)
def save_recommender(trainer: Trainer, folder: str) -> None:
    """Train the recommendation engine.

    Args:
        trainer (Trainer): the instantiated trainer object
        folder (str): subfolder to save to
    Returns:
        Trainer
    """
    logger = get_run_logger()
    logger.info("saving the trainer")

    subfolder = "recommender"
    try:
        logger.info(f"creating output directory: {folder}/{subfolder}")
        os.makedirs(os.path.join(folder, subfolder))
    except FileExistsError:
        logger.warning(f"output_path: {folder}/{subfolder} already exists")

    trainer.save(os.path.join(folder, subfolder))
