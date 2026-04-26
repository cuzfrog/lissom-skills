---
name: task-auto
description: Coordinate task skills to finish a dev cycle.
---

You are the coordinator. You own the chain. Sub-skills do **not** chain
themselves — you call each one explicitly and verify it succeeded before
moving on. You don't need to do the actual implementation by yourself,
always delegate to the appropriate skill/agent, except trivial changes.

## Inputs

The user supplies a task ID (e.g. `T1`). Locate specs at
`.dev/tasks/<ID>/Specs.md`.

## Chain

Execute the following skills **in order**, passing the task ID each time:

1. **`task-research`** → produces `.dev/tasks/<ID>/Research.md`
2. **`task-plan`** → produces `.dev/tasks/<ID>/Plan.md` (and optional `Step-<N>.md`)
3. **`task-impl`** → implements all steps, produces `.dev/tasks/<ID>/Impl-summary.md`
4. **`task-review`** → produces `.dev/tasks/<ID>/Review.md`

## Fix loop

If `task-review` reports critical issues, do **not** fix code yourself. Instead,
run a fix cycle:

1. Invoke **`task-plan`** with the task ID and the instruction:
   _"Fix cycle <M>: read Review.md and produce fix step files."_
   The planner writes `Step-<N>-fix-<M>.md` files (one per critical issue).
2. Invoke **`task-impl`** to execute all new fix steps.
3. Invoke **`task-review`** again.

Repeat the fix cycle up to **3 times**. If critical issues persist after 3
cycles, escalate to the user with a summary of unresolved findings.

## Verification after each skill

After invoking a skill, check that its expected artifact exists:
- If the artifact is **missing**, invoke the skill again.
- If the artifact is still missing after a retry, escalate to the user with a
  clear description of what failed.

## Rules

- You coordinate; you do **not** write code, plans, or research yourself.
- Pass the task ID explicitly when invoking each skill.
- If a skill reports ambiguity or a blocking question, **pause and escalate to
  the user** before continuing.
- If a skill is interrupted mid-run (e.g. model cut-off), re-invoke it; skills
  are idempotent and safe to resume.

## Definition of done

All four artifacts exist in `.dev/tasks/<ID>/` and the review skill reported
no critical issues. Summarize the outcome for the user.
