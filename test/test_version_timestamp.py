"""
Verify that the `version` field in agent/skill YAML frontmatter is not
older than each file's latest git commit timestamp by more than 3 hours.
"""
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _discover_files():
    files = []
    files.extend(REPO_ROOT.glob("agents/*.md"))
    files.extend(REPO_ROOT.glob("skills/*/SKILL.md"))
    return sorted(files)


def _parse_version(filepath):
    content = filepath.read_text()
    # Check for comment format on first line
    first_line = content.splitlines()[0] if content else ""
    if first_line.startswith("<!-- version:") and first_line.endswith("-->"):
        # Extract timestamp from: <!-- version: 2026-05-03T12:48:24Z -->
        inner = first_line[len("<!-- version:"):-len("-->")]
        return inner.strip()
    # Fallback: old YAML frontmatter format
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None
    for line in parts[1].splitlines():
        line = line.strip()
        if line.startswith("version:"):
            return line[len("version:"):].strip()
    return None


def _get_commit_time(filepath):
    result = subprocess.run(
        ["git", "log", "-1", "--format=%aI", "--", str(filepath)],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    out = result.stdout.strip()
    if result.returncode != 0 or not out:
        return None
    return out


def _parse_iso(dt_str):
    return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))


@pytest.mark.parametrize(
    "filepath",
    [pytest.param(p, id=str(p.relative_to(REPO_ROOT))) for p in _discover_files()],
)
def test_version_not_older_than_commit(filepath):
    version_str = _parse_version(filepath)
    if version_str is None:
        pytest.skip(f"No version field in {filepath.name}")

    commit_str = _get_commit_time(filepath)
    if commit_str is None:
        pytest.skip(f"No git history for {filepath.name}")

    diff = _parse_iso(version_str) - _parse_iso(commit_str)
    three_hours = timedelta(hours=3)

    assert diff >= -three_hours, (
        f"version={version_str} is more than 3h older than commit={commit_str} diff={diff}"
    )
