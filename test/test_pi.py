"""
Unit tests for the Pi converter.
"""

from scripts.lib.pi import PiConverter

converter = PiConverter()


class TestPiConverter:
    def test_convert_skill_preserves_agent_tool_name(self):
        """`Agent` preserved in body text (pi-subagents exposes Agent natively)."""
        content = "---\nname: lissom-auto\ndescription: fixture\n---\nUse `Agent` to delegate work.\n"
        result = converter.convert_skill(content, "lissom-auto")
        assert "`Agent`" in result
        assert "`lissom-agent`" not in result

    def test_convert_skill_preserves_frontmatter(self):
        """name, description, argument-hint unchanged."""
        content = "---\nname: lissom-auto\ndescription: fixture\nargument-hint: <task_id>\n---\nUse `Agent`.\n"
        result = converter.convert_skill(content, "lissom-auto")
        assert "name: lissom-auto" in result
        assert "description: fixture" in result
        assert "argument-hint: <task_id>" in result

    def test_convert_skill_other_tools_unchanged(self):
        """AskUserQuestion, Bash remain unchanged in skill body (skills instruct main agent)."""
        content = "---\nname: test\ndescription: test\n---\nUse `AskUserQuestion` and `Bash`.\n"
        result = converter.convert_skill(content, "test")
        assert "`AskUserQuestion`" in result
        assert "`Bash`" in result

    def test_convert_agent_rewrites_body_tools(self):
        """`Bash` → `bash`, `Read` → `read`, etc. in body text."""
        content = "---\nname: test-agent\ndescription: test\ntools: Bash, Read, Edit, Glob, Grep\n---\nUse `Bash` and `Read`.\n"
        result = converter.convert_agent(content, "lissom-researcher")
        assert "`bash`" in result
        assert "`read`" in result
        assert "`Bash`" not in result

    def test_convert_agent_preserves_tools_frontmatter(self):
        """tools: field preserved with converted tool names."""
        content = "---\nname: test-agent\ndescription: test\ntools: Bash, Read\n---\nbody\n"
        result = converter.convert_agent(content, "lissom-researcher")
        assert "tools: bash, read" in result
        assert "Bash" not in result.split("---")[1]  # tools in frontmatter are lowercase

    def test_convert_agent_preserves_name_description(self):
        """name and description kept."""
        content = "---\nname: lissom-researcher\ndescription: A test agent\ntools: Bash\n---\nbody\n"
        result = converter.convert_agent(content, "lissom-researcher")
        assert "name: lissom-researcher" in result
        assert "description: A test agent" in result

    def test_convert_agent_no_model_injection(self):
        """No model: field in output."""
        content = "---\nname: test-agent\ndescription: test\ntools: Bash\n---\nbody\n"
        result = converter.convert_agent(content, "lissom-researcher")
        assert "model:" not in result

    def test_convert_agent_args_not_shifted(self):
        """$0, $1 stay unchanged (unlike Qwen/Gemini)."""
        content = "---\nname: test\ndescription: test\ntools: Bash\n---\nUse `$0` and `$1`.\n"
        result = converter.convert_agent(content, "lissom-researcher")
        assert "`$0`" in result
        assert "`$1`" in result
