# 06 - Project Lifecycle

## Purpose

Implement creating, listing, opening, and displaying web-managed research
projects. A project is the main container for metadata, storage artifacts,
searches, documents, PRISMA status, exports, jobs, and audit events.

The initial implementation supports projects initiated within the web app.
Importing existing RWA projects is deferred.

## Scope

This guide covers:

- Project create/list/detail APIs.
- Project metadata validation.
- Backend-owned storage prefix creation.
- Initial project artifact setup.
- Project dashboard summary data.
- User ownership checks.

This guide does not implement full search execution, documents, PRISMA editing,
or project import.

## Backend Layout

Create or extend:

```text
web/backend/src/rwa_web/
  api/
    projects.py
  schemas/
    __init__.py
    projects.py
  services/
    projects.py
```

Register the project router under:

```text
/api/projects
```

## Project Metadata

Initial project creation fields:

- `title`
- `review_type`
- `research_question`
- optional `description`
- optional authorship metadata

Recommended review type values:

```text
systematic_review
scoping_review
rapid_review
umbrella_review
evidence_map
other
```

Keep validation helpful but not overly restrictive. Researchers should be able
to create a project before every protocol detail is finalized.

## Slug Generation

Generate a project slug from the title and make it unique per user.

Rules:

- Lowercase.
- Replace non-alphanumeric runs with `-`.
- Trim leading and trailing separators.
- Limit length to a reasonable maximum, such as 80 characters.
- If the slug already exists for the same user, append `-2`, `-3`, and so on.

Do not accept a storage path or storage prefix from the browser.

## Storage Prefix

Use the backend-owned prefix shape from guide 04:

```text
users/{user_id}/projects/{project_id}
```

The database stores this prefix on the `Project` record. The browser sees the
project ID and metadata, not the resolved storage location.

## Project Creation Service

Create a service function:

```python
def create_project(
    db: Session,
    storage: ProjectStorage,
    *,
    user: User,
    title: str,
    review_type: str,
    research_question: str,
    metadata: dict[str, Any] | None = None,
) -> Project:
    ...
```

The service should:

1. Validate the metadata.
2. Create a `Project` database record.
3. Generate and assign `storage_prefix`.
4. Initialize project storage files and directories.
5. Create an audit event such as `project.created`.
6. Commit the database transaction.

If storage initialization fails, avoid leaving a committed project record that
cannot be opened. Use clear transaction boundaries and error handling.

## Initial Project Artifacts

Initialize at least:

```text
project-config.yaml
ai-contributions-log.md
project-tracking/
  project.yaml
  tasks.yaml
  decisions.yaml
review-tracking/
  prisma-flow.json
documents/
exports/
data/
```

Initial metadata should identify the project as web-managed:

```yaml
created_by: rwa-web
web_project_id: <project_id>
title: <project_title>
review_type: <review_type>
research_question: <research_question>
```

Preserve compatibility with existing RWA project artifact conventions where
practical.

## API Endpoints

Implement:

```text
POST /api/projects
GET /api/projects
GET /api/projects/{project_id}
PATCH /api/projects/{project_id}
```

Optional later endpoint:

```text
GET /api/projects/{project_id}/dashboard
```

Behavior:

- `POST` creates a project for the authenticated user.
- `GET /api/projects` lists only projects owned by the authenticated user.
- `GET /api/projects/{project_id}` returns only owned projects.
- `PATCH` updates editable metadata and records an audit event.

Use `404` for projects not owned by the current user.

## Dashboard Summary

The project detail or dashboard endpoint should return a compact summary:

- project metadata
- storage initialized status
- number of searches
- number of search results
- latest job status
- latest audit event timestamp
- PRISMA status availability
- document artifact availability
- export artifact availability

Avoid expensive computation in the dashboard endpoint. Add targeted aggregate
queries or cached summary fields only when needed.

## Frontend Screens

Initial screens:

- Project list.
- Project creation form.
- Project dashboard.

The dashboard should surface status and next actions, such as protocol setup,
search setup, results review, PRISMA, documents, and exports.

Do not require users to understand storage prefixes or project filesystem
layout.

## Tests

Add tests under:

```text
web/backend/tests/test_projects.py
```

Minimum tests:

- Authenticated user can create a project.
- Project creation initializes storage artifacts.
- Project list returns only the current user's projects.
- Project detail rejects another user's project.
- Slug generation handles duplicates per user.
- Project metadata update records an audit event.

Use `memory://` storage for service tests and temporary SQLite for database
tests.

## Implementation Checklist

- [ ] Create project schemas.
- [ ] Create project service functions.
- [ ] Implement slug generation.
- [ ] Integrate project storage initialization.
- [ ] Add project API router.
- [ ] Register router in FastAPI app.
- [ ] Add project list and create frontend screens.
- [ ] Add project dashboard placeholder.
- [ ] Add project lifecycle tests.
- [ ] Update README with project creation flow.

## Acceptance Criteria

- Authenticated users can create web-managed projects.
- Projects are isolated by authenticated user identity.
- Project storage prefixes are backend-owned.
- Initial project artifact directories and files are created through
  `ProjectStorage`.
- Project list and detail APIs do not expose other users' projects.
- Project dashboard data gives enough status for the next workflow steps.
