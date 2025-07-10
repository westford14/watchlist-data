lint:
	pipenv run tox -e lint
.PHONY: lint

type-check:
	pipenv run tox -e type-check
.PHONY: type-check

test:
	pipenv run tox -e coverage
.PHONY: test

stop-server:
	docker compose down --volumes server worker database
.PHONY: stop-server

start-server: stop-server
	docker compose up -d server worker database --build
.PHONY: start-server

start-prefect: start-server
	docker compose run cli
.PHONY: start-prefect

clean-docker:
	docker system prune -f
	docker images | grep 'watchlist-data-cli' | awk '{print $$3}' | xargs docker rmi
.PHONY: clean-docker