#!/usr/bin/env bash
# UI interaction functions for prompting users.

# Detect which dialog tool is available (dialog, whiptail, or bash select)
# Returns: tool name ("dialog", "whiptail", "select", or "none")
detect_dialog_tool() {
    if command -v dialog &>/dev/null; then
        echo "dialog"
    elif command -v whiptail &>/dev/null; then
        echo "whiptail"
    else
        echo "select"
    fi
}

# Prompt user to choose between .claude/ and .opencode/ target directories
# Args: dialog_tool (e.g. "dialog", "whiptail", "select")
# Returns: target directory name (".claude" or ".opencode")
# Respects LISSOM_YES=1 (defaults to ".claude" without prompting)
prompt_target_directory() {
    local dialog_tool="$1"
    
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
    
    local choice
    case "$dialog_tool" in
        dialog)
            choice=$(dialog --title "Install Target" \
                --menu "Select installation target:" 10 40 2 \
                ".claude" "Claude Code format (current)" \
                ".opencode" "Opencode format (converted)" \
                2>&1 >/dev/tty) || choice=".claude"
            ;;
        whiptail)
            choice=$(whiptail --title "Install Target" \
                --menu "Select installation target:" 10 40 2 \
                ".claude" "Claude Code format (current)" \
                ".opencode" "Opencode format (converted)" \
                3>&1 1>&2 2>&3) || choice=".claude"
            ;;
        select|*)
            # Fallback: use bash select
            echo "Select installation target:"
            select choice in ".claude (Claude Code format)" ".opencode (Opencode format)"; do
                case "$REPLY" in
                    1) choice=".claude"; break ;;
                    2) choice=".opencode"; break ;;
                    *) echo "Invalid choice. Try again." ;;
                esac
            done
            ;;
    esac
    
    echo "$choice"
}

# Prompt user whether to set default models for agents
# Args: dialog_tool (e.g. "dialog", "whiptail", "select")
# Returns: "true" or "false"
# Respects LISSOM_NO=1 (skips prompt, returns false)
prompt_model_preference() {
    local dialog_tool="$1"
    
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
    
    local choice
    case "$dialog_tool" in
        dialog)
            dialog --title "Model Configuration" \
                --yesno "Set default models for agents?" 7 40 >/dev/tty 2>&1 && choice="true" || choice="false"
            ;;
        whiptail)
            whiptail --title "Model Configuration" \
                --yesno "Set default models for agents?" 7 40 >/dev/tty 2>&1 && choice="true" || choice="false"
            ;;
        select|*)
            # Fallback: simple yes/no prompt
            echo -n "Set default models for agents? [Y/n] "
            read -n 1 -r reply
            echo
            if [[ -z "$reply" ]] || [[ "$reply" =~ ^[Yy]$ ]]; then
                choice="true"
            else
                choice="false"
            fi
            ;;
    esac
    
    echo "$choice"
}
