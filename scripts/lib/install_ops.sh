#!/usr/bin/env bash
# Install operation utilities for the lissom-skills installer.

# classify_file SRC DEST
# Appends to SILENT_SRC/SILENT_DEST or OLDER_SRC/OLDER_DEST
# Requires: get_version (from frontmatter.sh), SILENT_SRC, SILENT_DEST,
#           OLDER_SRC, OLDER_DEST arrays (declared by caller)
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

# Copy a file with format-specific handling and conversion.
# Handles .claude/ (Claude Code format) and .opencode/ (Opencode format) with conversion.
# Args: src, dest, target_format, add_model_field
copy_with_conversion() {
    local src="$1" dest="$2" target_format="$3" add_model_field="$4"
    local basename_dest
    basename_dest=$(basename "$dest")
    
    # JSON files (user_preference_questions.json) are copied verbatim regardless of format
    if [[ "$basename_dest" == "user_preference_questions.json" ]]; then
        cp "$src" "$dest"
        return 0
    fi
    
    # For .claude/ format, use existing model-handling logic
    if [[ "$target_format" == "claude" ]]; then
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
            if $add_model_field; then
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
    if [[ "$target_format" == "opencode" ]]; then
        # JSON files are already handled above
        
        # For agent files: convert frontmatter and tool names in body
        if [[ "$dest" == *"/agents/"*.md ]]; then
            # Validate source frontmatter before conversion
            if ! validate_yaml_frontmatter "$src"; then
                echo "Error: $src has malformed YAML frontmatter." >&2
                return 1
            fi
            local src_content
            src_content=$(cat "$src")
            # Extract agent name from filename (e.g. "lissom-researcher.md" -> "lissom-researcher")
            local agent_name="${basename_dest%.md}"
            # Convert and write to dest
            convert_agent_file "$src_content" "$agent_name" "$add_model_field" > "$dest"
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

# Check whether a target directory has lissom agent files installed.
# Returns 0 (true) if target/agents/lissom-*.md exist, 1 otherwise.
has_lissom_installation() {
    local target="$1"
    [[ -d "$target/agents" ]] && [[ -n "$(ls -A "$target"/agents/lissom-* 2>/dev/null)" ]]
}

# Install files from an array pair (source → destination) with format conversion.
# Updates global INSTALLED counter.
# Args: source_array_name, dest_array_name, target_format, add_model_field
install_files() {
    local -n src_array="$1"
    local -n dest_array="$2"
    local target_format="$3" add_model_field="$4"
    local i
    for i in "${!src_array[@]}"; do
        mkdir -p "$(dirname "${dest_array[$i]}")"
        if ! copy_with_conversion "${src_array[$i]}" "${dest_array[$i]}" "$target_format" "$add_model_field"; then
            echo "Installation failed." >&2
            exit 1
        fi
        INSTALLED=$((INSTALLED + 1))
    done
}
