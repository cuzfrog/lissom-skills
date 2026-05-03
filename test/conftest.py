"""
Shared test helpers for install/uninstall test suites.
"""
from pathlib import Path

AGENTS = (
    "lissom-implementer",
    "lissom-planner",
    "lissom-researcher",
    "lissom-reviewer",
    "lissom-specs-reviewer",
)
SKILLS = (
    "lissom-auto",
    "lissom-impl",
    "lissom-plan",
    "lissom-research",
    "lissom-review",
)


def make_opencode_frontmatter(agent_name: str, include_model: bool = False) -> str:
    """
    Generate Opencode-style YAML frontmatter for an agent.
    
    Args:
        agent_name: Agent name (e.g. "lissom-researcher")
        include_model: Whether to include model field
    
    Returns:
        Opencode frontmatter as string
    """
    fm = f"---\nname: {agent_name}\ndescription: fixture\nmode: subagent\n"
    
    if include_model:
        # Map agent names to Opencode models
        model_map = {
            "lissom-implementer": "opencode-go/deepseek-v4-flash",
            "lissom-planner": "opencode-go/qwen3.6-plus",
            "lissom-researcher": "opencode-go/deepseek-v4-flash",
            "lissom-reviewer": "opencode-go/qwen3.6-plus",
        }
        model = model_map.get(agent_name, "opencode-go/qwen3.6-plus")
        fm += f"model: {model}\n"
    
    fm += "temperature: 0.1\npermission:\n  read: allow\n  write: allow\n---\nbody\n"
    return fm


def make_qwen_frontmatter(agent_name: str, include_model: bool = False) -> str:
    """
    Generate Qwen Code-style YAML frontmatter for an agent.

    Args:
        agent_name: Agent name (e.g. "lissom-researcher")
        include_model: Whether to include model field

    Returns:
        Qwen Code frontmatter as string
    """
    # Qwen Code tool mapping (consistent with CLAUDE_TO_QWEN_TOOL in constants.sh)
    tool_map = {
        "Bash": "run_shell_command",
        "Read": "read_file",
        "Write": "write_file",
        "Edit": "edit",
        "Glob": "glob",
        "Grep": "grep_search",
        "WebFetch": "web_fetch",
        "WebSearch": "web_search",
    }
    tools_yaml = "\n".join(f"  - {t}" for t in tool_map.values())

    fm = f"---\nname: {agent_name}\ndescription: fixture\n"

    if include_model:
        model_map = {
            "lissom-implementer": "qwen3-coder-plus",
            "lissom-planner": "qwen3.6-plus",
            "lissom-researcher": "qwen3.6-plus",
            "lissom-reviewer": "qwen3.6-plus",
            "lissom-specs-reviewer": "qwen3.6-plus",
        }
        model = model_map.get(agent_name, "qwen3.6-plus")
        fm += f"model: {model}\n"

    fm += f"tools:\n{tools_yaml}\n---\nbody\n"
    return fm


def make_gemini_frontmatter(agent_name: str, include_model: bool = False) -> str:
    """
    Generate Gemini CLI-style YAML frontmatter for an agent.

    Args:
        agent_name: Agent name (e.g. "lissom-researcher")
        include_model: Whether to include model field

    Returns:
        Gemini CLI frontmatter as string (with temperature: 0.1)
    """
    tool_map = {
        "Bash": "run_shell_command",
        "Read": "read_file",
        "Write": "write_file",
        "Edit": "replace",
        "Glob": "glob",
        "Grep": "grep_search",
        "WebFetch": "web_fetch",
        "WebSearch": "google_web_search",
        "AskUserQuestion": "ask_user",
    }
    tools_yaml = "\n".join(f"  - {t}" for t in tool_map.values())

    fm = f"---\nname: {agent_name}\ndescription: fixture\n"
    fm += "temperature: 0.1\n"

    if include_model:
        model_map = {
            "lissom-implementer": "gemini-3-flash-preview",
            "lissom-planner": "gemini-3-flash-preview",
            "lissom-researcher": "gemini-3-pro-preview",
            "lissom-reviewer": "gemini-3-flash-preview",
            "lissom-specs-reviewer": "gemini-3-flash-preview",
        }
        model = model_map.get(agent_name, "gemini-3-flash-preview")
        fm += f"model: {model}\n"

    fm += f"tools:\n{tools_yaml}\n---\nbody\n"
    return fm


def make_src_tree(
    src: Path, with_model: dict = None, target_format: str = "claude"
) -> None:
    """
    Create a fixture source tree with all agents and skills.
    
    Args:
        src: Root directory for the fixture tree
        with_model: Optional dict mapping agent names to model values.
                   If provided, adds model: field to specified agents.
                   Example: {"lissom-researcher": "opus-4.6", "lissom-planner": "sonnet"}
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
            frontmatter = make_opencode_frontmatter(agent, include_model)
        elif target_format == "qwen":
            # Use Qwen Code format
            include_model = with_model and agent in with_model
            frontmatter = make_qwen_frontmatter(agent, include_model)
        elif target_format == "gemini":
            # Use Gemini CLI format
            include_model = with_model and agent in with_model
            frontmatter = make_gemini_frontmatter(agent, include_model)
        else:
            # Use Claude Code format (default)
            frontmatter = f"---\nname: {agent}\ndescription: fixture\ntools: Read, Write\n"
            if with_model and agent in with_model:
                frontmatter += f"model: {with_model[agent]}\n"
            frontmatter += "---\nbody\n"
        
        (src / "agents" / f"{agent}.md").write_text(frontmatter)
    
    for skill in SKILLS:
        (src / "skills" / skill).mkdir(parents=True, exist_ok=True)
        (src / "skills" / skill / "SKILL.md").write_text(
            f"---\nname: {skill}\ndescription: fixture\n---\nbody\n"
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
        agent_name: Name of the agent (e.g., "lissom-researcher")
    """
    path.write_text(
        f"---\nname: {agent_name}\ndescription: fixture\ntools: read\nbody without closing frontmatter\n"
    )
