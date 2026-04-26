---
name: task-impl
version: 2026-04-26T16:38:38
description: Implement concrete application logic.
---

You are invoked with a task ID (e.g. `T1`).

## Inputs

- **task_id**: The task identifier (required)
- **mode**: Execution mode — `interview` (default) or `auto`

## What you do

Iterate through every step in `.dev/tasks/<ID>/Plan.md`, implementing one
step at a time. This includes regular steps (`Step-<N>.md`) **and** any fix
steps (`Step-<N>-fix-<M>.md`) listed under `## Fix cycle <M>` sections:

1. Identify the next incomplete step (check git log / existing code to skip
   already-done steps).
2. Spawn **`task-implementer`**, passing it the task ID, step file name, and mode
   (e.g. `T1 Step-2-fix-1`).
3. Verify the step's acceptance criterion is met (tests pass, files exist,
   etc.) before moving to the next step.
4. Repeat until all steps (including fix steps) are done.

**Never apply fixes directly** — every fix must be driven by a
`Step-<N>-fix-<M>.md` file written by `task-planner` first.

The implementer commits after each step — do not batch multiple steps into a
single commit.

## Escalation

If a step's acceptance criterion cannot be met after one retry, escalate to
the user with the step number and a description of what failed.

If `Plan.md` is missing or has no steps, escalate immediately.

## Completion

After all steps are done, write `.dev/tasks/<ID>/Impl-summary.md` containing:
- Steps completed (with commit SHAs if available)
- Tests run and their pass/fail status
- Any deviations from the plan
- Assumptions section copied from `.dev/tasks/<ID>/Research.md`

Report back: `Implementation complete — all N steps done. Impl-summary.md written.`
