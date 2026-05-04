"""
Unit tests for install.sh functions (prompt_overwrite, prompt_target_directory).

These tests source the script with --source-only and call individual functions.
They do not start an HTTP server or download zips — see test_install_e2e.py for
full end-to-end tests.
"""

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_prompt_overwrite_yes_accepts():
    """prompt_overwrite returns true with LISSOM_YES=1."""
    result = subprocess.run(
        ["bash", "-c",
         "source scripts/install.sh --source-only && prompt_overwrite '.claude'"],
        cwd=REPO_ROOT,
        env={**__import__("os").environ, "LISSOM_YES": "1"},
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "true"


def test_prompt_overwrite_non_tty_declines():
    """prompt_overwrite returns false without LISSOM_YES when stdin is not a TTY."""
    result = subprocess.run(
        ["bash", "-c",
         "source scripts/install.sh --source-only && prompt_overwrite '.claude'"],
        cwd=REPO_ROOT,
        env={**__import__("os").environ},
        capture_output=True, text=True,
        start_new_session=True,  # ← detaches from /dev/tty
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "false"


def test_prompt_target_directory_stdout_clean():
    """Regression: prompt_target_directory outputs only the target name to stdout."""
    for target in (".claude", ".opencode", ".qwen", ".gemini"):
        result = subprocess.run(
            ["bash", "-c", f"""
                source scripts/install.sh --source-only
                LISSOM_TARGET={target} prompt_target_directory
            """],
            capture_output=True, text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0
        lines = result.stdout.strip().splitlines()
        assert len(lines) == 1, (
            f"Expected 1 line of stdout (the target name), got {len(lines)}: {lines}\n"
            f"stderr: {result.stderr}"
        )
        assert lines[0] == target, f"stdout should be '{target}', got: {lines[0]!r}"
