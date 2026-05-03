#!/usr/bin/env bash

set -e  # Exit on error

# Source constants and utility functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[[ "$(basename "$SCRIPT_DIR")" == "scripts" ]] && SCRIPT_DIR="$(dirname "$SCRIPT_DIR")"
source "$SCRIPT_DIR/scripts/lib/common.sh"
source "$SCRIPT_DIR/scripts/lib/constants.sh"
source "$SCRIPT_DIR/scripts/lib/opencode.sh"
source "$SCRIPT_DIR/scripts/lib/qwen.sh"
source "$SCRIPT_DIR/scripts/lib/gemini.sh"
source "$SCRIPT_DIR/scripts/lib/ui.sh"
source "$SCRIPT_DIR/scripts/lib/frontmatter.sh"
source "$SCRIPT_DIR/scripts/lib/install_ops.sh"

parse_no_args "$@"

# Determine target directory and format
INSTALL_TARGET=$(prompt_target_directory)
TARGET="./$INSTALL_TARGET"
TARGET_FORMAT=$(get_target_format "$INSTALL_TARGET")
ADD_MODEL_FIELD=false

# Check for alternate target directories and warn if they have lissom installations
TARGET_HAS_LISSOM=false
has_lissom_installation "$TARGET" && TARGET_HAS_LISSOM=true
if ! $TARGET_HAS_LISSOM; then
    WARN_TARGETS=()
    for alt_target in "${!TARGET_CONFIG[@]}"; do
        [[ "$alt_target" == "$INSTALL_TARGET" ]] && continue
        has_lissom_installation "$alt_target" && WARN_TARGETS+=("$alt_target")
    done
    if [[ ${#WARN_TARGETS[@]} -gt 0 ]]; then
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        for alt in "${WARN_TARGETS[@]}"; do
            echo "⚠️  Warning: Found existing installation in $alt/"
        done
        echo ""
        echo "You are installing to $INSTALL_TARGET/, but the director(ies) above already contain"
        echo "lissom-skills files. Consider running uninstall.sh first to remove the"
        echo "old installation(s) and avoid confusion."
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        
        # Prompt for confirmation unless LISSOM_YES is set
        if [[ -z "$LISSOM_YES" ]]; then
            read -p "Continue anyway? (y/N) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo "Installation cancelled."
                exit 0
            fi
        fi
    fi
fi

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

# Create directory structure
echo "Installing to $TARGET..."
mkdir -p "$TARGET/agents"

# Variable declarations
MODELS_FOUND=false

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

# Count new agent files
NEW_AGENT_COUNT=0
for i in "${!SILENT_DEST[@]}"; do
    if [[ "${SILENT_DEST[$i]}" == */agents/*.md ]] && [[ ! -f "${SILENT_DEST[$i]}" ]]; then
        NEW_AGENT_COUNT=$((NEW_AGENT_COUNT + 1))
    fi
done

# Model configuration prompt — unified for all target formats
if [[ $NEW_AGENT_COUNT -gt 0 ]]; then
    model_default=$(get_model_default "$TARGET_FORMAT")
    INCLUDE_MODEL=$(prompt_model_preference "$model_default")
    [[ "$INCLUDE_MODEL" == "true" ]] && ADD_MODEL_FIELD=true
fi

# Downgrade prompt (single, covering all older-source files)
OVERWRITE_OLDER=false
if [[ ${#OLDER_SRC[@]} -gt 0 ]]; then
    COUNT=${#OLDER_SRC[@]}
    if [[ "${LISSOM_YES:-}" == "1" ]]; then
        OVERWRITE_OLDER=true
    else
        REPLY="n"
        # Only prompt if stdin is a TTY (interactive mode)
        if [[ -t 0 ]]; then
            {
                printf "%d installed file(s) are newer than the source. Overwrite all? [y/N] " \
                    "$COUNT" > /dev/tty \
                && read -n 1 -r < /dev/tty \
                && echo > /dev/tty
            } 2>/dev/null || true
        fi
        [[ $REPLY =~ ^[Yy]$ ]] && OVERWRITE_OLDER=true
    fi
fi

# Silent copies (new files, same version, source-newer)
install_files SILENT_SRC SILENT_DEST "$TARGET_FORMAT" "$ADD_MODEL_FIELD"

# Downgrade copies
if $OVERWRITE_OLDER; then
    install_files OLDER_SRC OLDER_DEST "$TARGET_FORMAT" "$ADD_MODEL_FIELD"
else
    SKIPPED=$((SKIPPED + ${#OLDER_SRC[@]}))
fi

# Create sample Specs.md only if absent
specs_dir=".lissom/tasks/T1"
specs_dest="$specs_dir/Specs.md"
if [[ ! -f "$specs_dest" ]]; then
    mkdir -p "$specs_dir"
    cp "$SCRIPT_DIR/templates/Specs.md" "$specs_dest"
    echo "Created sample $specs_dest"
fi

# Add .lissom/ to .gitignore if not already present
gitignore_msg="# We recommend not to commit development doc. If you want to stage the content, comment out this line."
if [[ -f ".gitignore" ]]; then
    if ! grep -q "^\.lissom/" ".gitignore"; then
        {
            echo ""
            echo "$gitignore_msg"
            echo ".lissom/"
        } >> ".gitignore"
        echo "Added .lissom/ to .gitignore"
    fi
else
    {
        echo "$gitignore_msg"
        echo ".lissom/"
    } > ".gitignore"
    echo "Created .gitignore with .lissom/"
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

# Display model configuration table if any agent has a model field
if [[ -d "$TARGET/agents" ]]; then
    declare -A AGENT_MODELS
    if collect_agent_models "$TARGET/agents" AGENT_MODELS; then
        MODELS_FOUND=true
        echo ""
        display_model_table AGENT_MODELS
    fi
fi
if $MODELS_FOUND; then
    echo "The model field can be modified in the agent files at $TARGET/agents/"
fi
echo ""
echo "Next steps:"
echo "- A sample Specs.md has been created at .lissom/tasks/T1/Specs.md"
echo "- Invoke '/lissom-auto T1', get interviewed and wait for the job to be done!"

# Clean up temp directory used when fetching from GitHub
if [[ -n "$CLEANUP_TMPDIR" ]]; then
    rm -rf "$CLEANUP_TMPDIR"
fi
