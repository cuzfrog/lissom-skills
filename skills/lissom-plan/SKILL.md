---
name: lissom-plan
version: 2026-04-30T02:15:17Z
description: Dispatches to lissom-planner to produce Plan.md for a given task ID.
argument-hint: <task_id> [fix_cycle] [fix_threshold]
---

## Inputs

- `task_id`: The task identifier.
- `fix_cycle` (optional): Fix-cycle counter for the fix loop.
- `fix_threshold` (optional): `critical`, `warning`, or `suggestion`.

## Process

Use Tool `Agent` to spawn `lissom-planner`, passing: `task_id`, `fix_cycle` (if present), and `fix_threshold` (if present).

## Completion

Return to the caller only after `.lissom/tasks/<ID>/Plan.md` exists
and contains at least one step. If it does not exist, re-invoke the agent once
before escalating.
