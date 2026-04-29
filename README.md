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

This skill set provides the minimal skills to relentlessly protect the context while respect the foundamental high-quality dev cycles.
- Thin-skill dispatcher pattern (lifecycle in skill, domain logic in agent) to ensure minimal coordinator context requirement.
- Idempotency of each stage and step to provide resume ability.
- Unequivocal logic that works on mundane models. See also: **[claude-code-litellm-hybrid-setup](https://github.com/cuzfrog/claude-code-litellm-hybrid-setup)**.
- Reinforced specs to eliminate any surprises.

Lissom-skills is developed by Lissom-skills.

### Basic Workflow
```
          ┌─ interview ─┐
          │             /
research ─┘ auto ──►   +   ──► plan ──► impl ──► review ──► done
  ▲         Research.md  /    Plan.md         Review.md     │
  │                     /                                   │ critical?
  │                     └──────────── fix cycle (max 3)  ◄──┘
  │                                          │
  └──────────────── fix cycles exhausted ────┘
```
Why there is no `explore` stage? It's essentially duplicate with `research`.
The simplifiy of `lissom-skills` gives users the control on the task scope and level.
For a fine-grind task, knowing the whole picture, usually a large doc, is not necessary.
For a high-level task, the user can define a dedicated explore task.

## Installation
Install into your project's `.claude/`:
```bash
curl -fsSL https://raw.githubusercontent.com/cuzfrog/lissom-skills/main/install.sh | bash -s -- --project
```
or home directory (`~/.claude/`) with `--user`

## Here We Go!

1. Update your specs at `.dev/tasks/T1/Specs.md`

2. **Run your first task** - get interviewed and wait for the job done!
```claude
/task-auto T1
```
or, with best effort:
```claude
/task-auto T1, no interview
```

#### Multi-tasking
```claude
/task-auto T1 T2 T3
```
Dependency analysis and reordering included.

## Uninstallation

Remove all installed files from the target directory:

```bash
curl -fsSL https://raw.githubusercontent.com/cuzfrog/lissom-skills/main/uninstall.sh | bash
```

Removes from both `./.claude/` and `~/.claude/`. Pass `--project` or `--user` to target only one. Only files originally installed by this bundle are removed — any custom files you added are left untouched. Empty directories are cleaned up automatically.

## Author
Cause Chung <cuzfrog@gmail.com>
