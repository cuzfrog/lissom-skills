"""
Unit tests for Gemini-related constants in scripts/lib/constants.sh.
Verifies the acceptance criteria from Step 1 (T25).
"""
import subprocess
from pathlib import Path
import pytest


def run_constants_check(script_dir: Path, bash_expr: str) -> str:
    """Source constants.sh and execute bash_expr, returning stdout."""
    bash_code = f'''
    source "{script_dir}/scripts/lib/constants.sh"
    {bash_expr}
    '''
    result = subprocess.run(
        ["bash", "-c", bash_code],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Expression failed: {result.stderr}")
    return result.stdout


class TestGeminiConstants:
    """Verify Gemini constants defined in constants.sh"""

    def test_source_succeeds(self, script_dir: Path):
        """Acceptance: sourcing constants.sh succeeds with no errors"""
        bash_code = f'source "{script_dir}/scripts/lib/constants.sh"'
        result = subprocess.run(
            ["bash", "-c", bash_code],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert result.stderr == ""

    def test_target_config_gemini(self, script_dir: Path):
        """Acceptance: echo ${{TARGET_CONFIG[.gemini]}} prints gemini"""
        out = run_constants_check(script_dir, 'echo "${TARGET_CONFIG[.gemini]}"')
        assert out.strip() == "gemini"

    def test_target_model_default_gemini(self, script_dir: Path):
        """Acceptance: echo ${{TARGET_MODEL_DEFAULT[gemini]}} prints false"""
        out = run_constants_check(script_dir, 'echo "${TARGET_MODEL_DEFAULT[gemini]}"')
        assert out.strip() == "false"

    def test_get_gemini_model_implementer(self, script_dir: Path):
        """Acceptance: get_gemini_model lissom-implementer prints gemini-3-flash-preview"""
        out = run_constants_check(script_dir, "get_gemini_model lissom-implementer")
        assert out.strip() == "gemini-3-flash-preview"

    def test_get_gemini_model_researcher(self, script_dir: Path):
        """Acceptance: get_gemini_model lissom-researcher prints gemini-3-pro-preview"""
        out = run_constants_check(script_dir, "get_gemini_model lissom-researcher")
        assert out.strip() == "gemini-3-pro-preview"

    def test_get_gemini_model_planner(self, script_dir: Path):
        """get_gemini_model lissom-planner prints gemini-3-flash-preview"""
        out = run_constants_check(script_dir, "get_gemini_model lissom-planner")
        assert out.strip() == "gemini-3-flash-preview"

    def test_get_gemini_model_reviewer(self, script_dir: Path):
        """get_gemini_model lissom-reviewer prints gemini-3-flash-preview"""
        out = run_constants_check(script_dir, "get_gemini_model lissom-reviewer")
        assert out.strip() == "gemini-3-flash-preview"

    def test_get_gemini_model_specs_reviewer(self, script_dir: Path):
        """get_gemini_model lissom-specs-reviewer prints gemini-3-flash-preview"""
        out = run_constants_check(script_dir, "get_gemini_model lissom-specs-reviewer")
        assert out.strip() == "gemini-3-flash-preview"

    def test_get_gemini_model_unknown(self, script_dir: Path):
        """get_gemini_model with unknown agent uses default gemini-3-flash-preview"""
        out = run_constants_check(script_dir, "get_gemini_model unknown-agent")
        assert out.strip() == "gemini-3-flash-preview"

    def test_claude_to_gemini_tool_edit(self, script_dir: Path):
        """Acceptance: ${{CLAUDE_TO_GEMINI_TOOL[Edit]}} prints replace"""
        out = run_constants_check(script_dir, 'echo "${CLAUDE_TO_GEMINI_TOOL[Edit]}"')
        assert out.strip() == "replace"

    def test_claude_to_gemini_tool_askuserquestion(self, script_dir: Path):
        """Acceptance: ${{CLAUDE_TO_GEMINI_TOOL[AskUserQuestion]}} prints ask_user"""
        out = run_constants_check(script_dir, 'echo "${CLAUDE_TO_GEMINI_TOOL[AskUserQuestion]}"')
        assert out.strip() == "ask_user"

    def test_claude_to_gemini_body_websearch(self, script_dir: Path):
        """Acceptance: ${{CLAUDE_TO_GEMINI_BODY[WebSearch]}} prints google_web_search"""
        out = run_constants_check(script_dir, 'echo "${CLAUDE_TO_GEMINI_BODY[WebSearch]}"')
        assert out.strip() == "google_web_search"

    def test_claude_to_gemini_tool_all_mappings(self, script_dir: Path):
        """Verify all tool mappings in CLAUDE_TO_GEMINI_TOOL"""
        out = run_constants_check(
            script_dir,
            'echo "${CLAUDE_TO_GEMINI_TOOL[Bash]}" '
            '&& echo "${CLAUDE_TO_GEMINI_TOOL[Read]}" '
            '&& echo "${CLAUDE_TO_GEMINI_TOOL[Write]}" '
            '&& echo "${CLAUDE_TO_GEMINI_TOOL[Edit]}" '
            '&& echo "${CLAUDE_TO_GEMINI_TOOL[Glob]}" '
            '&& echo "${CLAUDE_TO_GEMINI_TOOL[Grep]}" '
            '&& echo "${CLAUDE_TO_GEMINI_TOOL[WebFetch]}" '
            '&& echo "${CLAUDE_TO_GEMINI_TOOL[WebSearch]}" '
            '&& echo "${CLAUDE_TO_GEMINI_TOOL[AskUserQuestion]}"'
        )
        lines = out.strip().split("\n")
        assert lines[0] == "run_shell_command"
        assert lines[1] == "read_file"
        assert lines[2] == "write_file"
        assert lines[3] == "replace"
        assert lines[4] == "glob"
        assert lines[5] == "grep_search"
        assert lines[6] == "web_fetch"
        assert lines[7] == "google_web_search"
        assert lines[8] == "ask_user"

    def test_claude_to_gemini_body_all_mappings(self, script_dir: Path):
        """Verify all tool mappings in CLAUDE_TO_GEMINI_BODY"""
        out = run_constants_check(
            script_dir,
            'echo "${CLAUDE_TO_GEMINI_BODY[Bash]}" '
            '&& echo "${CLAUDE_TO_GEMINI_BODY[Read]}" '
            '&& echo "${CLAUDE_TO_GEMINI_BODY[Write]}" '
            '&& echo "${CLAUDE_TO_GEMINI_BODY[Edit]}" '
            '&& echo "${CLAUDE_TO_GEMINI_BODY[Glob]}" '
            '&& echo "${CLAUDE_TO_GEMINI_BODY[Grep]}" '
            '&& echo "${CLAUDE_TO_GEMINI_BODY[WebFetch]}" '
            '&& echo "${CLAUDE_TO_GEMINI_BODY[WebSearch]}" '
            '&& echo "${CLAUDE_TO_GEMINI_BODY[AskUserQuestion]}"'
        )
        lines = out.strip().split("\n")
        assert lines[0] == "run_shell_command"
        assert lines[1] == "read_file"
        assert lines[2] == "write_file"
        assert lines[3] == "replace"
        assert lines[4] == "glob"
        assert lines[5] == "grep_search"
        assert lines[6] == "web_fetch"
        assert lines[7] == "google_web_search"
        assert lines[8] == "ask_user"
