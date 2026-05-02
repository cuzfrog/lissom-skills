from pathlib import Path
import pytest


@pytest.fixture
def script_dir() -> Path:
    """Return the root directory of the lissom-skills project."""
    return Path(__file__).resolve().parent.parent.parent
