"""
Unit tests for opencode-format functions (scripts/lib/opencode.sh).
Tests frontmatter conversion, tool name mapping, and permission block generation.
"""
import subprocess
from pathlib import Path
import pytest


def run_opencode_function(script_dir: Path, func_name: str, *args) -> str:
    """
    Execute an opencode bash function and return its output.
    
    Args:
        script_dir: Path to lissom-skills root directory
        func_name: Name of the function to call (e.g., "opencode_parse_tools")
        *args: Arguments to pass to the function
    
    Returns:
        stdout from the function
    """
    bash_code = f"""
    source "{script_dir}/scripts/lib/constants.sh"
    source "{script_dir}/scripts/lib/opencode.sh"
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


class TestOpencodeParseTools:
    """Test opencode_parse_tools function"""
    
    def test_single_tool(self, script_dir: Path):
        """Parse tools line with single tool"""
        output = run_opencode_function(script_dir, "opencode_parse_tools", "tools: Bash")
        assert "Bash" in output
    
    def test_multiple_tools(self, script_dir: Path):
        """Parse tools line with multiple tools"""
        tools_input = "tools: Bash, Read, Write, Edit"
        output = run_opencode_function(script_dir, "opencode_parse_tools", tools_input)
        for tool in ["Bash", "Read", "Write", "Edit"]:
            assert tool in output
    
    def test_tools_with_spaces(self, script_dir: Path):
        """Parse tools line handles spaces correctly"""
        tools_input = "tools: Bash , Read , Write"
        output = run_opencode_function(script_dir, "opencode_parse_tools", tools_input)
        for tool in ["Bash", "Read", "Write"]:
            assert tool in output


class TestOpencodePermissionsFromTools:
    """Test opencode_permissions_from_tools function"""
    
    def test_bash_tool(self, script_dir: Path):
        """Generate permission block for Bash tool"""
        output = run_opencode_function(script_dir, "opencode_permissions_from_tools", "Bash")
        assert "permission:" in output
        assert "bash: allow" in output
    
    def test_multiple_tools(self, script_dir: Path):
        """Generate permission block for multiple tools"""
        output = run_opencode_function(script_dir, "opencode_permissions_from_tools", "Bash Read Write")
        assert "bash: allow" in output
        assert "read: allow" in output
        assert "write: allow" in output
    
    def test_asquserquestion_mapping(self, script_dir: Path):
        """AskUserQuestion maps to 'question' permission"""
        output = run_opencode_function(script_dir, "opencode_permissions_from_tools", "AskUserQuestion")
        assert "question: allow" in output


class TestOpencodeRewriteBodyTools:
    """Test opencode_rewrite_body_tools function"""
    
    def test_bash_conversion(self, script_dir: Path):
        """Test Bash tool name replacement in body"""
        bash_code = f"""
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/opencode.sh"
        content="Use tool \\`Bash\\` to run commands"
        opencode_rewrite_body_tools "$content"
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
        source "{script_dir}/scripts/lib/opencode.sh"
        content="Ask using \\`AskUserQuestion\\` tool"
        opencode_rewrite_body_tools "$content"
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
        source "{script_dir}/scripts/lib/opencode.sh"
        content="Use \\`Agent\\` or \\`TodoWrite\\` for other tasks"
        opencode_rewrite_body_tools "$content"
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
        source "{script_dir}/scripts/lib/opencode.sh"
        content="Use \\`Read\\` here and \\`Read\\` there"
        opencode_rewrite_body_tools "$content"
        """
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True,
            text=True,
        )
        count = result.stdout.count("`read`")
        assert count == 2


class TestOpencodeFormatFrontmatter:
    """Test opencode_format_frontmatter function"""
    
    def test_preserves_name_version_description(self, script_dir: Path):
        """Name, description, and version comment are preserved; no version in YAML"""
        bash_code = f"""
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/opencode.sh"
        content="<!-- version: 2026-01-01T00:00:00Z -->
---
name: test-agent
description: Test agent
tools: Read, Write
---"
        opencode_format_frontmatter "$content" "test-agent" "false"
        """
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True,
            text=True,
        )
        assert "<!-- version: 2026-01-01T00:00:00Z -->" in result.stdout
        assert "name: test-agent" in result.stdout
        assert "description: Test agent" in result.stdout
        # Version must NOT appear as a YAML frontmatter field
        fm_section = result.stdout.split("---")[1]
        assert "version:" not in fm_section
    
    def test_adds_mode_and_temperature(self, script_dir: Path):
        """Adds mode: subagent and temperature: 0.1"""
        bash_code = f"""
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/opencode.sh"
        content="---
name: test-agent
version: 2026-01-01T00:00:00Z
description: Test
tools: Read
---"
        opencode_format_frontmatter "$content" "test-agent" "false"
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
        source "{script_dir}/scripts/lib/opencode.sh"
        content="---
name: test-agent
version: 2026-01-01T00:00:00Z
description: Test
tools: Bash, Read, Write
---"
        opencode_format_frontmatter "$content" "test-agent" "false"
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
        source "{script_dir}/scripts/lib/opencode.sh"
        content="---
