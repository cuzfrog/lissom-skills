"""
Unit tests for qwen-format functions (scripts/lib/qwen.sh).
Tests frontmatter conversion, tool name mapping, and skill frontmatter stripping.
"""
import subprocess
from pathlib import Path
import pytest


def run_qwen_function(script_dir: Path, func_name: str, *args) -> str:
    """
    Execute a qwen bash function and return its output.

    Args:
        script_dir: Path to lissom-skills root directory
        func_name: Name of the function to call (e.g., "qwen_format_agent_frontmatter")
        *args: Arguments to pass to the function

    Returns:
        stdout from the function
    """
    bash_code = f"""
    source "{script_dir}/scripts/lib/constants.sh"
    source "{script_dir}/scripts/lib/qwen.sh"
    {func_name} {' '.join(f'"{arg}"' for arg in args)}
    """
    result = subprocess.run(
        ["bash", "-c", bash_code],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Function {func_name} failed: {result.stderr}")
    return result.stdout


class TestQwenFormatAgentFrontmatter:
    """Test qwen_format_agent_frontmatter function"""

    def test_preserves_name_and_description(self, script_dir: Path):
        """Name and description fields are preserved; no version: in YAML"""
        bash_code = f'''
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/qwen.sh"
        content="<!-- version: 2026-01-01T00:00:00Z -->
---
name: test-agent
description: Test agent
tools: Read, Write
---"
        qwen_format_agent_frontmatter "$content" "test-agent" "false"
        '''
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "<!-- version: 2026-01-01T00:00:00Z -->" in result.stdout
        assert "name: test-agent" in result.stdout
        assert "description: Test agent" in result.stdout
        # No "version:" line should appear in the YAML section
        fm_section = result.stdout.split("---")[1]
        assert "version:" not in fm_section

    def test_includes_model_when_requested(self, script_dir: Path):
        """Model field is included when include_model=true"""
        bash_code = f'''
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/qwen.sh"
        content="---
name: lissom-researcher
version: 2026-01-01T00:00:00Z
description: Test
tools: Read
---"
        qwen_format_agent_frontmatter "$content" "lissom-researcher" "true"
        '''
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "model: qwen3.6-plus" in result.stdout

    def test_omits_model_when_not_requested(self, script_dir: Path):
        """Model field is omitted when include_model=false"""
        bash_code = f'''
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/qwen.sh"
        content="---
name: test-agent
version: 2026-01-01T00:00:00Z
description: Test
tools: Read
---"
        qwen_format_agent_frontmatter "$content" "test-agent" "false"
        '''
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        fm_lines = result.stdout.split("---")
        fm_section = fm_lines[1]
        assert "model:" not in fm_section

    def test_model_override_takes_precedence(self, script_dir: Path):
        """model_override is used when provided, even if include_model=false"""
        bash_code = f'''
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/qwen.sh"
        content="---
name: test-agent
version: 2026-01-01T00:00:00Z
description: Test
tools: Read
---"
        qwen_format_agent_frontmatter "$content" "test-agent" "false" "qwen-custom-model"
        '''
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "model: qwen-custom-model" in result.stdout

    def test_tools_as_yaml_list(self, script_dir: Path):
        """Tools are output as YAML list with snake_case names"""
        bash_code = f'''
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/qwen.sh"
        content="---
name: test-agent
version: 2026-01-01T00:00:00Z
description: Test
tools: Bash, Read, Write
---"
        qwen_format_agent_frontmatter "$content" "test-agent" "false"
        '''
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        fm_lines = result.stdout.split("---")
        fm_section = fm_lines[1]
        assert "tools:" in fm_section
        assert "  - run_shell_command" in fm_section
        assert "  - read_file" in fm_section
        assert "  - write_file" in fm_section
        # Original tools: line should no longer appear
        assert "tools: Bash, Read, Write" not in fm_section

    def test_askuserquestion_excluded_from_tools(self, script_dir: Path):
        """AskUserQuestion is excluded from the Qwen tools list"""
        bash_code = f'''
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/qwen.sh"
        content="---
name: test-agent
version: 2026-01-01T00:00:00Z
description: Test
tools: Bash, AskUserQuestion, Read
---"
        qwen_format_agent_frontmatter "$content" "test-agent" "false"
        '''
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        fm_section = result.stdout.split("---")[1]
        # Question tool is not in CLAUDE_TO_QWEN_TOOL, so it should be absent
        assert "question" not in fm_section
        # But the mapped tools should still be there
        assert "  - run_shell_command" in fm_section
        assert "  - read_file" in fm_section

    def test_unknown_tool_skipped(self, script_dir: Path):
        """Unknown/unmapped tool names are silently skipped"""
        bash_code = f'''
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/qwen.sh"
        content="---
name: test-agent
version: 2026-01-01T00:00:00Z
description: Test
tools: Bash, NonExistentTool, Read
---"
        qwen_format_agent_frontmatter "$content" "test-agent" "false"
        '''
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        fm_section = result.stdout.split("---")[1]
        assert "  - run_shell_command" in fm_section
        assert "  - read_file" in fm_section
        assert "NonExistentTool" not in fm_section

    def test_field_ordering(self, script_dir: Path):
        """Fields appear in correct order: comment, ---, name, description, model, tools"""
        bash_code = f'''
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/qwen.sh"
        content="<!-- version: 2026-01-01T00:00:00Z -->
---
name: test-agent
description: Test description
tools: Bash, Read
---"
        qwen_format_agent_frontmatter "$content" "test-agent" "true"
        '''
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        # Comment should appear before the first ---
        assert result.stdout.startswith("<!-- version: 2026-01-01T00:00:00Z -->")
        # No "version:" line in YAML section
        fm_section = result.stdout.split("---")[1]
        assert "version:" not in fm_section
        # YAML fields order: name, description, model, tools
        fm_lines = [line for line in fm_section.strip().split("\n") if line.strip()]
        name_idx = next((i for i, line in enumerate(fm_lines) if line.startswith("name:")), -1)
        desc_idx = next((i for i, line in enumerate(fm_lines) if line.startswith("description:")), -1)
        model_idx = next((i for i, line in enumerate(fm_lines) if line.startswith("model:")), -1)
        tools_idx = next((i for i, line in enumerate(fm_lines) if line.startswith("tools:")), -1)
        assert name_idx < desc_idx < model_idx
        assert model_idx < tools_idx

    def test_no_tools_line(self, script_dir: Path):
        """When there is no tools: line, no tools block is emitted"""
        bash_code = f'''
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/qwen.sh"
        content="---
name: test-agent
version: 2026-01-01T00:00:00Z
description: Test
---"
        qwen_format_agent_frontmatter "$content" "test-agent" "false"
        '''
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        fm_section = result.stdout.split("---")[1]
        assert "tools:" not in fm_section

    def test_missing_required_fields_error(self, script_dir: Path):
        """Missing required fields produce error on stderr and return non-zero"""
        bash_code = f'''
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/qwen.sh"
        content="---
tools: Bash
---"
        qwen_format_agent_frontmatter "$content" "test-agent" "false"
        '''
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "Error: Missing required frontmatter fields" in result.stderr

    def test_preserves_body_text(self, script_dir: Path):
        """Body text after closing --- is preserved"""
        bash_code = f'''
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/qwen.sh"
        content="---
name: test-agent
version: 2026-01-01T00:00:00Z
description: Test
tools: Read
---
This is the body content.
It should be preserved after conversion."
        qwen_format_agent_frontmatter "$content" "test-agent" "false"
        '''
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "This is the body content." in result.stdout
        assert "It should be preserved after conversion." in result.stdout

    def test_rejects_missing_name(self, script_dir: Path):
        """Missing name field produces error on stderr"""
        bash_code = f'''
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/qwen.sh"
        content="---
version: 2026-01-01T00:00:00Z
description: Test
tools: Read
---"
        qwen_format_agent_frontmatter "$content" "test-agent" "false"
        '''
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True, text=True
        )
        assert result.returncode != 0
        assert "Missing required frontmatter fields" in result.stderr

    def test_rejects_missing_description(self, script_dir: Path):
        """Missing description field produces error on stderr"""
        bash_code = f'''
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/qwen.sh"
        content="---
name: test-agent
version: 2026-01-01T00:00:00Z
tools: Read
---"
        qwen_format_agent_frontmatter "$content" "test-agent" "false"
        '''
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True, text=True
        )
        assert result.returncode != 0
        assert "Missing required frontmatter fields" in result.stderr

    def test_missing_version_is_not_an_error(self, script_dir: Path):
        """Missing version (no comment, no YAML field) is now accepted"""
        bash_code = f'''
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/qwen.sh"
        content="---
name: test-agent
description: Test
tools: Read
---"
        qwen_format_agent_frontmatter "$content" "test-agent" "false"
        '''
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "name: test-agent" in result.stdout
        assert "description: Test" in result.stdout
        # No "version:" YAML field should appear in the YAML section
        assert "version:" not in result.stdout.split("---")[1]

    def test_tool_name_mapping(self, script_dir: Path):
        """Each Claude tool name maps to its Qwen equivalent in frontmatter"""
        bash_code = f'''
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/qwen.sh"
        content="---
name: test-agent
version: 2026-01-01T00:00:00Z
description: Test
tools: Bash, Read, Write, Edit, Glob, Grep, WebFetch, WebSearch
---"
        qwen_format_agent_frontmatter "$content" "test-agent" "false"
        '''
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        fm_section = result.stdout.split("---")[1]
        assert "  - run_shell_command" in fm_section
        assert "  - read_file" in fm_section
        assert "  - write_file" in fm_section
        assert "  - edit" in fm_section
        assert "  - glob" in fm_section
        assert "  - grep_search" in fm_section
        assert "  - web_fetch" in fm_section
        assert "  - web_search" in fm_section

    def test_all_agents_conversion(self, script_dir: Path):
        """Test with each agent in AGENTS array to verify mapping completeness"""
        bash_code = f'''
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/qwen.sh"
        for agent in "${{AGENTS[@]}}"; do
            content="---
name: $agent
version: 2026-01-01T00:00:00Z
description: $agent description
tools: Bash, Read
---"
            if ! output=$(qwen_format_agent_frontmatter "$content" "$agent" "true" 2>&1); then
                echo "FAIL: $agent"
                exit 1
            fi
            echo "$output"
        done
        '''
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        for agent in ["lissom-implementer", "lissom-planner", "lissom-researcher", "lissom-reviewer", "lissom-specs-reviewer"]:
            assert f"name: {agent}" in result.stdout

    def test_missing_closing_frontmatter(self, script_dir: Path):
        """Missing closing --- produces non-zero exit"""
        bash_code = f'''
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/qwen.sh"
        content="---
name: test-agent
version: 2026-01-01T00:00:00Z
description: Test
tools: Read
This body content should not appear"
        qwen_format_agent_frontmatter "$content" "test-agent" "false"
        '''
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True, text=True
        )
        assert result.returncode != 0
        assert "Missing closing --- delimiter" in result.stderr
        # Without closing ---, the function cannot properly delimit the body
        assert "This body content should not appear" not in result.stdout

    def test_empty_tools_line(self, script_dir: Path):
        """Empty tools: line produces no tools block in output"""
        bash_code = f'''
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/qwen.sh"
        content="---
name: test-agent
version: 2026-01-01T00:00:00Z
description: Test
tools:
---"
        qwen_format_agent_frontmatter "$content" "test-agent" "false"
        '''
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        fm_section = result.stdout.split("---")[1]
        # Empty tools line means no YAML tools list is emitted
        assert "  -" not in fm_section


