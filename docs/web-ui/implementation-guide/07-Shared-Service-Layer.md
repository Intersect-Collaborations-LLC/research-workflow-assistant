# 07 - Shared Service Layer

## Purpose

Create the shared Python service boundary used by both the FastAPI web backend
and existing MCP tool wrappers. The goal is to avoid building a separate web
implementation that duplicates business logic already present in RWA MCP
servers and utility modules.

Target shape:

```text
Shared service function
        |
        |-- FastAPI endpoint
        |
        |-- MCP tool wrapper
```

## Scope

This guide covers:

- Service module organization.
- Service context objects.
- Refactoring principles for existing MCP code.
- Error and result conventions.
- Test expectations for shared services.

This guide does not require every MCP tool to be refactored immediately.
During transition, mixed implementation is acceptable.

## Directory Layout

Use backend-local services for web-specific orchestration:

```text
web/backend/src/rwa_web/services/
  projects.py
  searches.py
  prisma.py
  bibliography.py
  documents.py
  exports.py
  audit.py
```

For reusable RWA logic that should also be used by MCP packages, prefer placing
it in an importable shared package location already suitable for existing RWA
code, such as:

```text
src/research_workflow_assistant/services/
```

Exact placement should follow the repository's existing Python package layout.
Avoid importing FastAPI, Starlette, or web-specific database session objects
from shared RWA service modules.

## Service Boundary Principles

- Shared service functions should accept explicit inputs.
- Shared service functions should not read browser requests directly.
- Shared service functions should not depend on FastAPI route objects.
- MCP wrappers should become thin input/output adapters over shared services.
- Web endpoints should handle HTTP concerns, authentication, and response
  schemas.
- Service functions should return structured data or domain objects, not raw
  HTTP responses.
- Existing behavior should remain compatible for Copilot and MCP users.

## Service Context

Create lightweight context objects where a function needs project, storage, and
credential information:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class ProjectContext:
    project_id: str
    user_id: str
    storage_prefix: str
    project_title: str


@dataclass(frozen=True)
class ServiceCredentials:
    ncbi_api_key: str | None = None
    openalex_email: str | None = None
    openalex_api_key: str | None = None
    s2_api_key: str | None = None
    crossref_email: str | None = None
    zotero_api_key: str | None = None
    zotero_user_id: str | None = None
```

Use explicit credentials where possible. If legacy code still reads
environment variables, adapt at the boundary and plan a later cleanup.

## Candidate Shared Services

### Project Services

- Initialize project artifacts.
- Read project configuration.
- Update project tracking files.
- Append AI contribution logs.

### Search Services

- Build provider-specific queries from structured concepts.
- Preview queries.
- Run PubMed/OpenAlex/Semantic Scholar/Crossref searches where supported.
- Normalize provider results.

### PRISMA Services

- Read/write PRISMA count state.
- Generate diagram data.
- Export PRISMA flow artifacts.

### Bibliography Services

- Parse and write BibTeX.
- Validate DOI metadata.
- Export references.
- Sync or interoperate with existing Zotero-related functions where supported.

### Document Services

- Initialize protocol templates.
- Render or update `.qmd` artifacts.
- Generate reviewable document sections.
- Preserve human approval metadata.

## Error Handling

Shared services should raise domain-specific exceptions rather than HTTP
exceptions:

```python
class RwaServiceError(Exception):
    pass


class ProviderCredentialError(RwaServiceError):
    pass


class ExternalProviderError(RwaServiceError):
    pass


class ProjectArtifactError(RwaServiceError):
    pass
```

FastAPI endpoints translate these exceptions into appropriate HTTP responses.
MCP wrappers translate them into clear tool responses.

## Result Shapes

Prefer typed result objects:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class SearchPreview:
    source: str
    query: str
    parameters: dict[str, object]
    warnings: list[str]
```

For web persistence, convert result objects into SQLAlchemy models in web
service orchestration code. Do not make shared provider code depend directly on
web database models.

## Refactoring Existing MCP Code

Refactor incrementally:

1. Identify a function currently embedded in an MCP `server.py`.
2. Move provider-independent or business logic into a shared module.
3. Keep the MCP tool signature stable.
4. Call the shared service from the MCP wrapper.
5. Add or update tests around the shared function.
6. Wire the same shared function into FastAPI when the web feature is built.

Do not combine large MCP behavior changes with frontend work in the same small
implementation step unless required.

## Transitional Compatibility

Some capabilities may remain MCP-only during the first prototype. When this
happens:

- Document the temporary boundary.
- Avoid making browser code call MCP directly.
- Prefer a FastAPI endpoint that calls a shared or web-local service.
- Plan a later MCP wrapper refactor rather than duplicating logic permanently.

## Tests

Add shared-service tests near the module being tested.

Minimum patterns:

- Pure query-building functions have unit tests without network access.
- Provider clients are tested with mocked HTTP responses.
- Storage-writing services are tested with `memory://`.
- Web orchestration services are tested with temporary database sessions.
- MCP wrappers retain smoke tests where existing behavior is covered.

## Implementation Checklist

- [ ] Create service modules for web orchestration.
- [ ] Identify first MCP function to extract.
- [ ] Create shared context/result types where needed.
- [ ] Add domain-specific service exceptions.
- [ ] Refactor one search or project function into shared service code.
- [ ] Update MCP wrapper to call the shared function.
- [ ] Add FastAPI-facing service wrapper if needed.
- [ ] Add unit tests for the shared function.
- [ ] Document transitional MCP-only capabilities.

## Acceptance Criteria

- New web endpoints call service functions rather than embedding business logic
  in route handlers.
- Shared service modules do not depend on FastAPI request/response objects.
- At least one existing MCP capability is demonstrably callable through a
  shared service function.
- Existing MCP behavior remains available.
- Service errors can be translated cleanly by both FastAPI and MCP wrappers.
