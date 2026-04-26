# Lissom Skills — Claude Code task workflow system

A reusable bundle of Claude Code skills and agents that implement a structured development workflow: **research → plan → implement → review**.

This package helps teams:
- Break down complex tasks into verifiable steps
- Maintain consistent code quality with automated reviews
- Document decisions and context for each task
- Iterate quickly with structured fix cycles

## Requirements

- [Claude Code CLI](https://docs.github.com/en/copilot/using-github-copilot/using-claude-in-vs-code) installed
- Git (for the workflow; not required for installation)
- Bash shell (for the install script)

## Installation

### Option 1: Project-local install (recommended)

Install into your project's `.claude/` directory:

```bash
git clone https://github.com/cuzfrog/lissom-skills.git
cd lissom-skills
./install.sh --project
```

### Option 2: Global install

Install into your home directory (`~/.claude/`) to use across all projects:

```bash
git clone https://github.com/cuzfrog/lissom-skills.git
cd lissom-skills
./install.sh --user
```

### Option 3: One-line install (project-local)

```bash
curl -fsSL https://raw.githubusercontent.com/cuzfrog/lissom-skills/main/install.sh | bash -s -- --project
```

### Option 4: One-line install (global)

```bash
curl -fsSL https://raw.githubusercontent.com/cuzfrog/lissom-skills/main/install.sh | bash -s -- --user
```

## After installation

1. **Customize CLAUDE.md**
   - Edit `.claude/CLAUDE.md` (or `~/.claude/CLAUDE.md`) to describe your project
   - Document your project structure, coding conventions, and off-limits directories

2. **Set up task structure**
   - Create `.dev/tasks/<ID>/` directories for each task
   - Write task specifications in `.dev/tasks/<ID>/Specs.md`

3. **Run your first task**
   - Open Claude Code in VS Code
   - Use the `task-auto` skill with your task ID: "Run task-auto for task T1"
   - The workflow will research, plan, implement, and review automatically

## Skills

This bundle includes 5 skills:

| Skill | Description | When to use |
|-------|-------------|-------------|
| **task-auto** | Orchestrator that runs the full dev cycle (research → plan → impl → review) with fix loops | Default choice for most tasks |
| **task-research** | Spawns task-researcher agent to explore codebase and produce Research.md | When you need to understand the codebase before planning |
| **task-plan** | Spawns task-planner agent to create Plan.md with ordered steps | When you have research and need a detailed implementation plan |
| **task-impl** | Spawns task-implementer agent to execute steps from Plan.md | When you have a plan and need to implement it |
| **task-review** | Spawns code-reviewer agent to examine changes and produce Review.md | When you want to review changes before considering a task complete |

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
| **code-reviewer** | Claude Sonnet | Review git diffs, identify issues, categorize findings | `.dev/tasks/<ID>/Review.md` |

Agents are automatically invoked by skills — you don't call them directly.

## Example workflow

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

# 2. Run the automated workflow
# Open Claude Code in VS Code and say:
# "Run task-auto for task T1"

# The skill will:
# - Research: Explore your codebase, identify auth patterns
# - Plan: Create a step-by-step implementation plan
# - Implement: Execute each step, run tests, commit changes
# - Review: Examine the diff, report any issues
# - Fix (if needed): Create fix steps, re-implement, re-review

# 3. Review the outputs
ls .dev/tasks/T1/
# Research.md  - Context and exploration notes
# Plan.md      - Implementation steps
# Review.md    - Code review findings

# 4. Check the commits
git log --oneline
# Each step creates a commit with "Co-authored-by: Copilot"
```
