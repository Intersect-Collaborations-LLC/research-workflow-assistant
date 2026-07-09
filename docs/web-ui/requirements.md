# Web UI Requirements

## Purpose

The Research Workflow Assistant is powerful, but feedback indicates that the
current VS Code and Copilot-centered interaction model is difficult for less
technical researchers. A web interface should provide an alternative way to use
RWA capabilities without requiring users to understand VS Code, MCP servers,
filesystem layout, or agent prompts.

The goal is not to remove the existing Copilot workflow. The goal is to add a
guided, browser-based interaction layer over the same research workflow
capabilities.

## Product Direction

Build a web wrapper that treats the existing RWA project structure and server
logic as the backend for a researcher-facing application.

The interface should emphasize guided workflows, forms, checklists, review
screens, and explicit human approval points. A chat assistant may be included,
but it should not be the primary interaction model for core research tasks.

## Initial Users

- Researchers who need systematic review or evidence synthesis support but are
  uncomfortable working directly in VS Code.
- Research teams that want reproducible workflows without asking every team
  member to configure developer tooling.
- Project leads who need visibility into search progress, PRISMA counts,
  references, decisions, and outputs.

## Core Principles

- Preserve human ownership and ICMJE compliance.
- Keep Copilot/MCP workflows available for technical users.
- Avoid creating a generic chatbot wrapper as the first product.
- Prefer guided workflows with clear states, validations, and review steps.
- Reuse existing RWA project artifacts where possible.
- Keep generated outputs auditable and reproducible.
- Hide unnecessary implementation details from non-technical users.

## Proposed Architecture

```text
Web UI
  Next.js researcher-facing forms, dashboards, tables, review screens
        |
API Backend
  FastAPI
        |
Authentication
  GitHub OAuth identity
        |
Application Database
  SQLAlchemy models
  Environment-configured database backend
  Postgres recommended for hosted deployments
        |
Job Handling
  SQLAlchemy-backed job table
  Worker process for long-running tasks
        |
Storage Layer
  fsspec-backed project storage
  Environment-configured storage provider
  Local filesystem as the localhost default
  Server/cloud storage for hosted deployments
        |
Service Layer
  Project service
  Search service
  Bibliography service
  PRISMA service
  Document generation service
        |
Existing RWA Capabilities
  rwa_result_store
  search_runners
  project tracking logic
  PRISMA tracking logic
  bibliography tools
  Quarto templates
        |
Project Files
  YAML / JSON / QMD / BibTeX / Excel / compatibility exports
```

## Architecture Decisions So Far

- The web UI should not replace the existing Copilot agent workflow.
- The frontend will use Next.js.
- The API backend will use FastAPI.
- The first web UI version should support multi-user hosted deployment and
  localhost use.
- Authentication will use GitHub OAuth for user identity.
- User identity will isolate project workspaces and application records.
- The backend owns project paths and storage locations.
- Project storage will be abstracted behind `fsspec`.
- Project storage providers will be configured by environment.
- Localhost storage may use any suitable `fsspec` provider, with the local
  filesystem as the default.
- The web application database will use SQLAlchemy.
- The application database backend will be configured by environment.
- Localhost deployments may use any suitable SQLAlchemy-supported database.
- Hosted deployments should use Postgres as the system of record.
- SQLite in hosted mode is problematic and not recommended.
- Search results will be stored in SQLAlchemy-backed application tables.
- Project-local SQLite search databases remain a localhost and compatibility
  export format.
- Academic database and external service credentials will be provided through
  the runtime environment, either directly or through a `.env` file.
- Long-running work will use a SQLAlchemy-backed job table and a separate
  worker process.
- The first prototype should not require Redis or another external queue
  service.
- The browser will poll job status through web API endpoints.
- The web UI should not depend exclusively on MCP as its internal integration
  boundary.
- MCP servers should remain available for Copilot and other MCP clients.
- Shared business logic should gradually move out of MCP `server.py` files into
  reusable Python service modules.
