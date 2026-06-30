"""Google Workspace MCP server.

Supports OAuth user login, Google Drive import/export, and Google Docs comment
round-tripping into structured local change proposals.
"""

from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import re
from datetime import UTC, datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from urllib import parse, request

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaInMemoryUpload
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "google-workspace",
    instructions=(
        "Manage Google Drive and Google Docs review workflows with OAuth, "
        "import/export, and comment-to-proposal mapping for project files."
    ),
)

ANCHOR_RE = re.compile(r"\[\[RWA-LINE:(\d{6}):([0-9a-f]{8})\]\]")
DEFAULT_REDIRECT_URI = "http://localhost:8765/"
DEFAULT_SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents.readonly",
]


def _workspace_root() -> Path:
    """Resolve the workspace root path."""
    start = Path(__file__).resolve().parent
    for candidate in (start, *start.parents):
        if (candidate / ".vscode" / "mcp.json").is_file():
            return candidate
    return Path.cwd()


def _utc_now() -> str:
    """Return UTC timestamp in ISO format."""
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _scopes() -> list[str]:
    """Get OAuth scopes from environment or defaults."""
    raw = os.environ.get("GOOGLE_OAUTH_SCOPES", "").strip()
    if not raw:
        return DEFAULT_SCOPES
    scopes = [item.strip() for item in raw.split(",") if item.strip()]
    return scopes or DEFAULT_SCOPES


def _redirect_uri(override: str | None = None) -> str:
    """Resolve OAuth redirect URI."""
    if override and override.strip():
        return override.strip()
    return os.environ.get("GOOGLE_OAUTH_REDIRECT_URI", DEFAULT_REDIRECT_URI).strip()


def _oauth_client_config(override_redirect_uri: str | None = None) -> dict[str, Any]:
    """Build OAuth client config from environment variables."""
    client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "").strip()
    client_secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "").strip()
    redirect_uri = _redirect_uri(override_redirect_uri)

    if not client_id or not client_secret:
        raise RuntimeError(
            "Google OAuth is not configured. Set GOOGLE_OAUTH_CLIENT_ID and "
            "GOOGLE_OAUTH_CLIENT_SECRET in .env."
        )

    return {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri],
        }
    }


def _token_file() -> Path:
    """Resolve OAuth token file path."""
    raw_path = os.environ.get(
        "GOOGLE_WORKSPACE_TOKEN_PATH", "./secrets/google-workspace-token.json"
    ).strip()
    token_path = Path(raw_path)
    if not token_path.is_absolute():
        token_path = _workspace_root() / token_path
    token_path.parent.mkdir(parents=True, exist_ok=True)
    return token_path.resolve()


def _pending_state_file() -> Path:
    """Resolve pending OAuth state file path."""
    token_path = _token_file()
    return token_path.with_suffix(".pending.json")


