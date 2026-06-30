# Contributing to the Research Workflow Assistant

Thank you for your interest in contributing to the Research Workflow Assistant (RWA)! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Project Structure](#project-structure)
- [Making Changes](#making-changes)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Contributing Agents and Templates](#contributing-agents-and-templates)
- [ICMJE Compliance Note](#icmje-compliance-note)

## Code of Conduct

This project follows the [Contributor Covenant v2.1](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior through GitHub Issues using a template: https://github.com/andre-inter-collab-llc/research-workflow-assistant/issues/new/choose or via GitHub Discussions: https://github.com/andre-inter-collab-llc/research-workflow-assistant/discussions.

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/research-workflow-assistant.git
   cd research-workflow-assistant
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/andre-inter-collab-llc/research-workflow-assistant.git
   ```

## Development Environment

### Prerequisites

- Python 3.11 or higher
- Git
- VS Code (recommended) with GitHub Copilot
- [Quarto CLI](https://quarto.org/docs/get-started/) (for rendering documents)

### Setup

1. **Create and activate virtual environment**:
   ```powershell
   # Windows (PowerShell)
   python -m venv .venv
   & .venv\Scripts\Activate.ps1
   ```
   ```bash
   # macOS/Linux
   python -m venv .venv
   source .venv/bin/activate
   ```

2. **Install all MCP servers in development mode**:
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

3. **Install dev dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

4. **Copy environment file**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys (see docs/api-setup-guide.md)
   ```

5. **Validate setup**:
   ```bash
   python scripts/validate_setup.py
   ```

> **Important**: Never install packages into the global/system Python. All work must use the project virtual environment at `.venv/`.

## Project Structure

```
mcp-servers/          # MCP server implementations (Python)
  _shared/            # Shared utilities across servers
  pubmed-server/      # One directory per server
  ...
.github/
  agents/             # Custom Copilot agent definitions (.agent.md)
  workflows/          # GitHub Actions CI/CD
  copilot-instructions.md  # Global agent instructions
templates/            # Quarto/Markdown document templates
compliance/           # ICMJE, PRISMA, MOOSE checklists
csl/                  # Citation Style Language files
docs/                 # Documentation
scripts/              # Utility scripts (validation, release)
tests/                # Test suite
```

## Making Changes

1. **Create a feature branch** from `master`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**, following the [coding standards](#coding-standards) below.

3. **Test your changes** (see [Testing](#testing)).

4. **Commit** with clear, descriptive messages:
   ```bash
   git commit -m "feat: add Scopus MCP server with basic search"
   ```
   Follow [Conventional Commits](https://www.conventionalcommits.org/) format:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation only
   - `refactor:` for code restructuring
   - `test:` for adding/updating tests
   - `chore:` for build/CI/tooling changes

5. **Push** your branch and open a pull request.

## Coding Standards

### Python

- **Formatter/Linter**: [ruff](https://docs.astral.sh/ruff/) — run before every commit:
  ```bash
  ruff check .          # Lint
  ruff format .         # Format
  ```
- **Line length**: 100 characters
- **Target version**: Python 3.11+
- **Type hints**: Use type annotations for all public function signatures
- **Import order**: isort-compatible (handled by ruff)

### MCP Servers

- Each server lives in its own directory under `mcp-servers/`
- Each server has its own `pyproject.toml` with a `[project.scripts]` entry point
- Use the shared library (`mcp-servers/_shared`) for common patterns (HTTP clients, rate limiting, error handling)
- All tools must have clear docstrings that describe parameters and return values
- Respect API rate limits (see `.github/copilot-instructions.md` for limits per service)

### Quarto Templates

- Use `.qmd` file extension (not `.md` or `.Rmd`)
- Include proper YAML front matter with `title`, `date`, and `format` fields
- Use Mermaid for diagrams (natively supported by Quarto)

### Agent Definitions

- Agent files go in `.github/agents/` with `.agent.md` extension
- Follow the existing agent structure (YAML front matter + markdown instructions)
- Include tool restrictions where appropriate
- Reference ICMJE compliance requirements for any research-facing agent

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run tests for a specific server
pytest mcp-servers/pubmed-server/tests/

# Run with verbose output
pytest -v
```

### Writing Tests

- Place tests in the `tests/` directory of each MCP server, or in the root `tests/` directory
- Use `pytest` + `pytest-asyncio` for async MCP tool tests
- Mock external API calls — never hit live APIs in tests
- Use `pytest-httpx` for HTTP mocking

### Validation

Before submitting a PR, ensure:

```bash
ruff check .              # No lint errors
ruff format --check .     # Formatting is correct
python scripts/validate_setup.py  # Setup validation passes
pytest                    # All tests pass
```

## Pull Request Process

1. Ensure your branch is up to date with `master`:
   ```bash
   git fetch upstream
   git rebase upstream/master
   ```

2. Open a pull request against `master` on the upstream repository.

3. Fill out the [pull request template](.github/PULL_REQUEST_TEMPLATE.md) completely.

4. Ensure CI checks pass (validation + linting).

5. Wait for review. Address any feedback.

6. Once approved, a maintainer will merge your PR.

### What Makes a Good PR

- **Focused**: One feature, fix, or improvement per PR
- **Tested**: Include tests for new functionality
- **Documented**: Update docs if behavior changes
- **Clean history**: Rebase and squash as needed

## Contributing Agents and Templates

### New Copilot Agents

If you're contributing a new custom Copilot agent:

1. Create the agent definition in `.github/agents/your-agent.agent.md`
2. Follow the YAML front matter pattern of existing agents
3. Include ICMJE compliance guardrails if the agent interacts with research content
4. Document which MCP server tools the agent uses
5. Add the agent to the README's feature table
6. If the agent introduces reusable artifacts, add matching templates under `templates/`
7. If the agent supports verification workflows, include a verifier preference schema and an LLM execution contract template

### New Templates

If you're contributing a new Quarto template:

1. Place it in the appropriate `templates/` subdirectory
2. Use `.qmd` format with standard YAML front matter
3. Include placeholder text that guides users on what to fill in
4. Add CSL citation style support if the template includes references
5. For verification templates, include both human-readable guidance and machine-readable checkpoint expectations

## ICMJE Compliance Note

The Research Workflow Assistant is designed to help researchers maintain ICMJE compliance. If your contribution involves:

- **Text generation**: Ensure AI-drafted content is clearly flagged for human review
- **Data analysis**: Include comments explaining methodology and assumptions
- **Citation management**: Never fabricate references; always verify via MCP tools
- **Audit trails**: Maintain `ai-contributions-log.md` compatibility

All agents must enforce the human-in-the-loop mandate described in `.github/copilot-instructions.md`.

## Questions?

- Open an issue on GitHub for bugs or feature requests
- See [docs/getting-started.md](docs/getting-started.md) for user documentation
- See [docs/architecture.md](docs/architecture.md) for technical architecture

---

Thank you for contributing to making research workflows more efficient and reproducible!
