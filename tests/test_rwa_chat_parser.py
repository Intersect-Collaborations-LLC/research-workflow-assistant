from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

# Ensure local shared package is importable without editable install
_SHARED_SRC = Path(__file__).resolve().parents[1] / "mcp-servers" / "_shared" / "src"
if str(_SHARED_SRC) not in sys.path:
    sys.path.insert(0, str(_SHARED_SRC))

from rwa_chat_parser import parse_session, render_qmd  # noqa: E402
from rwa_chat_parser.models import ChatMessage, ChatSession, ToolCall  # noqa: E402


def _write_minimal_session(path: Path) -> None:
    entries = [
        {
            "kind": 0,
            "v": {
                "version": 1,
                "sessionId": "session-1",
                "modelId": "copilot/test-model",
                "creationDate": 1712400000000,
            },
        },
        {"kind": 1, "k": ["customTitle"], "v": "Test Session"},
        {
            "kind": 2,
            "k": ["requests"],
            "v": [
                {
                    "requestId": "req-1",
                    "timestamp": 1712400000000,
                    "modelId": "copilot/test-model",
                    "agent": {"name": "agent"},
                    "message": {"text": "Please clarify"},
                    "response": [
                        {
                            "kind": "toolInvocationSerialized",
                            "toolId": "vscode_askQuestions",
                            "invocationMessage": {
                                "value": "Asked 1 question",
                            },
                            "pastTenseMessage": {
                                "value": "Asked 1 question",
                            },
                            "isComplete": True,
                        },
                        {
                            "kind": "questionCarousel",
                            "questions": [
                                {
                                    "id": "q1",
                                    "title": "What type of output are you envisioning?",
                                    "message": (
                                        "What type of output are you envisioning for this project?"
                                    ),
                                    "options": [
                                        {
                                            "value": "Systematic review",
                                            "label": (
                                                "Systematic review - Formal PRISMA-guided "
                                                "systematic review"
                                            ),
                                        },
                                    ],
                                },
                            ],
                            "data": {
                                "q1": {
                                    "selectedValue": "Systematic review",
                                }
                            },
                        },
                        {
                            "kind": "toolInvocationSerialized",
                            "toolId": "run_in_terminal",
                            "invocationMessage": {
                                "value": "Running `echo hello`",
                            },
                            "pastTenseMessage": {
                                "value": "Ran `echo hello`",
                            },
                            "isComplete": True,
                            "toolSpecificData": {
                                "kind": "terminal",
                                "commandLine": {"original": "echo hello"},
                                "terminalCommandOutput": {
                                    "text": "hello from terminal",
                                },
                                "terminalCommandState": {"exitCode": 1},
                            },
                        },
                        {
                            "kind": "toolInvocationSerialized",
                            "toolId": "semantic-scholar",
                            "invocationMessage": {
                                "value": "Running Semantic Scholar search",
                            },
                            "pastTenseMessage": {
                                "value": "Semantic Scholar returned error",
                            },
                            "isComplete": True,
                            "resultDetails": {
                                "isError": True,
                                "output": "HTTP 429 Too Many Requests",
                            },
                        },
                        {"kind": "markdownContent", "value": "Done."},
                    ],
                }
            ],
        },
    ]

    with open(path, "w", encoding="utf-8") as fh:
        for entry in entries:
            fh.write(json.dumps(entry) + "\n")


def test_parse_session_includes_question_carousel_answers(tmp_path: Path) -> None:
    session_path = tmp_path / "session.jsonl"
    _write_minimal_session(session_path)

    session = parse_session(session_path)

    assert len(session.messages) == 1
    qas = session.messages[0].clarification_qas
    assert len(qas) == 1
    assert qas[0].question == "What type of output are you envisioning for this project?"
    assert qas[0].answer == "Systematic review - Formal PRISMA-guided systematic review"


