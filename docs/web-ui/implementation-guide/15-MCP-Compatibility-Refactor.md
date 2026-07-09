# 15 - MCP Compatibility Refactor

## Purpose

Refactor existing MCP tools toward thin wrappers around shared service
functions while preserving the current Copilot-centered workflow. The web UI
adds a browser-based interaction model; it does not replace MCP or Copilot
usage for technical users.

## Scope

This guide covers:

- Identifying MCP logic to extract.
- Preserving MCP tool signatures where practical.
- Introducing shared service functions.
- Updating FastAPI endpoints to use the same services.
- Compatibility tests.

This guide does not require all MCP tools to be refactored before the first web
prototype ships.

Treat this as an incremental refactor guide. Apply it when implementing or
touching workflow capabilities from guides 09-13, rather than as a single
large prerequisite project.

## Target Shape

```text
Copilot agent -> MCP server -> shared service function
Browser UI -> FastAPI endpoint -> shared service function
```

MCP wrappers handle MCP-specific input/output. FastAPI endpoints handle HTTP,
auth, database, and response schemas. Shared services handle research workflow
logic.

## Refactor Candidates

Prioritize capabilities needed by the first web workflow:

- project initialization helpers
- PubMed or initial provider search execution
- search result normalization
- bibliography/BibTeX export
- DOI validation
- PRISMA artifact generation
- Quarto protocol/document generation

Start with functions that have clear inputs and outputs and existing test
coverage.

## Extraction Pattern

For each selected MCP tool:

1. Locate business logic inside or beneath the MCP `server.py`.
2. Define a shared service function with explicit parameters.
3. Move reusable logic into the shared module.
4. Keep MCP-specific parsing and response formatting in the wrapper.
5. Add or update tests for the shared function.
6. Update the web endpoint or job handler to call the shared function.
7. Run existing MCP tests.

Avoid broad rewrites. Small, verified extractions are safer.

## Shared Function Example

```python
def run_pubmed_search(
    *,
    query: str,
    limit: int,
    api_key: str | None,
) -> SearchServiceResult:
    ...
```

MCP wrapper:

```python
@mcp.tool()
async def search_pubmed(query: str, limit: int = 100) -> dict:
    result = run_pubmed_search(query=query, limit=limit, api_key=...)
    return result.to_mcp_response()
```

FastAPI/job handler:

```python
result = run_pubmed_search(
    query=search.query,
    limit=payload.limit,
    api_key=settings.ncbi_api_key or None,
)
persist_search_results(db, search, result.records)
```

## Compatibility Rules

- Do not remove existing MCP tools as part of web UI work.
- Avoid changing tool names unless explicitly planned.
- Preserve existing input defaults where practical.
- Preserve existing artifact formats unless a migration is documented.
- Keep Copilot workflow docs valid.
- Browser UI code must not call MCP servers directly.

## Handling Web-Specific Concerns

Shared service modules should not know about:

- FastAPI request objects
- sessions/cookies
- SQLAlchemy web models
- frontend routes
- browser polling

Web orchestration code can adapt shared results into database rows, jobs, audit
events, and storage artifacts.

## Handling MCP-Specific Concerns

MCP wrappers can continue to handle:

- tool schemas
- chat-friendly result formatting
- compatibility with existing workspace paths
- Copilot-specific prompt expectations
- MCP server startup

Over time, wrappers should become thinner.

## Tests

Testing should include:

- shared service unit tests
- existing MCP wrapper smoke tests
- web job/endpoint tests using shared service fakes
- artifact compatibility tests where formats matter

When refactoring an MCP tool, run the nearest existing tests for that MCP
server and the new shared service tests.

## Transitional Inventory

Maintain a simple inventory in this guide or a separate implementation note:

```text
Capability              Current state
Project init            Shared service
PubMed search           Partially shared
BibTeX export           MCP-only
PRISMA generation       MCP-only
Document generation     Web-local wrapper
```

Update it as refactors land.

## Implementation Checklist

- [ ] Inventory MCP tools needed by the first web workflow.
- [ ] Pick the first low-risk extraction target.
- [ ] Create shared service module if needed.
- [ ] Move reusable logic behind explicit function inputs.
- [ ] Update MCP wrapper to call shared function.
- [ ] Update FastAPI endpoint or job handler to call shared function.
- [ ] Add shared service tests.
- [ ] Run MCP compatibility tests.
- [ ] Document any temporary MCP-only capabilities.

## Acceptance Criteria

- Existing MCP workflows remain available.
- Web API and MCP wrappers begin converging on shared service functions.
- At least the first web search/provider path uses shared logic rather than
  duplicated implementation.
- Refactors are covered by tests.
- Browser UI remains decoupled from MCP servers.
