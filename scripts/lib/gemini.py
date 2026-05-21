"""
Gemini CLI format converter.

Converts Claude Code agent/skill .md files to Gemini CLI format.
Ports logic from the backed-up gemini.sh.
"""

from scripts.lib.constants import (
    GEMINI_MODEL_MAP,
    GEMINI_TOOL_NAME_MAPPING,
)
from scripts.lib.converter import Converter
from scripts.lib.frontmatter import parse_frontmatter, rewrite_backtick_tools, shift_args


class GeminiConverter(Converter):
    """Converter for the Gemini CLI target — temperature, model, YAML tools list, arg shift."""

    def convert_agent(self, content: str, agent_name: str) -> str:
        """
        Convert a Claude Code agent .md file to Gemini CLI format.

        Transformations:
        1. Parse frontmatter → extract name, description, tools.
        2. Build new frontmatter:
           - name, description (preserved)
           - temperature: 0.1 (always added, before model)
           - model: <gemini model for agent_name> (only when mapped)
           - tools: as YAML list — for each Claude Code tool, emit "  - <gemini_name>"
             using GEMINI_TOOL_NAME_MAPPING map.
        3. Rewrite body tool names using GEMINI_TOOL_NAME_MAPPING.
        4. Shift $N args forward by 1.

        Returns: fully converted content string.
        """
        fields, body = parse_frontmatter(content)

        name = fields.get("name", agent_name)
        description = fields.get("description", "")
        tools_str = fields.get("tools", "")

        # Parse tools: "Bash, Read, AskUserQuestion" → list
        tool_list = [t.strip() for t in tools_str.split(",") if t.strip()]

        model = GEMINI_MODEL_MAP.get(agent_name)

        lines = ["---"]
        lines.append(f"name: {name}")
        lines.append(f"description: {description}")
        lines.append("temperature: 0.1")
        if model:
            lines.append(f"model: {model}")
        lines.append("tools:")
        for tool in tool_list:
            gemini_tool = GEMINI_TOOL_NAME_MAPPING.get(tool)
            if gemini_tool:
                lines.append(f"  - {gemini_tool}")
        lines.append("---")

        new_content = "\n".join(lines) + "\n"
        if body:
            body = rewrite_backtick_tools(body, GEMINI_TOOL_NAME_MAPPING)
            body = shift_args(body)
            new_content += body

        return new_content

    def convert_skill(self, content: str, skill_name: str) -> str:
        """
        Convert a Claude Code skill SKILL.md to Gemini CLI format.

        Transformations:
        1. Parse frontmatter → extract name, description (required),
           then preserve any additional fields the source may have
           (e.g. disable-model-invocation, argument-hint).
        2. Build new frontmatter with name, description, plus any
           extra fields.  (No temperature, no model, no tools).
        3. Rewrite body tool names (same mapping as agent).
        4. Shift $N args forward by 1.

        Returns: converted content string.
        """
        fields, body = parse_frontmatter(content)

        name = fields.get("name", skill_name)
        description = fields.get("description", "")

        lines = ["---"]
        lines.append(f"name: {name}")
        lines.append(f"description: {description}")

        # Preserve any extra frontmatter fields (e.g. disable-model-invocation)
        known = {"name", "description"}
        for key in fields:
            if key not in known:
                lines.append(f"{key}: {fields[key]}")

        lines.append("---")

        new_content = "\n".join(lines) + "\n"
        if body:
            body = rewrite_backtick_tools(body, GEMINI_TOOL_NAME_MAPPING)
            body = shift_args(body)
            new_content += body

        return new_content

