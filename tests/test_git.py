import asyncio
import subprocess
from pathlib import Path

import pytest

from gward import git
from gward.git import get_status, parse_status

# ---------- Фикстуры: реальный формат `git status --porcelain=v2 --branch` ----------

CLEAN = """\
# branch.oid 1a2b3c4d5e6f
# branch.head main
# branch.upstream origin/main
# branch.ab +0 -0
"""

MIXED = """\
# branch.oid 1a2b3c4d5e6f
# branch.head main
# branch.upstream origin/main
# branch.ab +1 -2
1 M. N... 100644 100644 100644 aaa aaa src/a.py
1 .M N... 100644 100644 100644 aaa aaa src/b.py
1 MM N... 100644 100644 100644 aaa aaa src/c.py
2 R. N... 100644 100644 100644 aaa aaa R100 new.py\told.py
? notes.txt
? tmp/
"""

DETACHED = """\
# branch.oid 1a2b3c4d5e6f
# branch.head (detached)
"""

NO_UPSTREAM = """\
# branch.oid 1a2b3c4d5e6f
# branch.head feature
"""

CONFLICT = """\
# branch.oid 1a2b3c4d5e6f
# branch.head main
# branch.upstream origin/main
# branch.ab +0 -0
u UU N... 100644 100644 100644 100644 aaa bbb ccc file.py
"""

AHEAD_ONLY = """\
# branch.oid 1a2b3c4d5e6f
# branch.head main
# branch.upstream origin/main
# branch.ab +3 -0
"""


# ---------- parse_status: чистая функция, без git ----------


def test_parse_clean():
    st = parse_status(Path("/p/repo"), CLEAN)
    assert st.name == "repo"
    assert st.branch == "main"
    assert (st.ahead, st.behind) == (0, 0)
    assert (st.staged, st.modified, st.untracked) == (0, 0, 0)
    assert not st.is_dirty


def test_parse_mixed_counts():
    st = parse_status(Path("/p/repo"), MIXED)
    assert (st.ahead, st.behind) == (1, 2)
    # staged: M., MM, R.  -> 3
    assert st.staged == 3
    # modified: .M, MM -> 2
    assert st.modified == 2
    # untracked: notes.txt, tmp/ -> 2
    assert st.untracked == 2
    assert st.is_dirty


def test_parse_rename_counts_as_staged_not_untracked():
    text = (
        "# branch.head main\n"
        "2 R. N... 100644 100644 100644 aaa aaa R100 new.py\told.py\n"
    )
    st = parse_status(Path("/p/repo"), text)
    assert st.staged == 1
    assert st.untracked == 0


def test_parse_detached_head():
    st = parse_status(Path("/p/repo"), DETACHED)
    assert st.branch == "(detached)"
    assert st.ahead is None and st.behind is None


def test_parse_no_upstream_keeps_ahead_behind_none():
    st = parse_status(Path("/p/repo"), NO_UPSTREAM)
    assert st.branch == "feature"
    assert st.ahead is None and st.behind is None


def test_parse_conflict_counts_as_modified():
    st = parse_status(Path("/p/repo"), CONFLICT)
    assert st.modified == 1
    assert st.is_dirty


def test_parse_ahead_only():
    st = parse_status(Path("/p/repo"), AHEAD_ONLY)
    assert (st.ahead, st.behind) == (3, 0)


def test_parse_empty_output():
    st = parse_status(Path("/p/repo"), "")
    assert st.branch is None
    assert not st.is_dirty


# ---------- get_status: ошибки и таймаут через подмену run_git ----------


def test_get_status_timeout(monkeypatch, tmp_path):
    async def fake_run_git(*args, **kwargs):
        raise TimeoutError

    monkeypatch.setattr(git, "run_git", fake_run_git)
    st = asyncio.run(get_status(tmp_path))
    assert st.error == "timeout"


def test_get_status_nonzero_exit(monkeypatch, tmp_path):
    async def fake_run_git(*args, **kwargs):
        return 128, "", "fatal: not a git repository\n"

    monkeypatch.setattr(git, "run_git", fake_run_git)
    st = asyncio.run(get_status(tmp_path))
    assert st.error == "fatal: not a git repository"


# ---------- Интеграционные тесты на настоящих репозиториях ----------

GIT_ENV = {
    "GIT_AUTHOR_NAME": "test",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "test",
    "GIT_COMMITTER_EMAIL": "test@example.com",
    "GIT_CONFIG_GLOBAL": "/dev/null",
}


def run(cwd: Path, *args: str) -> None:
    import os

    env = {**os.environ, **GIT_ENV}
    subprocess.run(["git", *args], cwd=cwd, check=True, env=env, capture_output=True)


def make_repo(path: Path) -> Path:
    path.mkdir(parents=True)
    run(path, "init", "-q", "-b", "main")
    (path / "file.txt").write_text("hello\n")
    run(path, "add", ".")
    run(path, "commit", "-q", "-m", "init")
    return path


@pytest.fixture
def repo(tmp_path):
    return make_repo(tmp_path / "repo")


@pytest.fixture
def remote_pair(tmp_path):
    """Возвращает (локальный репозиторий, путь к bare-remote), уже с upstream."""
    remote = tmp_path / "remote.git"
    run(tmp_path, "init", "-q", "--bare", "-b", "main", str(remote))
    local = make_repo(tmp_path / "local")
    run(local, "remote", "add", "origin", str(remote))
    run(local, "push", "-q", "-u", "origin", "main")
    return local, remote


def test_real_clean_repo(repo):
    st = asyncio.run(get_status(repo))
    assert st.error is None
    assert st.branch == "main"
    assert not st.is_dirty


def test_real_untracked_and_modified(repo):
    (repo / "file.txt").write_text("changed\n")
    (repo / "new.txt").write_text("new\n")
    st = asyncio.run(get_status(repo))
    assert st.modified == 1
    assert st.untracked == 1
    assert st.staged == 0


def test_real_staged(repo):
    (repo / "file.txt").write_text("changed\n")
    run(repo, "add", "file.txt")
    st = asyncio.run(get_status(repo))
    assert st.staged == 1
    assert st.modified == 0


def test_real_ahead(remote_pair):
    local, _ = remote_pair
    (local / "file.txt").write_text("v2\n")
    run(local, "commit", "-q", "-am", "second")
    st = asyncio.run(get_status(local))
    assert (st.ahead, st.behind) == (1, 0)


def test_real_behind_needs_fetch(remote_pair, tmp_path):
    local, remote = remote_pair
    # Второй клон пушит коммит в remote
    other = tmp_path / "other"
    run(tmp_path, "clone", "-q", str(remote), str(other))
    (other / "file.txt").write_text("from other\n")
    run(other, "commit", "-q", "-am", "remote change")
    run(other, "push", "-q")

    # Без fetch локальная картина не знает о новом коммите
    st = asyncio.run(get_status(local))
    assert st.behind == 0

    # После fetch видим отставание
    run(local, "fetch", "-q")
    st = asyncio.run(get_status(local))
    assert st.behind == 1


def test_real_no_upstream(repo):
    run(repo, "checkout", "-q", "-b", "feature")
    st = asyncio.run(get_status(repo))
    assert st.branch == "feature"
    assert st.ahead is None and st.behind is None
