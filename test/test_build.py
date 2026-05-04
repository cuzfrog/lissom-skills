"""
Tests for the Python build script and converter modules.

Covers unit tests for each converter (opencode, qwen, gemini),
Claude model injection, and build integration tests.
"""

import os
import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest

from scripts.lib.constants import AGENTS, SKILLS
from scripts.lib.frontmatter import inject_field, parse_frontmatter
from scripts.lib.opencode import convert_agent as opencode_convert_agent
from scripts.lib.opencode import convert_skill as opencode_convert_skill
from scripts.lib.qwen import convert_agent as qwen_convert_agent
from scripts.lib.qwen import convert_skill as qwen_convert_skill
from scripts.lib.gemini import convert_agent as gemini_convert_agent
from scripts.lib.gemini import convert_skill as gemini_convert_skill

REPO_ROOT = Path(__file__).resolve().parent.parent


# ── Helpers ──────────────────────────────────────────────────────────

def make_build_fixture(root: Path) -> None:
    """Create a minimal project tree for build testing."""
    agents_dir = root / "agents"
    agents_dir.mkdir(parents=True)
    for agent in AGENTS:
        (agents_dir / f"{agent}.md").write_text(
            f"---\nname: {agent}\ndescription: fixture\ntools: Bash, Read, Write, AskUserQuestion\n---\nBody for {agent} using `Bash` and `Read`.\n"
        )

    skills_dir = root / "skills"
    for skill in SKILLS:
        (skills_dir / skill).mkdir(parents=True)
        (skills_dir / skill / "SKILL.md").write_text(
            f"---\nname: {skill}\ndescription: fixture\n---\nBody for {skill} using `Grep`.\n"
        )

    (root / "templates").mkdir(parents=True)
    (root / "templates" / "Specs.md").write_text("# Sample Specs\n")

    # Add optional preferences file
    auto_dir = skills_dir / "lissom-auto"
    auto_dir.mkdir(parents=True, exist_ok=True)
    (auto_dir / "user_preference_questions.json").write_text('{"questions": []}\n')

    # Copy build scripts
    scripts_dest = root / "scripts" / "lib"
    scripts_dest.mkdir(parents=True, exist_ok=True)
    for py_file in (REPO_ROOT / "scripts" / "lib").glob("*.py"):
        shutil.copy2(py_file, scripts_dest / py_file.name)
    shutil.copy2(REPO_ROOT / "scripts" / "build.py", root / "scripts" / "build.py")
    shutil.copy2(REPO_ROOT / "scripts" / "prebuild.py", root / "scripts" / "prebuild.py")


# ── OpenCode Converter Tests ─────────────────────────────────────────

class TestOpenCodeConverter:
    def test_convert_agent_basic(self):
        """Agent with name, description, tools produces correct Opencode frontmatter."""
        content = "---\nname: test-agent\ndescription: A test agent\ntools: Bash, Read\n---\nUse `Bash` for commands.\n"
        result = opencode_convert_agent(content, "lissom-researcher")
        assert "mode: subagent" in result
        assert "temperature: 0.1" in result
        assert "permission:" in result
        assert "  bash: allow" in result
        assert "  read: allow" in result
        assert "model: opencode-go/deepseek-v4-pro" in result
        assert "`bash`" in result
        assert "`Bash`" not in result

    def test_convert_skill(self):
        """Skill frontmatter preserved, body tool names rewritten."""
        content = "---\nname: lissom-auto\ndescription: fixture\n---\nUse `Grep` to search.\n"
        result = opencode_convert_skill(content, "lissom-auto")
        assert "name: lissom-auto" in result
        assert "description: fixture" in result
        assert "mode: subagent" not in result
        assert "`grep`" in result

    def test_convert_agent_with_ask_user(self):
        """AskUserQuestion in tools → question permission."""
        content = "---\nname: test-agent\ndescription: test\ntools: AskUserQuestion\n---\nUse `AskUserQuestion`.\n"
        result = opencode_convert_agent(content, "lissom-reviewer")
        assert "  question: allow" in result
        assert "`question`" in result

    def test_convert_agent_model_for_implementer(self):
        """lissom-implementer gets opencode-go/deepseek-v4-flash."""
        content = "---\nname: lissom-implementer\ndescription: impl\ntools: Bash\n---\nbody\n"
        result = opencode_convert_agent(content, "lissom-implementer")
        assert "model: opencode-go/deepseek-v4-flash" in result


# ── Qwen Converter Tests ─────────────────────────────────────────────

