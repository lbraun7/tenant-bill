# Demo Walkthrough

Start the complete stack and create the deterministic demo fixtures:

```bash
docker compose up --build -d
docker compose exec api python manage.py seed_demo
```

The seed is idempotent and creates an owner, tenant, plan, active subscription, usage metric/event,
and paid invoice for `acme-demo`. Open the dashboard at `http://localhost:3000`, or follow the API
walkthrough below.

## Authenticate

```bash
curl -sS http://localhost:8000/api/auth/login/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"demo@tenantbill.local","password":"demo-password"}'
```

Copy the returned access token into `TOKEN`, then select the demo tenant explicitly:

```bash
curl -sS http://localhost:8000/api/subscriptions/ \
  -H "Authorization: Bearer $TOKEN" \
  -H 'X-Tenant-Slug: acme-demo'

curl -sS http://localhost:8000/api/invoices/ \
  -H "Authorization: Bearer $TOKEN" \
  -H 'X-Tenant-Slug: acme-demo'

curl -sS http://localhost:8000/api/usage/ \
  -H "Authorization: Bearer $TOKEN" \
  -H 'X-Tenant-Slug: acme-demo'
```

## Ingest metered usage

Use the seeded subscription and metric IDs returned by the APIs. Keep the idempotency key stable
when retrying the same logical event.

```bash
curl -sS http://localhost:8000/api/usage/events/ \
  -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H 'X-Tenant-Slug: acme-demo' \
  -H 'Content-Type: application/json' \
  -d '{"subscription_id":1,"metric_id":1,"quantity":250,"idempotency_key":"demo-cli-001"}'
```

## Provider behavior in the demo

The local usage ledger, aggregation, and dashboard work with the placeholder Stripe credentials.
Asynchronous meter synchronization will be marked `failed` until `STRIPE_SECRET_KEY` is replaced
with a valid Stripe test-mode key. Signed webhook ingestion additionally requires a matching
`STRIPE_WEBHOOK_SECRET`.

## API discovery and Admin

Visit `http://localhost:8000/api/docs/` or `http://localhost:8000/api/redoc/` for interactive API
documentation. The demo owner is intentionally not a Django staff user. Create an operational
Admin account before opening `http://localhost:8000/admin/`:

```bash
docker compose exec api python manage.py createsuperuser
```
