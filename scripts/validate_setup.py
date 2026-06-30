#!/usr/bin/env python3
"""Validate the research-workflow-assistant environment setup.

Run from the repository root:
    python scripts/validate_setup.py

Outputs a human-readable checklist by default.
Use --json to print the full machine-readable report.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

# Load .env so that env key checks reflect what servers will actually see
_workspace_root = Path(__file__).resolve().parent.parent
try:
    from dotenv import load_dotenv

    _env_file = _workspace_root / ".env"
    if _env_file.is_file():
        load_dotenv(_env_file)
except ImportError:
    pass  # python-dotenv not installed yet; env key checks will use system env only


def _check_python_version() -> dict:
    """Check Python version >= 3.11."""
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    ok = version >= (3, 11)
    return {"status": "ok" if ok else "fail", "version": version_str}


def _check_server_importable(module_name: str) -> dict:
    """Check if an MCP server package is importable."""
    try:
        importlib.import_module(module_name)
        return {"status": "ok"}
    except ImportError as e:
        return {"status": "fail", "error": str(e)}


def _check_servers() -> dict:
    """Check all configured MCP server packages."""
    servers = {
        "pubmed": "pubmed_server",
        "openalex": "openalex_server",
        "semantic-scholar": "semantic_scholar_server",
        "europe-pmc": "europe_pmc_server",
        "crossref": "crossref_server",
        "zotero": "zotero_server",
        "zotero-local": "zotero_local_server",
        "prisma-tracker": "prisma_tracker",
        "project-tracker": "project_tracker",
        "chat-exporter": "chat_exporter",
        "bibliography-manager": "bibliography_manager",
        "google-workspace": "google_workspace_server",
    }
    return {name: _check_server_importable(mod) for name, mod in servers.items()}


def _check_env_keys(workspace_root: Path) -> dict:
    """Check which .env keys are configured (without revealing values)."""
    env_path = workspace_root / ".env"
    keys_to_check = [
        "NCBI_API_KEY",
        "OPENALEX_API_KEY",
        "OPENALEX_EMAIL",
        "S2_API_KEY",
        "S2_API_KEY_STATUS",
        "CROSSREF_EMAIL",
        "ZOTERO_API_KEY",
        "ZOTERO_USER_ID",
        "ZOTERO_DATA_DIR",
        "GOOGLE_OAUTH_CLIENT_ID",
        "GOOGLE_OAUTH_CLIENT_SECRET",
        "GOOGLE_OAUTH_REDIRECT_URI",
        "GOOGLE_WORKSPACE_TOKEN_PATH",
        "PROJECTS_ROOT",
    ]
    result: dict[str, str] = {}

    if not env_path.exists():
        return {k: "missing" for k in keys_to_check}

    # Parse .env file (simple key=value, no shell expansion)
    env_vars: dict[str, str] = {}
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                env_vars[key.strip()] = value.strip()

    for key in keys_to_check:
        value = env_vars.get(key, "")
        if value:
            result[key] = "set"
        else:
            result[key] = "empty"

    # OPENALEX_EMAIL is optional when OPENALEX_API_KEY is configured.
    if result.get("OPENALEX_EMAIL") == "empty" and result.get("OPENALEX_API_KEY") == "set":
        result["OPENALEX_EMAIL"] = "optional"

    # Treat Semantic Scholar key as intentionally pending when explicitly marked.
    if result.get("S2_API_KEY") == "empty" and result.get("S2_API_KEY_STATUS") == "set":
        result["S2_API_KEY"] = "pending"

    return result


def _check_projects_dir(workspace_root: Path) -> dict:
    """Check if the projects directory exists and list projects."""
    # Determine projects root from .env or default
    _check_env_keys(workspace_root)
    projects_root_str = os.environ.get("PROJECTS_ROOT", "")

    if not projects_root_str:
        # Try reading from .env
        env_path = workspace_root / ".env"
        if env_path.exists():
            with open(env_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("PROJECTS_ROOT="):
                        projects_root_str = line.split("=", 1)[1].strip()
                        break

    if not projects_root_str:
        projects_root_str = "./my_projects"

    projects_root = Path(projects_root_str)
    if not projects_root.is_absolute():
        projects_root = workspace_root / projects_root

    if not projects_root.exists():
        return {"status": "missing", "path": str(projects_root), "projects": []}

    # List project directories and detect whether each appears initialized.
    # Support both tracker-based initialization and lightweight project config files.
    projects = []
    if projects_root.is_dir():
        for child in sorted(projects_root.iterdir()):
            if child.is_dir() and child.name != ".gitkeep":
                has_project_tracking = (child / "project-tracking" / "project.yaml").exists()
                has_review_tracking = (child / "review-tracking" / "prisma-flow.json").exists()
                has_project_config = (child / "project-config.yaml").exists()
                has_ai_log = (child / "ai-contributions-log.md").exists()

                # Mark as initialized if any supported project marker is present.
                is_initialized = (
                    has_project_tracking or has_review_tracking or has_project_config or has_ai_log
                )
                projects.append(
                    {
                        "name": child.name,
                        "initialized": is_initialized,
                    }
                )

    return {"status": "ok", "path": str(projects_root), "projects": projects}


def _check_optional_tool(command: str) -> dict:
    """Check if an optional CLI tool is available."""
    path = shutil.which(command)
    if path:
        return {"status": "available", "path": path}
    return {"status": "not-found"}


def _check_user_config(workspace_root: Path) -> dict:
    """Check .rwa-user-config.yaml disclaimer acceptance state."""
    config_path = workspace_root / ".rwa-user-config.yaml"
    if not config_path.exists():
        return {
            "status": "missing",
            "path": str(config_path),
            "disclaimer_accepted": False,
            "reason": "config file not found",
        }

    try:
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return {
            "status": "invalid",
            "path": str(config_path),
            "disclaimer_accepted": False,
            "reason": "invalid YAML",
        }

    if not isinstance(config, dict):
        return {
            "status": "invalid",
            "path": str(config_path),
            "disclaimer_accepted": False,
            "reason": "config is not a YAML mapping",
        }

    accepted = config.get("disclaimer_accepted") is True
    return {
        "status": "ok" if accepted else "not-accepted",
        "path": str(config_path),
        "disclaimer_accepted": accepted,
    }


def _check_zotero_local() -> dict:
    """Check if the local Zotero data directory is accessible."""
    try:
        from zotero_local_server import zotero_db
    except ImportError:
        return {"status": "skip", "reason": "zotero_local_server not installed"}

    data_dir = zotero_db.detect_zotero_data_dir()
    if data_dir is None:
        return {
            "status": "not-found",
            "message": ("Zotero data directory not detected. Set ZOTERO_DATA_DIR."),
        }

    version = zotero_db.get_zotero_version(data_dir)
    storage = data_dir / "storage"
    pdf_count = 0
    if storage.is_dir():
        for child in storage.iterdir():
            if child.is_dir():
                for f in child.iterdir():
                    if f.suffix.lower() == ".pdf":
                        pdf_count += 1

    result: dict = {
        "status": "ok",
        "data_dir": str(data_dir),
        "zotero_version": version,
        "pdf_count": pdf_count,
    }

    # Check for Better BibTeX (non-blocking)
    try:
        import httpx

        resp = httpx.post(
            "http://localhost:23119/better-bibtex/json-rpc",
            json={"jsonrpc": "2.0", "method": "user.groups", "params": [], "id": 1},
            timeout=3.0,
        )
        result["better_bibtex"] = "available" if resp.status_code == 200 else "not-running"
    except Exception:
        result["better_bibtex"] = "not-running"

    return result


def _check_server_health(module_name: str, workspace_root: Path) -> dict:
    """Start an MCP server process and verify it responds to a JSON-RPC initialize."""
    python = sys.executable
    server_map = {
        "pubmed_server": "pubmed-server",
        "openalex_server": "openalex-server",
        "semantic_scholar_server": "semantic-scholar-server",
        "europe_pmc_server": "europe-pmc-server",
        "crossref_server": "crossref-server",
        "zotero_server": "zotero-server",
        "zotero_local_server": "zotero-local-server",
        "prisma_tracker": "prisma-tracker",
        "project_tracker": "project-tracker",
        "chat_exporter": "chat-exporter",
        "bibliography_manager": "bibliography-manager",
        "google_workspace_server": "google-workspace-server",
    }
    dir_name = server_map.get(module_name, module_name)
    cwd = workspace_root / "mcp-servers" / dir_name / "src"
    if not cwd.is_dir():
        return {"status": "skip", "reason": f"source directory not found: {cwd}"}

    init_msg = (
        '{"jsonrpc":"2.0","id":1,"method":"initialize",'
        '"params":{"protocolVersion":"2024-11-05",'
        '"capabilities":{},"clientInfo":{"name":"validate","version":"0.1"}}}'
    )
    try:
        proc = subprocess.run(
            [python, "-m", module_name],
            input=f"Content-Length: {len(init_msg)}\r\n\r\n{init_msg}",
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(cwd),
        )
        if '"result"' in proc.stdout:
            return {"status": "ok"}
        return {
            "status": "fail",
            "stdout": proc.stdout[:500],
            "stderr": proc.stderr[:500],
        }
    except subprocess.TimeoutExpired:
        return {"status": "timeout"}
    except Exception as e:
        return {"status": "fail", "error": str(e)}


def _check_all_server_health(workspace_root: Path) -> dict:
    """Run health checks for all MCP servers."""
    modules = [
        "pubmed_server",
        "openalex_server",
        "semantic_scholar_server",
        "europe_pmc_server",
        "crossref_server",
        "zotero_server",
        "zotero_local_server",
        "prisma_tracker",
        "project_tracker",
        "chat_exporter",
        "bibliography_manager",
        "google_workspace_server",
    ]
    return {mod: _check_server_health(mod, workspace_root) for mod in modules}


def _print_human_report(report: dict[str, object]) -> None:
    """Print a concise, human-friendly setup summary."""
    print("Setup Verification Results")
    print("=" * 72)

    python_status = report["python"]["status"]  # type: ignore[index]
    python_icon = "OK" if python_status == "ok" else "FAIL"
    python_version = report["python"].get("version", "unknown")  # type: ignore[index]
    print(f"[{python_icon}] Python version: {python_version} (required: 3.11+)")

    servers = report["servers"]  # type: ignore[index]
    server_ok = sum(1 for s in servers.values() if s.get("status") == "ok")
    pkg_icon = "OK" if server_ok == len(servers) else "WARN"
    print(f"[{pkg_icon}] MCP packages importable: {server_ok}/{len(servers)}")

    server_health = report["server_health"]  # type: ignore[index]
    healthy = sum(1 for s in server_health.values() if s.get("status") == "ok")
    health_icon = "OK" if healthy == len(server_health) else "WARN"
    print(f"[{health_icon}] MCP startup checks passed: {healthy}/{len(server_health)}")

    env_file = report.get("env_file", "missing")
    print(f"[{'OK' if env_file == 'exists' else 'FAIL'}] .env file: {env_file}")

    user_config = report["user_config"]  # type: ignore[index]
    uc_status = user_config.get("status")
    if uc_status == "ok":
        print(f"[OK] Disclaimer accepted in {user_config.get('path')}")
    else:
        print(
            "[WARN] Disclaimer acceptance not confirmed "
            f"({user_config.get('reason', uc_status)}). Run @setup if needed."
        )

    env_keys = report["env_keys"]  # type: ignore[index]
    required = [
        "NCBI_API_KEY",
        "OPENALEX_API_KEY",
        "ZOTERO_API_KEY",
        "ZOTERO_USER_ID",
        "PROJECTS_ROOT",
    ]
    missing_required = [k for k in required if env_keys.get(k) in {"missing", "empty"}]
    if missing_required:
        print(f"[WARN] Required/recommended keys needing attention: {', '.join(missing_required)}")
    else:
        print("[OK] Required/recommended API keys are configured")

    projects = report["projects_dir"]  # type: ignore[index]
    projects_status = projects.get("status")
    projects_icon = "OK" if projects_status == "ok" else "WARN"
    project_count = len(projects.get("projects", []))
    print(
        f"[{projects_icon}] Projects root:"
        f" {projects.get('path', 'unknown')}"
        f" (projects found: {project_count})"
    )

    zotero_local = report["zotero_local"]  # type: ignore[index]
    zl_status = zotero_local.get("status")
    if zl_status == "ok":
        zl_dir = zotero_local.get("data_dir")
        zl_pdfs = zotero_local.get("pdf_count", 0)
        zl_bbt = zotero_local.get("better_bibtex", "unknown")
        print(f"[OK] Zotero local detected at {zl_dir} (PDFs: {zl_pdfs}, BBT: {zl_bbt})")
    else:
        print(
            f"[WARN] Zotero local:"
            f" {zotero_local.get('message', zotero_local.get('reason', 'not configured'))}"
        )

    overall = report.get("overall", "unknown")
    print("-" * 72)
    print(f"Overall status: {overall}")

    if overall != "ready":
        print("Next steps:")
        if env_file != "exists":
            print("- Create .env from .env.example and fill required keys")
        if missing_required:
            print("- Set missing keys in .env and restart MCP servers")
        if healthy != len(server_health):
            print("- Run task: Install All MCP Servers, then re-run this script")
        if projects_status != "ok":
            print("- Ensure PROJECTS_ROOT points to a valid directory (default: ./my_projects)")

    print("=" * 72)


def main() -> int:
    """Run all checks and output a setup report."""
    parser = argparse.ArgumentParser(description="Validate RWA setup")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON report")
    args = parser.parse_args()

    # Determine workspace root (parent of scripts/)
    workspace_root = Path(__file__).resolve().parent.parent

    report = {
        "python": _check_python_version(),
        "servers": _check_servers(),
        "server_health": _check_all_server_health(workspace_root),
        "env_file": "exists" if (workspace_root / ".env").exists() else "missing",
        "env_keys": _check_env_keys(workspace_root),
        "user_config": _check_user_config(workspace_root),
        "zotero_local": _check_zotero_local(),
        "projects_dir": _check_projects_dir(workspace_root),
        "optional_tools": {
            "r": _check_optional_tool("Rscript"),
            "quarto": _check_optional_tool("quarto"),
            "git": _check_optional_tool("git"),
        },
    }

    # Determine overall status
    python_ok = report["python"]["status"] == "ok"
    servers_ok = all(s["status"] == "ok" for s in report["servers"].values())
    env_ok = report["env_file"] == "exists"

    if python_ok and servers_ok and env_ok:
        report["overall"] = "ready"
    elif python_ok and servers_ok:
        report["overall"] = "needs-configuration"
    else:
        report["overall"] = "needs-setup"

    if args.json:
        json.dump(report, sys.stdout, indent=2)
        print()  # trailing newline
    else:
        _print_human_report(report)

    return 0 if report["overall"] != "needs-setup" else 1


if __name__ == "__main__":
    raise SystemExit(main())