class TestQwenConverter:
    def test_convert_agent(self):
        """Agent produces Qwen frontmatter with tools YAML list, excluding AskUserQuestion."""
        content = "---\nname: test-agent\ndescription: test\ntools: Bash, Read, AskUserQuestion\n---\nUse `Bash` and `AskUserQuestion`.\n"
        result = qwen_convert_agent(content, "lissom-researcher")
        assert "name: test-agent" in result
        assert "model: qwen3.6-plus" in result
        assert "  - run_shell_command" in result
        assert "  - read_file" in result
        assert "  - question" not in result.split("---")[0]  # not in frontmatter
        assert "`question`" in result  # but present in body
        assert "`Bash`" not in result

    def test_convert_skill(self):
        """Skill strips extra frontmatter fields, rewrites body tools."""
        content = "---\nname: lissom-auto\ndescription: fixture\nversion: 1.0\nargument-hint: <task>\n---\nUse `Grep` to search.\n"
        result = qwen_convert_skill(content, "lissom-auto")
        assert "name: lissom-auto" in result
        assert "description: fixture" in result
        assert "version:" not in result
        assert "argument-hint:" not in result
        assert "`grep_search`" in result

    def test_agent_implementer_model(self):
        """lissom-implementer gets qwen3-coder-plus model."""
        content = "---\nname: lissom-implementer\ndescription: impl\ntools: Bash\n---\nbody\n"
        result = qwen_convert_agent(content, "lissom-implementer")
        assert "model: qwen3-coder-plus" in result


# ── Gemini Converter Tests ───────────────────────────────────────────

class TestGeminiConverter:
    def test_convert_agent(self):
        """Agent produces Gemini frontmatter with temperature, including ask_user."""
        content = "---\nname: test-agent\ndescription: test\ntools: Bash, Edit, WebSearch, AskUserQuestion\n---\nUse `Bash` and `AskUserQuestion`.\n"
        result = gemini_convert_agent(content, "lissom-researcher")
        assert "temperature: 0.1" in result
        assert "model: gemini-3-pro-preview" in result
        assert "  - run_shell_command" in result
        assert "  - replace" in result
        assert "  - google_web_search" in result
        assert "  - ask_user" in result
        assert "`run_shell_command`" in result
        assert "`ask_user`" in result

    def test_convert_skill(self):
        """Skill strips extra fields, no temperature/model."""
        content = "---\nname: lissom-auto\ndescription: fixture\nversion: 1.0\n---\nUse `Grep` to search.\n"
        result = gemini_convert_skill(content, "lissom-auto")
        assert "name: lissom-auto" in result
        assert "description: fixture" in result
        assert "version:" not in result
        assert "temperature:" not in result
        assert "model:" not in result
        assert "`grep_search`" in result

    def test_temperature_present(self):
        """temperature: 0.1 present in agent but not skill."""
        agent_content = "---\nname: test\ndescription: test\ntools: Bash\n---\nbody\n"
        skill_content = "---\nname: test\ndescription: test\n---\nbody\n"
        agent_result = gemini_convert_agent(agent_content, "lissom-researcher")
        skill_result = gemini_convert_skill(skill_content, "lissom-test")
        assert "temperature: 0.1" in agent_result
        assert "temperature:" not in skill_result


# ── Claude Model Injection Tests ─────────────────────────────────────

class TestClaudeModelInjection:
    def test_model_injected_after_tools(self):
        """model: field added after tools: line."""
        content = "---\nname: test\ndescription: test\ntools: Bash, Read\n---\nbody\n"
        result = inject_field(content, "model", "sonnet", after_field="tools")
        assert "model: sonnet" in result
        # Check ordering: model comes after tools
        lines = result.splitlines()
        tools_idx = next(i for i, l in enumerate(lines) if l.startswith("tools:"))
        model_idx = next(i for i, l in enumerate(lines) if l.startswith("model:"))
        assert model_idx == tools_idx + 1

    def test_no_tools_field(self):
        """model: added before closing --- when no tools: field."""
        content = "---\nname: test\ndescription: test\n---\nbody\n"
        result = inject_field(content, "model", "sonnet")
        assert "model: sonnet" in result

    def test_replace_existing_model(self):
        """Existing model field is replaced."""
        content = "---\nname: test\nmodel: old\n---\nbody\n"
        result = inject_field(content, "model", "new")
        assert "model: new" in result
        assert "model: old" not in result

    def test_inject_without_frontmatter(self):
        """No frontmatter returns content unchanged."""
        content = "just text"
        result = inject_field(content, "model", "sonnet")
        assert result == content


# ── Frontmatter Parser Tests ─────────────────────────────────────────

class TestFrontmatterParser:
    def test_malformed_missing_opening(self):
        """Missing opening --- raises ValueError."""
        from scripts.lib.frontmatter import parse_frontmatter
        with pytest.raises(ValueError, match="opening"):
            parse_frontmatter("no frontmatter here")

    def test_malformed_missing_closing(self):
        """Missing closing --- raises ValueError."""
        from scripts.lib.frontmatter import parse_frontmatter
        with pytest.raises(ValueError, match="closing"):
            parse_frontmatter("---\nname: test\nno closing\n")

    def test_parse_real_file(self):
        """Parse a real agent file successfully."""
        content = (REPO_ROOT / "agents" / "lissom-researcher.md").read_text()
        fields, body = parse_frontmatter(content)
        assert "name" in fields
        assert "description" in fields
        assert "tools" in fields
        assert body.strip()


# ── Build Integration Tests ──────────────────────────────────────────

