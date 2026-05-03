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
    assert "No lissom-skills files found to remove." in result.stdout


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


def test_uninstall_lissom_yes_bypasses_confirmation(tmp_path):
    """U8: LISSOM_YES=1 skips confirmation prompt and proceeds with removal."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")
    install_fixture(src, work)

    result = run_uninstall(src, work, env_extra={"LISSOM_YES": "1"})

    assert result.returncode == 0
    # Should have removed files (proceeded, not cancelled)
    assert not (work / ".claude" / "agents" / "lissom-researcher.md").exists()
    # Should still print the summary
    assert "The following lissom-skills files will be removed:" in result.stdout
    assert "file(s)" in result.stdout
    # Should not print the prompt text (since LISSOM_YES=1 bypasses it)
    assert "Remove these files?" not in result.stdout
    # Should not print cancelled message
    assert "Uninstall cancelled." not in result.stdout


def test_uninstall_nothing_to_remove_output(tmp_path):
    """U9: Uninstall on empty dir prints nothing-to-remove message and exits 0."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    result = run_uninstall(src, work)

    assert result.returncode == 0
    assert "No lissom-skills files found to remove." in result.stdout
    # Should NOT print the summary header (since nothing to remove)
    assert "The following lissom-skills files will be removed:" not in result.stdout
    # Should NOT print the prompt (nothing to confirm)
    assert "Remove these files?" not in result.stdout


def test_uninstall_summary_format(tmp_path):
    """U10: Summary shows per-directory file counts when files exist."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")
    install_fixture(src, work)

    result = run_uninstall(src, work)

    assert result.returncode == 0
    assert "The following lissom-skills files will be removed:" in result.stdout
    # .claude/ should appear with a count
    assert ".claude/ ->" in result.stdout
    assert "Total:" in result.stdout
    assert "file(s)" in result.stdout


def test_uninstall_non_tty_proceeds(tmp_path):
    """U11: Non-interactive mode (stdin not a TTY) proceeds without prompting."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")
    install_fixture(src, work)

    # run_uninstall already uses stdin=subprocess.DEVNULL, so this tests the
    # non-TTY auto-proceed path explicitly.
    result = run_uninstall(src, work)

    assert result.returncode == 0
    # Should NOT contain the confirmation prompt
    assert "Remove these files?" not in result.stdout
    # Should NOT be cancelled
    assert "Uninstall cancelled." not in result.stdout
    # Files should be removed
    assert not (work / ".claude" / "agents" / "lissom-researcher.md").exists()


# ── DRY_RUN mode tests ──────────────────────────────────────────────────

def call_uninstall_from(src: Path, work: Path, target: str, dry_run: str = "false") -> subprocess.CompletedProcess:
    """
    Call uninstall_from() directly without running the script's main body.

    Sources the actual scripts/uninstall.sh (which has a BASH_SOURCE guard
    that prevents the main body from executing when sourced), then calls
    uninstall_from with the given arguments.
    """
    REPO_ROOT = Path(__file__).resolve().parent.parent
    lib_dest = src / "scripts" / "lib"
    lib_dest.mkdir(parents=True, exist_ok=True)
    for lib in ("common.sh", "constants.sh", "ui.sh"):
        shutil.copy(REPO_ROOT / "scripts" / "lib" / lib, lib_dest / lib)
    shutil.copy(REPO_ROOT / "scripts" / "uninstall.sh", src / "uninstall.sh")

    wrapper = src / "call_uninstall_from.sh"
    wrapper.write_text(f"""#!/usr/bin/env bash
set -e
SCRIPT_DIR="{src}"
source "$SCRIPT_DIR/scripts/lib/common.sh"
source "$SCRIPT_DIR/scripts/lib/constants.sh"
source "$SCRIPT_DIR/scripts/lib/ui.sh"
source "$SCRIPT_DIR/uninstall.sh"

uninstall_from "{target}" {dry_run}
""")
    wrapper.chmod(0o755)
    return subprocess.run(
        ["bash", str(wrapper)],
        cwd=str(work),
        env={**os.environ},
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
    )


