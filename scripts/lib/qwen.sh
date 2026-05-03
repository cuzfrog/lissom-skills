#!/usr/bin/env bash
# Qwen Code-format generation functions.
# Transforms Claude Code agent/skill files into Qwen Code-format equivalents.

QWEN_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$QWEN_LIB_DIR/constants.sh"

# Convert Claude Code agent frontmatter to Qwen Code format.
# Args:
#   content       - full agent file content
#   agent_name    - agent name (e.g. "lissom-researcher")
#   include_model - "true" or "false" (default "false")
#   model_override - optional model override (default "")
# Returns: transformed frontmatter + body to stdout
#
# Field ordering: name, description, version, model (optional), tools (YAML list)
qwen_format_agent_frontmatter() {
    local content="$1"
    local agent_name="$2"
    local include_model="${3:-false}"
    local model_override="${4:-}"

    local fmt=0 fm_end=0 ln=0
    local name_f="" desc_f="" tools_f=""
    local line

    # Extract version comment from first line (before frontmatter)
    local version_comment=""
    local first_line
    IFS= read -r first_line <<< "$content"
    local re='^<!--[[:space:]]*version:[[:space:]]*(.+)[[:space:]]*-->$'
    if [[ "$first_line" =~ $re ]]; then
        version_comment="$first_line"
    fi

    while IFS= read -r line; do
        ln=$((ln + 1))
        if [[ "$line" == "---" ]]; then
            if [[ $fmt -eq 0 ]]; then fmt=1  # echoed later with comment
            else fm_end=$ln; break
            fi
        elif [[ $fmt -eq 1 ]]; then
            if   [[ "$line" =~ ^name:[[:space:]]*(.*)$ ]];        then name_f="name: ${BASH_REMATCH[1]}"
            elif [[ "$line" =~ ^description:[[:space:]]*(.*)$ ]]; then desc_f="description: ${BASH_REMATCH[1]}"
            elif [[ "$line" =~ ^tools:[[:space:]]*(.*)$ ]];       then tools_f="${BASH_REMATCH[1]}"
            fi
        fi
    done <<< "$content"

    if [[ $fm_end -eq 0 ]]; then
        echo "Error: Missing closing --- delimiter in frontmatter" >&2
        return 1
    fi

    if [[ -z "$name_f" ]] || [[ -z "$desc_f" ]]; then
        echo "Error: Missing required frontmatter fields (name, description)" >&2
        return 1
    fi

    [[ -n "$version_comment" ]] && echo "$version_comment"
    echo "---"
    echo "$name_f"; echo "$desc_f"

    # Model resolution: use override if provided, else use include_model flag
    if [[ -n "$model_override" ]]; then
        echo "model: $model_override"
    elif [[ "$include_model" == "true" ]]; then
        local model
        model=$(get_qwen_model "$agent_name")
        echo "model: $model"
    fi

    # Emit tools: as YAML list
    if [[ -n "$tools_f" ]]; then
        echo "tools:"
        # Split comma-separated tool names, trim whitespace
        local IFS=',' tool_name qwen_name
        for tool_name in $tools_f; do
            tool_name=$(echo "$tool_name" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')
            if [[ -n "$tool_name" ]]; then
                qwen_name="${CLAUDE_TO_QWEN_TOOL[$tool_name]}"
                if [[ -n "$qwen_name" ]]; then
                    echo "  - $qwen_name"
                fi
                # Skip AskUserQuestion (not in CLAUDE_TO_QWEN_TOOL) and unknown tools
            fi
        done
    fi

    echo "---"
    [[ $fm_end -gt 0 ]] && echo "$content" | tail -n +$((fm_end + 1))
}

# Convert Claude Code skill frontmatter to Qwen Code format.
# Preserves only name and description fields, drops all others.
# Args: content - full skill file content
# Returns: transformed frontmatter + body to stdout
qwen_format_skill_frontmatter() {
    local content="$1"

    local fmt=0 fm_end=0 ln=0
    local name_f="" desc_f=""
    local line

    while IFS= read -r line; do
        ln=$((ln + 1))
        if [[ "$line" == "---" ]]; then
            if [[ $fmt -eq 0 ]]; then fmt=1; echo "$line"
            else fm_end=$ln; break
            fi
        elif [[ $fmt -eq 1 ]]; then
            if   [[ "$line" =~ ^name:[[:space:]]*(.*)$ ]];        then name_f="name: ${BASH_REMATCH[1]}"
            elif [[ "$line" =~ ^description:[[:space:]]*(.*)$ ]]; then desc_f="description: ${BASH_REMATCH[1]}"
            fi
        fi
    done <<< "$content"

    if [[ $fm_end -eq 0 ]]; then
        echo "Error: Missing closing --- delimiter in frontmatter" >&2
        return 1
    fi

    if [[ -z "$name_f" ]] || [[ -z "$desc_f" ]]; then
        echo "Error: Missing required frontmatter fields (name, description)" >&2
        return 1
    fi

    echo "$name_f"; echo "$desc_f"
    echo "---"
    [[ $fm_end -gt 0 ]] && echo "$content" | tail -n +$((fm_end + 1))
}

# Rewrite Claude Code tool names inside backticks to their Qwen Code equivalents.
# e.g. `Bash` -> `run_shell_command`, `AskUserQuestion` -> `question`
# Args: body text with backtick-wrapped tool names
# Returns: rewritten body text
qwen_rewrite_body_tools() {
    local content="$1"
    local sed_expr=""
    local claude_tool qwen_tool
    for claude_tool in "${!CLAUDE_TO_QWEN_BODY[@]}"; do
        qwen_tool="${CLAUDE_TO_QWEN_BODY[$claude_tool]}"
        sed_expr+="s/\`${claude_tool}\`/\`${qwen_tool}\`/g; "
    done
    echo "$content" | sed "$sed_expr"
}

# Full agent-file conversion: frontmatter + body tool-name rewriting.
# Args:
#   content       - full agent file content
#   agent_name    - agent name (e.g. "lissom-researcher")
#   include_model - "true" or "false" (default "false")
#   model_override - optional model override (default "")
# Returns: fully converted content to stdout
qwen_format_agent_file() {
    local content="$1"
    local agent_name="$2"
    local include_model="${3:-false}"
    local model_override="${4:-}"
    local tmp
    tmp=$(qwen_format_agent_frontmatter "$content" "$agent_name" "$include_model" "$model_override") || return 1
    qwen_rewrite_body_tools "$tmp"
}
