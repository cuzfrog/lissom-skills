# Project - Lissom-Skills

Purpose: built a neat Claude Code skill set that can run well on mundane AI models.

## Project structure
For development:
- `.lissom/tasks/<ID>/`
- `.claude` - lissom-skills is used to develop this project itself, do not change skills and agents in this dir, they are not project contents.

Project production contents:
- `skills/` - skills definitions
- `agents/` - agents definitions
- `templates/` - for installing into a client dir.
- `install.sh` and `uninstall.sh` scripts for a client to install or remove lissom-skills.

## General requirements
- When editing Skill/Agent definitions, refer to @Guidelines.md

