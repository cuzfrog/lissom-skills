#!/usr/bin/env bash
set -e

REPO="${LISSOM_REPO:-https://github.com/cuzfrog/lissom-skills}"
CLEANUP_TMPDIR=""

# 1. Resolve SCRIPT_DIR (mirror the old install.sh approach for curl | bash)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd 2>/dev/null || pwd)"
[[ "$(basename "$SCRIPT_DIR")" == "scripts" ]] && SCRIPT_DIR="$(dirname "$SCRIPT_DIR")"

if [[ ! -f "$SCRIPT_DIR/scripts/lib/common.sh" ]]; then
    SCRIPT_DIR="$(mktemp -d)"
    CLEANUP_TMPDIR="$SCRIPT_DIR"
    mkdir -p "$SCRIPT_DIR/scripts/lib"
    for f in common.sh constants.sh ui.sh; do
        curl -fsSL "$REPO/scripts/lib/$f" -o "$SCRIPT_DIR/scripts/lib/$f"
    done
fi

source "$SCRIPT_DIR/scripts/lib/common.sh"
source "$SCRIPT_DIR/scripts/lib/constants.sh"
source "$SCRIPT_DIR/scripts/lib/ui.sh"

parse_no_args "$@"

# 2. Prompt for target directory (same as before)
INSTALL_TARGET=$(prompt_target_directory)
TARGET="./$INSTALL_TARGET"

# 3. Map target to zip name
case "$INSTALL_TARGET" in
    .claude)   ZIP="lissom-skills-claude.zip" ;;
    .opencode) ZIP="lissom-skills-opencode.zip" ;;
    .qwen)     ZIP="lissom-skills-qwen.zip" ;;
    .gemini)   ZIP="lissom-skills-gemini.zip" ;;
    *) echo "Error: Unknown target $INSTALL_TARGET" >&2; exit 1 ;;
esac

# 4. If target directory already exists and is non-empty, prompt for overwrite
if [[ -d "$TARGET" ]] && [[ -n "$(ls -A "$TARGET" 2>/dev/null)" ]]; then
    OVERWRITE=false
    if [[ "${LISSOM_YES:-}" == "1" ]]; then
        OVERWRITE=true
    elif [[ -t 0 ]]; then
        read -p "$TARGET already exists and is not empty. Overwrite all files? (y/N) " -n 1 -r
        echo
        [[ $REPLY =~ ^[Yy]$ ]] && OVERWRITE=true
    fi
    if ! $OVERWRITE; then
        echo "Installation cancelled."
        exit 0
    fi
fi

# 5. Download the zip from GitHub releases
ZIP_URL="$REPO/releases/latest/download/$ZIP"
ZIP_FILE="lissom-skills-tmp.zip"
echo "Downloading $ZIP..."
curl -fsSL "$ZIP_URL" -o "$ZIP_FILE"

# 6. Unzip to current working directory
echo "Installing to $TARGET..."
unzip -o "$ZIP_FILE"

# 7. Clean up zip file
rm -f "$ZIP_FILE"

# 8. Create sample Specs.md (copy from installed template)
specs_dir=".lissom/tasks/T1"
specs_dest="$specs_dir/Specs.md"
if [[ ! -f "$specs_dest" ]]; then
    mkdir -p "$specs_dir"
    if [[ -f "$TARGET/templates/Specs.md" ]]; then
        cp "$TARGET/templates/Specs.md" "$specs_dest"
        echo "Created sample $specs_dest"
    fi
fi

# 9. Add .lissom/ to .gitignore if not already present
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

# 10. Print summary
echo ""
echo "Installation complete!"
echo "Installed to $TARGET"
echo ""
echo "Next steps:"
echo "- A sample Specs.md has been created at .lissom/tasks/T1/Specs.md"
echo "- Invoke '/lissom-auto T1', get interviewed and wait for the job to be done!"

# 11. Clean up temp directory
[[ -n "$CLEANUP_TMPDIR" ]] && rm -rf "$CLEANUP_TMPDIR"
