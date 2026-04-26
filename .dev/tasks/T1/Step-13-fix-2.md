# Step 13 (Fix cycle 2) — Add mode input declaration to `agents/task-planner.md`

**Problem:** From Review.md (Minor):
> `task-plan/SKILL.md` now passes `mode` to the planner agent, but `agents/task-planner.md` has no mention of `mode` in its Inputs section. Every other agent that receives mode declares it. The omission means a weaker model running the planner standalone may not be aware that mode was supplied.

**Root cause:** During Step 1 of the original plan, the planner skill was updated to pass `mode` to the agent, but the agent definition itself was not updated to declare `mode` in its Inputs section, creating an incomplete specification.

**Fix:** Edit `agents/task-planner.md` Inputs section to add mode declaration:

**Old:**
```
## Inputs

The caller supplies a task ID. Read `.dev/tasks/<ID>/Research.md` (fall back
to `Specs.md` if research does not exist yet).
```

**New:**
```
## Inputs

The caller supplies:
- A task ID. Read `.dev/tasks/<ID>/Research.md` (fall back to `Specs.md` if research does not exist yet).
- `mode`: `interview` (default) or `auto` — acknowledge only; planner behavior does not change based on mode.
```

**Acceptance criterion:** The Inputs section of `agents/task-planner.md` declares `mode` with both values and the acknowledge-only note, matching the pattern used in other agents.
