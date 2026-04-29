# Guidelines — Writing Skill and Agent Definitions

## Skill responsibilities (thin dispatcher)
- Declare inputs, spawn the partner agent, verify the output artifact exists, report back.
- Escalate on missing artifacts after one retry; do not retry indefinitely.
- Do not contain domain logic. (Stateless looping or branching is not domain logic, they belong to legitimate dispatcher logic.)
- Completion section owns lifecycle checkpoints (e.g., writing summary files).

## Agent responsibilities (rich domain logic)
- Own all domain logic: format, idempotency, iteration, escalation rules.
- Idempotency belongs here — the agent knows what "stale" means.
- Keep tool declarations to only what the agent actually needs.
- Condense verbose enumerated lists into tight bullets when the model is capable of inference.

## Descriptions
- Skill descriptions must say what the skill does (dispatches, coordinates), not what the agent does (implements, reviews).
- Agent descriptions summarize the logic.

## Checklist
- Is idempotency handled?
- Is there duplicate info?
