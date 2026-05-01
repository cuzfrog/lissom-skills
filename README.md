# Lissom Skills

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/cuzfrog/lissom-skills)](https://github.com/cuzfrog/lissom-skills/stargazers)
[![GitHub last commit](https://img.shields.io/github/last-commit/cuzfrog/lissom-skills/main)](https://github.com/cuzfrog/lissom-skills/commits/main)
[![GitHub repo size](https://img.shields.io/github/repo-size/cuzfrog/lissom-skills)](https://github.com/cuzfrog/lissom-skills)

```
┌─┐
│L│░ LISSOM  —  Simple, reliable Claude Code skills & agents
└─┘  SKILLS     for daily dev automation and context protection.
```

#### Why? How this is different from GSD, SuperPower?
They are complex tool sets that require powerful AI models. Pressure on the model needs more care from developers. I see a single input prompt from CLI reach 50k+ or even more tokens. It feels like a cauldron we throw everthing into.

This skill set features:
- Thin-skill dispatcher pattern - relentless context protection.
- Idempotency - hussle-free resume with minimal state.
- Reinforced Specs - no surprise dev experience.

Lissom-skills is developed by Lissom-skills.

#### When to use? 
When you have something relatively clear in mind and need to refine the specs and execute.

#### When not to use?
- Trivial tasks.
- Exploratory tasks with vague or evolving requirements.
- Huge scale tasks that require parallel processing.

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

## Installation
Install into your project's `.claude/`:
```bash
curl -fsSL https://raw.githubusercontent.com/cuzfrog/lissom-skills/main/install.sh | bash -s -- --project
```
or home directory (`~/.claude/`) with `--user`

## Here We Go!
1. Update your specs at `.lissom/tasks/T1/Specs.md`
2. **Run** `/lissom-auto T1` - get interviewed and wait for the job done!

## Configuration

Set preferences in `.lissom/settings.local.json` to avoid being asked each run:

```json
{
  "user_attention": "default",
  "fix_threshold": "warning"
}
```

| Key | Options |
|---|---|
| `user_attention` | `default` — Interview for major concerns; `auto` — Best effort auto pilot; `focused` — Exhaustive questioning |
| `fix_threshold` | `warning` — Fix critical & warnings; `critical` — Critical only; `suggestion` — All issues |
| `spec_review_required` | `yes` — Review and refine specs before research; `no` — Skip spec review |

## Uninstallation

Remove all installed files from the target directory:

```bash
curl -fsSL https://raw.githubusercontent.com/cuzfrog/lissom-skills/main/uninstall.sh | bash
```

Removes from both `./.claude/` and `~/.claude/`. Pass `--project` or `--user` to target only one. Only files originally installed by this bundle are removed — any custom files you added are left untouched. Empty directories are cleaned up automatically.

## Author
Cause Chung <cuzfrog@gmail.com> (Claude Certified)

See also: **[claude-code-litellm-hybrid-setup](https://github.com/cuzfrog/claude-code-litellm-hybrid-setup)**
