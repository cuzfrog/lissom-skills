---
name: task-impl
version: 2026-04-26T20:49:21Z
description: Dispatch to task-implementer agent to execute plan steps and verify completion.
---

You are invoked with a task ID (e.g. `T1`).

## Inputs

- **task_id**: The task identifier (required)

## What you do

Spawn the **`task-implementer`** agent, passing it the task ID. The agent
iterates through all steps in Plan.md (including fix steps) and commits after
each step.

## Completion

After all steps are done, write `.dev/tasks/<ID>/Impl-summary.md` containing:
- Steps completed (with commit SHAs if available)
- Tests run and their pass/fail status
- Any deviations from the plan
- Assumptions section copied from `.dev/tasks/<ID>/Research.md`

Verify the file exists and is non-empty.

Report back: `Implementation complete — all N steps done. Impl-summary.md written.`
