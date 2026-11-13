"""Module for git control."""

import asyncio
from pathlib import Path


class Git:
    """..."""

    def __init__(self) -> None:
        pass

    async def univ_git(self, path: Path, *args) -> str | RuntimeError:
        """Universal git func, for any git command in *args."""

        process = await asyncio.create_subprocess_exec(
            "git",
            *args,
            cwd=path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            return stdout.decode().strip()
        else:
            raise RuntimeError(f"Git error: {stderr.decode().strip()}")

    async def git_status(self, path: Path) -> str | RuntimeError:
        """Get one git status."""
        return await self.univ_git("status", "--porcelain=v2", "--branch", path=path)

    async def is_deep_repo(self, path: Path) -> bool:
        return False

    async def get_raw_dir_status(self):
        pass
