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

# Resolve model inclusion for an agent file installation.
# Sets two nameref variables:
#   model_include  — "true" if a model field should appear in output
#   model_value    — explicit model value to use (empty = use format default)
# Decision:
#   - dest exists with a model field → preserve existing (model_value = existing)
#   - new install + add_model_field=true → include flag on, value empty (format fills default)
#   - otherwise → no model
resolve_agent_model() {
    local src="$1" dest="$2" add_model_field="$3"
    local -n _include="$4" _value="$5"

    if [[ -f "$dest" ]]; then
        local existing
        existing=$(get_model "$dest")
        if [[ -n "$existing" ]]; then
            _include="true"; _value="$existing"
        else
            _include="false"; _value=""
        fi
        return
    fi
    if $add_model_field; then
        _include="true"; _value=""
    else
        _include="false"; _value=""
    fi
}

# Copy a file with format-specific handling and conversion.
# Uses path-type dispatch (agent | skill | other) to invoke the correct strategy
# function for the given target_format.  Adding a new format requires only
# defining _convert_{agent,skill,other}_${format}.
# Args: src, dest, target_format, add_model_field
copy_with_conversion() {
    local src="$1" dest="$2" target_format="$3" add_model_field="$4"

    if [[ "$(basename "$dest")" == "user_preference_questions.json" ]]; then
        cp "$src" "$dest"; return 0
    fi

    local path_type="other"
    local model_include model_value
    if [[ "$dest" == *"/agents/"*.md ]]; then
        path_type="agent"
        resolve_agent_model "$src" "$dest" "$add_model_field" model_include model_value
    elif [[ "$dest" == *"/skills/"*"/SKILL.md" ]]; then
        path_type="skill"
    fi

    "_convert_${path_type}_${target_format}" "$src" "$dest" "$model_include" "$model_value"
}

# ── Claude Code strategy ────────────────────────────────────────────

_convert_agent_claude() {
    local src="$1" dest="$2" model_include="$3" model_value="$4"

    if [[ -f "$dest" ]] && ! validate_yaml_frontmatter "$dest"; then
        echo "Error: $dest has malformed YAML frontmatter." >&2
        echo "Please fix or remove this file manually and re-run installation." >&2
        return 1
    fi

    local src_content
    src_content=$(cat "$src")
    if [[ -n "$model_value" ]]; then
        add_model_to_content "$src_content" "$model_value" > "$dest"
    elif [[ "$model_include" == "true" ]]; then
        local default_model
        default_model=$(get_default_model "$(basename "$dest")")
        if [[ -n "$default_model" ]]; then
            add_model_to_content "$src_content" "$default_model" > "$dest"
        else
            cp "$src" "$dest"
        fi
    else
        cp "$src" "$dest"
    fi
}

_convert_skill_claude()   { cp "$1" "$2"; }
_convert_other_claude()   { cp "$1" "$2"; }

# ── Opencode strategy ───────────────────────────────────────────────

_convert_agent_opencode() {
    local src="$1" dest="$2" model_include="$3" model_value="$4"

    if ! validate_yaml_frontmatter "$src"; then
        echo "Error: $src has malformed YAML frontmatter." >&2
        return 1
    fi

    local src_content agent_name
    src_content=$(cat "$src")
    agent_name="$(basename "$dest" .md)"
    opencode_format_agent_file "$src_content" "$agent_name" "$model_include" "$model_value" > "$dest"
}

_convert_skill_opencode() {
    local src="$1" dest="$2"
    local src_content
    src_content=$(cat "$src")
    opencode_rewrite_body_tools "$src_content" > "$dest"
}

_convert_other_opencode() { cp "$1" "$2"; }

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

# Collect agent→model mappings from installed agent files.
# Populates the associative array named by $2.  Returns true if at least one model found.
# Args: agents_directory, result_assoc_array_name
collect_agent_models() {
    local agents_dir="$1"
    local -n result="$2"
    local found=false
    local f
    for f in "$agents_dir"/*.md; do
        [[ -f "$f" ]] || continue
        local model
        model=$(get_model "$f")
        [[ -n "$model" ]] || continue
        result[$(basename "$f" .md)]="$model"
        found=true
    done
    $found
}
