# Architecture Decisions

## Multi-tenancy

Use shared schema multi-tenancy with explicit `tenant_id` ownership in domain tables.

This keeps the project easy to run locally while still demonstrating production-minded tenant
isolation.

## Stripe Boundary

Stripe calls should be isolated under `apps/integrations/stripe/`. Domain services and API views
should depend on that boundary instead of calling the Stripe SDK directly.
