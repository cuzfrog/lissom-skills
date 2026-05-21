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
    ".pi": "pi",
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
    "lissom-implementer": "qwen3-coder-plus",
    "lissom-planner": "qwen3.6-plus",
    "lissom-researcher": "qwen3.6-plus",
    "lissom-reviewer": "qwen3.6-plus",
    "lissom-specs-reviewer": "qwen3.6-plus",
}

# Agent name → Gemini model
GEMINI_MODEL_MAP = {
    "lissom-implementer": "gemini-3-flash-preview",
    "lissom-planner": "gemini-3-flash-preview",
    "lissom-researcher": "gemini-3-pro-preview",
    "lissom-reviewer": "gemini-3-flash-preview",
    "lissom-specs-reviewer": "gemini-3-flash-preview",
}

OPENCODE_TOOL_NAME_MAPPING = {
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

QWEN_TOOL_NAME_MAPPING = {
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

GEMINI_TOOL_NAME_MAPPING = {
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

PI_TOOL_NAME_MAPPING = {
    "Bash": "bash",
    "Read": "read",
    "Write": "write",
    "Edit": "edit",
    "Glob": "find,ls", # special case, in frontmatter, pi uses a comma-separated list
    "Grep": "grep",
    "WebFetch": "web_fetch",
    "WebSearch": "web_search",
    "AskUserQuestion": "ask_user_question",
    # "Agent": "Agent", # handled by https://github.com/tintinweb/pi-subagents
}