class TestQwenFormatSkillFrontmatter:
    """Test qwen_format_skill_frontmatter function"""

    def test_preserves_name_and_description(self, script_dir: Path):
        """Name and description fields are preserved"""
        bash_code = f'''
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/qwen.sh"
        content="---
name: test-skill
version: 2026-01-01T00:00:00Z
description: A test skill
argument-hint: <task_dir>
---"
        qwen_format_skill_frontmatter "$content"
        '''
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "name: test-skill" in result.stdout
        assert "description: A test skill" in result.stdout

    def test_strips_extra_frontmatter_fields(self, script_dir: Path):
        """Extra fields like version, argument-hint are stripped"""
        bash_code = f'''
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/qwen.sh"
        content="---
name: test-skill
version: 2026-01-01T00:00:00Z
description: A test skill
argument-hint: <task_dir>
---"
        qwen_format_skill_frontmatter "$content"
        '''
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        fm_section = result.stdout.split("---")[1]
        assert "version:" not in fm_section
        assert "argument-hint:" not in fm_section

    def test_missing_name_error(self, script_dir: Path):
        """Missing name field produces error"""
        bash_code = f'''
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/qwen.sh"
        content="---
description: A test skill
---"
        qwen_format_skill_frontmatter "$content"
        '''
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "Error: Missing required frontmatter fields" in result.stderr

    def test_preserves_body_after_frontmatter(self, script_dir: Path):
        """Body text after closing --- is preserved"""
        bash_code = f'''
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/qwen.sh"
        content="---
name: test-skill
description: A test skill
---

## Process

Do something useful."
        qwen_format_skill_frontmatter "$content"
        '''
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "## Process" in result.stdout
        assert "Do something useful." in result.stdout

    def test_strips_version(self, script_dir: Path):
        """Version field is stripped from skill frontmatter"""
        bash_code = f'''
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/qwen.sh"
        content="---
name: test-skill
version: 2026-01-01T00:00:00Z
description: A test skill
---"
        qwen_format_skill_frontmatter "$content"
        '''
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        fm_section = result.stdout.split("---")[1]
        assert "version:" not in fm_section

    def test_strips_argument_hint(self, script_dir: Path):
        """argument-hint field is stripped from skill frontmatter"""
        bash_code = f'''
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/qwen.sh"
        content="---
name: test-skill
description: A test skill
argument-hint: <task_dir>
---"
        qwen_format_skill_frontmatter "$content"
        '''
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        fm_section = result.stdout.split("---")[1]
        assert "argument-hint:" not in fm_section

    def test_strips_other_fields(self, script_dir: Path):
        """Any other non-standard field is stripped from skill frontmatter"""
        bash_code = f'''
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/qwen.sh"
        content="---
name: test-skill
description: A test skill
custom-field: should-be-stripped
another-unknown: also-stripped
---"
        qwen_format_skill_frontmatter "$content"
        '''
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        fm_section = result.stdout.split("---")[1]
        assert "custom-field:" not in fm_section
        assert "another-unknown:" not in fm_section

    def test_rejects_missing_description(self, script_dir: Path):
        """Missing description produces error for skill frontmatter"""
        bash_code = f'''
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/qwen.sh"
        content="---
name: test-skill
---"
        qwen_format_skill_frontmatter "$content"
        '''
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True, text=True
        )
        assert result.returncode != 0
        assert "Missing required frontmatter fields" in result.stderr

    def test_missing_closing_frontmatter(self, script_dir: Path):
        """Missing closing --- produces non-zero exit with error message"""
        bash_code = f'''
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/qwen.sh"
        content="---
name: test-skill
description: A test skill
This body content should not appear"
        qwen_format_skill_frontmatter "$content"
        '''
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True, text=True
        )
        assert result.returncode != 0
        assert "Missing closing --- delimiter" in result.stderr
        assert "This body content should not appear" not in result.stdout


