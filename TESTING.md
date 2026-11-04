# Tests and checks

Run backend tests:

```powershell
python -m pytest tests -q
```

Run schema migration checks:

```powershell
python -m alembic upgrade head
python -m alembic check
```

Run frontend type-check and production build:

```powershell
cd frontend
npm ci
npm run typecheck
npm run build
```

The current API tests cover registration/session revocation, profile isolation, resume upload/download isolation, job and application events, dashboard counts, truthful integration states, matching, and immutable resume export/linking. No tests submit real applications or contact external providers.