def test_render_qmd_includes_clarification_qas_and_errors(tmp_path: Path) -> None:
    session_path = tmp_path / "session.jsonl"
    _write_minimal_session(session_path)

    session = parse_session(session_path)
    qmd = render_qmd(session)

    assert "**Clarification Q/A:**" in qmd
    assert "Q: What type of output are you envisioning for this project?" in qmd
    assert "A: Systematic review - Formal PRISMA-guided systematic review" in qmd
    assert "HTTP 429 Too Many Requests" in qmd
    assert "**Status:** Error" in qmd


def test_render_qmd_full_mode_does_not_truncate_tool_output() -> None:
    long_output = "x" * 2501
    message = ChatMessage(
        request_id="req-2",
        timestamp=datetime.now(UTC),
        user_text="run",
        response_text="done",
        tool_calls=[
            ToolCall(
                tool_id="run_in_terminal",
                invocation_message="Running cmd",
                past_tense_message="Ran cmd",
                result_input="echo hello",
                result_output=long_output,
                is_error=False,
            )
        ],
    )
    session = ChatSession(
        session_id="s2",
        title="Long output",
        creation_date=datetime.now(UTC),
        model_id="copilot/test-model",
        messages=[message],
    )

    qmd = render_qmd(session)

    assert "... (truncated)" not in qmd
    assert long_output in qmd


def test_render_qmd_summary_mode_hides_tool_io(tmp_path: Path) -> None:
    session_path = tmp_path / "session.jsonl"
    _write_minimal_session(session_path)

    session = parse_session(session_path)
    qmd = render_qmd(session, detail_level="summary")

    assert "Details: run_in_terminal" not in qmd
    assert "**Input:**" not in qmd
    assert "**Output:**" not in qmd


def _write_metadata_first_request_session(path: Path) -> None:
    """Session where the first request is embedded in kind-0 metadata and
    a retry confirmation ("Try Again") follows a failed attempt."""
    entries = [
        {
            "kind": 0,
            "v": {
                "version": 3,
                "sessionId": "session-meta",
                "modelId": "copilot/test-model",
                "creationDate": 1712400000000,
                "requests": [
                    {
                        "requestId": "req-0",
                        "timestamp": 1712400000000,
                        "modelId": "copilot/test-model",
                        "agent": {"name": "agent"},
                        "message": {"text": "What is the capital of France?"},
                        "response": [],
                    }
                ],
            },
        },
        # Failed attempt: response patch for request 0 (error path, no content)
        {"kind": 2, "k": ["requests", 0, "response"], "v": []},
        # Retry confirmation duplicating request 0
        {
            "kind": 2,
            "k": ["requests"],
            "v": [
                {
                    "requestId": "req-0-retry",
                    "timestamp": 1712400005000,
                    "confirmation": "Try Again",
                    "message": {"text": "@agent Try Again"},
                    "response": [],
                }
            ],
        },
        # Successful response arrives as a patch targeted at the retry index (1)
        {
            "kind": 2,
            "k": ["requests", 1, "response"],
            "v": [{"kind": "markdownContent", "value": "The capital is Paris."}],
        },
    ]

    with open(path, "w", encoding="utf-8") as fh:
        for entry in entries:
            fh.write(json.dumps(entry) + "\n")


def test_parse_session_reads_first_request_from_metadata(tmp_path: Path) -> None:
    session_path = tmp_path / "session.jsonl"
    _write_metadata_first_request_session(session_path)

    session = parse_session(session_path)

    # The retry must not create a duplicate turn
    assert len(session.messages) == 1
    # The original prompt from kind-0 metadata is preserved
    assert session.messages[0].user_text == "What is the capital of France?"
    # The response patched at the retry index is merged into the original turn
    assert session.messages[0].response_text == "The capital is Paris."


def test_render_qmd_includes_metadata_first_prompt(tmp_path: Path) -> None:
    session_path = tmp_path / "session.jsonl"
    _write_metadata_first_request_session(session_path)

    session = parse_session(session_path)
    qmd = render_qmd(session)

    assert "What is the capital of France?" in qmd
    assert "The capital is Paris." in qmd
    assert "Try Again" not in qmd
