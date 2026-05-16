"""
Pi CLI format converter.

Converts Claude Code agent/skill .md files to Pi format.
"""

from scripts.lib.constants import CLAUDE_TO_PI_BODY
from scripts.lib.frontmatter import parse_frontmatter, rewrite_backtick_tools


def convert_agent(content: str, agent_name: str) -> str:
    """
    Convert a Claude Code agent .md file to Pi format.

    Transformations:
    1. Parse frontmatter → extract name, description, tools.
    2. Build new frontmatter:
       - name, description (preserved)
       - tools: field stripped (tools are passed via CLI --tools)
       - No model, no temperature (subagent inherits Pi defaults).
    3. Rewrite body tool names using CLAUDE_TO_PI_BODY map.
    4. $0, $1, etc. argument references stay unchanged.

    Returns: fully converted content string.
    """
    fields, body = parse_frontmatter(content)

    name = fields.get("name", agent_name)
    description = fields.get("description", "")

    lines = ["---"]
    lines.append(f"name: {name}")
    lines.append(f"description: {description}")
    lines.append("---")

    new_content = "\n".join(lines) + "\n"
    if body:
        body = rewrite_backtick_tools(body, CLAUDE_TO_PI_BODY)
        new_content += body

    return new_content


def convert_skill(content: str, skill_name: str) -> str:
    """
    Convert a Claude Code skill SKILL.md to Pi format.

    Transformations:
    - Replace `Agent` → `lissom-agent` in body text.
    - Frontmatter preserved as-is.
    - Other tool names (Bash, Read, etc.) remain unchanged
      because skills instruct the main agent, which already knows
      its tool names.

    Returns: converted content string.
    """
    # Only rewrite `Agent` → `lissom-agent`
    # All other backtick tool names stay unchanged
    return rewrite_backtick_tools(content, {"Agent": "lissom-agent"})
