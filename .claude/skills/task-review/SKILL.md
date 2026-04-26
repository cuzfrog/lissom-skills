---
name: task-review
description: Review the implementation.
---

You are invoked with a task ID (e.g. `T1`).

## What you do

Spawn the **`task-reviewer`** agent, passing it the task ID so it can read
`.dev/tasks/<ID>/Specs.md` and `.dev/tasks/<ID>/Research.md` as reference for
intent, then review recent commits.

## Completion

After the reviewer finishes, write `.dev/tasks/<ID>/Review.md` containing the
agent's full output.

Report back with one of:
- `Review passed — no critical issues. Review.md written.`
- `Review failed — N critical issue(s) found. Review.md written.`

If critical issues are found, **do not mark the task as done** and **do not
attempt to fix the code yourself**. Escalate to the caller (`task-auto` or
the user) with a summary of what must be fixed so that `task-plan` can
generate fix step files and `task-implementer` can apply the actual changes.

## Idempotency

If `Review.md` already exists and the code has not changed since it was
written (check `git log`), return the existing result without re-running the
reviewer.
