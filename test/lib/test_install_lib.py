"""
Unit tests for install.sh utility functions.

Tests for:
- get_version()   - extract version from YAML frontmatter
- get_model()     - extract model from YAML frontmatter
- validate_yaml_frontmatter() - validate frontmatter structure
- add_model_to_content() - insert model field into frontmatter
- classify_file() - classify source/dest by version
"""
import subprocess
from pathlib import Path


def run_install_function(script_dir: Path, bash_body: str) -> subprocess.CompletedProcess:
    """Run bash code with frontmatter.sh and install_ops.sh function definitions loaded."""
    bash_code = f"""#!/usr/bin/env bash
SCRIPT_DIR="{script_dir}"
source "$SCRIPT_DIR/scripts/lib/constants.sh"
source "$SCRIPT_DIR/scripts/lib/frontmatter.sh"
source "$SCRIPT_DIR/scripts/lib/install_ops.sh"

{bash_body}
"""
    return subprocess.run(
        ["bash", "-c", bash_code],
        capture_output=True,
        text=True,
    )


class TestGetVersion:
    """get_version() extracts version from YAML frontmatter."""

    def test_valid_version(self, tmp_path, script_dir):
        f = tmp_path / "test.md"
        f.write_text("---\nname: test\nversion: 2026-01-01\n---\nbody\n")
        r = run_install_function(script_dir, f"get_version '{f}'")
        assert r.returncode == 0
        assert r.stdout.strip() == "2026-01-01"

    def test_no_version_field(self, tmp_path, script_dir):
        f = tmp_path / "test.md"
        f.write_text("---\nname: test\ndescription: no version\n---\nbody\n")
        r = run_install_function(script_dir, f"get_version '{f}'")
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_value_found_before_eof_without_closing(self, tmp_path, script_dir):
        """Extracts version even when closing --- is missing."""
        f = tmp_path / "test.md"
        f.write_text("---\nname: test\nversion: 2026-01-01\n")
        r = run_install_function(script_dir, f"get_version '{f}'")
        assert r.returncode == 0
        assert r.stdout.strip() == "2026-01-01"

    def test_no_frontmatter_at_all(self, tmp_path, script_dir):
        f = tmp_path / "test.md"
        f.write_text("just body text\nno frontmatter\n")
        r = run_install_function(script_dir, f"get_version '{f}'")
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_empty_file(self, tmp_path, script_dir):
        f = tmp_path / "test.md"
        f.write_text("")
        r = run_install_function(script_dir, f"get_version '{f}'")
        assert r.returncode == 0
        assert r.stdout.strip() == ""


class TestGetModel:
    """get_model() extracts model from YAML frontmatter."""

    def test_valid_model(self, tmp_path, script_dir):
        f = tmp_path / "test.md"
        f.write_text("---\nname: test\nversion: 1\nmodel: sonnet\n---\nbody\n")
        r = run_install_function(script_dir, f"get_model '{f}'")
        assert r.returncode == 0
        assert r.stdout.strip() == "sonnet"

    def test_no_model_field(self, tmp_path, script_dir):
        f = tmp_path / "test.md"
        f.write_text("---\nname: test\nversion: 1\n---\nbody\n")
        r = run_install_function(script_dir, f"get_model '{f}'")
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_value_found_before_eof_without_closing(self, tmp_path, script_dir):
        """Extracts model even when closing --- is missing."""
        f = tmp_path / "test.md"
        f.write_text("---\nname: test\nmodel: haiku\n")
        r = run_install_function(script_dir, f"get_model '{f}'")
        assert r.returncode == 0
        assert r.stdout.strip() == "haiku"

    def test_model_with_dots_and_slashes(self, tmp_path, script_dir):
        f = tmp_path / "test.md"
        f.write_text("---\nname: test\nversion: 1\nmodel: opencode-go/deepseek-v4-flash\n---\nbody\n")
        r = run_install_function(script_dir, f"get_model '{f}'")
        assert r.returncode == 0
        assert r.stdout.strip() == "opencode-go/deepseek-v4-flash"


