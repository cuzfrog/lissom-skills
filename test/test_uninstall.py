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
INSTALL_SH = REPO_ROOT / "scripts" / "install.sh"
UNINSTALL_SH = REPO_ROOT / "scripts" / "uninstall.sh"


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
    """U1: All installed agent and skill files are removed from both .claude/ and .opencode/."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")
    install_fixture(src, work)

    result = run_uninstall(src, work)

    assert result.returncode == 0
    assert not (work / ".claude" / "agents" / "lissom-researcher.md").exists()
    assert not (work / ".claude" / "skills" / "lissom-auto" / "SKILL.md").exists()


def test_empty_dirs_cleaned(tmp_path):
    """U3: agents/, skills/ dirs and the .claude/ dir are removed when empty."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")
    install_fixture(src, work)

    run_uninstall(src, work)

    assert not (work / ".claude" / "agents").exists()
    assert not (work / ".claude" / "skills").exists()
    assert not (work / ".claude").exists()


def test_uninstall_nothing_to_remove(tmp_path):
    """U4: Running uninstall against an empty work dir exits cleanly."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    result = run_uninstall(src, work)

    assert result.returncode == 0


def test_uninstall_claude_only(tmp_path):
    """U5: Uninstall removes files from .claude/ when only that directory exists."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")
    install_fixture(src, work)

    # Verify .claude exists
    assert (work / ".claude").exists()

    result = run_uninstall(src, work)

    assert result.returncode == 0
    assert not (work / ".claude").exists()


def test_uninstall_opencode_only(tmp_path):
    """U6: Uninstall removes files from .opencode/ when only that directory exists."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")
    
    # Install to .opencode instead of .claude
    shutil.copy(INSTALL_SH, src / "install.sh")
    subprocess.run(
        ["bash", str(src / "install.sh")],
        cwd=str(work),
        env={**os.environ, "LISSOM_YES": "1", "LISSOM_TARGET": ".opencode"},
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=True,
    )

    # Verify .opencode exists and .claude doesn't
    assert (work / ".opencode").exists()
    assert not (work / ".claude").exists()

    result = run_uninstall(src, work)

    assert result.returncode == 0
    assert not (work / ".opencode").exists()


def test_uninstall_both_directories(tmp_path):
    """U7: Uninstall removes files from both .claude/ and .opencode/ if both exist."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")
    
    # Install to .claude
    install_fixture(src, work)
    assert (work / ".claude").exists()

    # Also install to .opencode
    shutil.copy(INSTALL_SH, src / "install.sh")
    subprocess.run(
        ["bash", str(src / "install.sh")],
        cwd=str(work),
        env={**os.environ, "LISSOM_YES": "1", "LISSOM_TARGET": ".opencode"},
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=True,
    )
    
    # Verify both exist
    assert (work / ".claude").exists()
    assert (work / ".opencode").exists()

    result = run_uninstall(src, work)

    assert result.returncode == 0
    assert not (work / ".claude").exists()
    assert not (work / ".opencode").exists()


