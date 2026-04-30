---
name: lissom-research
version: 2026-04-29T16:20:07Z
description: Dispatches to lissom-specs-reviewer then lissom-researcher to produce Research.md for a given task ID.
disable-model-invocation: true
---

You are invoked with a task ID (e.g. `T1`) and an optional user_attention.

## Inputs

- `task_id`: The task identifier (e.g. `T1`)
- `user_attention`: Operation mode — `default` (default), `auto`, or `focused`

## What you do

1. Spawn **`lissom-specs-reviewer`**, passing it the task ID and `user_attention`.
   - If it returns `Specs COMPLETE`, proceed.
   - If it returns `Specs INCOMPLETE` (auto mode only), relay the reasons to the
     user as a warning, then proceed.
   - If `Specs.md` does not exist after the agent returns, escalate immediately.

2. Spawn **`lissom-researcher`**, passing it the task ID and `user_attention`.

## Completion

Return to the caller only after `.lissom/tasks/<ID>/Research.md` exists and is
non-empty. If it does not exist, re-invoke `lissom-researcher` once before
escalating.

Report back: `Research complete — Research.md written to .lissom/tasks/<ID>/`.
