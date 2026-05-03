#!/usr/bin/env bash
# UI interaction functions for prompting users.

# Prompt user to choose between .claude/ and .opencode/ target directories
# Returns: target directory name (".claude" or ".opencode")
# Respects LISSOM_TARGET (explicit target selection)
# Respects LISSOM_YES=1 (defaults to ".claude" without prompting)
prompt_target_directory() {
    # If LISSOM_TARGET is explicitly set, use it
    if [[ -n "${LISSOM_TARGET:-}" ]]; then
        echo "$LISSOM_TARGET"
        return 0
    fi
    
    # If LISSOM_YES=1, default to .claude/ (backward compatible)
    if [[ "${LISSOM_YES:-}" == "1" ]]; then
        echo ".claude"
        return 0
    fi
    
    # Check if stdin is a TTY (interactive mode)
    if [[ ! -t 0 ]]; then
        # Non-interactive (curl-pipe install) - default to .claude/
        echo ".claude"
        return 0
    fi
    
    echo "Select installation target:" >&2
    local choice=".claude"
    select choice in ".claude (Claude Code and most CLIs)" ".opencode (Opencode)"; do
        case "$REPLY" in
            1) choice=".claude"; break ;;
            2) choice=".opencode"; break ;;
            *) echo "Invalid choice. Try again." ;;
        esac
    done
    
    echo "$choice"
}

# Prompt user whether to set default models for agents
# Returns: "true" or "false"
# Respects LISSOM_NO=1 (skips prompt, returns false)
prompt_model_preference() {
    # If LISSOM_NO=1, skip model setting
    if [[ "${LISSOM_NO:-}" == "1" ]]; then
        echo "false"
        return 0
    fi
    
    # Check if stdin is a TTY (interactive mode)
    if [[ ! -t 0 ]]; then
        # Non-interactive (curl-pipe install) - default to not setting models
        echo "false"
        return 0
    fi
    
    echo -n "Set default models for agents? You can modify agent definition files later. [Y/n] " >&2
    read -n 1 -r reply
    echo >&2
    if [[ -z "$reply" ]] || [[ "$reply" =~ ^[Yy]$ ]]; then
        echo "true"
    else
        echo "false"
    fi
}

# Display an adaptive-width table of agent → model mappings.
# Args: name of an associative array variable (agent_name → model_value)
display_model_table() {
    local -n models="$1"
    local max_agent=5 max_model=5
    local key val
    for key in "${!models[@]}"; do
        val="${models[$key]}"
        (( ${#key} > max_agent )) && max_agent=${#key}
        (( ${#val} > max_model )) && max_model=${#val}
    done
    local c1=$((max_agent + 2)) c2=$((max_model + 2))
    local d1 d2
    printf -v d1 '%*s' "$c1" ''; d1="${d1// /─}"
    printf -v d2 '%*s' "$c2" ''; d2="${d2// /─}"
    echo "┌${d1}┬${d2}┐"
    printf "│ %-*s │ %-*s │\n" "$max_agent" "Agent" "$max_model" "Model"
    echo "├${d1}┼${d2}┤"
    local agent_name
    for agent_name in $(printf '%s\n' "${!models[@]}" | sort); do
        printf "│ %-*s │ %-*s │\n" "$max_agent" "$agent_name" "$max_model" "${models[$agent_name]}"
    done
    echo "└${d1}┴${d2}┘"
}
