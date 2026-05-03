"""
Integration tests for install.sh.

Each test creates a fresh fixture source tree and an empty work directory
inside tmp_path, copies install.sh into the fixture source so that
SCRIPT_DIR resolves to the fixture, then runs the script from the work
directory and asserts postconditions.
"""
import os
import shutil
import subprocess
from pathlib import Path

from conftest import AGENTS, SKILLS, make_src_tree, make_malformed_agent

REPO_ROOT = Path(__file__).resolve().parent.parent
INSTALL_SH = REPO_ROOT / "scripts" / "install.sh"


def run_install(src: Path, work: Path, args=(), env_extra=None):
    """Copy install.sh into src so SCRIPT_DIR resolves there, then run it from work."""
    shutil.copy(INSTALL_SH, src / "install.sh")
    env = {**os.environ}
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        ["bash", str(src / "install.sh"), *args],
        cwd=str(work),
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
    )


# Test cases

def test_fresh_install(tmp_path):
    """T1: Fresh install copies all agents, skills, and Specs.md."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    result = run_install(src, work, env_extra={"LISSOM_YES": "1"})

    assert result.returncode == 0
    assert (work / ".claude" / "agents" / "lissom-researcher.md").is_file()
    assert (work / ".claude" / "skills" / "lissom-auto" / "SKILL.md").is_file()
    assert (work / ".lissom" / "tasks" / "T1" / "Specs.md").is_file()


def test_reinstall_same_version(tmp_path):
    """T2: Re-installing the same version overwrites silently with no downgrade prompt."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")
    run_install(src, work, env_extra={"LISSOM_YES": "1"})

    result = run_install(src, work)

    assert result.returncode == 0
    # The downgrade prompt phrase must not appear in stdout
    assert "newer than the source" not in result.stdout
    assert (work / ".claude" / "agents" / "lissom-researcher.md").is_file()


def test_reinstall_same_dir_suppresses_cross_warning(tmp_path):
    """T2b: Reinstalling to same target dir suppresses cross-directory warning."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    # First install to .claude
    run_install(src, work, env_extra={"LISSOM_YES": "1"})

    # Seed .opencode with lissom files (simulate a prior OpenCode installation)
    (work / ".opencode" / "agents").mkdir(parents=True)
    (work / ".opencode" / "agents" / "lissom-researcher.md").write_text(
        "---\nname: lissom-researcher\nversion: 2026-01-01T00:00:00\ndescription: fixture\n---\nbody\n"
    )

    # Reinstall to .claude (same target) — should NOT warn about .opencode
    result = run_install(src, work, env_extra={"LISSOM_TARGET": ".claude"})

    assert result.returncode == 0
    assert "Found existing installation in .opencode/" not in result.stdout


def test_upgrade(tmp_path):
    """T3: Source newer than installed overwrites silently without a prompt."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2025-01-01T00:00:00")
    run_install(src, work, env_extra={"LISSOM_YES": "1", "LISSOM_TARGET": ".claude"})
    make_src_tree(src, "2026-06-01T00:00:00")

    result = run_install(src, work, env_extra={"LISSOM_TARGET": ".claude"})

    assert result.returncode == 0
    assert "newer than the source" not in result.stdout
    content = (work / ".claude" / "agents" / "lissom-researcher.md").read_text()
    assert "2026-06-01T00:00:00" in content


def test_downgrade_accepted(tmp_path):
    """T4: All files are downgraded when LISSOM_YES=1."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-06-01T00:00:00")
    run_install(src, work, env_extra={"LISSOM_YES": "1"})
    make_src_tree(src, "2025-01-01T00:00:00")

    result = run_install(src, work, env_extra={"LISSOM_YES": "1"})

    assert result.returncode == 0
    content = (work / ".claude" / "agents" / "lissom-researcher.md").read_text()
    assert "2025-01-01T00:00:00" in content


def test_downgrade_declined(tmp_path):
    """T5: No tty causes the downgrade prompt to default to 'no'; newer installed files preserved."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-06-01T00:00:00")
    run_install(src, work, env_extra={"LISSOM_YES": "1"})
    make_src_tree(src, "2025-01-01T00:00:00")

    result = run_install(src, work)

    assert result.returncode == 0
    content = (work / ".claude" / "agents" / "lissom-researcher.md").read_text()
    assert "2026-06-01T00:00:00" in content


