# Lissom Skills

Simple and reliable Claude Code Skills and Agents to automate daily tasks and protect the context.

#### Why? How this is different from GSD, SuperPower?

They are powerful skill sets. But I also noticed a sharp drop in coding quality from many projects. PRs have become hard to read, code base exploding, walls of documents and texts occupying dirs probably no one would dive into.

They require powerful AI models. Pressure on the model needs more care from developers. I see a single input prompt from CLI reach 50k+ or even more tokens. It feels like a cauldron we throw everthing into.

This skill set provides the minimal skills to improve context efficiency while respect the foundamental high-quality dev cycles.
- Thin-skill dispatcher pattern (lifecycle in skill, domain logic in agent) to ensure minimal coordinator context requirement.
- Idempotency of each stage and step to provide resume ability.
- Works on mundane models, see also: **[claude-code-litellm-hybrid-setup](https://github.com/cuzfrog/claude-code-litellm-hybrid-setup)**.

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

or home directory (`~/.claude/`):
```bash
curl -fsSL https://raw.githubusercontent.com/cuzfrog/lissom-skills/main/install.sh | bash -s -- --user
```

## Here We Go!

1. (Optional) **Customize CLAUDE.md**
   - Edit `.claude/CLAUDE.md` (or `~/.claude/CLAUDE.md`)
   - Document your project structure, coding conventions, and off-limits directories

2. **Set up task structure**
```bash
# 1. Create a task spec
mkdir -p .dev/tasks/T1
cat > .dev/tasks/T1/Specs.md << 'EOF'
# T1 — Add user authentication

Implement JWT-based authentication for the API.

## Requirements
- POST /auth/login endpoint
- JWT token generation with 24h expiry
- Middleware to verify tokens on protected routes
- Unit tests for auth logic
EOF
```

3. **Run your first task** - interview and wait for the job done!
```claude
/task-auto T1
```
or, with best effort:
```claude
/task-auto T1, no interview
```

## Uninstallation

Remove all installed files from the target directory:

```bash
curl -fsSL https://raw.githubusercontent.com/cuzfrog/lissom-skills/main/uninstall.sh | bash
```

Removes from both `./.claude/` and `~/.claude/`. Pass `--project` or `--user` to target only one. Only files originally installed by this bundle are removed — any custom files you added are left untouched. Empty directories are cleaned up automatically.

## Skills

This bundle includes 5 skills:

| Skill | Description | When to use |
|-------|-------------|-------------|
| **task-auto** | Orchestrator that runs the full dev cycle (research → plan → impl → review) with fix loops | Default choice for most tasks |
| **task-research** | Spawns task-researcher agent to explore codebase and produce Research.md | When you need to understand the codebase before planning |
| **task-plan** | Spawns task-planner agent to create Plan.md with ordered steps | When you have research and need a detailed implementation plan |
| **task-impl** | Spawns task-implementer agent to execute steps from Plan.md | When you have a plan and need to implement it |
| **task-review** | Spawns task-reviewer agent to examine changes and produce Review.md | When you want to review changes before considering a task complete |

## Agents

This bundle includes 4 sub-agents invoked by the skills:

| Agent | Model | Purpose | Output |
|-------|-------|---------|--------|
| **task-researcher** | Opus | Explore codebase, understand requirements, gather context, interviews | `.dev/tasks/<ID>/Research.md` |
| **task-planner** | Sonnet | Create step-by-step implementation plan with acceptance criteria | `.dev/tasks/<ID>/Plan.md` |
| **task-implementer** | Haiku | Execute plan steps, write code, run tests, commit changes | Commits per step |
| **task-reviewer** | Sonnet | Review git diffs, identify issues, categorize findings | `.dev/tasks/<ID>/Review.md` |

Model names here represent their strongth only, it can be any models you config. see also:
**[claude-code-litellm-hybrid-setup](https://github.com/cuzfrog/claude-code-litellm-hybrid-setup)**
