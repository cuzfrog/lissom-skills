"""
Abstract base class and factory for target-format converters.

Defines the contract that every format converter (claude_code, opencode,
qwen, gemini, pi) must fulfil so that build.py can dispatch through a
uniform interface.

Usage::

    from scripts.lib.converter_factory import get_converter

    conv = get_converter("pi")
    agent_out = conv.convert_agent(source, agent_name)
    skill_out = conv.convert_skill(source, skill_name)
"""

from abc import ABC, abstractmethod


class Converter(ABC):
    """Interface for converting lissom source files to a target format."""

    @abstractmethod
    def convert_agent(self, content: str, agent_name: str) -> str:
        """Convert a source agent .md file to the target format.

        Args:
            content: Raw file content (Claude Code source format).
            agent_name: Basename (without .md) of the agent, used to
                        look up per-agent configuration (e.g. model).

        Returns:
            Converted agent content string.
        """
        ...

    @abstractmethod
    def convert_skill(self, content: str, skill_name: str) -> str:
        """Convert a source skill SKILL.md to the target format.

        Args:
            content: Raw file content (Claude Code source format).
            skill_name: Skill directory name, used for any per-skill
                        configuration if needed.

        Returns:
            Converted skill content string.
        """
        ...



