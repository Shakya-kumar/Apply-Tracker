# Local setup

## Requirements

- Python 3.12 or newer.
- Node.js 20.9 or newer and npm.
- Docker Desktop only if you want the Compose PostgreSQL/Redis services.

## API with local SQLite

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m alembic upgrade head
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Without a root `.env`, the API uses `./applytrack.db` and stores private local resume files under `./uploads`.

## Web frontend

```powershell
cd frontend
npm ci
npm run dev
```

`frontend/.env.local` sets `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1`. Open <http://localhost:3000>. The root `.env.example` is for the API/Compose stack; frontend deployment variables are documented in `VERCEL_DEPLOYMENT.md`.

## Compose stack

At repository root, copy `.env.example` to `.env`, replace the pepper, then run `docker compose up --build`. Compose uses PostgreSQL and Redis. Its credentials are development-only.
