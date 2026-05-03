"""
Qwen Code format converter.

Converts Claude Code agent/skill .md files to Qwen Code format.
Ports logic from the backed-up qwen.sh.
"""

import re

from scripts.lib.constants import (
    CLAUDE_TO_QWEN_BODY,
    CLAUDE_TO_QWEN_TOOL,
    QWEN_MODEL_MAP,
)
from scripts.lib.frontmatter import parse_frontmatter


def _rewrite_body_tools(content: str) -> str:
    """
    Replace backtick-wrapped Claude Code tool names with Qwen Code equivalents.
    Uses CLAUDE_TO_QWEN_BODY from constants.py.
    """
    keys = list(CLAUDE_TO_QWEN_BODY.keys())
    pattern = r'`(' + '|'.join(re.escape(k) for k in keys) + r')`'

    def _replacer(m: re.Match) -> str:
        return f'`{CLAUDE_TO_QWEN_BODY[m.group(1)]}`'

    return re.sub(pattern, _replacer, content)


def convert_agent(content: str, agent_name: str) -> str:
    """
    Convert a Claude Code agent .md file to Qwen Code format.

    Transformations:
    1. Parse frontmatter → extract name, description, tools.
    2. Build new frontmatter:
       - name, description (preserved)
       - model: <qwen model for agent_name> (always injected)
       - tools: as YAML list — for each Claude Code tool, emit "  - <qwen_name>"
         using CLAUDE_TO_QWEN_TOOL map. Skip AskUserQuestion (NOT in map).
    3. Rewrite body tool names using CLAUDE_TO_QWEN_BODY map.

    Returns: fully converted content string.
    """
    fields, body = parse_frontmatter(content)

    name = fields.get("name", agent_name)
    description = fields.get("description", "")
    tools_str = fields.get("tools", "")

    # Parse tools: "Bash, Read, AskUserQuestion" → list
    tool_list = [t.strip() for t in tools_str.split(",") if t.strip()]

    model = QWEN_MODEL_MAP.get(agent_name, "qwen3.6-plus")

    lines = ["---"]
    lines.append(f"name: {name}")
    lines.append(f"description: {description}")
    lines.append(f"model: {model}")
    lines.append("tools:")
    for tool in tool_list:
        qwen_tool = CLAUDE_TO_QWEN_TOOL.get(tool)
        if qwen_tool:
            lines.append(f"  - {qwen_tool}")
    lines.append("---")

    new_content = "\n".join(lines) + "\n"
    if body:
        body = _rewrite_body_tools(body)
        new_content += body

    return new_content


def convert_skill(content: str, skill_name: str) -> str:
    """
    Convert a Claude Code skill SKILL.md to Qwen Code format.

    Transformations:
    1. Parse frontmatter → extract name, description only (drop all other fields).
    2. Build new frontmatter with only name and description.
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
