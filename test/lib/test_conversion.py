"""
Unit tests for conversion functions (scripts/lib/conversion.sh).
Tests frontmatter conversion, tool name mapping, and permission block generation.
"""
import subprocess
import tempfile
from pathlib import Path
import pytest


def run_conversion_function(script_dir: Path, func_name: str, *args) -> str:
    """
    Execute a bash conversion function and return its output.
    
    Args:
        script_dir: Path to lissom-skills root directory
        func_name: Name of the function to call (e.g., "parse_tools_line")
        *args: Arguments to pass to the function
    
    Returns:
        stdout from the function
    """
    bash_code = f"""
    source "{script_dir}/scripts/lib/constants.sh"
    source "{script_dir}/scripts/lib/conversion.sh"
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


class TestParseToolsLine:
    """Test parse_tools_line function"""
    
    def test_single_tool(self, script_dir: Path):
        """Parse tools line with single tool"""
        output = run_conversion_function(script_dir, "parse_tools_line", "tools: Bash")
        assert "Bash" in output
    
    def test_multiple_tools(self, script_dir: Path):
        """Parse tools line with multiple tools"""
        tools_input = "tools: Bash, Read, Write, Edit"
        output = run_conversion_function(script_dir, "parse_tools_line", tools_input)
        for tool in ["Bash", "Read", "Write", "Edit"]:
            assert tool in output
    
    def test_tools_with_spaces(self, script_dir: Path):
        """Parse tools line handles spaces correctly"""
        tools_input = "tools: Bash , Read , Write"
        output = run_conversion_function(script_dir, "parse_tools_line", tools_input)
        for tool in ["Bash", "Read", "Write"]:
            assert tool in output


class TestToolsToPermissions:
    """Test tools_to_permissions function"""
    
    def test_bash_tool(self, script_dir: Path):
        """Generate permission block for Bash tool"""
        output = run_conversion_function(script_dir, "tools_to_permissions", "Bash")
        assert "permission:" in output
        assert "bash: allow" in output
    
    def test_multiple_tools(self, script_dir: Path):
        """Generate permission block for multiple tools"""
        output = run_conversion_function(script_dir, "tools_to_permissions", "Bash Read Write")
        assert "bash: allow" in output
        assert "read: allow" in output
        assert "write: allow" in output
    
    def test_asquserquestion_mapping(self, script_dir: Path):
        """AskUserQuestion maps to 'question' permission"""
        output = run_conversion_function(script_dir, "tools_to_permissions", "AskUserQuestion")
        assert "question: allow" in output


class TestConvertToolNamesInBody:
    """Test convert_tool_names_in_body function"""
    
    def test_bash_conversion(self, script_dir: Path):
        """Test Bash tool name replacement in body"""
        bash_code = f"""
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/conversion.sh"
        content="Use tool \`Bash\` to run commands"
        convert_tool_names_in_body "$content"
        """
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True,
            text=True,
        )
        assert "`bash`" in result.stdout
    
    def test_asquserquestion_conversion(self, script_dir: Path):
        """Test AskUserQuestion tool name replacement"""
        bash_code = f"""
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/conversion.sh"
        content="Ask using \`AskUserQuestion\` tool"
        convert_tool_names_in_body "$content"
        """
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True,
            text=True,
        )
        assert "`question`" in result.stdout
    
    def test_unmapped_tools_pass_through(self, script_dir: Path):
        """Unmapped tool names like Agent pass through unchanged"""
        bash_code = f"""
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/conversion.sh"
        content="Use \`Agent\` or \`TodoWrite\` for other tasks"
        convert_tool_names_in_body "$content"
        """
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True,
            text=True,
        )
        assert "`Agent`" in result.stdout
        assert "`TodoWrite`" in result.stdout
    
    def test_multiple_occurrences(self, script_dir: Path):
        """Multiple occurrences of same tool are all converted"""
        bash_code = f"""
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/conversion.sh"
        content="Use \`Read\` here and \`Read\` there"
        convert_tool_names_in_body "$content"
        """
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True,
            text=True,
        )
        # Count occurrences of `read`
        count = result.stdout.count("`read`")
        assert count == 2


class TestConvertAgentFrontmatter:
    """Test convert_agent_frontmatter function"""
    
    def test_preserves_name_version_description(self, script_dir: Path):
        """Name, version, and description fields are preserved"""
        bash_code = f"""
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/conversion.sh"
        content="---
name: test-agent
version: 2026-01-01T00:00:00Z
description: Test agent
tools: Read, Write
---
body"
        convert_agent_frontmatter "$content" "test-agent" "false"
        """
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True,
            text=True,
        )
        assert "name: test-agent" in result.stdout
        assert "version: 2026-01-01T00:00:00Z" in result.stdout
        assert "description: Test agent" in result.stdout
    
    def test_adds_mode_and_temperature(self, script_dir: Path):
        """Adds mode: subagent and temperature: 0.1"""
        bash_code = f"""
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/conversion.sh"
        content="---
name: test-agent
version: 2026-01-01T00:00:00Z
description: Test
tools: Read
---
body"
        convert_agent_frontmatter "$content" "test-agent" "false"
        """
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True,
            text=True,
        )
        assert "mode: subagent" in result.stdout
        assert "temperature: 0.1" in result.stdout
    
    def test_adds_permission_block_from_tools(self, script_dir: Path):
        """Permission block is generated from tools line"""
        bash_code = f"""
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/conversion.sh"
        content="---
