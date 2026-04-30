---
name: lissom-plan
version: 2026-04-30T02:15:17Z
description: Dispatches to lissom-planner to produce Plan.md for a given task ID.
disable-model-invocation: true
---

You are invoked with a task ID (e.g. `T1`).

## Inputs

- `task_id`: The task identifier (e.g. `T1`)
- `user_attention` (optional): Control questioning depth — `auto`, `default`, or `focused`.
- `fix_cycle` (optional): Fix-cycle counter for the fix loop.

## What you do

Spawn the **`lissom-planner`** agent, passing it the task ID, user_attention (if provided), and fix-cycle counter (if present).

## Completion

Otherwise, return to the caller only after `.lissom/tasks/<ID>/Plan.md` exists
and contains at least one step. If it does not exist, re-invoke the agent once
before escalating.

If the plan contains open questions for the user (marked in the plan), pause
and surface them before reporting back.
