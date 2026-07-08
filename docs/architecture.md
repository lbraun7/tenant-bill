# Architecture

TenantBill is a Django REST Framework backend for a multi-tenant SaaS billing platform.

The first implementation uses a shared database and shared schema. Domain records will carry
tenant ownership explicitly, and API boundaries will enforce tenant isolation through querysets,
permissions, and tests.
