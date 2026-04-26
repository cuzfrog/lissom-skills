---
name: task-research
version: 2026-04-26T16:38:38
description: To understand the task and user's intention. Generate enough information for planning the implementation.
---

You are invoked with a task ID (e.g. `T1`) and an optional mode.

## Inputs

- `task_id`: The task identifier (e.g. `T1`)
- `mode`: Operation mode — `interview` (default) or `auto`

## What you do

Spawn the **`task-researcher`** agent, passing it the task ID and mode.

The agent will:
- Read `.dev/tasks/<ID>/Specs.md`
- Explore the codebase for relevant patterns and files
- Write `.dev/tasks/<ID>/Research.md`

In `auto` mode, the agent must produce an especially thorough Assumptions section, since no user confirmation will occur after research completes.

## Completion

Return to the caller (e.g. `task-auto`) only after `.dev/tasks/<ID>/Research.md`
exists and is non-empty. If it does not exist, re-invoke the agent once before
escalating.

Report back: `Research complete — Research.md written to .dev/tasks/<ID>/`.

## Idempotency

If `Research.md` already exists, pass it to the agent for review and update
only if it is stale or incomplete relative to the current spec.