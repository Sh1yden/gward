"""Output Module."""

from .models import RepoStatus


def render(items: list[RepoStatus], elapsed: float) -> str:
    if not items:
        return ""
    width = max(len(s.name) for s in items)
    lines = []
    for s in items:
        if s.error:
            state, extra = "ERROR", s.error
        else:
            state = "dirty" if s.is_dirty else "clean"
            sync = f"↑{s.ahead} ↓{s.behind}" if s.ahead is not None else "-"
            extra = f"S{s.staged} M{s.modified} U{s.untracked}  {sync}"
        lines.append(f"{s.name:<{width}}  {s.branch or '-':<14} {state:<6} {extra}")
    lines.append(f"\nПроверено за {elapsed:.2f} с")
    return "\n".join(lines)
