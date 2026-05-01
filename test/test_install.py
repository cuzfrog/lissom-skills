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
INSTALL_SH = REPO_ROOT / "install.sh"


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
    assert (work / ".claude" / "agents" / "task-researcher.md").is_file()
    assert (work / ".claude" / "skills" / "task-auto" / "SKILL.md").is_file()
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
    assert (work / ".claude" / "agents" / "task-researcher.md").is_file()


def test_upgrade(tmp_path):
    """T3: Source newer than installed overwrites silently without a prompt."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2025-01-01T00:00:00")
    run_install(src, work, env_extra={"LISSOM_YES": "1"})
    make_src_tree(src, "2026-06-01T00:00:00")

    result = run_install(src, work)

    assert result.returncode == 0
    assert "newer than the source" not in result.stdout
    content = (work / ".claude" / "agents" / "task-researcher.md").read_text()
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
    content = (work / ".claude" / "agents" / "task-researcher.md").read_text()
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
    content = (work / ".claude" / "agents" / "task-researcher.md").read_text()
    assert "2026-06-01T00:00:00" in content


def test_mixed_versions(tmp_path):
    """T6: Newer-source files upgrade silently; older-source file is skipped (one file skipped)."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")
    run_install(src, work, env_extra={"LISSOM_YES": "1"})

    # task-researcher source becomes newer → should upgrade silently
    (src / "agents" / "task-researcher.md").write_text(
        "---\nname: task-researcher\nversion: 2026-06-01T00:00:00\ndescription: fixture\n---\nbody\n"
    )
    # task-planner source becomes older → should be skipped (prompt declined via no tty)
    (src / "agents" / "task-planner.md").write_text(
        "---\nname: task-planner\nversion: 2025-01-01T00:00:00\ndescription: fixture\n---\nbody\n"
    )

    result = run_install(src, work)

    assert result.returncode == 0
    researcher = (work / ".claude" / "agents" / "task-researcher.md").read_text()
    planner = (work / ".claude" / "agents" / "task-planner.md").read_text()
    assert "2026-06-01T00:00:00" in researcher
    assert "2026-01-01T00:00:00" in planner   # old installed version preserved
    assert "Skipped 1" in result.stdout


def test_user_mode_target(tmp_path):
    """T11: --user installs to $HOME/.claude and does not create Specs.md."""
    src = tmp_path / "src"
    work = tmp_path / "work"
    fakehome = tmp_path / "home"
    src.mkdir(); work.mkdir(); fakehome.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    result = run_install(src, work, args=("--user",), env_extra={"HOME": str(fakehome), "LISSOM_YES": "1"})

    assert result.returncode == 0
    assert (fakehome / ".claude" / "agents" / "task-researcher.md").is_file()
    assert not (work / ".lissom" / "tasks" / "T1" / "Specs.md").exists()


def test_no_version_field_overwritten_silently(tmp_path):
    """T12: A versionless installed file is treated as 'version 0' and overwritten without a prompt."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")
    # Pre-place a file with no version field in the target
    (work / ".claude" / "agents").mkdir(parents=True)
    (work / ".claude" / "agents" / "task-researcher.md").write_text(
        "---\nname: task-researcher\ndescription: old, no version\n---\nbody\n"
    )

    result = run_install(src, work)

    assert result.returncode == 0
    assert "newer than the source" not in result.stdout
    content = (work / ".claude" / "agents" / "task-researcher.md").read_text()
    assert "2026-01-01T00:00:00" in content


def test_model_config_accepted(tmp_path):
    """AC1: User accepts model prompt (LISSOM_YES=1); new agent files get default model fields and table is displayed."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    result = run_install(src, work, env_extra={"LISSOM_YES": "1"})

    assert result.returncode == 0
    researcher = (work / ".claude" / "agents" / "task-researcher.md").read_text()
    planner = (work / ".claude" / "agents" / "task-planner.md").read_text()
    implementer = (work / ".claude" / "agents" / "task-implementer.md").read_text()
    reviewer = (work / ".claude" / "agents" / "task-reviewer.md").read_text()

    assert "model: opus-4.6" in researcher
    assert "model: sonnet" in planner
    assert "model: haiku" in implementer
    assert "model: sonnet" in reviewer

    assert "┌─────────────────────────────┬───────────┐" in result.stdout
    assert "│ Agent" in result.stdout
    assert "task-researcher" in result.stdout
    assert "opus-4.6" in result.stdout


