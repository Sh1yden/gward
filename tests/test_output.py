import io
import json
from pathlib import Path

from rich.console import Console

from gward.models import RepoStatus
from gward.output import (
    error_details,
    format_error,
    print_json,
    print_report,
    repo_payload,
    sync_cell,
    sync_style,
)


def make(name, **kw):
    return RepoStatus(path=Path(name), name=name, **kw)


def render(items, elapsed=None) -> str:
    buf = io.StringIO()
    console = Console(file=buf, width=120, color_system=None)
    print_report(items, elapsed, console=console)
    return buf.getvalue()


# ---------- sync_cell: exact values ----------


def test_sync_cell_zero_zero():
    assert sync_cell(make("r", ahead=0, behind=0)) == "↑0 ↓0"


def test_sync_cell_values():
    assert sync_cell(make("r", ahead=2, behind=3)) == "↑2 ↓3"


def test_sync_cell_no_upstream_is_dash():
    assert sync_cell(make("r", ahead=None, behind=None)) == "—"


def test_sync_style_marks_directions():
    assert sync_style(make("r", ahead=None, behind=None)) == "dim"
    assert sync_style(make("r", ahead=0, behind=2)) == "red"
    assert sync_style(make("r", ahead=1, behind=0)) == "green"
    assert sync_style(make("r", ahead=0, behind=0)) == "dim"


# ---------- error text compaction ----------


def test_format_error_keeps_first_line():
    assert format_error("fatal: first\nsecond line") == "fatal: first"


def test_format_error_truncates_long_line():
    text = "fatal: " + "x" * 60
    result = format_error(text, limit=20)
    assert len(result) == 20
    assert result.endswith("…")


def test_error_details_only_when_cell_is_shortened():
    short = [make("r", error="timeout")]
    assert error_details(short) == []
    long = [make("r", error="x" * 50)]
    assert error_details(long) == [("r", "x" * 50)]


# ---------- render: what actually ends up in the output ----------


def test_empty_list_prints_message():
    assert "No Git repositories found" in render([])


def test_empty_list_prints_custom_message():
    buf = io.StringIO()
    console = Console(file=buf, width=120, color_system=None)
    print_report([], console=console, empty_message="All clean")
    assert "All clean" in buf.getvalue()


def test_clean_row():
    out = render([make("repo", branch="main", ahead=0, behind=0)])
    assert "clean" in out
    assert "↑0 ↓0" in out


def test_dirty_row():
    out = render([make("repo", branch="main", modified=3, untracked=1)])
    assert "dirty" in out


def test_error_row_shows_error_text():
    out = render([make("repo", error="timeout")])
    assert "error" in out
    assert "timeout" in out
    assert "Errors:" not in out


def test_multiline_error_is_compacted_and_printed_in_full():
    error = "fatal: unable to access remote\nhint: check the URL"
    out = render([make("repo", error=error)])
    assert "fatal: unable to access" in out
    assert "hint: check the URL" in out
    assert "Errors:" in out


def test_no_upstream_row_shows_dash():
    out = render([make("repo", branch="feature", ahead=None, behind=None)])
    assert "—" in out


def test_footer_shown_when_elapsed_given():
    out = render([make("repo", branch="main")], elapsed=0.1234)
    assert "Checked in 0.12 s" in out


def test_footer_hidden_without_elapsed():
    out = render([make("repo", branch="main")], elapsed=None)
    assert "Checked in" not in out


# ---------- JSON payload ----------


def test_repo_payload_clean():
    payload = repo_payload(make("repo", branch="main", ahead=0, behind=0))
    assert payload["status"] == "clean"
    assert payload["branch"] == "main"
    assert payload["error"] is None


def test_repo_payload_dirty():
    payload = repo_payload(make("repo", modified=2))
    assert payload["status"] == "dirty"
    assert payload["modified"] == 2


def test_repo_payload_error():
    payload = repo_payload(make("repo", error="boom"))
    assert payload["status"] == "error"
    assert payload["error"] == "boom"


def test_repo_payload_no_upstream_is_null():
    payload = repo_payload(make("repo"))
    assert payload["ahead"] is None
    assert payload["behind"] is None


def test_print_json_writes_valid_json(capsys):
    print_json([make("repo", branch="main")])
    data = json.loads(capsys.readouterr().out)
    assert data[0]["name"] == "repo"
    assert data[0]["status"] == "clean"
