from pathlib import Path

from gward.filter import priority, sort_statuses
from gward.models import RepoStatus


def make(name, **kw):
    return RepoStatus(path=Path(name), name=name, **kw)


def test_priority_order():
    error = make("e", error="boom")
    dirty = make("d", modified=1)
    unsynced = make("u", ahead=1, behind=0)
    clean = make("c", ahead=0, behind=0)
    assert priority(error) < priority(dirty) < priority(unsynced) < priority(clean)


def test_no_upstream_is_not_unsynced():
    # ahead/behind = None не должны считаться расхождением
    assert priority(make("x", ahead=None, behind=None)) == 3


def test_sort_puts_problems_first_then_alphabetical():
    items = [
        make("zeta"),
        make("Alpha", modified=1),
        make("beta", error="fail"),
        make("gamma", behind=2),
        make("Beta"),
    ]
    names = [s.name for s in sort_statuses(items)]
    assert names == ["beta", "Alpha", "gamma", "Beta", "zeta"]


def test_sort_empty_list():
    assert sort_statuses([]) == []
