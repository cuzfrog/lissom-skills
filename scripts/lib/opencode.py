"""
Opencode format converter.

Converts Claude Code agent/skill .md files to Opencode format.
Ports logic from the backed-up opencode.sh.
"""

import re

from scripts.lib.constants import (
    OPENCODE_MODEL_MAP,
    TOOL_NAME_MAPPING,
    TOOL_TO_PERMISSION,
)
from scripts.lib.frontmatter import parse_frontmatter


def _rewrite_body_tools(content: str) -> str:
    """
    Replace backtick-wrapped Claude Code tool names with Opencode equivalents.
    Uses TOOL_NAME_MAPPING from constants.py.
    Only matches tool names inside backticks: `Bash`, `Read`, etc.
    """
    keys = list(TOOL_NAME_MAPPING.keys())
    pattern = r'`(' + '|'.join(re.escape(k) for k in keys) + r')`'

    def _replacer(m: re.Match) -> str:
        return f'`{TOOL_NAME_MAPPING[m.group(1)]}`'

    return re.sub(pattern, _replacer, content)


def convert_agent(content: str, agent_name: str) -> str:
    """
    Convert a Claude Code agent .md file to Opencode format.

    Transformations:
    1. Parse frontmatter → extract name, description, tools.
    2. Build new frontmatter:
       - name, description (preserved)
       - mode: subagent (always added)
       - model: <opencode model for agent_name> (always injected)
       - temperature: 0.1 (always added)
       - permission: block — map each Claude Code tool to its Opencode
         permission key with "allow" value (2-space indent).
    3. Rewrite body tool names: `Bash` → `bash`, `Read` → `read`, etc.

    Returns: fully converted content string.
    """
    fields, body = parse_frontmatter(content)

    name = fields.get("name", agent_name)
    description = fields.get("description", "")
    tools_str = fields.get("tools", "")

    # Parse tools: "Bash, Read, AskUserQuestion" → list
    tool_list = [t.strip() for t in tools_str.split(",") if t.strip()]

    model = OPENCODE_MODEL_MAP.get(agent_name, "opencode-go/qwen3.6-plus")

    lines = ["---"]
    lines.append(f"name: {name}")
    lines.append(f"description: {description}")
    lines.append("mode: subagent")
    lines.append(f"model: {model}")
    lines.append("temperature: 0.1")
    lines.append("permission:")
    for tool in tool_list:
        perm = TOOL_TO_PERMISSION.get(tool, tool.lower())
        lines.append(f"  {perm}: allow")
    lines.append("---")

    new_content = "\n".join(lines) + "\n"
    if body:
        # Rewrite body tool names
        body = _rewrite_body_tools(body)
        new_content += body

    return new_content


def convert_skill(content: str, skill_name: str) -> str:
    """
    Convert a Claude Code skill SKILL.md to Opencode format.

    Transformations:
    - Rewrite body tool names only (same mapping as agent).
    - Frontmatter is NOT restructured (preserved as-is).

    Returns: converted content string.
    """
    # Only rewrite body tool names — frontmatter preserved
    return _rewrite_body_tools(content)
