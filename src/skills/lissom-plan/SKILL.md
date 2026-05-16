---
name: lissom-plan
description: Dispatches to lissom-planner agent to produce an implementation plan given an explicit task_dir, which contains a specification or research document.
argument-hint: <task_dir> [fix_cycle] [fix_threshold]
---

## Inputs

- `task_dir` = "$0"
- `fix_cycle` = "$1" (optional)
- `fix_threshold` = "$2" (optional): `critical`, `warning`, or `suggestion`.

## Process

Use Tool `Agent` to spawn `lissom-planner`, passing: `task_dir`, `fix_cycle`, and `fix_threshold`.

## Completion

Return to the caller only after `<task_dir>/Plan.md` exists
and contains at least one step. If it does not exist, re-invoke the agent once
before escalating.
