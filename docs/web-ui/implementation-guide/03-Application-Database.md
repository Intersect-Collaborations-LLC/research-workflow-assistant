# 03 - Application Database

## Purpose

Set up the SQLAlchemy-backed application database for the RWA web app. This
database stores web application state such as users, OAuth accounts, projects,
searches, search results, audit events, and background jobs.

The database backend must be configured by environment. Localhost deployments
may use any suitable SQLAlchemy-supported database. Hosted deployments should
use Postgres as the system of record. SQLite is acceptable for local development
and tests, but is problematic and not recommended for hosted deployments.

## Scope

This guide covers:

- SQLAlchemy engine/session setup.
- Declarative model base.
- Initial application schema.
- Alembic migrations.
- Database initialization for local development.
- Test database patterns.

This guide does not implement API endpoints, OAuth flows, storage, search
execution, or workers. Later guides will use the database layer created here.

## Dependencies

Add backend dependencies:

```toml
dependencies = [
    "sqlalchemy>=2.0",
    "alembic>=1.13",
]
```

Add database drivers as optional or documented deployment dependencies:

```toml
[project.optional-dependencies]
postgres = [
    "psycopg[binary]>=3.2",
]
```

SQLite support comes from the Python standard library.

## Directory Layout

Create or extend:

```text
web/backend/
  alembic.ini
  migrations/
    env.py
    script.py.mako
    versions/
  src/rwa_web/
    db/
      __init__.py
      base.py
      session.py
    models/
      __init__.py
      user.py
      project.py
      search.py
      job.py
      audit.py
```

## Database Session Setup

Create:

```text
web/backend/src/rwa_web/db/session.py
```

Recommended shape:

```python
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from rwa_web.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

Async SQLAlchemy may be considered later. Use synchronous SQLAlchemy initially
to keep integration with existing synchronous RWA code straightforward.

## Declarative Base

Create:

```text
web/backend/src/rwa_web/db/base.py
```

Recommended shape:

```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

Import all models in `models/__init__.py` so Alembic can discover metadata.

## ID And Timestamp Conventions

Use string UUID primary keys for application-level entities:

```python
import uuid

from sqlalchemy.orm import Mapped, mapped_column


def new_uuid() -> str:
    return str(uuid.uuid4())


id: Mapped[str] = mapped_column(primary_key=True, default=new_uuid)
```

Use timezone-aware timestamps where possible:

```python
from datetime import UTC, datetime


def utc_now() -> datetime:
    return datetime.now(UTC)
```

Keep the schema portable across SQLite and Postgres. Avoid Postgres-only column
types in the first implementation unless wrapped carefully.

## Initial Models

### User

Stores application users.

Fields:

- `id`
- `display_name`
- `email`
- `avatar_url`
- `created_at`
- `updated_at`
- `last_login_at`

### OAuthAccount

Stores linked OAuth identity records.

Fields:

- `id`
- `user_id`
- `provider`
- `provider_subject`
- `provider_login`
- `provider_email`
- `created_at`
- `updated_at`

Constraints:

- Unique on `provider`, `provider_subject`.

### Project

Stores web-managed research projects.

Fields:

- `id`
- `user_id`
- `slug`
- `title`
- `review_type`
- `research_question`
- `storage_prefix`
- `status`
- `created_at`
- `updated_at`

Constraints:

- Unique on `user_id`, `slug`.

Notes:

- `storage_prefix` is the backend-managed project storage location relative to
  the configured project storage root/provider.
- Initial implementation only supports projects initiated within the web app.

### Search

Stores search execution metadata.

Fields:

- `id`
- `project_id`
- `user_id`
- `source`
- `query`
- `parameters_json`
- `total_count`
- `status`
- `job_id`
- `created_at`
- `completed_at`

Notes:

- `source` examples: `pubmed`, `openalex`, `semantic_scholar`,
  `europe_pmc`, `crossref`.
- `parameters_json` should use a portable JSON representation.

### SearchResult

