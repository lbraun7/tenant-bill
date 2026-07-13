# Architecture Decisions

## Multi-tenancy

Use shared schema multi-tenancy with explicit `tenant_id` ownership in domain tables.

This keeps the project easy to run locally while still demonstrating production-minded tenant
isolation.

## Stripe Boundary

Stripe calls should be isolated under `apps/integrations/stripe/`. Domain services and API views
should depend on that boundary instead of calling the Stripe SDK directly.

Webhook signature verification therefore lives in the Stripe integration package. The webhook app
owns persistence, idempotency, asynchronous dispatch, retry state, and domain handlers.

## Webhook idempotency

Persist Stripe events before dispatch and enforce a unique external event ID. Tasks lock and claim
the persisted event, while terminal `processed` and `ignored` states are no-ops on repeated task
delivery. Broker publication happens after commit and is timestamped; if publication fails, a later
Stripe delivery can safely try to publish the still-received event again.
