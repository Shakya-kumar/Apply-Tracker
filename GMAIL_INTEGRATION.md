# Gmail and Google Calendar connections

The app supports explicit Google OAuth connections for Gmail message metadata and Google Calendar event metadata. The OAuth callback uses a single-use state value and PKCE; access and refresh tokens are encrypted with `TOKEN_ENCRYPTION_KEY`. The Gmail permission is `gmail.metadata`, and the Calendar permission is `calendar.events.readonly`.

## Configure Google Cloud

1. Create a Google Cloud project and configure the OAuth consent screen for the intended audience.
2. Create an OAuth client with application type **Web application**.
3. Add the API callback as an authorized redirect URI: `https://YOUR_API_HOST/api/v1/integrations/google/callback` (local default: `http://localhost:8000/api/v1/integrations/google/callback`).
4. Set `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`, `FRONTEND_URL`, and a stable Fernet `TOKEN_ENCRYPTION_KEY` on the API host. Never place the client secret or encryption key in Vercel frontend variables.
5. Ensure the consent screen allows the Gmail metadata and Calendar readonly scopes. For an OAuth app in testing mode, add each test user in Google Cloud.
6. Restart/redeploy the API. Connected apps should show Gmail and Calendar as available.

The user starts authorization from **Connected apps**. Gmail sync fetches up to 50 recent messages and stores sender, subject, date, and a heuristic category; it does not request message bodies. A user must select a tracked application and confirm a proposed status before ApplyTrack records it. Calendar sync stores event title, organizer, and time for a bounded date range. Sync is explicit and deduplicated. Disconnect attempts Google revocation and deletes imported data for that service.

Provider authorization or quota errors can interrupt synchronization; reconnect from Connected apps if the integration reports that it needs attention. Google OAuth has not been configured in this development environment, so the UI correctly reports `setup required` until credentials are supplied.
