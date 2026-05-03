"""
Unit tests for install.sh utility functions.

Tests for:
- get_model()     - extract model from YAML frontmatter
- _get_frontmatter_field() - generic frontmatter field extraction
- validate_yaml_frontmatter() - validate frontmatter structure
- add_model_to_content() - insert model field into frontmatter
- classify_file() - classify files for install (silent vs overwrite)
- has_lissom_installation() - check if lissom agent files exist
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


class TestGetModel:
    """get_model() extracts model from YAML frontmatter."""

    def test_valid_model(self, tmp_path, script_dir):
        f = tmp_path / "test.md"
        f.write_text("---\nname: test\nmodel: sonnet\n---\nbody\n")
        r = run_install_function(script_dir, f"get_model '{f}'")
        assert r.returncode == 0
        assert r.stdout.strip() == "sonnet"

    def test_no_model_field(self, tmp_path, script_dir):
        f = tmp_path / "test.md"
        f.write_text("---\nname: test\n---\nbody\n")
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
        f.write_text("---\nname: test\nmodel: opencode-go/deepseek-v4-flash\n---\nbody\n")
        r = run_install_function(script_dir, f"get_model '{f}'")
        assert r.returncode == 0
        assert r.stdout.strip() == "opencode-go/deepseek-v4-flash"


class TestValidateYamlFrontmatter:
    """validate_yaml_frontmatter() checks frontmatter structure."""

    def test_valid_frontmatter(self, tmp_path, script_dir):
        f = tmp_path / "test.md"
        f.write_text("---\nname: test\n---\nbody\n")
        r = run_install_function(script_dir, f"validate_yaml_frontmatter '{f}'; echo EXIT:$?")
        assert r.returncode == 0
        assert "EXIT:0" in r.stdout

    def test_missing_closing(self, tmp_path, script_dir):
        f = tmp_path / "test.md"
        f.write_text("---\nname: test\nbody no close\n")
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
        content = "---\nname: test\n---\nbody\n"
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
        content = "---\nname: test-agent\ndescription: some agent\ntools: Bash\n---\nbody\n"
        r = run_install_function(script_dir, f"add_model_to_content '{content}' sonnet")
        assert r.returncode == 0
        assert "name: test-agent" in r.stdout
        assert "description: some agent" in r.stdout


class TestClassifyFile:
    """classify_file() sorts files into SILENT or OVERWRITE arrays."""

    def test_new_file_adds_to_silent(self, tmp_path, script_dir):
        """New file (no dest) goes to SILENT arrays."""
        src = tmp_path / "src.md"
        dest = tmp_path / "dest.md"
        src.write_text("---\nname: test\n---\nbody\n")
        r = run_install_function(script_dir, f"""
SILENT_SRC=(); SILENT_DEST=()
OVERWRITE_SRC=(); OVERWRITE_DEST=()
classify_file '{src}' '{dest}'
echo "SILENT:${{#SILENT_SRC[@]}}"
echo "OVERWRITE:${{#OVERWRITE_SRC[@]}}"
""")
        assert r.returncode == 0
        assert "SILENT:1" in r.stdout
        assert "OVERWRITE:0" in r.stdout

    def test_existing_file_adds_to_overwrite(self, tmp_path, script_dir):
        """Existing file goes to OVERWRITE arrays."""
        src = tmp_path / "src.md"
        dest = tmp_path / "dest.md"
        src.write_text("---\nname: test\n---\nbody\n")
        dest.write_text("---\nname: test\n---\nbody\n")
        r = run_install_function(script_dir, f"""
