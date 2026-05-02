#!/usr/bin/env bash

set -e  # Exit on error

# Source constants
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/scripts/lib/constants.sh"

uninstall_from() {
    local TARGET="$1"
    local REMOVED=0
    local SKIPPED=0

    if [[ ! -d "$TARGET" ]]; then
        echo "Nothing to uninstall: $TARGET does not exist."
        return
    fi

    echo "Uninstalling from $TARGET..."

    # Remove agents (only lissom-skills' own agents)
    for agent in "${AGENTS[@]}"; do
        dest="$TARGET/agents/$agent.md"
        if [[ -f "$dest" ]]; then
            rm "$dest"
            echo "  Removed $dest"
            REMOVED=$((REMOVED + 1))
        else
            SKIPPED=$((SKIPPED + 1))
        fi
    done

    # Remove empty agents directory
    if [[ -d "$TARGET/agents" ]] && [[ -z "$(ls -A "$TARGET/agents")" ]]; then
        rmdir "$TARGET/agents"
    fi

    # Remove skills (only lissom-skills' own skills)
    for skill in "${SKILLS[@]}"; do
        dest="$TARGET/skills/$skill/SKILL.md"
        if [[ -f "$dest" ]]; then
            rm "$dest"
            echo "  Removed $dest"
            REMOVED=$((REMOVED + 1))
        else
            SKIPPED=$((SKIPPED + 1))
        fi
        # Also remove supporting files for lissom-auto
        if [[ "$skill" == "lissom-auto" ]]; then
            pref_dest="$TARGET/skills/$skill/user_preference_questions.json"
            if [[ -f "$pref_dest" ]]; then
                rm "$pref_dest"
                echo "  Removed $pref_dest"
                REMOVED=$((REMOVED + 1))
            fi
        fi
        skill_target_dir="$TARGET/skills/$skill"
        if [[ -d "$skill_target_dir" ]] && [[ -z "$(ls -A "$skill_target_dir")" ]]; then
            rmdir "$skill_target_dir"
        fi
    done

    # Remove empty skills directory
    if [[ -d "$TARGET/skills" ]] && [[ -z "$(ls -A "$TARGET/skills")" ]]; then
        rmdir "$TARGET/skills"
    fi

    # Remove empty target directory
    if [[ -d "$TARGET" ]] && [[ -z "$(ls -A "$TARGET")" ]]; then
        rmdir "$TARGET"
        echo "  Removed empty directory $TARGET"
    fi

    echo ""
    echo "Removed $REMOVED files from $TARGET"
    echo "Skipped $SKIPPED already-absent files"
}

# Parse arguments
if [[ -n "$1" ]]; then
    echo "Usage: $0"
    exit 1
fi

# Always scan both .claude/ and .opencode/
uninstall_from "./.claude"
uninstall_from "./.opencode"
