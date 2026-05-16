"""
Unit tests for the Claude Code converter.
"""

from scripts.lib.claude_code import ClaudeCodeConverter

converter = ClaudeCodeConverter()


class TestClaudeCodeConverter:
    def test_convert_agent_injects_model(self):
        """Model field injected after tools."""
        content = "---\nname: test-agent\ndescription: test\ntools: Bash\n---\nbody\n"
        result = converter.convert_agent(content, "lissom-researcher")
        assert "model: opus-4.6" in result
        lines = result.splitlines()
        tools_idx = next(i for i, l in enumerate(lines) if l.startswith("tools:"))
        model_idx = next(i for i, l in enumerate(lines) if l.startswith("model:"))
        assert model_idx == tools_idx + 1

    def test_convert_agent_no_tools(self):
        """Model injected before closing --- when no tools field."""
        content = "---\nname: test-agent\ndescription: test\n---\nbody\n"
        result = converter.convert_agent(content, "lissom-researcher")
        assert "model: opus-4.6" in result

    def test_convert_agent_implementer_gets_sonnet(self):
        """lissom-implementer gets sonnet."""
        content = "---\nname: lissom-implementer\ndescription: impl\ntools: Bash\n---\nbody\n"
        result = converter.convert_agent(content, "lissom-implementer")
        assert "model: sonnet" in result

    def test_convert_agent_unknown_agent_no_model(self):
        """Unknown agent name gets no model field injected."""
        content = "---\nname: unknown\ndescription: unknown\ntools: Bash\n---\nbody\n"
        result = converter.convert_agent(content, "unknown-agent")
        assert "model:" not in result
        assert result == content  # passed through unchanged

    def test_convert_skill_passes_through(self):
        """Skill content returned verbatim."""
        content = "---\nname: test-skill\ndescription: test\n---\nbody\n"
        result = converter.convert_skill(content, "lissom-auto")
        assert result == content

    def test_convert_skill_with_extra_fields(self):
        """Extra frontmatter fields in skill are preserved."""
        content = "---\nname: test\ndescription: test\nargument-hint: <task>\nversion: 1.0\n---\nbody\n"
        result = converter.convert_skill(content, "lissom-auto")
        assert "argument-hint:" in result
        assert "version:" in result

    def test_convert_agent_preserves_existing_model(self):
        """Existing model field is replaced, not duplicated."""
        content = "---\nname: test-agent\ndescription: test\nmodel: old\ntools: Bash\n---\nbody\n"
        result = converter.convert_agent(content, "lissom-researcher")
        assert "model: opus-4.6" in result
        assert "model: old" not in result
        assert result.count("model:") == 1
