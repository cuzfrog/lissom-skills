---
name: lissom-review
description: Dispatches to lissom-reviewer agent to review the implementation given an explicit task_dir, which contains the related documents.
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
