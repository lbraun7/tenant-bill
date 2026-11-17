# TenantBill Dashboard

The TenantBill frontend is a small portfolio dashboard for exploring the billing backend. It signs
in through the Django JWT API, loads the selected tenant's subscription, usage, and invoices, and
can submit idempotent usage events.

## Stack

- Next.js 16 and React 19
- TypeScript
- Tailwind CSS 4
- Vinext and Vite for the local and Cloudflare-compatible build

## Requirements

- Node.js 22.13 or newer
- TenantBill API running at `http://localhost:8000`, or a custom API URL
- Demo data created with `python manage.py seed_demo`

## Run locally

```bash
npm ci
npm run dev
```

Open `http://localhost:3000` and sign in with:

```text
Email:    demo@tenantbill.local
Password: demo-password
Tenant:   acme-demo
```

The API URL defaults to `http://localhost:8000`. Override it when needed:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

## How it connects to the backend

The dashboard obtains a JWT access token from `/api/auth/login/` and sends it with
`X-Tenant-Slug: acme-demo` to tenant-scoped endpoints. The token is kept in `localStorage` for this
portfolio demo. A production client should prefer a hardened session strategy and implement access
token refresh.

The interface currently focuses on one deterministic demo tenant. Tenant selection, plan
management, checkout creation, and customer self-service are outside the dashboard's scope.

## Commands

```bash
npm run dev      # start the development server
npm run lint     # run ESLint
npm run build    # create a production build
npm test         # build and execute the rendered HTML test suite
```

The repository retains optional Cloudflare D1, Drizzle, and ChatGPT authentication scaffolding from
the hosting template, but the TenantBill dashboard does not depend on those features.
