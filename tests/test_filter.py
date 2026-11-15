from pathlib import Path

from gward.filter import only_attention, priority, sort_statuses
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
    # ahead/behind = None must not count as a divergence
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


def test_only_attention_hides_clean_repos():
    items = [
        make("clean", ahead=0, behind=0),
        make("dirty", modified=1),
        make("unsynced", behind=2),
        make("broken", error="boom"),
        make("no-upstream", ahead=None, behind=None),
    ]
    names = {s.name for s in only_attention(items)}
    assert names == {"dirty", "unsynced", "broken"}


def test_only_attention_all_clean_returns_empty():
    items = [make("a", ahead=0, behind=0), make("b", ahead=0, behind=0)]
    assert only_attention(items) == []
