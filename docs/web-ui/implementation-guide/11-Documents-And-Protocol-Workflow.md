# 11 - Documents And Protocol Workflow

## Purpose

Implement protocol initialization and document review support for the web UI.
The prototype should use in-app review and light editing through structured
fields or Markdown sections while preserving canonical generated artifacts such
as `.qmd`, BibTeX, Word, and PDF where appropriate.

This follows the requirements recommendation to avoid a full rich-text editor
in the first prototype.

## Scope

This guide covers:

- Protocol initialization from existing templates.
- Document section review and light editing.
- Human approval checkpoints.
- Canonical `.qmd` artifact preservation.
- Optional render jobs.

This guide does not implement collaborative editing, comments, tracked changes,
or a full browser-based word processor.

This guide builds on guide 04 for document artifacts, guide 08 for render jobs,
and guide 13 for human approval and audit events.

## Document Model

Recommended document types:

```text
protocol
manuscript
report
```

Start with `protocol`.

If a database model is added, include:

- `id`
- `project_id`
- `user_id`
- `document_type`
- `title`
- `status`
- `storage_path`
- `sections_json`
- `created_at`
- `updated_at`
- `approved_at`
- `approved_by_user_id`

Initial statuses:

```text
draft
ready_for_review
approved
rendered
```

It is also acceptable to store initial document state in project storage and
track only audit events in the database, but a model improves dashboard and
review behavior.

## Storage Paths

Use:

```text
documents/protocol.qmd
documents/protocol.sections.json
documents/rendered/
```

Generated rendered outputs can be written to:

```text
documents/rendered/protocol.docx
documents/rendered/protocol.pdf
```

Rendering may require Quarto and should run as a job.

## Template Integration

Use existing RWA/Quarto templates where possible. The document service should:

1. Load the selected protocol template.
2. Merge project metadata and review question fields.
3. Generate editable section content.
4. Write `protocol.sections.json`.
5. Generate canonical `protocol.qmd`.

Avoid copying template logic into frontend code.

## API Endpoints

Implement:

```text
POST /api/projects/{project_id}/documents/protocol
GET /api/projects/{project_id}/documents/protocol
PUT /api/projects/{project_id}/documents/protocol/sections
POST /api/projects/{project_id}/documents/protocol/approve
POST /api/projects/{project_id}/documents/protocol/render
```

Behavior:

- `POST` initializes protocol files if they do not exist.
- `GET` returns sections, status, artifact paths, and approval state.
- `PUT /sections` updates reviewed Markdown or structured fields and rewrites
  canonical `.qmd`.
- `POST /approve` records human approval.
- `POST /render` creates a document render job.

All routes use the project ownership boundary from guide 05.

## Section Editing

Represent sections as structured JSON:

```json
[
  {
    "id": "background",
    "title": "Background",
    "content_markdown": "...",
    "status": "draft"
  }
]
```

The frontend should provide Markdown text areas or structured inputs. Do not
introduce a rich text editor for the first prototype.

When sections are updated, regenerate `protocol.qmd` from the canonical section
data. The `.qmd` artifact remains the file-centered output for compatibility.

## Human Approval

Protocol approval should:

- require authenticated user identity
- record `approved_at` and approver
- create audit event `document.approved`
- freeze or clearly mark the approved version
- preserve the approved artifact path

Subsequent edits after approval should either reset approval status or create a
new draft version. The first implementation may reset status to `draft` when
approved content is changed.

## Render Jobs

Rendering should use the job system:

```text
document.render
```

The handler should:

1. Read the canonical `.qmd`.
2. Run the configured render command or shared render service.
3. Write output artifacts.
4. Update job result with artifact paths.
5. Record `document.rendered` audit event.

If Quarto is unavailable, the job should fail with a clear error message.

## Frontend Screen

The protocol screen should include:

- document status
- section editor list
- save action
- approval action
- render action
- generated artifact links or metadata
- audit/provenance summary

Do not expose raw storage prefixes. Use API routes for artifact metadata and
future download endpoints.

## Tests

Add tests under:

```text
web/backend/tests/test_documents.py
```

Minimum tests:

- Protocol initialization writes expected storage artifacts.
- Current user can retrieve protocol state.
- Section update rewrites section JSON and `.qmd`.
- Approval records approver and audit event.
- Editing after approval changes status according to the chosen rule.
- Render endpoint creates a job.
- Missing Quarto in render handler produces a failed job with clear error.

## Implementation Checklist

- [ ] Decide whether to add document database model.
- [ ] Add migration if needed.
- [ ] Create document schemas.
- [ ] Implement protocol initialization service.
- [ ] Implement section-to-QMD rendering helper.
- [ ] Implement document API routes.
- [ ] Add approval endpoint and audit events.
- [ ] Add render job handler.
- [ ] Add frontend protocol review screen.
- [ ] Add document workflow tests.

## Acceptance Criteria

- Users can initialize a protocol from existing templates.
- Users can review and lightly edit protocol sections in the web app.
- Canonical `.qmd` artifacts are preserved in project storage.
- Human approval is explicit and audited.
- Rendering is handled as a background job.
- The first prototype avoids full rich-text editor scope.
