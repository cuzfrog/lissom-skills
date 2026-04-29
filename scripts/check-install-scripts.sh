#!/usr/bin/env bash
# Detect file additions (Write) or removals (Bash rm/mv) in production content
# dirs, then inject a reminder for Claude to review install/uninstall/README.

input=$(cat)
tool=$(grep -o '"tool_name":"[^"]*"' <<< "$input" | cut -d'"' -f4)

case "$tool" in
  Write)
    f=$(grep -o '"file_path":"[^"]*"' <<< "$input" | cut -d'"' -f4)
    [[ "$f" == */skills/* || "$f" == */agents/* || "$f" == */templates/* ]] || exit 0
    ;;
  Bash)
    grep -qE '"command":"[^"]*(rm|mv)[^"]*(skills|agents|templates)/' <<< "$input" || exit 0
    ;;
  *)
    exit 0
    ;;
esac

printf '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"A file was added or removed under a Project production contents directory (skills/, agents/, or templates/). Review install.sh, uninstall.sh, and README.md — check if any of them need updating."}}\n'
