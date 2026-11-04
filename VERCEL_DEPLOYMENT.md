# Hosting the ApplyTrack web frontend on Vercel

The web frontend is in `frontend/`. The FastAPI service and PostgreSQL database are separate services; Vercel will host the Next.js frontend, not the API or database.

## Before deploying

1. Push this repository to GitHub.
2. Deploy the FastAPI API to a Python-capable host and attach managed PostgreSQL. The local SQLite database is for development only.
3. Set the API host's `DATABASE_URL`, `SESSION_TOKEN_PEPPER` (unique random secret), `APP_ENV=production`, and `CORS_ORIGINS` to your exact Vercel origin, such as `https://your-project.vercel.app`.
4. Run `alembic upgrade head` against the production database as part of the API release.

## Vercel project settings

- Import the GitHub repository in Vercel.
- Set **Root Directory** to `frontend`.
- Framework preset: **Next.js**.
- Add environment variable `NEXT_PUBLIC_API_BASE_URL` with the API URL ending in `/api/v1`, for example `https://api.example.com/api/v1`.
- Deploy. Redeploy whenever this public environment variable changes.

The API must allow the deployed frontend origin in `CORS_ORIGINS`. Do not use `*` with credentials. This frontend uses bearer tokens and does not send cross-origin cookies.

## Local frontend

From `frontend/`:

```sh
npm install
cp .env.example .env.local
npm run dev
```

On Windows PowerShell, replace the copy command with `Copy-Item .env.example .env.local`. The local API should be running at `http://127.0.0.1:8000`.

The repository includes an ignored `frontend/.env.local` for this local API URL. Keep it out of Git; set the production API URL in Vercel's project environment instead.

## Current scope and production work

Authentication, editable profile, master resume upload/extraction, manual jobs, deterministic job matching, tailored resume downloads, application status/timeline, dashboard metrics, and integration status call the real API. Gmail and Calendar require Google OAuth credentials on the API; without them the UI reports setup required. Google sync pages only render actual imported records. Portal automation, AI-provider features, submission automation, extension, Android, billing, and admin remain unimplemented.

The current browser session token is held in `localStorage` to survive refreshes. Before public launch, move this session to a same-site secure HttpOnly cookie via a backend-for-frontend or a reviewed cookie-based API design, and add CSRF protections, email verification, password recovery, abuse/rate limits, and production monitoring. Never use a real production database URL in a public Vercel environment variable.