class TestValidateYamlFrontmatter:
    """validate_yaml_frontmatter() checks frontmatter structure."""

    def test_valid_frontmatter(self, tmp_path, script_dir):
        f = tmp_path / "test.md"
        f.write_text("---\nname: test\nversion: 1\n---\nbody\n")
        r = run_install_function(script_dir, f"validate_yaml_frontmatter '{f}'; echo EXIT:$?")
        assert r.returncode == 0
        assert "EXIT:0" in r.stdout

    def test_missing_closing(self, tmp_path, script_dir):
        f = tmp_path / "test.md"
        f.write_text("---\nname: test\nversion: 1\nbody no close\n")
        r = run_install_function(script_dir, f"validate_yaml_frontmatter '{f}'; echo EXIT:$?")
        assert "EXIT:1" in r.stdout

    def test_no_frontmatter(self, tmp_path, script_dir):
        f = tmp_path / "test.md"
        f.write_text("just body\n")
        r = run_install_function(script_dir, f"validate_yaml_frontmatter '{f}'; echo EXIT:$?")
        assert "EXIT:1" in r.stdout

    def test_empty_file(self, tmp_path, script_dir):
        f = tmp_path / "test.md"
        f.write_text("")
        r = run_install_function(script_dir, f"validate_yaml_frontmatter '{f}'; echo EXIT:$?")
        assert "EXIT:1" in r.stdout

    def test_only_opening_delimiter(self, tmp_path, script_dir):
        f = tmp_path / "test.md"
        f.write_text("---\n")
        r = run_install_function(script_dir, f"validate_yaml_frontmatter '{f}'; echo EXIT:$?")
        assert "EXIT:1" in r.stdout


class TestAddModelToContent:
    """add_model_to_content() inserts model field into frontmatter."""

    def test_adds_after_tools_line(self, tmp_path, script_dir):
        content = "---\nname: test\ntools: Read, Write\n---\nbody\n"
        r = run_install_function(script_dir, f"add_model_to_content '{content}' sonnet")
        assert r.returncode == 0
        out = r.stdout
        assert "tools: Read, Write" in out
        assert "model: sonnet" in out
        # model should come after tools
        tools_idx = out.index("tools:")
        model_idx = out.index("model:")
        assert model_idx > tools_idx

    def test_adds_before_closing_when_no_tools(self, tmp_path, script_dir):
        content = "---\nname: test\nversion: 1\n---\nbody\n"
        r = run_install_function(script_dir, f"add_model_to_content '{content}' haiku")
        assert r.returncode == 0
        out = r.stdout
        assert "model: haiku" in out
        # model should be before closing ---
        model_idx = out.index("model:")
        close_idx = out.index("---", out.index("---") + 1)
        assert model_idx < close_idx

    def test_preserves_body_text(self, tmp_path, script_dir):
        content = "---\nname: test\ntools: Read\n---\nbody line 1\nbody line 2\n"
        r = run_install_function(script_dir, f"add_model_to_content '{content}' sonnet")
        assert r.returncode == 0
        assert "body line 1" in r.stdout
        assert "body line 2" in r.stdout

    def test_no_frontmatter_still_works(self, tmp_path, script_dir):
        content = "just body\nno frontmatter\n"
        r = run_install_function(script_dir, f"add_model_to_content '{content}' test")
        assert r.returncode == 0
        # No frontmatter means no insertion point; content passes through
        assert r.stdout.strip() == "just body\nno frontmatter"

    def test_preserves_other_frontmatter_fields(self, tmp_path, script_dir):
        content = "---\nname: test-agent\ndescription: some agent\nversion: 1.0\ntools: Bash\n---\nbody\n"
        r = run_install_function(script_dir, f"add_model_to_content '{content}' sonnet")
        assert r.returncode == 0
        assert "name: test-agent" in r.stdout
        assert "description: some agent" in r.stdout
        assert "version: 1.0" in r.stdout


