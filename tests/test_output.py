import io
from pathlib import Path

from rich.console import Console

from gward.models import RepoStatus
from gward.output import print_report, sync_cell


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


# ---------- render: what actually ends up in the output ----------


def test_empty_list_prints_message():
    assert "No Git repositories found" in render([])


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


def test_no_upstream_row_shows_dash():
    out = render([make("repo", branch="feature", ahead=None, behind=None)])
    assert "—" in out


def test_footer_shown_when_elapsed_given():
    out = render([make("repo", branch="main")], elapsed=0.1234)
    assert "Checked in 0.12 s" in out


def test_footer_hidden_without_elapsed():
    out = render([make("repo", branch="main")], elapsed=None)
    assert "Checked in" not in out
