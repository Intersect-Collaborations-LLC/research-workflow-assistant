# 12 - Bibliography And Citation Support

## Purpose

Implement project reference views, BibTeX export, DOI validation hooks, and
connections between references and project outputs. This area should align with
existing RWA bibliography and Zotero-related capabilities without attempting to
rebuild a complete reference manager.

## Scope

This guide covers:

- Reading and displaying project references.
- Exporting references to BibTeX.
- DOI validation and metadata lookup hooks.
- Linking references to documents or outputs.
- Bibliography audit events.

This guide does not implement a full Zotero replacement, collaborative library
management, or advanced citation editing.

This guide builds on guide 09 for references derived from search results, guide
04 for BibTeX artifacts, guide 08 for batch DOI validation jobs, and guide 13
for audit events.

## Data Sources

References may originate from:

- persisted search results
- uploaded or generated BibTeX files
- existing RWA bibliography tools
- Zotero-related integrations where already supported
- DOI metadata lookup

The first prototype can derive project references from selected search results
and generated BibTeX exports.

## Reference Model

If a dedicated model is added, include:

- `id`
- `project_id`
- `user_id`
- `source`
- `source_result_id`
- `doi`
- `pmid`
- `title`
- `authors_json`
- `year`
- `journal`
- `bibtex_key`
- `metadata_json`
- `created_at`
- `updated_at`

Use normalized fields for display and filtering. Store provider-specific or
BibTeX-specific metadata in JSON.

## Storage Artifacts

Use:

```text
references/
  project.bib
  doi-validation.json
```

or, if existing RWA conventions already use a specific path, preserve that
convention.

All writes must go through `ProjectStorage`.

## API Endpoints

Implement:

```text
GET /api/projects/{project_id}/references
POST /api/projects/{project_id}/references/from-search-results
POST /api/projects/{project_id}/references/export/bibtex
POST /api/projects/{project_id}/references/validate-dois
```

Optional later endpoints:

```text
POST /api/projects/{project_id}/references/import/bibtex
PATCH /api/projects/{project_id}/references/{reference_id}
```

Behavior:

- List references with pagination.
- Create references from selected search results or all results from a search.
- Export references to BibTeX as a job or fast synchronous operation depending
  on size.
- Validate DOI metadata as a job for batch operations.

All endpoints use the project ownership boundary from guide 05.

## DOI Validation

DOI validation should use existing RWA citation workflows where possible.

Validation result should include:

- DOI
- status
- normalized DOI
- resolved title
- provider metadata
- warnings
- checked timestamp

Store validation output in database JSON or project artifact:

```text
references/doi-validation.json
```

Batch validation should run as a job:

```text
bibliography.validate_doi_batch
```

## BibTeX Export

Export should:

1. Query references for the project and user.
2. Generate stable BibTeX keys.
3. Preserve DOI, PMID, title, authors, year, journal, and URL where available.
4. Write `references/project.bib`.
5. Return artifact metadata.
6. Record `bibliography.exported` audit event.

Avoid exposing raw storage prefixes in browser responses.

## Frontend Screen

The bibliography screen should include:

- reference table
- DOI/PMID identifiers
- source provenance
- validation status
- export action
- links to related search results or documents where available

Keep editing minimal for the first prototype.

## Tests

Add tests under:

```text
web/backend/tests/test_bibliography.py
```

Minimum tests:

- References can be created from search results.
- Reference list is scoped to current user's project.
- BibTeX export writes a project storage artifact.
- DOI validation job is created.
- DOI validation service handles valid and invalid DOI metadata responses.
- Audit event is recorded for export and validation.

Mock external DOI metadata providers.

## Implementation Checklist

- [ ] Decide whether to add reference database model.
- [ ] Add migration if needed.
- [ ] Create bibliography schemas.
- [ ] Implement reference creation from search results.
- [ ] Implement reference listing endpoint.
- [ ] Implement BibTeX export service.
- [ ] Implement DOI validation job handler.
- [ ] Add bibliography frontend screen.
- [ ] Add tests.

## Acceptance Criteria

- Users can view project references.
- References remain scoped to authenticated project ownership.
- Users can export references to BibTeX.
- DOI validation hooks are available without requiring live provider calls in
  tests.
- Bibliography actions are auditable.
- The implementation does not attempt to replace Zotero as a full reference
  manager.
