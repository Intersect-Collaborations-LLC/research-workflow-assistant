# Getting Started

This is the complete setup and orientation guide for the research-workflow-assistant. If you followed the [Quick Start in the README](../README.md#quick-start) and everything worked, you can skip ahead to [Working with Projects](#working-with-projects).

> **Prefer an interactive walkthrough?** Open Copilot Chat in VS Code and type
> `@setup`. It will guide you through every step below — environment
> validation, API key configuration, MCP server verification, and first-project
> creation — in a conversational format.
>
> **Already set up but something broke?** Use `@troubleshooter` for issue diagnosis,
> targeted repair steps, and day-to-day usage guidance.

During setup, RWA now also asks for a default author profile so future reports and manuscripts can start with the correct author metadata. New projects can then override or extend that metadata with project-specific authors.

## Quick Troubleshooting Flow

Follow this when setup appears broken:

1. Run `python scripts/validate_setup.py`
2. Run `python scripts/mcp_smoke_check.py`
3. If either fails, open Command Palette and run `MCP: List Servers`
4. If servers still fail, run `@troubleshooter` and share both script outputs

Decision path:

- No servers in MCP list: check `.vscode/mcp.json`, selected Python interpreter, then restart/reload VS Code
- Servers listed but tools unavailable: open a new Copilot Chat session
- Setup report shows wrong projects root: set `PROJECTS_ROOT=./my_projects` in `.env` and restart MCP servers

## Prerequisites

- [VS Code](https://code.visualstudio.com/) 1.99+ with GitHub Copilot (agent mode enabled)
- [Python](https://www.python.org/downloads/) 3.11 or later
- [R](https://cran.r-project.org/) 4.0+ (optional — for R-based analysis workflows)
- [Quarto](https://quarto.org/docs/get-started/) CLI (**recommended** — required for rendering all RWA templates to HTML, PDF, Word, PowerPoint, dashboards, and slides. Quarto is the default output layer for all RWA documents. See [docs/posit-quarto-guide.md](posit-quarto-guide.md) for the full ecosystem guide.)
- [Zotero](https://www.zotero.org/) desktop app (optional — for reference management; see [docs/zotero-plugins-guide.md](zotero-plugins-guide.md) for recommended plugins)
- A GitHub Copilot subscription with chat access

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/research-workflow-assistant.git
cd research-workflow-assistant
```

### 2. Install MCP servers

Each MCP server is a standalone Python package. Install them in development mode:

```bash
# Create a virtual environment (recommended)
python -m venv .venv

# Activate it
# Windows:
& .venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

# Install all MCP servers
pip install -e mcp-servers/_shared
pip install -e mcp-servers/pubmed-server
pip install -e mcp-servers/openalex-server
pip install -e mcp-servers/semantic-scholar-server
pip install -e mcp-servers/europe-pmc-server
pip install -e mcp-servers/crossref-server
pip install -e mcp-servers/zotero-server
pip install -e mcp-servers/zotero-local-server
pip install -e mcp-servers/prisma-tracker
pip install -e mcp-servers/project-tracker
pip install -e mcp-servers/chat-exporter
pip install -e mcp-servers/bibliography-manager
pip install -e mcp-servers/google-workspace-server
```

> **VS Code task shortcut:** You can also run `Ctrl+Shift+P` → "Tasks: Run Task" → "Install All MCP Servers" to install everything with a single click.

### 3. Configure API keys

Copy the example environment file and fill in your keys:

```bash
cp .env.example .env
```

Edit `.env` with your credentials. Each MCP server **automatically loads** this file on startup, so you do not need to set system-level environment variables.

```ini
# Required for PubMed (increases rate limit from 3/sec to 10/sec)
NCBI_API_KEY=your_key_here

# Required for OpenAlex (free API key)
OPENALEX_API_KEY=your_key_here

# Optional for Semantic Scholar (authenticated access)
S2_API_KEY=your_key_here

# Recommended for CrossRef (polite pool)
CROSSREF_EMAIL=your@email.com

# Required for Zotero
ZOTERO_API_KEY=your_key_here
# Numeric User ID (NOT your username) — find it at: https://www.zotero.org/settings/keys
ZOTERO_USER_ID=12345678

# Optional for Google Drive and Google Docs integration
GOOGLE_OAUTH_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8765/

# Optional: custom directories for tracking data
# PRISMA_PROJECT_DIR=./review-tracking
# PROJECT_TRACKER_DIR=./project-tracking

# Projects root directory (default: ./my_projects)
# Can be an absolute path to store projects elsewhere
PROJECTS_ROOT=./my_projects
```

See [api-setup-guide.md](api-setup-guide.md) for step-by-step instructions on obtaining each key.

### 4. Verify the setup

Open the workspace in VS Code and check that MCP servers start properly:

1. Open the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`)
2. Select "MCP: List Servers"
3. All 12 servers should appear and show as available

You can also test individual servers from the terminal:

```bash
python -m pubmed_server --help
```

You can also run the automated validation script:

```bash
python scripts/validate_setup.py
```

> **VS Code task shortcut:** `Ctrl+Shift+P` → "Tasks: Run Task" → "Validate Research Assistant Setup"

For a quick startup check after interpreter/server changes, run:

> `Ctrl+Shift+P` → "Tasks: Run Task" → "MCP Smoke Check (Project Tracker)"

### Troubleshooting

#### MCP servers not connecting to Copilot

The most common reason servers don't appear as tools in Copilot Chat is that `.vscode/mcp.json` is pointing to the wrong Python executable. The `command` field must use your **venv Python** — not just `python`, which may resolve to a system install that doesn't have the MCP packages.

The shipped `mcp.json` already uses the correct path:

```json
"command": "${workspaceFolder}/.venv/Scripts/python"   // Windows
"command": "${workspaceFolder}/.venv/bin/python"        // macOS/Linux
```

If you are on macOS/Linux, edit `.vscode/mcp.json` and change `Scripts/python` to `bin/python` for every server entry.

After editing, restart the MCP servers:

1. Open the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`)
2. Run **"MCP: List Servers"**
3. Click the **Start** (▶) button next to any stopped server, or use **"MCP: Restart Servers"**

#### Other common issues

| Problem | Solution |
|---------|----------|
| "Module not found" errors | Install the servers: run task "Install All MCP Servers", or `pip install -e mcp-servers/pubmed-server ...` |
| Default interpreter path could not be resolved | Verify `.vscode/settings.json` has `"python.defaultInterpreterPath": ".venv"`. Then run Command Palette → "Python: Select Interpreter" → choose `.venv`. If it still appears once at startup, run "Developer: Reload Window" and select `.venv` again to clear stale cache. |
| Need a quick MCP startup check | Run task "MCP Smoke Check (Project Tracker)". If it fails, use `@troubleshooter` and share the task output. |
| Servers not listed in MCP panel | Verify `.vscode/mcp.json` exists and is valid JSON. Restart VS Code. |
| Server crashes immediately | Run `python -m <server_module>` in terminal (with venv active) to see the error. |
| API keys not loading | The `.env` file must be at the workspace root. Servers auto-load it on startup via `python-dotenv`. |
| Zotero local not detecting data | Set `ZOTERO_DATA_DIR` in `.env` to the folder containing `zotero.sqlite` (e.g., `C:\Users\you\Zotero`). |
| Servers start but tools are "not available" | Open a **new** Copilot Chat session after starting servers. Existing sessions may not pick up newly started servers. |

## Working with Projects

Research projects are stored in a **private projects folder** that is not committed to version control. By default this is the `my_projects/` directory inside the assistant repository.

### Creating a project

Ask any agent to initialize a project, or use `@project-manager` directly:

```
@project-manager Initialize a project called "My Review" in my_projects/my-review.
```

This creates the following structure inside `my_projects/my-review/`:

```
my-review/
  ai-contributions-log.md
  project-config.yaml
  project-tracking/
    project.yaml
    tasks.yaml
    decisions.yaml
  review-tracking/       (if PRISMA tracking is initialized)
    prisma-flow.json
```

When you create a project through `@setup` or `@project-manager`, RWA should also prompt for the authors who will appear on reports or manuscripts from that project. Those details belong in `project-config.yaml` under `research_assistant.authors`, while your reusable personal defaults stay in `.rwa-user-config.yaml` under `default_author`.

Recommended `project-config.yaml` pattern:

```yaml
research_assistant:
  project_type: systematic-review
  reporting_standard: prisma-2020
  authors:
    - name: "Lead Author"
      credentials: "MPH"
      corresponding: true
      email: "author@example.org"
      orcid: "0000-0000-0000-0000"
      affiliation:
        name: "Organization"
        city: "City"
        state: "State / Province"
        country: "Country"
  output_defaults:
    bibliography: references.bib
    csl: vancouver-superscript.csl   # Resolved via: project config → user config → vancouver-superscript fallback
    include_rwa_methods_disclosure: true
    include_rwa_acknowledgments: true
```

The `csl` field determines which citation style is used when rendering. RWA resolves the style using a three-level priority chain:

1. **Project config** — `output_defaults.csl` in the project's `project-config.yaml`
2. **User config** — `default_citation_style` in `.rwa-user-config.yaml`
3. **Fallback** — `vancouver-superscript` (Vancouver superscript numbered)

The shared style library lives in `csl/` with 11 pre-bundled styles. Additional styles can be downloaded on demand from the [Zotero Style Repository](https://www.zotero.org/styles) using `@setup` or the `bib_download_csl_style` tool. Each project gets its own copy of the `.csl` file for portability. See `csl/README.md` for the full list of bundled styles.

### Using an external projects folder

If you want projects stored elsewhere (e.g., a OneDrive-synced folder), set `PROJECTS_ROOT` in your `.env`:

```ini
PROJECTS_ROOT=C:\Users\you\OneDrive\Research Projects
```

Relative project paths (like `my-review`) will then resolve under that folder instead of `my_projects/`.

### Switching between projects

Use the project-tracker or prisma-tracker tools to switch context:

```
@project-manager Switch to my-review project.
```

Or pass `project_path` directly to any tool call. Priority order:

1. Explicit `project_path` parameter on the tool call
2. Active project set via `set_active_project` / `set_active_review`
3. Relative paths resolve under `PROJECTS_ROOT` (recommended: `./my_projects`)
4. Legacy fallback: `PROJECT_DIR` / `PRISMA_PROJECT_DIR`

### Listing projects

```
@project-manager List all my projects.
```

This scans `PROJECTS_ROOT` and shows initialized projects with their status.

### Working with external / existing projects

You can point the assistant at any directory on your filesystem by providing an absolute path:

```
@project-manager Set active project to C:\Users\you\Documents\existing-project.
```

The assistant will create `project-tracking/` and `review-tracking/` folders inside that directory for its tracking data.

### Cross-workspace usage

If you work in a separate VS Code workspace, you have two options:

1. **Multi-root workspace** — add both the assistant repo and your project as workspace folders. Use the template at `templates/research-workspace.code-workspace.example`.

2. **Portable MCP config** — copy `templates/portable-mcp-config.json` to your project's `.vscode/mcp.json` and update the paths. This gives your project access to all 12 MCP servers without needing the assistant repo open.

## Chat Session Export

RWA can export your Copilot Chat conversations to QMD (Quarto Markdown) files for reproducibility and audit trails. This captures user requests, model responses, tool calls, and optionally model thinking blocks.

### CLI script

List all chat sessions for this workspace:

```bash
python scripts/export_chat_session.py --list
```

Export the most recent session to a project's `chat-logs/` directory:

```bash
python scripts/export_chat_session.py --latest --project my_projects/my-review
```

Export a specific session by ID:

```bash
python scripts/export_chat_session.py --session-id <id> --project my_projects/my-review
```

Options:
- `--verbose` — include full tool call input/output (default: summary only)
- `--no-thinking` — exclude model thinking blocks (default: included in collapsible `<details>` sections)

### MCP server

The `chat-exporter` MCP server exposes the same functionality as tools in Copilot Chat:
- `list_sessions` — list available sessions for this workspace
- `export_session` — export a specific session by ID
- `export_latest` — export the most recent session

### Third-party alternative

[SpecStory](https://specstory.com/) is a VS Code extension that automatically saves all Copilot Chat conversations to Markdown files in your repository. It runs continuously in the background and requires no manual export steps. Consider using it alongside or instead of the built-in export tools.

## Using the Agents

### Starting a research workflow

1. Open Copilot Chat in agent mode
2. Tag the agent you need:
  - `@research-orchestrator` for end-to-end guidance and handoff prompts across all stages
  - `@setup` for first-time setup or full environment reconfiguration
   - `@systematic-reviewer` for systematic reviews
   - `@data-analyst` for statistical analysis
   - `@academic-writer` for manuscript drafting
   - `@research-planner` for protocol and planning
   - `@project-manager` for progress tracking
  - `@verification-coordinator` for verification workbook design, execution support, and verifier preference logging
  - `@troubleshooter` for diagnosing errors, fixing environment issues, and usage support
  - `@developer` for bug fixes, feature requests, and codebase improvements

### Example: Starting a systematic review

```
@research-orchestrator I am starting a scoping review in my project. Route me stage by stage and provide the exact next agent prompt each time.
```

### Example: Direct specialist usage

```
@systematic-reviewer I want to conduct a systematic review on the effectiveness 
of mobile health interventions for maternal mental health in low-income countries. 
Help me develop a PICO framework and search strategy.
```

### Example: Tracking a project

```
@project-manager Initialize a new project called "mHealth Maternal Mental Health Review" 
with phases for protocol, searching, screening, extraction, synthesis, and writing. 
The target completion date is 2026-03-01.
```

### Example: Analyzing extracted data

```
@data-analyst I have extracted data from 23 studies on intervention effectiveness. 
Help me conduct a random-effects meta-analysis using R with the metafor package.
```

## Using Templates

Templates are in the `templates/` directory. Copy one to start your work:

```bash
# Start a new systematic review protocol
cp templates/systematic-review/protocol.qmd my-review/protocol.qmd

# Start a manuscript
cp templates/manuscript/imrad.qmd my-paper/manuscript.qmd
```

Render with Quarto:

```bash
quarto render my-review/protocol.qmd --to docx
```

The manuscript, protocol, and report templates now assume cite-bearing outputs should include author front matter, `bibliography`, `csl`, a Methods mention of RWA when relevant, and an acknowledgments / AI-disclosure section. Replace placeholders with verified author metadata and references before rendering.

## ICMJE Compliance

This tool enforces ICMJE authorship guidelines. Key points:

- AI tools cannot be listed as authors
- All AI assistance must be disclosed in the Methods section or Acknowledgments
- The `compliance/` folder contains checklists and templates for proper disclosure
- Agents will remind you of these requirements and help generate disclosure statements

## Search Result Storage

When you run a literature search with a `project_path` parameter, results are automatically persisted to a per-project SQLite database at `{project}/data/search_results.db`. This enables downstream analysis in both R and Python without re-running searches.

### How it works

- **Opt-in**: Results are only stored when `project_path` is provided to a search tool. Searches without a project context remain ephemeral.
- **All 5 search servers** support storage: PubMed, OpenAlex, Semantic Scholar, Europe PMC, and CrossRef.
- **Deduplication**: A built-in `deduplicated_results` view groups results by DOI or PMID across sources.
- **Query & export tools**: Each search server also provides `get_stored_results` and `export_stored_results` tools.

### Accessing results from R

```r
library(DBI)
library(RSQLite)
con <- dbConnect(SQLite(), "my_projects/my-review/data/search_results.db")
results <- dbReadTable(con, "results")
deduped  <- dbReadTable(con, "deduplicated_results")
dbDisconnect(con)
```

### Accessing results from Python

```python
import sqlite3
import pandas as pd

con = sqlite3.connect("my_projects/my-review/data/search_results.db")
results = pd.read_sql("SELECT * FROM results", con)
deduped  = pd.read_sql("SELECT * FROM deduplicated_results", con)
con.close()
```

### Schema

The database contains two tables and one view:

- **`searches`**: Log of every search executed (source, query, timestamp, total_count, parameters).
- **`results`**: Individual records with normalized fields (doi, pmid, title, authors_json, journal, year, volume, issue, pages, abstract) plus an `extra_json` column for source-specific metadata.
- **`deduplicated_results`** (view): Groups results by DOI or PMID to identify cross-database duplicates.

### Script-First Search (Reproducible Scripts)

Each search server also offers a `_scripted` variant tool (e.g., `search_pubmed_scripted`, `search_works_scripted`). When you use the scripted variant, the server:

1. **Generates a standalone Python script** in `{project}/scripts/search_{source}_{timestamp}.py`
2. **Executes the script** via subprocess
3. **Reads back results** from the SQLite database

The generated script is a thin runner stub that imports `rwa_result_store.search_runners`, so `rwa-shared` must be installed in the Python environment. You can re-run it independently to reproduce the exact same search:

```bash
# Re-run a search script directly
python my_projects/my-review/scripts/search_pubmed_20260315_021043.py
```

This produces a complete audit trail: the script records exactly which API was called, with which parameters, and stores the results in the same SQLite database. If script execution fails (e.g., network issues), the server automatically falls back to the standard direct API call.

### Bibliographic Export

All search servers expose an `export_stored_bibliography` tool that exports stored results to standard reference formats:

- **BibTeX** (`.bib`) — for use with LaTeX, Quarto, and Zotero
- **RIS** (`.ris`) — for import into Zotero, EndNote, Mendeley
- **CSL-JSON** (`.json`) — for programmatic use and Pandoc/Citeproc

Example via Copilot Chat:

```
Export my stored results as BibTeX to my_projects/my-review/exports/results.bib
```

Or from Python:

```python
from rwa_result_store import export_results_bibtex, export_results_ris, export_results_csljson

# Export deduplicated results as BibTeX
export_results_bibtex("my_projects/my-review", output_path="exports/results.bib", deduplicated=True)

# Export as RIS
export_results_ris("my_projects/my-review", output_path="exports/results.ris")

# Export as CSL-JSON
export_results_csljson("my_projects/my-review", output_path="exports/results.json")
```

The `deduplicated` parameter (default `True`) uses the DOI/PMID deduplication view to avoid duplicate entries across databases.

### Batch Zotero Import

Two tools on the Zotero server streamline importing search results into your Zotero library:

- **`batch_add_by_doi`**: Import multiple DOIs at once (up to 200). Supports a preview/confirm workflow.
- **`import_from_result_store`**: Read DOIs directly from the project's SQLite database and import them into Zotero.

Typical workflow:

1. Run searches across databases with `project_path` to populate the SQLite store
2. Preview the import: the tool shows how many DOIs will be added and lists the first few
3. Confirm to execute: items are added to Zotero with full metadata from CrossRef

```
Import results from my project database into Zotero (preview first)
```

You can filter by source (e.g., only PubMed results) and optionally specify a Zotero collection.

See `compliance/ai-disclosure-template.md` for ready-to-use disclosure language.

## Citing R and Python Packages

Citing the software packages you use in your analysis is important for **developer credit**, **reproducibility**, and **transparency**. The [FORCE11 Software Citation Principles](https://doi.org/10.7717/peerj-cs.86) recommend citing all software important to the research outcome.

RWA includes ready-to-use Quarto templates that generate BibTeX entries for your packages:

### R

Copy `analysis-templates/R/cite-r-packages.qmd` into your project, edit the package list, and render it. The template demonstrates three approaches:

1. **`knitr::write_bib()`** — built-in, zero extra dependencies. Writes BibTeX entries for any list of packages.
2. **`grateful::cite_packages()`** — auto-scans loaded packages and generates a formatted citation paragraph plus `.bib` file.
3. **`sessionInfo()`** — captures the full environment (all package versions) for reproducibility.

Quick example (run in R):

```r
# Generate BibTeX entries for your key packages
knitr::write_bib(c("base", "metafor", "ggplot2", "dplyr"), file = "packages.bib")
```

Then reference `packages.bib` in your Quarto document:

```yaml
bibliography:
  - references.bib
  - packages.bib
```

See the [rOpenSci guide: How to Cite R and R Packages](https://ropensci.org/blog/2021/11/16/how-to-cite-r-and-r-packages/) for background and best practices.

### Python

Copy `analysis-templates/python/cite-python-packages.qmd` into your project, edit the package list, and render it. The template:

- Uses `importlib.metadata` (standard library) to extract package metadata.
- Includes preferred citations (published papers with DOIs) for major scientific packages: numpy, scipy, pandas, scikit-learn, matplotlib, statsmodels, seaborn, lifelines, and pingouin.
- Falls back to `@Manual{}` BibTeX entries for other packages.

Quick example (run in Python):

```python
import importlib.metadata
meta = importlib.metadata.metadata("pandas")
print(f"{meta['Name']} v{meta['Version']} by {meta.get('Author', 'Unknown')}")
```

### In your manuscript

Include a sentence like this in your Methods section:

> All analyses were performed using R Statistical Software (v4.4.1; R Core Team, 2025). Meta-analysis was conducted with metafor (v4.6-0; Viechtbauer, 2010). Data visualization used ggplot2 (v3.5.1; Wickham, 2016).

The `@data-analyst` agent will include a software citations section when generating analysis code. The `@academic-writer` agent can help draft the software paragraph for your Methods section.

## Next Steps

- Run `@setup` for a guided interactive setup
- Read [database-access.md](database-access.md) to understand what each database offers
- Read [architecture.md](architecture.md) for a technical overview of the system
- Explore the `compliance/` folder for PRISMA, MOOSE, and RoB 2 checklists
- Try the agents with a sample research question
