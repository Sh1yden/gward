from pathlib import Path

from gward.models import RepoStatus
from gward.output import render


def make(name, **kw):
    return RepoStatus(path=Path(name), name=name, **kw)


def test_empty_returns_empty_string():
    assert render([], 0.01) == ""


def test_clean_row_contains_clean_and_zero_counts():
    out = render([make("repo", branch="main", ahead=0, behind=0)], 0.01)
    assert "clean" in out
    assert "S0 M0 U0" in out
    assert "↑0 ↓0" in out


def test_dirty_row_shows_counts():
    out = render([make("repo", branch="main", modified=3, untracked=1)], 0.01)
    assert "dirty" in out
    assert "M3" in out and "U1" in out


def test_error_row_shows_error_text():
    out = render([make("repo", error="timeout")], 0.01)
    assert "ERROR" in out
    assert "timeout" in out


def test_no_upstream_shows_dash_for_sync():
    out = render([make("repo", branch="feature", ahead=None, behind=None)], 0.01)
    assert "  -" in out or out.rstrip().endswith("-") or " - " in out


def test_column_widths_align_by_longest_name():
    items = [make("a", branch="main"), make("longname", branch="main")]
    lines = render(items, 0.0).splitlines()
    # первая колонка выровнена: имя дополнено до ширины самого длинного
    assert lines[0].index("main") == lines[1].index("main")


def test_footer_contains_elapsed_time():
    out = render([make("repo", branch="main")], 0.1234)
    assert "0.12 с" in out
