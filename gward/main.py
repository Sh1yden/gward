"""Main run gward."""

import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path

import typer

from .dir import find_repos
from .filter import only_attention, sort_statuses
from .git import fetch_repo, get_status
from .models import RepoStatus
from .output import print_json, print_report

# Maximum number of concurrent git processes
MAX_PARALLEL = 8


@dataclass(frozen=True)
class Options:
    """Options shared by the default command and subcommands."""

    directory: Path
    debug: bool
    dirty: bool
    depth: int
    json_output: bool
    exit_code: bool


app = typer.Typer(
    add_completion=True,
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
            try:
                return await worker(repo)
            except Exception as exc:
                # One broken repository must not abort the whole report
                message = str(exc).strip() or type(exc).__name__
                return RepoStatus(path=repo, name=repo.name, error=message)

    return await asyncio.gather(*(bounded(repo) for repo in repos))


async def gather_statuses(
    root: Path,
    worker: Callable[[Path], Awaitable[RepoStatus]] = get_status,
    depth: int = 1,
) -> list[RepoStatus]:
    # Find repositories under root, run the worker on each, then sort
    return sort_statuses(await collect(find_repos(root, depth), worker))


def compute_exit_code(statuses: list[RepoStatus]) -> int:
    # Errors are more severe than local changes or unsynced commits
    if any(s.error for s in statuses):
        return 2
    if any(s.is_dirty or s.ahead or s.behind for s in statuses):
        return 1
    return 0


def _report(
    options: Options,
    worker: Callable[[Path], Awaitable[RepoStatus]],
) -> list[RepoStatus]:
    # Shared pipeline for the default command and for fetch
    start = time.perf_counter()
    try:
        statuses = asyncio.run(
            gather_statuses(
                options.directory.resolve(),
                worker=worker,
                depth=options.depth,
            )
        )
    except OSError as exc:
        # Unreadable folders should not produce a traceback
        raise typer.BadParameter(str(exc), param_hint="--dir") from exc
    visible = only_attention(statuses) if options.dirty else statuses
    if statuses and not visible:
        empty_message = "All repositories are clean"
    else:
        empty_message = "No Git repositories found"
    elapsed = time.perf_counter() - start if options.debug else None
    if options.json_output:
        print_json(visible)
        if elapsed is not None:
            typer.echo(f"Checked in {elapsed:.2f} s", err=True)
    else:
        print_report(visible, elapsed, empty_message=empty_message)
    return statuses


def _run(
    options: Options,
    worker: Callable[[Path], Awaitable[RepoStatus]],
) -> None:
    statuses = _report(options, worker)
    if options.exit_code:
        raise typer.Exit(code=compute_exit_code(statuses))


@app.callback()
def default(
    ctx: typer.Context,
    directory: Path = typer.Option(
        Path("."),
        "--dir",
        "-C",
        help="Folder containing repositories",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    debug: bool = typer.Option(False, "--debug", help="Show elapsed time"),
    dirty: bool = typer.Option(
        False,
        "--dirty",
        "-d",
        help="Show only repositories that need attention",
    ),
    depth: int = typer.Option(
        1,
        "--depth",
        min=1,
        help="Search depth for nested folders",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Print statuses as JSON",
    ),
    exit_code: bool = typer.Option(
        False,
        "--exit-code",
        help="Exit with 1 if repositories need attention, 2 on errors",
    ),
) -> None:
    # Global options are resolved once and shared with subcommands through
    # the Click context, so `gward -C PATH fetch` works as expected.
    options = Options(
        directory=directory,
        debug=debug,
        dirty=dirty,
        depth=depth,
        json_output=json_output,
        exit_code=exit_code,
    )
    ctx.obj = options
    # Plain `gward` runs a quick local status check
    if ctx.invoked_subcommand is None:
        _run(options, get_status)


@app.command()
def fetch(ctx: typer.Context) -> None:
    """Fetch remotes, then show the status."""

    # Network operation: fetch each repository, then read its fresh status
    options: Options = ctx.obj
    _run(options, fetch_repo)


def main() -> None:
    app()
