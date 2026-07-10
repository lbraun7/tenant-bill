# API

OpenAPI schema will be available at `/api/schema/` and Swagger UI at `/api/docs/`.

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
- `GET /api/usage-events/`
- `POST /api/usage-events/`
- `GET /api/usage-events/{id}/`
