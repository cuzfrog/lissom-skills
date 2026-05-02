---
name: lissom-research
version: 2026-04-30T02:15:17Z
description: Dispatches to lissom-specs-reviewer then lissom-researcher to produce Research.md for a given task ID.
argument-hint: <task_dir> [user_attention] [spec_review_required]
---

## Inputs

- `task_dir` = "$0"
- `user_attention` = "$1" (optional): `default` (default), `auto`, or `focused`
- `spec_review_required` = "$2" (optional): `yes` (default) or `no`

## Process

Execute sequentially:

1. **Conditional**: Skip this step if `user_attention` is `auto` OR if `spec_review_required` is `no`. Otherwise:
   Use Tool `Agent` to spawn `lissom-specs-reviewer`, passing it the `task_dir` and `user_attention`.
   - If it returns `Specs INCOMPLETE` (auto mode only), relay the reasons to the
     user as a warning, then proceed.
   - Any other return value: treat as success and proceed.
   - If `<task_dir>/Specs.md` does not exist or is empty after the agent returns, escalate immediately.

2. Use Tool `Agent` to spawn `lissom-researcher`, passing it the `task_dir` and `user_attention`.

## Completion

Return to the caller only after `<task_dir>/Research.md` exists and is
non-empty. If it does not exist, re-invoke `lissom-researcher` once before
escalating.
