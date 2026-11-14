"""Main run gward."""

import asyncio
import time
from pathlib import Path

import typer

from .dir import find_repos
from .filter import sort_statuses
from .git import get_status
from .output import print_report

MAX_PARALLEL = 8

app = typer.Typer(
    add_completion=False,
    help="Статус локальных Git-репозиториев в текущей папке.",
)


async def collect(repos: list[Path]):
    sem = asyncio.Semaphore(MAX_PARALLEL)

    async def bounded(repo: Path):
        async with sem:
            return await get_status(repo)

    return await asyncio.gather(*(bounded(r) for r in repos))


async def async_main(root: Path, debug: bool) -> None:
    t0 = time.perf_counter()
    repos = find_repos(root)
    statuses = sort_statuses(await collect(repos))
    elapsed = time.perf_counter() - t0 if debug else None
    print_report(statuses, elapsed)


@app.command()
def run(
    debug: bool = typer.Option(False, "--debug", help="Показать время выполнения"),
) -> None:
    asyncio.run(async_main(Path.cwd(), debug))


def main() -> None:
    app()
