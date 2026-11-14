"""Module for file system control."""

from pathlib import Path


def find_repos(root: Path) -> list[Path]:
    """..."""

    if (root / ".git").exists():
        return [root]

    return [
        child
        for child in sorted(root.iterdir())
        if child.is_dir()
        and not child.name.startswith(".")
        and (child / ".git").exists()
    ]
