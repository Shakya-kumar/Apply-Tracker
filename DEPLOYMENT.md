# Deployment status and release outline

The frontend can be deployed to Vercel from the `frontend` root directory. Configure `NEXT_PUBLIC_API_BASE_URL` to a separately deployed API URL ending in `/api/v1` and configure backend `CORS_ORIGINS` with the Vercel origin. See `VERCEL_DEPLOYMENT.md`.

The FastAPI API must run on a Python-capable host with managed PostgreSQL and persistent private document storage. Run Alembic migrations during API release. `docker-compose.yml` is local development infrastructure, not a production deployment. Do not deploy SQLite/local file storage for multi-instance production.

No production domain, managed database, storage account, OAuth provider, or live deployment has been configured or verified. Production still needs HTTPS, secrets management, backups/restore testing, rate limits, monitoring, secure cookie-based sessions, email verification/recovery, and privacy/account deletion workflows.