class TestQwenRewriteBodyTools:
    """Test qwen_rewrite_body_tools function"""

    def test_bash_conversion(self, script_dir: Path):
        """Bash converts to run_shell_command"""
        bash_code = f'''
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/qwen.sh"
        content="Use tool \\`Bash\\` to run commands"
        qwen_rewrite_body_tools "$content"
        '''
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True,
            text=True,
        )
        assert "`run_shell_command`" in result.stdout

    def test_askuserquestion_conversion(self, script_dir: Path):
        """AskUserQuestion converts to question"""
        bash_code = f'''
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/qwen.sh"
        content="Ask using \\`AskUserQuestion\\` tool"
        qwen_rewrite_body_tools "$content"
        '''
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True,
            text=True,
        )
        assert "`question`" in result.stdout

    def test_all_tool_conversions(self, script_dir: Path):
        """All known tool names are converted"""
        bash_code = f'''
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/qwen.sh"
        content="Tools: \\`Bash\\` \\`Read\\` \\`Write\\` \\`Edit\\` \\`Glob\\` \\`Grep\\` \\`WebFetch\\` \\`WebSearch\\` \\`AskUserQuestion\\`"
        qwen_rewrite_body_tools "$content"
        '''
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True,
            text=True,
        )
        out = result.stdout
        assert "`run_shell_command`" in out
        assert "`read_file`" in out
        assert "`write_file`" in out
        assert "`edit`" in out
        assert "`glob`" in out
        assert "`grep_search`" in out
        assert "`web_fetch`" in out
        assert "`web_search`" in out
        assert "`question`" in out
        # Original names should not appear
        assert "`Bash`" not in out
        assert "`AskUserQuestion`" not in out

    def test_unmapped_tools_pass_through(self, script_dir: Path):
        """Unmapped tool names like Agent pass through unchanged"""
        bash_code = f'''
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/qwen.sh"
        content="Use \\`Agent\\` or \\`TodoWrite\\` for other tasks"
        qwen_rewrite_body_tools "$content"
        '''
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True,
            text=True,
        )
        assert "`Agent`" in result.stdout
        assert "`TodoWrite`" in result.stdout

    def test_multiple_occurrences(self, script_dir: Path):
        """Multiple occurrences of same tool are all converted"""
        bash_code = f'''
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/qwen.sh"
        content="Use \\`Read\\` here and \\`Read\\` there"
        qwen_rewrite_body_tools "$content"
        '''
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True,
            text=True,
        )
        count = result.stdout.count("`read_file`")
        assert count == 2

    def test_non_backtick_text_unchanged(self, script_dir: Path):
        """Text outside backticks is not affected by tool rewriting"""
        bash_code = f'''
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/qwen.sh"
        content="This is plain text with no tool references.
The word Bash without backticks should stay as is.
Some inline \\`Bash\\` should convert though."
        qwen_rewrite_body_tools "$content"
        '''
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True, text=True
        )
        out = result.stdout
        # "Bash" without backticks stays as "Bash"
        assert "Bash without backticks" in out
        # "`Bash`" gets converted to "`run_shell_command`"
        assert "`run_shell_command`" in out


