# Architecture Decisions

## Multi-tenancy

Use shared schema multi-tenancy with explicit `tenant_id` ownership in domain tables.

This keeps the project easy to run locally while still demonstrating production-minded tenant
isolation.

The trade-off is that every domain query must be tenant-scoped. This is enforced at API boundaries
and tested with cross-tenant access attempts. Schema-per-tenant was rejected for the first version
because it would add migration and connection-management complexity without improving the portfolio
demonstration proportionally.

## Stripe Boundary

Stripe calls should be isolated under `apps/integrations/stripe/`. Domain services and API views
should depend on that boundary instead of calling the Stripe SDK directly.

Webhook signature verification therefore lives in the Stripe integration package. The webhook app
owns persistence, idempotency, asynchronous dispatch, retry state, and domain handlers.

This boundary makes provider behavior mockable and prevents Stripe SDK exceptions from becoming
part of the domain API. The local database remains the application's operational projection, while
Stripe remains the external source of payment truth.

## Webhook idempotency

Persist Stripe events before dispatch and enforce a unique external event ID. Tasks lock and claim
the persisted event, while terminal `processed` and `ignored` states are no-ops on repeated task
delivery. Broker publication happens after commit and is timestamped; if publication fails, a later
Stripe delivery can safely try to publish the still-received event again.

## Usage as an immutable ledger

Usage is stored as append-only events instead of a mutable counter. Tenant-scoped idempotency keys
reject duplicate ingestion, and totals are derived for a billing period. This costs more rows and
aggregation work, but preserves auditability and allows totals to be recomputed after a bug fix.

## Asynchronous side effects

Celery handles webhook processing, usage synchronization, and invoice PDF generation. Tasks are
published with `transaction.on_commit()` whenever they depend on newly committed data. Retriable
operations record their state or error so operators can distinguish a broker failure from a domain
mapping problem.

## Invoice terminology and storage

The generated document is called an invoice, not a tax invoice or Brazilian *nota fiscal*, because
there is no fiscal authority integration. Django's storage abstraction keeps local development
simple while allowing an S3-compatible backend in production without changing domain code.
