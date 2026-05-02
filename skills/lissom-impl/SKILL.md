---
name: lissom-impl
version: 2026-05-02T00:00:00Z
description: Dispatch to lissom-implementer agent to execute plan steps and verify completion.
argument-hint: <task_dir>
---

## Inputs

- `task_dir` = "$0"

## Process

1. Read `<task_dir>/Impl-record.json` if it exists. Skip any step already
   recorded (with a `sha`). Escalate any step recorded with an `error`.
2. Read `<task_dir>/Plan.md` for task-level context.
3. Enumerate `Step-*.md` and `Fix-*.md` files in `<task_dir>/` in sorted order.
   For each file not already in `<task_dir>/Impl-record.json`, use Tool `Agent` to
   spawn `lissom-implementer` with `task_dir` and `step_file` (the
   filename, e.g. `Step-2.md`).

### Per step process

1. If the agent reports a blocker, escalate immediately.
2. Verify the step entry exists in `<task_dir>/Impl-record.json`.
3. If the record has an `error` field, escalate with the error reason.
4. If the record is missing, re-invoke `lissom-implementer` once more with
   the same step. If still missing after retry, escalate with the `step_file`
   and the agent's last response.

## Completion

After all steps are done, write `<task_dir>/Impl-summary.md` containing:
- Steps completed with commit SHAs from `<task_dir>/Impl-record.json`
- Any deviations from the plan
- Assumptions section copied from `<task_dir>/Research.md`

Verify the file exists and is non-empty.
