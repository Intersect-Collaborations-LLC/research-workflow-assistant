# 13 - Audit Trail And Human Approval

## Purpose

Implement audit event recording for generated outputs, searches, exports,
document actions, and human approval checkpoints. The web UI should make
provenance visible and preserve human ownership of substantive research
decisions.

## Scope

This guide covers:

- Audit event service functions.
- Event naming conventions.
- Human approval records.
- API endpoints for audit history.
- UI display requirements.

This guide does not implement a regulatory-grade immutable ledger. It provides
practical, queryable project provenance for the prototype.

Earlier workflow guides should call into this guide rather than defining their
own audit event machinery.

## Audit Event Model

Use the `AuditEvent` model from guide 03:

- `id`
- `user_id`
- `project_id`
- `event_type`
- `summary`
- `details_json`
- `created_at`

If needed later, add fields such as `actor_type`, `resource_type`,
`resource_id`, or `correlation_id`.

## Event Naming

Use dotted event names:

```text
project.created
project.updated
search.previewed
search.started
search.completed
search.failed
export.generated
prisma.updated
document.initialized
document.updated
document.generated
document.approved
document.rendered
bibliography.exported
bibliography.doi_validated
human.approved
job.created
job.failed
```

Keep event names stable. They become part of the project's provenance history.

## Audit Service

Create:

```python
def record_audit_event(
    db: Session,
    *,
    user_id: str,
    project_id: str,
    event_type: str,
    summary: str,
    details: dict[str, Any] | None = None,
) -> AuditEvent:
    ...
```

The service should not commit unexpectedly if the surrounding service owns the
transaction. Choose a consistent pattern and document it.

Use this service from project, search, PRISMA, document, bibliography, export,
and job code.

## Details JSON

Use `details_json` for structured provenance:

```json
{
  "source": "pubmed",
  "query": "...",
  "parameters": {},
  "job_id": "...",
  "artifact_path": "exports/searches/.../results.bib"
}
```

Do not store secrets, OAuth tokens, API keys, session values, or raw provider
credentials.

## Human Approval

Substantive generated outputs require explicit human approval before being
treated as accepted project outputs.

Approval checkpoints include:

- protocol approval
- generated manuscript/report section approval
- final search strategy approval if generated or AI-assisted
- final PRISMA state approval if used in an output

Initial approval can be represented through audit events and document fields.
If approval needs become more complex, add a dedicated model:

- `id`
- `project_id`
- `user_id`
- `resource_type`
- `resource_id`
- `approval_type`
- `summary`
- `details_json`
- `created_at`

## Approval API Pattern

Feature-specific approval endpoints are clearer than one generic approval
endpoint at first:

```text
POST /api/projects/{project_id}/documents/protocol/approve
POST /api/projects/{project_id}/searches/{search_id}/approve
```

Each endpoint should:

1. Verify project ownership.
2. Verify the target resource belongs to the project.
3. Record approval state on the target where appropriate.
4. Create an audit event.
5. Return updated resource status.

## Audit API Endpoints

Implement:

```text
GET /api/projects/{project_id}/audit-events
```

Query parameters:

```text
event_type=
limit=
offset=
```

Return events newest first by default.

All results must be scoped to the authenticated user's project.

## Frontend Display

The project dashboard should include recent audit events.

A full audit screen should show:

- timestamp
- actor
- event type
- summary
- linked resource where available
- expandable details

The UI should make human approvals distinct from automated events.

## AI-Assisted Outputs

When an action uses AI assistance, record:

- action type
- generated artifact path
- source inputs or references where practical
- model/provider metadata if available and safe to store
- human approval status

Do not claim AI-generated outputs are final until a human approval checkpoint
is recorded.

## Tests

Add tests under:

```text
web/backend/tests/test_audit.py
```

Minimum tests:

- Audit event service creates events.
- Audit list returns only current user's project events.
- Event filtering by type works.
- Approval endpoint records approval event.
- Audit details do not include configured secrets.
- Project dashboard includes recent audit events.

## Implementation Checklist

- [ ] Create audit service.
- [ ] Add audit API router.
- [ ] Add audit events to project lifecycle.
- [ ] Add audit events to search workflow.
- [ ] Add audit events to PRISMA updates.
- [ ] Add audit events to document approval/rendering.
- [ ] Add audit events to bibliography exports.
- [ ] Add recent audit events to project dashboard.
- [ ] Add audit trail frontend screen.
- [ ] Add tests.

## Acceptance Criteria

- Substantive project actions create audit events.
- Human approval checkpoints are explicit and visible.
- Audit history is scoped to authenticated project ownership.
- Provenance includes queries, parameters, timestamps, job IDs, and artifact
  paths where relevant.
- Secrets and credentials are never stored in audit details.
