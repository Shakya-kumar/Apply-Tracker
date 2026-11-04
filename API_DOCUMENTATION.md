# API reference

OpenAPI UI is served at `/docs`; the JSON schema is `/openapi.json`. API routes use `/api/v1` and bearer sessions returned by registration/login.

## Identity

- `POST /auth/register` — create an account, private workspace, and session.
- `POST /auth/login` — verify credentials and start a session.
- `POST /auth/logout` — revoke the presented session.
- `GET /auth/me` — return the current account.

## Career workspace

- `GET /profile`, `PUT /profile` — read/save personal details, skills, education, experience, projects, and search preferences. PUT replaces the editable profile collections with the submitted form.
- `GET /resume`, `POST /resume`, `GET /resume/extracted-text`, `GET /resume/download`, `DELETE /resume` — manage one master PDF/DOCX file. Upload is limited to 8 MB. Text extraction is deterministic and does not fill the profile automatically.
- `GET /jobs?q=&saved=` — list/search the account's manually added jobs.
- `POST /jobs` — add a job from user-provided details.
- `PATCH /jobs/{id}/saved?saved=true|false` — save or unsave.
- `GET /jobs/{id}/match` — calculate a rule-based match estimate against the profile.
- `POST /jobs/{id}/resume-versions`, `GET /jobs/{id}/resume-versions` — create/list immutable job-specific DOCX/PDF versions from verified profile facts.
- `GET /resume-versions/{id}/download?format=pdf|docx` — download an owned generated version.
- `GET /applications`, `POST /applications`, `PATCH /applications/{id}`, `POST /applications/{id}/events` — track statuses, associate a resume version, and append notes/status events.
- `GET /dashboard` — database counts and onboarding state for this account.
- `GET /integrations/status` — actual implemented/configured capabilities.
- `POST /integrations/google/start?service=gmail|calendar` — start Google OAuth for one service.
- `GET /integrations/google/callback` — Google OAuth callback (provider redirect).
- `POST /integrations/gmail/sync`, `GET /integrations/gmail/events`, `POST /integrations/gmail/events/{id}/confirm` — sync metadata and review an email-derived application status.
- `POST /integrations/calendar/sync`, `GET /integrations/calendar/events`, `DELETE /integrations/gmail|calendar` — sync event metadata or disconnect and remove imported records.

All job, profile, resume, and application queries are scoped to the authenticated user. Mutations validate ownership before writing.
