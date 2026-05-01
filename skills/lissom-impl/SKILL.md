---
name: lissom-impl
version: 2026-04-30T02:15:25Z
description: Dispatch to lissom-implementer agent to execute plan steps and verify completion.
---

## Inputs

- `task_id`

## Process

0. Use `TodoWrite` tool to track progress.
1. Read `.lissom/tasks/<ID>/Impl-record.json` if it exists to find already-completed
   steps, then resume from the next incomplete step.
2. Read `.lissom/tasks/<ID>/Plan.md`. Check whether `Step-<N>.md` files exist for the task.
3. **If step files exist**: iterate through each step in order (including fix
   steps listed under `## Fix cycle <M>` sections in Plan.md). For each step: Use Tool `Agent` to spawn `lissom-implementer` with the `task_id` and `step_name` (e.g. `T1 Step-2`).
4. **If no step files exist**: use Tool `Agent` to spawn `lissom-implementer` with only the `task_id`. The `Plan.md` is treated as the default "step file".

### Per step process
1. Extract: commit SHA, tests run, and pass/fail status from the agent's response.
2. Re-read the step file's acceptance criterion. If the agent's report confirms the criterion is met, record the step in `Impl-record.json`.
3. If not met, re-invoke `lissom-implementer` once more with the same step. If still failing, escalate with the step name and what failed.
4. If the agent reports a blocker (e.g. missing dependency, ambiguous spec), escalate immediately.

## Constraints

- Never apply fixes directly — every fix step must come from a `Step-<N>-fix-<M>.md`
  file written by `lissom-planner`.

## Impl-record.json format

```json
{
  "task": "<ID>",
  "steps": [
    { "step": "Step-1", "sha": "<commit SHA>" },
    { "step": "Step-2", "sha": "<commit SHA>" }
  ]
}
```

Rewrite the full file after each step completes. Never append.

## Completion

After all steps are done, write `.lissom/tasks/<ID>/Impl-summary.md` containing:
- Steps completed (with commit SHAs from `Impl-record.json`)
- Tests run and their pass/fail status (gathered from agent responses during step iteration)
- Any deviations from the plan
- Assumptions section copied from `.lissom/tasks/<ID>/Research.md`

Verify the file exists and is non-empty.
