---
name: task-research
description: To understand the task and user's intention. Generate enough information for planning the implementation.
---

You are invoked with a task ID (e.g. `T1`).

## What you do

Spawn the **`task-researcher`** agent, passing it the task ID.

The agent will:
- Read `.dev/tasks/<ID>/Specs.md`
- Explore the codebase for relevant patterns and files
- Write `.dev/tasks/<ID>/Research.md`

## Completion

Return to the caller (e.g. `task-auto`) only after `.dev/tasks/<ID>/Research.md`
exists and is non-empty. If it does not exist, re-invoke the agent once before
escalating.

Report back: `Research complete — Research.md written to .dev/tasks/<ID>/`.

## Idempotency

If `Research.md` already exists, pass it to the agent for review and update
only if it is stale or incomplete relative to the current spec.