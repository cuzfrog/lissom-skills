"""
Integration tests for uninstall.sh.

Each test calls install.sh first to set up a known state, then calls
uninstall.sh and asserts postconditions.
"""
import os
import shutil
import subprocess
from pathlib import Path

from conftest import AGENTS, SKILLS, make_src_tree

REPO_ROOT = Path(__file__).resolve().parent.parent
INSTALL_SH = REPO_ROOT / "install.sh"
UNINSTALL_SH = REPO_ROOT / "uninstall.sh"


def install_fixture(src: Path, work: Path) -> None:
    """Run install.sh from work with LISSOM_YES=1 to establish a known installed state."""
    shutil.copy(INSTALL_SH, src / "install.sh")
    subprocess.run(
        ["bash", str(src / "install.sh")],
        cwd=str(work),
        env={**os.environ, "LISSOM_YES": "1"},
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=True,
    )


def run_uninstall(src: Path, work: Path, args=(), env_extra=None):
    """Copy uninstall.sh into src so SCRIPT_DIR resolves there, then run it from work."""
    shutil.copy(UNINSTALL_SH, src / "uninstall.sh")
    env = {**os.environ}
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        ["bash", str(src / "uninstall.sh"), *args],
        cwd=str(work),
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
    )


# Test cases

def test_uninstall_removes_skills_and_agents(tmp_path):
    """U1: All installed agent and skill files are removed."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")
    install_fixture(src, work)

    result = run_uninstall(src, work, args=("--project",))

    assert result.returncode == 0
    assert not (work / ".claude" / "agents" / "task-researcher.md").exists()
    assert not (work / ".claude" / "skills" / "task-auto" / "SKILL.md").exists()


def test_claudemd_preserved_by_uninstall(tmp_path):
    """U2: CLAUDE.md remains after uninstall."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")
    install_fixture(src, work)

    result = run_uninstall(src, work, args=("--project",))

    assert result.returncode == 0
    assert (work / ".claude" / "CLAUDE.md").is_file()


def test_empty_dirs_cleaned(tmp_path):
    """U3: agents/ and skills/ dirs are removed; .claude/ dir is kept because CLAUDE.md remains."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")
    install_fixture(src, work)

    run_uninstall(src, work, args=("--project",))

    assert not (work / ".claude" / "agents").exists()
    assert not (work / ".claude" / "skills").exists()
    assert (work / ".claude").is_dir()


def test_uninstall_nothing_to_remove(tmp_path):
    """U4: Running uninstall against an empty work dir exits cleanly."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    result = run_uninstall(src, work, args=("--project",))

    assert result.returncode == 0


def test_uninstall_user_flag(tmp_path):
    """U5: --user flag removes files from $HOME/.claude and preserves CLAUDE.md."""
    src = tmp_path / "src"
    work = tmp_path / "work"
    fakehome = tmp_path / "home"
    src.mkdir(); work.mkdir(); fakehome.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    # Install into fakehome/.claude using --user
    shutil.copy(INSTALL_SH, src / "install.sh")
    subprocess.run(
        ["bash", str(src / "install.sh"), "--user"],
        cwd=str(work),
        env={**os.environ, "HOME": str(fakehome), "LISSOM_YES": "1"},
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=True,
    )

    result = run_uninstall(src, work, args=("--user",), env_extra={"HOME": str(fakehome)})

    assert result.returncode == 0
    assert not (fakehome / ".claude" / "agents" / "task-researcher.md").exists()
    assert (fakehome / ".claude" / "CLAUDE.md").is_file()


def test_specs_not_removed_by_uninstall(tmp_path):
    """U6: Specs.md created by install is not touched by uninstall."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")
    install_fixture(src, work)

    run_uninstall(src, work, args=("--project",))

    assert (work / ".dev" / "tasks" / "T1" / "Specs.md").is_file()
