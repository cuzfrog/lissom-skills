#!/usr/bin/env bash
set -e

REPO="${LISSOM_REPO:-https://github.com/cuzfrog/lissom-skills}"

cleanup() { rm -f lissom-skills-tmp.zip install-readme.txt; }
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

echo "Installing to $TARGET..."
unzip -o "$ZIP_FILE" -x ".lissom/*"
unzip -n "$ZIP_FILE" ".lissom/*"

if [[ -f "install-readme.txt" ]]; then
    echo ""
    cat "install-readme.txt"
    echo ""
    echo "Agent models can be edited later in $TARGET/agents/"
    echo ""
fi

rm -f "$ZIP_FILE" install-readme.txt

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
echo "│L│░ LISSOM  |  Installation complete!"
echo "└─┘  SKILLS  |  Installed to $TARGET"
echo ""
echo "Next steps:"
echo "- A sample Specs.md has been created at .lissom/tasks/T1/Specs.md"
echo "- Invoke '/lissom-auto T1', get interviewed and wait for the job to be done!"
