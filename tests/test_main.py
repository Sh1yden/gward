import asyncio
from pathlib import Path

from gward.main import collect, compute_exit_code, gather_statuses
from gward.models import RepoStatus


async def fake_worker(repo):
    return RepoStatus(path=repo, name=repo.name)


def test_empty_folder_returns_empty_list(tmp_path):
    # No repositories: nothing is queried, result is an empty list
    assert asyncio.run(gather_statuses(tmp_path, worker=fake_worker)) == []


def test_collect_respects_limit(tmp_path):
    # Track the peak number of concurrent worker calls
    active = 0
    peak = 0

    async def counting_worker(repo):
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0.01)
        active -= 1
        return RepoStatus(path=repo, name=repo.name)

    repos = [tmp_path / f"r{i}" for i in range(10)]
    asyncio.run(collect(repos, counting_worker, limit=2))
    assert peak == 2


def test_collect_returns_one_result_per_repo(tmp_path):
    repos = [tmp_path / f"r{i}" for i in range(5)]
    results = asyncio.run(collect(repos, fake_worker))
    assert len(results) == 5


def test_collect_isolates_worker_failure(tmp_path):
    # One failing worker must not abort the report for other repositories
    async def flaky_worker(repo):
        if repo.name == "broken":
            raise RuntimeError("boom")
        return RepoStatus(path=repo, name=repo.name)

    repos = [tmp_path / "ok", tmp_path / "broken"]
    results = asyncio.run(collect(repos, flaky_worker))
    assert [s.error for s in results] == [None, "boom"]


def test_gather_statuses_respects_depth(tmp_path):
    nested = tmp_path / "group" / "nested"
    nested.mkdir(parents=True)
    (nested / ".git").mkdir()

    assert asyncio.run(gather_statuses(tmp_path, worker=fake_worker)) == []
    result = asyncio.run(
        gather_statuses(tmp_path, worker=fake_worker, depth=2)
    )
    assert [s.name for s in result] == ["nested"]


# ---------- exit codes ----------


def make_status(name, **kw):
    return RepoStatus(path=Path(name), name=name, **kw)


def test_compute_exit_code_clean():
    assert compute_exit_code([make_status("r")]) == 0


def test_compute_exit_code_no_upstream_is_clean():
    status = make_status("r", ahead=None, behind=None)
    assert compute_exit_code([status]) == 0


def test_compute_exit_code_dirty():
    assert compute_exit_code([make_status("r", modified=1)]) == 1


def test_compute_exit_code_unsynced():
    assert compute_exit_code([make_status("r", ahead=1, behind=0)]) == 1


def test_compute_exit_code_error_wins():
    statuses = [
        make_status("dirty", modified=1),
        make_status("broken", error="boom"),
    ]
    assert compute_exit_code(statuses) == 2
