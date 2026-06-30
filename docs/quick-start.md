# Quick Start

This is the shortest path to a working Research Workflow Assistant setup.

## 1. Prerequisites

- VS Code with GitHub Copilot chat access
- Python 3.11+
- Optional: Zotero desktop, R, Quarto

## 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it:

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# macOS/Linux
source .venv/bin/activate
```

## 3. Install MCP servers

```bash
pip install -e mcp-servers/_shared \
            -e mcp-servers/pubmed-server \
            -e mcp-servers/openalex-server \
            -e mcp-servers/semantic-scholar-server \
            -e mcp-servers/europe-pmc-server \
            -e mcp-servers/crossref-server \
            -e mcp-servers/zotero-server \
            -e mcp-servers/zotero-local-server \
            -e mcp-servers/prisma-tracker \
            -e mcp-servers/project-tracker \
            -e mcp-servers/chat-exporter \
            -e mcp-servers/bibliography-manager \
            -e mcp-servers/google-workspace-server
```

Or run VS Code task: `Install All MCP Servers`.

> **Reproducibility tip:** Consider installing [SpecStory](https://specstory.com/) — a VS Code extension that automatically saves all Copilot Chat conversations to Markdown files in your repository. RWA also includes a built-in chat export script (`scripts/export_chat_session.py`) that converts sessions to QMD.

## 4. Configure environment

Copy `.env.example` to `.env` and set at least:

- `NCBI_API_KEY` (recommended)
- `OPENALEX_API_KEY` (recommended)
- `ZOTERO_API_KEY` and `ZOTERO_USER_ID` (if using Zotero)
- `PROJECTS_ROOT=./my_projects` (recommended default)

## 5. Validate setup

```bash
python scripts/validate_setup.py
python scripts/mcp_smoke_check.py
```

You can use `--json` with either script for machine-readable output.

## 6. Confirm servers in VS Code

- Open Command Palette
- Run `MCP: List Servers`
- Confirm all 12 servers are available

## 7. Start guided onboarding

In Copilot Chat, run:

```text
@setup
```

For deep troubleshooting and multi-project workflows, see [getting-started.md](getting-started.md).