def test_mixed_versions(tmp_path):
    """T6: Newer-source files upgrade silently; older-source file is skipped (one file skipped)."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")
    run_install(src, work, env_extra={"LISSOM_YES": "1"})

    # lissom-researcher source becomes newer → should upgrade silently
    (src / "agents" / "lissom-researcher.md").write_text(
        "---\nname: lissom-researcher\nversion: 2026-06-01T00:00:00\ndescription: fixture\n---\nbody\n"
    )
    # lissom-planner source becomes older → should be skipped (prompt declined via no tty)
    (src / "agents" / "lissom-planner.md").write_text(
        "---\nname: lissom-planner\nversion: 2025-01-01T00:00:00\ndescription: fixture\n---\nbody\n"
    )

    result = run_install(src, work)

    assert result.returncode == 0
    researcher = (work / ".claude" / "agents" / "lissom-researcher.md").read_text()
    planner = (work / ".claude" / "agents" / "lissom-planner.md").read_text()
    assert "2026-06-01T00:00:00" in researcher
    assert "2026-01-01T00:00:00" in planner   # old installed version preserved
    assert "Skipped 1" in result.stdout


def test_no_version_field_overwritten_silently(tmp_path):
    """T12: A versionless installed file is treated as 'version 0' and overwritten without a prompt."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")
    # Pre-place a file with no version field in the target
    (work / ".claude" / "agents").mkdir(parents=True)
    (work / ".claude" / "agents" / "lissom-researcher.md").write_text(
        "---\nname: lissom-researcher\ndescription: old, no version\n---\nbody\n"
    )

    result = run_install(src, work, env_extra={"LISSOM_TARGET": ".claude"})

    assert result.returncode == 0
    assert "newer than the source" not in result.stdout
    content = (work / ".claude" / "agents" / "lissom-researcher.md").read_text()
    assert "2026-01-01T00:00:00" in content


def test_model_config_accepted(tmp_path):
    """AC1: User accepts model prompt (LISSOM_YES=1); new agent files get default model fields and table is displayed."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    result = run_install(src, work, env_extra={"LISSOM_YES": "1"})

    assert result.returncode == 0
    researcher = (work / ".claude" / "agents" / "lissom-researcher.md").read_text()
    planner = (work / ".claude" / "agents" / "lissom-planner.md").read_text()
    implementer = (work / ".claude" / "agents" / "lissom-implementer.md").read_text()
    reviewer = (work / ".claude" / "agents" / "lissom-reviewer.md").read_text()

    assert "model: opus-4.6" in researcher
    assert "model: sonnet" in planner
    assert "model: sonnet" in implementer
    assert "model: sonnet" in reviewer

    assert "┬" in result.stdout                           # table top border (adaptive width)
    assert "│ Agent" in result.stdout
    assert "lissom-researcher" in result.stdout
    assert "opus-4.6" in result.stdout


def test_model_config_default_no_tty(tmp_path):
    """Edge case 1: no answer defaults to Y so model fields are added."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    result = run_install(src, work)  # no LISSOM_YES, no tty

    assert result.returncode == 0
    researcher = (work / ".claude" / "agents" / "lissom-researcher.md").read_text()
    assert "model: opus-4.6" in researcher


def test_existing_files_preserve_model(tmp_path):
    """AC3: Existing agent files with model fields preserve their values during upgrade."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()

    # Initial install with custom model values in destination
    make_src_tree(src, "2026-01-01T00:00:00")
    run_install(src, work, env_extra={"LISSOM_YES": "1"})

    # Overwrite installed researcher with a custom model value
    researcher_path = work / ".claude" / "agents" / "lissom-researcher.md"
    content = researcher_path.read_text()
    content = content.replace("model: opus-4.6", "model: my-custom-model")
    researcher_path.write_text(content)

    # Upgrade to newer version
    make_src_tree(src, "2026-06-01T00:00:00")
    result = run_install(src, work, env_extra={"LISSOM_YES": "1"})

    assert result.returncode == 0
    researcher = (work / ".claude" / "agents" / "lissom-researcher.md").read_text()
    assert "2026-06-01T00:00:00" in researcher   # version updated
    assert "my-custom-model" in researcher        # model preserved
    assert "my-custom-model" in result.stdout     # table shows preserved model


def test_mixed_existing_and_new_agents(tmp_path):
    """AC4: Some agents exist (preserve their model), new agents get default models."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    # Install only researcher manually with a custom model
    agents_dir = work / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "lissom-researcher.md").write_text(
        "---\nname: lissom-researcher\nversion: 2026-01-01T00:00:00\ndescription: fixture\ntools: read, write\nmodel: my-custom-model\n---\nbody\n"
    )

    result = run_install(src, work, env_extra={"LISSOM_YES": "1"})

    assert result.returncode == 0
    researcher = (work / ".claude" / "agents" / "lissom-researcher.md").read_text()
    planner = (work / ".claude" / "agents" / "lissom-planner.md").read_text()

    assert "my-custom-model" in researcher   # preserved
    assert "model: sonnet" in planner        # new file gets default


