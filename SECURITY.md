# Security Policy

TenantBill is a portfolio project that demonstrates security-conscious patterns for a
multi-tenant billing backend. It is not offered as a hosted service and has not undergone an
independent security audit.

## Reporting a vulnerability

Please do not disclose suspected vulnerabilities in a public issue. Use the repository's private
GitHub security advisory flow instead:

1. Open the repository's **Security** tab.
2. Select **Report a vulnerability**.
3. Include affected endpoints or components, reproduction steps, impact, and any suggested fix.

Reports involving cross-tenant access, authentication bypass, webhook signature verification,
financial duplication, or secret exposure are especially important.

## Security model

The implementation demonstrates the following controls:

- JWT authentication for protected API endpoints.
- Explicit tenant resolution through an active membership and `X-Tenant-Slug`.
- Tenant-scoped querysets and writable relationships at API boundaries.
- Cross-tenant isolation tests for list, retrieve, and write operations.
- Stripe webhook verification against the raw signed request body.
- Unique provider event IDs and tenant-scoped usage idempotency keys.
- Database transactions and row locking around webhook processing.
- Environment-based configuration for secrets and provider credentials.
- Structured operational records for retained failures and retry investigation.

## Demo and production boundaries

The seeded account and credentials are intentionally public and must never be reused in a real
deployment. `.env.example` contains placeholders only. Production deployments should provide a
strong `SECRET_KEY`, real Stripe test or live credentials as appropriate, restricted hosts and
CORS origins, TLS termination, secure storage, and managed database and queue services.

The portfolio dashboard stores its access token in `localStorage` and hardcodes the demo tenant.
Those choices keep the demonstration small; a production client should use a hardened session
strategy, refresh or rotation behavior, and a real tenant-selection flow.

## Known security limitations

- Membership roles are modeled but role-based authorization is not yet enforced on write actions.
- There is no rate limiting or abuse protection on authentication and ingestion endpoints.
- Webhook events do not yet have a timeout-based recovery process for workers terminated while an
  event is marked `processing`.
- Secret rotation, audit-log retention policy, and production infrastructure hardening are outside
  this repository's current scope.
- Dependency and container vulnerability scanning are not currently part of CI.

See [Architecture decisions](docs/decisions.md) and
[Scaling trade-offs](docs/tradeoffs.md) for related design context.
