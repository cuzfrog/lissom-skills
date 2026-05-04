#!/usr/bin/env bash

set -e

declare -A TARGET_CONFIG=(
    [".claude"]="claude"
    [".opencode"]="opencode"
    [".qwen"]="qwen"
    [".gemini"]="gemini"
)

parse_no_args() {
    if [[ -n "$1" ]]; then
        echo "Usage: uninstall.sh"
        exit 1
    fi
}

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

_rmdir_if_empty() {
    local dir="$1"
    [[ -d "$dir" ]] && [[ -z "$(ls -A "$dir" 2>/dev/null)" ]] && rmdir "$dir"
}

uninstall_from() {
    local TARGET="$1"
    local DRY_RUN="${2:-false}"
    local REMOVED=0

    if [[ -d "$TARGET/agents" ]]; then
        for agent_file in "$TARGET/agents"/*.md; do
            if [[ -f "$agent_file" ]]; then
                local agent_name=$(basename "$agent_file" .md)
                if [[ "$agent_name" =~ ^lissom- ]]; then
                    if [[ "$DRY_RUN" == "true" ]]; then
                        REMOVED=$((REMOVED + 1))
                    else
                        rm "$agent_file"
                        echo "  Removed $agent_file"
                        REMOVED=$((REMOVED + 1))
                    fi
                fi
            fi
        done
        [[ "$DRY_RUN" != "true" ]] && _rmdir_if_empty "$TARGET/agents"
    fi

    if [[ -d "$TARGET/skills" ]]; then
        for skill_dir in "$TARGET/skills"/*/; do
            if [[ -d "$skill_dir" ]]; then
                local skill_name=$(basename "$skill_dir")
                if [[ "$skill_name" =~ ^lissom- ]]; then
                    if [[ -f "$skill_dir/SKILL.md" ]]; then
                        if [[ "$DRY_RUN" == "true" ]]; then
                            REMOVED=$((REMOVED + 1))
                        else
                            rm "$skill_dir/SKILL.md"
                            echo "  Removed $skill_dir/SKILL.md"
                            REMOVED=$((REMOVED + 1))
                        fi
                    fi
                    if [[ -f "$skill_dir/user_preference_questions.json" ]]; then
                        if [[ "$DRY_RUN" == "true" ]]; then
                            REMOVED=$((REMOVED + 1))
                        else
                            rm "$skill_dir/user_preference_questions.json"
                            echo "  Removed $skill_dir/user_preference_questions.json"
                            REMOVED=$((REMOVED + 1))
                        fi
                    fi
                    [[ "$DRY_RUN" != "true" ]] && _rmdir_if_empty "$skill_dir"
                fi
            fi
        done
        [[ "$DRY_RUN" != "true" ]] && _rmdir_if_empty "$TARGET/skills"
    fi

    if [[ "$DRY_RUN" != "true" ]] && _rmdir_if_empty "$TARGET"; then
        echo "  Removed empty directory $TARGET"
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        echo "$REMOVED"
    else
        echo "Removed $REMOVED files from $TARGET"
    fi
}

if [[ -n "${BASH_SOURCE[0]}" ]] && [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    return
fi

parse_no_args "$@"

declare -A COUNTS
TOTAL=0
for target_dir in "${!TARGET_CONFIG[@]}"; do
    COUNT=$(uninstall_from "./$target_dir" true)
    COUNTS["$target_dir"]=$COUNT
    TOTAL=$((TOTAL + COUNT))
done

if [[ $TOTAL -eq 0 ]]; then
    echo "No lissom-skills files found to remove."
    exit 0
fi

echo "The following lissom-skills files will be removed:"
for target_dir in "${!TARGET_CONFIG[@]}"; do
    if [[ ${COUNTS["$target_dir"]} -gt 0 ]]; then
        echo "  $target_dir/ -> ${COUNTS["$target_dir"]} file(s)"
    fi
done
echo "Total: $TOTAL file(s)"

CONFIRMED=$(prompt_uninstall_confirmation)
if [[ "$CONFIRMED" != "true" ]]; then
    echo "Uninstall cancelled."
    exit 0
fi

for target_dir in "${!TARGET_CONFIG[@]}"; do
    if [[ ${COUNTS["$target_dir"]} -gt 0 ]]; then
        uninstall_from "./$target_dir"
    fi
done