def test_malformed_yaml_fails_installation(tmp_path):
    """AC5: Existing agent with malformed YAML causes install to fail with clear error."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    # Initial install
    run_install(src, work, env_extra={"LISSOM_YES": "1"})

    # Corrupt researcher file (remove closing ---)
    researcher_path = work / ".claude" / "agents" / "lissom-researcher.md"
    make_malformed_agent(researcher_path, "lissom-researcher")

    # Attempt upgrade
    make_src_tree(src, "2026-06-01T00:00:00")
    result = run_install(src, work, env_extra={"LISSOM_YES": "1"})

    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "malformed" in combined.lower() or "invalid" in combined.lower()
    assert "lissom-researcher.md" in combined
    assert "fix" in combined.lower() or "remove" in combined.lower()


def test_customization_message_displayed(tmp_path):
    """AC6: After successful install with models, user sees customization message."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    result = run_install(src, work, env_extra={"LISSOM_YES": "1"})

    assert result.returncode == 0
    assert "The model field can be modified in the agent files at ./.claude/agents/" in result.stdout


def test_model_config_declined(tmp_path):
    """AC2: User declines model prompt (LISSOM_NO=1); agent files get no model fields."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    result = run_install(src, work, env_extra={"LISSOM_NO": "1"})

    assert result.returncode == 0
    researcher = (work / ".claude" / "agents" / "lissom-researcher.md").read_text()
    planner = (work / ".claude" / "agents" / "lissom-planner.md").read_text()

    assert "model:" not in researcher
    assert "model:" not in planner
    # Table should NOT be shown (no border with ┬ character)
    assert "┬" not in result.stdout
    # Customization message should NOT be shown
    assert "The model field can be modified" not in result.stdout


def test_preserve_absence_of_model_field(tmp_path):
    """Upgrade preserves absence of model field when existing file has none."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    # Install researcher without a model field
    agents_dir = work / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "lissom-researcher.md").write_text(
        "---\nname: lissom-researcher\nversion: 2026-01-01T00:00:00\ndescription: fixture\ntools: read, write\n---\nbody\n"
    )

    # Upgrade
    make_src_tree(src, "2026-06-01T00:00:00")
    result = run_install(src, work, env_extra={"LISSOM_YES": "1"})

    assert result.returncode == 0
    researcher = (work / ".claude" / "agents" / "lissom-researcher.md").read_text()
    assert "2026-06-01T00:00:00" in researcher   # version updated
    assert "model:" not in researcher             # model field still absent


# Opencode integration tests (Step 9)

def test_install_opencode_target(tmp_path):
    """OC1: Selecting .opencode/ target produces converted agent files with Opencode frontmatter."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    result = run_install(src, work, env_extra={"LISSOM_YES": "1", "LISSOM_TARGET": ".opencode"})

    assert result.returncode == 0
    # Verify Opencode directory exists and .claude doesn't
    assert (work / ".opencode").exists()
    assert not (work / ".claude").exists()
    
    # Verify agent files exist in .opencode
    assert (work / ".opencode" / "agents" / "lissom-researcher.md").is_file()
    assert (work / ".opencode" / "agents" / "lissom-planner.md").is_file()
    
    # Verify Opencode frontmatter: mode: subagent, temperature: 0.1, permission block
    researcher = (work / ".opencode" / "agents" / "lissom-researcher.md").read_text()
    assert "mode: subagent" in researcher
    assert "temperature: 0.1" in researcher
    assert "permission:" in researcher
    assert "read: allow" in researcher
    
    # Verify Claude Code format fields are removed/converted
    assert "tools:" not in researcher  # Claude Code tools line is removed


def test_install_opencode_with_model(tmp_path):
    """OC2: Opencode installation preserves models when creating new files with model support."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    # For Claude target with LISSOM_YES=1, models are added by default
    result = run_install(src, work, env_extra={"LISSOM_YES": "1", "LISSOM_TARGET": ".claude"})
    assert result.returncode == 0
    
    # Then upgrade to Opencode target - existing model fields should be preserved/converted
    # Create an Opencode version of the file with models
    result = run_install(src, work, env_extra={"LISSOM_YES": "1", "LISSOM_TARGET": ".opencode"})
    assert result.returncode == 0
    
    # Files should exist in .opencode
    researcher = (work / ".opencode" / "agents" / "lissom-researcher.md").read_text()
    assert "mode: subagent" in researcher


