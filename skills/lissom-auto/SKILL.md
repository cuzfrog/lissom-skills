---
name: lissom-auto
version: 2026-04-30T02:15:06Z
description: Runs the full dev cycle (research → plan → impl → review + fix loop) for a task.
argument-hint: <taskId>
---

## Inputs

`taskId` (e.g. `T1`, `TASK-999`).

## Preference resolution

1. Load `user_preference_questions.json` in this skill's directory. Each entry has `preference_arg` (the preference name) and `env_var` (the corresponding environment variable).
2. For each preference, check its `env_var`. If set, use it.
3. For any preference not set via environment variable:
    - inform user: "Preferences can be set via environment variables, see README."
    - use `AskUserQuestion` to prompt the user using the entry's question/options. The first option in each question is the recommended one.

## Execution
0. Use `TodoWrite` tool to help user track progress.
1. Invoke `lissom-research` with task ID and `user_attention`. Verify `Research.md` exists; retry once on missing, then fail with `Research.md missing after retry`.
2. Invoke `lissom-plan` with task ID and `user_attention`. Verify `Plan.md` exists; retry once on missing.
3. Invoke `lissom-impl` with task ID. Verify `Impl-summary.md` exists; retry once on missing.
4. Invoke `lissom-review` with task ID. Verify `Review.md` exists; retry once on missing.
5. Check `Review.md` against `fix_threshold`:
   - `critical` → enter fix loop only if 🔴 Critical section is non-empty.
   - `warning` (default) → enter fix loop if 🔴 Critical or 🟡 Warning sections are non-empty.
   - `suggestion` → enter fix loop if any finding exists.
   If no issues at or above threshold → report success to the user.
6. Summarize the outcome for the user.

## Fix loop

Up to 3 cycles:
1. Invoke `lissom-plan` with task ID, `user_attention`, `fix_cycle=M`, and instruction: "Fix cycle <M>: read Review.md and produce fix step files. Apply the same user_attention level (<user_attention>) as the initial plan."
2. Invoke `lissom-impl` with task ID.
3. Invoke `lissom-review` with task ID.
4. If review passes → report success to the user.

After 3 cycles with persistent issues, report failure and direct the user to `Review.md`.

## Rules

- Never write code, plans, or research directly. Always delegate to the appropriate skill.
- Pass task ID explicitly in every skill invocation.
- If a sub-skill escalates a blocking question, use `AskUserQuestion` to relay it to the user and pass the answer back.
- If a skill is interrupted mid-run, re-invoke it (skills are idempotent).

## Definition of done
- All four artifacts exist in `.lissom/tasks/<ID>/`
- `Review.md` contains no issues within `fix_threshold` unless fix loop exhausts.
