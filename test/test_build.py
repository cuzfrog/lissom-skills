"""
Tests for the Python build script and shared utility modules.

Covers Claude model injection, frontmatter parsing, arg shifting,
backtick tool rewriting, and build integration tests.
"""

import os
import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest

from scripts.lib.constants import AGENTS, SKILLS
from scripts.lib.frontmatter import inject_field, parse_frontmatter, shift_args, rewrite_backtick_tools

REPO_ROOT = Path(__file__).resolve().parent.parent


# ── Helpers ──────────────────────────────────────────────────────────

def make_build_fixture(root: Path) -> None:
    """Create a minimal project tree for build testing."""
    agents_dir = root / "src" / "agents"
    agents_dir.mkdir(parents=True)
    for agent in AGENTS:
        (agents_dir / f"{agent}.md").write_text(
            f"---\nname: {agent}\ndescription: fixture\ntools: Bash, Read, Write, AskUserQuestion\n---\nBody for {agent} using `Bash` and `Read`.\n"
        )

    skills_dir = root / "src" / "skills"
    for skill in SKILLS:
        (skills_dir / skill).mkdir(parents=True)
        (skills_dir / skill / "SKILL.md").write_text(
            f"---\nname: {skill}\ndescription: fixture\n---\nBody for {skill} using `Grep`.\n"
        )

    (root / "src" / "templates").mkdir(parents=True)
    (root / "src" / "templates" / "Specs.md").write_text("# Sample Specs\n")

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
        with pytest.raises(ValueError, match="opening"):
            parse_frontmatter("no frontmatter here")

    def test_malformed_missing_closing(self):
        """Missing closing --- raises ValueError."""
        with pytest.raises(ValueError, match="closing"):
            parse_frontmatter("---\nname: test\nno closing\n")

    def test_parse_real_file(self):
        """Parse a real agent file successfully."""
        content = (REPO_ROOT / "src" / "agents" / "lissom-researcher.md").read_text()
        fields, body = parse_frontmatter(content)
        assert "name" in fields
        assert "description" in fields
        assert "tools" in fields
        assert body.strip()


# ── Shift Args Tests ─────────────────────────────────────────────────

class TestShiftArgs:
    def test_shift_0_to_1(self):
        """$0 becomes $1."""
        assert shift_args("`$0`") == "`$1`"

    def test_shift_1_to_2(self):
        """$1 becomes $2."""
        assert shift_args("`$1` and `$2`") == "`$2` and `$3`"

    def test_shift_10_to_11(self):
        """$10 becomes $11 (multi-digit)."""
        assert shift_args("`$10`") == "`$11`"

    def test_no_matches(self):
        """No dollar sign returns input unchanged."""
        assert shift_args("no args here") == "no args here"

    def test_shift_9_to_10(self):
        """$9 becomes $10 (boundary)."""
        assert shift_args("`$9`") == "`$10`"

    def test_mixed_no_dollar(self):
        """Text without $ is not affected."""
        assert shift_args("plain text") == "plain text"

    def test_multiple_shifts(self):
        """Multiple $N references all shifted."""
        result = shift_args("`$0` and `$1` then `$2`")
        assert result == "`$1` and `$2` then `$3`"


# ── Rewrite Backtick Tools Tests ─────────────────────────────────────

class TestRewriteBacktickTools:
    def test_basic_replacement(self):
        """Single tool name replaced."""
        result = rewrite_backtick_tools("Use `Bash` to run.", {"Bash": "bash"})
        assert result == "Use `bash` to run."

    def test_multiple_replacements(self):
        """Multiple tool names all replaced."""
        result = rewrite_backtick_tools(
            "Use `Bash` and `Read`.",
            {"Bash": "bash", "Read": "read"},
        )
        assert result == "Use `bash` and `read`."

    def test_unmapped_tool_unchanged(self):
        """Tool not in mapping is left as-is."""
        result = rewrite_backtick_tools("Use `Bash`.", {"Read": "read"})
        assert result == "Use `Bash`."

    def test_empty_content(self):
        """Empty content returns empty string."""
        result = rewrite_backtick_tools("", {"Bash": "bash"})
        assert result == ""

    def test_no_backtick_tools(self):
        """Tool names without backticks are not replaced."""
        result = rewrite_backtick_tools("Use Bash.", {"Bash": "bash"})
        assert result == "Use Bash."

    def test_empty_mapping(self):
        """Empty mapping leaves content unchanged."""
        result = rewrite_backtick_tools("Use `Bash`.", {})
        assert result == "Use `Bash`."

    def test_overlapping_patterns(self):
        """Patterns are independent (no regex overlap issues)."""
        result = rewrite_backtick_tools(
            "`AskUserQuestion` and `Bash`.",
            {"AskUserQuestion": "question", "Bash": "bash"},
        )
        assert result == "`question` and `bash`."




