#!/usr/bin/env bash

set -e  # Exit on error

# Parse arguments
MODE="project"
if [[ "$1" == "--user" ]]; then
    MODE="user"
elif [[ "$1" == "--project" ]]; then
    MODE="project"
elif [[ -n "$1" ]]; then
    echo "Usage: $0 [--project | --user]"
    exit 1
fi

# Determine target directory
if [[ "$MODE" == "user" ]]; then
    TARGET="$HOME/.claude"
else
    TARGET="./.claude"
fi

# Get script directory (where agents/, skills/, templates/ are located)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# When piped via curl, BASH_SOURCE[0] is empty so SCRIPT_DIR falls back to CWD.
# If the repo files aren't present, download them from GitHub into a temp dir.
REPO="https://raw.githubusercontent.com/cuzfrog/lissom-skills/main"
CLEANUP_TMPDIR=""
if [[ ! -f "$SCRIPT_DIR/agents/task-researcher.md" ]]; then
    SCRIPT_DIR="$(mktemp -d)"
    CLEANUP_TMPDIR="$SCRIPT_DIR"
    echo "Fetching files from GitHub..."
    mkdir -p "$SCRIPT_DIR/agents" \
             "$SCRIPT_DIR/skills/task-auto" \
             "$SCRIPT_DIR/skills/task-impl" \
             "$SCRIPT_DIR/skills/task-plan" \
             "$SCRIPT_DIR/skills/task-research" \
             "$SCRIPT_DIR/skills/task-review"
    for agent in task-implementer task-planner task-researcher task-reviewer; do
        curl -fsSL "$REPO/agents/$agent.md" -o "$SCRIPT_DIR/agents/$agent.md"
    done
    for skill in task-auto task-impl task-plan task-research task-review; do
        curl -fsSL "$REPO/skills/$skill/SKILL.md" -o "$SCRIPT_DIR/skills/$skill/SKILL.md"
    done
fi

# Extract the `version:` value from a file's YAML frontmatter.
# Returns empty string if no version field is found.
get_version() {
    local file="$1"
    local in_fm=0
    while IFS= read -r line; do
        if [[ "$line" == "---" ]]; then
            if [[ $in_fm -eq 0 ]]; then
                in_fm=1
            else
                break
            fi
        elif [[ $in_fm -eq 1 ]] && [[ "$line" =~ ^version:[[:space:]]*(.+)$ ]]; then
            echo "${BASH_REMATCH[1]}"
            return
        fi
    done < "$file"
    echo ""
}

# classify_file SRC DEST
# Appends to SILENT_SRC/SILENT_DEST or OLDER_SRC/OLDER_DEST
classify_file() {
    local src="$1" dest="$2"
    if [[ ! -f "$dest" ]]; then
        SILENT_SRC+=("$src"); SILENT_DEST+=("$dest")
        return
    fi
    local src_ver dest_ver
    src_ver=$(get_version "$src")
    dest_ver=$(get_version "$dest")
    # No dest version → treat as "infinitely old" → overwrite silently
    if [[ -z "$dest_ver" ]] || [[ -z "$src_ver" ]] || \
       [[ "$src_ver" > "$dest_ver" ]] || [[ "$src_ver" == "$dest_ver" ]]; then
        SILENT_SRC+=("$src"); SILENT_DEST+=("$dest")
    else
        OLDER_SRC+=("$src"); OLDER_DEST+=("$dest")
    fi
}

# Create directory structure
echo "Installing to $TARGET..."
mkdir -p "$TARGET/agents"
mkdir -p "$TARGET/skills/"{task-auto,task-impl,task-plan,task-research,task-review}

# Array declarations
SILENT_SRC=(); SILENT_DEST=()
OLDER_SRC=();  OLDER_DEST=()
INSTALLED=0
SKIPPED=0

# Classify agents
for agent in "$SCRIPT_DIR/agents"/*.md; do
    name=$(basename "$agent")
    classify_file "$agent" "$TARGET/agents/$name"
done

# Classify skills
for skill_dir in "$SCRIPT_DIR/skills"/*/; do
    skill_name=$(basename "$skill_dir")
    classify_file "$skill_dir/SKILL.md" "$TARGET/skills/$skill_name/SKILL.md"
done

# Downgrade prompt (single, covering all older-source files)
OVERWRITE_OLDER=false
if [[ ${#OLDER_SRC[@]} -gt 0 ]]; then
    COUNT=${#OLDER_SRC[@]}
    if [[ "${LISSOM_YES:-}" == "1" ]]; then
        OVERWRITE_OLDER=true
    else
        REPLY="n"
        {
            printf "%d installed file(s) are newer than the source. Overwrite all? [y/N] " \
                "$COUNT" > /dev/tty \
            && read -n 1 -r < /dev/tty \
            && echo > /dev/tty
        } 2>/dev/null || true
        [[ $REPLY =~ ^[Yy]$ ]] && OVERWRITE_OLDER=true
    fi
fi

# Silent copies (new files, same version, source-newer)
for i in "${!SILENT_SRC[@]}"; do
    cp "${SILENT_SRC[$i]}" "${SILENT_DEST[$i]}"
    INSTALLED=$((INSTALLED + 1))
done

# Downgrade copies
if $OVERWRITE_OLDER; then
    for i in "${!OLDER_SRC[@]}"; do
        cp "${OLDER_SRC[$i]}" "${OLDER_DEST[$i]}"
        INSTALLED=$((INSTALLED + 1))
    done
else
    SKIPPED=$((SKIPPED + ${#OLDER_SRC[@]}))
fi

# Print summary
echo ""
echo "Installation complete!"
echo "Installed $INSTALLED files to $TARGET"
echo "Skipped $SKIPPED existing files"
echo ""
echo "Next steps:"
echo "- Invoke the task-auto skill to run the full dev cycle"

# Clean up temp directory used when fetching from GitHub
if [[ -n "$CLEANUP_TMPDIR" ]]; then
    rm -rf "$CLEANUP_TMPDIR"
fi