class TestClassifyFile:
    """classify_file() sorts files into SILENT or OLDER arrays."""

    def test_new_file_adds_to_silent(self, tmp_path, script_dir):
        src = tmp_path / "src.md"
        dest = tmp_path / "dest.md"
        src.write_text("---\nname: test\nversion: 1\n---\nbody\n")
        # dest does not exist
        r = run_install_function(script_dir, f"""
SILENT_SRC=(); SILENT_DEST=()
OLDER_SRC=(); OLDER_DEST=()
classify_file '{src}' '{dest}'
echo "SILENT:${{#SILENT_SRC[@]}}"
echo "OLDER:${{#OLDER_SRC[@]}}"
""")
        assert r.returncode == 0
        assert "SILENT:1" in r.stdout
        assert "OLDER:0" in r.stdout

    def test_same_version_adds_to_silent(self, tmp_path, script_dir):
        src = tmp_path / "src.md"
        dest = tmp_path / "dest.md"
        src.write_text("---\nname: test\nversion: 1\n---\nbody\n")
        dest.write_text("---\nname: test\nversion: 1\n---\nbody\n")
        r = run_install_function(script_dir, f"""
SILENT_SRC=(); SILENT_DEST=()
OLDER_SRC=(); OLDER_DEST=()
classify_file '{src}' '{dest}'
echo "SILENT:${{#SILENT_SRC[@]}}"
echo "OLDER:${{#OLDER_SRC[@]}}"
""")
        assert r.returncode == 0
        assert "SILENT:1" in r.stdout
        assert "OLDER:0" in r.stdout

    def test_src_newer_adds_to_silent(self, tmp_path, script_dir):
        src = tmp_path / "src.md"
        dest = tmp_path / "dest.md"
        src.write_text("---\nname: test\nversion: 2\n---\nbody\n")
        dest.write_text("---\nname: test\nversion: 1\n---\nbody\n")
        r = run_install_function(script_dir, f"""
SILENT_SRC=(); SILENT_DEST=()
OLDER_SRC=(); OLDER_DEST=()
classify_file '{src}' '{dest}'
echo "SILENT:${{#SILENT_SRC[@]}}"
echo "OLDER:${{#OLDER_SRC[@]}}"
""")
        assert r.returncode == 0
        assert "SILENT:1" in r.stdout
        assert "OLDER:0" in r.stdout

    def test_src_older_adds_to_older(self, tmp_path, script_dir):
        src = tmp_path / "src.md"
        dest = tmp_path / "dest.md"
        src.write_text("---\nname: test\nversion: 1\n---\nbody\n")
        dest.write_text("---\nname: test\nversion: 2\n---\nbody\n")
        r = run_install_function(script_dir, f"""
SILENT_SRC=(); SILENT_DEST=()
OLDER_SRC=(); OLDER_DEST=()
classify_file '{src}' '{dest}'
echo "SILENT:${{#SILENT_SRC[@]}}"
echo "OLDER:${{#OLDER_SRC[@]}}"
""")
        assert r.returncode == 0
        assert "SILENT:0" in r.stdout
        assert "OLDER:1" in r.stdout

    def test_dest_no_version_adds_to_silent(self, tmp_path, script_dir):
        src = tmp_path / "src.md"
        dest = tmp_path / "dest.md"
        src.write_text("---\nname: test\nversion: 1\n---\nbody\n")
        dest.write_text("---\nname: test\ndescription: no version\n---\nbody\n")
        r = run_install_function(script_dir, f"""
SILENT_SRC=(); SILENT_DEST=()
OLDER_SRC=(); OLDER_DEST=()
classify_file '{src}' '{dest}'
echo "SILENT:${{#SILENT_SRC[@]}}"
echo "OLDER:${{#OLDER_SRC[@]}}"
""")
        assert r.returncode == 0
        assert "SILENT:1" in r.stdout
        assert "OLDER:0" in r.stdout

    def test_src_no_version_adds_to_silent(self, tmp_path, script_dir):
        src = tmp_path / "src.md"
        dest = tmp_path / "dest.md"
        src.write_text("---\nname: test\ndescription: no version\n---\nbody\n")
        dest.write_text("---\nname: test\nversion: 2\n---\nbody\n")
        r = run_install_function(script_dir, f"""
SILENT_SRC=(); SILENT_DEST=()
OLDER_SRC=(); OLDER_DEST=()
classify_file '{src}' '{dest}'
echo "SILENT:${{#SILENT_SRC[@]}}"
echo "OLDER:${{#OLDER_SRC[@]}}"
""")
        assert r.returncode == 0
        assert "SILENT:1" in r.stdout
        assert "OLDER:0" in r.stdout
