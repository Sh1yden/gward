"""Main run gward."""

import asyncio
import time
from pathlib import Path

import typer

from .dir import find_repos
from .filter import sort_statuses
from .git import get_status
from .models import RepoStatus
from .output import print_report

# Maximum number of concurrent git processes
MAX_PARALLEL = 8

app = typer.Typer(
    add_completion=False,
    help="Show the status of local Git repositories in a folder.",
)


async def collect(repos: list[Path], limit: int = MAX_PARALLEL) -> list[RepoStatus]:
    # Semaphore caps how many git processes run at the same time
    sem = asyncio.Semaphore(limit)

    async def bounded(repo: Path) -> RepoStatus:
        async with sem:
            return await get_status(repo)

    return await asyncio.gather(*(bounded(repo) for repo in repos))


async def gather_statuses(root: Path) -> list[RepoStatus]:
    # Find repositories under root, query them concurrently, then sort
    return sort_statuses(await collect(find_repos(root)))


@app.command()
def run(
    path: Path = typer.Argument(Path("."), help="Folder containing repositories"),
    debug: bool = typer.Option(False, "--debug", help="Show elapsed time"),
) -> None:
    start = time.perf_counter()
    statuses = asyncio.run(gather_statuses(path.resolve()))
    elapsed = time.perf_counter() - start if debug else None
    print_report(statuses, elapsed)


def main() -> None:
    app()
