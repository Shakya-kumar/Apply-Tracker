# ApplyTrack

ApplyTrack is being built as a phased job-search platform. The current working web/backend slice includes account authentication, editable career profiles/preferences, master resume upload and text extraction, manual job management, rule-based matching, tailored resume exports, application timelines, database-backed dashboard metrics, and Google OAuth connections for Gmail metadata and Calendar events.

## Local setup

1. Copy `.env.example` to `.env` and replace `SESSION_TOKEN_PEPPER` with a long random secret.
2. Start the stack with `docker compose up --build`.
3. Open the API documentation at <http://localhost:8000/docs>.
4. Check service liveness at <http://localhost:8000/health>.

The API container applies Alembic migrations before starting. The included database credentials are for local development only.

## Web and API

The Next.js application is in `frontend/`. See [LOCAL_SETUP.md](LOCAL_SETUP.md) to run both services and [VERCEL_DEPLOYMENT.md](VERCEL_DEPLOYMENT.md) for Vercel hosting.

## Current API

- `POST /api/v1/auth/register` — create an account and private tenant.
- `POST /api/v1/auth/login` — start a session.
- `POST /api/v1/auth/logout` — revoke the current session.
- `GET /api/v1/auth/me` — read the authenticated account.
- `GET|PUT /api/v1/profile` — read/save profile, education, experience, projects, skills, and preferences.
- `POST /api/v1/resume` — upload and extract text from one PDF/DOCX master resume.
- `GET|POST /api/v1/jobs` — list/search and add jobs manually.
- `GET /api/v1/jobs/{id}/match` — rule-based profile match.
- `POST /api/v1/jobs/{id}/resume-versions` — generate immutable DOCX/PDF files from verified profile information.
- `GET|POST|PATCH /api/v1/applications` — track application status and timeline.
- `GET /api/v1/dashboard` — database-backed workspace metrics.
- `/api/v1/integrations/*` — Google OAuth, Gmail metadata review, and Calendar event sync (requires Google OAuth configuration).

The registration flow requires a 12-character password minimum. Email verification and password recovery are not implemented. Resume extraction is text-only; matching is deterministic and no AI provider is configured. Job portals are manually assisted; application submission is not automated. Gmail sync imports metadata only and requires user confirmation before updating a tracked application. Calendar sync imports event metadata. Chrome extension, Android, billing, and admin features remain future phases and are not represented as connected.

## Structure

- `app/api` — versioned HTTP routes.
- `app/core` — process configuration.
- `app/models.py` — SQLAlchemy persistence models.
- `migrations` — Alembic schema history.
- `docker-compose.yml` — local API, PostgreSQL, and Redis.

## Development

For a local Python environment, install `requirements.txt`, run `alembic upgrade head`, then `uvicorn app.main:app --reload`. Without a `.env`, local development uses `./applytrack.db` (SQLite). To use PostgreSQL locally, set `DATABASE_URL`; Docker Compose uses PostgreSQL from `.env.example`.

Redis is provisioned for the planned worker and cache phases; no background jobs use it yet. Do not expose the development compose credentials to the internet.
