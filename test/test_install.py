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
    assert "model: haiku" in implementer
    assert "model: sonnet" in reviewer

    assert "┌─────────────────────────────┬───────────┐" in result.stdout
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
    assert "The model field can be modified in the agent files at .claude/agents/" in result.stdout


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
    # Table should NOT be shown
    assert "┌─────────────────────────────┬───────────┐" not in result.stdout
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
    for target in (".claude", ".opencode"):
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
    for target in (".claude", ".opencode"):
        result = run_install(src, work, env_extra={"LISSOM_YES": "1", "LISSOM_TARGET": target})

        assert result.returncode == 0, f"install.sh failed with {target}: {result.stderr}"
        assert (work / target).is_dir(), (
            f"Expected directory {target} to exist. "
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

