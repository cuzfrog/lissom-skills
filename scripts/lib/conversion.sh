#!/usr/bin/env bash
# Conversion functions for transforming Claude Code format to Opencode format.

# Source the constants (tool mappings, model assignments)
CONVERSION_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$CONVERSION_SCRIPT_DIR/constants.sh"

# Parse the tools: line and extract comma-separated tool names
# Args: tools_line (e.g. "tools: Bash, Read, Write, ...")
# Returns: space-separated list of tool names (e.g. "Bash Read Write ...")
parse_tools_line() {
    local tools_line="$1"
    # Remove "tools: " prefix and split on comma, trimming whitespace
    local tools_part="${tools_line#*: }"
    echo "$tools_part" | tr ',' '\n' | sed 's/^[[:space:]]*//; s/[[:space:]]*$//' | tr '\n' ' '
}

# Convert array of tool names to Opencode permission YAML block
# Args: array of tool names (passed as space-separated string)
# Returns: YAML permission block (indented 2 spaces)
tools_to_permissions() {
    local tools="$1"
    echo "permission:"
    for tool in $tools; do
        local permission_key="${TOOL_TO_PERMISSION[$tool]}"
        if [[ -n "$permission_key" ]]; then
            printf "  %s: allow\n" "$permission_key"
        fi
    done
}

# Convert tool names in body text from Claude Code to Opencode format
# Replaces tool names inside backticks (e.g. `AskUserQuestion` -> `question`)
# Args: content (reads from stdin or argument)
# Returns: transformed content to stdout
convert_tool_names_in_body() {
    local content="$1"
    
    # Build sed expression for all tool name mappings
    local sed_expr=""
    for claude_tool in "${!TOOL_NAME_MAPPING[@]}"; do
        local opencode_tool="${TOOL_NAME_MAPPING[$claude_tool]}"
        # Escape backticks in sed
        sed_expr+="s/\`${claude_tool}\`/\`${opencode_tool}\`/g; "
    done
    
    # Apply all replacements
    echo "$content" | sed "$sed_expr"
}

# Convert Claude Code agent frontmatter to Opencode format
# Args:
#   content - the full agent file content (reads from stdin if empty)
#   agent_name - agent name (e.g. "lissom-researcher")
#   include_model - boolean "true" or "false" whether to include model field
# Returns: transformed content to stdout
#
# Transform rules:
# - Keep name, version, description from original
# - Remove tools: line
# - Add mode: subagent
# - Add temperature: 0.1
# - Add model: field if include_model is true
# - Add permission: block based on tools
# - Field ordering: name, description, version, mode, model (optional), temperature, permission
convert_agent_frontmatter() {
    local content="$1"
    local agent_name="$2"
    local include_model="${3:-false}"
    
    local in_fm=0
    local fm_end_line=0
    local line_num=0
    local name_field=""
    local description_field=""
    local version_field=""
    local tools_line=""
    local other_fields=""
    
    # First pass: extract frontmatter fields
    while IFS= read -r line; do
        line_num=$((line_num + 1))
        if [[ "$line" == "---" ]]; then
            if [[ $in_fm -eq 0 ]]; then
                in_fm=1
                # Output opening ---
                echo "$line"
            else
                # End of frontmatter
                fm_end_line=$line_num
                break
            fi
        elif [[ $in_fm -eq 1 ]]; then
            if [[ "$line" =~ ^name:[[:space:]]*(.*)$ ]]; then
                name_field="name: ${BASH_REMATCH[1]}"
            elif [[ "$line" =~ ^description:[[:space:]]*(.*)$ ]]; then
                description_field="description: ${BASH_REMATCH[1]}"
            elif [[ "$line" =~ ^version:[[:space:]]*(.*)$ ]]; then
                version_field="version: ${BASH_REMATCH[1]}"
            elif [[ "$line" =~ ^tools:[[:space:]]*(.*)$ ]]; then
                tools_line="${BASH_REMATCH[1]}"
            elif [[ -n "$line" ]] && [[ "$line" != "---" ]]; then
                # Store other fields we don't recognize (preserve unknown fields)
                other_fields+="$line"$'\n'
            fi
        fi
    done <<< "$content"
    
    # Output converted frontmatter in correct field order
    [[ -n "$name_field" ]] && echo "$name_field"
    [[ -n "$description_field" ]] && echo "$description_field"
    [[ -n "$version_field" ]] && echo "$version_field"
    
    echo "mode: subagent"
    
    if [[ "$include_model" == "true" ]]; then
        local model_value
        model_value=$(get_opencode_model "$agent_name")
        echo "model: $model_value"
    fi
    
    echo "temperature: 0.1"
    
    # Generate permission block from tools
    if [[ -n "$tools_line" ]]; then
        local tools_array
        tools_array=$(parse_tools_line "tools: $tools_line")
        tools_to_permissions "$tools_array"
    fi
    
    # Output closing ---
    echo "---"
    
    # Output body (everything after the closing ---)
    if [[ $fm_end_line -gt 0 ]]; then
        local body_start=$((fm_end_line + 1))
        echo "$content" | tail -n +$body_start
    fi
}

# Wrapper function to convert both frontmatter and body text
# This is the main entry point for agent file conversion
# Args:
#   content - the full agent file content
#   agent_name - agent name for model assignment
#   include_model - boolean "true" or "false"
# Returns: fully converted content to stdout
convert_agent_file() {
    local content="$1"
    local agent_name="$2"
    local include_model="${3:-false}"
    
    # First convert frontmatter
    local temp_converted
    temp_converted=$(convert_agent_frontmatter "$content" "$agent_name" "$include_model")
    
    # Then convert tool names in body
    convert_tool_names_in_body "$temp_converted"
}
