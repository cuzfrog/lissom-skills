#!/usr/bin/env bash
# Shared boilerplate for install/uninstall scripts.

# Guard against positional arguments — both install.sh and uninstall.sh accept none.
parse_no_args() {
    if [[ -n "$1" ]]; then
        local caller="${BASH_SOURCE[1]##*/}"
        echo "Usage: $caller"
        exit 1
    fi
}
