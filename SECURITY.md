# Security notes

- Passwords are hashed with Argon2; API responses do not include hashes.
- Sessions use high-entropy opaque bearer tokens. Only peppered digests are stored, and logout revokes the current token.
- `SESSION_TOKEN_PEPPER` must be a unique high-entropy secret outside source control. Rotating it invalidates existing sessions.
- Configure CORS with explicit trusted origins.
- Compose credentials are development-only.
- Email verification, password reset, rate limiting, audit logging, production TLS, and secret rotation procedures remain required before public deployment.
- Never store job-portal passwords, cookies, or session tokens. Integration credentials require provider-scoped OAuth and encryption at rest in a later phase.
