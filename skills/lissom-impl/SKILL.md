---
name: lissom-impl
version: 2026-04-30T02:15:25Z
description: Dispatch to lissom-implementer agent to execute plan steps and verify completion.
---

You are invoked with a task ID (e.g. `T1`).

## Inputs

- **task_id**: The task identifier (required)

## What you do

0. Use `TodoWrite` tool to help user track progress.
1. Read `.lissom/tasks/<ID>/Impl-record.json` if it exists to find already-completed
   steps, then resume from the next incomplete step.
2. Check whether `Step-<N>.md` files exist for the task.
3. **If step files exist**: iterate through each step in order (including fix
   steps listed under `## Fix cycle <M>` sections in Plan.md). For each step:
   - Use Tool `Agent` to spawn `lissom-implementer` with the task ID and step name (e.g. `T1 Step-2`).
   - Verify the step's acceptance criterion is met.
   - If not met, use Tool `Agent` to spawn `lissom-implementer` once more. If still failing, escalate to the user with
     the step number and a description of what failed.
   - On success, record the completed step in `Impl-record.json` before moving to the next step.
4. **If no step files exist**: use Tool `Agent` to spawn `lissom-implementer` with the task ID, passing Plan.md as the sole guide.

Never apply fixes directly — every fix step must come from a `Step-<N>-fix-<M>.md`
file written by `lissom-planner` first.

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
- Tests run and their pass/fail status
- Any deviations from the plan
- Assumptions section copied from `.lissom/tasks/<ID>/Research.md`

Verify the file exists and is non-empty.