def test_opencode_reinstall_preserves_model(tmp_path):
    """OC2b: Reinstalling to opencode preserves existing model values and shows the model table."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    # Initial install to opencode
    result = run_install(src, work, env_extra={"LISSOM_YES": "1", "LISSOM_TARGET": ".opencode"})
    assert result.returncode == 0
    researcher = (work / ".opencode" / "agents" / "lissom-researcher.md").read_text()
    assert "model: opencode-go/deepseek-v4-pro" in researcher
    assert "┬" in result.stdout  # table shown

    # Overwrite with a custom model
    researcher_path = work / ".opencode" / "agents" / "lissom-researcher.md"
    content = researcher_path.read_text()
    content = content.replace("opencode-go/deepseek-v4-pro", "my-custom-model")
    researcher_path.write_text(content)

    # Reinstall (same version) — should preserve custom model
    result = run_install(src, work, env_extra={"LISSOM_TARGET": ".opencode"})

    assert result.returncode == 0
    researcher = (work / ".opencode" / "agents" / "lissom-researcher.md").read_text()
    assert "my-custom-model" in researcher       # custom model preserved
    assert "┬" in result.stdout                  # model table shown
    assert "my-custom-model" in result.stdout    # table shows preserved model


def test_install_opencode_without_model(tmp_path):
    """OC3: Opencode installation without model preference excludes model field."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    result = run_install(src, work, env_extra={"LISSOM_NO": "1", "LISSOM_TARGET": ".opencode"})

    assert result.returncode == 0
    researcher = (work / ".opencode" / "agents" / "lissom-researcher.md").read_text()
    
    # Verify model field is absent
    assert "model:" not in researcher
    # But other Opencode fields should still be present
    assert "mode: subagent" in researcher
    assert "temperature: 0.1" in researcher


def test_install_opencode_skill_frontmatter(tmp_path):
    """OC4: Skill files retain their frontmatter unchanged in Opencode target."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    result = run_install(src, work, env_extra={"LISSOM_YES": "1", "LISSOM_TARGET": ".opencode"})

    assert result.returncode == 0
    
    # Check skill frontmatter is preserved as-is
    skill = (work / ".opencode" / "skills" / "lissom-auto" / "SKILL.md").read_text()
    assert "name: lissom-auto" in skill
    assert "version: 2026-01-01T00:00:00" in skill
    # Skill frontmatter should NOT have Opencode-specific fields like mode/temperature
    assert "mode: subagent" not in skill
    assert "temperature:" not in skill


def run_install_from_scripts(src: Path, work: Path, env_extra=None):
    """Copy install.sh into src/scripts/ and run it, simulating `bash scripts/install.sh`."""
    scripts_dir = src / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(INSTALL_SH, scripts_dir / "install.sh")
    env = {**os.environ}
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        ["bash", str(scripts_dir / "install.sh")],
        cwd=str(work),
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
    )


def test_install_from_scripts_subdirectory(tmp_path):
    """SI1: Running install.sh from scripts/ subdirectory resolves paths correctly."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    result = run_install_from_scripts(src, work, env_extra={"LISSOM_YES": "1"})

    assert result.returncode == 0
    assert (work / ".claude" / "agents" / "lissom-researcher.md").is_file()
    assert (work / ".claude" / "skills" / "lissom-auto" / "SKILL.md").is_file()


