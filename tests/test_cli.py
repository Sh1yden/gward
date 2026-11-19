import json
import subprocess
from pathlib import Path

from typer.testing import CliRunner

from gward.main import app

runner = CliRunner()


def make_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "init", "-q", "-b", "main"],
        cwd=path,
        check=True,
        capture_output=True,
    )
    return path


def test_dir_option_applies_to_default_command(tmp_path):
    make_repo(tmp_path / "repo")
    result = runner.invoke(app, ["-C", str(tmp_path)])
    assert result.exit_code == 0
    assert "repo" in result.output


def test_dir_option_before_fetch_is_not_ignored(tmp_path):
    # Regression: global options used to be dropped for `gward -C DIR fetch`
    make_repo(tmp_path / "repo")
    result = runner.invoke(app, ["-C", str(tmp_path), "fetch"])
    assert result.exit_code == 0
    assert "repo" in result.output


def test_missing_directory_is_reported_without_traceback(tmp_path):
    missing = tmp_path / "missing"
    result = runner.invoke(app, ["-C", str(missing)])
    assert result.exit_code == 2
    assert "Traceback" not in result.output
    assert "does not exist" in result.output


def test_dirty_filter_reports_clean_state(tmp_path):
    make_repo(tmp_path / "repo")
    result = runner.invoke(app, ["-d", "-C", str(tmp_path)])
    assert result.exit_code == 0
    assert "All repositories are clean" in result.output


def test_dirty_filter_keeps_empty_message_for_empty_folder(tmp_path):
    result = runner.invoke(app, ["-d", "-C", str(tmp_path)])
    assert result.exit_code == 0
    assert "No Git repositories found" in result.output


# ---------- --json ----------


def test_json_output_has_expected_fields(tmp_path):
    make_repo(tmp_path / "clean")
    result = runner.invoke(app, ["--json", "-C", str(tmp_path)])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert len(data) == 1
    item = data[0]
    assert item["name"] == "clean"
    assert item["path"].endswith("clean")
    assert item["branch"] == "main"
    assert item["status"] == "clean"
    assert item["staged"] == 0
    assert item["modified"] == 0
    assert item["untracked"] == 0
    assert item["ahead"] is None
    assert item["behind"] is None
    assert item["error"] is None


def test_json_empty_folder_returns_empty_array(tmp_path):
    result = runner.invoke(app, ["--json", "-C", str(tmp_path)])
    assert result.exit_code == 0
    assert json.loads(result.stdout) == []


def test_json_works_with_fetch(tmp_path):
    make_repo(tmp_path / "repo")
    result = runner.invoke(app, ["--json", "-C", str(tmp_path), "fetch"])
    assert result.exit_code == 0
    assert json.loads(result.stdout)[0]["name"] == "repo"


def test_json_dirty_filter_keeps_only_attention(tmp_path):
    make_repo(tmp_path / "clean")
    dirty = make_repo(tmp_path / "dirty")
    (dirty / "file.txt").write_text("change\n")
    result = runner.invoke(app, ["--json", "-d", "-C", str(tmp_path)])
    assert result.exit_code == 0
    assert [item["name"] for item in json.loads(result.stdout)] == ["dirty"]


def test_json_error_status(tmp_path):
    broken = tmp_path / "broken"
    broken.mkdir()
    (broken / ".git").write_text("gitdir: /nonexistent\n")
    result = runner.invoke(app, ["--json", "-C", str(tmp_path)])
    assert result.exit_code == 0
    item = json.loads(result.stdout)[0]
    assert item["status"] == "error"
    assert item["error"]


# ---------- --exit-code ----------


def test_exit_code_clean(tmp_path):
    make_repo(tmp_path / "clean")
    result = runner.invoke(app, ["--exit-code", "-C", str(tmp_path)])
    assert result.exit_code == 0


def test_exit_code_dirty(tmp_path):
    repo = make_repo(tmp_path / "dirty")
    (repo / "file.txt").write_text("change\n")
    result = runner.invoke(app, ["--exit-code", "-C", str(tmp_path)])
    assert result.exit_code == 1


def test_exit_code_error(tmp_path):
    broken = tmp_path / "broken"
    broken.mkdir()
    (broken / ".git").write_text("gitdir: /nonexistent\n")
    result = runner.invoke(app, ["--exit-code", "-C", str(tmp_path)])
    assert result.exit_code == 2


def test_exit_code_is_opt_in(tmp_path):
    repo = make_repo(tmp_path / "dirty")
    (repo / "file.txt").write_text("change\n")
    result = runner.invoke(app, ["-C", str(tmp_path)])
    assert result.exit_code == 0


def test_json_and_exit_code_together(tmp_path):
    repo = make_repo(tmp_path / "dirty")
    (repo / "file.txt").write_text("change\n")
    result = runner.invoke(
        app, ["--json", "--exit-code", "-C", str(tmp_path)]
    )
    assert result.exit_code == 1
    assert json.loads(result.stdout)[0]["status"] == "dirty"


# ---------- --depth ----------


def test_depth_two_finds_nested_repository(tmp_path):
    make_repo(tmp_path / "group" / "nested")
    result = runner.invoke(app, ["--depth", "2", "-C", str(tmp_path)])
    assert result.exit_code == 0
    assert "nested" in result.output


def test_default_depth_skips_nested_repository(tmp_path):
    make_repo(tmp_path / "group" / "nested")
    result = runner.invoke(app, ["-C", str(tmp_path)])
    assert result.exit_code == 0
    assert "nested" not in result.output
    assert "No Git repositories found" in result.output


# ---------- completion ----------


def test_show_completion_is_available():
    result = runner.invoke(app, ["--show-completion"])
    assert result.exit_code == 0
    assert result.output.strip()
    assert "complete" in result.output
