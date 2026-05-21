"""
Pi CLI format converter.

Converts Claude Code agent/skill .md files to Pi format.
"""

from scripts.lib.constants import PI_TOOL_NAME_MAPPING
from scripts.lib.converter import Converter
from scripts.lib.frontmatter import parse_frontmatter, rewrite_backtick_tools


class PiConverter(Converter):
    """Converter for the Pi target — rewrites tool names, strips model/temperature."""

    def convert_agent(self, content: str, agent_name: str) -> str:
        """
        Convert a Claude Code agent .md file to Pi format.

        Transformations:
        1. Parse frontmatter → extract name, description, tools.
        2. Build new frontmatter:
           - name, description (preserved)
           - tools: field preserved with tool names converted to Pi --tools
             flag names via PI_TOOL_NAME_MAPPING
             (the LLM reads the frontmatter naturally at runtime)
           - No model, no temperature (subagent inherits Pi defaults).
        3. Rewrite body tool names using PI_TOOL_NAME_MAPPING.
        4. $0, $1, etc. argument references stay unchanged.

        Returns: fully converted content string.
        """
        fields, body = parse_frontmatter(content)

        name = fields.get("name", agent_name)
        description = fields.get("description", "")

        mapping = PI_TOOL_NAME_MAPPING

        # Convert tools field to Pi --tools flag names so the LLM can read them from frontmatter
        tools_raw = fields.get("tools", "")
        if tools_raw:
            pi_tools = []
            for t in tools_raw.split(","):
                t = t.strip()
                if t in mapping:
                    mapped = mapping[t]
                    # Some entries (Glob) map to comma-separated multiple flags
                    pi_tools.extend(p.strip() for p in mapped.split(","))
                else:
                    pi_tools.append(t)
            tools_str = ", ".join(pi_tools)
        else:
            tools_str = ""

        lines = ["---"]
        lines.append(f"name: {name}")
        lines.append(f"description: {description}")
        if tools_str:
            lines.append(f"tools: {tools_str}")
        lines.append("---")

        new_content = "\n".join(lines) + "\n"
        if body:
            body = rewrite_backtick_tools(body, mapping)
            new_content += body

        return new_content

    def convert_skill(self, content: str, skill_name: str) -> str:
        """
        Convert a Claude Code skill SKILL.md to Pi format.

        With tintinweb/pi-subagents, the Agent tool is exposed as `Agent`,
        matching Claude Code's naming — no tool name rewriting needed.

        Frontmatter preserved as-is.
        Other tool names (Bash, Read, etc.) remain unchanged
        because skills instruct the main agent, which already knows
        its tool names.

        Returns: content unchanged.
        """
        return content