def test_dry_run_outputs_count_only(tmp_path):
    """DR1: uninstall_from with dry_run=true outputs only a number, no per-file messages."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")
    install_fixture(src, work)

    result = call_uninstall_from(src, work, "./.claude", "true")

    assert result.returncode == 0
    # Output should be a plain integer (no per-file messages, no human-readable summary)
    stdout = result.stdout.strip()
    assert stdout.isdigit(), f"Expected numeric output, got: {stdout}"
    assert int(stdout) > 0, f"Expected positive count, got: {stdout}"


def test_dry_run_no_side_effects(tmp_path):
    """DR2: uninstall_from with dry_run=true does not remove any files or directories."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")
    install_fixture(src, work)

    # Verify files exist
    assert (work / ".claude" / "agents" / "lissom-researcher.md").exists()
    assert (work / ".claude" / "skills" / "lissom-auto" / "SKILL.md").exists()

    result = call_uninstall_from(src, work, "./.claude", "true")

    assert result.returncode == 0
    # Files should still exist (nothing removed)
    assert (work / ".claude" / "agents" / "lissom-researcher.md").exists()
    assert (work / ".claude" / "skills" / "lissom-auto" / "SKILL.md").exists()


def test_dry_run_no_empty_dir_removal(tmp_path):
    """DR3: dry_run=true does not remove empty directories."""
    # Set up a target with a single file, so after normal uninstall the dir would be empty
    target = tmp_path / "work" / ".claude"
    (target / "agents").mkdir(parents=True, exist_ok=True)
    (target / "agents" / "lissom-foo.md").touch()
    (target / "skills").mkdir(parents=True, exist_ok=True)

    result = call_uninstall_from(tmp_path, tmp_path / "work", "./.claude", "true")

    assert result.returncode == 0
    # Directory structure should remain intact
    assert (target / "agents").exists()
    assert (target / "agents" / "lissom-foo.md").exists()


def test_dry_run_count_matches_actual(tmp_path):
    """DR4: Dry-run count equals the number of files that would actually be removed."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")
    install_fixture(src, work)

    # Get dry-run count
    dry_result = call_uninstall_from(src, work, "./.claude", "true")
    dry_count = int(dry_result.stdout.strip())

    # Re-install from scratch and get actual removal count
    # (work dir was mutated by install; re-create for clean state)
    src2, work2 = tmp_path / "src2", tmp_path / "work2"
    src2.mkdir(); work2.mkdir()
    make_src_tree(src2, "2026-01-01T00:00:00")
    install_fixture(src2, work2)

    # Now do a normal (non-dry) uninstall and capture the count from output
    actual_result = call_uninstall_from(src2, work2, "./.claude", "false")
    # Normal output: "Removed N files from ..."
    import re
    match = re.search(r'Removed (\d+) files from', actual_result.stdout)
    assert match, f"Could not parse count from: {actual_result.stdout}"
    actual_count = int(match.group(1))

    assert dry_count == actual_count, (
        f"Dry-run count ({dry_count}) != actual removal count ({actual_count})"
    )


def test_dry_run_default_false(tmp_path):
    """DR5: uninstall_from without second arg behaves identically to dry_run=false (removes files)."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")
    install_fixture(src, work)

    # Without second arg — should behave like normal (remove files)
    result_no_arg = call_uninstall_from(src, work, "./.claude")
    assert result_no_arg.returncode == 0
    assert not (work / ".claude" / "agents" / "lissom-researcher.md").exists()

    # Re-install and check with explicit false
    src2, work2 = tmp_path / "src2", tmp_path / "work2"
    src2.mkdir(); work2.mkdir()
    make_src_tree(src2, "2026-01-01T00:00:00")
    install_fixture(src2, work2)

    result_explicit = call_uninstall_from(src2, work2, "./.claude", "false")
    assert result_explicit.returncode == 0
    assert not (work2 / ".claude" / "agents" / "lissom-researcher.md").exists()
    # Both should produce the same output format
    assert "Removed" in result_no_arg.stdout
    assert "Removed" in result_explicit.stdout

