"""The full configuration."""

import logging
from typing import Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Encapsulate configuration provided via env variables or the filesystem.

    Attributes:
        username (str): letterboxd username to scrape
        tmdb_access_token (str): the access token for TMDB
        tmdb_api_key (str): the TMDB API key
        selenium_port (str): the selenium port
        selenium_host (str): the selenium host
        local (bool): if it is being run locally / with a local docker instance
        default_log_level (int): default output level given to loggers.
            Can be integer or predefined levels in logging (e.g. INFO, DEBUG)
    """

    username: str
    tmdb_access_token: str
    tmdb_api_key: str
    selenium_port: str = "4444"
    selenium_host: str = "selenium-hub"
    local: bool = True
    default_log_level: int = logging.INFO
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("username")
    @classmethod
    def validate_username(
        cls,
        username: str,
    ) -> str:
        """
        Validate the username.

        Args:
            username (str): username of the letterboxd account
        Returns:
            The validated username.
        Raises:
            AttributeError if the username is not a string
        """
        if not isinstance(username, str):
            raise AttributeError(f"username must be of type str not {type(username)}")
        return username

    @field_validator("tmdb_access_token")
    @classmethod
    def validate_tmdb_access_token(
        cls,
        tmdb_access_token: str,
    ) -> str:
        """
        Validate the TMDB access token.

        Args:
            tmdb_access_token (str): the TMDB access token
        Returns:
            The validated TMDB access token.
        Raises:
            AttributeError if the TMDB access token is not a string
        """
        if not isinstance(tmdb_access_token, str):
            raise AttributeError(
                f"tmdb_access_token must be of type str not {type(tmdb_access_token)}"
            )
        return tmdb_access_token

    @field_validator("tmdb_access_token")
    @classmethod
    def validate_tmdb_api_key(
        cls,
        tmdb_api_key: str,
    ) -> str:
        """
        Validate the TMDB API key.

        Args:
            tmdb_api_key (str): the TMDB API key
        Returns:
            The validated TMDB API key.
        Raises:
            AttributeError if the TMDB API key is not a string
        """
        if not isinstance(tmdb_api_key, str):
            raise AttributeError(
                f"tmdb_api_key must be of type str not {type(tmdb_api_key)}"
            )
        return tmdb_api_key

    @field_validator("local")
    @classmethod
    def validate_local(
        cls,
        local: bool,
    ) -> bool:
        """
        Validate the local paramater.

        Args:
            local (bool): the local paramater
        Returns:
            The validated local paramater.
        Raises:
            AttributeError if the local parameter is not a bool
        """
        if not isinstance(local, bool):
            raise AttributeError(f"local must be of type str not {type(local)}")
        return local

    @field_validator("default_log_level", mode="before")
    @classmethod
    def validate_log_level(
        cls,
        default_log_level: Union[int, str],
    ) -> int:
        """
        Validate the default log level.

        Args:
            default_log_level: provided log level.  This could also be in string format
               for the coming logging levels (e.g. INFO, DEBUG)
        Returns:
            The validated default log level.
        Raises:
            AttributeError if a string is provided that is not a known log level
        """
        if isinstance(default_log_level, str):
            if default_log_level.isnumeric():
                default_log_level = int(default_log_level)
            else:
                default_log_level = int(getattr(logging, default_log_level.upper()))
        return default_log_level
