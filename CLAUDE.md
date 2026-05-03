# Project — Lissom-Skills

## Purpose

A Claude Code skill and agent set designed to specific and reliable.

## Project Structure

### Production contents (edit these)

- `skills/` — skill definitions (thin dispatchers)
- `agents/` — agent definitions (rich domain logic)
- `templates/` — files installed into a client project
- `scripts/` — client install/remove scripts

### Development workspace

- `test/` - unit test dir.
- `dev/` - hook scripts or developer scripts.
- `.claude/` — internal dev-time skills and agents used to build this project. **Do not edit** — these are not production contents.
- all dirs in @.gitignore

## Test Method
- `scripts/` changes must follow TDD workflow.
- use `pytest` to execute tests
- use `/tmp/tests/**` as the workspace for test cases that require file operations

## Rules

- When editing skill or agent definitions, follow `Guidelines.md`.
