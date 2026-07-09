# 08 - Job System

## Purpose

Implement SQLAlchemy-backed background jobs for long-running web workflows.
The first prototype should not require Redis, Celery, or another external
queue service. Jobs are stored in the application database and executed by a
separate worker process.

Long-running workflows include searches, exports, document generation, Quarto
rendering, DOI validation, project import/export, and PDF or annotation
processing.

## Scope

This guide covers:

- Job model usage.
- Job creation APIs and service functions.
- Worker claim/execute/update loop.
- Job status polling.
- Progress and error reporting.
- Cancellation semantics.

This guide does not implement every job type. Later workflow guides add
specific job handlers.

## Job Statuses

Initial statuses:

```text
queued
running
succeeded
failed
cancelled
```

Optional later statuses:

```text
cancelling
retrying
```

Keep the first implementation small unless a feature needs more nuance.

## Job Types

Initial candidate types:

```text
search.run
search.export
document.generate
document.render
bibliography.validate_doi_batch
project.export_bundle
```

Store the type in `Job.type` and route execution to a registered handler.

## Directory Layout

Create:

```text
web/backend/src/rwa_web/jobs/
  __init__.py
  registry.py
  runner.py
  worker.py
```

Create API routes:

```text
web/backend/src/rwa_web/api/jobs.py
```

## Job Creation Service

Create:

```python
def create_job(
    db: Session,
    *,
    user_id: str,
    project_id: str | None,
    job_type: str,
    payload: dict[str, Any],
) -> Job:
    ...
```

Rules:

- Validate that the project belongs to the user before creating project jobs.
- Store payload as JSON.
- Set `status="queued"`.
- Set `progress=0`.
- Create an audit event for substantive project jobs where appropriate.

API endpoints that start long-running work should return a job ID instead of
holding the HTTP request open.

## Worker Process

Provide a worker command that can be run separately:

```powershell
python -m rwa_web.jobs.worker
```

The worker should:

1. Poll for queued jobs.
2. Claim one job atomically.
3. Mark it `running`.
4. Execute the registered handler.
5. Update progress and result.
6. Mark it `succeeded`, `failed`, or `cancelled`.

Use conservative polling for the first version. Avoid busy loops.

## Claiming Jobs

Claiming must avoid two workers executing the same job.

For a portable first implementation:

- Query the oldest queued job.
- Attempt an update from `queued` to `running`.
- Commit.
- Proceed only if the update affected one row.

Postgres deployments can later use stronger locking patterns such as
`SELECT ... FOR UPDATE SKIP LOCKED`.

SQLite local development may not perfectly match hosted concurrency behavior,
so include Postgres-specific notes in deployment docs.

## Handler Registry

Create a simple registry:

```python
JobHandler = Callable[[JobContext], dict[str, Any] | None]


def register_job_handler(job_type: str, handler: JobHandler) -> None:
    ...


def get_job_handler(job_type: str) -> JobHandler:
    ...
```

The handler receives a context with:

- database session factory or session boundary
- project storage
- settings/credentials
- job payload
- progress callback

Handlers should not directly mutate unrelated jobs.

## Progress Updates

Use `Job.progress` as an integer percentage from `0` to `100`.

Allow handlers to store richer progress in `result_json` or a future
`progress_json` field if needed, but keep the initial UI compatible with a
simple percentage.

Examples:

```json
{
  "message": "Searching PubMed",
  "records_retrieved": 120
}
```

If adding a separate `progress_json` field, include it in the database guide or
a migration.

## Cancellation

Initial cancellation can be cooperative:

```text
POST /api/jobs/{job_id}/cancel
```

Behavior:

- If job is `queued`, set `cancelled`.
- If job is `running`, mark cancellation requested in payload/result or a
  dedicated field if added.
- Handlers check cancellation between external calls or batches.

Do not promise hard cancellation of already-running external provider requests
in the first prototype.

## API Endpoints

Implement:

```text
GET /api/jobs/{job_id}
POST /api/jobs/{job_id}/cancel
```

Rules:

- Return only jobs owned by the current user.
- Include status, progress, timestamps, result, and error.
- Use `404` for inaccessible jobs.

Feature-specific endpoints create jobs. The generic jobs API reports and
cancels them.

## Frontend Behavior

The browser polls:

```text
GET /api/jobs/{job_id}
```

Recommended polling:

- 1-2 seconds while active.
- Stop polling after terminal statuses.
- Show clear failure messages from `Job.error`.
- Provide a cancel control where supported.

The UI should tolerate page reloads by retrieving existing jobs from project
dashboard state or feature-specific history.

## Tests

Add tests under:

```text
web/backend/tests/test_jobs.py
```

Minimum tests:

- Authenticated user can read only their own job.
- Creating a job stores queued status and payload.
- Worker claims a queued job and marks it running.
- Successful handler marks job succeeded with result.
- Handler exception marks job failed with error.
- Queued job can be cancelled.
- Running job cancellation request is represented consistently.

Use fake job handlers in tests. Do not require external providers.

## Implementation Checklist

- [ ] Create job API router.
- [ ] Create job creation service.
- [ ] Create job handler registry.
- [ ] Implement worker claim logic.
- [ ] Implement worker execution loop.
- [ ] Add worker command/module entry point.
- [ ] Add job status endpoint.
- [ ] Add job cancellation endpoint.
- [ ] Add frontend polling helper.
- [ ] Add job tests.
- [ ] Document worker startup command.

## Acceptance Criteria

- Long-running workflows can create database-backed jobs.
- A separate worker process can claim and execute queued jobs.
- Browser clients can poll job status by ID.
- Jobs are scoped to authenticated users.
- Job failures are captured in the database and surfaced through the API.
- The first prototype does not require Redis or an external queue service.
