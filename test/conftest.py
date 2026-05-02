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


def make_opencode_frontmatter(agent_name: str, version: str, include_model: bool = False) -> str:
    """
    Generate Opencode-style YAML frontmatter for an agent.
    
    Args:
        agent_name: Agent name (e.g. "task-researcher")
        version: Version timestamp
        include_model: Whether to include model field
    
    Returns:
        Opencode frontmatter as string
    """
    fm = f"---\nname: {agent_name}\ndescription: fixture\nversion: {version}\nmode: subagent\n"
    
    if include_model:
        # Map agent names to Opencode models
        model_map = {
            "task-implementer": "opencode-go/deepseek-v4-flash",
            "task-planner": "opencode-go/qwen3.6-plus",
            "task-researcher": "opencode-go/deepseek-v4-flash",
            "task-reviewer": "opencode-go/qwen3.6-plus",
        }
        model = model_map.get(agent_name, "opencode-go/qwen3.6-plus")
        fm += f"model: {model}\n"
    
    fm += "temperature: 0.1\npermission:\n  read: allow\n  write: allow\n---\nbody\n"
    return fm


def make_src_tree(
    src: Path, version: str, with_model: dict = None, target_format: str = "claude"
) -> None:
    """
    Create a fixture source tree with all agents and skills at the given version.
    
    Args:
        src: Root directory for the fixture tree
        version: Version timestamp to use in all files
        with_model: Optional dict mapping agent names to model values.
                   If provided, adds model: field to specified agents.
                   Example: {"task-researcher": "opus-4.6", "task-planner": "sonnet"}
        target_format: "claude" (default) or "opencode" to control frontmatter format
    """
    # Copy scripts/lib from the real repo to the fixture
    import shutil as shutil_module
    repo_root = Path(__file__).resolve().parent.parent
    scripts_lib_src = repo_root / "scripts" / "lib"
    scripts_lib_dest = src / "scripts" / "lib"
    if scripts_lib_src.exists():
        shutil_module.copytree(scripts_lib_src, scripts_lib_dest, dirs_exist_ok=True)
    
    for agent in AGENTS:
        (src / "agents").mkdir(parents=True, exist_ok=True)
        
        if target_format == "opencode":
            # Use Opencode format
            include_model = with_model and agent in with_model
            frontmatter = make_opencode_frontmatter(agent, version, include_model)
        else:
            # Use Claude Code format (default)
            frontmatter = f"---\nname: {agent}\nversion: {version}\ndescription: fixture\ntools: read, write\n"
            if with_model and agent in with_model:
                frontmatter += f"model: {with_model[agent]}\n"
            frontmatter += "---\nbody\n"
        
        (src / "agents" / f"{agent}.md").write_text(frontmatter)
    
    for skill in SKILLS:
        (src / "skills" / skill).mkdir(parents=True, exist_ok=True)
        # Skills use the same frontmatter format in both Claude and Opencode
        # (only name, description, version are used; Opencode ignores extra fields)
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
