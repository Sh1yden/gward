"""Output Module."""

from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text

from .models import RepoStatus


def sync_cell(s: RepoStatus) -> str:
    # No upstream configured: ahead/behind are unknown
    if s.ahead is None or s.behind is None:
        return "—"
    return f"↑{s.ahead} ↓{s.behind}"


def sync_style(s: RepoStatus) -> str:
    if s.ahead is None or s.behind is None:
        return "dim"
    if s.behind:
        return "red"  # remote has commits we don't have
    if s.ahead:
        return "green"  # local commits not pushed yet
    return "dim"


def _count(n: int, style: str) -> Text:
    # Zero counts are dimmed so non-zero values stand out
    return Text(str(n), style=style if n else "dim")


def build_table(items: list[RepoStatus]) -> Table:
    table = Table(
        box=box.ROUNDED, header_style="bold cyan", title="gward", title_style="bold"
    )
    table.add_column("Repository", style="bold")
    table.add_column("Branch", style="magenta")
    table.add_column("Status")
    table.add_column("Staged", justify="right")
    table.add_column("Modified", justify="right")
    table.add_column("Untracked", justify="right")
    table.add_column("Sync")

    for s in items:
        if s.error:
            table.add_row(
                s.name,
                s.branch or "-",
                Text("error", style="bold red"),
                "",
                "",
                "",
                Text(s.error, style="red"),
            )
            continue

        state = (
            Text("dirty", style="yellow")
            if s.is_dirty
            else Text("clean", style="green")
        )
        table.add_row(
            s.name,
            s.branch or "-",
            state,
            _count(s.staged, "green"),
            _count(s.modified, "yellow"),
            _count(s.untracked, "red"),
            Text(sync_cell(s), style=sync_style(s)),
        )
    return table


def print_report(
    items: list[RepoStatus],
    elapsed: float | None = None,
    console: Console | None = None,
) -> None:
    console = console or Console()
    if not items:
        console.print("No Git repositories found")
        return
    console.print(build_table(items))
    if elapsed is not None:
        console.print(f"[dim]Checked in {elapsed:.2f} s[/dim]")
