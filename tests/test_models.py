from pathlib import Path

from gward.models import RepoStatus


def test_clean_repo_is_not_dirty():
    assert not RepoStatus(path=Path("x"), name="x").is_dirty


def test_staged_makes_dirty():
    assert RepoStatus(path=Path("x"), name="x", staged=1).is_dirty


def test_modified_makes_dirty():
    assert RepoStatus(path=Path("x"), name="x", modified=1).is_dirty


def test_untracked_makes_dirty():
    assert RepoStatus(path=Path("x"), name="x", untracked=1).is_dirty
