# Project - Lissom-Skills

Purpose: built a neat skill set that can run well on mundane AI models with small context windows.

## Project structure
For development:
- `.dev/tasks/<ID>/`
- `.claude` - lissom-skills is used to develop this project itself, do not change skills and agents in this dir, they are not project contents.

Project production contents:
- `skills/` - skills definitions
- `agents/` - agents definitions
- `templates/` - for installing into a client dir.
- `install.sh` and `uninstall.sh` scripts for a client to install or remove lissom-skills.

## General requirements
- keep text and files concise and simple.
- After skills and agents definitions are updated, stage the changes but do not commit, I need to review.
- After editing Skill/Agent defs, update the version to editing timestamp.
- Do not read `./deprecated/`, `./tmp/`.
- When editing Skill/Agent defs, refer to @Guidelines.md
- if files of "Project production contents" get added or removed, review and update `install.sh` and `uninstall.sh` scripts.
