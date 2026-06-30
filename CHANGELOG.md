# Changelog

All notable changes to the Research Workflow Assistant (RWA) are documented in this file.

This project uses [Calendar Versioning](https://calver.org/) with the format `YYYY.MM.DD`.
Same-day releases use a `.N` suffix (e.g., `2026.03.18.1`).

A machine-readable mirror of this log is maintained in [versions.yaml](versions.yaml).

## [Unreleased]

### Added

### Changed

### Fixed

### Removed

## [2026.06.30] — 2026-06-30

Google Workspace MCP server, OpenRouter model guidance with pricing table, author name normalization, and bibliography sync improvements.

### Added

- **Google Workspace MCP server**: New `google-workspace` server providing OAuth-secured Google Drive and Google Docs integration, including file listing/import/upload and a comment-to-proposal review-workflow round-trip with deterministic line anchors (11 tools total).
- **Google Workspace guide**: New `docs/google-workspace-guide.md` covering OAuth setup, the review-workflow round-trip, full tool reference, configuration, and troubleshooting.
- **OpenRouter model guidance**: Expanded the README "Model note" callout to document OpenRouter as a routing service that connects GitHub Copilot to models from many providers. Added a pricing table of open-source/open-weight models (GLM 5.2, DeepSeek V4 Pro/Flash, MiniMax M3, Qwen3.7 Max, Kimi K2.6) alongside frontier model pricing for comparison, sourced from the OpenRouter agentic-sorted catalog.
- **Author name normalization**: Implemented author name normalization in the shared result store with corresponding tests.

### Changed

- **Bibliography sync refactor**: Simplified the dictionary comprehension in `sync_project_bibliography` for cleaner code.
- **Documentation cross-references**: Added links from `docs/api-setup-guide.md` and `README.md` to the new Google Workspace guide.
- **Infrastructure updates**: Updated workflows, setup agent, copilot-instructions, tasks, and config files to register and support the new google-workspace server.

### Fixed

- (none)

### Removed

- (none)

## [2026.04.06] — 2026-04-06

Verification coordinator agent, reusable verification templates, and workflow integration for end-to-end reproducibility checks.

### Added

- **Verification coordinator agent**: Added `.github/agents/verification-coordinator.agent.md` for human-friendly and LLM-executable verification workflows, including verifier preference capture and execution contract requirements.
- **Verification template set**: Added `templates/verification/verification-workbook.qmd`, `templates/verification/verifier-preferences.yaml`, `templates/verification/llm-execution-contract.yaml`, and `templates/verification/verification-instructions-tracker.qmd`.

### Changed

- **Orchestration stage flow**: Updated `research-orchestrator` to include a dedicated verification stage routed to `@verification-coordinator` across supported workflow types.
- **User and contributor docs**: Updated `README.md`, `docs/getting-started.md`, `docs/architecture.md`, and `CONTRIBUTING.md` to document the new verification workflow capability.

## [2026.03.29] — 2026-03-29

Script-first literature search workflow, Zotero attachment uploads, README Philosophy section, and infrastructure improvements.

### Added

- **Script-first search workflow**: `draft_*_search` and `run_search_script` tools added to all five database MCP servers (PubMed, OpenAlex, Semantic Scholar, Europe PMC, CrossRef). Formal literature searches now generate a standalone Python script for user review before execution, improving reproducibility and auditability.
- **Shared search script engine**: `generate_search_script`, `execute_search_script`, and `generate_and_run_script` functions added to `rwa_result_store` shared library, powering the draft/run workflow across all servers.
- **Zotero attachment upload**: `upload_attachment` tool added to zotero-server for uploading PDFs and other files to Zotero items via the Web API.
- **PDF upload utility scripts**: `scripts/_upload_pdfs.py` and `scripts/_upload_pdfs2.py` for batch-uploading PDFs to Zotero library items.
- **Search results backfill utility**: `scripts/backfill_search_exports.py` for regenerating Excel exports from existing `search_results.db` files.
- **Bug report issue template**: `.github/ISSUE_TEMPLATE/bug-report.yml` for structured issue reporting.
- **README Philosophy section**: Added project philosophy explaining RWA as a proof of concept, the case against platform lock-in, and the existing research tech stack, with a link to the LinkedIn launch post.
- **Search strategy template update**: Added script-first workflow instructions to `templates/systematic-review/search-strategy.qmd`.
- **Agent instructions for script-first workflow**: Updated `systematic-reviewer` and `research-orchestrator` agents with the mandatory draft-then-approve search protocol, including allowed direct MCP tool usage and DB-as-source-of-truth rules.
- **Global copilot instructions**: Added Literature Search Protocol section enforcing the script-first, DB-as-source-of-truth workflow across all agents.

### Changed

- **MCP server project path handling**: Improved error messages and validation for `project_path` parameters across PubMed, OpenAlex, Semantic Scholar, Europe PMC, and CrossRef servers.
- **API documentation**: Updated `docs/api-setup-guide.md`, `docs/database-access.md`, and `docs/getting-started.md` with clarified instructions.
- **Search runners**: Improved `search_runners.py` in the shared library for better script execution handling.

### Fixed

- **Chat parser**: Handle non-string content in thinking blocks to prevent parsing errors in chat export.

### Removed

- Obsolete `search_results.db` files from sample project directories (data now lives in project-specific paths).
- Stale `prisma-flow.json` from sample project (replaced by PRISMA tracker server workflow).

## [2026.03.18] — 2026-03-18

Initial public release of the Research Workflow Assistant.

### Added

#### MCP Servers (11 total)
- **pubmed-server**: Search PubMed/MEDLINE via NCBI E-utilities (search, fetch abstracts, MeSH terms, related articles)
- **openalex-server**: Search OpenAlex for works, authors, sources, concepts, citations, and references
- **semantic-scholar-server**: Search Semantic Scholar Academic Graph; get paper details, citations, references, recommendations
- **europe-pmc-server**: Search Europe PMC for biomedical literature; access full text, citations, references, text-mined terms
- **crossref-server**: DOI resolution, metadata verification, reference validation, and scripted search
- **zotero-server**: Manage Zotero reference library via Web API (search, add items, tag, export, notes, annotations, collections)
- **zotero-local-server**: Access local Zotero data — PDF text/annotation extraction, full-text keyword search, Better BibTeX integration
- **bibliography-manager**: Local reference management for non-Zotero users — import BibTeX/RIS, link PDFs, notes, annotations, export for Quarto
- **prisma-tracker**: Track PRISMA 2020 systematic review flow — record searches, screening, deduplication; generate flow diagrams
- **project-tracker**: Track research project phases, milestones, tasks, decisions, meetings; generate progress briefs
- **chat-exporter**: Export Copilot Chat sessions to Quarto Markdown (QMD) files for reproducibility audit trails

#### Shared Library
- **mcp-servers/_shared**: Common utilities shared across all MCP servers (rate limiting, error handling, HTTP client helpers)

#### Custom Copilot Agents (10 total)
- **systematic-reviewer**: Guides PRISMA/PRISMA-ScR/MOOSE/Cochrane systematic reviews end-to-end
- **data-analyst**: Generates reproducible R/Python analysis scripts in Quarto documents
- **academic-writer**: Scaffolds manuscripts, manages citations, drafts sections with ICMJE compliance
- **research-planner**: Helps plan research projects, protocols, ethics applications, study design
- **project-manager**: Phase tracking, milestones, tasks, progress briefs, decision logging, meeting notes
- **critical-reviewer**: Structured critical appraisal using validated checklists (CASP, JBI, STROBE, CONSORT)
- **research-orchestrator**: Orchestrates end-to-end workflows across specialist agents
- **developer**: Resolves bugs, implements features, improves the RWA codebase
- **setup**: Guided first-time configuration — prerequisites, environment, API keys, MCP servers
- **troubleshooter**: Diagnoses environment, configuration, and MCP server issues

#### Compliance Documents (6)
- ICMJE authorship checklist
- AI disclosure template
- PRISMA 2020 checklist
- PRISMA-ScR checklist
- MOOSE checklist
- Cochrane RoB 2 template

#### Templates (12+)
- Systematic review: protocol, manuscript, search strategy, PRISMA flow diagram
- Manuscript: IMRaD format
- Project management: progress brief (Quarto + markdown), meeting notes, decision log
- Critical appraisal: CASP RCT, CASP qualitative, STROBE, cross-study summary
- Analysis: R and Python citation helpers, R summary table
- Project configuration: project-config.yaml, portable MCP config

#### CSL Citation Styles (11)
- APA (7th edition), AMA, BMJ, Chicago (author-date + fullnote), Harvard Cite Them Right, IEEE, NLM, Nature, Vancouver, Vancouver (superscript)

#### Documentation
- Getting started guide
- API setup guide
- Database access reference
- Architecture overview with diagram
- Posit/Quarto ecosystem guide
- Zotero plugins guide
- Quick start guide

#### Infrastructure
- GitHub Actions CI/CD: multi-platform validation (Ubuntu, Windows, macOS) + ruff linting
- Python virtual environment configuration with hatchling build system
- `.vscode/mcp.json` for MCP server configuration
- `.env.example` for API key setup
- Comprehensive `.gitignore` for Python, R, Quarto, and IDE artifacts

#### Versioning & Community Standards
- CalVer versioning scheme (YYYY.MM.DD)
- CHANGELOG.md (human-readable) + versions.yaml (machine-readable) dual changelog
- Local release script (`scripts/release.py`) with backup and tagging
- GitHub Actions release workflow for automated GitHub Releases
- CONTRIBUTING.md with development guidelines
- CODE_OF_CONDUCT.md (Contributor Covenant v2.1)
- SECURITY.md with responsible disclosure policy
- Feature request issue template
- Pull request template

### Notes
- All databases are free-tier (no institutional access required for core functionality)
- ICMJE compliance is enforced globally via `.github/copilot-instructions.md`
- Python 3.11+ required; R optional (for analysis templates only)
- License: MIT
