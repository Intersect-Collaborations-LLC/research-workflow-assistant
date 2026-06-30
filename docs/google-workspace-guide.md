# Google Workspace Guide

The `google-workspace` MCP server connects RWA to **Google Drive** and **Google Docs**, enabling a collaborative review workflow: export a local document to Google Docs, let reviewers add comments, then pull those comments back into RWA and map them to specific lines in your source file for human-approved edits.

This guide covers OAuth setup, the review-workflow round-trip, the full tool reference, and troubleshooting. For the abbreviated credential-creation steps and environment variable reference, see the [Google Workspace section of the API setup guide](api-setup-guide.md#google-workspace-drive-and-docs).

---

## Prerequisites

- A Google account with access to Google Drive and Google Docs
- A Google Cloud project with the **Google Drive API** and **Google Docs API** enabled
- An OAuth client ID of type **Desktop app** (see [OAuth Setup](#oauth-setup) below)
- The `google-workspace` MCP server installed and started (it is included in the standard RWA install; verify via the Command Palette → "MCP: List Servers")

> **When is this required?** Google Workspace integration is optional. You only need it if you want to use Google Drive import/export or the Google Docs review round-trip. All other RWA features work without it.

---

## OAuth Setup

RWA authenticates to Google using an OAuth Desktop client ID. The token is stored locally and never sent anywhere except Google's token endpoints.

### 1. Create OAuth credentials

1. Open the [Google Cloud Console](https://console.cloud.google.com/)
2. Create or select a project
3. Enable the **Google Drive API** and **Google Docs API** (APIs & Services → Library)
4. Go to **APIs & Services → Credentials**
5. Create an **OAuth client ID** with application type **Desktop app**
6. Copy the client ID and client secret
7. Configure the OAuth consent screen (External app type is fine for personal use; add your own email as a test user while the app is in testing)

### 2. Set the redirect URI

The default redirect URI used by RWA is:

```
http://localhost:8765/
```

Add this to the authorized redirect URIs for your OAuth client in the Google Cloud Console. The trailing slash is significant.

### 3. Configure environment variables

Add the following to your `.env` file in the project root:

```ini
GOOGLE_OAUTH_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8765/
GOOGLE_WORKSPACE_TOKEN_PATH=./secrets/google-workspace-token.json
```

Optional: override the default scopes (see [Configuration Reference](#configuration-reference)).

> **The `secrets/` directory is git-ignored.** The token file at `secrets/google-workspace-token.json` contains your refresh token and is never committed to version control. The `.gitignore` entry for `secrets/` is included with RWA by default.

### 4. Restart the MCP server

After editing `.env`, restart the `google-workspace` MCP server via the Command Palette → "MCP: List Servers", then open a new Copilot Chat session so the new environment variables are picked up.

---

## Connecting Your Account

Authentication is a two-step OAuth dance. Run both steps in Copilot Chat (or ask any RWA agent to do it for you).

### Step 1: Get the authorization URL

Call `gws_auth_get_authorization_url`. It returns:

- `authorization_url` — open this in a browser
- `state` — internal CSRF token (handled automatically)
- `redirect_uri` — the redirect URI in effect
- `scopes` — the scopes being requested

### Step 2: Exchange the authorization code

After you approve access in the browser, Google redirects to `http://localhost:8765/` with a `code` parameter. Call `gws_auth_exchange_code` with either:

- the full redirect URL (e.g., `http://localhost:8765/?code=...&scope=...`), or
- just the `code` query parameter value

The tool exchanges the code for a refreshable token, stores it at `secrets/google-workspace-token.json`, and reports success.

### Verify the connection

Call `gws_auth_status` to confirm the token is valid. It reports `connected`, `valid`, `expired`, `has_refresh_token`, the scopes, and the expiry time. Expired tokens with a refresh token are refreshed automatically on the next tool call.

### Revoke access

Call `gws_auth_revoke` to revoke the token at Google's revoke endpoint and delete the local token file. Use this if you want to disconnect, change accounts, or reset scopes.

---

## Google Drive Integration

Three tools cover Drive file management:

### `gws_drive_list_files`

Lists files in your Google Drive. Auto-excludes trashed files and supports shared drives.

- `query` (optional) — Google Drive query string (e.g., `"mimeType='application/vnd.google-apps.document'"` to list only Google Docs)
- `page_size` (optional, default 20) — number of files to return

### `gws_drive_import_file`

Imports a Drive file into your RWA project. Google Docs are exported to plain text, Markdown, or PDF as specified; other files are downloaded as-is.

- `file_id` — the Google Drive file ID
- `project_path` — the target RWA project path
- `output_path` (optional) — relative path under the project's `imports/` directory
- `export_mime_type` (optional, default `text/plain`) — for Google Docs: `text/plain`, `text/markdown`, or `application/pdf`

Returns the local file path, SHA-256 hash, and byte count. Files land in `{project}/imports/`.

### `gws_drive_upload_file`

Uploads or updates a local file on Google Drive.

- `local_file_path` — absolute path to the local file
- `project_path` — the RWA project path (for sync tracking)
- `parent_folder_id` (optional) — Drive folder to upload into
- `convert_to_google_doc` (optional, default false) — convert the upload to a Google Doc
- `update_file_id` (optional) — if set, updates an existing Drive file instead of creating a new one

---

## Google Docs Review Workflow

The review workflow is a round-trip: export a local file to Google Docs with deterministic line anchors, let reviewers comment, then pull the comments back and map them to your source lines.

### Step 1: Export a review copy

Call `gws_docs_export_review_copy`:

- `project_path` — the RWA project path
- `local_target_file` — the local file to export (e.g., a `.qmd` manuscript)
- `title` (optional) — title for the Google Doc
- `parent_folder_id` (optional) — Drive folder for the new doc

This uploads the file to Google Docs and inserts deterministic line-anchor tokens of the form `[[RWA-LINE:000042:1a2b3c4d]]` at each line. It writes:

- an **anchor map** (`*.anchors.json`) mapping anchor tokens to local line numbers
- a **per-doc manifest** (`*.manifest.json`) recording the doc ID, local file, and sync state

Both live under the project's sync directory.

### Step 2: Reviewers add comments

Open the Google Doc in a browser and add comments as usual. RWA does not need to be running during this phase.

### Step 3: Pull comments

Call `gws_docs_pull_comments`:

- `doc_id` — the Google Doc ID (from the manifest)
- `project_path` — the RWA project path
- `include_resolved` (optional, default false) — include resolved comments

This writes `comments-{doc_id}.json` under the project's sync directory and updates the manifest with the latest pull timestamp.

### Step 4: Build change proposals

Call `gws_docs_build_change_proposals`:

- `doc_id` — the Google Doc ID
- `project_path` — the RWA project path
- `local_target_file` (optional) — override the manifest's recorded local file
- `include_resolved` (optional, default false)

This maps each pulled comment back to a local source line using the anchor map. Matching is deterministic for anchored comments (confidence 0.99); a fuzzy `SequenceMatcher` fallback handles comments that drifted from their anchor. Output is two files in the project's `proposals/` directory:

- `{doc_id}-{timestamp}-proposals.json` — structured proposals
- `{doc_id}-{timestamp}-proposals.qmd` — a Quarto document for human review

Review the `.qmd` file, accept or reject each proposal, and apply approved edits to your source file manually. RWA never auto-edits your source.

### Inspect sync state

Call `gws_docs_list_sync_mappings` with `project_path` to list all per-doc manifests in a project. Useful for finding the doc ID for a given local file or checking the last pull timestamp.

---

## Per-Project Sync Artifacts

Each project that uses the review workflow accumulates artifacts under a sync root:

| Artifact | Purpose |
|----------|---------|
| `*.manifest.json` | Per-doc manifest: doc ID, local file, anchor map path, last pull timestamp |
| `*.anchors.json` | Anchor map: anchor token → local line number |
| `comments-{doc_id}.json` | Pulled comments and replies for a doc |
| `proposals/{doc_id}-{timestamp}-proposals.json` | Structured change proposals |
| `proposals/{doc_id}-{timestamp}-proposals.qmd` | Human-readable Quarto proposal document |

These files are project-specific and safe to commit (they contain no secrets). The exact sync root path is resolved per project.

---

## Configuration Reference

| Variable | Required | Default | Description |
|----------|:---:|---------|-------------|
| `GOOGLE_OAUTH_CLIENT_ID` | Yes | — | OAuth Desktop client ID |
| `GOOGLE_OAUTH_CLIENT_SECRET` | Yes | — | OAuth Desktop client secret |
| `GOOGLE_OAUTH_REDIRECT_URI` | No | `http://localhost:8765/` | Redirect URI registered with Google |
| `GOOGLE_OAUTH_SCOPES` | No | `drive`, `documents.readonly` | Comma-separated scope URLs |
| `GOOGLE_WORKSPACE_TOKEN_PATH` | No | `./secrets/google-workspace-token.json` | Local token file path |

### Default scopes

- `https://www.googleapis.com/auth/drive`
- `https://www.googleapis.com/auth/documents.readonly`

Override with `GOOGLE_OAUTH_SCOPES` (comma-separated) if you need different access. Changing scopes requires re-running the OAuth dance (`gws_auth_revoke` then `gws_auth_get_authorization_url`).

---

## Troubleshooting

### Token expired

If `gws_auth_status` reports `expired: true` and `has_refresh_token: true`, the next tool call will refresh the token automatically. No action needed. If the refresh fails, run `gws_auth_revoke` and re-authenticate.

### Token revoked or invalid

If `gws_auth_status` reports `connected: false`, run `gws_auth_get_authorization_url` and complete the OAuth dance again.

### Redirect URI mismatch

If Google rejects the redirect with a URI mismatch error, confirm that the `GOOGLE_OAUTH_REDIRECT_URI` in your `.env` exactly matches the authorized redirect URI in the Google Cloud Console, including the trailing slash. The default is `http://localhost:8765/`.

### Scope errors

If a tool fails with a permission or scope error, the token was likely granted before the required scope was added. Run `gws_auth_revoke`, then re-authenticate with `gws_auth_get_authorization_url` to request the updated scopes.

### MCP server not responding

If the `google-workspace` server does not appear in "MCP: List Servers" or tools are unavailable, open the Command Palette → "MCP: List Servers", start or restart the server, then open a new Copilot Chat session. Confirm that the `command` in `.vscode/mcp.json` points to the venv Python (`${workspaceFolder}/.venv/Scripts/python` on Windows).

---

## Further Documentation

- [Google Drive API](https://developers.google.com/drive/api/guides/about-sdk)
- [Google Docs API](https://developers.google.com/workspace/docs/api)
- [Google OAuth for installed apps](https://developers.google.com/identity/protocols/oauth2/native-app)
- [Google Cloud Console](https://console.cloud.google.com/)
