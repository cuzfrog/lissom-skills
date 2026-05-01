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


def make_src_tree(src: Path, version: str, with_model: dict = None) -> None:
    """
    Create a fixture source tree with all agents and skills at the given version.
    
    Args:
        src: Root directory for the fixture tree
        version: Version timestamp to use in all files
        with_model: Optional dict mapping agent names to model values.
                   If provided, adds model: field to specified agents.
                   Example: {"task-researcher": "opus-4.6", "task-planner": "sonnet"}
    """
    for agent in AGENTS:
        (src / "agents").mkdir(parents=True, exist_ok=True)
        frontmatter = f"---\nname: {agent}\nversion: {version}\ndescription: fixture\ntools: read, write\n"
        if with_model and agent in with_model:
            frontmatter += f"model: {with_model[agent]}\n"
        frontmatter += "---\nbody\n"
        (src / "agents" / f"{agent}.md").write_text(frontmatter)
    
    for skill in SKILLS:
        (src / "skills" / skill).mkdir(parents=True, exist_ok=True)
        (src / "skills" / skill / "SKILL.md").write_text(
            f"---\nname: {skill}\nversion: {version}\ndescription: fixture\n---\nbody\n"
        )
    (src / "templates").mkdir(parents=True, exist_ok=True)
    (src / "templates" / "Specs.md").write_text(
        "# Task <ID> - <Title>\n\n## Requirements\n1. ...\n\n## AC\n1. ..\n\n## Notes\n- ...\n"
    )


def make_malformed_agent(path: Path, agent_name: str) -> None:
    """
    Create an agent file with malformed YAML frontmatter (missing closing ---).
    
    Args:
        path: Path where the malformed agent file should be created
        agent_name: Name of the agent (e.g., "task-researcher")
    """
    path.write_text(
        f"---\nname: {agent_name}\nversion: 2026-01-01T00:00:00\ndescription: fixture\ntools: read\nbody without closing frontmatter\n"
    )
