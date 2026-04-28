---
name: task-plan
version: 2026-04-26T20:49:21Z
description: Generate concrete implementation instructions, and split tasks into steps.
---

You are invoked with a task ID (e.g. `T1`) and an optional mode.

## Inputs

- `task_id`: The task identifier (e.g. `T1`)

## What you do

Spawn the **`task-planner`** agent, passing it the task ID.

## Completion

Return to the caller only after `.dev/tasks/<ID>/Plan.md` exists and contains
at least one step. If it does not exist, re-invoke the agent once before
escalating.

If the plan contains open questions for the user (marked in the plan), pause
and surface them before reporting back.

Report back: `Plan complete — Plan.md written to .dev/tasks/<ID>/ with N steps.`

## Idempotency

If `Plan.md` already exists, pass it to the agent for review and update only
if the spec or research has changed since it was written.
