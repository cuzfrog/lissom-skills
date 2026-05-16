"""
Unit tests for the Qwen converter.
"""

from scripts.lib.qwen import QwenConverter

converter = QwenConverter()


class TestQwenConverter:
    def test_convert_agent(self):
        """Agent produces Qwen frontmatter with tools YAML list, excluding AskUserQuestion."""
        content = "---\nname: test-agent\ndescription: test\ntools: Bash, Read, AskUserQuestion\n---\nUse `Bash` and `AskUserQuestion`.\n"
        result = converter.convert_agent(content, "lissom-researcher")
        assert "name: test-agent" in result
        assert "model: qwen3.6-plus" in result
        assert "  - run_shell_command" in result
        assert "  - read_file" in result
        assert "  - question" not in result.split("---")[0]  # not in frontmatter
        assert "`question`" in result  # but present in body
        assert "`Bash`" not in result

    def test_convert_skill(self):
        """Skill strips extra frontmatter fields, rewrites body tools."""
        content = "---\nname: lissom-auto\ndescription: fixture\nversion: 1.0\nargument-hint: <task>\n---\nUse `Grep` to search.\n"
        result = converter.convert_skill(content, "lissom-auto")
        assert "name: lissom-auto" in result
        assert "description: fixture" in result
        assert "version:" not in result
        assert "argument-hint:" not in result
        assert "`grep_search`" in result

    def test_agent_implementer_model(self):
        """lissom-implementer gets qwen3-coder-plus model."""
        content = "---\nname: lissom-implementer\ndescription: impl\ntools: Bash\n---\nbody\n"
        result = converter.convert_agent(content, "lissom-implementer")
        assert "model: qwen3-coder-plus" in result

    def test_agent_args_shifted(self):
        """Qwen agent output has $0 → $1, $1 → $2."""
        content = "---\nname: test\ndescription: test\ntools: Bash\n---\nUse `$0` and `$1`.\n"
        result = converter.convert_agent(content, "lissom-researcher")
        assert "`$1`" in result
        assert "`$2`" in result
        assert "`$0`" not in result

    def test_skill_args_shifted(self):
        """Qwen skill output has $0 → $1."""
        content = "---\nname: test\ndescription: test\n---\nUse `$0`.\n"
        result = converter.convert_skill(content, "lissom-auto")
        assert "`$1`" in result
        assert "`$0`" not in result
