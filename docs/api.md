# API

OpenAPI schema is available at `/api/schema/`, Swagger UI at `/api/docs/`, and Redoc at
`/api/redoc/`.

Authenticated domain endpoints are scoped to the current tenant. Send `X-Tenant-Slug` to select
a tenant explicitly, or omit it to use the user's first active membership.

## Auth

- `POST /api/auth/register/`
- `POST /api/auth/login/`
- `POST /api/auth/refresh/`

## Tenants

- `GET /api/tenants/`
- `GET /api/tenants/{slug}/`
- `PATCH /api/tenants/{slug}/`
- `GET /api/tenants/me/`
- `PATCH /api/tenants/me/`

## Billing Domain

- `GET /api/plans/`
- `POST /api/plans/`
- `GET /api/plans/{slug}/`
- `PATCH /api/plans/{slug}/`
- `GET /api/subscriptions/`
- `POST /api/subscriptions/`
- `GET /api/subscriptions/{id}/`
- `PATCH /api/subscriptions/{id}/`
- `GET /api/invoices/`
- `GET /api/invoices/{id}/`
- `GET /api/invoices/{id}/pdf/`
- `GET /api/usage-events/`
- `POST /api/usage-events/`
- `GET /api/usage-events/{id}/`

## Stripe Webhooks

- `POST /webhooks/stripe/`

This public endpoint authenticates the raw request with the `Stripe-Signature` header. New events
return `202 Accepted`; already persisted event IDs return `200 OK`. Invalid signatures or malformed
Stripe events return `400 Bad Request`.

Invoice endpoints are read-only. Stripe invoice webhooks create or update the local financial
history and enqueue PDF generation. Until generation finishes, the detail response has a null
`pdf_url` and the PDF endpoint returns `404`.

## Operations

- `GET /health/` is an unauthenticated liveness endpoint.
- `GET /api/schema/` returns the generated OpenAPI document.
- `GET /api/docs/` and `GET /api/redoc/` render interactive API documentation.
