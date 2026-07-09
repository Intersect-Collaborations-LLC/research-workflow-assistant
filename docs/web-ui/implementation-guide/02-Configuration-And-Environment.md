# 02 - Configuration And Environment

## Purpose

Define the configuration system for the RWA web backend and frontend. This
guide should be completed before database setup, storage, authentication, job
handling, or feature workflows.

Configuration must support both localhost and hosted deployments without
hard-coding local-only assumptions. Values should come from environment
variables and may be loaded from `.env` files during local development.

## Configuration Principles

- Use environment variables as the source of truth.
- Allow `.env` files for local development.
- Do not commit real secrets.
- Keep backend and frontend configuration separate.
- Validate required settings at application startup where possible.
- Make database and storage providers configurable by URL.
- Support localhost development against non-localhost services, such as local
  Postgres or cloud/object storage.

## Backend Settings Module

Create a backend settings module:

```text
web/backend/src/rwa_web/core/config.py
```

Use `pydantic-settings`:

```python
from functools import lru_cache

from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="RWA_WEB_",
        extra="ignore",
    )

    app_name: str = "Research Workflow Assistant Web"
    environment: str = "local"
    debug: bool = False

    database_url: str = "sqlite:///./rwa-web.db"
    storage_url: str = "file://./rwa-web-data"

    session_secret: str = Field(default="", repr=False)

    github_client_id: str = ""
    github_client_secret: str = Field(default="", repr=False)
    github_callback_url: str = "http://localhost:8000/auth/github/callback"

    ncbi_api_key: str = Field(default="", repr=False)
    openalex_api_key: str = Field(default="", repr=False)
    openalex_email: str = ""
    s2_api_key: str = Field(default="", repr=False)
    crossref_email: str = ""
    zotero_api_key: str = Field(default="", repr=False)
    zotero_user_id: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

The exact field list may evolve, but configuration should remain centralized
and typed.

## Environment Variable Names

Use the `RWA_WEB_` prefix for web-app-specific settings:

```text
RWA_WEB_ENVIRONMENT=local
RWA_WEB_DEBUG=true
RWA_WEB_DATABASE_URL=sqlite:///./rwa-web.db
RWA_WEB_STORAGE_URL=file://./rwa-web-data
RWA_WEB_SESSION_SECRET=change-me
RWA_WEB_GITHUB_CLIENT_ID=
RWA_WEB_GITHUB_CLIENT_SECRET=
RWA_WEB_GITHUB_CALLBACK_URL=http://localhost:8000/auth/github/callback
```

Academic database and external service credentials should be accepted through
the web settings layer, but they may map to existing RWA environment names when
calling shared service code:

```text
RWA_WEB_NCBI_API_KEY=
RWA_WEB_OPENALEX_API_KEY=
RWA_WEB_OPENALEX_EMAIL=
RWA_WEB_S2_API_KEY=
RWA_WEB_CROSSREF_EMAIL=
RWA_WEB_ZOTERO_API_KEY=
RWA_WEB_ZOTERO_USER_ID=
```

When integrating existing shared code that reads legacy variable names directly,
the service boundary may translate web settings into the expected environment
or should refactor that code to accept explicit credentials.

## Backend `.env.example`

Create:

```text
web/backend/.env.example
```

Example content:

```text
RWA_WEB_ENVIRONMENT=local
RWA_WEB_DEBUG=true
RWA_WEB_DATABASE_URL=sqlite:///./rwa-web.db
RWA_WEB_STORAGE_URL=file://./rwa-web-data
RWA_WEB_SESSION_SECRET=replace-with-a-random-development-secret

RWA_WEB_GITHUB_CLIENT_ID=
RWA_WEB_GITHUB_CLIENT_SECRET=
RWA_WEB_GITHUB_CALLBACK_URL=http://localhost:8000/auth/github/callback

RWA_WEB_NCBI_API_KEY=
RWA_WEB_OPENALEX_API_KEY=
RWA_WEB_OPENALEX_EMAIL=
RWA_WEB_S2_API_KEY=
RWA_WEB_CROSSREF_EMAIL=
RWA_WEB_ZOTERO_API_KEY=
RWA_WEB_ZOTERO_USER_ID=
```

Do not include real credentials.

## Frontend Environment

Create:

```text
web/frontend/.env.example
```

Initial content:

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Only expose values to the browser that are safe to be public. Do not expose
GitHub client secrets, API keys, database URLs, storage secrets, or session
secrets through `NEXT_PUBLIC_*` variables.

## Localhost Defaults

Localhost defaults should be easy to run:

```text
RWA_WEB_DATABASE_URL=sqlite:///./rwa-web.db
RWA_WEB_STORAGE_URL=file://./rwa-web-data
```

These are defaults only. Localhost developers may use Postgres, S3-compatible
storage, memory storage for tests, or other suitable SQLAlchemy/`fsspec`
providers.

## Hosted Defaults

Hosted deployments should use Postgres as the application database system of
record:

```text
RWA_WEB_DATABASE_URL=postgresql+psycopg://user:password@host:5432/rwa_web
```

Hosted storage should use a backend-managed storage provider configured through
`RWA_WEB_STORAGE_URL`.

SQLite is problematic and not recommended for hosted deployments because of
concurrency, locking, backup, and scaling concerns.

## Settings Validation

Add lightweight startup validation:

- `database_url` must be non-empty.
- `storage_url` must be non-empty.
- `session_secret` must be set outside test mode.
- GitHub OAuth settings must be set before OAuth login is enabled.

Avoid failing startup for optional academic API credentials. Instead, surface
credential status in the UI and disable or warn on features that require missing
credentials.

## API Exposure

Add a safe settings/status endpoint later, not in the initial skeleton, such as:

```text
GET /api/config/status
```

It may expose non-secret readiness information:

```json
{
  "environment": "local",
  "database_configured": true,
  "storage_configured": true,
  "github_oauth_configured": false,
  "providers": {
    "pubmed": "configured",
    "openalex": "missing",
    "crossref": "configured"
  }
}
```

Never return secret values.

## Test Configuration

Tests should override settings without relying on developer `.env` files.

Recommended test defaults:

```text
RWA_WEB_ENVIRONMENT=test
RWA_WEB_DATABASE_URL=sqlite:///:memory:
RWA_WEB_STORAGE_URL=memory://
RWA_WEB_SESSION_SECRET=test-secret
```

Use dependency overrides or monkeypatching where appropriate.

## Implementation Checklist

- [ ] Add `pydantic-settings` to backend dependencies.
- [ ] Create `rwa_web.core.config`.
- [ ] Define the `Settings` class.
- [ ] Define `get_settings()`.
- [ ] Create `web/backend/.env.example`.
- [ ] Create `web/frontend/.env.example`.
- [ ] Update backend README with configuration notes.
- [ ] Add tests for settings defaults.
- [ ] Add tests for environment overrides.

## Acceptance Criteria

- Backend settings load from environment variables.
- Backend settings can load from `web/backend/.env` during local development.
- Frontend API base URL is configured through `NEXT_PUBLIC_API_BASE_URL`.
- No real secrets are committed.
- Local defaults work without Postgres, cloud storage, Redis, OAuth, or academic
  API credentials.
- Configuration supports local development against alternate SQLAlchemy and
  `fsspec` providers.