class TestQwenFormatAgentFile:
    """qwen_format_agent_file() — end-to-end agent file conversion."""

    def test_full_conversion_without_model(self, script_dir: Path):
        """Agent frontmatter and body are both converted."""
        bash_code = f'''
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/qwen.sh"
        content="<!-- version: 2026-01-01T00:00:00Z -->
---
name: test-agent
description: A test agent
tools: Bash, Read, AskUserQuestion
---
Use tool \\`Bash\\` and \\`Read\\` to work.
Ask the user with \\`AskUserQuestion\\` when needed.
"
        qwen_format_agent_file "$content" "test-agent" "false"
        '''
        result = subprocess.run(["bash", "-c", bash_code], capture_output=True, text=True)
        assert result.returncode == 0
        out = result.stdout

        # Version comment preserved before ---, no version: in YAML
        assert "<!-- version: 2026-01-01T00:00:00Z -->" in out
        assert "name: test-agent" in out
        assert "description: A test agent" in out
        assert "version:" not in out.split("---")[1]

        # Verify model is absent when not requested
        assert "model:" not in out.split("---")[1]

        # Tools as YAML list — AskUserQuestion excluded
        fm_section = out.split("---")[1]
        assert "tools:" in fm_section
        assert "  - run_shell_command" in fm_section
        assert "  - read_file" in fm_section
        assert "question" not in fm_section

        # Body tool names rewritten
        assert "`run_shell_command`" in out
        assert "`read_file`" in out
        assert "`question`" in out
        assert "`Bash`" not in out
        assert "`AskUserQuestion`" not in out

    def test_full_conversion_with_model(self, script_dir: Path):
        """Agent frontmatter and body are converted; model field included."""
        bash_code = f'''
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/qwen.sh"
        content="<!-- version: 2026-01-01T00:00:00Z -->
---
name: lissom-researcher
description: Research agent
tools: Read, WebFetch
---
Research with \\`Read\\` and \\`WebFetch\\`.
"
        qwen_format_agent_file "$content" "lissom-researcher" "true"
        '''
        result = subprocess.run(["bash", "-c", bash_code], capture_output=True, text=True)
        assert result.returncode == 0
        out = result.stdout

        assert "<!-- version: 2026-01-01T00:00:00Z -->" in out
        assert "version:" not in out.split("---")[1]
        assert "model: qwen3.6-plus" in out
        assert "  - read_file" in out
        assert "  - web_fetch" in out
        assert "`read_file`" in out
        assert "`web_fetch`" in out
        assert "`Read`" not in out
        assert "`WebFetch`" not in out

    def test_full_conversion_with_model_override(self, script_dir: Path):
        """model_override takes precedence over include_model."""
        bash_code = f'''
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/qwen.sh"
        content="<!-- version: 2026-01-01T00:00:00Z -->
---
name: lissom-researcher
description: Research agent
tools: Read
---
Research with \\`Read\\`.
"
        qwen_format_agent_file "$content" "lissom-researcher" "false" "qwen-custom-model"
        '''
        result = subprocess.run(["bash", "-c", bash_code], capture_output=True, text=True)
        assert result.returncode == 0
        out = result.stdout

        assert "<!-- version: 2026-01-01T00:00:00Z -->" in out
        assert "version:" not in out.split("---")[1]
        assert "model: qwen-custom-model" in out

    def test_all_agents(self, script_dir: Path):
        """End-to-end test with each standard agent source file"""
        bash_code = f'''
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/qwen.sh"
        for agent in "${{AGENTS[@]}}"; do
            content="<!-- version: 2026-01-01T00:00:00Z -->
---
name: $agent
description: $agent description
tools: Bash, Read, Write, Edit, Glob, Grep, WebFetch, WebSearch, AskUserQuestion
---
Use \\`Bash\\` and \\`Read\\` for the agent \\`$agent\\`."
            if ! output=$(qwen_format_agent_file "$content" "$agent" "true" 2>&1); then
                echo "FAIL: $agent"
                exit 1
            fi
            echo "$output"
        done
        '''
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        out = result.stdout
        for agent in ["lissom-implementer", "lissom-planner", "lissom-researcher", "lissom-reviewer", "lissom-specs-reviewer"]:
            assert f"name: {agent}" in out
        assert "<!-- version: 2026-01-01T00:00:00Z -->" in out
        assert "`run_shell_command`" in out
        assert "`read_file`" in out
