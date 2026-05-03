"""
Unit tests for ui.sh functions.
Tests for:
- display_model_table() - adaptive-width table for agent models
"""
import subprocess
from pathlib import Path


def run_ui_function(script_dir: Path, bash_body: str) -> subprocess.CompletedProcess:
    """Run bash code with ui.sh function definitions loaded."""
    bash_code = f"""#!/usr/bin/env bash
SCRIPT_DIR="{script_dir}"
source "$SCRIPT_DIR/scripts/lib/ui.sh"

{bash_body}
"""
    return subprocess.run(
        ["bash", "-c", bash_code],
        capture_output=True,
        text=True,
    )


class TestDisplayModelTable:
    """display_model_table() renders adaptive-width table."""

    def test_basic_table(self, script_dir):
        """Renders table with agent names and model values."""
        r = run_ui_function(script_dir, """
declare -A MODELS
MODELS["lissom-researcher"]="opus-4.6"
MODELS["lissom-planner"]="sonnet"
display_model_table MODELS
""")
        assert r.returncode == 0
        out = r.stdout
        assert "┌" in out
        assert "┬" in out
        assert "┤" in out
        assert "└" in out
        assert "lissom-researcher" in out
        assert "lissom-planner" in out
        assert "opus-4.6" in out
        assert "sonnet" in out
        assert "Agent" in out
        assert "Model" in out

    def column_width(self, text: str, header: str) -> int:
        """Extract the content width of a table column by matching the header."""
        lines = text.splitlines()
        # Find the separator line that contains ┼ and use it to determine column
        # A simpler approach: find the header line and measure spaces around the header
        sep_line = next((l for l in lines if "┼" in l), None)
        if sep_line:
            parts = sep_line.split("┼")
            if header == "Agent":
                return len(parts[0].lstrip("├─"))
            elif header == "Model":
                return len(parts[1].rstrip("─┤"))
        return 0

    def test_adaptive_column_widths(self, script_dir):
        """Columns expand for longer model values."""
        r = run_ui_function(script_dir, """
declare -A MODELS
MODELS["a"]="opencode-go/deepseek-v4-flash"
MODELS["b"]="opencode-go/qwen3.6-plus-preview"
display_model_table MODELS
""")
        assert r.returncode == 0
        out = r.stdout
        # Both long model names should be fully visible
        assert "opencode-go/deepseek-v4-flash" in out
        assert "opencode-go/qwen3.6-plus-preview" in out
        # Each row should contain both the agent name and model
        lines = out.splitlines()
        data_lines = [l for l in lines if "│ a" in l or "│ b" in l]
        assert len(data_lines) == 2

    def test_adaptive_agent_name_width(self, script_dir):
        """Columns expand for longer agent names."""
        r = run_ui_function(script_dir, """
declare -A MODELS
MODELS["lissom-specs-reviewer"]="sonnet"
MODELS["a"]="haiku"
display_model_table MODELS
""")
        assert r.returncode == 0
        out = r.stdout
        assert "lissom-specs-reviewer" in out
        # Verify formatting - each data line should have proper table separators
        lines = out.splitlines()
        for line in lines:
            if "lissom-specs-reviewer" in line:
                assert line.startswith("│ ")
                assert line.endswith(" │")

    def test_sorts_agent_names(self, script_dir):
        """Agent names are displayed in sorted order."""
        r = run_ui_function(script_dir, """
declare -A MODELS
MODELS["z-agent"]="model-z"
MODELS["a-agent"]="model-a"
display_model_table MODELS
""")
        assert r.returncode == 0
        out = r.stdout
        lines = out.splitlines()
        data_lines = [l for l in lines if "│" in l and "Agent" not in l and "─" not in l]
        data_text = " ".join(data_lines)
        a_idx = data_text.index("a-agent")
        z_idx = data_text.index("z-agent")
        assert a_idx < z_idx

    def test_column_header_padding(self, script_dir):
        """Column headers are padded to match the widest content."""
        r = run_ui_function(script_dir, """
declare -A MODELS
MODELS["lissom-implementer"]="haiku"
display_model_table MODELS
""")
        assert r.returncode == 0
        out = r.stdout
        lines = out.splitlines()
        # The border lines should have matching widths
        top = next(l for l in lines if "┌" in l and "┬" in l)
        bottom = next(l for l in lines if "└" in l and "┴" in l)
        assert len(top) == len(bottom)

    def test_multiple_rows_alligned(self, script_dir):
        """Multiple rows share the same column widths."""
        r = run_ui_function(script_dir, """
declare -A MODELS
MODELS["lissom-researcher"]="opus-4.6"
MODELS["lissom-planner"]="sonnet"
MODELS["lissom-implementer"]="haiku"
display_model_table MODELS
""")
        assert r.returncode == 0
        out = r.stdout
        lines = out.splitlines()
        # Find the separator ├──┼──┤ line
        sep = next(l for l in lines if "├" in l and "┼" in l)
        # All data lines should be the same length as the separator
        sep_len = len(sep)
        for line in lines:
            if line.startswith("│ ") and "Agent" not in line:
                assert len(line) == sep_len, f"Line length {len(line)} != separator {sep_len}: {line}"

    def test_no_models_no_crash(self, script_dir):
        """Empty associative array produces a header-only table."""
        r = run_ui_function(script_dir, """
declare -A MODELS
display_model_table MODELS
""")
        assert r.returncode == 0
        out = r.stdout
        # Should still produce a table with headers but no data rows
        assert "┌" in out
        assert "Agent" in out
        assert "Model" in out
        assert "└" in out
        assert "┴" in out

    def test_model_with_slash_and_dash(self, script_dir):
        """Model names containing slashes/dashes (like Opencode models) display correctly."""
        r = run_ui_function(script_dir, """
declare -A MODELS
MODELS["lissom-researcher"]="opencode-go/deepseek-v4-pro"
MODELS["lissom-planner"]="opencode-go/qwen3.6-plus"
display_model_table MODELS
""")
        assert r.returncode == 0
        out = r.stdout
        assert "opencode-go/deepseek-v4-pro" in out
        assert "opencode-go/qwen3.6-plus" in out

    def test_table_total_line_width(self, script_dir):
        """Top, separator, and bottom borders are all the same length."""
        r = run_ui_function(script_dir, """
declare -A MODELS
MODELS["lissom-implementer"]="haiku"
display_model_table MODELS
""")
        assert r.returncode == 0
        out = r.stdout
        lines = out.splitlines()
        top = next(l for l in lines if "┌" in l and "┬" in l)
        sep = next(l for l in lines if "├" in l and "┼" in l)
        bot = next(l for l in lines if "└" in l and "┴" in l)
        assert len(top) == len(sep) == len(bot), f"Borders differ: top={len(top)} sep={len(sep)} bot={len(bot)}"
        # Data rows also match border length
        for line in lines:
            if line.startswith("│ ") and "Agent" not in line:
                assert len(line) == len(sep), f"Data line {len(line)} != separator {len(sep)}: {line}"
