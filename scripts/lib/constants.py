"""
Immutable data constants ported from constants.sh.

Provides agent/skill lists, target configuration, model maps,
and tool name mappings for the Python build system.
"""

# Agent names (lissom production agents)
AGENTS = (
    "lissom-implementer",
    "lissom-planner",
    "lissom-researcher",
    "lissom-reviewer",
    "lissom-specs-reviewer",
)

# Skill names (lissom production skills)
SKILLS = (
    "lissom-auto",
    "lissom-impl",
    "lissom-plan",
    "lissom-research",
    "lissom-review",
)

# Target directories to format identifier shortname
TARGET_CONFIG = {
    ".claude": "claude",
    ".opencode": "opencode",
    ".qwen": "qwen",
    ".gemini": "gemini",
}

# Claude Code agent filename (basename without .md) → default model
CLAUDE_MODEL_MAP = {
    "lissom-implementer": "sonnet",
    "lissom-planner": "sonnet",
    "lissom-researcher": "opus-4.6",
    "lissom-reviewer": "sonnet",
    "lissom-specs-reviewer": "sonnet",
}

# Agent name → Opencode model
OPENCODE_MODEL_MAP = {
    "lissom-implementer": "opencode-go/deepseek-v4-flash",
    "lissom-planner": "opencode-go/deepseek-v4-pro",
    "lissom-researcher": "opencode-go/deepseek-v4-pro",
    "lissom-reviewer": "opencode-go/qwen3.6-plus",
    "lissom-specs-reviewer": "opencode-go/deepseek-v4-flash",
}

# Agent name → Qwen Code model
QWEN_MODEL_MAP = {
}

# Agent name → Gemini model
GEMINI_MODEL_MAP = {
}

# Claude Code tool name → Opencode permission key
TOOL_TO_PERMISSION = {
    "Bash": "bash",
    "Read": "read",
    "Write": "write",
    "Edit": "edit",
    "Glob": "glob",
    "Grep": "grep",
    "WebFetch": "webfetch",
    "WebSearch": "websearch",
    "AskUserQuestion": "question",
}

# Claude Code tool name → Opencode body text name
TOOL_NAME_MAPPING = {
    "AskUserQuestion": "question",
    "Bash": "bash",
    "Read": "read",
    "Write": "write",
    "Edit": "edit",
    "Glob": "glob",
    "Grep": "grep",
    "WebFetch": "webfetch",
    "WebSearch": "websearch",
}

# Claude Code tool name → Qwen Code frontmatter tool name
# NOTE: AskUserQuestion deliberately excluded — it is removed from tools list
CLAUDE_TO_QWEN_TOOL = {
    "Bash": "run_shell_command",
    "Read": "read_file",
    "Write": "write_file",
    "Edit": "edit",
    "Glob": "glob",
    "Grep": "grep_search",
    "WebFetch": "web_fetch",
    "WebSearch": "web_search",
}

# Claude Code tool name → Qwen Code body text name
CLAUDE_TO_QWEN_BODY = {
    "Bash": "run_shell_command",
    "Read": "read_file",
    "Write": "write_file",
    "Edit": "edit",
    "Glob": "glob",
    "Grep": "grep_search",
    "WebFetch": "web_fetch",
    "WebSearch": "web_search",
    "AskUserQuestion": "question",
}

# Claude Code tool name → Gemini CLI frontmatter tool name
CLAUDE_TO_GEMINI_TOOL = {
    "Bash": "run_shell_command",
    "Read": "read_file",
    "Write": "write_file",
    "Edit": "replace",
    "Glob": "glob",
    "Grep": "grep_search",
    "WebFetch": "web_fetch",
    "WebSearch": "google_web_search",
    "AskUserQuestion": "ask_user",
}

# Claude Code tool name → Gemini CLI body text name
CLAUDE_TO_GEMINI_BODY = {
    "Bash": "run_shell_command",
    "Read": "read_file",
    "Write": "write_file",
    "Edit": "replace",
    "Glob": "glob",
    "Grep": "grep_search",
    "WebFetch": "web_fetch",
    "WebSearch": "google_web_search",
    "AskUserQuestion": "ask_user",
}
