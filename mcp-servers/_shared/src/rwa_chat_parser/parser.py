"""JSONL parser for VS Code Copilot Chat session files.

Reads the undocumented JSONL format stored in:
  %APPDATA%/Code/User/workspaceStorage/<hash>/chatSessions/<session-id>.jsonl

JSONL entry kinds:
  kind 0 — Session metadata (version, model, sessionId, creationDate).
           May embed the session's first request(s) in v.requests.
  kind 1 — State patches (title, input text, model state, follow-ups, etc.)
  kind 2 — Request/response data (the actual conversation turns)
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .models import ChatMessage, ChatSession, ClarificationQA, ThinkingBlock, ToolCall

logger = logging.getLogger(__name__)


def parse_session(path: Path) -> ChatSession:
    """Parse a VS Code Copilot Chat JSONL file into a ChatSession.

    Parameters
    ----------
    path:
        Absolute path to the ``.jsonl`` session file.

    Returns
    -------
    ChatSession with all messages populated.
    """
    session = ChatSession()
    # Accumulate request entries and response patches separately
    request_map: dict[int, dict[str, Any]] = {}  # index -> raw request dict
    response_patches: dict[int, list[Any]] = {}  # index -> accumulated response items
    # Retry confirmations ("Try Again") map retry index -> original request index
    retry_targets: dict[int, int] = {}
    last_primary_index: int | None = None

    with open(path, encoding="utf-8") as fh:
        for line_no, raw_line in enumerate(fh, start=1):
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                entry = json.loads(raw_line)
            except json.JSONDecodeError:
                logger.warning("Skipping malformed JSON on line %d", line_no)
                continue

            kind = entry.get("kind")
            keys = entry.get("k", [])
            value = entry.get("v")

            if kind == 0:
                _parse_session_metadata(entry, session)
                # The first request(s) of a session are embedded in the
                # kind-0 metadata under v.requests. Later requests arrive as
                # kind-2 appends, so seed the request map from metadata first
                # to keep indices aligned with VS Code's own numbering.
                meta_requests = entry.get("v", {}).get("requests", [])
                if isinstance(meta_requests, list):
                    for raw_req in meta_requests:
                        if isinstance(raw_req, dict):
                            req_index = len(request_map)
                            request_map[req_index] = raw_req
                            last_primary_index = req_index
                            inline_response = raw_req.get("response", [])
                            if inline_response:
                                response_patches.setdefault(req_index, []).extend(
                                    inline_response
                                )
            elif kind == 1:
                _apply_state_patch(keys, value, session)
            elif kind == 2:
                _apply_data_entry(
                    keys, value, request_map, response_patches, retry_targets, last_primary_index
                )
            else:
                logger.debug("Unknown entry kind %s on line %d", kind, line_no)

    # Build ChatMessage objects from accumulated data
    session.messages = _build_messages(request_map, response_patches)

    # Backfill session model from first message if not set in metadata
    if not session.model_id and session.messages:
        session.model_id = session.messages[0].model_id

    return session


def _parse_session_metadata(entry: dict[str, Any], session: ChatSession) -> None:
    """Extract session-level metadata from a kind-0 entry."""
    v = entry.get("v", {})
    session.version = v.get("version", 0)
    session.session_id = v.get("sessionId", "")
    session.model_id = v.get("modelId", "")

    creation_ts = v.get("creationDate")
    if creation_ts and isinstance(creation_ts, (int, float)):
        session.creation_date = datetime.fromtimestamp(creation_ts / 1000, tz=UTC)


def _apply_state_patch(keys: list[str], value: Any, session: ChatSession) -> None:
    """Process kind-1 state patches (title, input text, etc.)."""
    if keys == ["customTitle"] and isinstance(value, str):
        session.title = value


def _apply_data_entry(
    keys: list[str],
    value: Any,
    request_map: dict[int, dict[str, Any]],
    response_patches: dict[int, list[Any]],
    retry_targets: dict[int, int],
    last_primary_index: int | None = None,
) -> None:
    """Process kind-2 data entries (requests and responses).

    kind-2 entries come in two forms:
      keys=["requests"]               -> new request(s) with inline response
      keys=["requests", N, "response"] -> response continuation for request index N
    """
    if keys == ["requests"] and isinstance(value, list):
        # New request entry — may contain multiple requests (usually 1)
        for raw_req in value:
            if not isinstance(raw_req, dict):
                continue
            req_index = len(request_map)
            if raw_req.get("confirmation"):
                # Retry confirmation ("Try Again"): duplicates a prior
                # request. Record the mapping so response patches targeted at
                # this retry index are merged into the original turn instead
                # of creating a duplicate turn with placeholder text.
                target = last_primary_index if last_primary_index is not None else req_index
                retry_targets[req_index] = target
                # A retry may carry its own response payload (the successful
                # attempt after earlier failures) — merge it into the target.
                inline_response = raw_req.get("response", [])
                if inline_response:
                    response_patches.setdefault(target, []).extend(inline_response)
                continue
            request_map[req_index] = raw_req
            last_primary_index = req_index
            # The initial request often contains response data inline
            inline_response = raw_req.get("response", [])
            if inline_response:
                response_patches.setdefault(req_index, []).extend(inline_response)

    elif (
        len(keys) == 3
        and keys[0] == "requests"
        and keys[2] == "response"
        and isinstance(value, list)
    ):
        try:
            idx = int(keys[1])
        except (ValueError, TypeError):
            return
        # Redirect patches aimed at retry confirmations to the original turn
        idx = retry_targets.get(idx, idx)
        response_patches.setdefault(idx, []).extend(value)

    elif keys == ["pendingRequests"]:
        # Ignore pending request markers
        pass


def _build_messages(
    request_map: dict[int, dict[str, Any]],
    response_patches: dict[int, list[Any]],
) -> list[ChatMessage]:
    """Assemble ChatMessage objects from raw request/response data."""
    messages: list[ChatMessage] = []

    for idx in sorted(request_map.keys()):
        raw_req = request_map[idx]
        msg = _parse_request(raw_req)

        # Merge all response patches for this index
        all_response_items = response_patches.get(idx, [])
        _parse_response_items(all_response_items, msg)

        messages.append(msg)

    return messages


def _parse_request(raw: dict[str, Any]) -> ChatMessage:
    """Extract user request metadata into a ChatMessage."""
    timestamp_ms = raw.get("timestamp", 0)
    ts = datetime.fromtimestamp(timestamp_ms / 1000, tz=UTC) if timestamp_ms else datetime.now(UTC)

    agent = raw.get("agent", {})
    message = raw.get("message", {})

    return ChatMessage(
        request_id=raw.get("requestId", ""),
        timestamp=ts,
        model_id=raw.get("modelId", ""),
        agent_name=agent.get("name", "") if isinstance(agent, dict) else "",
        user_text=message.get("text", "") if isinstance(message, dict) else "",
    )


def _parse_response_items(items: list[Any], msg: ChatMessage) -> None:
    """Parse response content items and populate the ChatMessage."""
    text_parts: list[str] = []

    for item in items:
        if not isinstance(item, dict):
            continue

        item_kind = item.get("kind")

        if item_kind == "thinking":
            content = item.get("value", "")
            if isinstance(content, list):
                content = "\n".join(str(c) for c in content)
            elif not isinstance(content, str):
                content = str(content)
            # Skip empty thinking blocks (stop markers)
            if content.strip():
                msg.thinking_blocks.append(ThinkingBlock(content=content))

        elif item_kind == "toolInvocationSerialized":
            msg.tool_calls.append(_parse_tool_call(item))

        elif item_kind == "questionCarousel":
            msg.clarification_qas.extend(_parse_question_carousel(item))

        elif item_kind == "mcpServersStarting":
            # Internal housekeeping — skip
            continue

        elif item_kind == "inlineReference":
            # File references embedded in response — skip (decorative)
            continue

        elif item_kind is None or item_kind == "markdownContent":
            # Plain text content block
            value = item.get("value", "")
            if isinstance(value, str) and value.strip():
                text_parts.append(value)

        else:
            logger.debug("Unknown response item kind: %s", item_kind)

    msg.response_text = "".join(text_parts)


def _parse_tool_call(item: dict[str, Any]) -> ToolCall:
    """Parse a tool invocation entry."""
    tool_id = item.get("toolId", "")

    inv_msg = item.get("invocationMessage", {})
    inv_text = inv_msg.get("value", "") if isinstance(inv_msg, dict) else str(inv_msg)

    past_msg = item.get("pastTenseMessage", {})
    past_text = past_msg.get("value", "") if isinstance(past_msg, dict) else str(past_msg)

    source = item.get("source", {})
    source_label = source.get("label", "") if isinstance(source, dict) else ""

    tc = ToolCall(
        tool_id=tool_id,
        invocation_message=inv_text,
        past_tense_message=past_text,
        is_complete=bool(item.get("isComplete", True)),
        source_label=source_label,
        is_error=bool(item.get("isError", False)),
    )

    # Verbose details from resultDetails (MCP tools)
    rd = item.get("resultDetails")
    if isinstance(rd, dict):
        tc.is_error = tc.is_error or bool(rd.get("isError", False))
        tc.result_input = _flatten_result(rd.get("input", ""))
        tc.result_output = _flatten_result(rd.get("output", ""))
    elif isinstance(rd, list):
        tc.is_error = tc.is_error or any(
            isinstance(part, dict) and bool(part.get("isError", False)) for part in rd
        )
        tc.result_output = _flatten_result(rd)
    elif rd:
        tc.result_output = _flatten_result(rd)

    # Terminal tool details
    tsd = item.get("toolSpecificData")
    if isinstance(tsd, dict):
        tsd_kind = tsd.get("kind")
        if tsd_kind == "terminal":
            cmd = tsd.get("commandLine", {})
            cmd_text = cmd.get("original", "") if isinstance(cmd, dict) else ""
            state = tsd.get("terminalCommandState", {})
            exit_code = state.get("exitCode") if isinstance(state, dict) else None
            output = tsd.get("terminalCommandOutput", {})
            out_text = output.get("text", "") if isinstance(output, dict) else ""
            if cmd_text:
                tc.result_input = cmd_text

            output_parts = [part for part in [tc.result_output, out_text] if part]
            if exit_code is not None:
                output_parts.append(f"[exit code: {exit_code}]")
                try:
                    if int(exit_code) != 0:
                        tc.is_error = True
                except (TypeError, ValueError):
                    # Preserve unknown exit code text while treating it as an error.
                    tc.is_error = True

            tc.result_output = "\n".join(output_parts)

    return tc


def _parse_question_carousel(item: dict[str, Any]) -> list[ClarificationQA]:
    """Parse clarification prompts and selected answers from questionCarousel items."""
    questions = item.get("questions")
    if not isinstance(questions, list):
        return []

    answers = item.get("data", {})
    if not isinstance(answers, dict):
        answers = {}

    qas: list[ClarificationQA] = []
    for question in questions:
        if not isinstance(question, dict):
            continue

        prompt = _resolve_question_prompt(question)
        if not prompt:
            continue

        question_id_raw = question.get("id")
        question_id = str(question_id_raw).strip() if question_id_raw is not None else ""
        selected = answers.get(question_id) if question_id else None
        answer = _resolve_selected_answer(selected, question)

        qas.append(ClarificationQA(question=prompt, answer=answer))

    return qas


def _resolve_question_prompt(question: dict[str, Any]) -> str:
    """Resolve the most descriptive prompt text for a clarification question."""
    candidates = [question.get("message"), question.get("title"), question.get("question")]
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
        if isinstance(candidate, dict):
            value = candidate.get("value")
            if isinstance(value, str) and value.strip():
                return value.strip()
    return ""


def _resolve_selected_answer(selected: Any, question: dict[str, Any]) -> str:
    """Resolve selected answer text, preferring option labels with descriptive text."""
    selected_values: list[str] = []
    if isinstance(selected, str) and selected.strip():
        selected_values.append(selected.strip())
    elif isinstance(selected, dict):
        selected_values.extend(_extract_selected_values(selected))

    options = question.get("options", [])
    resolved_values = [_resolve_option_label(value, options) for value in selected_values if value]

    if resolved_values:
        return "; ".join(resolved_values)

    return ""


def _extract_selected_values(selected: dict[str, Any]) -> list[str]:
    """Extract one or more selected values from a question response payload."""
    values: list[str] = []
    candidate_keys = ["selectedValue", "value", "text", "answer", "freeformValue"]
    for key in candidate_keys:
        value = selected.get(key)
        if isinstance(value, str) and value.strip():
            values.append(value.strip())

    selected_values = selected.get("selectedValues")
    if isinstance(selected_values, list):
        for value in selected_values:
            if isinstance(value, str) and value.strip():
                values.append(value.strip())

    # Preserve insertion order while de-duplicating
    deduped = list(dict.fromkeys(values))
    return deduped


def _resolve_option_label(value: str, options: Any) -> str:
    """Map a selected option value/id to its display label when available."""
    if not isinstance(options, list):
        return value

    normalized_value = value.strip().lower()
    for option in options:
        if not isinstance(option, dict):
            continue

        candidates = [option.get("id"), option.get("value"), option.get("label")]
        normalized_candidates = {
            str(candidate).strip().lower()
            for candidate in candidates
            if isinstance(candidate, str) and candidate.strip()
        }

        if normalized_value in normalized_candidates:
            label = option.get("label") or option.get("value") or option.get("id")
            if isinstance(label, str) and label.strip():
                return label.strip()

    return value


def _flatten_result(value: Any) -> str:
    """Flatten a result value to a string."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        if "value" in value:
            embedded = value.get("value")
            if isinstance(embedded, str):
                return embedded
            return _flatten_result(embedded)
        try:
            return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
        except TypeError:
            return str(value)
    if isinstance(value, list):
        parts = [_flatten_result(item) for item in value]
        return "\n".join(parts)
    if value is None:
        return ""
    return str(value)
