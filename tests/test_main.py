import asyncio

from gward.main import gather_statuses
from gward.models import RepoStatus


def test_empty_folder_returns_empty_list(tmp_path):
    # No repositories: nothing is queried, result is an empty list
    assert asyncio.run(gather_statuses(tmp_path)) == []


def test_collect_respects_limit(monkeypatch, tmp_path):
    from gward import main as main_module

    # Track the peak number of concurrent calls to get_status
    active = 0
    peak = 0

    async def fake_get_status(repo):
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0.01)
        active -= 1
        return RepoStatus(path=repo, name=repo.name)

    monkeypatch.setattr(main_module, "get_status", fake_get_status)
    repos = [tmp_path / f"r{i}" for i in range(10)]
    asyncio.run(main_module.collect(repos, limit=2))
    assert peak == 2
