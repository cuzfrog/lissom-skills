---
name: task-impl
version: 2026-04-28T03:18:59Z
description: Dispatch to task-implementer agent to execute plan steps and verify completion.
---

You are invoked with a task ID (e.g. `T1`).

## Inputs

- **task_id**: The task identifier (required)

## What you do

1. Check whether `Step-<N>.md` files exist for the task.
2. **If step files exist**: iterate through each step in order (including fix
   steps listed under `## Fix cycle <M>` sections in Plan.md). For each step:
   - Spawn **`task-implementer`** with the task ID and step name (e.g. `T1 Step-2`).
   - Verify the step's acceptance criterion is met.
   - If not met, spawn once more. If still failing, escalate to the user with
     the step number and a description of what failed.
3. **If no step files exist**: spawn **`task-implementer`** once with just the
   task ID, passing Plan.md as the sole guide.

Never apply fixes directly — every fix step must come from a `Step-<N>-fix-<M>.md`
file written by `task-planner` first.

## Completion

After all steps are done, write `.dev/tasks/<ID>/Impl-summary.md` containing:
- Steps completed (with commit SHAs if available)
- Tests run and their pass/fail status
- Any deviations from the plan
- Assumptions section copied from `.dev/tasks/<ID>/Research.md`

Verify the file exists and is non-empty.

Report back: `Implementation complete — all N steps done. Impl-summary.md written.`
