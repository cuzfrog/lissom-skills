# Plan — T1: Clear operation mode

## Goal

Add explicit `interview` (default) and `auto` modes to all core `task-*` skills and agents, moving all user Q&A from `task-plan` into `task-research`, and ensuring non-critical auto-mode assumptions are surfaced at the end of the dev cycle.

## Assumptions

1. The mode parameter uses values `interview` (default) and `auto`. No other values are needed.
2. Skills whose behavior is unchanged by mode (`task-review`) still declare and acknowledge the parameter for consistency.
3. The planner escalation mechanism ("pause if plan contains open questions") is distinct from an interview loop and is kept in `task-plan`.
4. The Assumptions section already present in the Research.md template is the canonical location for auto-mode assumption recording. No new section name is needed.
5. Only existing files are modified; no new skills, agents, or templates are created.

## Steps

### Step 1 — Update `skills/task-research/SKILL.md`

**File:** `skills/task-research/SKILL.md`

Add a `mode` parameter to the Inputs section. Update the agent invocation description to pass `mode` to the agent. Add a note that in `auto` mode the agent must produce an especially thorough Assumptions section since no user confirmation will occur.

Acceptance criterion: The file's Inputs section lists `mode` with both values and a default. The "What you do" section tells the skill to pass `mode` to the agent. A note about auto-mode assumption rigor is present.

---

### Step 2 — Update `agents/task-researcher.md`

**File:** `agents/task-researcher.md`

Add `mode` to the Inputs section. Add an interview loop to the Process section (active only when `mode` is `interview`). Add a note about auto-mode assumption recording. Describe exactly when the researcher must pause and escalate even in `auto` mode.

This step has detailed guidance — see `Step-2.md`.

Acceptance criterion: Inputs declares `mode`. Process contains an interview-loop block conditional on `interview` mode. Auto-mode escalation conditions (from the spec) are listed. The Output section notes that the Assumptions section must be thorough in `auto` mode.

---

### Step 3 — Update `skills/task-plan/SKILL.md`

**File:** `skills/task-plan/SKILL.md`

Remove the single line in the agent behavior list that instructs the planner to interview the user. The escalation sentence ("If the plan contains open questions for the user, pause and surface them before reporting back") is a different mechanism and must be kept.

Acceptance criterion: The file contains no language directing the planner to interview the user or ask Q&A. The escalation sentence for open questions is still present.

---

### Step 4 — Update `skills/task-impl/SKILL.md`

**File:** `skills/task-impl/SKILL.md`

Add `mode` to the Inputs section (acknowledge, no behavior change). Add to the Completion section an instruction that `Impl-summary.md` must include an Assumptions section copied from `.dev/tasks/<ID>/Research.md`.

Acceptance criterion: Inputs lists `mode`. The Completion / Impl-summary.md description includes a bullet for Assumptions sourced from Research.md.

---

### Step 5 — Update `agents/task-implementer.md`

**File:** `agents/task-implementer.md`

Add `mode` to the Inputs section. Add to the Finishing a step / Completion section an instruction to copy the Assumptions section from `Research.md` into `Impl-summary.md` so the user is informed of assumptions made during the auto run.

Acceptance criterion: Inputs declares `mode`. The section describing `Impl-summary.md` content includes the Assumptions copy instruction.

---

### Step 6 — Update `skills/task-review/SKILL.md`

**File:** `skills/task-review/SKILL.md`

Add an Inputs section that declares the `mode` parameter (acknowledge only; behavior does not change).

Acceptance criterion: The file has an Inputs section listing `mode` with both values and a default. No other behavior is changed.

---

### Step 7 — Update `agents/task-reviewer.md`

**File:** `agents/task-reviewer.md`

Add `mode` to the Inputs section (acknowledge only; review criteria and output format are unchanged).

Acceptance criterion: Inputs declares `mode`. No review criteria or output format lines are changed.

---

### Step 8 — Update `skills/task-auto/SKILL.md`

**File:** `skills/task-auto/SKILL.md`

Add mode-parsing logic to the Inputs section (detect `auto` / `no interview` from user arguments; default to `interview`). Update each sub-skill invocation in the Chain section and Fix loop to pass `mode` explicitly. Add an entry to Rules stating the coordinator must never ask Q&A unless escalation conditions are met.

This step has detailed guidance — see `Step-8.md`.

Acceptance criterion: Inputs section explains how to parse mode from user arguments. Every sub-skill call in Chain and Fix loop includes `mode`. Rules section forbids the coordinator from conducting Q&A independently.

---

## Risks

1. **Planner escalation ambiguity** (Risk from Research): The distinction between "interview loop" (removed) and "escalation for open questions in the plan" (kept) must be clear. If the implementer removes both, the planner loses its ability to surface genuine blockers.
2. **Interview loop wording vs. model capability**: The researcher agent's interview loop description must be prescriptive enough for weaker models to follow. Step-2.md provides the exact wording to use.
3. **Auto-mode escalation triggers**: The spec defines five specific conditions under which even auto mode must pause and escalate. These must be listed verbatim in the researcher agent so they are not lost.

---

## Fix cycle 1

Addresses findings from `Review.md`. Three fix steps:

- **Step-9-fix-1.md** — Critical: Remove incorrect interview/auto behavior description from `skills/task-impl/SKILL.md` Inputs. Replace with acknowledge-only mode line.
- **Step-10-fix-1.md** — Minor: Add `## Inputs` section (task_id + mode) to `skills/task-plan/SKILL.md`; update opening invocation line and agent spawn line.
- **Step-11-fix-1.md** — Minor: Add "and mode" to agent invocation lines in `skills/task-review/SKILL.md` and `skills/task-impl/SKILL.md`.

## Fix cycle 2

Addresses findings from Review.md (Fix cycle 1 re-review). Two fix steps:

- **Step-12-fix-2.md** — Critical: Fix incorrect mode-behavior description in `agents/task-implementer.md` line 17. The mode parameter was incorrectly documented as controlling pause-for-confirmation behavior; it must be documented as acknowledge-only (passed through but does not affect implementer behavior).
- **Step-13-fix-2.md** — Minor: Add mode input declaration to `agents/task-planner.md` Inputs section. The skill passes mode to the agent, but the agent definition did not declare it, creating an incomplete specification.
