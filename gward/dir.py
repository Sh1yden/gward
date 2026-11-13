"""Module for file system control."""

from pathlib import Path


class Dir:
    def __init__(self) -> None:
        pass

    def is_repo(self, path: Path) -> bool:
        """Check if have .git path(and repo) in path."""
        return (path / ".git").is_dir()

    async def get_curr_dir(self) -> Path:
        return Path.cwd()
