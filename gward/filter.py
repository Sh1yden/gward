"""Filter Module."""

from .models import RepoStatus


def priority(s: RepoStatus) -> int:
    if s.error:
        return 0
    if s.is_dirty:
        return 1
    if (s.ahead or 0) or (s.behind or 0):
        return 2
    return 3


def sort_statuses(items: list[RepoStatus]) -> list[RepoStatus]:
    return sorted(items, key=lambda s: (priority(s), s.name.lower()))
