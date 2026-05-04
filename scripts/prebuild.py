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

    models = [model_map.get(agent, "empty (inherit)") for agent in AGENTS]
    agent_width = max(len("Agent"), max(len(a) for a in AGENTS))
    model_width = max(len("Model"), max(len(m) for m in models))

    lines = []
    header = f"{'Agent':<{agent_width}}  {'Model':<{model_width}}"
    lines.append(header)
    lines.append("-" * agent_width + "  " + "-" * model_width)
    for agent, model in zip(AGENTS, models):
        lines.append(f"{agent:<{agent_width}}  {model:<{model_width}}")

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