Stores normalized search results.

Fields:

- `id`
- `search_id`
- `project_id`
- `user_id`
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

Indexes:

- `project_id`
- `search_id`
- `doi`
- `pmid`

Notes:

- Keep normalized core fields for common UI use.
- Store provider-specific metadata in `extra_json`.

### Job

Stores long-running work.

Fields:

- `id`
- `user_id`
- `project_id`
- `type`
- `status`
- `payload_json`
- `progress`
- `result_json`
- `error`
- `attempts`
- `created_at`
- `started_at`
- `finished_at`
- `updated_at`

Initial statuses:

- `queued`
- `running`
- `succeeded`
- `failed`
- `cancelled`

### AuditEvent

Stores audit and provenance events.

Fields:

- `id`
- `user_id`
- `project_id`
- `event_type`
- `summary`
- `details_json`
- `created_at`

Examples:

- `project.created`
- `search.started`
- `search.completed`
- `export.generated`
- `document.generated`
- `human.approved`

## JSON Columns

Use SQLAlchemy `JSON` for JSON-like fields where practical:

```python
from sqlalchemy import JSON
```

Be conservative with querying JSON fields to keep behavior portable across
SQLite and Postgres. Prefer normalized columns for fields that need filtering,
sorting, or indexing.

## Alembic Setup

Initialize Alembic in `web/backend`:

```powershell
alembic init migrations
```

Configure `alembic.ini` and `migrations/env.py` to read `RWA_WEB_DATABASE_URL`
through `rwa_web.core.config.get_settings()`.

`migrations/env.py` should import model metadata:

```python
from rwa_web.db.base import Base
from rwa_web import models  # noqa: F401

target_metadata = Base.metadata
```

Generate the initial migration:

```powershell
alembic revision --autogenerate -m "create initial web schema"
alembic upgrade head
```

Review autogenerated migrations before committing them.

## Local Development

Default local development can use:

```text
RWA_WEB_DATABASE_URL=sqlite:///./rwa-web.db
```

Developers may also use local Postgres:

```text
RWA_WEB_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/rwa_web
```

The application should not assume that localhost means SQLite.

## Hosted Deployment

Hosted deployments should set:

```text
RWA_WEB_DATABASE_URL=postgresql+psycopg://...
```

Document SQLite as not recommended for hosted mode because of concurrency,
locking, backup, and scaling concerns.

## FastAPI Dependency

Use `get_db()` as a FastAPI dependency in later API guides:

```python
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from rwa_web.db.session import get_db

DbSession = Annotated[Session, Depends(get_db)]
```

Do not create database sessions inside browser-facing route logic without a
clear dependency boundary.

## Tests

Add database tests under:

```text
web/backend/tests/test_database.py
```

Minimum tests:

- Settings can point to a test SQLite database.
- Tables can be created from metadata in a test database.
- A user can be inserted and queried.
- A project can be inserted and scoped to a user.
- Search and search result records can be inserted and queried by project.
- Job status can be updated.

Use temporary SQLite files or in-memory SQLite for unit tests. Postgres
integration tests can be added later.

## Implementation Checklist

- [ ] Add SQLAlchemy and Alembic dependencies.
- [ ] Add optional Postgres driver dependency.
- [ ] Create `db/base.py`.
- [ ] Create `db/session.py`.
- [ ] Create initial model files.
- [ ] Import models in `models/__init__.py`.
- [ ] Initialize Alembic under `web/backend`.
- [ ] Configure Alembic to use application settings.
- [ ] Generate and review initial migration.
- [ ] Add database tests.
- [ ] Update backend README with database setup and migration commands.

## Acceptance Criteria

- Database URL is read from configuration.
- SQLAlchemy models define users, OAuth accounts, projects, searches, search
  results, jobs, and audit events.
- Alembic can create the initial schema.
- Local development works with SQLite by default.
- Local development can be configured to use Postgres.
- Hosted deployments are documented to use Postgres.
- Tests verify basic model creation and persistence.

