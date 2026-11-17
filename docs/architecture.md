# Architecture

TenantBill is a Django REST Framework backend for a multi-tenant SaaS billing platform.

The application uses a shared database and shared schema. Domain records carry tenant ownership
explicitly, and API boundaries enforce tenant isolation through querysets, permissions, and tests.

## Stripe webhook flow

The webhook HTTP boundary validates Stripe's signature against the raw body, then persists the
event under its globally unique Stripe event ID. A Celery task is published only after the database
transaction commits. Publishing is tracked so that a Stripe redelivery can recover from a broker
failure without processing an event twice.

The worker claims the event under a database lock and applies its domain handler in a transaction.
Successful known events become `processed`, unsupported events become `ignored`, and failures become
`failed` with the error retained for operations. Celery retries failures with exponential backoff.

## Domain flows

Subscriptions are tenant-owned local projections of Stripe state. Invoice webhooks update the
financial history and publish PDF generation only after the database transaction commits. Usage is
an immutable ledger: every API-accepted event carries tenant ownership and a required,
tenant-scoped idempotency key, while Stripe meter synchronization runs asynchronously.

The HTTP API resolves the active tenant from `X-Tenant-Slug` (or the user's first active
membership), and domain querysets are always narrowed to it. Django Admin exposes tenant, provider
IDs, processing status, and retained errors for operational investigation.
