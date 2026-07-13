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
Docker Compose also starts the Celery worker used to process persisted Stripe webhooks.

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
- `POST /webhooks/stripe/` (requires a valid `Stripe-Signature` header)

## Stripe Webhooks

Set `STRIPE_WEBHOOK_SECRET` in `.env`, then forward Stripe events to
`http://localhost:8000/webhooks/stripe/`. Valid events are persisted before a Celery task is
published. Event IDs are idempotent, processing failures are recorded, and failed tasks retry
with exponential backoff.

## Roadmap

See [ROADMAP.md](ROADMAP.md) for implementation phases and architectural decisions.