class TestBuildScript:
    def test_build_creates_all_four_zips(self, tmp_path):
        """Running build.py produces 4 zip files."""
        make_build_fixture(tmp_path)
        result = subprocess.run(
            ["python3", str(tmp_path / "scripts" / "build.py"), "--root", str(tmp_path)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"

        dist_dir = tmp_path / "dist"
        assert dist_dir.exists()
        zips = sorted(dist_dir.glob("*.zip"))
        assert len(zips) == 4
        assert all(z.name.startswith("lissom-skills-") for z in zips)

    def test_claude_zip_contents(self, tmp_path):
        """Claude zip has correct structure and model injection."""
        make_build_fixture(tmp_path)
        subprocess.run(
            ["python3", str(tmp_path / "scripts" / "build.py"), "--root", str(tmp_path)],
            check=True, capture_output=True,
        )

        with zipfile.ZipFile(tmp_path / "dist" / "lissom-skills-claude.zip") as zf:
            names = zf.namelist()
            assert ".claude/agents/lissom-researcher.md" in names
            assert ".claude/skills/lissom-auto/SKILL.md" in names
            assert ".claude/templates/Specs.md" in names

            content = zf.read(".claude/agents/lissom-researcher.md").decode()
            assert "model: opus-4.6" in content

    def test_opencode_zip_contents(self, tmp_path):
        """Opencode zip has converted content."""
        make_build_fixture(tmp_path)
        subprocess.run(
            ["python3", str(tmp_path / "scripts" / "build.py"), "--root", str(tmp_path)],
            check=True, capture_output=True,
        )

        with zipfile.ZipFile(tmp_path / "dist" / "lissom-skills-opencode.zip") as zf:
            content = zf.read(".opencode/agents/lissom-researcher.md").decode()
            assert "mode: subagent" in content
            assert "permission:" in content
            assert "model: opencode-go/deepseek-v4-pro" in content

    def test_qwen_zip_contents(self, tmp_path):
        """Qwen zip has converted content."""
        make_build_fixture(tmp_path)
        subprocess.run(
            ["python3", str(tmp_path / "scripts" / "build.py"), "--root", str(tmp_path)],
            check=True, capture_output=True,
        )

        with zipfile.ZipFile(tmp_path / "dist" / "lissom-skills-qwen.zip") as zf:
            content = zf.read(".qwen/agents/lissom-implementer.md").decode()
            assert "model: qwen3-coder-plus" in content
            assert "  - run_shell_command" in content

    def test_gemini_zip_contents(self, tmp_path):
        """Gemini zip has converted content."""
        make_build_fixture(tmp_path)
        subprocess.run(
            ["python3", str(tmp_path / "scripts" / "build.py"), "--root", str(tmp_path)],
            check=True, capture_output=True,
        )

        with zipfile.ZipFile(tmp_path / "dist" / "lissom-skills-gemini.zip") as zf:
            content = zf.read(".gemini/agents/lissom-researcher.md").decode()
            assert "temperature: 0.1" in content
            assert "model: gemini-3-pro-preview" in content
            assert "  - ask_user" in content

    def test_templates_and_preferences_copied(self, tmp_path):
        """templates/Specs.md and user_preference_questions.json are in each zip."""
        make_build_fixture(tmp_path)
        subprocess.run(
            ["python3", str(tmp_path / "scripts" / "build.py"), "--root", str(tmp_path)],
            check=True, capture_output=True,
        )

        for shortname in ("claude", "opencode", "qwen", "gemini"):
            expected_target = f".{shortname}"
            if shortname == "claude":
                expected_target = ".claude"
            elif shortname == "opencode":
                expected_target = ".opencode"

            zip_path = tmp_path / "dist" / f"lissom-skills-{shortname}.zip"
            with zipfile.ZipFile(zip_path) as zf:
                names = zf.namelist()
                assert f"{expected_target}/templates/Specs.md" in names, f"missing Specs.md in {shortname}"
                assert f"{expected_target}/skills/lissom-auto/user_preference_questions.json" in names, f"missing prefs in {shortname}"

    def test_build_idempotent(self, tmp_path):
        """Running build.py twice succeeds (overwrites zips)."""
        make_build_fixture(tmp_path)
        subprocess.run(
            ["python3", str(tmp_path / "scripts" / "build.py"), "--root", str(tmp_path)],
            check=True, capture_output=True,
        )

        # Run again
        result = subprocess.run(
            ["python3", str(tmp_path / "scripts" / "build.py"), "--root", str(tmp_path)],
            capture_output=True,
        )
        assert result.returncode == 0

    def test_missing_preferences_does_not_crash(self, tmp_path):
        """Missing optional user_preference_questions.json does not crash build."""
        make_build_fixture(tmp_path)
        # Remove the preferences file
        prefs = tmp_path / "skills" / "lissom-auto" / "user_preference_questions.json"
        prefs.unlink()

        result = subprocess.run(
            ["python3", str(tmp_path / "scripts" / "build.py"), "--root", str(tmp_path)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "warn" in result.stdout.lower()
