"""Module for git control."""

import asyncio
import os
from pathlib import Path

from .models import RepoStatus

# Git must never prompt for input, and index locks should not block other tools
GIT_ENV = {**os.environ, "GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0"}

# Network operations are slower, so fetch gets a longer timeout
FETCH_TIMEOUT = 60


async def run_git(repo: Path, *args: str, timeout: float = 10) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        "git",
        "-C",
        str(repo),
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        stdin=asyncio.subprocess.DEVNULL,
        env=GIT_ENV,
    )
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout)
    except TimeoutError:
        # Kill the hung process so it does not linger in the background
        proc.kill()
        await proc.wait()
        raise
    return proc.returncode, out.decode(), err.decode()


def parse_status(repo: Path, text: str) -> RepoStatus:
    # Pure parser: takes raw `git status --porcelain=v2 --branch` output
    st = RepoStatus(path=repo, name=repo.name)
    for line in text.splitlines():
        if line.startswith("# branch.head "):
            st.branch = line.split(" ", 2)[2]
        elif line.startswith("# branch.ab "):
            _, _, a, b = line.split()
            st.ahead, st.behind = int(a[1:]), int(b[1:])
        elif line[:2] in ("1 ", "2 "):
            # Changed and renamed entries: first status char is index, second is worktree
            xy = line.split(" ", 2)[1]
            if xy[0] != ".":
                st.staged += 1
            if xy[1] != ".":
                st.modified += 1
        elif line.startswith("u "):
            # Unmerged (conflict) entries count as modified
            st.modified += 1
        elif line.startswith("? "):
            st.untracked += 1
    return st


async def get_status(repo: Path) -> RepoStatus:
    try:
        code, out, err = await run_git(repo, "status", "--porcelain=v2", "--branch")
    except TimeoutError:
        return RepoStatus(repo, repo.name, error="timeout")
    if code != 0:
        return RepoStatus(repo, repo.name, error=err.strip() or f"exit {code}")
    return parse_status(repo, out)


async def fetch_repo(repo: Path) -> RepoStatus:
    # Fetch from remotes, then re-read status so the Sync column is up to date
    try:
        code, _, err = await run_git(repo, "fetch", "--prune", timeout=FETCH_TIMEOUT)
    except TimeoutError:
        return RepoStatus(repo, repo.name, error="fetch timeout")
    if code != 0:
        return RepoStatus(repo, repo.name, error=err.strip() or f"fetch exit {code}")
    return await get_status(repo)
