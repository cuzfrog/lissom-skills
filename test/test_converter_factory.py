"""
Tests for converter_factory.py — registry and get_converter.
"""

import pytest
from scripts.lib.converter import Converter
from scripts.lib.converter_factory import get_converter


class TestGetConverter:
    """get_converter returns the correct Converter instance per shortname."""

    def test_claude(self):
        conv = get_converter("claude")
        assert isinstance(conv, Converter)
        assert type(conv).__name__ == "ClaudeCodeConverter"

    def test_opencode(self):
        conv = get_converter("opencode")
        assert isinstance(conv, Converter)
        assert type(conv).__name__ == "OpencodeConverter"

    def test_qwen(self):
        conv = get_converter("qwen")
        assert isinstance(conv, Converter)
        assert type(conv).__name__ == "QwenConverter"

    def test_gemini(self):
        conv = get_converter("gemini")
        assert isinstance(conv, Converter)
        assert type(conv).__name__ == "GeminiConverter"

    def test_pi(self):
        conv = get_converter("pi")
        assert isinstance(conv, Converter)
        assert type(conv).__name__ == "PiConverter"

    def test_unknown_shortname_raises_keyerror(self):
        with pytest.raises(KeyError):
            get_converter("nonexistent")

    def test_empty_string_raises_keyerror(self):
        with pytest.raises(KeyError):
            get_converter("")

    def test_registry_has_exactly_five_entries(self):
        """Ensure no converter is accidentally added or removed."""
        from scripts.lib.converter_factory import _registry
        assert len(_registry) == 5
        assert set(_registry.keys()) == {"claude", "opencode", "qwen", "gemini", "pi"}

    def test_each_converter_can_convert(self):
        """Smoke test — every converter can process a minimal agent/skill."""
        agent_content = "---\nname: test-agent\ndescription: test\ntools: Bash\n---\nbody\n"
        skill_content = "---\nname: test-skill\ndescription: test\n---\nbody\n"

        for shortname in ("claude", "opencode", "qwen", "gemini", "pi"):
            conv = get_converter(shortname)
            agent_out = conv.convert_agent(agent_content, "lissom-test")
            skill_out = conv.convert_skill(skill_content, "lissom-test")
            assert "test-agent" in agent_out or "test" in agent_out
            assert "test-skill" in skill_out or "test" in skill_out
