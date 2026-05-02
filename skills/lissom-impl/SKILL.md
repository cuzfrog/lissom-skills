---
name: lissom-impl
version: 2026-05-02T00:00:00Z
description: Dispatch to lissom-implementer agent to execute plan steps and verify completion.
argument-hint: <task_dir>
---

## Inputs

- `task_dir` = "$0"

## Process

0. Use Tool `TodoWrite` to track progress.
1. Read `<task_dir>/Impl-record.json` if it exists to find already-completed
   steps, then resume from the next incomplete step.
2. Read `<task_dir>/Plan.md`. Check whether `Step-<N>.md` files exist for the task.
3. **If step files exist**: iterate through each step in order (including fix
   steps listed under `## Fix cycle <M>` sections in Plan.md). For each step: use Tool `Agent` to spawn `lissom-implementer` with the `task_dir` and `step_name` (e.g. `Step-2`).
4. **If no step files exist**: use Tool `Agent` to spawn `lissom-implementer` with only the `task_dir`. The `Plan.md` is treated as the default "step file".

### Per step process

1. If the agent reports a blocker (e.g. missing dependency, ambiguous spec), escalate immediately.
2. Verify the step entry exists in `<task_dir>/Impl-record.json`.
3. If the record is missing, re-invoke `lissom-implementer` once more with the same step. If still missing after retry, escalate with the step name and the agent's last response.

## Constraints

- Never apply fixes directly — every fix step must come from a `Step-<N>-fix-<M>.md`
  file written by `lissom-planner`.

## Completion

After all steps are done, write `<task_dir>/Impl-summary.md` containing:
- Steps completed with commit SHAs from `<task_dir>/Impl-record.json`
- Any deviations from the plan
- Assumptions section copied from `<task_dir>/Research.md`

Verify the file exists and is non-empty.
