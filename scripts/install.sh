#!/usr/bin/env bash
set -e

REPO="${LISSOM_REPO:-https://github.com/cuzfrog/lissom-skills}"
NO_OVERWRITE_FRONTMATTER_FIELDS=('model' 'temperature')

cleanup() { rm -f lissom-skills-tmp.zip; }
trap cleanup EXIT

parse_no_args() {
    if [[ -n "$1" ]]; then
        echo "Usage: install.sh"
        exit 1
    fi
}

prompt_target_directory() {
    [[ -n "${LISSOM_TARGET:-}" ]] && { echo "$LISSOM_TARGET"; return 0; }
    [[ "${LISSOM_YES:-}" == "1" ]] && { echo ".claude"; return 0; }

    if [[ -t 0 ]]; then
        echo "Select installation target:" >&2
        select _ in ".claude (Claude Code and most CLIs)" ".opencode (Opencode)" ".qwen (Qwen Code)" ".gemini (Gemini CLI)"; do
            case "$REPLY" in
                1) echo ".claude"; return 0 ;;
                2) echo ".opencode"; return 0 ;;
                3) echo ".qwen"; return 0 ;;
                4) echo ".gemini"; return 0 ;;
                *) echo "Invalid choice. Try again." >&2 ;;
            esac
        done
    fi

    if [[ -t 2 ]] && ( : </dev/tty ) 2>/dev/null; then
        echo "Select installation target:" >&2
        echo "1) .claude (Claude Code and most CLIs)" >&2
        echo "2) .opencode (Opencode)" >&2
        echo "3) .qwen (Qwen Code)" >&2
        echo "4) .gemini (Gemini CLI)" >&2
        echo -n "Choice: " >&2
        read -r _ui_reply </dev/tty
        case "${_ui_reply:-1}" in
            1|"") echo ".claude" ;;
            2) echo ".opencode" ;;
            3) echo ".qwen" ;;
            4) echo ".gemini" ;;
            *) echo "Invalid choice, defaulting to .claude." >&2; echo ".claude" ;;
        esac
        return 0
    fi

    echo ".claude"
}

prompt_overwrite() {
    local dir="$1"
    if [[ "${LISSOM_YES:-}" == "1" ]]; then
        echo "true"; return 0
    elif ( : </dev/tty ) 2>/dev/null; then
        echo -n "$dir already exists and is not empty. Overwrite all files? (y/N) " >&2
        read -n 1 -r _ow_reply </dev/tty
        echo >&2
        [[ $_ow_reply =~ ^[Yy]$ ]] && echo "true" || echo "false"
        return 0
    fi
    echo "false"
}

if [[ "$1" == "--source-only" ]]; then
    [[ "${BASH_SOURCE[0]}" != "${0}" ]] && return || exit 0
fi

parse_no_args "$@"

INSTALL_TARGET=$(prompt_target_directory)
TARGET="./$INSTALL_TARGET"

case "$INSTALL_TARGET" in
    .claude)   ZIP="lissom-skills-claude.zip" ;;
    .opencode) ZIP="lissom-skills-opencode.zip" ;;
    .qwen)     ZIP="lissom-skills-qwen.zip" ;;
    .gemini)   ZIP="lissom-skills-gemini.zip" ;;
    *) echo "Error: Unknown target $INSTALL_TARGET" >&2; exit 1 ;;
esac

if [[ -d "$TARGET" ]] && [[ -n "$(ls -A "$TARGET" 2>/dev/null)" ]]; then
    if [[ "$(prompt_overwrite "$TARGET")" != "true" ]]; then
        echo "Installation cancelled."
        exit 0
    fi
fi

ZIP_URL="$REPO/releases/latest/download/$ZIP"
ZIP_FILE="lissom-skills-tmp.zip"
echo "Downloading $ZIP..."
curl -fsSL "$ZIP_URL" -o "$ZIP_FILE"

SAVED_KEYS=()
SAVED_VALUES=()