name: test-agent
version: 2026-01-01T00:00:00Z
description: Test
tools: Bash, Read, Write
---
body"
        convert_agent_frontmatter "$content" "test-agent" "false"
        """
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True,
            text=True,
        )
        assert "permission:" in result.stdout
        assert "bash: allow" in result.stdout
        assert "read: allow" in result.stdout
        assert "write: allow" in result.stdout
    
    def test_removes_tools_line(self, script_dir: Path):
        """Original tools: line is removed"""
        bash_code = f"""
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/conversion.sh"
        content="---
name: test-agent
version: 2026-01-01T00:00:00Z
description: Test
tools: Read, Write
---
body"
        convert_agent_frontmatter "$content" "test-agent" "false"
        """
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True,
            text=True,
        )
        # The original frontmatter should not contain "tools: Read"
        fm_lines = result.stdout.split("---")
        assert len(fm_lines) >= 3
        fm_section = fm_lines[1]
        assert "tools:" not in fm_section
    
    def test_includes_model_when_requested(self, script_dir: Path):
        """Model field is included when include_model=true"""
        bash_code = f"""
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/conversion.sh"
        content="---
name: lissom-researcher
version: 2026-01-01T00:00:00Z
description: Test
tools: Read
---
body"
        convert_agent_frontmatter "$content" "lissom-researcher" "true"
        """
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True,
            text=True,
        )
        assert "model: opencode-go/" in result.stdout
    
    def test_omits_model_when_not_requested(self, script_dir: Path):
        """Model field is omitted when include_model=false"""
        bash_code = f"""
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/conversion.sh"
        content="---
name: test-agent
version: 2026-01-01T00:00:00Z
description: Test
tools: Read
---
body"
        convert_agent_frontmatter "$content" "test-agent" "false"
        """
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True,
            text=True,
        )
        # Model should not be in the output
        fm_lines = result.stdout.split("---")
        fm_section = fm_lines[1]
        assert "model:" not in fm_section
    
    def test_field_ordering(self, script_dir: Path):
        """Fields appear in correct order: name, description, version, mode, temperature, permission"""
        bash_code = f"""
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/conversion.sh"
        content="---
name: test-agent
version: 2026-01-01T00:00:00Z
description: Test description
tools: Read, Write
---
body"
        convert_agent_frontmatter "$content" "test-agent" "false"
        """
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True,
            text=True,
        )
        fm_lines = result.stdout.split("---")
        fm_section = fm_lines[1].strip().split("\n")
        
        # Extract lines (skip empty ones)
        fm_lines = [line for line in fm_section if line.strip()]
        
        # Check that name comes before version
        name_idx = next((i for i, line in enumerate(fm_lines) if line.startswith("name:")), -1)
        desc_idx = next((i for i, line in enumerate(fm_lines) if line.startswith("description:")), -1)
        version_idx = next((i for i, line in enumerate(fm_lines) if line.startswith("version:")), -1)
        mode_idx = next((i for i, line in enumerate(fm_lines) if line.startswith("mode:")), -1)
        temp_idx = next((i for i, line in enumerate(fm_lines) if line.startswith("temperature:")), -1)
        perm_idx = next((i for i, line in enumerate(fm_lines) if line.startswith("permission:")), -1)
        
        # Verify ordering
        assert name_idx < desc_idx < version_idx < mode_idx < temp_idx < perm_idx


class TestConvertAgentFile:
    """convert_agent_file() wrapper — end-to-end agent file conversion."""

    def test_full_conversion_without_model(self, script_dir: Path):
        """Agent frontmatter and body are both converted."""
        bash_code = f"""
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/conversion.sh"
        content="---
name: test-agent
version: 2026-01-01T00:00:00Z
description: A test agent
tools: Bash, Read, AskUserQuestion
---
Use tool \`Bash\` and \`Read\` to work.
Ask the user with \`AskUserQuestion\` when needed.
"
        convert_agent_file "$content" "test-agent" "false"
        """
        result = subprocess.run(["bash", "-c", bash_code], capture_output=True, text=True)
        assert result.returncode == 0
        out = result.stdout

        # Frontmatter converted
        assert "name: test-agent" in out
        assert "mode: subagent" in out
        assert "temperature: 0.1" in out
        assert "permission:" in out
        assert "bash: allow" in out
        assert "read: allow" in out
        assert "question: allow" in out
        assert "tools:" not in out.split("---")[1]  # removed from frontmatter

        # Model not included
        assert "model:" not in out.split("---")[1]

        # Body tool names rewritten
        assert "`bash`" in out
        assert "`read`" in out
        assert "`question`" in out
        assert "`Bash`" not in out
        assert "`AskUserQuestion`" not in out

    def test_full_conversion_with_model(self, script_dir: Path):
        """Agent frontmatter and body are converted; model field included."""
        bash_code = f"""
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/conversion.sh"
        content="---
name: lissom-researcher
version: 2026-01-01T00:00:00Z
description: Research agent
tools: Read, WebFetch
---
Research with \`Read\` and \`WebFetch\`.
"
        convert_agent_file "$content" "lissom-researcher" "true"
        """
        result = subprocess.run(["bash", "-c", bash_code], capture_output=True, text=True)
        assert result.returncode == 0
        out = result.stdout

        # Model field present in frontmatter
        assert "model: opencode-go/deepseek-v4-pro" in out

        # Body tool names rewritten
        assert "`read`" in out
        assert "`webfetch`" in out
        assert "`WebFetch`" not in out
        assert "`Read`" not in out

