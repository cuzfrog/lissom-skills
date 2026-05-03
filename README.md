# Lissom Skills

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/cuzfrog/lissom-skills)](https://github.com/cuzfrog/lissom-skills/stargazers)
[![GitHub last commit](https://img.shields.io/github/last-commit/cuzfrog/lissom-skills/main)](https://github.com/cuzfrog/lissom-skills/commits/main)
[![GitHub repo size](https://img.shields.io/github/repo-size/cuzfrog/lissom-skills)](https://github.com/cuzfrog/lissom-skills)
[![CI](https://github.com/cuzfrog/lissom-skills/actions/workflows/ci.yml/badge.svg)](https://github.com/cuzfrog/lissom-skills/actions/workflows/ci.yml)

**English** · [简体中文](README.zh.md) · [日本語](README.ja.md)

```
┌─┐
│L│░ LISSOM  —  Simple, reliable Claude Code skills & agents
└─┘  SKILLS     for daily dev automation and context protection.
```

---

#### Why? What's the difference from [GSD](https://github.com/gsd-build/get-shit-done), [SuperPower](https://github.com/obra/superpowers)?
- **Zero Dependency** — just plain files.
- **Thin Skill Dispatchers** — relentless context protection.
- **Idempotency** — hussle-free resume with minimal state.
- **Hammered Specs** — no surprise dev experience.

#### When to use?
- I have an idea, help me refine the specs and automate the implementation.

#### When not to use?
- Trivial tasks — do it in one agent.
- Exploratory tasks — use `/explore`.

### Basic Workflow
```
           ┌─ interview ─┐
           │             /
 research ─┘ auto ──►   +   ──► plan ──► impl ──► review ──► done
  Specs.md    Research.md /    Plan.md         Review.md     │
   ▲                     /                                   │ critical?
   │                     └──────────── fix cycle (max 3)  ◄──┘
   │                                          │
   └──────────────── fix cycles exhausted ────┘
```

---

## Installation

Install into your project's directory with:

```bash
curl -fsSL https://raw.githubusercontent.com/cuzfrog/lissom-skills/main/scripts/install.sh | bash
```

Supported:
- `.claude/` [Claude Code](https://code.claude.com/) and compatible agents.
- `.opencode/` [OpenCode](https://opencode.ai).
- `.qwen/` [Qwen Code](https://qwen.ai/qwencode).
- `.gemini/` [Gemini CLI](https://geminicli.com/).

---

## Here We Go!

**Run** `/lissom-auto <task_id>` — get interviewed and wait for the job done!

1. It looks for the task in `.lissom/tasks/<task_id>/Specs.md`
2. If not found, it tries to locate with tools (e.g. JIRA MCP)

### Best practices

- Reference to project documentation in your `Specs.md`. This saves exploration.
- Ensure test methods are clearly defined (e.g. in `CLAUDE.md`)

---

## Configuration

Set preferences in `.lissom/settings.local.json` to avoid being asked each run:

```json
{
  "user_attention": "default",
  "fix_threshold": "warning",
  "spec_review_required": "yes"
}
```

| Key | Options |
|---|---|
| `user_attention` | `default` — Interview for major concerns; `auto` — Best effort auto pilot; `focused` — Exhaustive questioning |
| `fix_threshold` | `warning` — Fix critical & warnings; `critical` — Critical only; `suggestion` — All issues |
| `spec_review_required` | `yes` — Review and refine specs before research; `no` — Skip spec review |

---

## Uninstallation

Remove all installed files from both `.claude/` and `.opencode/` directories in the current project:

```bash
curl -fsSL https://raw.githubusercontent.com/cuzfrog/lissom-skills/main/scripts/uninstall.sh | bash
```

Only files originally installed by this bundle are removed — any custom files you added are left untouched. Empty directories are cleaned up automatically.

---

## Links

- [GitHub](https://github.com/cuzfrog/lissom-skills) — source code and releases
- [Issues](https://github.com/cuzfrog/lissom-skills/issues) — bug reports and feature requests
- [License](LICENSE) — MIT

---

## Author

Cause Chung <cuzfrog@gmail.com>
