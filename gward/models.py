"""Data Model Class."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class RepoStatus:
    path: Path
    name: str
    branch: str | None = None
    ahead: int | None = None
    behind: int | None = None
    staged: int = 0
    modified: int = 0
    untracked: int = 0
    error: str | None = None

    @property
    def is_dirty(self) -> bool:
        return bool(self.staged or self.modified or self.untracked)
