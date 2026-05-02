#!/usr/bin/env bash

set -e  # Exit on error

# Source constants and utility functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/scripts/lib/constants.sh"
source "$SCRIPT_DIR/scripts/lib/conversion.sh"
source "$SCRIPT_DIR/scripts/lib/ui.sh"

# Parse arguments
if [[ -n "$1" ]]; then
    echo "Usage: $0"
    exit 1
fi

# Determine target directory (prompt user for .claude/ vs .opencode/)
# Initialize model preference (only relevant for .opencode/)
DIALOG_TOOL=$(detect_dialog_tool)
INSTALL_TARGET=$(prompt_target_directory "$DIALOG_TOOL")
TARGET="./$INSTALL_TARGET"
TARGET_FORMAT="claude"  # default to Claude Code format
ADD_MODEL_FIELD=false

if [[ "$INSTALL_TARGET" == ".opencode" ]]; then
    TARGET_FORMAT="opencode"
    # For Opencode target, ask about model preference
    INCLUDE_MODEL=$(prompt_model_preference "$DIALOG_TOOL")
    if [[ "$INCLUDE_MODEL" == "true" ]]; then
        ADD_MODEL_FIELD=true
    fi
fi

# For .claude/ target, also handle the legacy model preference prompt
if [[ "$INSTALL_TARGET" == ".claude" ]]; then
    # This will be set later after checking if there are new agent files
    :
fi

# When piped via curl, BASH_SOURCE[0] is empty so SCRIPT_DIR falls back to CWD.
# If the repo files aren't present, download them from GitHub into a temp dir.
REPO="https://raw.githubusercontent.com/cuzfrog/lissom-skills/main"
CLEANUP_TMPDIR=""
if [[ ! -f "$SCRIPT_DIR/agents/lissom-researcher.md" ]] && [[ ! -f "$SCRIPT_DIR/agents/task-researcher.md" ]]; then
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

# Extract the `model:` value from a file's YAML frontmatter.
# Returns empty string if no model field is found.
get_model() {
    local file="$1"
    local in_fm=0
    while IFS= read -r line; do
        if [[ "$line" == "---" ]]; then
            if [[ $in_fm -eq 0 ]]; then
                in_fm=1
            else
                break
            fi
        elif [[ $in_fm -eq 1 ]] && [[ "$line" =~ ^model:[[:space:]]*(.+)$ ]]; then
            echo "${BASH_REMATCH[1]}"
            return
        fi
    done < "$file"
    echo ""
}

# Validate YAML frontmatter structure.
# Returns 0 if valid, 1 if malformed (missing closing --- or unopened frontmatter).
validate_yaml_frontmatter() {
    local file="$1"
    local in_fm=0
    local has_opening=0
    local has_closing=0
    while IFS= read -r line; do
        if [[ "$line" == "---" ]]; then
            if [[ $in_fm -eq 0 ]]; then
                in_fm=1
                has_opening=1
            else
                has_closing=1
                break
            fi
        fi
    done < "$file"
    [[ $has_opening -eq 1 ]] && [[ $has_closing -eq 1 ]]
}

