# Web UI Implementation Guide Overview

This folder breaks the web UI implementation into numbered guides. Each guide
should be detailed enough for a human or LLM coder to implement that area while
preserving the architectural decisions in `docs/web-ui/requirements.md`.

## How To Use These Guides

Implement the guides in order unless a later guide is being used only for
planning. The sequence is intentionally layered:

- Guides 01-04 establish repository structure, configuration, persistence, and
  storage.
- Guide 05 establishes authenticated user identity and record ownership.
- Guide 06 introduces the web-managed project lifecycle that later workflows
  attach to.
- Guides 07-08 establish shared service and background job boundaries.
- Guides 09-13 implement research workflow capabilities on top of those
  foundations.
- Guide 14 builds the browser experience over the FastAPI endpoints.
- Guide 15 is an incremental compatibility refactor that should happen as
  workflow code is touched; it does not block every earlier guide.
- Guides 16-17 define verification and operating instructions for the full
  stack.

Cross-cutting rules are defined once and reused throughout:

- Authentication and ownership checks come from guide 05.
- Project artifact reads and writes go through the storage abstraction from
  guide 04.
- Long-running work uses the job system from guide 08.
- Substantive workflow actions record audit events using guide 13.
- Browser code calls FastAPI endpoints and never calls MCP servers directly.
- Shared research logic should move toward the service boundary in guide 07
  and the MCP compatibility pattern in guide 15.

## 01 - Repository Structure And Tooling

Define where the Next.js frontend, FastAPI backend, shared service modules, and
tests live in the repository. Establish development commands, environment file
conventions, formatting, linting, and local startup expectations.

## 02 - Configuration And Environment

Define the application settings model for database URLs, storage provider URLs,
GitHub OAuth credentials, academic API credentials, runtime mode, and paths.
Configuration should work from environment variables and `.env` files without
hard-coding localhost-only assumptions.

## 03 - Application Database

Set up SQLAlchemy models, database sessions, migrations, and the initial schema
for users, OAuth accounts, projects, searches, search results, audit events, and
jobs. The implementation should support environment-configured database
backends, with Postgres recommended for hosted deployments.

## 04 - Project Storage

Create a small RWA project storage interface backed by `fsspec`. It should
support local filesystem development by default while allowing other storage
providers during local testing and hosted deployments.

## 05 - Authentication And User Identity

Implement GitHub OAuth login, session handling, user creation, and identity
lookup. User identity must scope project records, storage locations, search
results, jobs, and audit records.

## 06 - Project Lifecycle

Implement creating, listing, opening, and displaying projects initiated within
the web application. This includes project metadata, backend-managed storage
initialization, and basic dashboard data.

## 07 - Shared Service Layer

Extract or introduce reusable Python service functions that can be called by
both FastAPI endpoints and MCP wrappers. This is the target boundary for search,
project, PRISMA, bibliography, and document-generation behavior.

## 08 - Job System

Implement SQLAlchemy-backed job records and a worker process for long-running
tasks. The API should return job identifiers, workers should claim and update
jobs, and the browser should poll job status.

## 09 - Search Workflow

Implement structured search forms, search preview, search execution through
shared services, result persistence, result tables, provenance display, and
exports. Initial work should focus on the minimum viable workflow before adding
all database providers.

## 10 - PRISMA Tracking

Implement PRISMA status display, count updates, and flow diagram preview or
generation. PRISMA data should remain tied to the authenticated user's project.

## 11 - Documents And Protocol Workflow

Implement protocol initialization from templates using the recommended prototype
editing model: in-app review and light editing through structured fields or
Markdown sections. Preserve canonical `.qmd` artifacts and avoid full
rich-text editor scope.

## 12 - Bibliography And Citation Support

Implement project reference views, BibTeX export, DOI validation hooks, and
connections between references and project outputs. This area should align with
the existing RWA bibliography and Zotero-related capabilities without attempting
to rebuild a full reference manager.

## 13 - Audit Trail And Human Approval

Implement audit event recording for generated outputs, searches, exports, and
human approval checkpoints. The interface should expose provenance and make
substantive human decisions explicit.

## 14 - Next.js User Interface

Implement the researcher-facing frontend: layout, navigation, project
dashboard, forms, tables, job status views, and review screens. The browser UI
should call FastAPI HTTP endpoints and never call MCP servers directly.

## 15 - MCP Compatibility Refactor

Refactor existing MCP tools toward thin wrappers around shared service
functions. Copilot mode should continue to work while the web API and MCP tools
converge on the same underlying implementation.

## 16 - Testing And Verification

Define unit, integration, and workflow tests for backend services, storage,
database behavior, jobs, auth boundaries, and frontend API usage. Tests should
cover both localhost-friendly configuration and hosted deployment assumptions.

## 17 - Local Development And Deployment

Document how to run the full stack locally and how to deploy the hosted version.
This should include FastAPI, Next.js, the worker process, database setup,
storage configuration, GitHub OAuth callback configuration, and environment
variables.
