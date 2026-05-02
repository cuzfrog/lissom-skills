#!/usr/bin/env bash
# Constants for installation, uninstallation, and conversion.

# Agent names (lissom production agents)
AGENTS=(lissom-implementer lissom-planner lissom-researcher lissom-reviewer lissom-specs-reviewer)

# Skill names (lissom production skills)
SKILLS=(lissom-auto lissom-impl lissom-plan lissom-research lissom-review)

# Map agent filename to default model value (for Claude Code).
# Args: basename of agent file (e.g. "lissom-implementer.md")
# Returns: model name (haiku, sonnet, opus-4.6)
get_default_model() {
    local filename="$1"
    case "$filename" in
        lissom-implementer.md|task-implementer.md) echo "haiku" ;;
        lissom-planner.md|task-planner.md) echo "sonnet" ;;
        lissom-researcher.md|task-researcher.md) echo "opus-4.6" ;;
        lissom-reviewer.md|task-reviewer.md) echo "sonnet" ;;
        lissom-specs-reviewer.md) echo "sonnet" ;;
        *) echo "" ;;
    esac
}

# Map agent name to Opencode model value.
# Args: agent name (e.g. "lissom-implementer")
# Returns: model string for Opencode (e.g. "opencode-go/deepseek-v4-flash")
get_opencode_model() {
    local agent_name="$1"
    case "$agent_name" in
        lissom-implementer|task-implementer) echo "opencode-go/deepseek-v4-flash" ;;
        lissom-planner|task-planner) echo "opencode-go/qwen3.6-plus" ;;
        lissom-researcher|task-researcher) echo "opencode-go/deepseek-v4-flash" ;;
        lissom-reviewer|task-reviewer) echo "opencode-go/qwen3.6-plus" ;;
        lissom-specs-reviewer) echo "opencode-go/qwen3.6-plus" ;;
        *) echo "opencode-go/qwen3.6-plus" ;;
    esac
}

# Claude Code tool names to Opencode permission key mapping
# Declares an associative array TOOL_TO_PERMISSION that maps tool names
declare -A TOOL_TO_PERMISSION=(
    [Bash]="bash"
    [Read]="read"
    [Write]="write"
    [Edit]="edit"
    [Glob]="glob"
    [Grep]="grep"
    [WebFetch]="webfetch"
    [WebSearch]="websearch"
    [AskUserQuestion]="question"
)

# Claude Code tool names to Opencode body text mapping
# Maps tool names that appear in backticks in agent/skill body text
declare -A TOOL_NAME_MAPPING=(
    [AskUserQuestion]="question"
    [Bash]="bash"
    [Read]="read"
    [Write]="write"
    [Edit]="edit"
    [Glob]="glob"
    [Grep]="grep"
    [WebFetch]="webfetch"
    [WebSearch]="websearch"
)
