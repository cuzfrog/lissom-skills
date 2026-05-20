"""
Unit tests for install.sh functions (prompt_overwrite, prompt_target_directory,
restore_frontmatter_fields).

These tests source the script with --source-only and call individual functions.
They do not start an HTTP server or download zips — see test_install_e2e.py for
full end-to-end tests.
"""

import subprocess
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "install.sh"


# ---------------------------------------------------------------------------
# prompt_overwrite
# ---------------------------------------------------------------------------


def test_prompt_overwrite_yes_accepts():
    """prompt_overwrite returns true with LISSOM_YES=1."""
    result = subprocess.run(
        [
            "bash",
            "-c",
            "source scripts/install.sh --source-only && prompt_overwrite '.claude'",
        ],
        cwd=REPO_ROOT,
        env={**__import__("os").environ, "LISSOM_YES": "1"},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "true"


def test_prompt_overwrite_non_tty_declines():
    """prompt_overwrite returns false without LISSOM_YES when stdin is not a TTY."""
    result = subprocess.run(
        [
            "bash",
            "-c",
            "source scripts/install.sh --source-only && prompt_overwrite '.claude'",
        ],
        cwd=REPO_ROOT,
        env={**__import__("os").environ},
        capture_output=True,
        text=True,
        start_new_session=True,  # ← detaches from /dev/tty
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "false"


# ---------------------------------------------------------------------------
# prompt_target_directory
# ---------------------------------------------------------------------------


def test_prompt_target_directory_stdout_clean():
    """Regression: prompt_target_directory outputs only the target name to stdout."""
    for target in (".claude", ".opencode", ".qwen", ".gemini", ".pi"):
        result = subprocess.run(
            [
                "bash",
                "-c",
                f"""
                source scripts/install.sh --source-only
                LISSOM_TARGET={target} prompt_target_directory
            """,
            ],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0
        lines = result.stdout.strip().splitlines()
        assert len(lines) == 1, (
            f"Expected 1 line of stdout (the target name), got {len(lines)}: {lines}\n"
            f"stderr: {result.stderr}"
        )
        assert lines[0] == target, f"stdout should be '{target}', got: {lines[0]!r}"


# ---------------------------------------------------------------------------
# save_frontmatter_fields / restore_frontmatter_fields
# ---------------------------------------------------------------------------


def _run_restore_script(md_file_content, saved_entries):
    """
    Helper: write a temporary .md file, populate SAVED_KEYS/SAVED_VALUES,
    run restore_frontmatter_fields, and return the final file content.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        md_path = Path(tmpdir) / "test.md"
        md_path.write_text(md_file_content)

        # Construct full keys with absolute path
        keys_str = " ".join(
            f'"{Path(tmpdir) / "test.md"}|{field}"' for field, value in saved_entries
        )
        values_str = " ".join(f'"{value}"' for field, value in saved_entries)

        script = f"""
        source {SCRIPT} --source-only

        # Populate the global arrays
        SAVED_KEYS=({keys_str})
        SAVED_VALUES=({values_str})

        restore_frontmatter_fields

        cat "{md_path}"
        """
        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
        )
        # Return stdout (file content), stderr for diagnostics, and exit code
        return result.stdout, result.stderr, result.returncode


def test_restore_existing_field_sed_branch():
    """
    restore_frontmatter_fields: sed branch — field exists and is overwritten.
    """
    frontmatter = """\
---
model: claude-sonnet-4
temperature: 0.7
---
"""
    saved = [("model", "gpt-4o")]
    stdout, stderr, rc = _run_restore_script(frontmatter, saved)
    assert rc == 0, f"restore failed: {stderr}"
    assert "model: gpt-4o" in stdout
    assert "model: claude-sonnet-4" not in stdout


def test_restore_existing_field_preserves_other_fields():
    """sed branch does not touch other frontmatter fields."""
    frontmatter = """\
---
model: claude-sonnet-4
temperature: 0.7
---
"""
    saved = [("model", "gpt-4o")]
    stdout, stderr, rc = _run_restore_script(frontmatter, saved)
    assert rc == 0
    assert "temperature: 0.7" in stdout


def test_restore_existing_field_preserves_body():
    """sed branch does not alter content below the frontmatter."""
    frontmatter = """\
---
model: claude-sonnet-4
---
# Hello
Some text.
"""
    saved = [("model", "gpt-4o")]
    stdout, stderr, rc = _run_restore_script(frontmatter, saved)
    assert rc == 0
    assert "# Hello" in stdout
    assert "Some text." in stdout


def test_restore_missing_field_awk_branch():
    """
    restore_frontmatter_fields: awk branch — field absent, inserted after
    the second --- delimiter.
    """
    frontmatter = """\
---
model: claude-sonnet-4
---
# Header
"""
    saved = [("temperature", "0.2")]
    stdout, stderr, rc = _run_restore_script(frontmatter, saved)
    assert rc == 0, f"restore failed: {stderr}"
    # temperature should be inserted after the second ---
    assert "temperature: 0.2" in stdout


def test_restore_multiple_fields():
    """Both branches work together for multiple saved entries."""
    frontmatter = """\
---
model: claude-sonnet-4
---
"""
    saved = [
        ("model", "gpt-4o"),  # existing → sed
        ("temperature", "0.2"),  # missing → awk
    ]
    stdout, stderr, rc = _run_restore_script(frontmatter, saved)
    assert rc == 0, f"restore failed: {stderr}"
    assert "model: gpt-4o" in stdout
    assert "temperature: 0.2" in stdout


def test_save_and_restore_roundtrip():
    """
    Full save → restore cycle via save_frontmatter_fields:
    1. Save values from a directory of .md files.
    2. Mutate the files so the saved fields are different.
    3. Restore — values should be back to the originals.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        md_path = Path(tmpdir) / "agent.md"
        original = """\
---
model: claude-sonnet-4
temperature: 0.7
---
# Content
"""
        md_path.write_text(original)

        script = f"""
        source {SCRIPT} --source-only

        # 1. Save
        save_frontmatter_fields "{tmpdir}"

        # 2. Mutate: change model, remove temperature (portable, no sed -i)
        sed "s|^model:.*|model: CHANGED|" "{md_path}" > "{md_path}.tmp" && mv "{md_path}.tmp" "{md_path}"
        grep -v "^temperature:" "{md_path}" > "{md_path}.tmp" && mv "{md_path}.tmp" "{md_path}"

        # 3. Restore
        restore_frontmatter_fields

        # 4. Output result
        cat "{md_path}"
        """
        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"roundtrip failed: {result.stderr}"
        assert "model: claude-sonnet-4" in result.stdout
        assert "temperature: 0.7" in result.stdout
        assert "CHANGED" not in result.stdout


def test_save_and_restore_empty_dir():
    """save + restore on an empty directory is a no-op (no crash)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        script = f"""
        source {SCRIPT} --source-only
        save_frontmatter_fields "{tmpdir}"
        restore_frontmatter_fields
        echo "done"
        """
        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "done"


def test_restore_no_frontmatter_sed():
    """Field not preceded by --- ... --- frontmatter is still replaced by sed."""
    content = "model: old\n"
    saved = [("model", "new")]
    stdout, stderr, rc = _run_restore_script(content, saved)
    assert rc == 0, f"restore failed: {stderr}"
    assert stdout.strip() == "model: new"


def test_restore_multiple_md_files():
    """restore works across multiple .md files in different subdirs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        a_dir = Path(tmpdir) / "a"
        b_dir = Path(tmpdir) / "b"
        a_dir.mkdir()
        b_dir.mkdir()
        a_path = a_dir / "one.md"
        b_path = b_dir / "two.md"
        a_path.write_text("---\nmodel: old-a\n---\n")
        b_path.write_text("---\nmodel: old-b\n---\n")

        script = f"""
        source {SCRIPT} --source-only
        save_frontmatter_fields "{tmpdir}"
        # Mutate both
        # Mutate both (one at a time for portability)
        sed "s|^model:.*|model: MUTATED|" "{a_path}" > "{a_path}.tmp" && mv "{a_path}.tmp" "{a_path}"
        sed "s|^model:.*|model: MUTATED|" "{b_path}" > "{b_path}.tmp" && mv "{b_path}.tmp" "{b_path}"
        restore_frontmatter_fields
        echo "--- A ---"
        cat "{a_path}"
        echo "--- B ---"
        cat "{b_path}"
        """
        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"multi-file restore failed: {result.stderr}"
        assert "model: old-a" in result.stdout
        assert "model: old-b" in result.stdout
        assert "model: MUTATED" not in result.stdout
