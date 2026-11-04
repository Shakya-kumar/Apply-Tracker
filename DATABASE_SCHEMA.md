# Database schema

Phase 1 migrations create `users`, `tenants`, `memberships`, and `user_sessions`. Foreign keys cascade on account/workspace deletion; membership pairs and emails are unique. Session tokens are stored only as keyed SHA-256 digests and carry expiry and revocation timestamps.

Run `alembic upgrade head` to apply schema changes and `alembic downgrade -1` to revert one revision. Add all future schema changes as migrations; do not use metadata `create_all` in deployed environments.
