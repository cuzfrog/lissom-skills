"""
Integration tests for uninstall.sh.

Each test seeds lissom files directly, then calls uninstall.sh and
asserts postconditions. Remote execution via curl | bash is also tested.
"""
import os
import shutil
import subprocess
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from conftest import AGENTS, SKILLS, seed_lissom_files

REPO_ROOT = Path(__file__).resolve().parent.parent
UNINSTALL_SH = REPO_ROOT / "scripts" / "uninstall.sh"


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
    """U1: All installed agent and skill files are removed from .claude/."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    seed_lissom_files(work)

    result = run_uninstall(src, work)

    assert result.returncode == 0
    assert not (work / ".claude" / "agents" / "lissom-researcher.md").exists()
    assert not (work / ".claude" / "skills" / "lissom-auto" / "SKILL.md").exists()


def test_empty_dirs_cleaned(tmp_path):
    """U3: agents/, skills/ dirs and the .claude/ dir are removed when empty."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    seed_lissom_files(work)

    run_uninstall(src, work)

    assert not (work / ".claude" / "agents").exists()
    assert not (work / ".claude" / "skills").exists()
    assert not (work / ".claude").exists()


def test_uninstall_nothing_to_remove(tmp_path):
    """U4: Running uninstall against an empty work dir exits cleanly."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()

    result = run_uninstall(src, work)

    assert result.returncode == 0
    assert "No lissom-skills files found to remove." in result.stdout


def test_uninstall_claude_only(tmp_path):
    """U5: Uninstall removes files from .claude/ when only that directory exists."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    seed_lissom_files(work)

    assert (work / ".claude").exists()

    result = run_uninstall(src, work)

    assert result.returncode == 0
    assert not (work / ".claude").exists()


def test_uninstall_opencode_only(tmp_path):
    """U6: Uninstall removes files from .opencode/ when only that directory exists."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    seed_lissom_files(work, ".opencode")

    assert (work / ".opencode").exists()
    assert not (work / ".claude").exists()

    result = run_uninstall(src, work)

    assert result.returncode == 0
    assert not (work / ".opencode").exists()


def test_uninstall_both_directories(tmp_path):
    """U7: Uninstall removes files from both .claude/ and .opencode/ if both exist."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    seed_lissom_files(work, ".claude")
    seed_lissom_files(work, ".opencode")

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
    seed_lissom_files(work)

    result = run_uninstall(src, work, env_extra={"LISSOM_YES": "1"})

    assert result.returncode == 0
    assert not (work / ".claude" / "agents" / "lissom-researcher.md").exists()
    assert "The following lissom-skills files will be removed:" in result.stdout
    assert "file(s)" in result.stdout
    assert "Remove these files?" not in result.stdout
    assert "Uninstall cancelled." not in result.stdout


def test_uninstall_nothing_to_remove_output(tmp_path):
    """U9: Uninstall on empty dir prints nothing-to-remove message and exits 0."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()

    result = run_uninstall(src, work)

    assert result.returncode == 0
    assert "No lissom-skills files found to remove." in result.stdout
    assert "The following lissom-skills files will be removed:" not in result.stdout
    assert "Remove these files?" not in result.stdout


def test_uninstall_summary_format(tmp_path):
    """U10: Summary shows per-directory file counts when files exist."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    seed_lissom_files(work)

    result = run_uninstall(src, work)

    assert result.returncode == 0
    assert "The following lissom-skills files will be removed:" in result.stdout
    assert ".claude/ ->" in result.stdout
    assert "Total:" in result.stdout
    assert "file(s)" in result.stdout


def test_uninstall_non_tty_proceeds(tmp_path):
    """U11: Non-interactive mode (stdin not a TTY) proceeds without prompting."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    seed_lissom_files(work)

    result = run_uninstall(src, work)

    assert result.returncode == 0
    assert "Remove these files?" not in result.stdout
    assert "Uninstall cancelled." not in result.stdout
    assert not (work / ".claude" / "agents" / "lissom-researcher.md").exists()


# ── DRY_RUN mode tests ──────────────────────────────────────────────────

def call_uninstall_from(src: Path, work: Path, target: str, dry_run: str = "false") -> subprocess.CompletedProcess:
    """
    Call uninstall_from() directly without running the script's main body.
    """
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
    seed_lissom_files(work)

    result = call_uninstall_from(src, work, "./.claude", "true")

    assert result.returncode == 0
    stdout = result.stdout.strip()
    assert stdout.isdigit(), f"Expected numeric output, got: {stdout}"
    assert int(stdout) > 0, f"Expected positive count, got: {stdout}"


def test_dry_run_no_side_effects(tmp_path):
    """DR2: uninstall_from with dry_run=true does not remove any files or directories."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    seed_lissom_files(work)

    assert (work / ".claude" / "agents" / "lissom-researcher.md").exists()
    assert (work / ".claude" / "skills" / "lissom-auto" / "SKILL.md").exists()

    result = call_uninstall_from(src, work, "./.claude", "true")

    assert result.returncode == 0
    assert (work / ".claude" / "agents" / "lissom-researcher.md").exists()
    assert (work / ".claude" / "skills" / "lissom-auto" / "SKILL.md").exists()