- MCP tools and the web backend should eventually call the same underlying
  service functions.
- Browser UI code will call normal web API endpoints, not MCP servers directly.
- Web API endpoints should call shared Python service functions directly.
- MCP tools should remain as Copilot-facing wrappers around the same shared
  service functions.
- During transition, a mixed implementation is acceptable where some
  capabilities still live behind MCP wrappers, but the target architecture is a
  shared service layer used by both MCP and the web API.

The target integration shape is:

```text
Shared RWA service function
        |
        |-- MCP tool wrapper for Copilot
        |
        |-- FastAPI endpoint for web UI
```

Example usage paths:

```text
Copilot agent -> MCP server -> shared service function
Browser UI -> FastAPI endpoint -> shared service function
```

Example implementation shape:

```python
# shared service
def run_pubmed_search(project_context, query, options):
    ...

# MCP wrapper
@mcp.tool()
async def search_pubmed(...):
    return run_pubmed_search(...)

# FastAPI endpoint
@router.post("/projects/{project_id}/searches/pubmed")
async def create_pubmed_search(...):
    return run_pubmed_search(...)
```

## Working Assumption: Minimum Viable Workflow

Working assumption: the minimum viable workflow is centered on project
creation, review question and protocol setup, structured database search,
persisted search results, exports, and PRISMA status.

1. Create or select a research project.
2. Enter review question and project metadata.
3. Generate or edit a protocol from existing templates.
4. Run structured searches across selected databases.
5. Save and display search results through the web application database.
6. Export search results to Excel and/or BibTeX.
7. Show PRISMA counts and current review progress.

This slice should reduce onboarding friction while preserving the existing RWA
project artifact model.

## Full Prototype Workflow

1. Sign in with GitHub OAuth.
2. Create or select a research project.
3. Enter project metadata, including title, review type, research question,
   authorship metadata, and basic project details.
4. Set up the review question using a guided structure, such as PICO, PEO, or
   SPIDER where relevant.
5. Generate or initialize a protocol from existing RWA/Quarto templates.
6. Review generated protocol sections and record human approval before treating
   the protocol as accepted.
7. Build database searches through structured forms for concepts, terms,
   filters, date ranges, and result limits.
8. Preview generated database queries before execution.
9. Run searches through shared search service functions.
10. Store search results in SQLAlchemy-backed application tables.
11. Preserve query, parameters, source database, timestamp, and retrieval
    metadata.
12. Review search results in a table with title, authors, year, journal,
    DOI/PMID, abstract, source, and search provenance.
13. Filter, sort, and identify duplicates or likely relevant records.
14. Export search results to Excel and/or BibTeX.
15. Generate compatibility artifacts such as project-local `search_results.db`
    where appropriate.
16. View and update PRISMA status, including search, deduplication, screening,
    eligibility, and inclusion counts.
17. Generate or preview a PRISMA flow diagram.
18. Return to a project dashboard showing project status, searches run, result
    counts, PRISMA progress, documents, exports, and audit trail entries.
19. Log AI-assisted or generated outputs and capture human approvals at
    substantive decision points.

## Candidate Screens

- Project dashboard
- Project creation form
- Setup and credentials status
- Review question/protocol workspace
- Database search builder
- Search results table
- Deduplication/review queue
- PRISMA flow status
- Bibliography/reference manager view
- Outputs and exports view
- Human review and audit log view

## Functional Requirements

### Project Management

- Users can create a new project from the web interface.
- Users can open projects that were initiated within the web application and
  are present in their backend-managed workspace.
- Users can view project metadata, authorship metadata, tasks, milestones, and
  decisions.
- Users can see whether required setup steps are complete.
- User project access is scoped by GitHub OAuth identity.

### Search

- Users can construct database searches through forms.
- Users can run searches against supported RWA search providers.
- Search results are persisted through SQLAlchemy-backed application tables.
- Users can inspect prior searches and their parameters.
- Users can export results for downstream review.

### PRISMA Tracking

