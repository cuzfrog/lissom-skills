# Project — Lissom-Skills

## Purpose

A Claude Code skill and agent set designed to be specific and reliable.

## Project Structure

### Production contents (edit these)

- `skills/` — skill definitions (thin dispatchers)
- `agents/` — agent definitions (rich domain logic)
- `templates/` — files installed into a client project (`Specs.md`)
- `scripts/` — client install/remove scripts with helpers in `scripts/lib/`

### Development workspace

- `test/` - unit test dir.
- `dev/` - hook scripts or developer scripts.
- `.claude/` — internal dev-time skills and agents used to build this project. **Do not edit** — these are not production contents.
- all dirs in @.gitignore

## Test Method
- `scripts/` changes must follow TDD workflow.
- When implementing `.sh` scripts, must take into consideration that the script will be pipelined into `bash`, so user input should be read from tty.
- Use `pytest` to execute tests. Run a single test file: `pytest test/test_install.py -v`
- Use `/tmp/tests/**` as the workspace for test cases that require file operations.

## Rules

- When touching `skills/` or `agents/`, follow @Guidelines.md.
