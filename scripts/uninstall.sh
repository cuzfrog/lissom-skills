#!/usr/bin/env bash

set -e  # Exit on error

# Source constants
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[[ "$(basename "$SCRIPT_DIR")" == "scripts" ]] && SCRIPT_DIR="$(dirname "$SCRIPT_DIR")"
source "$SCRIPT_DIR/scripts/lib/common.sh"
source "$SCRIPT_DIR/scripts/lib/constants.sh"

_rmdir_if_empty() {
    local dir="$1"
    [[ -d "$dir" ]] && [[ -z "$(ls -A "$dir" 2>/dev/null)" ]] && rmdir "$dir"
}

uninstall_from() {
    local TARGET="$1"
    local REMOVED=0

    if [[ -d "$TARGET/agents" ]]; then
        for agent_file in "$TARGET/agents"/*.md; do
            if [[ -f "$agent_file" ]]; then
                local agent_name=$(basename "$agent_file" .md)
                if [[ "$agent_name" =~ ^lissom- ]]; then
                    rm "$agent_file"
                    echo "  Removed $agent_file"
                    REMOVED=$((REMOVED + 1))
                fi
            fi
        done
        _rmdir_if_empty "$TARGET/agents"
    fi

    if [[ -d "$TARGET/skills" ]]; then
        for skill_dir in "$TARGET/skills"/*/; do
            if [[ -d "$skill_dir" ]]; then
                local skill_name=$(basename "$skill_dir")
                if [[ "$skill_name" =~ ^lissom- ]]; then
                    if [[ -f "$skill_dir/SKILL.md" ]]; then
                        rm "$skill_dir/SKILL.md"
                        echo "  Removed $skill_dir/SKILL.md"
                        REMOVED=$((REMOVED + 1))
                    fi
                    if [[ -f "$skill_dir/user_preference_questions.json" ]]; then
                        rm "$skill_dir/user_preference_questions.json"
                        echo "  Removed $skill_dir/user_preference_questions.json"
                        REMOVED=$((REMOVED + 1))
                    fi
                    _rmdir_if_empty "$skill_dir"
                fi
            fi
        done
        _rmdir_if_empty "$TARGET/skills"
    fi

    if _rmdir_if_empty "$TARGET"; then
        echo "  Removed empty directory $TARGET"
    fi

    echo "Removed $REMOVED files from $TARGET"
}

parse_no_args "$@"

# Always scan both .claude/ and .opencode/
for target_dir in "${!TARGET_CONFIG[@]}"; do
    uninstall_from "./$target_dir"
done