def test_install_opencode_body_rewrite(tmp_path):
    """OC5: Tool names in agent body text are rewritten during Opencode conversion."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")
    
    # Create an agent with tool references in the body
    (src / "agents" / "lissom-custom.md").write_text(
        "---\nname: lissom-custom\nversion: 2026-01-01T00:00:00\ndescription: custom\ntools: Bash, Read, AskUserQuestion\n---\n"
        "Use Tool `Bash` and `Read` and `AskUserQuestion` for this task.\n"
    )

    result = run_install(src, work, env_extra={"LISSOM_YES": "1", "LISSOM_TARGET": ".opencode"})

    assert result.returncode == 0
    custom = (work / ".opencode" / "agents" / "lissom-custom.md").read_text()
    
    # Verify tool names are rewritten in body
    assert "`bash`" in custom
    assert "`read`" in custom
    assert "`question`" in custom
    # Verify old names are NOT present
    assert "`Bash`" not in custom
    assert "`Read`" not in custom
    assert "`AskUserQuestion`" not in custom


# Regression tests: ui.sh prompt functions must not leak prompt text to stdout
# when called via command substitution $(...).

def test_prompt_target_directory_stdout_clean(tmp_path):
    """T1 regression: prompt_target_directory outputs only the target name to stdout."""
    for target in (".claude", ".opencode", ".qwen", ".gemini"):
        result = subprocess.run(
            ["bash", "-c", f"""
                source scripts/lib/ui.sh
                LISSOM_TARGET={target} prompt_target_directory
            """],
            capture_output=True, text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0
        lines = result.stdout.strip().splitlines()
        assert len(lines) == 1, (
            f"Expected 1 line of stdout (the target name), got {len(lines)}: {lines}\n"
            f"stderr: {result.stderr}"
        )
        assert lines[0] == target, f"stdout should be '{target}', got: {lines[0]!r}"


def test_prompt_model_preference_stdout_clean(tmp_path):
    """Regression: prompt_model_preference outputs only 'true'/'false' to stdout."""
    # LISSOM_NO=1 path — outputs "false"
    result = subprocess.run(
        ["bash", "-c", "source scripts/lib/ui.sh && LISSOM_NO=1 prompt_model_preference"],
        capture_output=True, text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0
    lines = result.stdout.strip().splitlines()
    assert len(lines) == 1, (
        f"Expected 1 line of stdout ('false'), got {len(lines)}: {lines}\n"
        f"stderr: {result.stderr}"
    )
    assert lines[0] == "false", f"stdout should be 'false', got: {lines[0]!r}"


def test_install_target_directory_clean(tmp_path):
    """Install creates the correct target directory without prompt text leakage in path."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    # LISSOM_TARGET env overrides the interactive prompt entirely,
    # ensuring no prompt text gets captured in INSTALL_TARGET
    for target in (".claude", ".opencode", ".qwen", ".gemini"):
        result = run_install(src, work, env_extra={"LISSOM_YES": "1", "LISSOM_TARGET": target})

        assert result.returncode == 0, f"install.sh failed with {target}: {result.stderr}"
        assert (work / target).is_dir(), (
            f"Expected directory {target} to exist. "
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )


# Qwen install tests (Step 5)

def test_install_qwen_target(tmp_path):
    """QW1: Selecting .qwen/ target with LISSOM_YES=1 produces converted agent files with Qwen Code frontmatter."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    result = run_install(src, work, env_extra={"LISSOM_YES": "1", "LISSOM_TARGET": ".qwen"})

    assert result.returncode == 0
    assert (work / ".qwen").exists()
    assert not (work / ".claude").exists()

    assert (work / ".qwen" / "agents" / "lissom-researcher.md").is_file()
    assert (work / ".qwen" / "agents" / "lissom-planner.md").is_file()

    researcher = (work / ".qwen" / "agents" / "lissom-researcher.md").read_text()
    assert "model: qwen3.6-plus" in researcher
    assert "name: lissom-researcher" in researcher
    assert "description:" in researcher
    assert "tools:" in researcher
    assert "  - read_file" in researcher
    assert "  - write_file" in researcher
    assert "tools: Bash, Read" not in researcher  # old format removed


def test_install_qwen_with_model(tmp_path):
    """QW2: Qwen install with LISSOM_YES includes model fields."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    result = run_install(src, work, env_extra={"LISSOM_YES": "1", "LISSOM_TARGET": ".qwen"})

    assert result.returncode == 0
    researcher = (work / ".qwen" / "agents" / "lissom-researcher.md").read_text()
    assert "model: qwen3.6-plus" in researcher