def test_model_config_default_no_tty(tmp_path):
    """Edge case 1: no answer defaults to Y so model fields are added."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    result = run_install(src, work)  # no LISSOM_YES, no tty

    assert result.returncode == 0
    researcher = (work / ".claude" / "agents" / "task-researcher.md").read_text()
    assert "model: opus-4.6" in researcher


def test_existing_files_preserve_model(tmp_path):
    """AC3: Existing agent files with model fields preserve their values during upgrade."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()

    # Initial install with custom model values in destination
    make_src_tree(src, "2026-01-01T00:00:00")
    run_install(src, work, env_extra={"LISSOM_YES": "1"})

    # Overwrite installed researcher with a custom model value
    researcher_path = work / ".claude" / "agents" / "task-researcher.md"
    content = researcher_path.read_text()
    content = content.replace("model: opus-4.6", "model: my-custom-model")
    researcher_path.write_text(content)

    # Upgrade to newer version
    make_src_tree(src, "2026-06-01T00:00:00")
    result = run_install(src, work, env_extra={"LISSOM_YES": "1"})

    assert result.returncode == 0
    researcher = (work / ".claude" / "agents" / "task-researcher.md").read_text()
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
    (agents_dir / "task-researcher.md").write_text(
        "---\nname: task-researcher\nversion: 2026-01-01T00:00:00\ndescription: fixture\ntools: read, write\nmodel: my-custom-model\n---\nbody\n"
    )

    result = run_install(src, work, env_extra={"LISSOM_YES": "1"})

    assert result.returncode == 0
    researcher = (work / ".claude" / "agents" / "task-researcher.md").read_text()
    planner = (work / ".claude" / "agents" / "task-planner.md").read_text()

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
    researcher_path = work / ".claude" / "agents" / "task-researcher.md"
    make_malformed_agent(researcher_path, "task-researcher")

    # Attempt upgrade
    make_src_tree(src, "2026-06-01T00:00:00")
    result = run_install(src, work, env_extra={"LISSOM_YES": "1"})

    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "malformed" in combined.lower() or "invalid" in combined.lower()
    assert "task-researcher.md" in combined
    assert "fix" in combined.lower() or "remove" in combined.lower()


def test_customization_message_displayed(tmp_path):
    """AC6: After successful install with models, user sees customization message."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    result = run_install(src, work, env_extra={"LISSOM_YES": "1"})

    assert result.returncode == 0
    assert "The model field can be modified in the agent md files at .claude/agents/" in result.stdout


def test_model_config_declined(tmp_path):
    """AC2: User declines model prompt (LISSOM_NO=1); agent files get no model fields."""
    src, work = tmp_path / "src", tmp_path / "work"
    src.mkdir(); work.mkdir()
    make_src_tree(src, "2026-01-01T00:00:00")

    result = run_install(src, work, env_extra={"LISSOM_NO": "1"})

    assert result.returncode == 0
    researcher = (work / ".claude" / "agents" / "task-researcher.md").read_text()
    planner = (work / ".claude" / "agents" / "task-planner.md").read_text()

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
    (agents_dir / "task-researcher.md").write_text(
        "---\nname: task-researcher\nversion: 2026-01-01T00:00:00\ndescription: fixture\ntools: read, write\n---\nbody\n"
    )

    # Upgrade
    make_src_tree(src, "2026-06-01T00:00:00")
    result = run_install(src, work, env_extra={"LISSOM_YES": "1"})

    assert result.returncode == 0
    researcher = (work / ".claude" / "agents" / "task-researcher.md").read_text()
    assert "2026-06-01T00:00:00" in researcher   # version updated
    assert "model:" not in researcher             # model field still absent



