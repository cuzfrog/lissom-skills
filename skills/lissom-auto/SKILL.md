---
name: lissom-auto
description: Runs the full dev cycle (research → plan → impl → review + fix loop) for a task.
argument-hint: <task_id>
---

## Inputs

- `task_id` = "$0"
- `extra_info` = $ARGUMENTS (optional)

## Preference resolution

1. Load `.lissom/settings.local.json` from the project root. It may be absent or empty — treat either as no preferences set.
2. Load `<skill_dir>/user_preference_questions.json` from this skill's directory. Each entry has a `preference_arg` key (the preference name).
3. For each preference, check if it is present in `settings.local.json`. If set, use it.
4. For any preference not found in `settings.local.json`:
    - Inform user: "Preferences can be set in `.lissom/settings.local.json`, see README."
    - If the user answers `user_attention`=`auto` or `extra_info` demands auto processing, skip all rest questions and set `fix_threshold`=`critical`, `spec_review_required`=`false`.
    - If the user answers `spec_review_required`=`true`, set `research_required`=`true` and skip that question.
    - Use Tool `AskUserQuestion` to prompt the user using the entry's question/options. The first option in each question is the default one.

### Preference variables (question order):
- `user_attention` = `default`, `auto`, `focused`
- `fix_threshold` = `warning`, `critical`, `suggestion`
- `spec_review_required` = `false`, `true`
- `research_required` = `true`, `false`

## Task Directory Resolution
1. `task_dir` = `.lissom/tasks/<task_id>` or `.lissom/tasks/backlog/<task_id>`
2. If neither path exists, search available tools to locate the task, for example a JIRA ID. Then copy the task into `.lissom/tasks/<task_id>/Specs.md` and use `.lissom/tasks/<task_id>` as `task_dir`.
3. If the task still cannot be found, fail.

### Task Artifact discovery
- Prefer read files directly or list dir instead of file search. Because file search tools may respect exclusion rules, such as `.gitignore`, that hide the artifacts.

## Execution
0. Use Tool `TodoWrite` to track progress.
1. Invoke `lissom-research` with `task_dir`, `user_attention`, `spec_review_required`, and `research_required`. Wait for completion. If `spec_review_required` and `research_required` are both `false`, skip this step.
2. Invoke `lissom-plan` with `task_dir`. Verify `Plan.md` exists; retry once on missing.
3. Invoke `lissom-impl` with `task_dir`. Verify `Impl-summary.md` exists; retry once on missing.
4. Invoke `lissom-review` with `task_dir`. Verify `Review.md` exists; retry once on missing.
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
1. Invoke `lissom-plan` with `task_dir`, `fix_cycle`, and `fix_threshold`.
2. Invoke `lissom-impl` with `task_dir`.
3. Invoke `lissom-review` with `task_dir`.
4. Parse `Review.md` the same way as Execution step 5. If it passes → report success.

After 3 cycles with persistent issues, report failure and direct the user to `Review.md`.

## Rules

- Never write code, plans, or research directly. Delegate all work by invoking the named sub-skills above.
- If a sub-skill escalates a blocking question, use Tool `AskUserQuestion` to relay it to the user and pass the answer back.
- If a skill is interrupted mid-run, re-invoke it (skills are idempotent).
- Follow user instructions optionally from `extra_info`.

## Definition of done
- These artifacts exist in `.lissom/tasks/<task_id>/`: `Research.md`, `Plan.md`, `Impl-summary.md`, `Review.md`.
- `Review.md` contains no issues at or above `fix_threshold`, or the fix loop has exhausted 3 cycles.
