#!/usr/bin/env python3
"""
Prebuild script: generates install-readme.txt for a given target.

Usage:
    python scripts/prebuild.py <target_shortname>
"""

import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from scripts.lib.constants import (
    AGENTS,
    CLAUDE_MODEL_MAP,
    OPENCODE_MODEL_MAP,
    QWEN_MODEL_MAP,
    GEMINI_MODEL_MAP,
)

MODEL_MAPS = {
    "claude": CLAUDE_MODEL_MAP,
    "opencode": OPENCODE_MODEL_MAP,
    "qwen": QWEN_MODEL_MAP,
    "gemini": GEMINI_MODEL_MAP,
}


def generate_readme(target: str) -> str:
    model_map = MODEL_MAPS[target]

    lines = ["| Agent | Model |", "| --- | --- |"]
    for agent in AGENTS:
        model = model_map.get(agent, "empty (inherit)")
        lines.append(f"| {agent} | {model} |")

    return "\n".join(lines) + "\n"


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python scripts/prebuild.py <target>", file=sys.stderr)
        sys.exit(1)

    target = sys.argv[1]
    if target not in MODEL_MAPS:
        print(f"Unknown target: {target}. Choose from: {', '.join(MODEL_MAPS.keys())}", file=sys.stderr)
        sys.exit(1)

    content = generate_readme(target)
    Path("install-readme.txt").write_text(content, encoding="utf-8")
    print(f"Generated install-readme.txt for {target}")


if __name__ == "__main__":
    main()
