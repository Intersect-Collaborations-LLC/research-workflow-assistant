# 16 - Testing And Verification

## Purpose

Define the testing strategy for the RWA web app across backend services,
database behavior, storage providers, jobs, authentication boundaries, frontend
API usage, and end-to-end workflows.

Testing should cover localhost-friendly defaults and hosted deployment
assumptions without requiring live third-party credentials in routine test
runs.

## Scope

This guide covers:

- Backend unit and integration tests.
- Storage and database tests.
- Auth and authorization tests.
- Job worker tests.
- Frontend lint/typecheck and smoke tests.
- End-to-end workflow tests.
- External provider mocking.

## Backend Test Layout

Use:

```text
web/backend/tests/
  conftest.py
  test_health.py
  test_config.py
  test_database.py
  test_project_storage.py
  test_auth.py
  test_projects.py
  test_jobs.py
  test_search_workflow.py
  test_prisma.py
  test_documents.py
  test_bibliography.py
  test_audit.py
```

Shared RWA service tests should live near the shared package or in the existing
repository test layout, following current conventions.

## Test Configuration

Tests should override settings explicitly:

```text
RWA_WEB_ENVIRONMENT=test
RWA_WEB_DATABASE_URL=sqlite:///:memory:
RWA_WEB_STORAGE_URL=memory://
RWA_WEB_SESSION_SECRET=test-secret
```

Do not rely on a developer's `.env` file in automated tests.

Use dependency overrides for:

- database sessions
- current user
- project storage
- external provider clients
- job handlers

## Database Tests

Minimum coverage:

- metadata creates all tables
- migrations can run on SQLite for local testing
- user/project ownership constraints
- search/search result persistence
- job status transitions
- audit event persistence

Add Postgres integration tests when hosted deployment work begins. Mark them so
they are not required for quick local test runs unless Postgres is configured.

## Storage Tests

Minimum coverage:

- `memory://` read/write/list behavior
- temporary `file://` read/write/list behavior
- unsafe path rejection
- project initialization artifacts
- provider-independent path normalization

Do not assume object storage supports local filesystem semantics such as atomic
renames or SQLite file locking.

## Authentication And Authorization Tests

Minimum coverage:

- unauthenticated requests return `401`
- authenticated requests resolve current user
- project access is scoped to current user
- inaccessible records return `404` where appropriate
- OAuth user upsert handles new and returning users
- logout clears session

Mock GitHub OAuth responses. Do not call GitHub from tests.

## Job Tests

Minimum coverage:

- job creation stores queued job
- worker claims queued job once
- successful handler updates result and status
- failing handler updates error and status
- cancellation of queued jobs
- user cannot inspect another user's job

Use fake handlers and short polling intervals for tests.

## External Provider Tests

Search, DOI, and metadata provider tests should mock network calls.

Coverage should include:

- successful provider response
- empty response
- rate limit or transient failure
- missing credentials
- malformed provider payload

Live integration tests may be added separately and skipped by default unless
explicit environment variables are set.

## Frontend Verification

At minimum:

```powershell
npm run lint
npm run typecheck
```

If the generated Next.js app does not include a `typecheck` command, add one:

```json
{
  "scripts": {
    "typecheck": "tsc --noEmit"
  }
}
```

Add component or API client tests after selecting a test runner such as Vitest
or Jest.

## End-To-End Tests

Add E2E tests after the first workflow is implemented.

Recommended initial workflow:

1. Sign in using a test auth override.
2. Create a project.
3. Initialize protocol.
4. Preview a search.
5. Run a mocked search job.
6. View persisted results.
7. Export BibTeX.
8. Update PRISMA counts.
9. View audit events.

Use mocked providers so E2E tests are deterministic.

## Manual Verification

Before considering the prototype usable locally, verify:

- backend health endpoint works
- frontend loads
- GitHub OAuth login works with local callback
- project creation initializes storage
- worker process executes a fake or mocked job
- search workflow stores results
- dashboard reflects project status

## Continuous Integration

CI should run:

- backend formatting/linting if configured
- backend tests
- frontend linting
- frontend typecheck
- frontend tests when added

Avoid requiring live OAuth, academic API, Postgres, or cloud storage for the
default CI path.

## Implementation Checklist

- [ ] Add backend test fixtures for settings, DB, storage, and auth.
- [ ] Add backend tests by guide area.
- [ ] Add external provider mocks.
- [ ] Add job handler test helpers.
- [ ] Add frontend lint/typecheck commands.
- [ ] Add E2E test plan after first workflow is wired.
- [ ] Add CI commands or documentation.
- [ ] Document optional live integration tests.

## Acceptance Criteria

- Backend tests cover configuration, DB, storage, auth, projects, jobs, search,
  PRISMA, documents, bibliography, and audit.
- Tests do not require live third-party credentials by default.
- Authorization boundaries are tested for cross-user access.
- Frontend lint and typecheck pass.
- The main project workflow can be verified end to end with mocked providers.