def _save_pending_state(state: str, redirect_uri: str, code_verifier: str = "") -> None:
    """Persist pending OAuth state metadata."""
    payload = {
        "state": state,
        "redirect_uri": redirect_uri,
        "created_at": _utc_now(),
        "scopes": _scopes(),
        "code_verifier": code_verifier,
    }
    _pending_state_file().write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _load_pending_state() -> dict[str, Any] | None:
    """Load pending OAuth state metadata if available."""
    state_file = _pending_state_file()
    if not state_file.exists():
        return None
    try:
        return json.loads(state_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _clear_pending_state() -> None:
    """Delete pending OAuth state metadata."""
    state_file = _pending_state_file()
    if state_file.exists():
        state_file.unlink()


def _save_credentials(creds: Credentials) -> None:
    """Persist OAuth credentials to disk."""
    _token_file().write_text(creds.to_json(), encoding="utf-8")


def _load_credentials(*, require_valid: bool = True) -> Credentials:
    """Load OAuth credentials and refresh when possible."""
    token_path = _token_file()
    if not token_path.exists():
        raise RuntimeError("Google auth token not found. Run gws_auth_get_authorization_url first.")

    info = json.loads(token_path.read_text(encoding="utf-8"))
    creds = Credentials.from_authorized_user_info(info, scopes=_scopes())

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        _save_credentials(creds)

    if require_valid and not creds.valid:
        raise RuntimeError("Google auth token is invalid. Reconnect with OAuth tools.")

    return creds


def _drive_service() -> Any:
    """Build Google Drive API client."""
    creds = _load_credentials(require_valid=True)
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def _require_project_path(project_path: str) -> Path:
    """Validate and resolve project path."""
    if not project_path or not project_path.strip():
        raise ValueError("project_path is required and must point to an existing directory.")

    resolved = Path(project_path).expanduser()
    if not resolved.is_absolute():
        resolved = (_workspace_root() / resolved).resolve()

    if not resolved.exists() or not resolved.is_dir():
        raise ValueError(f"Invalid project_path: {project_path}")

    return resolved


def _resolve_local_path(project_root: Path, path_value: str) -> Path:
    """Resolve a local file path relative to project root."""
    if not path_value or not path_value.strip():
        raise ValueError("A non-empty file path is required.")

    candidate = Path(path_value).expanduser()
    if not candidate.is_absolute():
        candidate = (project_root / candidate).resolve()

    return candidate


def _sync_root(project_root: Path) -> Path:
    """Return project sync root for Google integration artifacts."""
    root = project_root / "review-sync" / "google-docs"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _manifest_path(project_root: Path, doc_id: str) -> Path:
    """Return path to sync manifest for a document."""
    return _sync_root(project_root) / f"{doc_id}.manifest.json"


def _anchors_path(project_root: Path, doc_id: str) -> Path:
    """Return path to stored line-anchor mapping for a document."""
    return _sync_root(project_root) / f"{doc_id}.anchors.json"


def _comments_path(project_root: Path, doc_id: str) -> Path:
    """Return path to stored raw comments for a document."""
    return _sync_root(project_root) / f"{doc_id}.comments.json"


def _update_manifest(project_root: Path, doc_id: str, patch: dict[str, Any]) -> dict[str, Any]:
    """Upsert sync manifest fields for a document."""
    path = _manifest_path(project_root, doc_id)
    current: dict[str, Any] = {}

    if path.exists():
        try:
            current = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            current = {}

    current.update(patch)
    current["updated_at"] = _utc_now()

    path.write_text(json.dumps(current, indent=2), encoding="utf-8")
    return current


def _load_manifest(project_root: Path, doc_id: str) -> dict[str, Any] | None:
    """Load sync manifest when present."""
    path = _manifest_path(project_root, doc_id)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _sha256_bytes(content: bytes) -> str:
    """Compute SHA-256 hash for bytes content."""
    return hashlib.sha256(content).hexdigest()


def _sha256_text(content: str) -> str:
    """Compute SHA-256 hash for UTF-8 text."""
    return _sha256_bytes(content.encode("utf-8"))


def _sanitize_filename(name: str) -> str:
    """Sanitize filename to avoid invalid path characters."""
    candidate = re.sub(r"[^A-Za-z0-9._ -]", "_", name).strip()
    return candidate or "untitled"


def _extract_code(value: str) -> str:
    """Extract auth code from code string or redirected URL."""
    candidate = value.strip()
    if "code=" not in candidate:
        return candidate

    parsed = parse.urlparse(candidate)
    params = parse.parse_qs(parsed.query)
    if "code" in params and params["code"]:
        return params["code"][0]
    return candidate


def _line_hash(line_text: str, line_number: int) -> str:
    """Build stable 8-char hash for a source line."""
    basis = line_text if line_text else f"blank-{line_number}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:8]


def _insert_line_anchors(content: str) -> tuple[str, dict[str, Any]]:
    """Append deterministic line anchors used for Docs comment mapping."""
    source_lines = content.splitlines()
    anchored_lines: list[str] = []
    anchors: list[dict[str, Any]] = []

    for idx, line in enumerate(source_lines, start=1):
        hash_value = _line_hash(line.strip(), idx)
        token = f"[[RWA-LINE:{idx:06d}:{hash_value}]]"
        combined = f"{line} {token}" if line.strip() else token
        anchored_lines.append(combined)
        anchors.append({"line": idx, "hash": hash_value, "token": token})

    anchored_text = "\n".join(anchored_lines)
    if content.endswith("\n") and anchored_text:
        anchored_text += "\n"

    return anchored_text, {
        "strategy": "line-token-v1",
        "line_count": len(source_lines),
        "anchors": anchors,
    }


def _strip_anchor_tokens(text: str) -> str:
    """Remove deterministic line-anchor tokens from text."""
    return ANCHOR_RE.sub("", text or "").strip()


def _extract_anchor_reference(text: str) -> tuple[int | None, str | None]:
    """Extract line and hash from anchor token when present."""
    match = ANCHOR_RE.search(text or "")
    if not match:
        return None, None

    return int(match.group(1)), match.group(2)


def _normalize_ws(text: str) -> str:
    """Normalize whitespace for fuzzy matching."""
    return " ".join((text or "").split()).strip()


def _best_line_match(lines: list[str], snippet: str) -> tuple[int | None, float]:
    """Find best candidate line for text snippet using fuzzy similarity."""
    normalized_snippet = _normalize_ws(_strip_anchor_tokens(snippet))
    if not normalized_snippet:
        return None, 0.0

    best_line: int | None = None
    best_score = 0.0

    for idx, line in enumerate(lines, start=1):
        normalized_line = _normalize_ws(line)
        if not normalized_line:
            continue

        if normalized_snippet in normalized_line or normalized_line in normalized_snippet:
            ratio = min(len(normalized_snippet), len(normalized_line)) / max(
                len(normalized_snippet), len(normalized_line)
            )
            score = max(0.85, ratio)
        else:
            score = SequenceMatcher(
                None,
                normalized_snippet.lower(),
                normalized_line.lower(),
            ).ratio()

        if score > best_score:
            best_line = idx
            best_score = score

    return best_line, best_score


def _read_text_file(file_path: Path) -> str:
    """Read UTF-8 text file content."""
    return file_path.read_text(encoding="utf-8")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write JSON data with indentation."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _proposals_dir(project_root: Path) -> Path:
    """Return proposal output directory."""
    out = _sync_root(project_root) / "proposals"
    out.mkdir(parents=True, exist_ok=True)
    return out


def _render_proposals_qmd(
    *,
    doc_id: str,
    local_target_file: str,
    proposals: list[dict[str, Any]],
) -> str:
    """Render proposal summary in QMD for reviewer-friendly inspection."""
    ts = _utc_now()
    lines = [
        "---",
        'title: "Google Docs Review Proposals"',
        f'date: "{ts}"',
        "format:",
        "  html:",
        "    toc: true",
        "    self-contained: true",
        "---",
        "",
        "# Summary",
        "",
        f"- Google Doc ID: {doc_id}",
        f"- Target file: {local_target_file}",
        f"- Proposal count: {len(proposals)}",
        "",
        "# Proposals",
        "",
    ]

    if not proposals:
        lines.extend(["No proposals were generated.", ""])
        return "\n".join(lines)

    for item in proposals:
        replies = item.get("replies", [])
        lines.extend(
            [
                f"## Proposal {item.get('proposal_id')}",
                "",
                f"- Comment ID: {item.get('comment_id')}",
                f"- Mapping strategy: {item.get('mapping_strategy')}",
                f"- Confidence: {item.get('confidence')}",
                f"- Target line: {item.get('target_line')}",
                f"- Status: {item.get('status')}",
                "",
                "### Comment",
                "",
                item.get("comment", ""),
                "",
                "### Quoted Text",
                "",
                "```text",
                item.get("quoted_text", ""),
                "```",
                "",
                "### Replies",
                "",
            ]
        )
        if replies:
            for reply in replies:
                lines.append(f"- {reply.get('author', 'unknown')}: {reply.get('content', '')}")
        else:
            lines.append("- No replies")
        lines.extend(["", "### Suggested Patch", "", "```text", "None", "```", ""])

    return "\n".join(lines)


def _drive_list_comments(
    drive_service: Any, doc_id: str, include_resolved: bool
) -> list[dict[str, Any]]:
    """Fetch comments from Google Drive for a document."""
    comments: list[dict[str, Any]] = []
    page_token: str | None = None

    while True:
        response = (
            drive_service.comments()
            .list(
                fileId=doc_id,
                pageSize=100,
                pageToken=page_token,
                includeDeleted=False,
                fields=(
                    "nextPageToken,comments(id,content,quotedFileContent,createdTime,"
                    "modifiedTime,resolved,author(displayName,emailAddress),"
                    "replies(id,content,createdTime,modifiedTime,"
                    "author(displayName,emailAddress),action),deleted)"
                ),
            )
            .execute()
        )

        for comment in response.get("comments", []):
            if comment.get("deleted"):
                continue
            if not include_resolved and comment.get("resolved"):
                continue
            comments.append(comment)

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return comments


@mcp.tool()
def gws_auth_get_authorization_url(redirect_uri: str = "") -> dict[str, Any]:
    """Generate OAuth authorization URL for Google Workspace access."""
    resolved_redirect = _redirect_uri(redirect_uri or None)
    config = _oauth_client_config(resolved_redirect)

    flow = InstalledAppFlow.from_client_config(
        config,
        scopes=_scopes(),
        redirect_uri=resolved_redirect,
    )
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    code_verifier = getattr(flow, "code_verifier", "")
    if not code_verifier:
        code_verifier = getattr(getattr(flow, "oauth2session", None), "_client", None)
        code_verifier = getattr(code_verifier, "code_verifier", "")

    _save_pending_state(state, resolved_redirect, str(code_verifier or ""))

    return {
        "authorization_url": auth_url,
        "state": state,
        "redirect_uri": resolved_redirect,
        "scopes": _scopes(),
        "message": (
            "Open authorization_url in a browser, approve access, then call "
            "gws_auth_exchange_code with the returned code or full redirect URL."
        ),
    }


@mcp.tool()
def gws_auth_exchange_code(code_or_redirect_url: str, redirect_uri: str = "") -> dict[str, Any]:
    """Exchange OAuth code for a refreshable token and store it locally."""
    authorization_code = _extract_code(code_or_redirect_url)
    if not authorization_code:
        raise ValueError("A non-empty authorization code is required.")

    # Accept supersets of requested scopes when a Google account has prior grants.
    os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")

    pending = _load_pending_state()
    resolved_redirect = _redirect_uri(redirect_uri or None)
    if pending and pending.get("redirect_uri"):
        resolved_redirect = str(pending.get("redirect_uri"))

    config = _oauth_client_config(resolved_redirect)
    flow = InstalledAppFlow.from_client_config(
        config,
        scopes=_scopes(),
        redirect_uri=resolved_redirect,
    )
    fetch_kwargs: dict[str, Any] = {"code": authorization_code}
    if pending and pending.get("code_verifier"):
        fetch_kwargs["code_verifier"] = str(pending.get("code_verifier"))

    flow.fetch_token(**fetch_kwargs)

    creds = flow.credentials
    _save_credentials(creds)
    _clear_pending_state()

    return {
        "status": "connected",
        "token_path": str(_token_file()),
        "scopes": sorted(list(creds.scopes or [])),
        "expires_at": creds.expiry.isoformat() if creds.expiry else None,
    }


@mcp.tool()
def gws_auth_status() -> dict[str, Any]:
    """Check Google OAuth connection status."""
    token_path = _token_file()
    if not token_path.exists():
        return {
            "connected": False,
            "token_path": str(token_path),
            "message": "No token file found. Run OAuth connect tools.",
        }

    try:
        creds = _load_credentials(require_valid=False)
        valid = bool(creds.valid)
        return {
            "connected": True,
            "valid": valid,
            "expired": bool(creds.expired),
            "has_refresh_token": bool(creds.refresh_token),
            "scopes": sorted(list(creds.scopes or [])),
            "token_path": str(token_path),
            "expires_at": creds.expiry.isoformat() if creds.expiry else None,
        }
    except Exception as exc:  # pragma: no cover
        return {
            "connected": False,
            "token_path": str(token_path),
            "error": str(exc),
        }


@mcp.tool()
def gws_auth_revoke() -> dict[str, Any]:
    """Revoke Google OAuth token and remove local credentials."""
    token_path = _token_file()
    if not token_path.exists():
        return {"status": "not-connected", "message": "No token file found."}

    info = json.loads(token_path.read_text(encoding="utf-8"))
    token = str(info.get("token", "")).strip()
    remote_status: int | None = None

    if token:
        data = parse.urlencode({"token": token}).encode("utf-8")
        req = request.Request(
            "https://oauth2.googleapis.com/revoke",
            data=data,
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        try:
            with request.urlopen(req, timeout=10) as response:  # noqa: S310
                remote_status = int(getattr(response, "status", 0))
        except Exception:
            remote_status = None

    token_path.unlink(missing_ok=True)
    _clear_pending_state()

    return {
        "status": "revoked",
        "remote_status": remote_status,
        "token_path": str(token_path),
    }


@mcp.tool()
def gws_drive_list_files(query: str = "", page_size: int = 20) -> dict[str, Any]:
    """List Drive files for the authenticated user."""
    drive_service = _drive_service()
    page_size = min(max(page_size, 1), 100)

    effective_query = query.strip() or "trashed = false"
    if "trashed" not in effective_query.lower():
        effective_query = f"({effective_query}) and trashed = false"

    try:
        response = (
            drive_service.files()
            .list(
                q=effective_query,
                pageSize=page_size,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                fields=(
                    "nextPageToken,files(id,name,mimeType,modifiedTime,webViewLink,parents,size)"
                ),
            )
            .execute()
        )
    except HttpError as exc:
        raise RuntimeError(f"Drive list failed: {exc}") from exc

    return {
        "files": response.get("files", []),
        "next_page_token": response.get("nextPageToken"),
        "query": effective_query,
    }


@mcp.tool()
def gws_drive_import_file(
    file_id: str,
    project_path: str,
    output_path: str = "",
    export_mime_type: str = "text/plain",
) -> dict[str, Any]:
    """Import a Drive file into a local project path."""
    project_root = _require_project_path(project_path)
    drive_service = _drive_service()

    try:
        metadata = (
            drive_service.files()
            .get(
                fileId=file_id,
                fields="id,name,mimeType,modifiedTime,webViewLink,size",
                supportsAllDrives=True,
            )
            .execute()
        )

        mime_type = str(metadata.get("mimeType", ""))

        if mime_type.startswith("application/vnd.google-apps"):
            raw = (
                drive_service.files()
                .export_media(fileId=file_id, mimeType=export_mime_type)
                .execute()
            )
            default_extension = {
                "text/plain": ".txt",
                "text/markdown": ".md",
                "application/pdf": ".pdf",
            }.get(export_mime_type, ".txt")
        else:
            raw = drive_service.files().get_media(fileId=file_id).execute()
            default_extension = Path(str(metadata.get("name", "")).strip()).suffix or ""
    except HttpError as exc:
        raise RuntimeError(f"Drive import failed: {exc}") from exc

    if output_path.strip():
        destination = _resolve_local_path(project_root, output_path)
    else:
        safe_name = _sanitize_filename(str(metadata.get("name", "untitled")))
        destination = project_root / "imports" / safe_name
        if default_extension and not destination.suffix:
            destination = destination.with_suffix(default_extension)

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(raw)

    return {
        "imported_file": str(destination),
        "source": metadata,
        "sha256": _sha256_bytes(raw),
        "bytes": len(raw),
    }


@mcp.tool()
def gws_drive_upload_file(
    local_file_path: str,
    project_path: str,
    parent_folder_id: str = "",
    convert_to_google_doc: bool = False,
    update_file_id: str = "",
) -> dict[str, Any]:
    """Upload a local file to Drive or update an existing Drive file."""
    project_root = _require_project_path(project_path)
    local_path = _resolve_local_path(project_root, local_file_path)

    if not local_path.exists() or not local_path.is_file():
        raise ValueError(f"Local file not found: {local_path}")

    drive_service = _drive_service()
    guessed_mime = mimetypes.guess_type(str(local_path))[0] or "text/plain"

    metadata: dict[str, Any] = {"name": local_path.name}
    if parent_folder_id.strip():
        metadata["parents"] = [parent_folder_id.strip()]
    if convert_to_google_doc:
        metadata["mimeType"] = "application/vnd.google-apps.document"

    media = MediaFileUpload(str(local_path), mimetype=guessed_mime, resumable=False)

    try:
        if update_file_id.strip():
            uploaded = (
                drive_service.files()
                .update(
                    fileId=update_file_id.strip(),
                    body=metadata,
                    media_body=media,
                    fields="id,name,mimeType,webViewLink,modifiedTime,size",
                    supportsAllDrives=True,
                )
                .execute()
            )
        else:
            uploaded = (
                drive_service.files()
                .create(
                    body=metadata,
                    media_body=media,
                    fields="id,name,mimeType,webViewLink,modifiedTime,size",
                    supportsAllDrives=True,
                )
                .execute()
            )
    except HttpError as exc:
        raise RuntimeError(f"Drive upload failed: {exc}") from exc

    return {
        "uploaded": uploaded,
        "local_file": str(local_path),
        "sha256": _sha256_bytes(local_path.read_bytes()),
    }


@mcp.tool()
def gws_docs_export_review_copy(
    project_path: str,
    local_target_file: str,
    title: str = "",
    parent_folder_id: str = "",
) -> dict[str, Any]:
    """Export local file to Google Docs with deterministic line-anchor tokens."""
    project_root = _require_project_path(project_path)
    target_file = _resolve_local_path(project_root, local_target_file)

    if not target_file.exists() or not target_file.is_file():
        raise ValueError(f"Local target file not found: {target_file}")

    source_text = _read_text_file(target_file)
    anchored_text, anchor_map = _insert_line_anchors(source_text)

    review_title = title.strip() or f"{target_file.stem} review copy"

    body: dict[str, Any] = {
        "name": review_title,
        "mimeType": "application/vnd.google-apps.document",
    }
    if parent_folder_id.strip():
        body["parents"] = [parent_folder_id.strip()]

    drive_service = _drive_service()
    media = MediaInMemoryUpload(
        anchored_text.encode("utf-8"), mimetype="text/plain", resumable=False
    )

    try:
        created = (
            drive_service.files()
            .create(
                body=body,
                media_body=media,
                fields="id,name,mimeType,webViewLink,modifiedTime",
                supportsAllDrives=True,
            )
            .execute()
        )
    except HttpError as exc:
        raise RuntimeError(f"Google Docs review export failed: {exc}") from exc

    doc_id = str(created.get("id"))
    if not doc_id:
        raise RuntimeError("Google Docs review export failed: missing document id")

    _write_json(_anchors_path(project_root, doc_id), anchor_map)

    relative_target = str(target_file.relative_to(project_root))
    manifest = _update_manifest(
        project_root,
        doc_id,
        {
            "doc_id": doc_id,
            "doc_name": created.get("name"),
            "doc_web_view_link": created.get("webViewLink"),
            "local_target_file": relative_target,
            "anchor_strategy": anchor_map.get("strategy"),
            "anchor_line_count": anchor_map.get("line_count"),
            "source_sha256": _sha256_text(source_text),
            "exported_at": _utc_now(),
        },
    )

    return {
        "doc": created,
        "doc_id": doc_id,
        "manifest_path": str(_manifest_path(project_root, doc_id)),
        "anchors_path": str(_anchors_path(project_root, doc_id)),
        "anchor_count": len(anchor_map.get("anchors", [])),
        "manifest": manifest,
    }


@mcp.tool()
def gws_docs_pull_comments(
    doc_id: str,
    project_path: str,
    include_resolved: bool = False,
) -> dict[str, Any]:
    """Pull comments and replies from a Google Doc into project sync storage."""
    project_root = _require_project_path(project_path)
    drive_service = _drive_service()

    try:
        comments = _drive_list_comments(drive_service, doc_id, include_resolved)
    except HttpError as exc:
        raise RuntimeError(f"Failed to pull comments for {doc_id}: {exc}") from exc

    payload = {
        "doc_id": doc_id,
        "include_resolved": include_resolved,
        "pulled_at": _utc_now(),
        "count": len(comments),
        "comments": comments,
    }

    comments_file = _comments_path(project_root, doc_id)
    _write_json(comments_file, payload)
    manifest = _update_manifest(
        project_root,
        doc_id,
        {
            "doc_id": doc_id,
            "last_comment_sync": payload["pulled_at"],
            "comment_count": len(comments),
        },
    )

    return {
        "doc_id": doc_id,
        "comments_path": str(comments_file),
        "comment_count": len(comments),
        "manifest_path": str(_manifest_path(project_root, doc_id)),
        "manifest": manifest,
    }


@mcp.tool()
def gws_docs_build_change_proposals(
    doc_id: str,
    project_path: str,
    local_target_file: str = "",
    include_resolved: bool = False,
) -> dict[str, Any]:
    """Build local change proposals from Google Docs comments."""
    project_root = _require_project_path(project_path)

    comments_file = _comments_path(project_root, doc_id)
    if not comments_file.exists():
        gws_docs_pull_comments(
            doc_id=doc_id,
            project_path=str(project_root),
            include_resolved=include_resolved,
        )

    payload = json.loads(comments_file.read_text(encoding="utf-8"))
    comments = payload.get("comments", [])

    manifest = _load_manifest(project_root, doc_id) or {}
    target_value = local_target_file.strip() or str(manifest.get("local_target_file", "")).strip()
    if not target_value:
        raise ValueError(
            "local_target_file is required when no manifest mapping exists for this doc_id."
        )

    target_file = _resolve_local_path(project_root, target_value)
    if not target_file.exists() or not target_file.is_file():
        raise ValueError(f"Local target file not found: {target_file}")

    source_lines = _read_text_file(target_file).splitlines()
    proposals: list[dict[str, Any]] = []

    for comment in comments:
        comment_id = str(comment.get("id", "")).strip()
        if not comment_id:
            continue

        quoted_text = str(comment.get("quotedFileContent", {}).get("value", "") or "")
        target_line, anchor_hash = _extract_anchor_reference(quoted_text)

        mapping_strategy = "anchor"
        confidence = 0.99

        if target_line is None or target_line < 1 or target_line > len(source_lines):
            mapping_strategy = "fuzzy"
            fuzzy_line, fuzzy_score = _best_line_match(
                source_lines, quoted_text or comment.get("content", "")
            )
            target_line = fuzzy_line
            confidence = round(float(fuzzy_score), 3)

        replies = []
        for reply in comment.get("replies", []):
            replies.append(
                {
                    "id": reply.get("id"),
                    "author": reply.get("author", {}).get("displayName", "unknown"),
                    "content": reply.get("content", ""),
                    "created_time": reply.get("createdTime"),
                    "modified_time": reply.get("modifiedTime"),
                    "action": reply.get("action"),
                }
            )

        proposals.append(
            {
                "proposal_id": f"{doc_id}:{comment_id}",
                "doc_id": doc_id,
                "comment_id": comment_id,
                "target_file": str(target_file),
                "target_line": target_line,
                "mapping_strategy": mapping_strategy,
                "confidence": confidence,
                "anchor_hash": anchor_hash,
                "quoted_text": _strip_anchor_tokens(quoted_text),
                "comment": str(comment.get("content", "") or "").strip(),
                "author": comment.get("author", {}).get("displayName", "unknown"),
                "created_time": comment.get("createdTime"),
                "modified_time": comment.get("modifiedTime"),
                "resolved": bool(comment.get("resolved")),
                "replies": replies,
                "recommended_action": "review-and-edit",
                "suggested_patch": None,
                "status": "proposed",
            }
        )

    ts = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    proposals_dir = _proposals_dir(project_root)
    json_path = proposals_dir / f"{doc_id}-{ts}-proposals.json"
    qmd_path = proposals_dir / f"{doc_id}-{ts}-proposals.qmd"

    json_payload = {
        "doc_id": doc_id,
        "generated_at": _utc_now(),
        "target_file": str(target_file),
        "comment_count": len(comments),
        "proposal_count": len(proposals),
        "proposals": proposals,
    }

    _write_json(json_path, json_payload)
    qmd_text = _render_proposals_qmd(
        doc_id=doc_id,
        local_target_file=str(target_file),
        proposals=proposals,
    )
    qmd_path.write_text(qmd_text, encoding="utf-8")

    _update_manifest(
        project_root,
        doc_id,
        {
            "doc_id": doc_id,
            "local_target_file": str(target_file.relative_to(project_root)),
            "last_proposal_build": _utc_now(),
            "proposal_file": str(json_path),
            "proposal_count": len(proposals),
        },
    )

    return {
        "doc_id": doc_id,
        "target_file": str(target_file),
        "proposal_count": len(proposals),
        "proposals_json": str(json_path),
        "proposals_qmd": str(qmd_path),
    }


@mcp.tool()
def gws_docs_list_sync_mappings(project_path: str) -> dict[str, Any]:
    """List Google Doc sync mappings for a project."""
    project_root = _require_project_path(project_path)
    sync_root = _sync_root(project_root)

    mappings: list[dict[str, Any]] = []
    for manifest_path in sorted(sync_root.glob("*.manifest.json")):
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue

        mappings.append(
            {
                "doc_id": payload.get("doc_id"),
                "doc_name": payload.get("doc_name"),
                "local_target_file": payload.get("local_target_file"),
                "last_comment_sync": payload.get("last_comment_sync"),
                "last_proposal_build": payload.get("last_proposal_build"),
                "manifest_path": str(manifest_path),
            }
        )

    return {"project_path": str(project_root), "mapping_count": len(mappings), "mappings": mappings}


def serve() -> None:
    """Run the Google Workspace MCP server."""
    mcp.run(transport="stdio")
