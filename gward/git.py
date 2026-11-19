"""Module for git control."""

import asyncio
import os
import signal
from pathlib import Path

from .models import RepoStatus

# Network operations are slower, so fetch gets a longer timeout
FETCH_TIMEOUT = 60

# Git must not inherit the repository context of the calling process,
# otherwise `-C repo` may silently inspect a different repository.
_GIT_CONTEXT_VARS = frozenset(
    {
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_COMMON_DIR",
        "GIT_NAMESPACE",
        "GIT_PREFIX",
    }
)


def _git_env() -> dict[str, str]:
    # Git must never prompt for input, and index locks should not block
    # other tools.
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in _GIT_CONTEXT_VARS
    }
    env["GIT_OPTIONAL_LOCKS"] = "0"
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def _kill_group(proc: asyncio.subprocess.Process) -> None:
    # Kill the whole process group so ssh and helpers do not linger
    if os.name == "posix":
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    else:
        proc.kill()


async def _terminate(proc: asyncio.subprocess.Process) -> None:
    _kill_group(proc)
    await proc.wait()


async def run_git(
    repo: Path, *args: str, timeout: float = 10
) -> tuple[int, str, str]:
    posix = os.name == "posix"
    proc = await asyncio.create_subprocess_exec(
        "git",
        "-C",
        str(repo),
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        stdin=asyncio.subprocess.DEVNULL,
        env=_git_env(),
        start_new_session=posix,
    )
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout)
    except TimeoutError:
        await _terminate(proc)
        raise
    except asyncio.CancelledError:
        # Ctrl-C must not leave background network operations running
        await _terminate(proc)
        raise
    # communicate() reaps the process, so the exit code is always set here
    returncode = proc.returncode
    assert returncode is not None
    return (
        returncode,
        out.decode(errors="replace"),
        err.decode(errors="replace"),
    )


def _spawn_error(repo: Path, exc: OSError) -> RepoStatus:
    # Map failures to start git itself to an error row instead of a crash
    if isinstance(exc, FileNotFoundError):
        message = "git not found"
    else:
        message = str(exc).strip() or type(exc).__name__
    return RepoStatus(path=repo, name=repo.name, error=message)


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
            # First status char is the index, second is the worktree
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
        code, out, err = await run_git(
            repo, "status", "--porcelain=v2", "--branch"
        )
    except TimeoutError:
        return RepoStatus(repo, repo.name, error="timeout")
    except OSError as exc:
        return _spawn_error(repo, exc)
    if code != 0:
        return RepoStatus(repo, repo.name, error=err.strip() or f"exit {code}")
    return parse_status(repo, out)


async def fetch_repo(repo: Path) -> RepoStatus:
    # Fetch from remotes, then re-read status so the Sync column is up to date
    try:
        code, _, err = await run_git(
            repo, "fetch", "--prune", timeout=FETCH_TIMEOUT
        )
    except TimeoutError:
        return RepoStatus(repo, repo.name, error="fetch timeout")
    except OSError as exc:
        return _spawn_error(repo, exc)
    if code != 0:
        return RepoStatus(
            repo, repo.name, error=err.strip() or f"fetch exit {code}"
        )
    return await get_status(repo)
