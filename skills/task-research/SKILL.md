---
name: task-research
version: 2026-04-29T04:00:57Z
description: Dispatches to task-specs-reviewer then task-researcher to produce Research.md for a given task ID.
---

You are invoked with a task ID (e.g. `T1`) and an optional mode.

## Inputs

- `task_id`: The task identifier (e.g. `T1`)
- `mode`: Operation mode — `interview` (default) or `auto`

## What you do

1. Spawn **`task-specs-reviewer`**, passing it the task ID and mode.
   - If it returns `Specs COMPLETE`, proceed.
   - If it returns `Specs INCOMPLETE` (auto mode only), relay the reasons to the
     user as a warning, then proceed.
   - If `Specs.md` does not exist after the agent returns, escalate immediately.

2. Spawn **`task-researcher`**, passing it the task ID and mode.

## Completion

Return to the caller only after `.dev/tasks/<ID>/Research.md` exists and is
non-empty. If it does not exist, re-invoke `task-researcher` once before
escalating.

Report back: `Research complete — Research.md written to .dev/tasks/<ID>/`.
