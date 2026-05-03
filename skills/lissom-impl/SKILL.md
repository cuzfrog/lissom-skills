---
name: lissom-impl
version: 2026-05-02T00:00:00Z
description: Dispatch to lissom-implementer agent to execute plan steps and verify completion.
argument-hint: <task_dir>
---

## Inputs

- `task_dir` = "$0"

## Process

Enumerate `Step-*.md` and `Fix-*.md` files in `<task_dir>/` in numeric order. For each file not already in `<task_dir>/Impl-record.json` with a `sha`, use Tool `Agent` to spawn `lissom-implementer` with `task_dir` and `step_file` (the filename with extension).

### Per step process

1. If the agent reports `FAILED`, report immediately.
2. Verify the step entry exists in `<task_dir>/Impl-record.json`.
3. If the record is missing, re-invoke `lissom-implementer` once more with the same step. If still missing after retry, report with the agent's last response.

## Completion

Write `<task_dir>/Impl-summary.md` containing:
- Summary
- Steps completed with commit SHAs from `<task_dir>/Impl-record.json`
- Any deviations or issues from the plan
