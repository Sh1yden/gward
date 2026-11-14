"""Main run gward."""

import asyncio
import time
from pathlib import Path
from .dir import find_repos
from .git import get_status
from .filter import sort_statuses
from .output import render

MAX_PARALLEL = 8


async def collect(repos: list[Path]):
    sem = asyncio.Semaphore(MAX_PARALLEL)

    async def bounded(repo: Path):
        async with sem:
            return await get_status(repo)

    return await asyncio.gather(*(bounded(r) for r in repos))


async def async_main(root: Path) -> None:
    t0 = time.perf_counter()
    repos = find_repos(root)
    if not repos:
        print("Git-репозиториев не найдено")
        return
    statuses = sort_statuses(await collect(repos))
    print(render(statuses, time.perf_counter() - t0))


def main() -> None:
    asyncio.run(async_main(Path.cwd()))
