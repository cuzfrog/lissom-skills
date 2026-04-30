#!/usr/bin/env bash

set -e  # Exit on error

AGENTS=(lissom-implementer lissom-planner lissom-researcher lissom-reviewer lissom-specs-reviewer)
SKILLS=(lissom-auto lissom-impl lissom-plan lissom-research lissom-review)

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
if [[ ! -f "$SCRIPT_DIR/agents/lissom-researcher.md" ]]; then
    SCRIPT_DIR="$(mktemp -d)"
    CLEANUP_TMPDIR="$SCRIPT_DIR"
    echo "Fetching files from GitHub..."
    mkdir -p "$SCRIPT_DIR/agents" "$SCRIPT_DIR/templates"
    for skill in "${SKILLS[@]}"; do mkdir -p "$SCRIPT_DIR/skills/$skill"; done
    for agent in "${AGENTS[@]}"; do
        curl -fsSL "$REPO/agents/$agent.md" -o "$SCRIPT_DIR/agents/$agent.md"
    done
    for skill in "${SKILLS[@]}"; do
        curl -fsSL "$REPO/skills/$skill/SKILL.md" -o "$SCRIPT_DIR/skills/$skill/SKILL.md"
        # Download supporting files for lissom-auto
        if [[ "$skill" == "lissom-auto" ]]; then
            curl -fsSL "$REPO/skills/$skill/user_preference_questions.json" -o "$SCRIPT_DIR/skills/$skill/user_preference_questions.json" || true
        fi
    done
    curl -fsSL "$REPO/templates/Specs.md" -o "$SCRIPT_DIR/templates/Specs.md"
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
mkdir -p "$TARGET/skills/"{lissom-auto,lissom-impl,lissom-plan,lissom-research,lissom-review}

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
    # Also classify supporting files for lissom-auto
    if [[ "$skill_name" == "lissom-auto" ]]; then
        [[ -f "$skill_dir/user_preference_questions.json" ]] && classify_file "$skill_dir/user_preference_questions.json" "$TARGET/skills/$skill_name/user_preference_questions.json"
    fi
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

# Create sample Specs.md only in project mode and only if absent
if [[ "$MODE" == "project" ]]; then
    specs_dir=".lissom/tasks/T1"
    specs_dest="$specs_dir/Specs.md"
    if [[ ! -f "$specs_dest" ]]; then
        mkdir -p "$specs_dir"
        cp "$SCRIPT_DIR/templates/Specs.md" "$specs_dest"
        echo "Created sample $specs_dest"
    fi

    # Add .lissom/ to .gitignore if not already present
    if [[ -f ".gitignore" ]]; then
        if ! grep -q "^\.lissom/" ".gitignore"; then
            {
                echo ""
                echo "# We recommend not to commit development doc. If you want to stage the content, comment out this line."
                echo ".lissom/"
            } >> ".gitignore"
            echo "Added .lissom/ to .gitignore"
        fi
    else
        {
            echo "# We recommend not to commit development doc. If you want to stage the content, comment out this line."
            echo ".lissom/"
        } > ".gitignore"
        echo "Created .gitignore with .lissom/"
    fi
fi

# Print summary
echo ""
echo "┌─┐"
echo "│L│░ LISSOM"
echo "└─┘  SKILLS"
echo ""
echo "Installation complete!"
echo "Installed $INSTALLED files to $TARGET"
echo "Skipped $SKIPPED existing files"
echo ""
echo "Next steps:"
if [[ "$MODE" == "project" ]]; then
    echo "- A sample Specs.md has been created at .lissom/tasks/T1/Specs.md"
fi
echo "- Invoke '/lissom-auto T1', get interviewed and wait for the job to be done!"

# Clean up temp directory used when fetching from GitHub
if [[ -n "$CLEANUP_TMPDIR" ]]; then
    rm -rf "$CLEANUP_TMPDIR"
fi
