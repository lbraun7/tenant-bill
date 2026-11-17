# Testing Strategy

The suite concentrates on failure modes that are expensive in a billing SaaS: tenant data leakage,
duplicate financial events, inconsistent provider state, and non-auditable usage.

## Test layers

- API tests prove authentication, tenant selection, permissions, serialization, and HTTP behavior.
- Domain tests cover invoice synchronization, immutable usage, billing periods, and totals.
- Webhook tests cover invalid signatures, duplicate delivery, asynchronous publication, retries,
  terminal states, and Stripe event handlers.
- Operational tests validate the demo seed, structured log context, and generated API docs.
- Frontend rendered-HTML tests verify the public sign-in experience and its API integration
  contract after a production build.

Tests use SQLite in memory for fast feedback. PostgreSQL remains the production database and Docker
Compose supplies it for local integration work. External Stripe calls and Celery dispatch are
mocked at their boundaries; Celery runs eagerly under test settings.

## Commands

```bash
make test
make coverage
poetry run pytest tests/test_stripe_webhooks.py -q
poetry run pytest tests/test_tenant_isolation.py -q
cd frontend && npm run lint && npm test
```

`make coverage` enforces 90% branch-aware coverage and writes an HTML report to `htmlcov/`. CI
applies the same threshold and uploads `coverage.xml` as a build artifact. Coverage is a regression
guard, not a substitute for assertions around billing invariants.

GitHub Actions runs backend and frontend checks as separate jobs. The frontend job uses Node.js
22.13, runs ESLint, builds the Vinext application, and executes the Node test suite.
