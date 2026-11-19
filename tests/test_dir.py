from pathlib import Path

from gward.dir import find_repos


def make_repo(path: Path) -> Path:
    path.mkdir(exist_ok=True)
    (path / ".git").mkdir()
    return path


def test_root_itself_is_repo(tmp_path):
    make_repo(tmp_path)
    assert find_repos(tmp_path) == [tmp_path]


def test_direct_subfolders_are_found(tmp_path):
    make_repo(tmp_path / "first")
    make_repo(tmp_path / "second")
    assert find_repos(tmp_path) == [tmp_path / "first", tmp_path / "second"]


def test_hidden_and_plain_folders_are_skipped(tmp_path):
    make_repo(tmp_path / "visible")
    make_repo(tmp_path / ".hidden")
    (tmp_path / "plain").mkdir()
    assert find_repos(tmp_path) == [tmp_path / "visible"]


def test_git_file_marks_worktree(tmp_path):
    # Worktrees and submodules have .git as a regular file
    repo = tmp_path / "worktree"
    repo.mkdir()
    (repo / ".git").write_text("gitdir: /somewhere\n")
    assert find_repos(tmp_path) == [repo]
