# Implementation Summary — T40: migrate installation to pre-built zip

## Steps Completed

| Step | File | SHA | Description |
|------|------|-----|-------------|
| 1 | Step-1.md | `33ef5bc` | Backup old bash files to `scripts/.backup/` |
| 2 | Step-2.md | `e0e87e1` | Create `scripts/lib/constants.py` with ported data constants |
| 3 | Step-3.md | `c09e376` | Create `scripts/lib/frontmatter.py` — YAML frontmatter parser |
| 4 | Step-4.md | `c3b5997` | Create `scripts/lib/opencode.py` — Opencode format converter |
| 5 | Step-5.md | `bffee4d` | Create `scripts/lib/qwen.py` — Qwen Code format converter |
| 6 | Step-6.md | `da85ea1` | Create `scripts/lib/gemini.py` — Gemini CLI format converter |
| 7 | Step-7.md | `650919d` | Create `scripts/build.py` — build orchestrator producing 4 zips |
| 8 | Step-8.md | `0851ddb` | Create new `scripts/install.sh` — thin download-and-unzip wrapper |
| 9 | Step-9.md | `aa29beb` | Fix `scripts/uninstall.sh` SCRIPT_DIR resolution for remote execution |
| 10 | Step-10.md | `528902a` | Extend CI pipeline with release job |
| 11 | Step-11.md | `432fe69` | Create `test/test_build.py` — 25 tests for build + converters |
| 12 | Step-12.md | `7f0dd59` | Rewrite `test/test_install.py` — 13 tests for new install flow |
| 13 | Step-13.md | `8e42dc3` | Extend `test/test_uninstall.py` — 20 tests including remote |
| 14 | Step-14.md | `7ab6a0a` | Update `test/conftest.py` with `seed_lissom_files` helper |
| — | Cleanup | `4b9bdf8` | Remove obsolete `test/lib/*` tests for old bash implementation |

## Deviations from Plan

1. **Removed obsolete test/lib/ tests**: The plan did not explicitly mention removing the old `test/lib/test_*.py` files that test the backed-up bash scripts. These tests were left behind and failed because they sourced `opencode.sh`, `qwen.sh`, `gemini.sh`, `frontmatter.sh`, and `install_ops.sh` which are now in `scripts/.backup/`. Removed them as part of the cleanup.

2. **BASH_SOURCE guard fix**: Step 9's fix uncovered an additional issue — the uninstall script's `BASH_SOURCE` guard (`if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then return; fi`) failed when executed via `curl | bash` because `BASH_SOURCE[0]` is empty in a pipe context. Added a check for `-n "${BASH_SOURCE[0]}"` to handle this case.

3. **Exit code bug in install.sh and uninstall.sh**: The `[[ -n "$CLEANUP_TMPDIR" ]] && rm -rf "$CLEANUP_TMPDIR"` pattern at the end of both scripts returned exit code 1 when `CLEANUP_TMPDIR` was empty (since `[[ -n "" ]]` evaluates to false/1 and `&&` short-circuits). Fixed with `|| true` suffix.

## Issues Encountered

1. **Backward-incompatible test infrastructure**: The existing `test/test_uninstall.py` used `install_fixture()` which ran the old `install.sh`. After Step 1 backed up the old install.sh and the new one requires pre-built zips from GitHub releases, the fixture function broke. Fixed by replacing with `seed_lissom_files()` helper in `conftest.py` that directly creates the directory structure without running any install script.

2. **Test install server routing**: The install.sh downloads from `$REPO/releases/latest/download/<zip>`. Testing required a custom HTTP server handler that routes `/releases/latest/download/` to the `dist/` directory.

## Fix Cycle 1

| Fix | File | SHA | Description |
|-----|------|-----|-------------|
| #1 | Fix-1-Issue-1.md | `162af19` | Split `REPO` into `REPO` (GitHub API) and `RAW_REPO` (raw content) in `install.sh` and `uninstall.sh` |
| #2 | Fix-1-Issue-2.md | `162af19` | Add `trap cleanup EXIT` in both scripts to clean up temp dir on early exit |
| #3 | Fix-1-Issue-3.md | `b3e67a8` | Deduplicate `_rewrite_body_tools` → shared `rewrite_backtick_tools()` in `frontmatter.py` |
| #4 | Fix-1-Issue-4.md | `162af19` | Resolved by Fix #2's trap — zip file cleaned up via trap on early exit |

### Fix Cycle Details

1. **Fix #1 — REPO split**: Introduced `REPO` (GitHub API base for zip downloads) and `RAW_REPO` (raw.githubusercontent.com for lib file downloads). Both overridable via `LISSOM_REPO` and `LISSOM_RAW_REPO` env vars. Fixed `install.sh` lib download URL and `uninstall.sh` which had the opposite default.

2. **Fix #2 — trap cleanup**: Added `cleanup()` trap function for `EXIT` in both `install.sh` and `uninstall.sh` so that `$CLEANUP_TMPDIR` and (in install.sh) `lissom-skills-tmp.zip` are cleaned up even if the script exits early due to `set -e`. Removed the manual cleanup at the bottom of both scripts.

3. **Fix #3 — dedup `_rewrite_body_tools`**: Extracted the identical function from `opencode.py`, `qwen.py`, and `gemini.py` into a shared `rewrite_backtick_tools(content, mapping)` utility in `frontmatter.py`. Each converter now imports and calls the shared utility with its own mapping dict. Removed unused `import re` from all three converters.

4. **Fix #4 — zip cleanup**: Verified that Fix #2's trap already includes `rm -f lissom-skills-tmp.zip`, which cleans up the downloaded zip on unzip failure. No additional code changes needed.

## Test Results

```
78 passed in 16.12s
```

- `test/test_build.py`: 25 tests (converter unit tests, build integration)
- `test/test_install.py`: 13 tests (fresh install, overwrite, all targets, remote curl)
- `test/test_uninstall.py`: 20 tests (basic, dry-run, multi-target, remote curl)
- `test/test_frontmatter_description.py`: 10 tests (description format)
- `test/test_tool_call_format.py`: 10 tests (backtick tool names)
