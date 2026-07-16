# Operations

## Health and API discovery

`GET /health/` is the process liveness probe. The generated OpenAPI schema is served at
`/api/schema/`, with Swagger at `/api/docs/` and Redoc at `/api/redoc/`.

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

Run `make seed` after migrations. The command is safe to repeat and creates tenant `acme-demo`, an
owner, plan, active subscription, usage metric/event, and paid invoice. Default development login:
`demo@tenantbill.local` / `demo-password`.
