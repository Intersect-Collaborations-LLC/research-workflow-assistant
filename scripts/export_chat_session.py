#!/usr/bin/env python3
"""Export VS Code Copilot Chat sessions to Quarto Markdown (.qmd) files.

Discovers chat sessions from VS Code's local storage and converts them
to readable QMD documents for research reproducibility.

Usage:
    python scripts/export_chat_session.py --list
    python scripts/export_chat_session.py --latest --project my_projects/my-review
    python scripts/export_chat_session.py --session-id <id> --project <path>
    python scripts/export_chat_session.py --session-id <id> --output output.qmd

Options:
    --list              List available chat sessions and exit.
    --latest            Export the most recent session.
    --session-id ID     Export a specific session by ID.
    --project PATH      Target project directory (output goes to chat-logs/).
    --output PATH       Explicit output file path (overrides --project).
    --summary           Export compact summary mode (tool labels only).
    --verbose           Deprecated alias for full-detail mode (now default).
    --no-thinking       Exclude model thinking/reasoning blocks.
    --raw               Also copy the raw session .jsonl next to the .qmd.
    --workspace PATH    Override workspace root for session discovery.
    --json              JSON output (with --list)
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import unquote

# Resolve workspace root from script location
_WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

# Ensure the _shared package is importable if running before pip install
_shared_src = _WORKSPACE_ROOT / "mcp-servers" / "_shared" / "src"
if _shared_src.is_dir() and str(_shared_src) not in sys.path:
    sys.path.insert(0, str(_shared_src))

from rwa_chat_parser import parse_session, render_qmd  # noqa: E402


def _vscode_storage_root() -> Path:
    """Return the VS Code workspaceStorage root for the current OS."""
    system = platform.system()
    if system == "Windows":
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            return Path(appdata) / "Code" / "User" / "workspaceStorage"
    elif system == "Darwin":
        return (
            Path.home() / "Library" / "Application Support" / "Code" / "User" / "workspaceStorage"
        )
    else:  # Linux
        config = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
        return Path(config) / "Code" / "User" / "workspaceStorage"

    raise RuntimeError("Cannot determine VS Code storage path")


def _normalize_uri(uri: str) -> str:
    """Normalize a file URI for reliable comparison.

    VS Code stores URIs with percent-encoded colons (``%3A``) and varying
    case for drive letters.  ``pathlib.as_uri()`` produces ``file:///C:/…``
    while VS Code may store ``file:///c%3A/…``.  Decode percent-encoding
    and lowercase the whole thing so both forms match.
    """
    decoded = unquote(uri)
    return decoded.lower().rstrip("/")


def _find_workspace_hash(storage_root: Path, workspace_path: Path) -> str | None:
    """Find the workspace storage hash that maps to the given workspace URI."""
    if not storage_root.is_dir():
        return None

    workspace_uri = _normalize_uri(workspace_path.resolve().as_uri())

    for entry in storage_root.iterdir():
        if not entry.is_dir():
            continue
        ws_file = entry / "workspace.json"
        if not ws_file.is_file():
            continue
        try:
            data = json.loads(ws_file.read_text(encoding="utf-8"))
            folder = data.get("folder", "")
            if _normalize_uri(folder) == workspace_uri:
                return entry.name
        except (json.JSONDecodeError, OSError):
            continue

    return None


def _discover_sessions(storage_root: Path, workspace_path: Path) -> list[dict]:
    """Discover all chat sessions for a workspace.

    Returns a list of dicts with keys: session_id, path, title, creation_date, model_id.
    """
    ws_hash = _find_workspace_hash(storage_root, workspace_path)
    if not ws_hash:
        return []

    sessions_dir = storage_root / ws_hash / "chatSessions"
    if not sessions_dir.is_dir():
        return []

    results = []
    for jsonl_file in sorted(sessions_dir.glob("*.jsonl")):
        session_id = jsonl_file.stem
        info: dict = {
            "session_id": session_id,
            "path": str(jsonl_file),
            "title": "",
            "creation_date": "",
            "model_id": "",
            "line_count": 0,
        }
        # Quick parse: read only the first few lines for metadata
        try:
            with open(jsonl_file, encoding="utf-8") as fh:
                line_count = 0
                for raw_line in fh:
                    line_count += 1
                    raw_line = raw_line.strip()
                    if not raw_line:
                        continue
                    try:
                        entry = json.loads(raw_line)
                    except json.JSONDecodeError:
                        continue

                    kind = entry.get("kind")
                    keys = entry.get("k", [])
                    value = entry.get("v")

                    if kind == 0:
                        v = entry.get("v", {})
                        info["model_id"] = v.get("modelId", "")
                        ts = v.get("creationDate")
                        if ts and isinstance(ts, (int, float)):
                            dt = datetime.fromtimestamp(ts / 1000, tz=UTC)
                            info["creation_date"] = dt.strftime("%Y-%m-%d %H:%M UTC")
                    elif kind == 1 and keys == ["customTitle"]:
                        if isinstance(value, str):
                            info["title"] = value

                info["line_count"] = line_count
        except OSError:
            continue

        results.append(info)

    # Sort by creation date (newest first)
    results.sort(key=lambda x: x["creation_date"], reverse=True)
    return results


def _slugify(text: str, max_len: int = 50) -> str:
    """Create a filesystem-safe slug from text."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:max_len] if text else "untitled"


