<!-- version: 2026-05-03T18:25:00Z -->
---
name: lissom-review
description: Dispatches to lissom-reviewer and relays the verdict to the caller.
argument-hint: <task_dir>
---

## Inputs

- `task_dir` = "$0"

## Process

Use Tool `Agent` to spawn `lissom-reviewer`, passing it the `task_dir`.

## Completion

Verify `<task_dir>/Review.md` exists and is non-empty.

Return to the caller with:
- Confirmation that `Review.md` was written.
- Whether any findings exist (the caller owns threshold logic and fix-loop decisions).

Do **not** attempt to fix code or mark the task as done.
