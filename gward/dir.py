"""Module for file system control."""

from pathlib import Path


def find_repos(root: Path, depth: int = 1) -> list[Path]:
    """Return Git repositories in root and its subfolders up to depth.

    A folder counts as a repository when it contains a .git entry,
    which may be a directory or a file (worktree, submodule).
    Repository folders are not searched further. Hidden folders
    and symlinks are ignored.
    """

    repos: list[Path] = []

    def walk(path: Path, level: int) -> None:
        if (path / ".git").exists():
            repos.append(path)
            return
        if level >= depth:
            return
        try:
            children = sorted(path.iterdir())
        except OSError:
            return
        for child in children:
            if child.name.startswith(".") or child.is_symlink():
                continue
            if child.is_dir():
                walk(child, level + 1)

    walk(root, 0)
    return repos
