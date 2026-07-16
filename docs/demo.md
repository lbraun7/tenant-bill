# Demo Walkthrough

Run `make migrate && make seed && make runserver`. The seed is idempotent and creates an active
subscription, metered usage, and a paid invoice for `acme-demo`.

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

Visit `/api/docs/`, `/api/redoc/`, and `/admin/` to show API discovery and operational debugging.
