"""Module for file system control."""

from pathlib import Path


def find_repos(root: Path) -> list[Path]:
    """Return Git repositories in root and its direct subfolders.

    A folder counts as a repository when it contains a .git entry,
    which may be a directory or a file (worktree, submodule).
    Hidden subfolders are ignored.
    """

    if (root / ".git").exists():
        return [root]

    return [
        child
        for child in sorted(root.iterdir())
        if child.is_dir()
        and not child.name.startswith(".")
        and (child / ".git").exists()
    ]
