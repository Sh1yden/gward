# 🛡 gward

🌐 Language / Язык **README**: [Русский](README.md) · **English**

![icon](assets/icon.svg)

> **Short description:** 🛡️ A console utility for instant status checks of dozens of local Git repositories: uncommitted changes, unpushed commits and lag behind the remote, in one command.

## ❔ Why this project?

If you have dozens of local projects, it's easy to forget an unpushed commit or uncommitted changes. `gward` checks all repositories in a folder in parallel and shows a single table in a fraction of a second, without `cd`-ing into each folder.

## 🛠 Tech stack

- **Language:** `Python 3.13`
- **Git engine:** `asyncio.subprocess`, native `git status --porcelain=v2`
- **CLI:** `typer`
- **Output:** `rich`
- **Package manager and build:** `uv` (`uv_build`)
- **Tests:** `pytest`
- **Checks:** `ruff`, `mypy`

## 🧭 Table of contents

- [🛡 gward](#-gward)
  - [❔ Why this project?](#-why-this-project)
  - [🛠 Tech stack](#-tech-stack)
  - [📸 Example output](#-example-output)
  - [💜 User guide](#-user-guide)
    - [🔽 Install / Quick start](#-install--quick-start)
    - [🖱 Daily use](#-daily-use)
    - [❓ FAQ](#-faq)
  - [💻 Developer sections](#-developer-sections)
    - [🧰 Project setup](#-project-setup)
    - [🧪 Tests](#-tests)
  - [🗄 Project structure](#-project-structure)
  - [☑ Roadmap / Planned](#-roadmap--planned)
  - [📄 License](#-license)
  - [🤝 Contribution guidelines](#-contribution-guidelines)
  - [💜 Questions, contacts / FAQ](#-questions-contacts--faq)

## 📸 Example output

This is what `gward fetch` looks like on a folder of repositories (names are made up):

```text
                                gward
╭──────────────┬────────┬────────┬────────┬──────────┬───────────┬───────╮
│ Repository   │ Branch │ Status │ Staged │ Modified │ Untracked │ Sync  │
├──────────────┼────────┼────────┼────────┼──────────┼───────────┼───────┤
│ api-server   │ main   │ dirty  │      0 │        4 │         0 │ ↑0 ↓0 │
│ notes        │ main   │ dirty  │      2 │        0 │         1 │ ↑1 ↓0 │
│ dotfiles     │ main   │ clean  │      0 │        0 │         0 │ ↑0 ↓0 │
│ legacy-tool  │ master │ clean  │      0 │        0 │         0 │ —     │
╰──────────────┴────────┴────────┴────────┴──────────┴───────────┴───────╯
```

## 💜 User guide

### 🔽 Install / Quick start

Requirements: Python 3.13, `git` installed, Linux or macOS. Package manager `uv`: [installation guide](https://docs.astral.sh/uv/).

1. Install `gward` from the repository:

```shell
uv tool install git+https://github.com/Sh1yden/gward
```

1. Check that the command is available:

```shell
gward --help
```

For development, see the [«Project setup»](#-project-setup) section.

### 🖱 Daily use

- **`gward`** — status of all repositories in the current folder. Runs locally, does not use the network.
- **`gward -C ~/projects`** — the same for another folder. The `-C` flag works like `git -C`.
- **`gward -d`** — show only repositories that need attention: with errors, local changes, or diverged from the remote.
- **`gward --debug`** — add the elapsed time at the bottom.
- **`gward fetch`** — run `git fetch --prune` in all repositories first, then show the status. Requires network.
- **`gward -C ~/projects fetch`** — the same for another folder. Global options (`-C`, `-d`, `--debug`) go **before** the subcommand.

Table columns:

- **Staged** — files added to the index (`git add`) but not yet committed.
- **Modified** — changed files in the working copy, including conflicts.
- **Untracked** — new files that git does not track.
- **Sync** — `↑N` commits waiting to be pushed, `↓N` commits on the remote that are not present locally. `—` means no upstream is configured.

### ❓ FAQ

- **Sync shows `↓0`, but there are new commits on GitHub.** Without `fetch`, git doesn't know about commits on the server: it compares against saved remote-tracking refs, and those go stale. Run `gward fetch`.
- **Sync shows `—`.** The branch has no upstream configured. Add one with `git push -u origin <branch>`, and the column will start showing `↑` and `↓`.
- **A row is marked `error`.** Git could not read the status or complete the fetch. The first line of the error is shown in the Sync column, and the full text is printed below the table. Common causes: a broken repository, an unreachable remote, a timeout.
- **`Invalid value for '--dir' / '-C'` is printed.** The folder does not exist or is a file. Check the path; `gward` does not run the check until the folder is found.
- **"No Git repositories found" is printed.** `gward` looks for repositories in the folder itself and in its direct subfolders. Hidden folders (starting with a dot) are skipped. If you run `gward` inside a repository, only that repository is shown.
- **Why is `fetch` a separate command and not a flag?** A regular check should be instant and never touch the network. Fetch takes seconds and depends on the network, so it runs only when requested explicitly.
- **Which remote does `fetch` update?** The one configured for the current branch (its upstream, usually `origin`). `git fetch --prune` without arguments does not iterate over every remote. This is deliberate: an unreachable second remote should not mark the repository as broken. Use `git fetch --all` manually for all remotes.
- **A clean repository disappeared from the list.** The `-d` flag hides all clean repositories, including those without an upstream.
- **"All repositories are clean" is printed.** The `-d` filter ran and found no problems: every repository is clean and in sync. "No Git repositories found" remains only for a folder with no repositories at all.
- **Timeouts.** A regular check waits up to 10 seconds per repository, fetch up to 60. A repository that doesn't respond in time is marked `error`, and the rest keep being checked.

## 💻 Developer sections

### 🧰 Project setup

1. Clone the repository:

```shell
git clone https://github.com/Sh1yden/gward.git
cd gward
```

1. Set up the environment with `uv`:

```shell
uv sync
```

1. Install `gward` in editable mode, so changes take effect in the `gward` command immediately:

```shell
uv tool install --editable .
```

### 🧪 Tests

Tests live in the [`tests`](tests) directory. The `git status` parser is checked against fixtures with real git output, without calling git itself. Integration tests create temporary repositories via `tmp_path` and work with a local bare remote, so no network is needed.

```shell
uv run pytest -v
```

Linter and type checks (configured in `pyproject.toml`):

```shell
uv run ruff check
uv run mypy
```

## 🗄 Project structure

- `gward/` — the application package.
  - `main.py` — `typer` CLI: the default command (`gward`) and `fetch`, parallel execution through a semaphore.
  - `git.py` — running git (`run_git`), the `parse_status` parser, `get_status` and `fetch_repo`.
  - `dir.py` — repository discovery in a folder.
  - `filter.py` — priorities, sorting and the `only_attention` filter for the `-d` flag.
  - `output.py` — the `rich` table and report output.
  - `models.py` — the `RepoStatus` dataclass describing one repository's state.
- `tests/` — tests per module; `test_git.py` contains integration tests on real repositories.
- `pyproject.toml` and `uv.lock` — project configuration and dependencies.
- [`README.md`](README.md) — the Russian version; [`README.en.md`](README.en.md) — this file.
- [`LICENSE`](LICENSE) — project license.
- `.github/workflows/ci.yml` — CI: `ruff`, `mypy` and `pytest` on every push and pull request.

## ☑ Roadmap / Planned

See [CHANGELOG.md](CHANGELOG.md).

## 📄 License

This project is distributed under the MIT license. Details in the [LICENSE](LICENSE) file.

## 🤝 Contribution guidelines

- For a bugfix, first reproduce the problem and add or update a test in `tests/`.
- Follow PEP 8 (4 spaces, up to 79 characters), PEP 257 and type hints; do not leave `except Exception: pass`.
- Reflect user-facing changes in `README.md`/`README.en.md` and `CHANGELOG.md`.
- Do not commit `logs/`, `.venv` or API keys.
- Discuss major architectural changes in an Issue before implementing them.

## 💜 Questions, contacts / FAQ

For questions and suggestions, create Issues in the repository or message the Telegram account listed in the profile.

PS I would be very grateful for any help or advice.
