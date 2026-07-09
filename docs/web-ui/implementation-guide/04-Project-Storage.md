# 04 - Project Storage

## Purpose

Create a small project storage abstraction for the RWA web app backed by
`fsspec`. All web-managed project files should be read and written through this
interface rather than direct filesystem calls.

The storage layer must support local development by default while allowing other
`fsspec` providers during localhost testing and hosted deployments.

## Scope

This guide covers:

- Storage configuration.
- A small `ProjectStorage` interface.
- Backend-managed project prefixes.
- Project initialization files.
- Safe path handling.
- Local and non-local storage testing.

This guide does not implement project API endpoints, document generation,
exports, or search execution.

## Dependencies

Add backend dependency:

```toml
dependencies = [
    "fsspec>=2024.0",
]
```

Provider-specific dependencies should be optional and added only when needed,
for example:

```toml
[project.optional-dependencies]
s3 = [
    "s3fs>=2024.0",
]
gcs = [
    "gcsfs>=2024.0",
]
```

Do not require cloud storage packages for the default local setup.

## Configuration

Storage is configured through:

```text
RWA_WEB_STORAGE_URL=file://./rwa-web-data
```

The storage URL is interpreted by `fsspec`.

Examples:

```text
file://./rwa-web-data
memory://
s3://bucket-name/rwa-web
gcs://bucket-name/rwa-web
```

Localhost development may use any suitable `fsspec` provider. The local
filesystem is only the default.

## Directory Layout

Create:

```text
web/backend/src/rwa_web/storage/
  __init__.py
  project_storage.py
  paths.py
```

## Storage Model

Each web-managed project receives a backend-owned `storage_prefix`, stored on
the `Project` database record.

Recommended prefix shape:

```text
users/{user_id}/projects/{project_id}
```

Example project files:

```text
users/{user_id}/projects/{project_id}/
  project-config.yaml
  ai-contributions-log.md
  project-tracking/
    project.yaml
    tasks.yaml
    decisions.yaml
  review-tracking/
    prisma-flow.json
  documents/
    protocol.qmd
  exports/
  data/
```

The browser should never provide the full storage path. Browser requests should
use project IDs. The backend resolves project IDs to storage prefixes.

## ProjectStorage Interface

Create a small interface that wraps `fsspec` and hides provider details from the
rest of the app.

Recommended initial API:

```python
from collections.abc import Iterable


class ProjectStorage:
    def exists(self, path: str) -> bool:
        ...

    def mkdir(self, path: str) -> None:
        ...

    def read_text(self, path: str) -> str:
        ...

    def write_text(self, path: str, content: str) -> None:
        ...

    def read_bytes(self, path: str) -> bytes:
        ...

    def write_bytes(self, path: str, content: bytes) -> None:
        ...

    def list(self, path: str) -> list[str]:
        ...

    def delete(self, path: str) -> None:
        ...
```

Keep the initial API intentionally small. Add streaming, copy, signed URLs, or
recursive operations only when a feature requires them.

## Backend Factory

Create a factory function:

```python
from functools import lru_cache

import fsspec

from rwa_web.core.config import get_settings


@lru_cache
def get_project_storage() -> ProjectStorage:
    settings = get_settings()
    fs, root = fsspec.core.url_to_fs(settings.storage_url)
    return ProjectStorage(fs=fs, root=root)
```

The concrete implementation should prepend the configured root to all
application-relative paths.

## Path Safety Rules

All paths passed to `ProjectStorage` must be application-relative paths.

Rules:

- Reject absolute paths.
- Reject paths containing `..`.
- Normalize path separators.
- Use POSIX-style paths internally, even on Windows.
- Never allow a browser request to provide a resolved filesystem path.
- Never join paths using string concatenation in route handlers.

Create a helper:

```python
from pathlib import PurePosixPath


def normalize_storage_path(path: str) -> str:
    candidate = PurePosixPath(path)
    if candidate.is_absolute():
        raise ValueError("Storage paths must be relative")
    if ".." in candidate.parts:
        raise ValueError("Storage paths may not contain '..'")
    return str(candidate)
```

Apply this normalization inside `ProjectStorage`, not only at callers.

## Project Initialization

Create a service function later used by project lifecycle code:

```python
def initialize_project_storage(
    storage: ProjectStorage,
    storage_prefix: str,
    project_title: str,
) -> None:
    ...
```

Initial files/directories:

```text
project-config.yaml
ai-contributions-log.md
project-tracking/
review-tracking/
documents/
exports/
data/
```

Initial content can be minimal:

```yaml
title: Example Project
created_by: rwa-web
```

Do not copy or import arbitrary existing project directories in the first
implementation. Project import is a future consideration.

## Storage And Database Boundary

The database stores project records, metadata, and `storage_prefix`.

The storage layer stores project artifacts:

- QMD documents
- YAML/JSON project artifacts
- BibTeX files
- Excel/CSV exports
- compatibility exports
- generated reports

Search results for hosted workflows live in SQLAlchemy-backed application
tables. Project-local SQLite search databases are compatibility exports, not the
hosted system of record.

## Handling Provider Differences

Different `fsspec` providers do not behave exactly like a local filesystem.

Implementation should avoid assuming:

- atomic directory renames
- reliable empty directory semantics
- local file locking
- SQLite compatibility on object storage
- OS-specific path behavior

Prefer simple read/write/list operations and explicit generated artifacts.

## Tests

Add tests under:

```text
web/backend/tests/test_project_storage.py
```

Minimum tests:

- `memory://` storage can write and read text.
- `file://` storage can write and read text in a temporary directory.
- absolute paths are rejected.
- paths containing `..` are rejected.
- project initialization creates expected files/directories.
- storage prefix generation does not depend on user-provided paths.

Use `memory://` for fast unit tests. Use a temporary local directory for file
provider tests.

## Implementation Checklist

- [ ] Add `fsspec` dependency.
- [ ] Create `storage/project_storage.py`.
- [ ] Create `storage/paths.py`.
- [ ] Implement `normalize_storage_path`.
- [ ] Implement `ProjectStorage`.
- [ ] Implement `get_project_storage`.
- [ ] Add project initialization helper.
- [ ] Add storage tests with `memory://`.
- [ ] Add storage tests with temporary `file://` path.
- [ ] Update backend README with storage configuration examples.

## Acceptance Criteria

- All project artifact storage goes through `ProjectStorage`.
- Storage provider is configured by `RWA_WEB_STORAGE_URL`.
- Local filesystem is the default local storage provider, but not hard-coded.
- Unsafe paths are rejected by the storage layer.
- Project storage prefixes are backend-owned.
- Initial project storage can be created without direct filesystem assumptions.
- Tests pass for both memory and local file storage providers.

