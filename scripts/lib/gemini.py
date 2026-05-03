"""
Gemini CLI format converter.

Converts Claude Code agent/skill .md files to Gemini CLI format.
Ports logic from the backed-up gemini.sh.
"""

import re

from scripts.lib.constants import (
    CLAUDE_TO_GEMINI_BODY,
    CLAUDE_TO_GEMINI_TOOL,
    GEMINI_MODEL_MAP,
)
from scripts.lib.frontmatter import parse_frontmatter


def _rewrite_body_tools(content: str) -> str:
    """
    Replace backtick-wrapped Claude Code tool names with Gemini CLI equivalents.
    Uses CLAUDE_TO_GEMINI_BODY from constants.py.
    """
    keys = list(CLAUDE_TO_GEMINI_BODY.keys())
    pattern = r'`(' + '|'.join(re.escape(k) for k in keys) + r')`'

    def _replacer(m: re.Match) -> str:
        return f'`{CLAUDE_TO_GEMINI_BODY[m.group(1)]}`'

    return re.sub(pattern, _replacer, content)


def convert_agent(content: str, agent_name: str) -> str:
    """
    Convert a Claude Code agent .md file to Gemini CLI format.

    Transformations:
    1. Parse frontmatter → extract name, description, tools.
    2. Build new frontmatter:
       - name, description (preserved)
       - temperature: 0.1 (always added, before model)
       - model: <gemini model for agent_name> (always injected)
       - tools: as YAML list — for each Claude Code tool, emit "  - <gemini_name>"
         using CLAUDE_TO_GEMINI_TOOL map. AskUserQuestion IS included (→ ask_user).
    3. Rewrite body tool names using CLAUDE_TO_GEMINI_BODY map.

    Returns: fully converted content string.
    """
    fields, body = parse_frontmatter(content)

    name = fields.get("name", agent_name)
    description = fields.get("description", "")
    tools_str = fields.get("tools", "")

    # Parse tools: "Bash, Read, AskUserQuestion" → list
    tool_list = [t.strip() for t in tools_str.split(",") if t.strip()]

    model = GEMINI_MODEL_MAP.get(agent_name, "gemini-3-flash-preview")

    lines = ["---"]
    lines.append(f"name: {name}")
    lines.append(f"description: {description}")
    lines.append("temperature: 0.1")
    lines.append(f"model: {model}")
    lines.append("tools:")
    for tool in tool_list:
        gemini_tool = CLAUDE_TO_GEMINI_TOOL.get(tool)
        if gemini_tool:
            lines.append(f"  - {gemini_tool}")
    lines.append("---")

    new_content = "\n".join(lines) + "\n"
    if body:
        body = _rewrite_body_tools(body)
        new_content += body

    return new_content


def convert_skill(content: str, skill_name: str) -> str:
    """
    Convert a Claude Code skill SKILL.md to Gemini CLI format.

    Transformations:
    1. Parse frontmatter → extract name, description only (drop all other fields).
    2. Build new frontmatter with only name and description.
       (No temperature, no model, no tools).
    3. Rewrite body tool names (same mapping as agent).

    Returns: converted content string.
    """
    fields, body = parse_frontmatter(content)

    name = fields.get("name", skill_name)
    description = fields.get("description", "")

    lines = ["---"]
    lines.append(f"name: {name}")
    lines.append(f"description: {description}")
    lines.append("---")

    new_content = "\n".join(lines) + "\n"
    if body:
        body = _rewrite_body_tools(body)
        new_content += body

    return new_content
