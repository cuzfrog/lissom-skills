---
name: task-research
version: 2026-04-28T02:48:53Z
description: To understand the task and user's intention. Generate enough information for planning the implementation.
---

You are invoked with a task ID (e.g. `T1`) and an optional mode.

## Inputs

- `task_id`: The task identifier (e.g. `T1`)
- `mode`: Operation mode — `interview` (default) or `auto`

## What you do

Spawn the **`task-researcher`** agent, passing it the task ID and mode.

## Completion

Return to the caller (e.g. `task-auto`) only after `.dev/tasks/<ID>/Research.md`
exists and is non-empty. If it does not exist, re-invoke the agent once before
escalating.

Report back: `Research complete — Research.md written to .dev/tasks/<ID>/`.
