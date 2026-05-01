---
name: lissom-auto
version: 2026-04-30T02:15:06Z
description: Runs the full dev cycle (research → plan → impl → review + fix loop) for a task.
argument-hint: <task_id> [additional_instructions]
---

## Inputs

- `task_id`
- `additional_instructions` (optional)

## Preference resolution

1. Load `.lissom/settings.local.json` from the project root. It may be absent or empty — treat either as no preferences set.
2. Load `user_preference_questions.json` from this skill's directory. Each entry has a `preference_arg` key (the preference name).
3. For each preference, check if it is present in `settings.local.json`. If set, use it.
4. For any preference not found in `settings.local.json`:
    - inform user: "Preferences can be set in `.lissom/settings.local.json`, see README."
    - use `AskUserQuestion` to prompt the user using the entry's question/options. The first option in each question is the recommended one.

## Execution
0. Use Tool `TodoWrite` to track progress.
1. Invoke `lissom-research` with `task_id`, `user_attention`, and `spec_review_required`. Verify `Research.md` exists; retry once on missing, then fail with `Research.md missing after retry`.
2. Invoke `lissom-plan` with `task_id` and `user_attention`. Verify `Plan.md` exists; retry once on missing.
3. Invoke `lissom-impl` with `task_id`. Verify `Impl-summary.md` exists; retry once on missing.
4. Invoke `lissom-review` with `task_id`. Verify `Review.md` exists; retry once on missing.
5. Parse `Review.md` to decide whether to enter the fix loop:
  - Search for heading `**Critical**`. If found and followed by content before the next heading, critical issues exist.
  - Search for heading `**Warning**`. Same rule.
  - Search for heading `**Suggestion**`. Same rule.
   - Compare found issues against `fix_threshold`:
     - `critical` → fix loop only if critical issues exist.
     - `warning` (default) → fix loop if critical or warning issues exist.
     - `suggestion` → fix loop if any issues exist.
   If no issues at or above threshold → report success to the user.
6. Summarize the outcome for the user.

## Fix loop

Up to 3 cycles:
1. Invoke `lissom-plan` with `task_id`, `fix_cycle`, and `fix_threshold`.
2. Invoke `lissom-impl` with `task_id`.
3. Invoke `lissom-review` with `task_id`.
4. Parse `Review.md` the same way as Execution step 5. If it passes → report success.

After 3 cycles with persistent issues, report failure and direct the user to `Review.md`.

## Rules

- Never write code, plans, or research directly. Delegate all work by invoking the named sub-skills above.
- If a sub-skill escalates a blocking question, use `AskUserQuestion` to relay it to the user and pass the answer back.
- If a skill is interrupted mid-run, re-invoke it (skills are idempotent).

## Definition of done
- These artifacts exist in `.lissom/tasks/<ID>/`: `Research.md`, `Plan.md`, `Impl-summary.md`, `Review.md`.
- `Review.md` contains no issues at or above `fix_threshold`, or the fix loop has exhausted 3 cycles.
