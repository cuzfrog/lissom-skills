"""
Shared test helpers for install/uninstall test suites.
"""
from pathlib import Path

AGENTS = (
    "task-implementer",
    "task-planner",
    "task-researcher",
    "task-reviewer",
)
SKILLS = (
    "task-auto",
    "task-impl",
    "task-plan",
    "task-research",
    "task-review",
)


def make_src_tree(src: Path, version: str) -> None:
    """Create a fixture source tree with all agents and skills at the given version."""
    for agent in AGENTS:
        (src / "agents").mkdir(parents=True, exist_ok=True)
        (src / "agents" / f"{agent}.md").write_text(
            f"---\nname: {agent}\nversion: {version}\ndescription: fixture\n---\nbody\n"
        )
    for skill in SKILLS:
        (src / "skills" / skill).mkdir(parents=True, exist_ok=True)
        (src / "skills" / skill / "SKILL.md").write_text(
            f"---\nname: {skill}\nversion: {version}\ndescription: fixture\n---\nbody\n"
        )
