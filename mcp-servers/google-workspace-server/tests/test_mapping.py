import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from google_workspace_server import server


def test_insert_line_anchors_and_extract_reference() -> None:
    content = "alpha\nbeta\n\n"
    anchored, mapping = server._insert_line_anchors(content)

    assert mapping["line_count"] == 3
    assert len(mapping["anchors"]) == 3
    assert "[[RWA-LINE:000001:" in anchored

    token = mapping["anchors"][1]["token"]
    line_number, hash_value = server._extract_anchor_reference(token)

    assert line_number == 2
    assert hash_value == mapping["anchors"][1]["hash"]


def test_best_line_match_prefers_nearest_line() -> None:
    lines = [
        "Systematic reviews are time intensive.",
        "The workflow uses explicit human checkpoints.",
        "Results are exported to Quarto.",
    ]
    snippet = "workflow uses explicit human checkpoints"

    line_number, score = server._best_line_match(lines, snippet)

    assert line_number == 2
    assert score > 0.7


def test_extract_code_from_redirect_url() -> None:
    redirect = "http://localhost:8765/?code=abc123&scope=drive"

    assert server._extract_code(redirect) == "abc123"
