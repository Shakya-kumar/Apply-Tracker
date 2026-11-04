# ApplyTrack architecture

## Current shape

The system starts as a modular monolith: one FastAPI process, one PostgreSQL database, and Redis reserved for background work. The API owns identity and tenant membership. Each newly registered user receives a private tenant. Domain modules will use the authenticated user's membership context for tenant-scoped queries.

## Phase 1 data model

- `users`: unique normalized email, Argon2 password hash, account state, verification timestamp.
- `tenants`: workspace boundary.
- `memberships`: user-to-tenant relationship and role.
- `user_sessions`: keyed digest of an opaque random bearer token, expiration and revocation timestamps.

Raw session tokens are returned once and never persisted. Token digests use an HMAC pepper configured outside the codebase. Passwords use the recommended Argon2 configuration from `pwdlib`.

## Request flow

The `/api/v1` router owns public API contracts. Authentication dependencies resolve a valid session and user. Database sessions are request-scoped. Alembic is the only schema change path; application startup does not create tables implicitly.

## Planned modules

Career profile and resume processing, job sources and company career adapters, matching, applications and immutable documents, integrations, notifications, and administration will be added as separate domain modules in later phases. Third-party integrations must expose capability and health state based on actual provider support.

## Deployment boundary

Compose is a local development stack, not production deployment configuration. Production requires managed secrets, TLS, hardened database/Redis networking, object storage, backups, observability, and reviewed OAuth provider configuration.
