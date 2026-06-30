# Research Workflow Assistant

An open-source, modular AI research assistant that runs inside **[VS Code](https://code.visualstudio.com/) + [GitHub Copilot](https://github.com/features/copilot)**. It connects to academic databases via MCP (Model Context Protocol) servers and encodes research best practices through custom Copilot agents. Built for reproducibility, ICMJE compliance, and human-centered research.

All RWA outputs — manuscripts, protocols, reports, analysis scripts, dashboards, and progress briefs — use **[Quarto](https://quarto.org/)** (by [Posit](https://posit.co/)) as the default document format. Quarto supports R and Python code execution, multi-format rendering (HTML, PDF, Word, PowerPoint, dashboards, websites, books, slides), native Mermaid diagrams, and built-in bibliography management. See [docs/posit-quarto-guide.md](docs/posit-quarto-guide.md) for the full ecosystem guide.

> **Model note:** This project was developed and tested using **Claude Opus 4.6** and **GPT-5.3-Codex** in GitHub Copilot agent mode. You can switch between models depending on task type and preference. Other models available in Copilot ([model comparison](https://docs.github.com/en/copilot/reference/ai-models/model-comparison)) may also work, but behavior can vary by agent workflow, so validate critical outputs after switching.
>
> **Using OpenRouter with GitHub Copilot:** [OpenRouter](https://openrouter.ai/) is a routing service (it does not host its own models) that connects GitHub Copilot to models from many providers through a single API. In addition to frontier models from Anthropic and OpenAI, it gives access to capable but more affordable open-source and open-weight models. See the [OpenRouter + GitHub Copilot integration guide](https://openrouter.ai/works-with-openrouter/github-copilot) and the [model catalog sorted by agentic ability](https://openrouter.ai/models?order=agentic-high-to-low).
>
> Examples of open-source/open-weight models available via OpenRouter alongside the frontier models above (pricing per million tokens, as of June 2026):
>
> | Model | Provider | Context | Input $/M | Output $/M |
> |---|---|---|---|---|
> | GLM 5.2 | Z.ai | 1.05M | $0.94 | $3.00 |
> | DeepSeek V4 Pro | DeepSeek | 1.05M | $0.44 | $0.87 |
> | DeepSeek V4 Flash | DeepSeek | 1.05M | $0.09 | $0.18 |
> | MiniMax M3 | MiniMax | 1.05M | $0.30 | $1.20 |
> | Qwen3.7 Max | Alibaba | 1M | $1.25 | $3.75 |
> | Kimi K2.6 | Moonshot AI | 262K | $0.55 | $3.20 |
>
> For comparison, frontier models on the same catalog include Anthropic Claude Opus 4.8 ($5/$25), OpenAI GPT-5.5 ($5/$30), and Anthropic Claude Sonnet 4.6 ($3/$15). The open-source options above can produce similar results for RWA workflows at a fraction of the cost. As with any model switch, validate critical outputs after changing providers.

> **First time here?** Start with [docs/quick-start.md](docs/quick-start.md),
> or open Copilot Chat and type `@setup` for an interactive guided setup.
> If setup is complete and something is not working, use `@troubleshooter` for diagnostics and issue resolution.
> For the full walkthrough, see [docs/getting-started.md](docs/getting-started.md).

> **Important:** Before using non-setup agents, you must accept the user disclaimer once via `@setup`.

## Philosophy

The question isn't which AI research tool to adopt. It's whether researchers have the right tech stack to build their own.

RWA is a proof of concept for what becomes possible when researchers have a capable IDE, open-source tools, and access to a capable LLM. If your researchers already have VS Code, R, Python, Quarto, Markdown, and git, they have the building blocks. Give them LLM access, and someone on the team could build a custom, organization-compliant research workflow assistant in a few weeks, with MCP servers tailored to their specific needs.

Any specific implementation is going to be opinionated. This one integrates with Zotero, enforces ICMJE authorship guidelines, and defaults to Quarto for reproducible documents. Your organization might make entirely different choices, and that's fine.

What matters is **not locking researchers into a single platform**. Tools that sound impressive but limit you to one documentation system, one output format, one way of working are the kind of constraint that slows people down. The better path: meet researchers where they already are. Make their existing environment AI-capable. Don't replace their tools; connect them.

The stack already exists:

- **[Positron](https://positron.posit.co/) / [VS Code](https://code.visualstudio.com/)** for the IDE
- **[R](https://www.r-project.org/) and [Python](https://www.python.org/)** for analysis
- **[Quarto](https://quarto.org/) and Markdown** for reproducible documents
- **[Git](https://git-scm.com/)** for version control and collaboration
- **[MCP](https://modelcontextprotocol.io/)** for connecting LLMs to structured data sources

The missing piece for most organizations isn't a new product. It's access to a capable LLM within the tools researchers already use, and permission to experiment.

Read the [launch post on LinkedIn](https://www.linkedin.com/posts/andre-van-zyl_evidencesynthesis-systematicreview-publichealth-activity-7437474997612417024-yQ20) for the full backstory.

## Who Is This For?

Any researcher who wants AI-assisted support without surrendering intellectual ownership:

- **NGO and public sector researchers** managing evidence reviews or program evaluations
- **Government analysts** producing policy briefs backed by systematic evidence
- **Academic faculty and postdocs** running systematic reviews or multi-study projects
- **Independent researchers and consultants** needing structured, reproducible workflows
- **Research organizations** wanting standardized, auditable research processes

No PhD required. If you do research, this tool is for you.

## What It Does

| Capability | How |
|---|---|
| **Systematic literature reviews** | `@systematic-reviewer` agent guides PRISMA-compliant workflows: question refinement (PICO/PEO/SPIDER), search strategy development, database searching, screening, data extraction, risk of bias |
| **Academic database access** | MCP servers for PubMed, OpenAlex, Semantic Scholar, Europe PMC, and CrossRef |
| **Reference management** | Zotero MCP server: search library, add items by DOI, tag, organize collections, export BibTeX |
| **Data analysis** | `@data-analyst` agent generates reproducible R or Python analysis scripts in Quarto documents |
| **Academic writing** | `@academic-writer` agent scaffolds IMRaD manuscripts, manages citations, enforces ICMJE AI disclosure |
| **Research planning** | `@research-planner` agent helps with protocols, ethics applications, study design, grant writing |
| **Project management** | `@project-manager` agent tracks phases, milestones, tasks, decisions; generates progress briefs for colleagues |
| **End-to-end orchestration** | `@research-orchestrator` routes workflows across specialist agents, tracks stage progression, and provides ready-to-run handoff prompts |
| **Verification and reproducibility** | `@verification-coordinator` agent co-develops human-friendly, LLM-executable verification workbooks, tracks verifier preferences, and standardizes checkpoint evidence outputs |
| **Troubleshooting and support** | `@troubleshooter` agent diagnoses environment and MCP issues, validates API keys, and provides practical how-to help for day-to-day RWA usage |
| **Development and bug fixes** | `@developer` agent gathers requirements for bug fixes, feature requests, and codebase improvements, then directs to plan mode for implementation |
| **Chat session export** | Export Copilot Chat conversations to QMD for reproducibility via `scripts/export_chat_session.py` or `chat-exporter` MCP server |
| **Google Drive and Docs review sync** | `google-workspace` MCP server handles OAuth login, Drive import/export, and Docs comment-to-proposal round trips |
| **ICMJE compliance** | Built into every agent: human-in-the-loop mandate, audit trail, AI disclosure generation, authorship checklist |

## Architecture

```mermaid
graph TB
    YOU["👤 You · the Researcher<br/>All decisions · All ownership · All accountability"]

    VSCODE["VS Code + GitHub Copilot Chat"]

    YOU --> VSCODE

    subgraph AGENTS["Specialist AI Agents"]
        direction LR
        ORCH["@research-orchestrator<br/>End-to-end<br/>workflow routing"] ~~~ SR["@systematic-reviewer<br/>PRISMA-compliant<br/>evidence reviews"] ~~~ RP["@research-planner<br/>Protocols &<br/>study design"] ~~~ DA["@data-analyst<br/>Reproducible R / Python<br/>analysis scripts"] ~~~ AW["@academic-writer<br/>Manuscript drafting<br/>& citations"] ~~~ PM["@project-manager<br/>Milestones, decisions<br/>& progress briefs"] ~~~ VC["@verification-coordinator<br/>Human + LLM<br/>verification workbooks"] ~~~ TS["@troubleshooter<br/>Diagnostics &<br/>environment fixes"] ~~~ DEV["@developer<br/>Bug fixes &<br/>feature planning"]
    end

    VSCODE --> AGENTS

    ICMJE["🔒 ICMJE Compliance Layer<br/>Human-in-the-loop · Audit trail · AI disclosure"]

    AGENTS --> ICMJE

    subgraph MCP["MCP Servers · Model Context Protocol"]
        direction LR
        subgraph LITERATURE["Literature Databases"]
            direction LR
            PUB["PubMed<br/>NCBI E-utilities"] ~~~ OA["OpenAlex<br/>REST API"] ~~~ SS["Semantic Scholar<br/>Academic Graph"] ~~~ EPMC["Europe PMC<br/>REST API"] ~~~ CR["CrossRef<br/>DOI metadata"]
        end
        subgraph REFERENCE["Reference Management"]
            direction LR
            ZOT["Zotero Web<br/>API v3"] ~~~ ZLOC["Zotero Local<br/>PDFs & annotations"]
        end
        subgraph TRACKING["Project Tracking"]
            direction LR
            PRISMA["PRISMA Tracker<br/>flow diagrams"] ~~~ PROJ["Project Tracker<br/>tasks & milestones"] ~~~ CHATEX["Chat Exporter<br/>session audit trails"]
        end
    end

    ICMJE --> MCP

    subgraph OUTPUTS["Research Outputs"]
        direction LR
        QMD["📄 Quarto Documents<br/>Manuscripts · Protocols · Reports"] ~~~ SCRIPTS["📊 Analysis Scripts<br/>R · Python · Reproducible"] ~~~ PFLOW["📋 PRISMA Flow<br/>Diagrams & Checklists"] ~~~ BRIEFS["📝 Progress Briefs<br/>Decision logs · Meeting notes"]
    end

    MCP --> OUTPUTS

    %% ── Styles ──
    classDef researcher fill:#2563eb,stroke:#1e40af,color:#fff,font-weight:bold
    classDef vscode fill:#007acc,stroke:#005a9e,color:#fff,font-weight:bold
    classDef agent fill:#7c3aed,stroke:#5b21b6,color:#fff
    classDef compliance fill:#dc2626,stroke:#991b1b,color:#fff,font-weight:bold
    classDef litdb fill:#10b981,stroke:#047857,color:#fff
    classDef refmgmt fill:#14b8a6,stroke:#0d9488,color:#fff
    classDef tracking fill:#06b6d4,stroke:#0891b2,color:#fff
    classDef output fill:#d97706,stroke:#b45309,color:#fff

    class YOU researcher
    class VSCODE vscode
    class ORCH,SR,RP,DA,AW,PM,VC,TS,DEV agent
    class ICMJE compliance
    class PUB,OA,SS,EPMC,CR litdb
    class ZOT,ZLOC refmgmt
    class PRISMA,PROJ tracking
    class QMD,SCRIPTS,PFLOW,BRIEFS output
```

> Also available as [SVG](docs/rwa-architecture.svg), [rendered HTML](docs/architecture-diagram.qmd) (`quarto render docs/architecture-diagram.qmd`), or [Mermaid source](docs/rwa-architecture.mmd).

## ICMJE Compliance: You Are the Author

This tool is designed around the [ICMJE authorship criteria](https://www.icmje.org/recommendations/browse/roles-and-responsibilities/defining-the-role-of-authors-and-contributors.html). AI cannot be an author. You must meet all four criteria:

1. **Substantial contributions** to conception, design, data acquisition, analysis, or interpretation
2. **Drafting or critically revising** the work for important intellectual content
3. **Final approval** of the version to be published
4. **Accountability** for all aspects of the work

The tool enforces this by:
- Requiring human decisions at every substantive step
- Tracking AI contributions in an audit trail (`ai-contributions-log.md`)
- Generating ICMJE-compliant AI disclosure statements for your manuscripts
- Refusing to finalize outputs without explicit human review

Per ICMJE Section II.A.4: AI use must be disclosed in acknowledgments (writing assistance) and methods (data analysis). This tool generates those disclosures for you.

Setup also captures a default author profile in [.rwa-user-config.yaml](.rwa-user-config.yaml), and new projects can store per-project `authors` metadata in [templates/project-config.yaml](templates/project-config.yaml) so future reports and manuscripts start with the correct author front matter.

When RWA itself is cited in a Methods or Acknowledgments section, use the `vanzyl2026rwa` BibTeX entry from [templates/rwa-citation.bib](templates/rwa-citation.bib).

## Disclaimer and Readiness Gate

RWA enforces a disclaimer/readiness gate before non-setup agent workflows.

- Source disclaimer text: [compliance/user-disclaimer.md](compliance/user-disclaimer.md)
- Acceptance state file: [.rwa-user-config.yaml](.rwa-user-config.yaml)
- Required value: `disclaimer_accepted: true` (boolean)

When accepted through `@setup`, `.rwa-user-config.yaml` should include values like:

```yaml
disclaimer_accepted: true
disclaimer_accepted_date: "YYYY-MM-DD"
setup_completed: true
setup_completed_date: "YYYY-MM-DD"
default_author:
  name: "Author Name"
  affiliation:
    name: "Organization"
```

If acceptance is missing or invalid, agents will return:

`Before using RWA, you need to review and accept the disclaimer. Run @setup to get started.`

If you see this message unexpectedly:

1. Confirm [.rwa-user-config.yaml](.rwa-user-config.yaml) exists at workspace root.
2. Confirm `disclaimer_accepted` is boolean `true` (not a quoted string).
3. Run `@setup` again to refresh config if needed.
4. Open a new Copilot Chat session after setup changes.

## Quick Start

<details>
<summary><strong>What setup includes (typical 20-30 minutes)</strong></summary>

- Stage 1: Verify Python and VS Code prerequisites
- Stage 2: Create `.venv` and install all MCP servers
- Stage 3: Configure `.env` API keys and `PROJECTS_ROOT`
- Stage 4: Run setup validation + MCP smoke check
- Stage 5: Confirm servers in VS Code
- Stage 6: Save a default author profile for future outputs
- Stage 7: Optionally start a first project with project-specific authorship metadata

</details>

> **Prefer a guided setup?** Open Copilot Chat and type `@setup`. It will
> walk you through every step interactively.

### Prerequisites

| Requirement | Notes |
|---|---|
| [VS Code](https://code.visualstudio.com/) 1.99+ with [GitHub Copilot](https://github.com/features/copilot) | Agent mode must be enabled |
| [Python 3.11+](https://www.python.org/) | Required — runs the MCP servers |
| [R 4.0+](https://www.r-project.org/) | Optional — for R-based analysis templates |
| [Quarto](https://quarto.org/) | Optional — for rendering document templates |
| [Zotero](https://www.zotero.org/) | Optional — for reference management |

### Step 1 — Clone and open the repo

```bash
git clone https://github.com/yourusername/research-workflow-assistant.git
cd research-workflow-assistant
code .
```

### Step 2 — Create a Python environment and install MCP servers

```bash
# Create and activate a virtual environment
python -m venv .venv
# Windows:
& .venv\Scripts\Activate.ps1
# macOS / Linux:
# source .venv/bin/activate

# Install all 12 MCP servers in development mode
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

# Install dev tools (linting, testing)
pip install -e ".[dev]"
```

### Step 3 — Configure API keys

```bash
# Copy the example env file
cp .env.example .env          # macOS / Linux
copy .env.example .env        # Windows
```

Open `.env` and add your credentials. At minimum:

| Key | Where to get it | Required? |
|---|---|---|
| `NCBI_API_KEY` | [NCBI account settings](https://www.ncbi.nlm.nih.gov/account/settings/) | Recommended |
| `OPENALEX_API_KEY` | [OpenAlex API key settings](https://openalex.org/settings/api-key) | Recommended |
| `ZOTERO_API_KEY` | [Zotero key settings](https://www.zotero.org/settings/keys) | If using Zotero |
| `ZOTERO_USER_ID` | Numeric ID shown at the top of the [Zotero keys page](https://www.zotero.org/settings/keys) (not your username) | If using Zotero |

Full details: [docs/api-setup-guide.md](docs/api-setup-guide.md). For Google Drive and Google Docs integration setup and the review-workflow round-trip, see [docs/google-workspace-guide.md](docs/google-workspace-guide.md).

`PROJECTS_ROOT` should normally remain `./my_projects` unless you explicitly want projects in another folder.

### Step 4 — Verify everything works

```bash
python scripts/validate_setup.py
```

Need JSON for automation?

```bash
python scripts/validate_setup.py --json
```

Or in VS Code: **Ctrl+Shift+P** → "MCP: List Servers" — all 12 servers should appear.

### Step 5 — Start using it

If you want one entry point that coordinates all phases, start with:

```
@research-orchestrator I am starting a systematic review. Orchestrate the full workflow and tell me exactly which agent prompt to run at each stage.
```

Or choose a specialist agent directly if you already know the stage.

Open Copilot Chat and try an agent:

```
@project-manager Initialize a new project called "my-first-review" in my_projects/my-first-review.
```

See [docs/getting-started.md](docs/getting-started.md) for the full guide, including project setup, multi-project workflows, and cross-workspace usage.

### Usage examples

```
@systematic-reviewer I want to conduct a systematic review on the effectiveness
of community health worker interventions for maternal mental health in low- and
middle-income countries.
```

```
@project-manager Initialize a new project for my systematic review. Target
completion is September 2026.
```

```
@data-analyst I have extracted data from 23 studies. Help me set up a
random-effects meta-analysis using the metafor package in R.
```

### Sample project

The repository includes a fully worked sample project at [`sample_projects/chw-maternal-mental-health/`](sample_projects/chw-maternal-mental-health/) — a systematic review of community health worker interventions for maternal mental health in low- and middle-income countries. It demonstrates the end-to-end outputs that RWA generates:

| Output | Path | What it shows |
|---|---|---|
| Review protocol | [`protocol.qmd`](sample_projects/chw-maternal-mental-health/protocol.qmd) | PRISMA-compliant protocol with PICO framework |
| Manuscript (source) | [`manuscript.qmd`](sample_projects/chw-maternal-mental-health/manuscript.qmd) | IMRaD manuscript with citations and AI disclosure |
| Manuscript (HTML) | [`manuscript.html`](sample_projects/chw-maternal-mental-health/manuscript.html) | Rendered HTML version for browser viewing |
| Manuscript (PDF) | [`manuscript.pdf`](sample_projects/chw-maternal-mental-health/manuscript.pdf) | Rendered PDF for print/submission |
| Manuscript (Word) | [`manuscript.docx`](sample_projects/chw-maternal-mental-health/manuscript.docx) | Rendered DOCX for journal submission or collaboration |
| Search results (SQLite) | [`data/search_results.db`](sample_projects/chw-maternal-mental-health/data/) | Structured database of results from PubMed, OpenAlex, CrossRef, Semantic Scholar |
| Search results (Excel) | [`data/search_results.xlsx`](sample_projects/chw-maternal-mental-health/data/) | Filterable Excel workbook with clickable DOI/PMID hyperlinks |
| Reproducible search scripts | [`scripts/`](sample_projects/chw-maternal-mental-health/scripts/) | Thin stub scripts that reproduce each database search |
| Data extraction | [`data-extraction.qmd`](sample_projects/chw-maternal-mental-health/data-extraction.qmd) | Structured data extraction template |
| Risk of bias | [`rob2-assessments.qmd`](sample_projects/chw-maternal-mental-health/rob2-assessments.qmd) | Cochrane RoB 2 assessments |
| Evidence synthesis | [`synthesis.qmd`](sample_projects/chw-maternal-mental-health/synthesis.qmd) | Narrative and quantitative synthesis |
| PRISMA flow | [`review-tracking/`](sample_projects/chw-maternal-mental-health/review-tracking/) | PRISMA flow diagram tracking data |
| Project tracking | [`project-tracking/`](sample_projects/chw-maternal-mental-health/project-tracking/) | Milestones, tasks, and decision log |
| AI contributions log | [`ai-contributions-log.md`](sample_projects/chw-maternal-mental-health/ai-contributions-log.md) | Full audit trail of AI-assisted work |
| References | [`references.bib`](sample_projects/chw-maternal-mental-health/references.bib) | BibTeX bibliography managed via Zotero |

Browse the sample project to see what a completed RWA-assisted review looks like before starting your own.

## Project Structure

```
research-workflow-assistant/
├── .github/
│   ├── copilot-instructions.md      # ICMJE + research integrity rules
│   └── agents/                      # Custom Copilot agents
├── .vscode/
│   ├── settings.json
│   └── mcp.json                     # MCP server configuration
├── mcp-servers/                     # MCP server implementations (Python)
│   ├── _shared/                     # Shared SQLite result storage module
│   ├── pubmed-server/
│   ├── openalex-server/
│   ├── semantic-scholar-server/
│   ├── europe-pmc-server/
│   ├── crossref-server/
│   ├── zotero-server/
│   ├── prisma-tracker/
│   └── project-tracker/
├── templates/                       # Quarto templates
│   ├── systematic-review/
│   ├── manuscript/
│   ├── report/
│   └── project-management/
├── analysis-templates/              # Reusable R/Python analysis templates
├── compliance/                      # ICMJE checklists, reporting standards
├── docs/                            # User documentation
└── tests/
```

## Database Access

| Database | API | Access | Auth |
|---|---|---|---|
| PubMed/MEDLINE | NCBI E-utilities | Free | API key (recommended) |
| OpenAlex | REST API | Free ($1/day budget) | API key (free) |
| Semantic Scholar | Academic Graph API | Free (rate limited) | API key (optional) |
| Europe PMC | REST API | Free | None |
| CrossRef | REST API | Free | Email (polite pool) |
| Zotero | Web API v3 | Free | API key |
| Scopus | Elsevier API | Planned (institutional) | API key |

Databases without APIs (CINAHL, PsycINFO, Web of Science, Google Scholar, Cochrane Library): the agents help you build database-specific queries, but you run the searches manually and import results.

## Reporting Standards

The tool supports multiple systematic review reporting standards (user selects):
- **PRISMA 2020** (systematic reviews with meta-analysis)
- **PRISMA-ScR** (scoping reviews)
- **MOOSE** (meta-analyses of observational studies)
- **Cochrane Handbook** methods

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

[MIT License](LICENSE)

## How To Cite

If you use Research Workflow Assistant in a manuscript, report, protocol, or other cited output, cite it as:

van Zyl, A. (2026). Research Workflow Assistant [Computer software]. https://github.com/andre-inter-collab-llc/research-workflow-assistant

BibTeX:

```bibtex
@misc{vanzyl2026rwa,
  author = {{Van Zyl}, Andre},
  title = {Research Workflow Assistant},
  year = {2026},
  url = {https://github.com/andre-inter-collab-llc/research-workflow-assistant},
  note = {GitHub repository}
}
```

You can also copy the canonical entry directly from [templates/rwa-citation.bib](templates/rwa-citation.bib) into your project's `references.bib`.

## Acknowledgments

- [ICMJE](https://www.icmje.org/) for authorship and AI disclosure guidelines
- [PRISMA](http://www.prisma-statement.org/) for systematic review reporting standards
- [MCP](https://modelcontextprotocol.io/) for the Model Context Protocol specification
- [Quarto](https://quarto.org/) for scientific publishing
- [Posit](https://posit.co/) for the R ecosystem
- Built with [GitHub Copilot](https://github.com/features/copilot) using [Claude Opus 4.6](https://docs.github.com/en/copilot/reference/ai-models/model-comparison) by Anthropic and GPT-5.3-Codex
