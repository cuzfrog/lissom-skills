---
name: task-auto
version: 2026-04-29T04:00:57Z
description: Dispatches one or more task IDs to task-coordinator after parsing mode and IDs from user input.
---

## Inputs

The user supplies one or more task IDs and an optional mode flag.

**Parsing mode from user arguments:**
- If the user's message contains `auto` or `no interview`, set `mode = auto`.
- Otherwise, default to `mode = interview`.

**Parsing task IDs:**
- Split the user message on whitespace and commas.
- Remove any token that was already consumed as a mode keyword (`auto`, `no interview`).
- From the remaining tokens, collect those that match the task-ID pattern: at least one letter followed by at least one digit (e.g. `T1`, `TEST01`). Pure-word tokens such as "auto" or "interview" are excluded by this pattern.

Examples:
- `/task-auto T1` → mode is `interview`
- `/task-auto T1, auto` → mode is `auto`
- `/task-auto T1 T2 T3` → mode is `interview`
- `/task-auto T1, T2, auto` → mode is `auto`

## Dispatch

After parsing the mode and task ID(s), invoke `task-coordinator` with:
- `task_ids`: the list of parsed task IDs
- `mode`: the parsed mode (`auto` or `interview`)

The coordinator returns a verdict token. If the return does not contain a verdict token (`DONE: PASS` or `DONE: FAIL -- ...`), escalate to the user with a description of the error.

Summarize the outcome to the user based on the verdict.
