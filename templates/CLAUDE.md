# Project context for Claude Code

## Project structure
- Describe key directories and files here.

## General requirements
- List coding conventions, testing requirements, and commit standards.
- Example: always run unit tests before committing.
- Example: keep code simple and readable.

## Off-limits
- List files or directories the agent must never read or modify.
- Example: never read `./deprecated/`, `./tmp/`.

## Task workflow
- Tasks live in `.dev/tasks/<ID>/Specs.md`.
- Use `task-auto` skill to run the full research → plan → implement → review cycle.
- Use individual `task-research`, `task-plan`, `task-impl`, `task-review` skills for finer control.