SILENT_SRC=(); SILENT_DEST=()
OVERWRITE_SRC=(); OVERWRITE_DEST=()
classify_file '{src}' '{dest}'
echo "SILENT:${{#SILENT_SRC[@]}}"
echo "OVERWRITE:${{#OVERWRITE_SRC[@]}}"
""")
        assert r.returncode == 0
        assert "SILENT:0" in r.stdout
        assert "OVERWRITE:1" in r.stdout


class TestGetFrontmatterField:
    """_get_frontmatter_field() is the shared implementation behind get_model."""

    def test_field_prefix_collision_does_not_match(self, tmp_path, script_dir):
        """A field named 'model_version' does NOT match when extracting 'model'."""
        f = tmp_path / "test.md"
        f.write_text("---\nname: test\nmodel_version: xyz\nmodel: sonnet\n---\nbody\n")
        r = run_install_function(script_dir, f"_get_frontmatter_field '{f}' model")
        assert r.returncode == 0
        assert r.stdout.strip() == "sonnet"

    def test_field_at_start_of_line_only(self, tmp_path, script_dir):
        """Field name must appear at the start of a line (^ anchor)."""
        f = tmp_path / "test.md"
        f.write_text("---\nname: test\n not_model: xyz\nmodel: haiku\n---\nbody\n")
        r = run_install_function(script_dir, f"_get_frontmatter_field '{f}' model")
        assert r.returncode == 0
        assert r.stdout.strip() == "haiku"

    def test_model_value_with_trailing_whitespace(self, tmp_path, script_dir):
        """Trailing whitespace is stripped from the extracted value."""
        f = tmp_path / "test.md"
        f.write_text("---\nname: test\nmodel: sonnet   \n---\nbody\n")
        r = run_install_function(script_dir, f"get_model '{f}'")
        assert r.returncode == 0
        assert r.stdout.strip() == "sonnet"


class TestHasLissomInstallation:
    """has_lissom_installation() checks whether a target dir has lissom agent files."""

    def test_has_lissom_agents_returns_true(self, tmp_path, script_dir):
        target = tmp_path / "target"
        (target / "agents").mkdir(parents=True)
        (target / "agents" / "lissom-researcher.md").write_text("body\n")
        r = run_install_function(script_dir, f"has_lissom_installation '{target}'; echo EXIT:$?")
        assert r.returncode == 0
        assert "EXIT:0" in r.stdout

    def test_no_lissom_agents_returns_false(self, tmp_path, script_dir):
        target = tmp_path / "target"
        (target / "agents").mkdir(parents=True)
        (target / "agents" / "other.md").write_text("body\n")
        r = run_install_function(script_dir, f"has_lissom_installation '{target}'; echo EXIT:$?")
        assert r.returncode == 0
        assert "EXIT:1" in r.stdout

    def test_missing_directory_returns_false(self, tmp_path, script_dir):
        target = tmp_path / "nonexistent"
        r = run_install_function(script_dir, f"has_lissom_installation '{target}'; echo EXIT:$?")
        assert r.returncode == 0
        assert "EXIT:1" in r.stdout

    def test_no_agents_subdir_returns_false(self, tmp_path, script_dir):
        target = tmp_path / "target"
        target.mkdir()
        r = run_install_function(script_dir, f"has_lissom_installation '{target}'; echo EXIT:$?")
        assert r.returncode == 0
        assert "EXIT:1" in r.stdout

    def test_empty_agents_dir_returns_false(self, tmp_path, script_dir):
        target = tmp_path / "target"
        (target / "agents").mkdir(parents=True)
        r = run_install_function(script_dir, f"has_lissom_installation '{target}'; echo EXIT:$?")
        assert r.returncode == 0
        assert "EXIT:1" in r.stdout

    def test_hidden_lissom_file_not_detected(self, tmp_path, script_dir):
        target = tmp_path / "target"
        (target / "agents").mkdir(parents=True)
        (target / "agents" / ".lissom-researcher.md").write_text("body\n")
        r = run_install_function(script_dir, f"has_lissom_installation '{target}'; echo EXIT:$?")
        assert r.returncode == 0
        assert "EXIT:1" in r.stdout


class TestCollectAgentModels:
    """collect_agent_models() collects agent→model mappings from agent files."""

    def test_collects_models_from_agents(self, tmp_path, script_dir):
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        (agents_dir / "lissom-researcher.md").write_text(
            "---\nname: lissom-researcher\nmodel: opus-4.6\n---\nbody\n"
        )
        (agents_dir / "lissom-planner.md").write_text(
            "---\nname: lissom-planner\nmodel: sonnet\n---\nbody\n"
        )
        r = run_install_function(script_dir, f"""
declare -A MODELS
collect_agent_models '{agents_dir}' MODELS
echo "RESEARCHER:${{MODELS[lissom-researcher]}}"
echo "PLANNER:${{MODELS[lissom-planner]}}"
echo "COUNT:${{#MODELS[@]}}"
""")
        assert r.returncode == 0
        assert "RESEARCHER:opus-4.6" in r.stdout
        assert "PLANNER:sonnet" in r.stdout
        assert "COUNT:2" in r.stdout

    def test_excludes_agents_without_model(self, tmp_path, script_dir):
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        (agents_dir / "lissom-researcher.md").write_text(
            "---\nname: lissom-researcher\nmodel: opus-4.6\n---\nbody\n"
        )
        (agents_dir / "no-model.md").write_text(
            "---\nname: no-model\n---\nbody\n"
        )
        r = run_install_function(script_dir, f"""
