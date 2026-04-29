---
name: task-review
version: 2026-04-29T04:00:57Z
description: Dispatches to task-reviewer and relays the pass/fail verdict to task-coordinator.
---

You are invoked with a task ID (e.g. `T1`) and an optional mode.

## Inputs

- `task_id`: The task identifier (e.g. `T1`)

## What you do

Spawn the **`task-reviewer`** agent, passing it the task ID.

## Completion

Verify `.dev/tasks/<ID>/Review.md` exists and is non-empty.

Report back with one of:
- `Review passed — no critical issues. Review.md written.`
- `Review failed — N critical issue(s) found. Review.md written.`

If critical issues are found, **do not mark the task as done** and **do not
attempt to fix the code yourself**. Escalate to the caller (`task-coordinator`)
with a summary of what must be fixed so that `task-plan` can generate fix step
files and `task-implementer` can apply the actual changes.
