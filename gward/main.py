"""Main run gward."""

import asyncio
import time
from collections.abc import Awaitable, Callable
from pathlib import Path

import typer

from .dir import find_repos
from .filter import only_attention, sort_statuses
from .git import fetch_repo, get_status
from .models import RepoStatus
from .output import print_report

# Maximum number of concurrent git processes
MAX_PARALLEL = 8

app = typer.Typer(
    add_completion=False,
    invoke_without_command=True,
    help="Show the status of local Git repositories in a folder.",
)


async def collect(
    repos: list[Path],
    worker: Callable[[Path], Awaitable[RepoStatus]],
    limit: int = MAX_PARALLEL,
) -> list[RepoStatus]:
    # Semaphore caps how many git processes run at the same time
    sem = asyncio.Semaphore(limit)

    async def bounded(repo: Path) -> RepoStatus:
        async with sem:
            return await worker(repo)

    return await asyncio.gather(*(bounded(repo) for repo in repos))


async def gather_statuses(
    root: Path,
    worker: Callable[[Path], Awaitable[RepoStatus]] = get_status,
    dirty_only: bool = False,
) -> list[RepoStatus]:
    # Find repositories under root, run the worker on each, then sort
    statuses = sort_statuses(await collect(find_repos(root), worker))
    return only_attention(statuses) if dirty_only else statuses


def _report(
    directory: Path,
    debug: bool,
    dirty: bool,
    worker: Callable[[Path], Awaitable[RepoStatus]],
) -> None:
    # Shared pipeline for the default command and for fetch
    start = time.perf_counter()
    statuses = asyncio.run(
        gather_statuses(directory.resolve(), worker=worker, dirty_only=dirty)
    )
    elapsed = time.perf_counter() - start if debug else None
    print_report(statuses, elapsed)


@app.callback()
def default(
    ctx: typer.Context,
    directory: Path = typer.Option(
        Path("."), "--dir", "-C", help="Folder containing repositories"
    ),
    debug: bool = typer.Option(False, "--debug", help="Show elapsed time"),
    dirty: bool = typer.Option(
        False, "--dirty", "-d", help="Show only repositories that need attention"
    ),
) -> None:
    # Plain `gward` runs a quick local status check; subcommands take over otherwise
    if ctx.invoked_subcommand is None:
        _report(directory, debug, dirty, get_status)


@app.command()
def fetch(
    directory: Path = typer.Option(
        Path("."), "--dir", "-C", help="Folder containing repositories"
    ),
    debug: bool = typer.Option(False, "--debug", help="Show elapsed time"),
    dirty: bool = typer.Option(
        False, "--dirty", "-d", help="Show only repositories that need attention"
    ),
) -> None:
    # Network operation: fetch each repository, then read its fresh status
    _report(directory, debug, dirty, fetch_repo)


def main() -> None:
    app()
