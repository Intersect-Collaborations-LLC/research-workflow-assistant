# 17 - Local Development And Deployment

## Purpose

Document how to run the full RWA web stack locally and how to deploy the
hosted version. The stack includes FastAPI, Next.js, the worker process, the
application database, project storage, GitHub OAuth, and environment variables.

## Scope

This guide covers:

- Local startup commands.
- Environment files.
- Database setup and migrations.
- Storage configuration.
- GitHub OAuth callback setup.
- Worker process startup.
- Hosted deployment assumptions.
- Operational checks.

## Local Components

Local development runs:

```text
FastAPI backend
Next.js frontend
SQLAlchemy database
Project storage provider
Worker process
GitHub OAuth app
```

Redis or another external queue service is not required for the first
prototype.

## Backend Setup

From:

```powershell
cd web/backend
```

Install:

```powershell
pip install -e .
```

Run migrations:

```powershell
alembic upgrade head
```

Start API:

```powershell
uvicorn rwa_web.main:app --reload
```

Expected health check:

```text
http://localhost:8000/health
```

## Frontend Setup

From:

```powershell
cd web/frontend
```

Install:

```powershell
npm install
```

Start:

```powershell
npm run dev
```

Default URL:

```text
http://localhost:3000
```

## Worker Setup

From:

```powershell
cd web/backend
```

Start:

```powershell
python -m rwa_web.jobs.worker
```

The worker should use the same environment configuration as the API process.

## Local Environment

Create:

```text
web/backend/.env
web/frontend/.env
```

Backend example:

```text
RWA_WEB_ENVIRONMENT=local
RWA_WEB_DEBUG=true
RWA_WEB_DATABASE_URL=sqlite:///./rwa-web.db
RWA_WEB_STORAGE_URL=file://./rwa-web-data
RWA_WEB_SESSION_SECRET=replace-with-a-random-development-secret

RWA_WEB_GITHUB_CLIENT_ID=
RWA_WEB_GITHUB_CLIENT_SECRET=
RWA_WEB_GITHUB_CALLBACK_URL=http://localhost:8000/auth/github/callback

RWA_WEB_NCBI_API_KEY=
RWA_WEB_OPENALEX_API_KEY=
RWA_WEB_OPENALEX_EMAIL=
RWA_WEB_S2_API_KEY=
RWA_WEB_CROSSREF_EMAIL=
RWA_WEB_ZOTERO_API_KEY=
RWA_WEB_ZOTERO_USER_ID=
```

Frontend example:

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Do not commit real `.env` files.

## GitHub OAuth Setup

Create a GitHub OAuth app for local development.

Set callback URL:

```text
http://localhost:8000/auth/github/callback
```

Copy the client ID and client secret into `web/backend/.env`.

Hosted deployments must use their hosted callback URL, for example:

```text
https://api.example.org/auth/github/callback
```

## Local Database Options

Default:

```text
RWA_WEB_DATABASE_URL=sqlite:///./rwa-web.db
```

Optional local Postgres:

```text
RWA_WEB_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/rwa_web
```

SQLite is acceptable for local development and tests. Hosted deployments should
use Postgres.

## Local Storage Options

Default:

```text
RWA_WEB_STORAGE_URL=file://./rwa-web-data
```

Other local/test options:

```text
RWA_WEB_STORAGE_URL=memory://
RWA_WEB_STORAGE_URL=s3://bucket-name/rwa-web-dev
```

Project storage provider dependencies such as `s3fs` should be installed only
when using that provider.

## Hosted Deployment

Hosted deployment should provide:

- FastAPI service
- Next.js frontend service
- worker service
- Postgres database
- configured `fsspec` storage backend
- GitHub OAuth app with hosted callback URL
- HTTPS
- secret management
- logs and health checks

Use Postgres as the application database system of record.

Do not use SQLite for hosted multi-user deployments.

## Hosted Environment Variables

Required:

```text
RWA_WEB_ENVIRONMENT=production
RWA_WEB_DEBUG=false
RWA_WEB_DATABASE_URL=postgresql+psycopg://...
RWA_WEB_STORAGE_URL=...
RWA_WEB_SESSION_SECRET=...
RWA_WEB_GITHUB_CLIENT_ID=...
RWA_WEB_GITHUB_CLIENT_SECRET=...
RWA_WEB_GITHUB_CALLBACK_URL=https://...
NEXT_PUBLIC_API_BASE_URL=https://...
```

Optional provider credentials:

```text
RWA_WEB_NCBI_API_KEY=
RWA_WEB_OPENALEX_API_KEY=
RWA_WEB_OPENALEX_EMAIL=
RWA_WEB_S2_API_KEY=
RWA_WEB_CROSSREF_EMAIL=
RWA_WEB_ZOTERO_API_KEY=
RWA_WEB_ZOTERO_USER_ID=
```

Store secrets in the deployment platform's secret manager, not in committed
files.

## Deployment Order

Recommended order:

1. Provision Postgres.
2. Provision storage.
3. Configure secrets and environment variables.
4. Run database migrations.
5. Deploy backend API.
6. Deploy worker using same backend image/package.
7. Deploy frontend with API base URL.
8. Configure GitHub OAuth callback.
9. Run smoke checks.

## Health Checks

Backend:

```text
GET /health
```

Add richer readiness checks later:

```text
GET /api/config/status
```

Readiness may verify:

- database reachable
- storage reachable
- GitHub OAuth configured
- provider credential status
- worker heartbeat if implemented

## Operational Notes

- API and worker must use the same database and storage configuration.
- Browser-facing frontend should receive only public configuration.
- Logs should include job IDs for long-running tasks.
- Failed jobs should remain visible for debugging.
- Project artifacts should be backed up according to the storage provider's
  operational model.
- Database migrations should be run before starting a new backend version.

## Manual Smoke Test

After local or hosted setup:

1. Open frontend.
2. Sign in with GitHub.
3. Create a project.
4. Confirm project dashboard loads.
5. Initialize protocol.
6. Preview a search.
7. Run a mocked or real configured search.
8. Confirm worker completes the job.
9. View search results.
10. Export BibTeX.
11. Update PRISMA counts.
12. Confirm audit events appear.

## Implementation Checklist

- [ ] Document backend setup commands.
- [ ] Document frontend setup commands.
- [ ] Document worker startup command.
- [ ] Document local `.env` examples.
- [ ] Document GitHub OAuth app setup.
- [ ] Document database migration commands.
- [ ] Document local and hosted storage configuration.
- [ ] Document hosted deployment requirements.
- [ ] Add health/readiness checks.
- [ ] Add manual smoke test checklist.

## Acceptance Criteria

- A developer can run backend, frontend, and worker locally from documented
  commands.
- Local setup works with SQLite and local filesystem storage by default.
- Hosted setup is documented for Postgres and configurable storage.
- GitHub OAuth callback configuration is clear for local and hosted
  deployments.
- Deployment docs do not require Redis or an external queue for the first
  prototype.