def test_install_qwen_warns_about_claude(tmp_path):
    """QW3: Installing to .qwen/ when .claude/ has lissom files shows warning about .claude/."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    # Seed .claude with lissom files
    run_install(src, work, env_extra={"LISSOM_YES": "1", "LISSOM_TARGET": ".claude"})

    # Install to .qwen — should warn about .claude
    result = run_install(src, work, env_extra={"LISSOM_YES": "1", "LISSOM_TARGET": ".qwen"})

    assert result.returncode == 0
    assert "Found existing installation in .claude/" in result.stdout
    assert (work / ".qwen" / "agents" / "lissom-researcher.md").is_file()


def test_install_qwen_warns_about_multiple_alts(tmp_path):
    """QW4: Installing to .qwen/ when both .claude/ and .opencode/ have lissom files warns about both."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    # Seed .claude
    run_install(src, work, env_extra={"LISSOM_YES": "1", "LISSOM_TARGET": ".claude"})
    # Seed .opencode
    run_install(src, work, env_extra={"LISSOM_YES": "1", "LISSOM_TARGET": ".opencode"})

    # Install to .qwen — should warn about both
    result = run_install(src, work, env_extra={"LISSOM_YES": "1", "LISSOM_TARGET": ".qwen"})

    assert result.returncode == 0
    assert "Found existing installation in .claude/" in result.stdout
    assert "Found existing installation in .opencode/" in result.stdout


def test_reinstall_qwen_suppresses_warning(tmp_path):
    """QW5: Reinstalling to .qwen/ (already has lissom files) does NOT show warning."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    # First install to .qwen
    run_install(src, work, env_extra={"LISSOM_YES": "1", "LISSOM_TARGET": ".qwen"})

    # Seed .claude as well
    make_src_tree(src, "2026-01-01T00:00:00")
    run_install(src, work, env_extra={"LISSOM_YES": "1", "LISSOM_TARGET": ".claude"})

    # Reinstall to .qwen (already populated) — should NOT warn even though .claude has files
    result = run_install(src, work, env_extra={"LISSOM_YES": "1", "LISSOM_TARGET": ".qwen"})

    assert result.returncode == 0
    assert "Found existing installation in" not in result.stdout


# Qwen content integration tests (Step 9)

def test_install_qwen_without_model(tmp_path):
    """QW2: Qwen Code installation without model preference excludes model field."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    result = run_install(src, work, env_extra={"LISSOM_NO": "1", "LISSOM_TARGET": ".qwen"})

    assert result.returncode == 0
    researcher = (work / ".qwen" / "agents" / "lissom-researcher.md").read_text()
    assert "model:" not in researcher
    assert "tools:" in researcher


def test_install_qwen_skill_frontmatter(tmp_path):
    """QW3: Skill files have Qwen Code frontmatter (name + description only)."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    result = run_install(src, work, env_extra={"LISSOM_YES": "1", "LISSOM_TARGET": ".qwen"})

    assert result.returncode == 0
    skill = (work / ".qwen" / "skills" / "lissom-auto" / "SKILL.md").read_text()
    assert "name: lissom-auto" in skill
    assert "description: fixture" in skill
    # version and argument-hint must be stripped
    assert "version:" not in skill
    assert "argument-hint:" not in skill
    assert "mode:" not in skill      # no Opencode-specific fields


def test_install_qwen_skill_body_rewrite(tmp_path):
    """QW3b: Tool names in skill body text are rewritten during Qwen Code install."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    # Overwrite lissom-auto skill with body containing tool references
    (src / "skills" / "lissom-auto" / "SKILL.md").write_text(
        "---\nname: lissom-auto\nversion: 2026-01-01T00:00:00\ndescription: fixture\n"
        "argument-hint: <task_dir>\n---\n"
        "Use tool `Bash` to execute commands. Use `Read` to inspect files.\n"
        "Also try `Grep` for searching and `AskUserQuestion` for user input.\n"
    )

    result = run_install(src, work, env_extra={"LISSOM_YES": "1", "LISSOM_TARGET": ".qwen"})

    assert result.returncode == 0
    skill = (work / ".qwen" / "skills" / "lissom-auto" / "SKILL.md").read_text()

    # Frontmatter simplified (existing requirement)
    assert "name: lissom-auto" in skill
    assert "description: fixture" in skill
    assert "version:" not in skill
    assert "argument-hint:" not in skill

    # Body tool names rewritten
    assert "`run_shell_command`" in skill
    assert "`read_file`" in skill
    assert "`grep_search`" in skill
    assert "`question`" in skill

    # Original tool names gone from body
    assert "`Bash`" not in skill
    assert "`Read`" not in skill
    assert "`Grep`" not in skill
    assert "`AskUserQuestion`" not in skill


