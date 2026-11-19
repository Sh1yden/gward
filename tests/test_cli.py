import subprocess
from pathlib import Path

from typer.testing import CliRunner

from gward.main import app

runner = CliRunner()


def make_repo(path: Path) -> Path:
    path.mkdir()
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