# Insert model field into file content after the tools: line.
# Args: content (as string), model value
# Writes modified content to stdout.
add_model_to_content() {
    local content="$1"
    local model="$2"
    local in_fm=0
    local found_tools=0
    while IFS= read -r line; do
        if [[ "$line" == "---" ]]; then
            if [[ $in_fm -eq 0 ]]; then
                echo "$line"
                in_fm=1
            else
                # End of frontmatter; insert model before closing --- if not already added
                if [[ $found_tools -eq 0 ]]; then
                    echo "model: $model"
                fi
                echo "$line"
                in_fm=0
            fi
        elif [[ $in_fm -eq 1 ]] && [[ "$line" =~ ^tools: ]]; then
            echo "$line"
            echo "model: $model"
            found_tools=1
        else
            echo "$line"
        fi
    done <<< "$content"
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

# Variable declarations
ADD_MODEL_FIELD=false
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
    # Also classify supporting files for lissom-auto and task-auto
    if [[ "$skill_name" == "lissom-auto" || "$skill_name" == "task-auto" ]]; then
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

# Model configuration prompt (only for .claude/ format)
if [[ "$TARGET_FORMAT" == "claude" ]] && [[ $NEW_AGENT_COUNT -gt 0 ]]; then
    if [[ "${LISSOM_YES:-}" == "1" ]]; then
        ADD_MODEL_FIELD=true
    elif [[ "${LISSOM_NO:-}" == "1" ]]; then
        ADD_MODEL_FIELD=false
    else
        REPLY=""
        {
            printf "Add default model settings to agent files? [Y/n] " > /dev/tty \
            && read -n 1 -r < /dev/tty \
            && echo > /dev/tty
        } 2>/dev/null || true
        if [[ -z "$REPLY" ]] || [[ "$REPLY" =~ ^[Yy]([Ee][Ss])?$ ]]; then
            ADD_MODEL_FIELD=true
        elif [[ "$REPLY" =~ ^[Nn]([Oo])?$ ]]; then
            ADD_MODEL_FIELD=false
        else
            ADD_MODEL_FIELD=true
        fi
    fi
fi

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

# Helper function to copy a file with format-specific handling and conversion
# Handles .claude/ (Claude Code format) and .opencode/ (Opencode format) with conversion
copy_with_conversion() {
    local src="$1" dest="$2" is_new="$3"
    local basename_dest
    basename_dest=$(basename "$dest")
    local dirname_dest
    dirname_dest=$(basename "$(dirname "$dest")")
    
    # JSON files (user_preference_questions.json) are copied verbatim regardless of format
    if [[ "$basename_dest" == "user_preference_questions.json" ]]; then
        cp "$src" "$dest"
        return 0
    fi
    
    # For .claude/ format, use existing model-handling logic
    if [[ "$TARGET_FORMAT" == "claude" ]]; then
        # Only process agent files; copy others directly
        if [[ "$dest" != *"/agents/"*.md ]]; then
            cp "$src" "$dest"
            return 0
        fi
        
        # Validate existing file's YAML if it exists
        if [[ -f "$dest" ]]; then
            if ! validate_yaml_frontmatter "$dest"; then
                echo "Error: $dest has malformed YAML frontmatter." >&2
                echo "Please fix or remove this file manually and re-run installation." >&2
                return 1
            fi
        fi
        
        # If this is an upgrade (dest exists), preserve existing model field (or absence)
        if [[ -f "$dest" ]]; then
            local existing_model
            existing_model=$(get_model "$dest")
            local src_content
            src_content=$(cat "$src")
            
            # If existing file has a model field, preserve it
            if [[ -n "$existing_model" ]]; then
                add_model_to_content "$src_content" "$existing_model" > "$dest"
            else
                # No model field in existing file → preserve absence
                cp "$src" "$dest"
            fi
        else
            # New file: add model field if user accepted prompt
            if $ADD_MODEL_FIELD; then
                local default_model
                default_model=$(get_default_model "$basename_dest")
                if [[ -n "$default_model" ]]; then
                    local src_content
                    src_content=$(cat "$src")
                    add_model_to_content "$src_content" "$default_model" > "$dest"
                else
                    cp "$src" "$dest"
                fi
            else
                cp "$src" "$dest"
            fi
        fi
        return 0
    fi
    
    # For .opencode/ format, apply conversion
    if [[ "$TARGET_FORMAT" == "opencode" ]]; then
        # JSON files are already handled above
        
        # For agent files: convert frontmatter and tool names in body
        if [[ "$dest" == *"/agents/"*.md ]]; then
            local src_content
            src_content=$(cat "$src")
            # Extract agent name from filename (e.g. "lissom-researcher.md" -> "lissom-researcher")
            local agent_name="${basename_dest%.md}"
            # Convert and write to dest
            convert_agent_file "$src_content" "$agent_name" "$ADD_MODEL_FIELD" > "$dest"
            return 0
        fi
        
        # For skill files: convert tool names in body but keep frontmatter
        if [[ "$dest" == *"/skills/"*"/SKILL.md" ]]; then
            local src_content
            src_content=$(cat "$src")
            # Only convert tool names in body, skill frontmatter stays unchanged
            convert_tool_names_in_body "$src_content" > "$dest"
            return 0
        fi
        
        # For other files, copy as-is
        cp "$src" "$dest"
        return 0
    fi
    
    # Fallback
    cp "$src" "$dest"
    return 0
}


# Silent copies (new files, same version, source-newer)
for i in "${!SILENT_SRC[@]}"; do
    mkdir -p "$(dirname "${SILENT_DEST[$i]}")"
    is_new="false"
    [[ ! -f "${SILENT_DEST[$i]}" ]] && is_new="true"
    if ! copy_with_conversion "${SILENT_SRC[$i]}" "${SILENT_DEST[$i]}" "$is_new"; then
        echo "Installation failed." >&2
        exit 1
    fi
    INSTALLED=$((INSTALLED + 1))
done

# Downgrade copies
if $OVERWRITE_OLDER; then
    for i in "${!OLDER_SRC[@]}"; do
        mkdir -p "$(dirname "${OLDER_DEST[$i]}")"
        if ! copy_with_conversion "${OLDER_SRC[$i]}" "${OLDER_DEST[$i]}" "false"; then
            echo "Installation failed." >&2
            exit 1
        fi
        INSTALLED=$((INSTALLED + 1))
    done
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
    AGENT_FILES=("$TARGET/agents"/*.md)
    declare -A AGENT_MODELS
    
    # Collect agents with model fields
    for agent_file in "${AGENT_FILES[@]}"; do
        if [[ -f "$agent_file" ]]; then
            model_value=$(get_model "$agent_file")
            if [[ -n "$model_value" ]]; then
                MODELS_FOUND=true
                agent_name=$(basename "$agent_file" .md)
                AGENT_MODELS["$agent_name"]="$model_value"
            fi
        fi
    done
    
    # Display table if at least one agent has a model
    if $MODELS_FOUND; then
        echo ""
        echo "┌─────────────────────────────┬───────────┐"
        echo "│ Agent                       │ Model     │"
        echo "├─────────────────────────────┼───────────┤"
        
        # Sort agent names and display rows
        for agent_name in $(printf '%s\n' "${!AGENT_MODELS[@]}" | sort); do
            printf "│ %-27s │ %-9s │\n" "$agent_name" "${AGENT_MODELS[$agent_name]}"
        done
        
        echo "└─────────────────────────────┴───────────┘"
    fi
fi
if $MODELS_FOUND; then
    echo "The model field can be modified in the agent files at .claude/agents/"
fi
echo ""
echo "Next steps:"
echo "- A sample Specs.md has been created at .lissom/tasks/T1/Specs.md"
echo "- Invoke '/lissom-auto T1', get interviewed and wait for the job to be done!"

# Clean up temp directory used when fetching from GitHub
if [[ -n "$CLEANUP_TMPDIR" ]]; then
    rm -rf "$CLEANUP_TMPDIR"
fi
