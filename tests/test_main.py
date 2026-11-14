import asyncio

from gward.main import collect, gather_statuses
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
