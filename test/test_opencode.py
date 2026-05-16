"""
Unit tests for the Opencode converter.
"""

from scripts.lib.opencode import OpencodeConverter

converter = OpencodeConverter()


class TestOpenCodeConverter:
    def test_convert_agent_basic(self):
        """Agent with name, description, tools produces correct Opencode frontmatter."""
        content = "---\nname: test-agent\ndescription: A test agent\ntools: Bash, Read\n---\nUse `Bash` for commands.\n"
        result = converter.convert_agent(content, "lissom-researcher")
        assert "mode: subagent" in result
        assert "temperature: 0.1" in result
        assert "permission:" in result
        assert "  bash: allow" in result
        assert "  read: allow" in result
        assert "model: opencode-go/deepseek-v4-pro" in result
        assert "`bash`" in result
        assert "`Bash`" not in result

    def test_convert_skill(self):
        """Skill frontmatter preserved, body tool names rewritten."""
        content = "---\nname: lissom-auto\ndescription: fixture\n---\nUse `Grep` to search.\n"
        result = converter.convert_skill(content, "lissom-auto")
        assert "name: lissom-auto" in result
        assert "description: fixture" in result
        assert "mode: subagent" not in result
        assert "`grep`" in result

    def test_convert_agent_with_ask_user(self):
        """AskUserQuestion in tools → question permission."""
        content = "---\nname: test-agent\ndescription: test\ntools: AskUserQuestion\n---\nUse `AskUserQuestion`.\n"
        result = converter.convert_agent(content, "lissom-reviewer")
        assert "  question: allow" in result
        assert "`question`" in result

    def test_convert_agent_model_for_implementer(self):
        """lissom-implementer gets opencode-go/deepseek-v4-flash."""
        content = "---\nname: lissom-implementer\ndescription: impl\ntools: Bash\n---\nbody\n"
        result = converter.convert_agent(content, "lissom-implementer")
        assert "model: opencode-go/deepseek-v4-flash" in result


class TestOpenCodeArgsNotShifted:
    def test_opencode_agent_args_not_shifted(self):
        """Opencode agent output keeps $0 unchanged."""
        content = "---\nname: test\ndescription: test\ntools: Bash\n---\nUse `$0`.\n"
        result = converter.convert_agent(content, "lissom-researcher")
        assert "`$0`" in result

    def test_opencode_skill_args_not_shifted(self):
        """Opencode skill output keeps $0 unchanged."""
        content = "---\nname: test\ndescription: test\n---\nUse `$0`.\n"
        result = converter.convert_skill(content, "lissom-auto")
        assert "`$0`" in result
