#!/usr/bin/env bash
# UI interaction functions for prompting users.

prompt_target_directory() {
    [[ -n "${LISSOM_TARGET:-}" ]] && { echo "$LISSOM_TARGET"; return 0; }
    [[ "${LISSOM_YES:-}" == "1" ]] && { echo ".claude"; return 0; }

    # When stdin is a terminal, use select interactively
    if [[ -t 0 ]]; then
        echo "Select installation target:" >&2
        select _ in ".claude (Claude Code and most CLIs)" ".opencode (Opencode)" ".qwen (Qwen Code)" ".gemini (Gemini CLI)"; do
            case "$REPLY" in
                1) echo ".claude"; return 0 ;;
                2) echo ".opencode"; return 0 ;;
                3) echo ".qwen"; return 0 ;;
                4) echo ".gemini"; return 0 ;;
                *) echo "Invalid choice. Try again." >&2 ;;
            esac
        done
    fi

    # When stdin is piped (e.g. curl | bash) but a terminal is available,
    # read from /dev/tty to show the interactive menu.
    if [[ -t 2 ]] && exec {_ui_tty_fd}</dev/tty 2>/dev/null; then
        echo "Select installation target:" >&2
        echo "1) .claude (Claude Code and most CLIs)" >&2
        echo "2) .opencode (Opencode)" >&2
        echo "3) .qwen (Qwen Code)" >&2
        echo "4) .gemini (Gemini CLI)" >&2
        echo -n "Choice [1]: " >&2
        read -r _ui_reply <&${_ui_tty_fd}
        exec {_ui_tty_fd}<&-
        case "${_ui_reply:-1}" in
            1|"") echo ".claude" ;;
            2) echo ".opencode" ;;
            3) echo ".qwen" ;;
            4) echo ".gemini" ;;
            *) echo "Invalid choice, defaulting to .claude." >&2; echo ".claude" ;;
        esac
        return 0
    fi

    # No TTY available at all (e.g. CI) — safe default
    echo ".claude"
}

# Prompt user whether to set default models for agents.
# Args: <default_answer> — "true" or "false" to return when non-interactive (default: "false")
# Returns: "true" or "false" on stdout
# Respects: LISSOM_YES=1 → "true" (skip), LISSOM_NO=1  → "false" (skip)
prompt_model_preference() {
    local default="${1:-false}"
    local reply

    if [[ "${LISSOM_YES:-}" == "1" ]]; then
        echo "true"; return 0
    fi
    if [[ "${LISSOM_NO:-}" == "1" ]]; then
        echo "false"; return 0
    fi

    if [[ ! -t 0 ]]; then
        echo "$default"; return 0
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

# Prompt user to confirm uninstallation of files.
# Returns: "true" or "false" on stdout
# Respects: LISSOM_YES=1 → "true" (skip prompt, proceed with uninstall)
# Non-TTY stdin → "true" (non-interactive default is proceed)
prompt_uninstall_confirmation() {
    local reply

    if [[ "${LISSOM_YES:-}" == "1" ]]; then
        echo "true"; return 0
    fi

    if [[ ! -t 0 ]]; then
        echo "true"; return 0
    fi

    echo -n "Remove these files? [y/N] " >&2
    read -n 1 -r reply
    echo >&2
    if [[ "$reply" =~ ^[Yy]$ ]]; then
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
