"""
Verify that tool call references in agents/ and skills/ follow the format
specified in Guidelines.md: 'use Tool `<ToolName>` to'
"""
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# Canonical tool names from https://code.claude.com/docs/en/tools-reference
KNOWN_TOOLS = frozenset({
    "Agent",
    "AskUserQuestion",
    "Bash",
    "CronCreate",
    "CronDelete",
    "CronList",
    "Edit",
    "EnterPlanMode",
    "EnterWorktree",
    "ExitPlanMode",
    "ExitWorktree",
    "Glob",
    "Grep",
    "ListMcpResourcesTool",
    "LSP",
    "Monitor",
    "NotebookEdit",
    "PowerShell",
    "Read",
    "ReadMcpResourceTool",
    "SendMessage",
    "Skill",
    "TaskCreate",
    "TaskGet",
    "TaskList",
    "TaskOutput",
    "TaskStop",
    "TaskUpdate",
    "TeamCreate",
    "TeamDelete",
    "TodoWrite",
    "ToolSearch",
    "WebFetch",
    "WebSearch",
    "Write",
})


def _discover_files():
    files = []
    files.extend(REPO_ROOT.glob("agents/*.md"))
    files.extend(REPO_ROOT.glob("skills/*/SKILL.md"))
    return sorted(files)


def _get_body(content: str) -> str:
    """Return content after YAML frontmatter."""
    parts = content.split("---", 2)
    if len(parts) < 3:
        return content
    return parts[2]


def _find_violations(filepath: Path) -> list[tuple[int, str]]:
    """Find tool call references not matching: ``[Uu]se Tool `<Name>``` pattern.

    Guideline: 'use Tool `<ToolName>` to'
    Valid:   "Use Tool `AskUserQuestion` to interview user."
    Invalid: "Use Tool AskUserQuestion to interview user."  (no backticks)
    """
    body = _get_body(filepath.read_text())

    violations: list[tuple[int, str]] = []
    for line_num, line in enumerate(body.splitlines(), start=1):
        for m in re.finditer(r"\b[Uu]se\s+Tool\s+", line):
            pos = m.end()
            while pos < len(line) and line[pos] in (" ", "\t"):
                pos += 1
            if pos >= len(line):
                continue
            if line[pos] == "`":
                continue
            rest = line[pos:]
            tool_match = re.match(r"([A-Z]\w+)", rest)
            if tool_match and tool_match.group(1) in KNOWN_TOOLS:
                violations.append((line_num, tool_match.group(1)))
    return violations


@pytest.mark.parametrize(
    "filepath",
    [pytest.param(p, id=str(p.relative_to(REPO_ROOT))) for p in _discover_files()],
)
def test_tool_call_format(filepath: Path) -> None:
    violations = _find_violations(filepath)
    assert not violations, (
        f"Tool call format violations in {filepath.relative_to(REPO_ROOT)}:\n"
        + "\n".join(
            f"  L{ln}: '{name}' should be backtick-quoted (Use Tool `{name}`)"
            for ln, name in violations
        )
    )
