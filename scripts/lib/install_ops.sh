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
