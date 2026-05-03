# Guidelines — Writing Skill and Agent Definitions

## Skill responsibilities (thin dispatcher)
- Declare inputs, spawn the partner agent, verify the output artifact exists, report back.
- Escalate on missing artifacts after one retry; do not retry indefinitely.
- Do not contain domain logic. Stateless looping or branching is dispatcher logic, not domain logic.
- The Completion section is where the skill writes lifecycle artifacts (e.g., summary files).

## Agent responsibilities (rich domain logic)
- Own all domain logic: format, idempotency, iteration, escalation rules.
- Idempotency belongs in the agent — the agent knows what "stale" means.
- Declare only tools the agent actually uses.

## Descriptions
- Skill descriptions say what the skill does (dispatches, coordinates), not what the agent does.
- Agent descriptions summarize the domain logic.

## Section order
Skills: Inputs → Process → Constraints (if any) → Completion.
Agents: Inputs → Idempotency → Process → Output → Constraints.

## Format
- Keep files small. Remove decorative formatting that adds no meaning.
- **Important** Prefer single-line statements. Do not add newline to break a sentence for visual alignment.
- Use bold sparingly — for section-internal labels, not emphasis on random words.
- For tool call, explicitly write: "use Tool `<ToolName>` to". For example, "Use Tool `AskUserQuestion` to interview user."
- Arguments must be explicitly declared in **Inputs** section, using "snake_case".
- Identifiers like arguments, filename, toolname, enums, anchor use apostrophe quotes. E.g. `task_id`.
- Logic clauses and titles use double star quotes (bold). E.g. **If no step files exist**, **Goal**.
- Descriptive terms use double quotes when needed.
- Do not use emojis in Markdown files.


## Frontmatter
Required fields for all definitions: `name`, `description`.
Required top comment on line 1: `<!-- version: ISO8601-timestamp -->`.
All definitions must begin with the version comment before the `---` frontmatter delimiter.
Example: `<!-- version: 2026-05-03T12:48:24Z -->`.
Additional agent fields: `tools`, `model`.
Optional: `argument-hint` (skills only, shown to the user as invocation hint).
`description` must be one concise sentence. Multi-line YAML block scalars (`>`) are acceptable if the sentence is long.

## Checklist
1. Is idempotency handled (in the agent)?
2. Is information on a need-to-know basis? Are there duplicates across skill and agent?
3. Are input and output contracts specific and accurate?
4. Is `AskUserQuestion` used for all user interaction?
5. Can a tool, hook, or non-LLM mechanism replace an LLM call?
6. Is `TodoWrite` used to report task progress for user observability?
