# 05 - Authentication And User Identity

## Purpose

Implement GitHub OAuth authentication and the user identity boundary for the
RWA web app. Authenticated identity is required before project lifecycle,
storage access, searches, jobs, exports, documents, and audit records can be
scoped safely.

The web app should support hosted multi-user deployments and localhost
development. GitHub OAuth is the initial identity provider.

## Scope

This guide covers:

- GitHub OAuth login and callback handling.
- Session cookie setup.
- User and OAuth account creation.
- Current-user dependency for FastAPI routes.
- Project and record ownership boundaries.
- Local development behavior when OAuth is not configured.

This guide does not implement project APIs, search workflows, or frontend
screens beyond the minimum login/logout integration.

## Dependencies

Add backend dependencies:

```toml
dependencies = [
    "authlib>=1.3",
    "itsdangerous>=2.2",
]
```

FastAPI's session middleware uses signed cookies through Starlette. Authlib is
used for the OAuth client.

## Configuration

Use settings introduced in guide 02:

```text
RWA_WEB_SESSION_SECRET=
RWA_WEB_GITHUB_CLIENT_ID=
RWA_WEB_GITHUB_CLIENT_SECRET=
RWA_WEB_GITHUB_CALLBACK_URL=http://localhost:8000/auth/github/callback
```

`RWA_WEB_SESSION_SECRET` must be set outside tests. GitHub OAuth routes may
return a clear configuration error when GitHub credentials are missing.

## Backend Layout

Create or extend:

```text
web/backend/src/rwa_web/
  api/
    auth.py
    deps.py
  auth/
    __init__.py
    github.py
    sessions.py
  services/
    users.py
```

Register the auth router in `rwa_web.main`.

## Session Middleware

Add session middleware during app creation:

```python
from starlette.middleware.sessions import SessionMiddleware

from rwa_web.core.config import get_settings

settings = get_settings()

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    same_site="lax",
    https_only=settings.environment == "production",
)
```

Hosted deployments should use HTTPS and secure cookies. Localhost development
may use non-HTTPS cookies.

## OAuth Flow

Implement routes:

```text
GET /auth/github/login
GET /auth/github/callback
POST /auth/logout
GET /api/auth/me
```

Behavior:

- `/auth/github/login` starts the GitHub OAuth authorization flow.
- `/auth/github/callback` exchanges the code, fetches GitHub user profile data,
  creates or updates local user records, and stores `user_id` in the session.
- `/auth/logout` clears the session.
- `/api/auth/me` returns the current authenticated user or `401`.

The callback should not trust browser-provided identity fields. Identity comes
from GitHub's OAuth response and user API.

## User Upsert Service

Create a service function that maps a GitHub identity to application records:

```python
def upsert_github_user(
    db: Session,
    *,
    provider_subject: str,
    login: str,
    email: str | None,
    display_name: str | None,
    avatar_url: str | None,
) -> User:
    ...
```

Rules:

- Find existing `OAuthAccount` by `provider="github"` and
  `provider_subject`.
- If found, update user profile fields and `last_login_at`.
- If not found, create a `User` and linked `OAuthAccount`.
- Preserve the stable local `User.id` after first creation.
- Commit inside the service or make transaction ownership explicit and
  consistent with the surrounding backend pattern.

## Current User Dependency

Create a FastAPI dependency:

```python
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from rwa_web.db.session import get_db


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
```

All browser-facing project, search, job, document, bibliography, and audit APIs
must use this dependency or an equivalent authorization boundary.

## Authorization Boundary

Authentication answers "who is this user." Authorization must also check "does
this user own or have access to this project or record."

Initial implementation is single-owner:

- Every project has one `user_id`.
- Searches, search results, jobs, and audit events include `user_id`.
- API queries filter by both record ID and `user_id`.
- Browser requests pass project IDs, never storage prefixes or filesystem
  paths.

Example project lookup:

```python
project = (
    db.query(Project)
    .filter(Project.id == project_id, Project.user_id == current_user.id)
    .one_or_none()
)
if project is None:
    raise HTTPException(status_code=404)
```

Returning `404` for inaccessible project records avoids revealing whether
another user's project exists.

## Frontend Integration

The frontend should call:

```text
GET /api/auth/me
```

to determine whether the user is signed in.

The login button can navigate to:

```text
{API_BASE_URL}/auth/github/login
```

Logout should call:

```text
POST /auth/logout
```

The browser should use credentials for API calls when the frontend and backend
run on different localhost ports:

```ts
fetch(url, { credentials: "include" })
```

Configure CORS later if needed for local cross-origin development.

## Local Development

Local development should use a real GitHub OAuth app when testing auth.

Recommended callback:

```text
http://localhost:8000/auth/github/callback
```

Do not add a permanent unauthenticated bypass for hosted deployments. If a
developer-only fake user mode is introduced for tests or local demos, guard it
behind explicit test/local configuration and document that it must not be
enabled in hosted environments.

## Tests

Add tests under:

```text
web/backend/tests/test_auth.py
```

Minimum tests:

- `/api/auth/me` returns `401` without a session.
- A session containing a valid `user_id` returns the current user.
- Logout clears the session.
- GitHub user upsert creates a user and OAuth account.
- GitHub user upsert updates an existing linked user.
- Project lookup helpers reject records owned by another user.

Mock Authlib/GitHub network calls. Do not require live GitHub credentials for
automated tests.

## Implementation Checklist

- [ ] Add Authlib and session dependencies.
- [ ] Add session middleware to the FastAPI app.
- [ ] Create GitHub OAuth client setup.
- [ ] Implement login, callback, logout, and current-user routes.
- [ ] Implement GitHub user upsert service.
- [ ] Implement current-user dependency.
- [ ] Ensure protected routes filter by `current_user.id`.
- [ ] Add auth tests with mocked GitHub responses.
- [ ] Update backend README with GitHub OAuth setup instructions.

## Acceptance Criteria

- Users can sign in with GitHub OAuth.
- Signed-in sessions resolve to a local `User` record.
- OAuth accounts are linked by stable GitHub subject ID.
- Protected API routes can require authenticated users.
- Project and application records are scoped to the authenticated user.
- Automated tests do not require live GitHub credentials.
- No secret OAuth values are exposed to the frontend.
