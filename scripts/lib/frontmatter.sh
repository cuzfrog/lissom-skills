#!/usr/bin/env bash
# Frontmatter parsing and manipulation functions for YAML frontmatter in .md files.

# Extract a named scalar value from a file's YAML frontmatter (e.g. "version", "model").
# Uses ^anchor so field names that are prefixes of each other do not collide.
# Returns empty string if field is not found.
_get_frontmatter_field() {
    local file="$1" field="$2"
    local in_fm=0
    while IFS= read -r line; do
        if [[ "$line" == "---" ]]; then
            if [[ $in_fm -eq 0 ]]; then in_fm=1; else break; fi
        elif [[ $in_fm -eq 1 ]] && [[ "$line" =~ ^$field:[[:space:]]*(.+)$ ]]; then
            echo "${BASH_REMATCH[1]}"
            return
        fi
    done < "$file"
    echo ""
}

# Extract a named field from an HTML comment on line 1 of the file.
# Format: <!-- key: value -->
# Returns the captured value, or empty string if not found.
_get_comment_field() {
    local file="$1" field="$2"
    local first_line
    read -r first_line < "$file" || true
    if [[ "$first_line" =~ ^\<\!--[[:space:]]*$field:[[:space:]]*(.+)[[:space:]]*--\>$ ]]; then
        echo "${BASH_REMATCH[1]}"
        return
    fi
    echo ""
}

get_version() {
    local file="$1"
    # Try comment format first (new source files)
    local comment_ver
    comment_ver=$(_get_comment_field "$file" "version")
    if [[ -n "$comment_ver" ]]; then
        echo "$comment_ver"
        return
    fi
    # Fall back to YAML frontmatter (backward-compat for old destination files)
    _get_frontmatter_field "$file" "version"
}
get_model()   { _get_frontmatter_field "$1" "model"; }

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
