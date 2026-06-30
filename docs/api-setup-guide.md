# API Setup Guide

This guide explains how to obtain API keys and credentials for each academic database used by the research-workflow-assistant.

## Quick Start: Which Keys To Set First

If you are setting up RWA for the first time, configure these in this order:

| Priority | Key(s) | Why | Typical Time |
|---|---|---|---|
| 1 | `OPENALEX_API_KEY` | Required for OpenAlex tools | 2 min |
| 2 | `NCBI_API_KEY` | Improves PubMed throughput (10 req/sec vs 3 req/sec) | 2 min |
| 3 | `PROJECTS_ROOT` | Ensures project tracking targets the correct folder | 1 min |
| 4 | `ZOTERO_API_KEY`, `ZOTERO_USER_ID` | Needed for Zotero integration features | 3 min |
| Optional | `S2_API_KEY`, `CROSSREF_EMAIL`, `ZOTERO_DATA_DIR`, `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET` | Nice-to-have for specific workflows | 1-10 min |

Recommended default:

```ini
PROJECTS_ROOT=./my_projects
```

## PubMed / NCBI E-utilities

**Key type:** NCBI API Key
**Required:** Recommended (works without, but rate-limited to 3 requests/second)
**With key:** 10 requests/second

### How to get your key

1. Go to [NCBI](https://www.ncbi.nlm.nih.gov/) and create an account (or sign in)
2. Click your username in the top-right corner, then select "Account settings"
3. Scroll to "API Key Management"
4. Click "Create an API Key"
5. Copy the generated key

### Configuration

```ini
NCBI_API_KEY=your_key_here
```

### Documentation

- [NCBI E-utilities docs](https://www.ncbi.nlm.nih.gov/books/NBK25497/)
- [Usage guidelines](https://www.ncbi.nlm.nih.gov/books/NBK25497/#chapter2.Usage_Guidelines_and_Requiremen)

---

## OpenAlex

**Key type:** API Key (free)
**Required:** Yes (free key gives $1/day of API usage)
**Rate limit:** 100 requests/second; $1/day free budget covers ~1,000 searches or ~10,000 list/filter calls

### How to get your key

1. Go to [OpenAlex](https://openalex.org/) and create a free account
2. Navigate to [API Key Settings](https://openalex.org/settings/api-key)
3. Copy your API key

### Configuration

```ini
OPENALEX_API_KEY=your_key_here
```

### Free tier daily budget

Your free key gives you $1/day to spend across API operations:

| Operation | Cost per call | Free daily allowance |
|-----------|--------------|---------------------|
| Get single entity (by ID/DOI) | Free | Unlimited |
| List + filter | $0.0001 | ~10,000 calls |
| Search (full-text) | $0.001 | ~1,000 calls |
| Semantic search | $0.01 | ~100 calls |

Monitor usage at [openalex.org/settings/usage](https://openalex.org/settings/usage) or via the `/rate-limit` endpoint.

### Documentation

- [OpenAlex Developer Docs](https://developers.openalex.org/)
- [Authentication & Pricing](https://developers.openalex.org/api-reference/authentication)
- [API Reference](https://developers.openalex.org/api-reference/introduction)

---

## Semantic Scholar

**Key type:** API Key
**Required:** No (works without, but recommended for stable access)
**Rate limit:** 1 req/sec (standard key — same for unauthenticated and authenticated). Higher-tier keys may allow more; check your approval email.
**Key inactivity:** Keys inactive for ~60 days may be revoked

### How to get your key

1. Go to the [Semantic Scholar API key request form](https://www.semanticscholar.org/product/api#api-key-form)
3. Fill out the form describing your use case and expected endpoints
4. Complete the [API License Agreement](https://www.semanticscholar.org/product/api/license)
5. You will receive an API key via email (may take a few business days)

### Configuration

```ini
S2_API_KEY=your_key_here
```

### License requirements

By using the Semantic Scholar API, you agree to the [API License Agreement](https://www.semanticscholar.org/product/api/license). Key obligations:

- **Attribution**: Include attribution to "Semantic Scholar" in any published materials that use S2 data
- **Citation**: Cite [The Semantic Scholar Open Data Platform](https://www.semanticscholar.org/paper/cb92a7f9d9dbcf9145e32fdfa0e70e2a6b828eb1) in scientific publications that use API results
- **Rate limits**: Do not attempt to exceed or circumvent rate limits
- **Exponential backoff**: Apply exponential backoff on 429 responses (implemented in the MCP server)
- **Key security**: Do not share your API key beyond authorized users in your organization

### Documentation

- [API docs](https://api.semanticscholar.org/api-docs/)
- [API overview](https://www.semanticscholar.org/product/api)
- [API tutorial](https://www.semanticscholar.org/product/api/tutorial) — step-by-step guide covering keyword search, recommendations, author lookups, bulk search, dataset downloads, and query syntax
- [License agreement](https://www.semanticscholar.org/product/api/license)

---

## Europe PMC

**Key type:** None required
**Required:** No authentication needed
**Rate limits:** Fair use; be respectful with request frequency

### Configuration

No configuration needed. The Europe PMC server works out of the box.

### Documentation

- [Europe PMC REST API](https://europepmc.org/RestfulWebService)
- [Article search](https://europepmc.org/searchsyntax)

---

## CrossRef

**Key type:** Email address (for polite pool)
**Required:** No, but strongly recommended
**Benefit:** Faster responses via the "polite pool"

### How to configure

Provide your email address:

```ini
CROSSREF_EMAIL=your@email.com
```

For projects with heavy usage, consider registering for the [CrossRef Plus service](https://www.crossref.org/services/metadata-retrieval/).

### Documentation

- [CrossRef REST API](https://api.crossref.org/)
- [API docs](https://api.crossref.org/swagger-ui/index.html)

---

## Zotero

**Key type:** API Key + User ID
**Required:** Yes (for Zotero integration)

### How to get your credentials

1. Go to [Zotero Settings](https://www.zotero.org/settings/keys)
2. Log in (create an account if needed)
3. Click "Create new private key"
4. Give it a description (e.g., "research-workflow-assistant")
5. Under "Personal Library," check:
   - Allow library access
   - Allow write access
   - Allow notes access
6. Click "Save Key"
7. Copy the generated key

To find your User ID:

1. Go to [Zotero Settings](https://www.zotero.org/settings/keys)
2. Your **numeric** User ID is displayed at the top of the page (e.g., `12345678`)

> **Important:** The User ID is a number, not your username. Look for the line that says "Your userID for use in API calls is **XXXXXXX**" near the top of the page.

### Configuration

```ini
ZOTERO_API_KEY=your_key_here
ZOTERO_USER_ID=12345678
```

### Working with group libraries

If you need to access a group library instead of your personal library, set the group ID:

```ini
ZOTERO_GROUP_ID=your_group_id
```

Find group IDs at: `https://www.zotero.org/groups/`

### Documentation

- [Zotero Web API v3](https://www.zotero.org/support/dev/web_api/v3/start)
- [API key permissions](https://www.zotero.org/support/dev/web_api/v3/basics)

---

## Zotero Local (PDF Text & Annotations)

**Key type:** File system path (no API key needed)
**Required:** No (optional — enhances Zotero integration with local PDF access)

The `zotero-local` MCP server reads directly from your local Zotero installation to enable:

- **Full-text extraction** from PDFs stored in your Zotero library
- **Annotation extraction** — highlights, sticky notes, underlines from both PDF-embedded annotations and Zotero's built-in reader annotations
- **Keyword search** across all stored PDFs
- **Notes** from local database (faster than API, works offline)
- **Better BibTeX integration** (optional) for stable citation keys and enhanced export

### Prerequisites

1. [Zotero desktop](https://www.zotero.org/download/) must be installed
2. PDFs must be stored locally (not "linked" to external URLs only)
3. PyMuPDF is installed automatically with the `zotero-local-server` package

### Finding your Zotero data directory

1. Open Zotero → Edit → Settings (or Preferences on macOS) → Advanced → Files and Folders
2. The "Data Directory Location" shows the path, e.g.:
   - **Windows**: `C:\Users\YourName\Zotero`
   - **macOS**: `/Users/YourName/Zotero`
   - **Linux**: `/home/yourname/Zotero`
3. That folder will contain `zotero.sqlite` and a `storage/` subdirectory

> **Auto-detection:** If you leave `ZOTERO_DATA_DIR` blank, the server will try to auto-detect standard locations. Set the variable explicitly if auto-detection fails.

### Configuration

```ini
# Path to your Zotero data directory (folder containing zotero.sqlite)
ZOTERO_DATA_DIR=C:\Users\YourName\Zotero
```

### Better BibTeX (optional)

If you use [Better BibTeX](https://retorque.re/zotero-better-bibtex/) for citation key management:

1. Install BBT in Zotero: Tools → Add-ons → Install from file (or URL)
2. Zotero must be **running** for BBT features to work (BBT exposes a local JSON-RPC API)
3. No additional configuration needed — the server auto-detects BBT at `localhost:23119`

**BBT features available:**
- Stable, human-readable citation keys (e.g., `smith2024climate`)
- Enhanced BibTeX/BibLaTeX export
- Citation key lookup and reverse search

### Documentation

- [Zotero data directory](https://www.zotero.org/support/zotero_data)
- [Better BibTeX](https://retorque.re/zotero-better-bibtex/)
- [Zotero 7 reader annotations](https://www.zotero.org/support/pdf_reader)

---

## Google Workspace (Drive and Docs)

**Key type:** OAuth client ID + client secret (Desktop app)
**Required:** No (required only for Google Drive/Docs integration)

The `google-workspace` MCP server enables:

- Google Drive file listing, upload, and import to local projects
- Exporting local review files to Google Docs with deterministic anchor tokens
- Pulling Google Docs comments and replies back into RWA project artifacts
- Building local comment-to-proposal files for human review before edits

### How to create OAuth credentials

1. Open [Google Cloud Console](https://console.cloud.google.com/)
2. Create/select a project
3. Enable **Google Drive API** and **Google Docs API**
4. Go to **APIs & Services → Credentials**
5. Create **OAuth client ID** with application type **Desktop app**
6. Copy the client ID and client secret
7. Add the redirect URI you plan to use (default in RWA: `http://localhost:8765/`)

### Configuration

```ini
GOOGLE_OAUTH_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8765/
# Optional
# GOOGLE_OAUTH_SCOPES=https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/documents.readonly
GOOGLE_WORKSPACE_TOKEN_PATH=./secrets/google-workspace-token.json
```

### Scope defaults

By default, RWA requests:

- `https://www.googleapis.com/auth/drive`
- `https://www.googleapis.com/auth/documents.readonly`

You can override scopes with `GOOGLE_OAUTH_SCOPES`.

### Documentation

- [Google Drive API](https://developers.google.com/drive/api/guides/about-sdk)
- [Google Docs API](https://developers.google.com/workspace/docs/api)
- [Google OAuth for installed apps](https://developers.google.com/identity/protocols/oauth2/native-app)

> **See also:** [google-workspace-guide.md](google-workspace-guide.md) for the full OAuth setup walkthrough, the Google Docs review-workflow round-trip, the complete tool reference, and troubleshooting.

---

## Summary Table

| Service | Auth Required | Key Type | Free Tier | Rate Limit |
|---------|:---:|----------|-----------|------------|
| PubMed | Recommended | API Key | Yes (unlimited) | 3/sec without key, 10/sec with key |
| OpenAlex | Yes (free) | API Key | $1/day free | 100/sec, $1/day budget |
| Semantic Scholar | No | API Key | Yes (1 req/sec) | 1 req/sec (standard key) |
| Europe PMC | No | None | Yes (unlimited) | Fair use |
| CrossRef | No | Email (polite pool) | Yes (unlimited) | Polite pool preferred |
| Zotero | Yes | API Key + User ID | Yes (300MB storage) | Fair use |
| Zotero Local | No | File path | Yes (local only) | Disk I/O bound |
| Google Workspace | Yes (for integration) | OAuth client ID + secret | Yes | Quota-based |

## Environment File Template

Create a `.env` file in the project root:

```ini
# PubMed / NCBI
NCBI_API_KEY=

# OpenAlex (free API key required)
OPENALEX_API_KEY=

# Semantic Scholar (optional, for authenticated access)
S2_API_KEY=

# CrossRef (email for polite pool)
CROSSREF_EMAIL=

# Zotero (required for reference management)
ZOTERO_API_KEY=
ZOTERO_USER_ID=

# Zotero Local (optional — for PDF text/annotations)
ZOTERO_DATA_DIR=

# Google Workspace OAuth (optional — for Drive/Docs integration)
GOOGLE_OAUTH_CLIENT_ID=
GOOGLE_OAUTH_CLIENT_SECRET=
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8765/
# Optional comma-separated scope override
# GOOGLE_OAUTH_SCOPES=https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/documents.readonly
GOOGLE_WORKSPACE_TOKEN_PATH=./secrets/google-workspace-token.json

# Tracking directories (optional, defaults to ./review-tracking and ./project-tracking)
PRISMA_PROJECT_DIR=
PROJECT_TRACKER_DIR=
```
