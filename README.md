# TenantBill

TenantBill is a production-minded Django backend for SaaS recurring billing and usage-based
billing in a shared-schema multi-tenant architecture.

## Stack

- Django 5 and Django REST Framework
- PostgreSQL
- Redis and Celery
- Stripe SDK behind an integration boundary
- pytest, pytest-django, factory_boy and Ruff
- drf-spectacular for OpenAPI
- Docker Compose for local services

## Local Setup

```bash
poetry install
cp .env.example .env
make migrate
make test
make lint
```

## Docker

```bash
docker compose up --build
```

The API runs at `http://localhost:8000`.

## Useful Commands

```bash
make test
make lint
make runserver
make docker-up
make docker-down
```

## Operational Endpoints

- `GET /health/`
- `GET /api/schema/`
- `GET /api/docs/`

## Roadmap

See [ROADMAP.md](ROADMAP.md) for implementation phases and architectural decisions.
