---
name: lissom-impl
description: Dispatch to lissom-implementer agent to execute the implementation given an explicit task_dir, which contains the plan.
argument-hint: <task_dir>
---

## Inputs

- `task_dir` = "$0"
- `impl_delegation` = "single" | "multiple" (default: "single")

## Process

- **If `impl_delegation` == "multiple"**
    - Enumerate `Step-*.md` and `Fix-*.md` files in `<task_dir>/` in numeric order. For each file not already in `<task_dir>/Impl-record.json` with a `sha`, use Tool `Agent` to spawn `lissom-implementer` with `task_dir` and `step_file` (the filename with extension).
    - Read `Step-dependency-graph.md` or `Fix-dependency-graph-<N>.md` to find out parallel execution opportunities.
- **If `impl_delegation` == "single"**
    - Spawn a single `lissom-implementer` agent with `task_dir` and let it execute all steps sequentially.

### Per step process

1. If the agent reports `FAILED`, report immediately.
2. Verify the step entry exists in `<task_dir>/Impl-record.json`.
3. If the record is missing, re-invoke `lissom-implementer` once more with the same step. If still missing after retry, report with the agent's last response.

## Completion

Write `<task_dir>/Impl-summary.md` containing:
- Steps completed with commit SHAs from `<task_dir>/Impl-record.json`
- Any deviations from the plan
- Any issues met during the implementation.
