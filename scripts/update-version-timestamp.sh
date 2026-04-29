#!/usr/bin/env bash
input=$(cat)
f=$(grep -o '"file_path":"[^"]*"' <<< "$input" | cut -d'"' -f4)
[[ -z "$f" || ("$f" != */skills/* && "$f" != */agents/*) ]] && exit 0
[[ -f "$f" ]] || exit 0
sed -i "s/^version: .*/version: $(date -u +%Y-%m-%dT%H:%M:%SZ)/" "$f"
