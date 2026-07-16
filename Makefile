.PHONY: install lint test coverage migrate seed runserver docker-up docker-down

install:
	poetry install

lint:
	poetry run ruff check .

test:
	poetry run pytest

coverage:
	poetry run coverage run -m pytest
	poetry run coverage report --fail-under=90
	poetry run coverage html

migrate:
	poetry run python manage.py migrate

seed:
	poetry run python manage.py seed_demo

runserver:
	poetry run python manage.py runserver

docker-up:
	docker compose up --build

docker-down:
	docker compose down
