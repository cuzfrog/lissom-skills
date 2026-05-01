---
name: lissom-research
version: 2026-04-30T02:15:17Z
description: Dispatches to lissom-specs-reviewer then lissom-researcher to produce Research.md for a given task ID.
argument-hint: <task_id> [user_attention]
---

## Inputs

- `task_id`
- `user_attention`: (optional) `default` (default), `auto`, or `focused`

## Process

Execute sequentially:

1. Use Tool `Agent` to spawn `lissom-specs-reviewer`, passing it the task ID and `user_attention`.
   - If it returns `Specs INCOMPLETE` (auto mode only), relay the reasons to the
     user as a warning, then proceed.
   - Any other return value: treat as success and proceed.
   - If `.lissom/tasks/<ID>/Specs.md` does not exist or is empty after the agent returns, escalate immediately.

2. Use Tool `Agent` to spawn `lissom-researcher`, passing it the task ID and `user_attention`.

## Completion

Return to the caller only after `.lissom/tasks/<ID>/Research.md` exists and is
non-empty. If it does not exist, re-invoke `lissom-researcher` once before
escalating.