declare -A MODELS
collect_agent_models '{agents_dir}' MODELS
echo "COUNT:${{#MODELS[@]}}"
echo "HAS_NO_MODEL:${{MODELS[no-model]:-absent}}"
""")
        assert r.returncode == 0
        assert "COUNT:1" in r.stdout
        assert "HAS_NO_MODEL:absent" in r.stdout

    def test_returns_false_when_no_models_found(self, tmp_path, script_dir):
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        (agents_dir / "no-model.md").write_text(
            "---\nname: no-model\n---\nbody\n"
        )
        r = run_install_function(script_dir, f"""
declare -A MODELS
if collect_agent_models '{agents_dir}' MODELS; then
    echo "FOUND:true"
else
    echo "FOUND:false"
fi
""")
        assert r.returncode == 0
        assert "FOUND:false" in r.stdout

    def test_missing_directory_returns_false(self, tmp_path, script_dir):
        r = run_install_function(script_dir, f"""
declare -A MODELS
if collect_agent_models '{tmp_path}/nonexistent' MODELS; then
    echo "FOUND:true"   
else
    echo "FOUND:false"
fi
""")
        assert r.returncode == 0
        assert "FOUND:false" in r.stdout


class TestConvertAgentGemini:
    """_convert_agent_gemini() converts agent files to Gemini CLI format."""

    def test_valid_frontmatter_with_model(self, tmp_path, script_dir):
        src = tmp_path / "src.md"
        dest = tmp_path / "dest.md"
        src.write_text(
            "---\nname: lissom-researcher\ndescription: fixture\ntools: Bash, Read\n---\nbody\n"
        )
        r = run_install_function(script_dir, f"""
source "$SCRIPT_DIR/scripts/lib/gemini.sh"
_convert_agent_gemini '{src}' '{dest}' "true" ""
cat '{dest}'
""")
        assert r.returncode == 0
        out = r.stdout
        assert "name: lissom-researcher" in out
        assert "description: fixture" in out
        assert "temperature: 0.1" in out
        assert "model: gemini-3-flash-preview" in out
        assert "tools:" in out
        assert "  - run_shell_command" in out
        assert "  - read_file" in out
        assert "body" in out

    def test_valid_frontmatter_with_model_value(self, tmp_path, script_dir):
        src = tmp_path / "src.md"
        dest = tmp_path / "dest.md"
        src.write_text(
            "---\nname: lissom-researcher\ndescription: fixture\ntools: Bash, Read\n---\nbody\n"
        )
        r = run_install_function(script_dir, f"""
source "$SCRIPT_DIR/scripts/lib/gemini.sh"
_convert_agent_gemini '{src}' '{dest}' "true" "gemini-3-pro-preview"
cat '{dest}'
""")
        assert r.returncode == 0
        out = r.stdout
        assert "model: gemini-3-pro-preview" in out

    def test_valid_frontmatter_without_model(self, tmp_path, script_dir):
        src = tmp_path / "src.md"
        dest = tmp_path / "dest.md"
        src.write_text(
            "---\nname: lissom-researcher\ndescription: fixture\ntools: Bash, Read\n---\nbody\n"
        )
        r = run_install_function(script_dir, f"""
source "$SCRIPT_DIR/scripts/lib/gemini.sh"
_convert_agent_gemini '{src}' '{dest}' "false" ""
cat '{dest}'
""")
        assert r.returncode == 0
        out = r.stdout
        assert "model:" not in out

    def test_malformed_frontmatter_returns_error(self, tmp_path, script_dir):
        src = tmp_path / "src.md"
        dest = tmp_path / "dest.md"
        src.write_text(
            "---\nname: lissom-researcher\nbody without closing frontmatter\n"
        )
        r = run_install_function(script_dir, f"""