def test_install_qwen_body_rewrite(tmp_path):
    """QW4: Tool names in agent body text are rewritten during Qwen Code conversion."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    # Create a custom agent with tool references in the body
    (src / "agents" / "lissom-custom.md").write_text(
        "---\nname: lissom-custom\nversion: 2026-01-01T00:00:00\ndescription: custom\ntools: Bash, Read, AskUserQuestion\n---\n"
        "Use Tool `Bash` and `Read` and `AskUserQuestion` for this task.\n"
    )

    result = run_install(src, work, env_extra={"LISSOM_YES": "1", "LISSOM_TARGET": ".qwen"})

    assert result.returncode == 0
    custom = (work / ".qwen" / "agents" / "lissom-custom.md").read_text()

    # Body tool names rewritten
    assert "`run_shell_command`" in custom
    assert "`read_file`" in custom
    assert "`question`" in custom
    # Old names gone
    assert "`Bash`" not in custom
    assert "`Read`" not in custom
    assert "`AskUserQuestion`" not in custom


def test_install_qwen_implementer_model(tmp_path):
    """QW5: lissom-implementer gets qwen3-coder-plus model."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    result = run_install(src, work, env_extra={"LISSOM_YES": "1", "LISSOM_TARGET": ".qwen"})

    assert result.returncode == 0
    impl = (work / ".qwen" / "agents" / "lissom-implementer.md").read_text()
    assert "model: qwen3-coder-plus" in impl


def test_install_qwen_model_table(tmp_path):
    """QW6: After Qwen install with models, the model table is displayed."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    result = run_install(src, work, env_extra={"LISSOM_YES": "1", "LISSOM_TARGET": ".qwen"})

    assert result.returncode == 0
    assert "┬" in result.stdout  # table border present
    assert "lissom-researcher" in result.stdout
    assert "qwen3.6-plus" in result.stdout


# Gemini install integration tests (Step 9)

def test_install_gemini_target(tmp_path):
    """GM1: Selecting .gemini/ target produces converted agent files with Gemini CLI frontmatter."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    # Overwrite researcher with broader tools to verify Gemini-specific mappings
    (src / "agents" / "lissom-researcher.md").write_text(
        "---\nname: lissom-researcher\nversion: 2026-01-01T00:00:00\ndescription: fixture\n"
        "tools: Bash, Read, Write, Edit, Glob, Grep, WebFetch, WebSearch, AskUserQuestion\n---\nbody\n"
    )

    result = run_install(src, work, env_extra={"LISSOM_YES": "1", "LISSOM_TARGET": ".gemini"})

    assert result.returncode == 0
    assert (work / ".gemini").exists()
    assert not (work / ".claude").exists()

    assert (work / ".gemini" / "agents" / "lissom-researcher.md").is_file()
    assert (work / ".gemini" / "agents" / "lissom-planner.md").is_file()

    researcher = (work / ".gemini" / "agents" / "lissom-researcher.md").read_text()
    assert "temperature: 0.1" in researcher
    assert "tools:" in researcher
    assert "tools: Bash, Read" not in researcher  # old inline format removed
    assert "  - replace" in researcher
    assert "  - google_web_search" in researcher
    assert "  - ask_user" in researcher


def test_install_gemini_with_model(tmp_path):
    """GM2: Gemini install with LISSOM_YES includes model fields."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    result = run_install(src, work, env_extra={"LISSOM_YES": "1", "LISSOM_TARGET": ".gemini"})

    assert result.returncode == 0
    researcher = (work / ".gemini" / "agents" / "lissom-researcher.md").read_text()
    assert "model: gemini-3-pro-preview" in researcher
    impl = (work / ".gemini" / "agents" / "lissom-implementer.md").read_text()
    assert "model: gemini-3-flash-preview" in impl


def test_install_gemini_without_model(tmp_path):
    """GM3: Gemini install without model preference excludes model field."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    result = run_install(src, work, env_extra={"LISSOM_NO": "1", "LISSOM_TARGET": ".gemini"})

    assert result.returncode == 0
    researcher = (work / ".gemini" / "agents" / "lissom-researcher.md").read_text()
    assert "model:" not in researcher
    assert "tools:" in researcher
    assert "temperature: 0.1" in researcher