name: test-agent
version: 2026-01-01T00:00:00Z
description: Test
tools: Read, Write
---"
        opencode_format_frontmatter "$content" "test-agent" "false"
        """
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True,
            text=True,
        )
        fm_lines = result.stdout.split("---")
        assert len(fm_lines) >= 3
        fm_section = fm_lines[1]
        assert "tools:" not in fm_section
    
    def test_includes_model_when_requested(self, script_dir: Path):
        """Model field is included when include_model=true"""
        bash_code = f"""
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/opencode.sh"
        content="---
name: lissom-researcher
version: 2026-01-01T00:00:00Z
description: Test
tools: Read
---"
        opencode_format_frontmatter "$content" "lissom-researcher" "true"
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
        source "{script_dir}/scripts/lib/opencode.sh"
        content="---
name: test-agent
version: 2026-01-01T00:00:00Z
description: Test
tools: Read
---"
        opencode_format_frontmatter "$content" "test-agent" "false"
        """
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True,
            text=True,
        )
        fm_lines = result.stdout.split("---")
        fm_section = fm_lines[1]
        assert "model:" not in fm_section
    
    def test_field_ordering(self, script_dir: Path):
        """Fields appear in correct order: version_comment, ---, name, description, mode, temperature, permission"""
        bash_code = f"""
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/opencode.sh"
        content="<!-- version: 2026-01-01T00:00:00Z -->
---
name: test-agent
description: Test description
tools: Read, Write
---"
        opencode_format_frontmatter "$content" "test-agent" "false"
        """
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True,
            text=True,
        )
        # Result should start with version comment, then ---, then YAML frontmatter
        stdout = result.stdout
        assert stdout.startswith("<!-- version: 2026-01-01T00:00:00Z -->")
        # After version comment, next line should be ---
        lines = stdout.split("\n")
        assert lines[1] == "---"
        
        fm_lines = stdout.split("---")
        fm_section = fm_lines[1].strip().split("\n")
        
        fm_lines = [line for line in fm_section if line.strip()]
        
        name_idx = next((i for i, line in enumerate(fm_lines) if line.startswith("name:")), -1)
        desc_idx = next((i for i, line in enumerate(fm_lines) if line.startswith("description:")), -1)
        mode_idx = next((i for i, line in enumerate(fm_lines) if line.startswith("mode:")), -1)
        temp_idx = next((i for i, line in enumerate(fm_lines) if line.startswith("temperature:")), -1)
        perm_idx = next((i for i, line in enumerate(fm_lines) if line.startswith("permission:")), -1)
        
        assert name_idx < desc_idx < mode_idx < temp_idx < perm_idx
        # Version must NOT appear in YAML frontmatter
        assert "version:" not in fm_section


class TestOpencodeFormatAgentFile:
    """opencode_format_agent_file() — end-to-end agent file conversion."""

    def test_full_conversion_without_model(self, script_dir: Path):
        """Agent frontmatter and body are both converted."""
        bash_code = f"""
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/opencode.sh"
        content="---
name: test-agent
version: 2026-01-01T00:00:00Z
description: A test agent
tools: Bash, Read, AskUserQuestion
---
Use tool \\`Bash\\` and \\`Read\\` to work.
Ask the user with \\`AskUserQuestion\\` when needed.
"
        opencode_format_agent_file "$content" "test-agent" "false"
        """
        result = subprocess.run(["bash", "-c", bash_code], capture_output=True, text=True)
        assert result.returncode == 0
        out = result.stdout

        assert "name: test-agent" in out
        assert "mode: subagent" in out
        assert "temperature: 0.1" in out
        assert "permission:" in out
        assert "bash: allow" in out
        assert "read: allow" in out
        assert "question: allow" in out
        assert "tools:" not in out.split("---")[1]

        assert "model:" not in out.split("---")[1]

        assert "`bash`" in out
        assert "`read`" in out
        assert "`question`" in out
        assert "`Bash`" not in out
        assert "`AskUserQuestion`" not in out

    def test_full_conversion_with_model(self, script_dir: Path):
        """Agent frontmatter and body are converted; model field included."""
        bash_code = f"""
        source "{script_dir}/scripts/lib/constants.sh"
        source "{script_dir}/scripts/lib/opencode.sh"
        content="---
name: lissom-researcher
version: 2026-01-01T00:00:00Z
description: Research agent
tools: Read, WebFetch
---
Research with \\`Read\\` and \\`WebFetch\\`.
"
        opencode_format_agent_file "$content" "lissom-researcher" "true"
        """
        result = subprocess.run(["bash", "-c", bash_code], capture_output=True, text=True)
        assert result.returncode == 0
        out = result.stdout

        assert "model: opencode-go/deepseek-v4-pro" in out

        assert "`read`" in out
        assert "`webfetch`" in out
        assert "`WebFetch`" not in out
        assert "`Read`" not in out
