#!/usr/bin/env bash
# Opencode-format generation functions.
# Transforms Claude Code agent/skill files into Opencode-format equivalents.

OPENCODE_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$OPENCODE_LIB_DIR/constants.sh"

# Parse a tools: line into space-separated tool names.
# Args: tools_line (e.g. "tools: Bash, Read, Write")
# Returns: space-separated list (e.g. "Bash Read Write")
opencode_parse_tools() {
    local tools_line="$1"
    local tools_part="${tools_line#*: }"
    echo "$tools_part" | tr ',' '\n' | sed 's/^[[:space:]]*//; s/[[:space:]]*$//' | tr '\n' ' '
}

# Generate an Opencode permission: block from a space-separated tool list.
# Args: tools (space-separated tool names)
# Returns: YAML permission block (indented 2 spaces)
opencode_permissions_from_tools() {
    local tools="$1"
    echo "permission:"
    local tool
    for tool in $tools; do
        local key="${TOOL_TO_PERMISSION[$tool]}"
        [[ -n "$key" ]] && printf "  %s: allow\n" "$key"
    done
}

# Rewrite Claude Code tool names inside backticks to their Opencode equivalents.
# e.g. `AskUserQuestion` -> `question`, `Bash` -> `bash`
# Args: body text with backtick-wrapped tool names
# Returns: rewritten body text
opencode_rewrite_body_tools() {
    local content="$1"
    local sed_expr=""
    local claude_tool opencode_tool
    for claude_tool in "${!TOOL_NAME_MAPPING[@]}"; do
        opencode_tool="${TOOL_NAME_MAPPING[$claude_tool]}"
        sed_expr+="s/\`${claude_tool}\`/\`${opencode_tool}\`/g; "
    done
    echo "$content" | sed "$sed_expr"
}

# Convert Claude Code agent frontmatter to Opencode format.
# Args:
#   content      - full agent file content
#   agent_name   - agent name (e.g. "lissom-researcher")
#   include_model - "true" or "false"
# Returns: transformed frontmatter + body to stdout
#
# Field ordering: name, description, mode, model, temperature, permission
opencode_format_frontmatter() {
    local content="$1"
    local agent_name="$2"
    local include_model="${3:-false}"
    local model_override="${4:-}"

    local fmt=0 fm_end=0 ln=0
    local name_f="" desc_f="" tools_f="" other_f=""
    local line

    while IFS= read -r line; do
        ln=$((ln + 1))
        if [[ "$line" == "---" ]]; then
            if [[ $fmt -eq 0 ]]; then fmt=1  # opening --- echoed later with comment
            else fm_end=$ln; break
            fi
        elif [[ $fmt -eq 1 ]]; then
            if   [[ "$line" =~ ^name:[[:space:]]*(.*)$ ]];        then name_f="name: ${BASH_REMATCH[1]}"
            elif [[ "$line" =~ ^description:[[:space:]]*(.*)$ ]]; then desc_f="description: ${BASH_REMATCH[1]}"
            elif [[ "$line" =~ ^tools:[[:space:]]*(.*)$ ]];       then tools_f="${BASH_REMATCH[1]}"
            elif [[ -n "$line" ]]; then other_f+="$line"$'\n'
            fi
        fi
    done <<< "$content"

    if [[ -z "$name_f" ]] || [[ -z "$desc_f" ]]; then
        echo "Error: Missing required frontmatter fields (name, description)" >&2
        return 1
    fi

    echo "---"
    echo "$name_f"; echo "$desc_f"
    echo "mode: subagent"
    if [[ "$include_model" == "true" ]] || [[ -n "$model_override" ]]; then
        local model="${model_override:-$(get_opencode_model "$agent_name")}"
        echo "model: $model"
    fi
    echo "temperature: 0.1"
    if [[ -n "$tools_f" ]]; then
        local tools
        tools=$(opencode_parse_tools "tools: $tools_f")
        opencode_permissions_from_tools "$tools"
    fi
    echo "---"
    [[ $fm_end -gt 0 ]] && echo "$content" | tail -n +$((fm_end + 1))
}

# Full agent-file conversion: frontmatter + body tool-name rewriting.
# This is the main entry point called by the Opencode strategy functions.
# Args:
#   content       - full agent file content
#   agent_name    - agent name (e.g. "lissom-researcher")
#   include_model - "true" or "false"
# Returns: fully converted content to stdout
opencode_format_agent_file() {
    local content="$1"
    local agent_name="$2"
    local include_model="${3:-false}"
    local model_override="${4:-}"
    local tmp
    tmp=$(opencode_format_frontmatter "$content" "$agent_name" "$include_model" "$model_override")
    opencode_rewrite_body_tools "$tmp"
}