- Users can view current PRISMA counts.
- Users can update search, deduplication, screening, eligibility, and inclusion
  counts through guided forms.
- Users can generate or preview a PRISMA flow diagram.

### Bibliography

- Users can view project references.
- Users can export references to BibTeX.
- Users can connect references to project outputs.
- DOI validation should remain part of citation workflows.

### Documents

- Users can generate Quarto documents from existing templates.
- Users can review generated protocol/manuscript/report sections. Editing
  behavior depends on the document editing model decision.
- Generated outputs should remain saved in the project directory.
- Project files should be read and written through the web storage abstraction.

### Auditability

- AI-assisted actions should be logged.
- Human approval should be required before finalizing substantive research
  outputs.
- The interface should make provenance visible: source database, query,
  timestamp, parameters, and generated artifact location.

### Long-Running Jobs

- Long-running work should be represented as application job records.
- Job records should include user, project, job type, status, payload, progress,
  result, error, and timestamps.
- A worker process should claim queued jobs, execute them, and update job
  status.
- The web API should return job identifiers for long-running requests.
- The browser should poll job status and display progress, completion, failure,
  or cancellation.
- Initial job statuses should include `queued`, `running`, `succeeded`,
  `failed`, and `cancelled`.
- Likely job types include multi-database searches, large exports, AI document
  generation, Quarto rendering, batch DOI/reference validation, project bundle
  import/export, and PDF or annotation processing.

## Non-Goals For Initial Version

- Replacing VS Code or Copilot workflows entirely.
- Building a full generic chat-first research assistant.
- Rebuilding Zotero as a complete reference manager.
- Implementing every MCP tool in the first web release.
- Hiding or discarding the existing project file structure.

## Open Questions

- Should document editing happen inside the web app or through generated files
  opened in external tools?

### Document Editing Model

The document editing model remains open. The decision concerns where and how
users interact with generated research documents such as protocols,
manuscripts, reports, and other `.qmd` outputs.

Option 1: Generate files for external review.

- The web app creates `.qmd`, BibTeX, Word, PDF, or other output files.
- Users review and edit generated documents outside the web app.
- This is the simplest implementation and preserves the current RWA
  file-centered model.
- This is less friendly for non-technical researchers and may require users to
  understand external tools.

Option 2: In-app review and light editing.

- The web app displays generated sections in the browser.
- Users edit structured fields or Markdown text areas.
- Users approve generated sections before they become accepted project outputs.
- The app generates or updates canonical `.qmd` artifacts from reviewed
  content.
- This improves usability while avoiding the scope of a full document editor.

Option 3: Full web document editor.

- The web app provides rich document editing with formatting controls,
  citations, comments, tracked changes, previews, or collaboration features.
- This may provide the best user experience over time.
- This is a large product and engineering scope and is not recommended for the
  first prototype.

Recommendation: use Option 2 for the prototype. Provide in-app review and
light editing through structured fields and Markdown section editors, while
preserving canonical exported artifacts such as `.qmd`, BibTeX, Word, and PDF
where appropriate.

## Future Considerations

### Project Import

The initial implementation will only support projects initiated within the web
application. Importing existing RWA projects is deferred.

As the platform matures, project import may support uploading a project archive,
importing from a configured storage provider, or a localhost-only path import
flow. Any future import mechanism must preserve user isolation and ensure the
backend remains responsible for all resolved storage locations.

## Implementation Notes

- The API backend should be implemented with FastAPI.
- GitHub OAuth should be implemented early because project isolation depends on
  authenticated user identity.
- SQLAlchemy should be introduced early because multi-user hosted workflows
  depend on shared application persistence.
- The first job system should use the application database rather than a Redis
  or broker-backed queue.
- Storage access should go through a small RWA project storage interface backed
  by `fsspec`.
- The frontend should be implemented as a Next.js application.
- Refactoring should start by extracting reusable service functions from MCP
  server modules without breaking current MCP behavior.
- Existing tests around shared search runners, bibliography sync, and chat
  parsing should remain valid.
