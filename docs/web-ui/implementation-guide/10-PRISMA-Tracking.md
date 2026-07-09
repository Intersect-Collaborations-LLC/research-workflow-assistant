# 10 - PRISMA Tracking

## Purpose

Implement PRISMA status display, count updates, and flow diagram data for
web-managed projects. PRISMA state should be tied to authenticated user project
records and should remain auditable.

## Scope

This guide covers:

- PRISMA data model choices.
- API endpoints for reading and updating counts.
- Storage artifact synchronization.
- Flow diagram preview data.
- Audit events for count changes.

This guide does not implement a complete screening workflow. Counts may be
entered manually or derived from search results where available.

This guide builds on guide 05 for project ownership, guide 04 for the
compatibility JSON artifact, and guide 13 for audit events.

## Data Ownership

Store current PRISMA state in the application database if it needs to be queried
or displayed frequently. Also write a project artifact for compatibility:

```text
review-tracking/prisma-flow.json
```

If a dedicated `PrismaState` model is added, include:

- `id`
- `project_id`
- `user_id`
- `records_identified`
- `records_removed_duplicates`
- `records_screened`
- `records_excluded`
- `reports_sought`
- `reports_not_retrieved`
- `reports_assessed`
- `reports_excluded`
- `studies_included`
- `updated_at`

Alternatively, store PRISMA state in `Project` metadata for the first prototype
only if the fields are not yet queried independently. A dedicated table is more
extensible.

## PRISMA State Shape

Use a portable JSON representation:

```json
{
  "identification": {
    "database_records": 0,
    "register_records": 0,
    "other_records": 0,
    "duplicates_removed": 0
  },
  "screening": {
    "records_screened": 0,
    "records_excluded": 0
  },
  "eligibility": {
    "reports_sought": 0,
    "reports_not_retrieved": 0,
    "reports_assessed": 0,
    "reports_excluded": 0
  },
  "included": {
    "studies_included": 0
  }
}
```

Keep names clear enough for UI labels and export mappings.

## API Endpoints

Implement:

```text
GET /api/projects/{project_id}/prisma
PUT /api/projects/{project_id}/prisma
GET /api/projects/{project_id}/prisma/flow
```

Behavior:

- `GET /prisma` returns current counts and last updated timestamp.
- `PUT /prisma` validates and saves counts.
- `GET /prisma/flow` returns diagram-ready nodes and edges or an SVG/PNG
  artifact reference if generation is implemented.

All endpoints use the project ownership boundary from guide 05.

## Count Validation

Validate that counts are non-negative integers.

Where possible, warn about inconsistent counts rather than blocking every
update. Examples:

- screened records exceed identified records after duplicates
- included studies exceed assessed reports
- excluded counts are greater than screened counts

Researchers may need to enter partial counts while a review is in progress, so
the UI should distinguish warnings from hard errors.

## Search Integration

The PRISMA screen can offer to populate identification counts from stored
searches:

- total records identified from all completed searches
- records by source database
- duplicate removal count when deduplication is implemented

Initial implementation may show suggested counts without automatically
overwriting manually entered PRISMA state.

## Storage Synchronization

After PRISMA updates, write:

```text
review-tracking/prisma-flow.json
```

through `ProjectStorage`.

The artifact should include:

- current count state
- timestamp
- user ID or display name if appropriate
- source indicating `rwa-web`

If storage write fails, return a clear error and avoid pretending the artifact
was updated.

## Audit Events

Create audit events:

```text
prisma.updated
prisma.flow.generated
```

Include changed fields and previous/current values where practical. Do not log
private secrets or provider credentials.

## Frontend Screen

The PRISMA screen should include:

- count sections matching PRISMA stages
- inline validation warnings
- save action
- flow preview area
- timestamp and provenance

Use standard form controls. Do not make users edit JSON directly.

## Tests

Add tests under:

```text
web/backend/tests/test_prisma.py
```

Minimum tests:

- Current user can read PRISMA state for owned project.
- Another user's project returns `404`.
- Negative counts are rejected.
- Valid updates persist to database or project metadata.
- PRISMA artifact is written through `ProjectStorage`.
- Audit event is created on update.
- Flow endpoint returns diagram-ready data.

## Implementation Checklist

- [ ] Decide whether to add dedicated `PrismaState` model.
- [ ] Add migration if a model is added.
- [ ] Create PRISMA schemas.
- [ ] Implement PRISMA service functions.
- [ ] Implement API routes.
- [ ] Write storage artifact synchronization.
- [ ] Add audit events.
- [ ] Add frontend PRISMA screen.
- [ ] Add tests.

## Acceptance Criteria

- Users can view and update PRISMA counts for owned projects.
- Count updates are validated and audited.
- PRISMA state is available to the project dashboard.
- A compatibility JSON artifact is written to project storage.
- Flow preview data can be generated from the saved state.
