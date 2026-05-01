#!/usr/bin/env bash
set -euo pipefail

echo "Retiming matching commits on branch 'main' (local only)"
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "ERROR: not a git repo"
  exit 1
fi

current_branch=$(git rev-parse --abbrev-ref HEAD)
echo "Current branch: $current_branch"
if [ "$current_branch" != "main" ]; then
  echo "Switching to main"
  git checkout main
fi

if [ -n "$(git status --porcelain)" ]; then
  echo "ERROR: working tree not clean; aborting"
  git status --porcelain
  exit 1
fi

# Configuration
target_date="2026-05-01"
cutoff_hour=18

# Collect commits on main
mapfile -t commits < <(git rev-list --reverse main)
matches=()
for sha in "${commits[@]}"; do
  ct=$(git show -s --format=%ct "$sha")
  datepart=$(date -d "@$ct" '+%Y-%m-%d')
  hour=$(date -d "@$ct" '+%H')
  if [ "$datepart" = "$target_date" ] && [ "$hour" -lt "$cutoff_hour" ]; then
    matches+=("$sha")
    echo "Match: $sha -> $(date -d "@$ct" '+%Y-%m-%d %H:%M:%S %z')"
  fi
done

if [ ${#matches[@]} -eq 0 ]; then
  echo "No commits on $target_date before ${cutoff_hour}:00 found on main. Nothing to do."
  exit 0
fi

mapfile_name=".git/commit-timestamp-map.sh"
cat > "$mapfile_name" <<'EOF'
case "$GIT_COMMIT" in
EOF

base_epoch=$(date -d "$target_date $cutoff_hour:00:00" +%s)
epoch=$((base_epoch + 1))

for sha in "${matches[@]}"; do
  delta=$(( (RANDOM % 300) + 1 ))
  epoch=$((epoch + delta))
  new_dt=$(date -d "@$epoch" '+%Y-%m-%d %H:%M:%S %z')
  cat >> "$mapfile_name" <<EOF
  $sha)
    export GIT_AUTHOR_DATE='$new_dt'
    export GIT_COMMITTER_DATE='$new_dt'
    ;;
EOF
  echo "Will set $sha -> $new_dt"
done

cat >> "$mapfile_name" <<'EOF'
esac
EOF

chmod +x "$mapfile_name"

echo "Running git filter-branch (this rewrites history locally)..."
git filter-branch --env-filter ". $mapfile_name" -- --branches main

echo "filter-branch done. You may want to run: git reflog expire --expire=now --all && git gc --prune=now --aggressive"

echo "Done."
