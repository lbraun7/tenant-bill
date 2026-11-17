# Scaling and Production Trade-offs

TenantBill optimizes for a locally runnable portfolio demonstration while preserving the invariants
that matter in a real billing system. This document separates intentional first-version choices
from changes that would become valuable with more tenants, traffic, or operational requirements.

## Shared-schema tenancy

**Current choice:** all tenants share one database schema, and tenant ownership is explicit on
billing records.

**Why it fits:** local setup, migrations, analytics, and operational inspection remain simple. API
boundaries and cross-tenant tests make the primary risk visible.

**At larger scale:** add database-level row security, tenant-aware repository abstractions, and
automated checks for unscoped queries. Regulatory or high-isolation customers may justify separate
databases, but that adds migration orchestration, connection routing, and fleet management.

## Usage aggregation

**Current choice:** current-period usage is calculated from the append-only ledger with database
aggregation.

**Why it fits:** every total remains explainable and recomputable, and no secondary counter can
drift from its source events.

**At larger scale:** retain the immutable ledger but introduce incremental rollups by tenant,
subscription, metric, and billing period. Reconciliation jobs should compare rollups with ledger
totals before financial use.

## Task delivery and transactional publication

**Current choice:** Celery uses Redis, and tasks that depend on writes are published with
`transaction.on_commit()`.

**Why it fits:** it prevents workers from observing uncommitted rows and keeps the local stack easy
to operate.

**At larger scale:** use a transactional outbox so a broker outage cannot lose work after the
database commit. A managed queue with dead-letter handling, delivery metrics, and explicit task
deduplication would improve recovery guarantees.

## Webhook recovery

**Current choice:** webhook records retain status, attempts, payload, and errors; workers use row
locks and bounded retries.

**Why it fits:** duplicate delivery is safe and ordinary failures remain inspectable.

**At larger scale:** add a lease or heartbeat to `processing`, reclaim abandoned events after a
timeout, provide an audited replay command, and alert on event age and failure rate. Provider-side
reconciliation should detect events that were never delivered.

## Local financial projection

**Current choice:** subscription and invoice state is projected locally from Stripe events.

**Why it fits:** API reads are fast, invoice lines are auditable, and tests do not require provider
network access.

**At larger scale:** schedule reconciliation against Stripe, record projection versions, preserve
event-to-aggregate causality, and define conflict rules. Stripe remains the payment source of truth;
the local model remains the application's operational view.

## Authorization

**Current choice:** active tenant membership grants access, while owner, admin, and member roles are
stored but do not yet change API permissions.

**Why it fits:** the project demonstrates tenant isolation without hiding it behind a large policy
framework.

**At larger scale:** introduce action-level RBAC, centralize authorization policies, test each
role-resource-action combination, and retain audit records for privileged financial changes.

## Storage and generated documents

**Current choice:** Django's storage abstraction writes invoice PDFs to the local filesystem.

**Why it fits:** generation is easy to run and verify locally, while domain code remains independent
from the storage backend.

**At larger scale:** use private object storage, short-lived signed downloads, encryption and
retention policies, background malware scanning where relevant, and immutable document versioning.

## Observability

**Current choice:** JSON logs and searchable Django Admin records expose provider IDs, task state,
and retained errors.

**At larger scale:** add metrics, traces, correlation IDs, SLOs, dashboards, and alerts for webhook
lag, queue depth, usage sync failure, invoice projection drift, and cross-tenant authorization
denials.
