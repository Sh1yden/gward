"""Output Module."""

from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text

from .models import RepoStatus

# Error text in the table is kept on one line; the full message is
# printed below the table when it does not fit the cell.
ERROR_LIMIT = 30


def _first_line(message: str) -> str:
    for line in message.splitlines():
        if line.strip():
            return line.strip()
    return ""


def format_error(message: str, limit: int = ERROR_LIMIT) -> str:
    # Compact one-line representation of a possibly multi-line git error
    line = _first_line(message)
    if len(line) > limit:
        return line[: limit - 1].rstrip() + "…"
    return line


def error_details(
    items: list[RepoStatus], limit: int = ERROR_LIMIT
) -> list[tuple[str, str]]:
    # Full message is worth printing when the cell had to shorten it
    details: list[tuple[str, str]] = []
    for s in items:
        if not s.error:
            continue
        message = s.error.strip()
        shortened = format_error(message, limit) != message
        if len(s.error.splitlines()) > 1 or shortened:
            details.append((s.name, message))
    return details


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
        box=box.ROUNDED,
        header_style="bold cyan",
        title="gward",
        title_style="bold",
    )
    table.add_column("Repository", style="bold")
    table.add_column("Branch", style="magenta")
    table.add_column("Status")
    table.add_column("Staged", justify="right")
    table.add_column("Modified", justify="right")
    table.add_column("Untracked", justify="right")
    table.add_column("Sync", max_width=ERROR_LIMIT + 2)

    for s in items:
        if s.error:
            table.add_row(
                s.name,
                s.branch or "-",
                Text("error", style="bold red"),
                "",
                "",
                "",
                Text(
                    format_error(s.error),
                    style="red",
                    no_wrap=True,
                    overflow="ellipsis",
                ),
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
    empty_message: str = "No Git repositories found",
) -> None:
    console = console or Console()
    if not items:
        console.print(empty_message)
        return
    console.print(build_table(items))
    details = error_details(items)
    if details:
        console.print()
        console.print(Text("Errors:", style="bold"))
        for name, message in details:
            console.print(
                Text.assemble((f"{name}: ", "bold"), (message, "red"))
            )
    if elapsed is not None:
        console.print(f"[dim]Checked in {elapsed:.2f} s[/dim]")
