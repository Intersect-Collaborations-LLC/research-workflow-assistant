# 14 - Next.js User Interface

## Purpose

Implement the researcher-facing Next.js frontend for the RWA web app. The UI
should guide non-technical researchers through project setup, protocol review,
searches, results, PRISMA, bibliography, exports, jobs, and audit history.

The browser UI calls FastAPI HTTP endpoints. MCP compatibility is handled by
guide 15, not by frontend code.

## Scope

This guide covers:

- Frontend application structure.
- API client conventions.
- Authentication-aware routing.
- Core screens and navigation.
- Form, table, job polling, and review patterns.
- Accessibility and usability expectations.

This guide does not select a large component framework unless the project later
chooses one explicitly.

This guide consumes the API and workflow boundaries from guides 05-13. It
should not redefine backend ownership, storage, job, or audit behavior.

## Directory Layout

Use the Next.js App Router:

```text
web/frontend/src/
  app/
    layout.tsx
    page.tsx
    projects/
      page.tsx
      new/
        page.tsx
      [projectId]/
        page.tsx
        searches/
          page.tsx
        prisma/
          page.tsx
        documents/
          protocol/
            page.tsx
        references/
          page.tsx
        audit/
          page.tsx
  components/
    layout/
    projects/
    searches/
    prisma/
    documents/
    references/
    jobs/
    audit/
    ui/
  lib/
    api.ts
    auth.ts
    jobs.ts
  types/
    api.ts
```

Keep reusable UI primitives small and local unless a design system is adopted.

## API Client

Create a typed API helper in:

```text
web/frontend/src/lib/api.ts
```

It should:

- read `NEXT_PUBLIC_API_BASE_URL`
- send `credentials: "include"`
- parse JSON responses
- normalize API errors
- expose typed methods for common calls

Example shape:

```ts
export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    throw new ApiError(response.status, await response.text());
  }

  return response.json() as Promise<T>;
}
```

## Authentication UX

Initial auth behavior:

- On load, call `GET /api/auth/me`.
- If unauthenticated, show a sign-in screen with GitHub login.
- Login navigates to backend `/auth/github/login`.
- Logout calls backend `/auth/logout`.

Authenticated pages should not render project data until the user identity is
known.

## Navigation

Use a project-centered layout:

- Project dashboard
- Protocol
- Searches
- Results
- PRISMA
- References
- Outputs/exports
- Audit

The top-level project list and create project screen should be available after
login.

Avoid exposing implementation concepts such as MCP servers, storage prefixes,
database rows, or filesystem paths in the main UI.

## Core Screens

### Project List

Show:

- project title
- review type
- research question preview
- status
- updated timestamp

Actions:

- create project
- open project

### Project Dashboard

Show:

- project metadata
- setup status
- recent searches
- result counts
- PRISMA summary
- protocol status
- recent jobs
- recent audit events

### Search Builder

Provide structured controls for:

- provider selection
- concepts
- terms
- filters
- date range
- result limit
- query preview
- run search

### Search Results

Use a paginated table with:

- title
- authors
- year
- journal
- DOI/PMID
- source
- abstract preview
- provenance details

### Protocol Review

Use section editors with:

- section title
- Markdown text area or structured fields
- save
- approve
- render
- artifact status

### PRISMA

Use grouped numeric inputs and warnings. Show a flow preview from API data.

### References

Show reference rows, validation status, source provenance, and export actions.

### Audit

Show timestamped events with expandable details.

## Job Polling

Create a helper:

```text
web/frontend/src/lib/jobs.ts
```

Behavior:

- Poll active jobs every 1-2 seconds.
- Stop polling on terminal states.
- Surface errors clearly.
- Allow feature screens to resume polling after reload if they know the job ID.

Terminal states:

```text
succeeded
failed
cancelled
```

## Forms And Validation

Use client-side validation for immediate feedback, but rely on backend
validation as authoritative.

Patterns:

- Keep form labels explicit.
- Show field-level errors where possible.
- Preserve user input after failed submissions.
- Do not require all protocol details before project creation.
- Use warnings for partial PRISMA inconsistency where backend allows it.

## Visual And Accessibility Expectations

The UI should feel like a working research operations tool:

- predictable navigation
- compact but readable forms
- tables optimized for scanning
- clear empty states
- visible provenance
- accessible labels and focus states
- responsive behavior for laptop and tablet widths

Avoid a marketing-style landing page as the primary experience.

## Tests

Add frontend tests only after the test framework is selected. At minimum, the
frontend should support:

- linting
- type checking
- API client unit tests where practical
- smoke tests for core routes

End-to-end tests are covered in guide 16.

## Implementation Checklist

- [ ] Create typed API client.
- [ ] Implement auth state loading.
- [ ] Implement project list screen.
- [ ] Implement project creation screen.
- [ ] Implement project dashboard.
- [ ] Implement search builder and preview.
- [ ] Implement search history and results table.
- [ ] Implement job polling helper.
- [ ] Implement PRISMA screen.
- [ ] Implement protocol review screen.
- [ ] Implement references screen.
- [ ] Implement audit screen.
- [ ] Add lint/typecheck commands to README.

## Acceptance Criteria

- Authenticated users can navigate the core project workflow.
- Frontend calls FastAPI endpoints with credentials.
- Frontend never calls MCP servers directly.
- Project, search, PRISMA, protocol, references, jobs, and audit screens have
  usable first versions.
- Active jobs show progress and terminal state.
- UI avoids exposing backend storage paths or implementation internals.
