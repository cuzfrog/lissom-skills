---
name: lissom-plan
version: 2026-04-29T04:00:57Z
description: Dispatches to lissom-planner to produce Plan.md for a given task ID.
---

You are invoked with a task ID (e.g. `T1`).

## Inputs

- `task_id`: The task identifier (e.g. `T1`)
- `fix_cycle` (optional): Fix-cycle counter supplied by lissom-coordinator during the fix loop.

## What you do

Spawn the **`lissom-planner`** agent, passing it the task ID and, if present, the fix-cycle counter.

## Completion

If the agent emits `ESCALATE: stale-conflict <file> — <reason>` (Plan.md was
intentionally not written), relay that exact token to the caller unchanged —
do not retry.

Otherwise, return to the caller only after `.dev/tasks/<ID>/Plan.md` exists
and contains at least one step. If it does not exist, re-invoke the agent once
before escalating.

If the plan contains open questions for the user (marked in the plan), pause
and surface them before reporting back.

Report back: `Plan complete — Plan.md written to .dev/tasks/<ID>/ with N steps.`
