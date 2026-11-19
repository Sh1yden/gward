from pathlib import Path

from gward.dir import find_repos


def make_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
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


def test_depth_one_does_not_scan_grandchildren(tmp_path):
    make_repo(tmp_path / "group" / "nested")
    assert find_repos(tmp_path) == []


def test_depth_two_finds_nested_repositories(tmp_path):
    direct = make_repo(tmp_path / "direct")
    nested = make_repo(tmp_path / "group" / "nested")
    assert find_repos(tmp_path, depth=2) == [direct, nested]


def test_repository_root_is_not_searched_further(tmp_path):
    make_repo(tmp_path)
    make_repo(tmp_path / "nested")
    assert find_repos(tmp_path, depth=5) == [tmp_path]


def test_hidden_folders_are_skipped_at_any_depth(tmp_path):
    make_repo(tmp_path / "group" / ".hidden")
    visible = make_repo(tmp_path / "group" / "visible")
    assert find_repos(tmp_path, depth=2) == [visible]


def test_symlinks_are_not_followed(tmp_path):
    repo = make_repo(tmp_path / "real")
    (tmp_path / "loop").symlink_to(tmp_path, target_is_directory=True)
    assert find_repos(tmp_path, depth=5) == [repo]
