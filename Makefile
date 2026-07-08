.PHONY: install lint test migrate runserver docker-up docker-down

install:
	poetry install

lint:
	poetry run ruff check .

test:
	poetry run pytest

migrate:
	poetry run python manage.py migrate

runserver:
	poetry run python manage.py runserver

docker-up:
	docker compose up --build

docker-down:
	docker compose down
