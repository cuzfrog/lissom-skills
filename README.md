# Lissom Skills

Simple and reliable Claude Code Skills and Agents to automate daily tasks and protect the context.
Tested on mundane models, see also:
**[claude-code-litellm-hybrid-setup](https://github.com/cuzfrog/claude-code-litellm-hybrid-setup)** — Route Claude Code requests through LiteLLM to mix models and providers.

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

3. **Run your first task** - and wait for the job done!
```claude
/task-auto T1
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

### Workflow

1. **Research phase**: Explores relevant code, reads specs, produces `Research.md`
2. **Planning phase**: Creates `Plan.md` with ordered steps and acceptance criteria
3. **Implementation phase**: Executes each step, runs tests, commits changes
4. **Review phase**: Examines git diffs, reports critical/warning/suggestion findings
5. **Fix cycle** (if needed): Planner creates fix steps, implementer executes, review re-runs (max 3 cycles)

## Agents

This bundle includes 4 sub-agents invoked by the skills:

| Agent | Model | Purpose | Output |
|-------|-------|---------|--------|
| **task-researcher** | Claude Opus | Explore codebase, understand requirements, gather context | `.dev/tasks/<ID>/Research.md` |
| **task-planner** | Claude Sonnet | Create step-by-step implementation plan with acceptance criteria | `.dev/tasks/<ID>/Plan.md` |
| **task-implementer** | Claude Haiku | Execute plan steps, write code, run tests, commit changes | Commits per step |
| **task-reviewer** | Claude Sonnet | Review git diffs, identify issues, categorize findings | `.dev/tasks/<ID>/Review.md` |

Agents are automatically invoked by skills — you don't call them directly.
