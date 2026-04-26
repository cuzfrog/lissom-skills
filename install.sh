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
             "$SCRIPT_DIR/skills/task-review" \
             "$SCRIPT_DIR/templates"
    for agent in code-reviewer task-implementer task-planner task-researcher; do
        curl -fsSL "$REPO/agents/$agent.md" -o "$SCRIPT_DIR/agents/$agent.md"
    done
    for skill in task-auto task-impl task-plan task-research task-review; do
        curl -fsSL "$REPO/skills/$skill/SKILL.md" -o "$SCRIPT_DIR/skills/$skill/SKILL.md"
    done
    curl -fsSL "$REPO/templates/CLAUDE.md" -o "$SCRIPT_DIR/templates/CLAUDE.md"
fi

# Create directory structure
echo "Installing to $TARGET..."
mkdir -p "$TARGET/agents"
mkdir -p "$TARGET/skills/"{task-auto,task-impl,task-plan,task-research,task-review}

# Counters
INSTALLED=0
SKIPPED=0

# Function to prompt for overwrite
prompt_overwrite() {
    local file="$1"
    read -p "File $file already exists. Overwrite? [y/N] " -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]]
}

# Copy agents
for agent in "$SCRIPT_DIR/agents"/*.md; do
    name=$(basename "$agent")
    dest="$TARGET/agents/$name"
    
    if [[ -f "$dest" ]]; then
        if prompt_overwrite "$dest"; then
            cp "$agent" "$dest"
            INSTALLED=$((INSTALLED + 1))
        else
            SKIPPED=$((SKIPPED + 1))
        fi
    else
        cp "$agent" "$dest"
        INSTALLED=$((INSTALLED + 1))
    fi
done

# Copy skills
for skill_dir in "$SCRIPT_DIR/skills"/*/; do
    skill_name=$(basename "$skill_dir")
    src="$skill_dir/SKILL.md"
    dest="$TARGET/skills/$skill_name/SKILL.md"
    
    if [[ -f "$dest" ]]; then
        if prompt_overwrite "$dest"; then
            cp "$src" "$dest"
            INSTALLED=$((INSTALLED + 1))
        else
            SKIPPED=$((SKIPPED + 1))
        fi
    else
        cp "$src" "$dest"
        INSTALLED=$((INSTALLED + 1))
    fi
done

# Copy CLAUDE.md template
src="$SCRIPT_DIR/templates/CLAUDE.md"
dest="$TARGET/CLAUDE.md"

if [[ -f "$dest" ]]; then
    if prompt_overwrite "$dest"; then
        cp "$src" "$dest"
        INSTALLED=$((INSTALLED + 1))
    else
        SKIPPED=$((SKIPPED + 1))
    fi
else
    cp "$src" "$dest"
    INSTALLED=$((INSTALLED + 1))
fi

# Print summary
echo ""
echo "Installation complete!"
echo "Installed $INSTALLED files to $TARGET"
echo "Skipped $SKIPPED existing files"
echo ""
echo "Next steps:"
echo "- Edit $TARGET/CLAUDE.md to describe your project"
echo "- Create .dev/tasks/<ID>/Specs.md for your first task"
echo "- Invoke the task-auto skill to run the full dev cycle"

# Clean up temp directory used when fetching from GitHub
if [[ -n "$CLEANUP_TMPDIR" ]]; then
    rm -rf "$CLEANUP_TMPDIR"
fi