def test_install_gemini_temperature_field(tmp_path):
    """GM4: Verify temperature: 0.1 present in all converted agents but not in skills."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    result = run_install(src, work, env_extra={"LISSOM_YES": "1", "LISSOM_TARGET": ".gemini"})

    assert result.returncode == 0

    for agent in AGENTS:
        content = (work / ".gemini" / "agents" / f"{agent}.md").read_text()
        assert "temperature: 0.1" in content, f"{agent} missing temperature: 0.1"

    # Skills should NOT have temperature
    for skill in SKILLS:
        content = (work / ".gemini" / "skills" / skill / "SKILL.md").read_text()
        assert "temperature:" not in content, f"{skill} skill should not have temperature"


def test_install_gemini_ask_user_included(tmp_path):
    """GM5: Verify ask_user in tools list (unlike Qwen where it was removed)."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    # Create custom agent with AskUserQuestion
    (src / "agents" / "lissom-custom.md").write_text(
        "---\nname: lissom-custom\nversion: 2026-01-01T00:00:00\ndescription: custom\n"
        "tools: Bash, Read, AskUserQuestion\n---\n"
        "Ask user with `AskUserQuestion` when needed.\n"
    )

    result = run_install(src, work, env_extra={"LISSOM_YES": "1", "LISSOM_TARGET": ".gemini"})

    assert result.returncode == 0
    custom = (work / ".gemini" / "agents" / "lissom-custom.md").read_text()
    assert "  - ask_user" in custom       # in tools list
    assert "`ask_user`" in custom          # in body text


def test_install_gemini_skill_frontmatter(tmp_path):
    """GM6: Skill files have Gemini CLI frontmatter (name + description only)."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    result = run_install(src, work, env_extra={"LISSOM_YES": "1", "LISSOM_TARGET": ".gemini"})

    assert result.returncode == 0
    skill = (work / ".gemini" / "skills" / "lissom-auto" / "SKILL.md").read_text()
    assert "name: lissom-auto" in skill
    assert "description: fixture" in skill
    assert "version:" not in skill
    assert "argument-hint:" not in skill
    assert "temperature:" not in skill


def test_install_gemini_body_rewrite(tmp_path):
    """GM7: Tool names in agent body text are rewritten during Gemini conversion."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    # Create a custom agent with tool references in the body
    (src / "agents" / "lissom-custom.md").write_text(
        "---\nname: lissom-custom\nversion: 2026-01-01T00:00:00\ndescription: custom\n"
        "tools: Bash, Read, Edit, WebSearch, AskUserQuestion\n---\n"
        "Use Tool `Bash` and `Edit` and `WebSearch` and `AskUserQuestion` for this task.\n"
        "Also use `Agent` for delegation.\n"
    )

    result = run_install(src, work, env_extra={"LISSOM_YES": "1", "LISSOM_TARGET": ".gemini"})

    assert result.returncode == 0
    custom = (work / ".gemini" / "agents" / "lissom-custom.md").read_text()

    # Tool names rewritten
    assert "`run_shell_command`" in custom
    assert "`replace`" in custom
    assert "`google_web_search`" in custom
    assert "`ask_user`" in custom

    # Old names gone
    assert "`Bash`" not in custom
    assert "`Edit`" not in custom
    assert "`WebSearch`" not in custom
    assert "`AskUserQuestion`" not in custom

    # Unmapped tools pass through
    assert "`Agent`" in custom


def test_install_gemini_warns_about_claude(tmp_path):
    """GM8: Installing to .gemini/ when .claude/ has lissom files shows warning."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    # Seed .claude with lissom files
    run_install(src, work, env_extra={"LISSOM_YES": "1", "LISSOM_TARGET": ".claude"})

    # Install to .gemini — should warn about .claude
    result = run_install(src, work, env_extra={"LISSOM_YES": "1", "LISSOM_TARGET": ".gemini"})

    assert result.returncode == 0
    assert "Found existing installation in .claude/" in result.stdout
    assert (work / ".gemini" / "agents" / "lissom-researcher.md").is_file()


def test_install_gemini_model_table(tmp_path):
    """GM9: After Gemini install with models, the model table is displayed."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    result = run_install(src, work, env_extra={"LISSOM_YES": "1", "LISSOM_TARGET": ".gemini"})

    assert result.returncode == 0
    assert "┬" in result.stdout  # table border present
    assert "lissom-researcher" in result.stdout
    assert "gemini-3-pro-preview" in result.stdout
