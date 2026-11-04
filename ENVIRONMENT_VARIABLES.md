# Environment variables

| Variable | Required | Purpose |
|---|---|---|
| `APP_ENV` | No | `development` or `production`; production rejects the default session pepper. |
| `APP_NAME` | No | OpenAPI service title. |
| `API_V1_PREFIX` | No | Versioned API base path. |
| `DATABASE_URL` | No locally; yes in production | SQLAlchemy URL. Default local DB is SQLite; deploy with managed PostgreSQL. |
| `REDIS_URL` | No yet | Reserved for planned background tasks. |
| `SESSION_TTL_DAYS` | No | Session lifetime; default 30. |
| `SESSION_TOKEN_PEPPER` | Yes in production | Long random secret used to HMAC session token digests. |
| `CORS_ORIGINS` | Yes for hosted web | Comma-separated exact frontend origins, e.g. `https://applytrack.vercel.app`. |
| `UPLOAD_DIR` | No locally; configure for API host | Private persistent location for uploaded and generated documents. Current implementation uses local filesystem storage. |
| `NEXT_PUBLIC_API_BASE_URL` | Yes in Vercel | Public API origin ending in `/api/v1`. Never put secrets in a `NEXT_PUBLIC_` variable. |
| `GOOGLE_CLIENT_ID` | For Gmail/Calendar OAuth | Google Cloud OAuth web client ID. |
| `GOOGLE_CLIENT_SECRET` | For Gmail/Calendar OAuth | Server-only OAuth client secret. Never expose to the browser. |
| `GOOGLE_REDIRECT_URI` | For OAuth | Must exactly match the authorized Google OAuth redirect URI. |
| `FRONTEND_URL` | For OAuth callback | Frontend origin used after the Google consent callback. |
| `TOKEN_ENCRYPTION_KEY` | For storing OAuth tokens | Fernet-compatible key; generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`. Keep stable and private; losing it makes stored tokens unreadable. |

Email delivery, AI provider, object storage, billing, and mobile push credentials are not consumed by this code yet. Google OAuth variables are consumed by the Gmail/Calendar connection flow.
