# Operations

## Health and API discovery

`GET /health/` is the process liveness probe. The generated OpenAPI schema is served at
`/api/schema/`, with Swagger at `/api/docs/` and Redoc at `/api/redoc/`.

## Admin access

The seeded dashboard owner is an application user, not a Django staff user. Create a separate
operational account before using `/admin/`:

```bash
docker compose exec api python manage.py createsuperuser
```

## Structured logs

Logs are emitted as one JSON object per line by default. Common fields are `timestamp`, `level`,
`logger`, and `message`; webhook tasks add `webhook_event_id` and `handled`. Set
`LOG_FORMAT=console` for local human-readable output and `LOG_LEVEL=DEBUG` when investigating.

## Debugging Stripe webhooks

1. Find the provider event ID in Admin under **Webhook events**.
2. Inspect status, processing attempts, timestamps, payload, and retained error.
3. Correlate the numeric Admin ID with `webhook_event_id` in worker logs.
4. Fix the mapping or provider issue before redelivering the event from Stripe.

Terminal `processed` and `ignored` events are idempotent. Failed events are retained and Celery
retries transient failures with backoff.

## Debugging invoices and usage

Invoice Admin can search by Stripe invoice/subscription IDs, customer email, tenant, or number.
Check `pdf_generated_at` and worker logs when a PDF is absent. Usage events are read-only in Admin;
inspect `sync_status` and `sync_error`, then correct configuration before retrying the task.

## Demo data

For Docker Compose, run `docker compose exec api python manage.py seed_demo`. For native execution,
run `make seed` after migrations. The command is safe to repeat and creates tenant `acme-demo`, an
owner, plan, active subscription, usage metric/event, and paid invoice. Default dashboard login:
`demo@tenantbill.local` / `demo-password`.

The placeholder keys in `.env.example` keep local domain behavior available but do not represent a
working Stripe connection. Usage synchronization will retain a `failed` status and error until a
valid Stripe test-mode secret is configured. Webhook signature verification requires the signing
secret from the Stripe endpoint or local forwarding session.
