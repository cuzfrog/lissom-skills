# Gemini CLI Agent Frontmatter — Reference Example

Below is the expected output after converting a Claude Code agent file to Gemini CLI format.

## Input (Claude Code source frontmatter)

```yaml
---
name: lissom-researcher
version: 2026-04-30T10:00:00Z
description: Researches and analyzes code, documentation, and best practices...
tools: Bash, Read, Write, Edit, Glob, Grep, WebFetch, WebSearch, AskUserQuestion
---
```

## Output (Gemini CLI target frontmatter)

```yaml
---
name: lissom-researcher
description: Researches and analyzes code, documentation, and best practices...
version: 2026-04-30T10:00:00Z
temperature: 0.1
model: gemini-3-pro-preview
tools:
  - run_shell_command
  - read_file
  - write_file
  - replace
  - glob
  - grep_search
  - web_fetch
  - google_web_search
  - ask_user
---
```

## Conversion rules applied

- `name`, `description`, `version` preserved
- `temperature: 0.1` added (always)
- `model: gemini-3-pro-preview` added (when user opts in; otherwise omitted)
- `tools:` inline CSV converted to YAML list with Gemini CLI tool names
- `AskUserQuestion` → `ask_user` (included, not removed)
- `Edit` → `replace`
- `WebSearch` → `google_web_search`
