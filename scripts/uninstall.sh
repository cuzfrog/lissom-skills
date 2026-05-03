#!/usr/bin/env bash

set -e  # Exit on error

REPO="${LISSOM_REPO:-https://raw.githubusercontent.com/cuzfrog/lissom-skills/main}"
CLEANUP_TMPDIR=""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd 2>/dev/null || pwd)"
[[ "$(basename "$SCRIPT_DIR")" == "scripts" ]] && SCRIPT_DIR="$(dirname "$SCRIPT_DIR")"

if [[ ! -f "$SCRIPT_DIR/scripts/lib/common.sh" ]]; then
    SCRIPT_DIR="$(mktemp -d)"
    CLEANUP_TMPDIR="$SCRIPT_DIR"
    mkdir -p "$SCRIPT_DIR/scripts/lib"
    for f in common.sh constants.sh ui.sh; do
        curl -fsSL "$REPO/scripts/lib/$f" -o "$SCRIPT_DIR/scripts/lib/$f"
    done
fi

source "$SCRIPT_DIR/scripts/lib/common.sh"
source "$SCRIPT_DIR/scripts/lib/constants.sh"
source "$SCRIPT_DIR/scripts/lib/ui.sh"

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

# Only run the main body when executed directly (not sourced)
# This allows sourcing for testing individual functions like uninstall_from()
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    return
fi

parse_no_args "$@"

# ── Phase 1: Count lissom files per target ──────────────────────────
declare -A COUNTS
TOTAL=0
for target_dir in "${!TARGET_CONFIG[@]}"; do
    COUNT=$(uninstall_from "./$target_dir" true)
    COUNTS["$target_dir"]=$COUNT
    TOTAL=$((TOTAL + COUNT))
done

# ── Phase 2: Report ─────────────────────────────────────────────────
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

# ── Phase 3: Confirm ────────────────────────────────────────────────
CONFIRMED=$(prompt_uninstall_confirmation)
if [[ "$CONFIRMED" != "true" ]]; then
    echo "Uninstall cancelled."
    exit 0
fi

# ── Phase 4: Remove ─────────────────────────────────────────────────
for target_dir in "${!TARGET_CONFIG[@]}"; do
    if [[ ${COUNTS["$target_dir"]} -gt 0 ]]; then
        uninstall_from "./$target_dir"
    fi
done

# Clean up temp directory used when fetching from GitHub
[[ -n "$CLEANUP_TMPDIR" ]] && rm -rf "$CLEANUP_TMPDIR" || true