source "$SCRIPT_DIR/scripts/lib/gemini.sh"
_convert_agent_gemini '{src}' '{dest}' "false" ""
echo "EXIT:$?"
""")
        assert "EXIT:1" in r.stdout

    def test_body_tool_rewrite(self, tmp_path, script_dir):
        src = tmp_path / "src.md"
        dest = tmp_path / "dest.md"
        src.write_text(
            "---\nname: lissom-researcher\ndescription: fixture\ntools: Bash\n---\n"
            "Use tool `Bash` and `Read` and `AskUserQuestion` for this task.\n"
        )
        r = run_install_function(script_dir, f"""
source "$SCRIPT_DIR/scripts/lib/gemini.sh"
_convert_agent_gemini '{src}' '{dest}' "false" ""
cat '{dest}'
""")
        assert r.returncode == 0
        out = r.stdout
        assert "`run_shell_command`" in out
        assert "`read_file`" in out
        assert "`ask_user`" in out
        assert "`Bash`" not in out
        assert "`Read`" not in out
        assert "`AskUserQuestion`" not in out


class TestConvertSkillGemini:
    """_convert_skill_gemini() converts skill files to Gemini CLI format."""

    def test_skill_frontmatter_stripped(self, tmp_path, script_dir):
        src = tmp_path / "src.md"
        dest = tmp_path / "dest.md"
        src.write_text(
            "---\nname: lissom-auto\ndescription: fixture\n"
            "argument-hint: <task_dir>\n---\nbody\n"
        )
        r = run_install_function(script_dir, f"""
source "$SCRIPT_DIR/scripts/lib/gemini.sh"
_convert_skill_gemini '{src}' '{dest}'
cat '{dest}'
""")
        assert r.returncode == 0
        out = r.stdout
        assert "name: lissom-auto" in out
        assert "description: fixture" in out
        assert "version:" not in out
        assert "argument-hint:" not in out
        assert "body" in out

    def test_skill_body_tool_rewrite(self, tmp_path, script_dir):
        src = tmp_path / "src.md"
        dest = tmp_path / "dest.md"
        src.write_text(
            "---\nname: lissom-auto\ndescription: fixture\n---\n"
            "Use tool `Bash` to execute commands. Use `Read` to inspect files.\n"
            "Also try `Grep` for searching and `WebSearch` for web.\n"
        )
        r = run_install_function(script_dir, f"""
source "$SCRIPT_DIR/scripts/lib/gemini.sh"
_convert_skill_gemini '{src}' '{dest}'
cat '{dest}'
""")
        assert r.returncode == 0
        out = r.stdout
        assert "`run_shell_command`" in out
        assert "`read_file`" in out
        assert "`grep_search`" in out
        assert "`google_web_search`" in out
        assert "`Bash`" not in out
        assert "`Read`" not in out
        assert "`Grep`" not in out
        assert "`WebSearch`" not in out

    def test_malformed_skill_frontmatter_returns_error(self, tmp_path, script_dir):
        src = tmp_path / "src.md"
        dest = tmp_path / "dest.md"
        src.write_text(
            "---\nname: lissom-auto\n---no closing---\nbody\n"
        )
        r = run_install_function(script_dir, f"""
source "$SCRIPT_DIR/scripts/lib/gemini.sh"
_convert_skill_gemini '{src}' '{dest}'
echo "EXIT:$?"
""")
        assert "EXIT:1" in r.stdout


class TestConvertOtherGemini:
    """_convert_other_gemini() copies files verbatim."""

    def test_other_file_copied_verbatim(self, tmp_path, script_dir):
        src = tmp_path / "src.md"
        dest = tmp_path / "dest.md"
        src.write_text("some random content\nwith multiple lines\n")
        r = run_install_function(script_dir, f"""
source "$SCRIPT_DIR/scripts/lib/gemini.sh"
_convert_other_gemini '{src}' '{dest}'
cat '{dest}'
""")
        assert r.returncode == 0
        assert r.stdout.strip() == "some random content\nwith multiple lines"

    def test_binary_file_copy(self, tmp_path, script_dir):
        src = tmp_path / "src.bin"
        dest = tmp_path / "dest.bin"
        src.write_bytes(b"binary\x00data\xff")
        r = run_install_function(script_dir, f"""
source "$SCRIPT_DIR/scripts/lib/gemini.sh"
_convert_other_gemini '{src}' '{dest}'
echo "EXIT:$?"
""")
        assert r.returncode == 0
        assert dest.read_bytes() == b"binary\x00data\xff"
