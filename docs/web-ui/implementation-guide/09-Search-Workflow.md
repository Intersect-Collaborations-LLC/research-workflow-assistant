# 09 - Search Workflow

## Purpose

Implement the web search workflow for constructing structured database
searches, previewing generated queries, executing searches through shared
services, persisting results in application tables, and exporting results.

The first implementation should prioritize the minimum viable workflow over
supporting every provider and advanced search option.

## Scope

This guide covers:

- Structured search request models.
- Query preview.
- Search job creation.
- Search execution handlers.
- Result normalization and persistence.
- Search history and result tables.
- Excel and BibTeX export jobs.

This guide does not implement deduplication or screening as a full review
queue. Those can be added after reliable search persistence exists.

This guide builds on guide 05 for project ownership, guide 07 for shared search
services, guide 08 for background execution, and guide 13 for audit events.

## Search Providers

Start with one or two providers already well-supported by existing RWA search
logic. PubMed is a strong first provider because systematic review users expect
it and RWA already has search-related capabilities.

Candidate provider order:

1. PubMed
2. OpenAlex
3. Semantic Scholar
4. Crossref
5. Europe PMC

Provider availability should depend on configured credentials and existing
service support.

## Structured Search Model

The web UI should collect structured inputs:

- source database
- concepts
- terms per concept
- boolean operator between concepts
- filters
- date range
- language
- result limit
- optional raw query override

Example request:

```json
{
  "source": "pubmed",
  "concepts": [
    {
      "label": "population",
      "terms": ["adolescents", "young adults"]
    },
    {
      "label": "intervention",
      "terms": ["telehealth", "digital health"]
    }
  ],
  "filters": {
    "date_from": "2018-01-01",
    "date_to": "2026-05-17",
    "language": "english"
  },
  "limit": 200
}
```

Keep the persisted `parameters_json` close to the submitted structure so
search provenance remains auditable.

## Query Preview

Implement:

```text
POST /api/projects/{project_id}/searches/preview
```

The response should include:

- source
- generated query string
- normalized parameters
- warnings
- missing credential status if relevant

Preview should not execute provider calls unless explicitly needed for syntax
validation. It should be fast and safe to call repeatedly while users edit.

## Search Execution

Implement:

```text
POST /api/projects/{project_id}/searches
GET /api/projects/{project_id}/searches
GET /api/projects/{project_id}/searches/{search_id}
GET /api/projects/{project_id}/searches/{search_id}/results
```

`POST /searches` creates a `search.run` job and returns the job ID. Project
authorization should follow the ownership boundary from guide 05.

The job handler should:

1. Validate project ownership.
2. Build or confirm the query.
3. Create a `Search` record with `status="running"`.
4. Call the shared provider search service.
5. Normalize results.
6. Insert `SearchResult` rows.
7. Update `Search.total_count`, `status`, and `completed_at`.
8. Write audit events for search start and completion.
9. Optionally write compatibility artifacts to project storage.

## Result Normalization

Normalize provider-specific records into common fields:

- `source`
- `external_id`
- `doi`
- `pmid`
- `title`
- `authors_json`
- `journal`
- `year`
- `abstract`
- `extra_json`
- `retrieved_at`

Keep the original provider metadata in `extra_json` where useful. Avoid
discarding identifiers that may matter for deduplication later.

## Search Results UI

The result table should support:

- title
- authors
- year
- journal
- DOI/PMID
- source
- abstract preview
- search provenance
- sorting and filtering

Do not load massive result sets into the browser at once. Add pagination:

```text
GET /api/projects/{project_id}/searches/{search_id}/results?limit=50&offset=0
```

## Search History

Each project should show prior searches with:

- source
- query
- submitted parameters
- status
- total results
- created/completed timestamps
- initiating user
- linked job

Failed searches should remain visible with error information in the related job
record.

## Exports

Implement export endpoints:

```text
POST /api/projects/{project_id}/searches/{search_id}/exports/excel
POST /api/projects/{project_id}/searches/{search_id}/exports/bibtex
```

These can create `search.export` jobs. The job should write artifacts under:

```text
exports/searches/{search_id}/
```

Recommended filenames:

```text
results.xlsx
results.bib
search-metadata.json
```

The API should return job IDs. Completed jobs return artifact metadata through
`result_json`.

## Compatibility Artifacts

Hosted workflows should use SQLAlchemy-backed search tables as the system of
record. Project-local SQLite search databases are compatibility exports, not
the hosted persistence layer.

If compatibility export is implemented, write it as a generated artifact under
project storage, not as the primary data store.

## Tests

Add tests under:

```text
web/backend/tests/test_search_workflow.py
```

Minimum tests:

- Search preview builds the expected provider query.
- Search execution creates a job.
- Search job persists `Search` and `SearchResult` rows.
- Search results are scoped to project and user.
- Result pagination works.
- Export job writes expected storage artifacts.
- Missing credentials produce clear errors or warnings.

Mock external provider calls. Do not require live academic database access in
automated tests.

## Implementation Checklist

- [ ] Create search request/response schemas.
- [ ] Implement query preview service.
- [ ] Add search API routes.
- [ ] Add `search.run` job handler.
- [ ] Normalize provider results into `SearchResult`.
- [ ] Add search history endpoint.
- [ ] Add paginated results endpoint.
- [ ] Add Excel export job.
- [ ] Add BibTeX export job.
- [ ] Add search workflow tests.
- [ ] Add initial frontend search builder and results table.

## Acceptance Criteria

- Users can build and preview a structured search.
- Search execution runs through a background job.
- Results are persisted in SQLAlchemy application tables.
- Search provenance is visible and stored.
- Users can inspect prior searches and paginated results.
- Users can export results to Excel and BibTeX artifacts.
- Browser code calls FastAPI endpoints, not MCP servers.
