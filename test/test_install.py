"""
Integration tests for install.sh.

Each test creates a fresh fixture source tree and an empty work directory
inside tmp_path, copies install.sh into the fixture source so that
SCRIPT_DIR resolves to the fixture, then runs the script from the work
directory and asserts postconditions.
"""
import os
import shutil
import subprocess
from pathlib import Path

from conftest import AGENTS, SKILLS, make_src_tree

REPO_ROOT = Path(__file__).resolve().parent.parent
INSTALL_SH = REPO_ROOT / "install.sh"


def run_install(src: Path, work: Path, args=(), env_extra=None):
    """Copy install.sh into src so SCRIPT_DIR resolves there, then run it from work."""
    shutil.copy(INSTALL_SH, src / "install.sh")
    env = {**os.environ}
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        ["bash", str(src / "install.sh"), *args],
        cwd=str(work),
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
    )


# Test cases

def test_fresh_install(tmp_path):
    """T1: Fresh install copies all agents, skills, and Specs.md."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    result = run_install(src, work)

    assert result.returncode == 0
    assert (work / ".claude" / "agents" / "task-researcher.md").is_file()
    assert (work / ".claude" / "skills" / "task-auto" / "SKILL.md").is_file()
    assert (work / ".lissom" / "tasks" / "T1" / "Specs.md").is_file()


def test_reinstall_same_version(tmp_path):
    """T2: Re-installing the same version overwrites silently with no downgrade prompt."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")
    run_install(src, work)

    result = run_install(src, work)

    assert result.returncode == 0
    # The downgrade prompt phrase must not appear in stdout
    assert "newer than the source" not in result.stdout
    assert (work / ".claude" / "agents" / "task-researcher.md").is_file()


def test_upgrade(tmp_path):
    """T3: Source newer than installed overwrites silently without a prompt."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2025-01-01T00:00:00")
    run_install(src, work)
    make_src_tree(src, "2026-06-01T00:00:00")

    result = run_install(src, work)

    assert result.returncode == 0
    assert "newer than the source" not in result.stdout
    content = (work / ".claude" / "agents" / "task-researcher.md").read_text()
    assert "2026-06-01T00:00:00" in content


def test_downgrade_accepted(tmp_path):
    """T4: All files are downgraded when LISSOM_YES=1."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-06-01T00:00:00")
    run_install(src, work)
    make_src_tree(src, "2025-01-01T00:00:00")

    result = run_install(src, work, env_extra={"LISSOM_YES": "1"})

    assert result.returncode == 0
    content = (work / ".claude" / "agents" / "task-researcher.md").read_text()
    assert "2025-01-01T00:00:00" in content


def test_downgrade_declined(tmp_path):
    """T5: No tty causes the downgrade prompt to default to 'no'; newer installed files preserved."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-06-01T00:00:00")
    run_install(src, work)
    make_src_tree(src, "2025-01-01T00:00:00")

    result = run_install(src, work)

    assert result.returncode == 0
    content = (work / ".claude" / "agents" / "task-researcher.md").read_text()
    assert "2026-06-01T00:00:00" in content


def test_mixed_versions(tmp_path):
    """T6: Newer-source files upgrade silently; older-source file is skipped (one file skipped)."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")
    run_install(src, work)

    # task-researcher source becomes newer → should upgrade silently
    (src / "agents" / "task-researcher.md").write_text(
        "---\nname: task-researcher\nversion: 2026-06-01T00:00:00\ndescription: fixture\n---\nbody\n"
    )
    # task-planner source becomes older → should be skipped (prompt declined via no tty)
    (src / "agents" / "task-planner.md").write_text(
        "---\nname: task-planner\nversion: 2025-01-01T00:00:00\ndescription: fixture\n---\nbody\n"
    )

    result = run_install(src, work)

    assert result.returncode == 0
    researcher = (work / ".claude" / "agents" / "task-researcher.md").read_text()
    planner = (work / ".claude" / "agents" / "task-planner.md").read_text()
    assert "2026-06-01T00:00:00" in researcher
    assert "2026-01-01T00:00:00" in planner   # old installed version preserved
    assert "Skipped 1" in result.stdout


def test_user_mode_target(tmp_path):
    """T11: --user installs to $HOME/.claude and does not create Specs.md."""
    src = tmp_path / "src"
    work = tmp_path / "work"
    fakehome = tmp_path / "home"
    src.mkdir(); work.mkdir(); fakehome.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    result = run_install(src, work, args=("--user",), env_extra={"HOME": str(fakehome)})

    assert result.returncode == 0
    assert (fakehome / ".claude" / "agents" / "task-researcher.md").is_file()
    assert not (work / ".lissom" / "tasks" / "T1" / "Specs.md").exists()


def test_no_version_field_overwritten_silently(tmp_path):
    """T12: A versionless installed file is treated as 'version 0' and overwritten without a prompt."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")
    # Pre-place a file with no version field in the target
    (work / ".claude" / "agents").mkdir(parents=True)
    (work / ".claude" / "agents" / "task-researcher.md").write_text(
        "---\nname: task-researcher\ndescription: old, no version\n---\nbody\n"
    )

    result = run_install(src, work)

    assert result.returncode == 0
    assert "newer than the source" not in result.stdout
    content = (work / ".claude" / "agents" / "task-researcher.md").read_text()
    assert "2026-01-01T00:00:00" in content



