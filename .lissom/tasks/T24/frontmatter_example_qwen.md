# Qwen Code Agent Frontmatter Reference

Example of a converted lissom agent file as it appears after installation to `.qwen/agents/`:

## Agent file: lissom-researcher.md

```yaml
---
name: lissom-researcher
description: Researches and analyzes code, documentation, and best practices.
version: 2026-04-30T10:00:00Z
model: qwen3.6-plus
tools:
  - run_shell_command
  - read_file
  - write_file
  - edit
  - glob
  - grep_search
  - web_fetch
  - web_search
---
```

### Field reference

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Agent name used as an identifier |
| `description` | Yes | Human-readable description of the agent |
| `version` | Yes | Version timestamp (preserved from source) |
| `model` | No | Model ID for subagent (present only if user opted in) |
| `tools` | Yes | YAML list of available tools in snake_case |

### Tool name mapping

| Claude Code | Qwen Code |
|-------------|-----------|
| `Bash` | `run_shell_command` |
| `Read` | `read_file` |
| `Write` | `write_file` |
| `Edit` | `edit` |
| `Glob` | `glob` |
| `Grep` | `grep_search` |
| `WebFetch` | `web_fetch` |
| `WebSearch` | `web_search` |
| `AskUserQuestion` | (removed from tools list) |
