"""
Claude Code format converter.

Claude Code is the canonical source format for lissom agents and skills,
so conversion is minimal: inject the model field into agent frontmatter
and pass skills through verbatim.
"""

from scripts.lib.constants import CLAUDE_MODEL_MAP
from scripts.lib.converter import Converter
from scripts.lib.frontmatter import inject_field


class ClaudeCodeConverter(Converter):
    """Converter for the Claude Code target — injects model, passes skills."""

    def convert_agent(self, content: str, agent_name: str) -> str:
        """
        Convert a source agent .md file to Claude Code format.

        The source is already in Claude Code format — the only transformation
        is injecting a default ``model:`` field into the frontmatter using the
        per-agent model map (CLAUDE_MODEL_MAP).  Agents not in the map fall
        back to ``sonnet``.

        Returns: content with model field injected.
        """
        model = CLAUDE_MODEL_MAP.get(agent_name, "sonnet")
        try:
            output = inject_field(content, "model", model, after_field="tools")
        except ValueError:
            output = inject_field(content, "model", model)
        return output

    def convert_skill(self, content: str, skill_name: str) -> str:
        """
        Convert a source skill SKILL.md to Claude Code format.

        The source is already in Claude Code format — pass through verbatim.

        Returns: content unchanged.
        """
        return content