def _export_session(
    session_path: Path,
    output_path: Path,
    *,
    include_thinking: bool,
    detail_level: str,
) -> Path:
    """Parse and export a single session to QMD."""
    session = parse_session(session_path)
    qmd = render_qmd(
        session,
        include_thinking=include_thinking,
        detail_level=detail_level,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(qmd, encoding="utf-8")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export VS Code Copilot Chat sessions to QMD",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true", help="List available sessions")
    group.add_argument("--latest", action="store_true", help="Export most recent session")
    group.add_argument("--session-id", help="Export a specific session by ID")

    parser.add_argument("--project", help="Target project directory (output to chat-logs/)")
    parser.add_argument("--output", help="Explicit output file path")
    detail_group = parser.add_mutually_exclusive_group()
    detail_group.add_argument(
        "--summary",
        action="store_true",
        help="Export compact summary mode (tool labels only)",
    )
    detail_group.add_argument(
        "--verbose",
        action="store_true",
        help="Deprecated alias for full-detail mode (default)",
    )
    parser.add_argument("--no-thinking", action="store_true", help="Exclude thinking blocks")
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Also copy the raw session .jsonl next to the exported .qmd",
    )
    parser.add_argument("--workspace", help="Override workspace root path")
    parser.add_argument("--json", action="store_true", help="JSON output (with --list)")

    args = parser.parse_args()

    workspace_path = Path(args.workspace) if args.workspace else _WORKSPACE_ROOT
    storage_root = _vscode_storage_root()

    if args.list:
        sessions = _discover_sessions(storage_root, workspace_path)
        if args.json:
            print(json.dumps(sessions, indent=2))
        else:
            if not sessions:
                print("No chat sessions found for this workspace.")
                return 0
            print(f"Found {len(sessions)} session(s):\n")
            for s in sessions:
                title = s["title"] or "(untitled)"
                print(f"  {s['session_id']}")
                print(f"    Title:   {title}")
                print(f"    Date:    {s['creation_date']}")
                print(f"    Model:   {s['model_id']}")
                print(f"    Lines:   {s['line_count']}")
                print()
        return 0

    # Resolve session to export
    sessions = _discover_sessions(storage_root, workspace_path)
    if not sessions:
        print("Error: No chat sessions found for this workspace.", file=sys.stderr)
        return 1

    if args.latest:
        target = sessions[0]
    else:
        matches = [s for s in sessions if s["session_id"] == args.session_id]
        if not matches:
            print(f"Error: Session '{args.session_id}' not found.", file=sys.stderr)
            print("Use --list to see available sessions.", file=sys.stderr)
            return 1
        target = matches[0]

    session_path = Path(target["path"])

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    elif args.project:
        project_dir = Path(args.project)
        if not project_dir.is_absolute():
            project_dir = workspace_path / project_dir
        title_slug = _slugify(target["title"]) if target["title"] else target["session_id"][:8]
        date_prefix = target["creation_date"][:10] if target["creation_date"] else "undated"
        filename = f"session-{date_prefix}-{title_slug}.qmd"
        output_path = project_dir / "chat-logs" / filename
    else:
        print("Error: Specify --project or --output for export destination.", file=sys.stderr)
        return 1

    detail_level = "summary" if args.summary else "full"
    include_thinking = not args.no_thinking

    result = _export_session(
        session_path,
        output_path,
        include_thinking=include_thinking,
        detail_level=detail_level,
    )
    if args.raw:
        raw_dest = output_path.with_suffix(".jsonl")
        shutil.copyfile(session_path, raw_dest)
        print(f"Raw session copied to: {raw_dest}")
    print(f"Exported to: {result}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
