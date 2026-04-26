# Project - Lissom-Skills

A set of Skills and Agents that power a simple, clean, and reliable task resolution process.

## Project structure
For development:
- `.dev/tasks/<ID>/` - Tasks for this project's development
- `.claude` - lissom-skills is used to develop this project itself, do not change skills and agents in this dir, they are not project contents.

Project contents:
- `skills/` - skills definitions
- `agents/` - agents definitions
- `templates/` - for installing into a client dir.
- `install.sh` and `uninstall.sh` script for a client to install or remove lissom-skills.

## General requirements
- keep code and text simple and readable.
- After skills and agents definitions are updated, stage the changes but do not commit, I need to review.
