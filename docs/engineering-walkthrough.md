# Engineering Walkthrough

This guide gives reviewers a short path through the parts of TenantBill that carry the most design
value. The complete demo can be run from the repository [Quick start](../README.md#quick-start).

## One-minute overview

TenantBill is a multi-tenant SaaS billing backend built around three invariants:

1. A request must never read or write another tenant's billing data.
2. Retried usage and provider events must not duplicate financial effects.
3. External failures must remain observable and recoverable instead of disappearing from the
   request path.

The system uses Django REST Framework and PostgreSQL for the domain model, Redis and Celery for
asynchronous work, Stripe behind an integration boundary, and a small Next.js dashboard for the
demonstration.

## Suggested code tour

### 1. Start with tenant isolation

- [`apps/tenants/selectors.py`](../apps/tenants/selectors.py) resolves the active membership.
- [`apps/tenants/permissions.py`](../apps/tenants/permissions.py) attaches the tenant to the request.
- [`tests/test_tenant_isolation.py`](../tests/test_tenant_isolation.py) proves cross-tenant denial.

Look for the same `request.current_tenant` constraint in plans, subscriptions, usage, and invoices.

### 2. Follow a usage event

- [`apps/usage/serializers.py`](../apps/usage/serializers.py) validates tenant ownership, billing
  period, and idempotency before inserting an event.
- [`apps/usage/models.py`](../apps/usage/models.py) defines the immutable ledger and synchronization
  state.
- [`apps/usage/tasks.py`](../apps/usage/tasks.py) sends the meter event through the Stripe boundary.
- [`apps/usage/views.py`](../apps/usage/views.py) derives current totals from the ledger.

The important distinction is between accepting usage locally and synchronizing it externally. A
provider failure does not erase the accepted ledger entry; it changes observable sync state.

### 3. Follow a Stripe webhook

- [`apps/webhooks/views.py`](../apps/webhooks/views.py) authenticates and persists the event before
  dispatch.
- [`apps/webhooks/tasks.py`](../apps/webhooks/tasks.py) claims the event under a database lock and
  records terminal or failed state.
- [`apps/webhooks/handlers.py`](../apps/webhooks/handlers.py) maps provider events to domain changes.
- [`tests/test_stripe_webhooks.py`](../tests/test_stripe_webhooks.py) covers duplicates, broker
  failure, retries, unknown events, and handler behavior.

This flow is intentionally durable before it is asynchronous: returning an HTTP response does not
make the only copy of the work disappear into a queue.

### 4. Inspect the financial projection

- [`apps/billing/services.py`](../apps/billing/services.py) projects invoices and auditable lines.
- [`apps/billing/tasks.py`](../apps/billing/tasks.py) generates PDFs outside the request path.
- [`apps/billing/views.py`](../apps/billing/views.py) serves tenant-scoped, read-only invoice data.

The local projection supports fast reads and operational investigation while Stripe remains the
external source of payment truth.

## Useful discussion questions

- Why use shared-schema tenancy instead of one schema or database per tenant?
- Why store usage events instead of incrementing a counter?
- What does `transaction.on_commit()` protect, and what does it not protect?
- How does the webhook flow behave if Stripe sends the same event twice?
- What happens if a worker dies after claiming an event?
- When would a transactional outbox become necessary?
- How would usage aggregation change at millions of events per billing period?
- Which write operations should require owner or admin role?

The answers and next-step designs are summarized in
[Architecture decisions](decisions.md) and [Scaling and production trade-offs](tradeoffs.md).

## Honest project boundaries

TenantBill demonstrates billing infrastructure, not a complete commercial billing product. It does
not create Stripe Checkout sessions, calculate overage pricing, provide a customer portal, issue
jurisdiction-specific fiscal documents, or define production cloud infrastructure. Those omissions
keep the repository focused on isolation, idempotency, auditability, and asynchronous correctness.