# ── Build Integration Tests ──────────────────────────────────────────

class TestBuildScript:
    def test_build_creates_all_five_zips(self, tmp_path):
        """Running build.py produces 5 zip files."""
        make_build_fixture(tmp_path)
        result = subprocess.run(
            ["python3", str(tmp_path / "scripts" / "build.py"), "--root", str(tmp_path)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"

        dist_dir = tmp_path / "dist"
        assert dist_dir.exists()
        zips = sorted(dist_dir.glob("*.zip"))
        assert len(zips) == 5
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
            assert ".lissom/tasks/T1/Specs.md" in names

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

    def test_specs_and_preferences_copied(self, tmp_path):
        """.lissom/tasks/T1/Specs.md and user_preference_questions.json are in each zip."""
        make_build_fixture(tmp_path)
        subprocess.run(
            ["python3", str(tmp_path / "scripts" / "build.py"), "--root", str(tmp_path)],
            check=True, capture_output=True,
        )

        for shortname in ("claude", "opencode", "qwen", "gemini", "pi"):
            zip_path = tmp_path / "dist" / f"lissom-skills-{shortname}.zip"
            with zipfile.ZipFile(zip_path) as zf:
                names = zf.namelist()
                assert ".lissom/tasks/T1/Specs.md" in names, f"missing Specs.md in {shortname}"
                # Preferences path differs for pi target
                if shortname == "pi":
                    prefs_path = ".pi/skills/lissom-auto/user_preference_questions.json"
                else:
                    prefs_path = f".{shortname}/skills/lissom-auto/user_preference_questions.json"
                assert prefs_path in names, f"missing prefs in {shortname}"

    def test_pi_zip_structure(self, tmp_path):
        """Pi zip has correct directory layout (agents at .pi/agents/)."""
        make_build_fixture(tmp_path)
        subprocess.run(
            ["python3", str(tmp_path / "scripts" / "build.py"), "--root", str(tmp_path)],
            check=True, capture_output=True,
        )

        with zipfile.ZipFile(tmp_path / "dist" / "lissom-skills-pi.zip") as zf:
            names = zf.namelist()
            assert ".pi/agents/lissom-researcher.md" in names
            assert ".pi/skills/lissom-auto/SKILL.md" in names
            assert ".lissom/tasks/T1/Specs.md" in names

    def test_pi_zip_agent_content(self, tmp_path):
        """Pi agent has rewritten body tools, no model, tools preserved."""
        make_build_fixture(tmp_path)
        subprocess.run(
            ["python3", str(tmp_path / "scripts" / "build.py"), "--root", str(tmp_path)],
            check=True, capture_output=True,
        )

        with zipfile.ZipFile(tmp_path / "dist" / "lissom-skills-pi.zip") as zf:
            content = zf.read(".pi/agents/lissom-researcher.md").decode()
            assert "`bash`" in content
            assert "`Bash`" not in content
            assert "`read`" in content
            assert "model:" not in content
            # tools: field is preserved with converted flag names
            assert "tools:" in content
            assert "Bash" not in content.split("---")[1]  # frontmatter has lowercase tools

    def test_pi_zip_skill_preserves_agent_tool_name(self, tmp_path):
        """Pi skill preserves `Agent` (pi-subagents exposes Agent natively)."""
        # Create a skill with Agent reference to verify no rewrite
        make_build_fixture(tmp_path)
        # Overwrite one skill with an Agent reference
        skill_path = tmp_path / "src" / "skills" / "lissom-plan" / "SKILL.md"
        skill_path.write_text(
            "---\nname: lissom-plan\ndescription: fixture\n---\nUse `Agent` to delegate.\n"
        )

        subprocess.run(
            ["python3", str(tmp_path / "scripts" / "build.py"), "--root", str(tmp_path)],
            check=True, capture_output=True,
        )

        with zipfile.ZipFile(tmp_path / "dist" / "lissom-skills-pi.zip") as zf:
            content = zf.read(".pi/skills/lissom-plan/SKILL.md").decode()
            assert "`Agent`" in content
            assert "`lissom-agent`" not in content

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
        prefs = tmp_path / "src" / "skills" / "lissom-auto" / "user_preference_questions.json"
        prefs.unlink()

        result = subprocess.run(
            ["python3", str(tmp_path / "scripts" / "build.py"), "--root", str(tmp_path)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "warn" in result.stdout.lower()
