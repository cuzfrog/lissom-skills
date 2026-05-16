#!/usr/bin/env python3
"""
Build orchestrator: reads agent/skill sources, converts per target, produces zips.

Usage:
    python scripts/build.py [--root <project_root>]

No CLI arguments by default — always builds all targets (claude, opencode, qwen, gemini, pi).
Output goes to dist/ (created if missing).
"""

import argparse
import os
import sys
import tempfile
import zipfile
from pathlib import Path

# Ensure project root is on sys.path so 'scripts.lib' is importable
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from scripts.lib.constants import (
    AGENTS,
    SKILLS,
    TARGET_CONFIG,
)
from scripts.lib.converter_factory import get_converter


def read_source(path: Path) -> str:
    """Read a source file, raising FileNotFoundError if missing."""
    if not path.exists():
        raise FileNotFoundError(f"Required source file not found: {path}")
    return path.read_text(encoding="utf-8")


def build(root: Path) -> None:
    """Run the full build: enumerate sources, convert per target, zip."""
    # ── 1. Locate source directories ──────────────────────────────
    agents_src = root / "src" / "agents"
    skills_src = root / "src" / "skills"
    templates_src = root / "src" / "templates"
    dist_dir = root / "dist"

    # ── 2. Enumerate source contents ──────────────────────────────
    agent_contents: dict[str, str] = {}
    for agent in AGENTS:
        path = agents_src / f"{agent}.md"
        agent_contents[agent] = read_source(path)

    skill_contents: dict[str, str] = {}
    for skill in SKILLS:
        path = skills_src / skill / "SKILL.md"
        skill_contents[skill] = read_source(path)

    # Optional files
    preferences_path = skills_src / "lissom-auto" / "user_preference_questions.json"
    preferences_content: str | None = None
    if preferences_path.exists():
        preferences_content = preferences_path.read_text(encoding="utf-8")
    else:
        print("  [warn] skills/lissom-auto/user_preference_questions.json not found, skipping")

    specs_content = read_source(templates_src / "Specs.md")

    # ── 3. Build per target ───────────────────────────────────────
    os.makedirs(dist_dir, exist_ok=True)

    for target_dir, shortname in TARGET_CONFIG.items():
        print(f"Building {target_dir} ({shortname})...")

        with tempfile.TemporaryDirectory(prefix=f"build-{shortname}-") as tmpdir:
            staging = Path(tmpdir)
            agents_dst = staging / target_dir / "agents"
            skills_dst = staging / target_dir / "skills"
            agents_dst.mkdir(parents=True)
            skills_dst.mkdir(parents=True)

            # Convert agents and skills via the shared Converter interface
            converter = get_converter(shortname)
            for agent_name, source_content in agent_contents.items():
                output = converter.convert_agent(source_content, agent_name)
                (agents_dst / f"{agent_name}.md").write_text(
                    output, encoding="utf-8"
                )

            for skill_name, source_content in skill_contents.items():
                output = converter.convert_skill(source_content, skill_name)

                skill_dir = skills_dst / skill_name
                skill_dir.mkdir(parents=True, exist_ok=True)
                (skill_dir / "SKILL.md").write_text(output, encoding="utf-8")

            # Stage Specs.md at its installed location (.lissom/tasks/T1/)
            # so install.sh can use 'unzip -n' to skip it on re-installs
            lissom_dir = staging / ".lissom" / "tasks" / "T1"
            lissom_dir.mkdir(parents=True, exist_ok=True)
            (lissom_dir / "Specs.md").write_text(specs_content, encoding="utf-8")

            # Copy preferences (optional)
            if preferences_content is not None:
                auto_dir = skills_dst / "lissom-auto"
                auto_dir.mkdir(parents=True, exist_ok=True)
                (auto_dir / "user_preference_questions.json").write_text(
                    preferences_content, encoding="utf-8"
                )

            # Create zip
            zip_path = dist_dir / f"lissom-skills-{shortname}.zip"
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for file_path in staging.rglob("*"):
                    if file_path.is_file():
                        arcname = str(file_path.relative_to(staging))
                        zf.write(file_path, arcname=arcname)

            # Count files in zip
            with zipfile.ZipFile(zip_path, "r") as zf:
                file_count = len(zf.namelist())
            size = os.path.getsize(zip_path)
            print(f"  Created {zip_path.name} — {file_count} files, {size} bytes")

    print("Build complete!")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build lissom-skills zips for all targets"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Project root (default: auto-detect from script location)",
    )
    args = parser.parse_args()

    if args.root:
        project_root = args.root.resolve()
    else:
        project_root = _project_root

    build(project_root)


if __name__ == "__main__":
    main()
