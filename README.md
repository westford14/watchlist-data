# Watchlist-Data

[Prefect](https://www.prefect.io/) orchestration for scraping the watchlist
of a specified user for usage with the Watchlist-Frontend.

## Quick Start

Requirements:
* Python 3.13
* Pipenv
* Docker
* Docker Compose
* Chromedriver Binary

To install run:

* `pipenv install` from the root of the directory

To run the prefect instance locally, run:

* `make start-prefect`

Once the docker compose finishes, navigate to http://localhost:4200 to interact
with the Prefect UI.

### Development

* `make lint` to run the linting
* `make type-check` to run the type-checking

### Maintainers

* westford14