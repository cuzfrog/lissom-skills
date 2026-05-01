---
name: lissom-review
version: 2026-04-30T02:15:17Z
description: Dispatches to lissom-reviewer and relays the verdict to the caller.
argument-hint: <task_id>
---

## Inputs

- `task_id`

## Process

Use Tool `Agent` to spawn `lissom-reviewer`, passing it the `task_id`.

## Completion

Verify `.lissom/tasks/<ID>/Review.md` exists and is non-empty.

Return to the caller with:
- Confirmation that `Review.md` was written.
- Whether any findings exist (the caller owns threshold logic and fix-loop decisions).

Do **not** attempt to fix code or mark the task as done.
