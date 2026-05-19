"""
Unit tests for the Gemini converter.
"""

from scripts.lib.gemini import GeminiConverter

converter = GeminiConverter()


class TestGeminiConverter:
    def test_convert_agent(self):
        """Agent produces Gemini frontmatter with temperature, including ask_user."""
        content = "---\nname: test-agent\ndescription: test\ntools: Bash, Edit, WebSearch, AskUserQuestion\n---\nUse `Bash` and `AskUserQuestion`.\n"
        result = converter.convert_agent(content, "lissom-researcher")
        assert "temperature: 0.1" in result
        assert "model: gemini-3-pro-preview" in result
        assert "  - run_shell_command" in result
        assert "  - replace" in result
        assert "  - google_web_search" in result
        assert "  - ask_user" in result
        assert "`run_shell_command`" in result
        assert "`ask_user`" in result

    def test_convert_skill(self):
        """Skill preserves extra frontmatter fields, no temperature/model."""
        content = "---\nname: lissom-auto\ndescription: fixture\nversion: 1.0\n---\nUse `Grep` to search.\n"
        result = converter.convert_skill(content, "lissom-auto")
        assert "name: lissom-auto" in result
        assert "description: fixture" in result
        assert "version: 1.0" in result
        assert "temperature:" not in result
        assert "model:" not in result
        assert "`grep_search`" in result

    def test_temperature_present(self):
        """temperature: 0.1 present in agent but not skill."""
        agent_content = "---\nname: test\ndescription: test\ntools: Bash\n---\nbody\n"
        skill_content = "---\nname: test\ndescription: test\n---\nbody\n"
        agent_result = converter.convert_agent(agent_content, "lissom-researcher")
        skill_result = converter.convert_skill(skill_content, "lissom-test")
        assert "temperature: 0.1" in agent_result
        assert "temperature:" not in skill_result

    def test_agent_args_shifted(self):
        """Gemini agent output has $0 → $1."""
        content = "---\nname: test\ndescription: test\ntools: Bash\n---\nUse `$0` and `$1`.\n"
        result = converter.convert_agent(content, "lissom-researcher")
        assert "`$1`" in result
        assert "`$2`" in result
        assert "`$0`" not in result

    def test_skill_args_shifted(self):
        """Gemini skill output has $0 → $1."""
        content = "---\nname: test\ndescription: test\n---\nUse `$0`.\n"
        result = converter.convert_skill(content, "lissom-auto")
        assert "`$1`" in result
        assert "`$0`" not in result