save_frontmatter_fields() {
    local dir="$1"
    local field value key
    while IFS= read -r -d '' file; do
        for field in "${NO_OVERWRITE_FRONTMATTER_FIELDS[@]}"; do
            value=$(sed -n "/^---$/,/^---$/ s|^${field}: *||p" "$file" | head -1)
            if [[ -n "$value" ]]; then
                key="${file}|${field}"
                SAVED_KEYS+=("$key")
                SAVED_VALUES+=("$value")
            fi
        done
    done < <(find "$dir" -name '*.md' -print0 2>/dev/null)
}

find_saved_value() {
    local search_key="$1"
    local i
    for i in "${!SAVED_KEYS[@]}"; do
        if [[ "${SAVED_KEYS[$i]}" == "$search_key" ]]; then
            echo "${SAVED_VALUES[$i]}"
            return 0
        fi
    done
    return 1
}

restore_frontmatter_fields() {
    local i path field value
    for i in "${!SAVED_KEYS[@]}"; do
        path="${SAVED_KEYS[$i]%|*}"
        field="${SAVED_KEYS[$i]##*|}"
        value="${SAVED_VALUES[$i]}"
        if grep -q "^${field}:" "$path"; then
            sed -i "s|^${field}:.*|${field}: ${value}|" "$path"
        else
            awk -v line="${field}: ${value}" '
                /^---$/ { c++; if(c==2) { print line } }
                { print }
            ' "$path" > "$path.tmp" && mv "$path.tmp" "$path"
        fi
    done
}

print_agent_models() {
    local agents_dir="$TARGET/agents"
    [[ -d "$agents_dir" ]] || return 0

    local -a names models
    local file name model key
    for file in "$agents_dir"/*.md; do
        [[ -f "$file" ]] || continue
        name="$(basename "$file" .md)"
        key="${file}|model"
        if model=$(find_saved_value "$key"); then
            : # model already set
        else
            model="$(sed -n '/^---$/,/^---$/ s|^model: *||p' "$file" | head -1)"
            [[ -z "$model" ]] && model="empty (inherit)"
        fi
        names+=("$name")
        models+=("$model")
    done
    ((${#names[@]})) || return 0

    local name_width=0 model_width=0 i
    for i in "${!names[@]}"; do
        ((${#names[i]} > name_width)) && name_width=${#names[i]}
        ((${#models[i]} > model_width)) && model_width=${#models[i]}
    done
    name_width=$((name_width > 5 ? name_width : 5))
    model_width=$((model_width > 5 ? model_width : 5))

    echo ""
    printf "  %-${name_width}s  %s\n" "Agent" "Model"
    printf "  %-${name_width}s  %s\n" "$(printf '%*s' "$name_width" '' | tr ' ' '-')" "$(printf '%*s' "$model_width" '' | tr ' ' '-')"
    for i in "${!names[@]}"; do
        printf "  %-${name_width}s  %s\n" "${names[$i]}" "${models[$i]}"
    done
    echo "  (edit in $TARGET/agents/ to customize)"
    echo ""
}

if [[ -d "$TARGET" ]] && [[ -n "$(ls -A "$TARGET" 2>/dev/null)" ]]; then
    save_frontmatter_fields "$TARGET"
fi

echo "Installing to $TARGET..."
unzip -oq "$ZIP_FILE" -x ".lissom/*"
unzip -nq "$ZIP_FILE" ".lissom/*"

if [[ ${#SAVED_KEYS[@]} -gt 0 ]]; then
    restore_frontmatter_fields
fi

print_agent_models

rm -f "$ZIP_FILE"

gitignore_msg="# We recommend not to commit development doc. If you want to stage the content, comment out this line."
if [[ -f ".gitignore" ]]; then
    if ! grep -q "^\.lissom/" ".gitignore"; then
        { echo ""; echo "$gitignore_msg"; echo ".lissom/"; } >> ".gitignore"
        echo "Added .lissom/ to .gitignore"
    fi
else
    { echo "$gitignore_msg"; echo ".lissom/"; } > ".gitignore"
    echo "Created .gitignore with .lissom/"
fi

echo "┌─┐"
echo "│L│░ LISSOM  |  Installation complete,"
echo "└─┘  SKILLS  |  Happy hacking!"
echo ""
echo "Next steps:"
echo "- A sample Specs.md has been created at .lissom/tasks/T1/Specs.md"
echo "- Invoke '/lissom-auto T1', get interviewed and wait for the job to be done!"