def test_dry_run_no_empty_dir_removal(tmp_path):
    """DR3: dry_run=true does not remove empty directories."""
    target = tmp_path / "work" / ".claude"
    (target / "agents").mkdir(parents=True, exist_ok=True)
    (target / "agents" / "lissom-foo.md").touch()
    (target / "skills").mkdir(parents=True, exist_ok=True)

    result = call_uninstall_from(tmp_path, tmp_path / "work", "./.claude", "true")

    assert result.returncode == 0
    assert (target / "agents").exists()
    assert (target / "agents" / "lissom-foo.md").exists()


def test_dry_run_count_matches_actual(tmp_path):
    """DR4: Dry-run count equals the number of files that would actually be removed."""
    import re
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    seed_lissom_files(work)

    dry_result = call_uninstall_from(src, work, "./.claude", "true")
    dry_count = int(dry_result.stdout.strip())

    src2, work2 = tmp_path / "src2", tmp_path / "work2"
    src2.mkdir(); work2.mkdir()
    seed_lissom_files(work2)

    actual_result = call_uninstall_from(src2, work2, "./.claude", "false")
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
    seed_lissom_files(work)

    result_no_arg = call_uninstall_from(src, work, "./.claude")
    assert result_no_arg.returncode == 0
    assert not (work / ".claude" / "agents" / "lissom-researcher.md").exists()

    src2, work2 = tmp_path / "src2", tmp_path / "work2"
    src2.mkdir(); work2.mkdir()
    seed_lissom_files(work2)

    result_explicit = call_uninstall_from(src2, work2, "./.claude", "false")
    assert result_explicit.returncode == 0
    assert not (work2 / ".claude" / "agents" / "lissom-researcher.md").exists()
    assert "Removed" in result_no_arg.stdout
    assert "Removed" in result_explicit.stdout


# ── Qwen uninstall tests ─────────────────────────────────────────────

def test_uninstall_qwen(tmp_path):
    """UQ1: Uninstall finds and removes files from .qwen/ when only that directory exists."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    seed_lissom_files(work, ".qwen")

    assert (work / ".qwen").exists()

    result = run_uninstall(src, work)

    assert result.returncode == 0
    assert not (work / ".qwen").exists()


def test_uninstall_all_targets(tmp_path):
    """UQ2: Uninstall removes files from all four directories when all populated."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()

    for target in (".claude", ".opencode", ".qwen", ".gemini"):
        seed_lissom_files(work, target)

    assert (work / ".claude").exists()
    assert (work / ".opencode").exists()
    assert (work / ".qwen").exists()
    assert (work / ".gemini").exists()

    result = run_uninstall(src, work)

    assert result.returncode == 0
    assert not (work / ".claude").exists()
    assert not (work / ".opencode").exists()
    assert not (work / ".qwen").exists()
    assert not (work / ".gemini").exists()
    assert ".claude/ ->" in result.stdout
    assert ".opencode/ ->" in result.stdout
    assert ".qwen/ ->" in result.stdout
    assert ".gemini/ ->" in result.stdout


def test_uninstall_gemini(tmp_path):
    """UG1: Uninstall finds and removes files from .gemini/ when only that directory exists."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    seed_lissom_files(work, ".gemini")

    assert (work / ".gemini").exists()
    assert (work / ".gemini" / "agents" / "lissom-researcher.md").exists()

    result = run_uninstall(src, work)

    assert result.returncode == 0
    assert not (work / ".gemini").exists()
    assert not (work / ".gemini" / "agents" / "lissom-researcher.md").exists()


# ── Remote uninstall tests (curl | bash) ─────────────────────────────

class _UninstallRepoHandler(SimpleHTTPRequestHandler):
    """HTTP handler that serves files from the repo root silently."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(REPO_ROOT), **kwargs)
    def log_message(self, fmt, *args):
        pass


def test_remote_uninstall_via_curl(tmp_path):
    """Verify 'curl ... | bash' remote uninstall works."""
    work = tmp_path / "work"
    work.mkdir()

    # Seed lissom files to remove
    seed_lissom_files(work)

    server = HTTPServer(("127.0.0.1", 0), _UninstallRepoHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        result = subprocess.run(
            ["bash", "-c",
             f"curl -fsSL http://127.0.0.1:{port}/scripts/uninstall.sh | bash"],
            cwd=str(work),
            env={
                **os.environ,
                "LISSOM_REPO": f"http://127.0.0.1:{port}",
                "LISSOM_YES": "1",
            },
            capture_output=True, text=True, timeout=60,
        )

        assert result.returncode == 0, (
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        assert not (work / ".claude" / "agents" / "lissom-researcher.md").exists()
        assert not (work / ".claude" / "skills" / "lissom-auto" / "SKILL.md").exists()
    finally:
        server.shutdown()


def test_remote_uninstall_nothing_to_remove(tmp_path):
    """Remote uninstall on empty dir exits cleanly without errors."""
    work = tmp_path / "work"
    work.mkdir()

    server = HTTPServer(("127.0.0.1", 0), _UninstallRepoHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        result = subprocess.run(
            ["bash", "-c",
             f"curl -fsSL http://127.0.0.1:{port}/scripts/uninstall.sh | bash"],
            cwd=str(work),
            env={
                **os.environ,
                "LISSOM_REPO": f"http://127.0.0.1:{port}",
                "LISSOM_YES": "1",
            },
            capture_output=True, text=True, timeout=60,
        )

        assert result.returncode == 0, (
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        assert "No lissom-skills files found to remove." in result.stdout
    finally:
        server.shutdown()
