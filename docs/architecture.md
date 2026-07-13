# Architecture

TenantBill is a Django REST Framework backend for a multi-tenant SaaS billing platform.

The first implementation uses a shared database and shared schema. Domain records will carry
tenant ownership explicitly, and API boundaries will enforce tenant isolation through querysets,
permissions, and tests.

## Stripe webhook flow

The webhook HTTP boundary validates Stripe's signature against the raw body, then persists the
event under its globally unique Stripe event ID. A Celery task is published only after the database
transaction commits. Publishing is tracked so that a Stripe redelivery can recover from a broker
failure without processing an event twice.

The worker claims the event under a database lock and applies its domain handler in a transaction.
Successful known events become `processed`, unsupported events become `ignored`, and failures become
`failed` with the error retained for operations. Celery retries failures with exponential backoff.
