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

    # Remove agents - scan the agents directory for any files that were installed by lissom-skills
    # This includes production (lissom-*) agent names
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
        
        # Remove empty agents directory
        if [[ -d "$TARGET/agents" ]] && [[ -z "$(ls -A "$TARGET/agents")" ]]; then
            rmdir "$TARGET/agents"
        fi
    fi

    # Remove skills - scan the skills directory for any subdirectories that were installed by lissom-skills
    # This includes production (lissom-*) skill names
    if [[ -d "$TARGET/skills" ]]; then
        for skill_dir in "$TARGET/skills"/*/; do
            if [[ -d "$skill_dir" ]]; then
                local skill_name=$(basename "$skill_dir")
                if [[ "$skill_name" =~ ^lissom- ]]; then
                    # Remove SKILL.md file
                    if [[ -f "$skill_dir/SKILL.md" ]]; then
                        rm "$skill_dir/SKILL.md"
                        echo "  Removed $skill_dir/SKILL.md"
                        REMOVED=$((REMOVED + 1))
                    fi
                    
                    # Remove user_preference_questions.json if present
                    if [[ -f "$skill_dir/user_preference_questions.json" ]]; then
                        rm "$skill_dir/user_preference_questions.json"
                        echo "  Removed $skill_dir/user_preference_questions.json"
                        REMOVED=$((REMOVED + 1))
                    fi
                    
                    # Remove empty skill directory
                    if [[ -z "$(ls -A "$skill_dir")" ]]; then
                        rmdir "$skill_dir"
                    fi
                fi
            fi
        done
        
        # Remove empty skills directory
        if [[ -d "$TARGET/skills" ]] && [[ -z "$(ls -A "$TARGET/skills")" ]]; then
            rmdir "$TARGET/skills"
        fi
    fi

    # Remove empty target directory
    if [[ -d "$TARGET" ]] && [[ -z "$(ls -A "$TARGET")" ]]; then
        rmdir "$TARGET"
        echo "  Removed empty directory $TARGET"
    fi

    echo ""
    echo "Removed $REMOVED files from $TARGET"
}

# Parse arguments
if [[ -n "$1" ]]; then
    echo "Usage: $0"
    exit 1
fi

# Always scan both .claude/ and .opencode/
uninstall_from "./.claude"
uninstall_from "./.opencode"
