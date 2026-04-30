---
name: lissom-review
version: 2026-04-29T17:08:12Z
description: Dispatches to lissom-reviewer and relays the pass/fail verdict to the caller.
disable-model-invocation: true
---

You are invoked with a task ID (e.g. `T1`) and an optional mode.

## Inputs

- `task_id`: The task identifier (e.g. `T1`)

## What you do

Spawn the **`lissom-reviewer`** agent, passing it the task ID.

## Completion

Verify `.lissom/tasks/<ID>/Review.md` exists and is non-empty.

Report back with one of:
- `Review passed — no critical issues. Review.md written.`
- `Review failed — N critical issue(s) found. Review.md written.`

If critical issues are found, **do not mark the task as done** and **do not
attempt to fix the code yourself**. Escalate to the caller with a summary of what must be fixed so that `lissom-plan` can generate fix step
files and `lissom-implementer` can apply the actual changes.
