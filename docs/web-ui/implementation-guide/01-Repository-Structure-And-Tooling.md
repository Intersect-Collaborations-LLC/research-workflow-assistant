# 01 - Repository Structure And Tooling

## Purpose

Establish the initial repository layout and development tooling for the RWA web
UI. This guide should be completed before implementing configuration,
database, authentication, storage, or feature workflows.

The goal is to add a web application without disrupting the existing MCP server
packages, Copilot agents, templates, sample projects, or current tests.

## Target Repository Layout

Add a new top-level `web/` directory:

```text
web/
  backend/
    pyproject.toml
    README.md
    src/
      rwa_web/
        __init__.py
        main.py
        api/
          __init__.py
        core/
          __init__.py
        db/
          __init__.py
        models/
          __init__.py
        services/
          __init__.py
        storage/
          __init__.py
        jobs/
          __init__.py
    tests/
      __init__.py
  frontend/
    package.json
    README.md
    next.config.ts
    tsconfig.json
    src/
      app/
      components/
      lib/
      types/
```

Keep the web implementation separate from existing packages:

```text
mcp-servers/
src/research_workflow_assistant/
templates/
docs/
sample_projects/
web/
```

Do not move existing MCP server code as part of this setup step.

## Backend Package

Create `web/backend` as a standalone Python package named `rwa-web`.

Recommended package metadata:

```toml
[project]
name = "rwa-web"
version = "0.1.0"
description = "Web API for the Research Workflow Assistant"
requires-python = ">=3.11"
```

Initial backend dependencies:

```toml
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
    "pydantic>=2",
    "pydantic-settings>=2",
    "python-dotenv>=1",
]
```

Additional dependencies such as SQLAlchemy, Alembic, Authlib, `fsspec`, and
database drivers should be introduced in their specific implementation guides.

## Backend Entry Point

Create `web/backend/src/rwa_web/main.py` with a minimal FastAPI app:

```python
from fastapi import FastAPI

app = FastAPI(title="Research Workflow Assistant Web API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

The app should be runnable with:

```powershell
uvicorn rwa_web.main:app --reload
```

Run the command from `web/backend` with the backend package installed in editable
mode, or configure `PYTHONPATH=src` for local development.

## Frontend App

Create `web/frontend` as a Next.js application.

Use TypeScript. The app should call FastAPI HTTP endpoints and must not call MCP
servers directly.

Recommended initial structure:

```text
web/frontend/src/app/
  layout.tsx
  page.tsx

web/frontend/src/lib/
  api.ts

web/frontend/src/types/
  api.ts
```

The initial home page can be a simple placeholder that confirms the frontend is
running and can later be wired to the backend health endpoint.

## Root-Level Commands

Prefer adding thin helper commands without disrupting the existing Python
package setup.

Recommended development commands to document:

```powershell
# Backend
cd web/backend
pip install -e .
uvicorn rwa_web.main:app --reload

# Frontend
cd web/frontend
npm install
npm run dev
```

Do not require Redis or any external queue service for local startup.

Do not require Postgres for the earliest skeleton startup. Database setup is
handled in later guides.

## Environment Files

Use separate example environment files:

```text
web/backend/.env.example
web/frontend/.env.example
```

The backend should eventually support values such as:

```text
RWA_WEB_DATABASE_URL=
RWA_WEB_STORAGE_URL=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
GITHUB_CALLBACK_URL=
```

The frontend should eventually support values such as:

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Do not commit real secrets.

## Formatting And Linting

Backend should follow the repository's existing Python conventions where
possible:

- Python 3.11+
- Ruff-compatible formatting and linting
- Pytest for tests
- Type annotations for public service and API boundaries

Frontend should use standard Next.js TypeScript tooling:

- TypeScript
- ESLint
- `npm run lint`
- Component and API client code under `src/`

Avoid introducing a frontend UI component framework in this step unless a later
design decision explicitly chooses one.

## Testing Expectations

Add a minimal backend test:

```text
web/backend/tests/test_health.py
```

The test should verify that `GET /health` returns `{"status": "ok"}`.

Add a minimal frontend smoke check only if the generated Next.js setup includes
one naturally. Full frontend testing choices can be deferred.

## Implementation Checklist

- [ ] Create `web/backend` package skeleton.
- [ ] Create `web/backend/src/rwa_web/main.py` with `/health`.
- [ ] Create `web/backend/tests/test_health.py`.
- [ ] Create `web/backend/.env.example`.
- [ ] Create `web/frontend` Next.js TypeScript app.
- [ ] Create `web/frontend/.env.example`.
- [ ] Confirm backend starts locally.
- [ ] Confirm frontend starts locally.
- [ ] Document startup commands in `web/backend/README.md` and
      `web/frontend/README.md`.

## Acceptance Criteria

- Existing repository files and MCP server packages are not moved.
- `web/backend` can run a FastAPI `/health` endpoint.
- `web/frontend` can run a Next.js development server.
- No external database, Redis, OAuth provider, storage provider, or academic API
  credentials are required for the skeleton startup.
- The structure leaves clear extension points for configuration, database,
  storage, jobs, authentication, and shared services.

