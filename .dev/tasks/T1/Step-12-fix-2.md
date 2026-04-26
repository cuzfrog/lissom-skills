# Step 12 (Fix cycle 2) — Fix mode description in `agents/task-implementer.md`

**Problem:** From Review.md (Critical):
> The agent's Inputs section reads: `- \`mode\`: \`interview\` (default) or \`auto\` — controls whether the implementer pauses for user confirmation or runs autonomously.`
> 
> The spec is explicit: "Interview only happens at \`research\` stage." The implementer must not change behavior based on mode.

**Root cause:** During Step 5 (original implementation), the mode input description was copied from the skill template without correcting the incorrect behavior assumption. The same defect was fixed in `skills/task-impl/SKILL.md` during Fix cycle 1 (commit `efcad2c`), but the corresponding agent definition was not updated.

**Fix:** Edit `agents/task-implementer.md` line 17:

**Old:**
```
- `mode`: `interview` (default) or `auto` — controls whether the implementer pauses for user confirmation or runs autonomously.
```

**New:**
```
- `mode`: `interview` (default) or `auto` — passed through from the calling skill; does not affect implementer behavior.
```

**Acceptance criterion:** Line 17 of `agents/task-implementer.md` contains the corrected description acknowledging that mode is passed through but does not affect implementer behavior.
