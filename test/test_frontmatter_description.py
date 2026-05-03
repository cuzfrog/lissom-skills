"""
Verify that the `description` field in YAML frontmatter is a single-line
plain scalar as required by Guidelines.md.
"""
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _discover_files():
    files = []
    files.extend(REPO_ROOT.glob("agents/*.md"))
    files.extend(REPO_ROOT.glob("skills/*/SKILL.md"))
    return sorted(files)


@pytest.mark.parametrize(
    "filepath",
    [pytest.param(p, id=str(p.relative_to(REPO_ROOT))) for p in _discover_files()],
)
def test_description_is_oneline(filepath: Path) -> None:
    content = filepath.read_text()
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("description:"):
            value = stripped[len("description:"):].strip()
            assert value, f"{filepath.name}: description value is empty"
            assert not value.startswith(">"), (
                f"{filepath.name}: description uses YAML block scalar '>', "
                f"use a plain single-line scalar instead"
            )
            assert not value.startswith("|"), (
                f"{filepath.name}: description uses YAML literal block '|', "
                f"use a plain single-line scalar instead"
            )
            return
    pytest.fail(f"{filepath.name}: no description field found in frontmatter")
