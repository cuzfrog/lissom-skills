"""
End-to-end tests for install.sh using a shared local HTTP server.

All tests share one server instance (module-scoped). Zips for all 4 targets
are pre-built once before the first test and cleaned up after the last.
"""

import os
import subprocess
import threading
import zipfile
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

import pytest

from conftest import AGENTS, SKILLS

REPO_ROOT = Path(__file__).resolve().parent.parent
INSTALL_SH = REPO_ROOT / "scripts" / "install.sh"


def make_install_zip(root: Path, target: str = ".claude") -> Path:
    """Create a pre-built zip file for install testing. Returns zip path."""
    dist_dir = root / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)

    target_map = {
        ".claude": "claude",
        ".opencode": "opencode",
        ".qwen": "qwen",
        ".gemini": "gemini",
    }
    shortname = target_map[target]
    zip_path = dist_dir / f"lissom-skills-{shortname}.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for agent in AGENTS:
            content = (
                f"---\nname: {agent}\ndescription: fixture\ntools: Bash, Read\n"
                f"model: sonnet\n---\nBody for {agent}.\n"
            )
            zf.writestr(f"{target}/agents/{agent}.md", content)

        for skill in SKILLS:
            content = (
                f"---\nname: {skill}\ndescription: fixture\n---\nBody for {skill}.\n"
            )
            zf.writestr(f"{target}/skills/{skill}/SKILL.md", content)

        zf.writestr(f"{target}/templates/Specs.md", "# Sample Specs\n")
        zf.writestr(".lissom/tasks/T1/Specs.md", "# Sample Specs\n")

    return zip_path


def _start_server(root: Path = REPO_ROOT):
    """Start an HTTP server that routes /releases/latest/download/ to root/dist/."""
    class _Handler(SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(root), **kw)
        def log_message(self, *a): pass

        def do_GET(self):
            if self.path.startswith("/releases/latest/download/"):
                zip_name = self.path.split("/")[-1]
                self.path = f"/dist/{zip_name}"
            super().do_GET()

    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, port


@pytest.fixture(scope="module")
def install_server():
    """Pre-build all 4 zips and start HTTP server once for all e2e tests."""
    dist_dir = REPO_ROOT / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)

    for target in (".claude", ".opencode", ".qwen", ".gemini"):
        make_install_zip(REPO_ROOT, target)

    server, port = _start_server()
    yield server, port

    server.shutdown()
    for f in dist_dir.glob("*.zip"):
        f.unlink()


def test_fresh_install_creates_target_tree(tmp_path, install_server):
    """Fresh install downloads zip and extracts all agents, skills, templates."""
    work = tmp_path / "work"
    work.mkdir()
    _, port = install_server

    result = subprocess.run(
        ["bash", str(INSTALL_SH)],
        cwd=str(work),
        env={
            **os.environ,
            "LISSOM_REPO": f"http://127.0.0.1:{port}",
            "LISSOM_TARGET": ".claude",
            "LISSOM_YES": "1",
        },
        capture_output=True, text=True, timeout=30,
    )

    assert result.returncode == 0, (
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert (work / ".claude" / "agents" / "lissom-researcher.md").is_file()
    assert (work / ".claude" / "skills" / "lissom-auto" / "SKILL.md").is_file()
    assert (work / ".lissom" / "tasks" / "T1" / "Specs.md").is_file()


def test_overwrite_confirmation_accepted(tmp_path, install_server):
    """LISSOM_YES=1 overwrites existing target directory."""
    work = tmp_path / "work"
    work.mkdir()
    _, port = install_server

    (work / ".claude" / "agents").mkdir(parents=True)
    (work / ".claude" / "agents" / "old.md").write_text("old content")

    result = subprocess.run(
        ["bash", str(INSTALL_SH)],
        cwd=str(work),
        env={
            **os.environ,
            "LISSOM_REPO": f"http://127.0.0.1:{port}",
            "LISSOM_TARGET": ".claude",
            "LISSOM_YES": "1",
        },
        capture_output=True, text=True, timeout=30,
    )

    assert result.returncode == 0
    assert (work / ".claude" / "agents" / "lissom-researcher.md").is_file()


def test_overwrite_declined_exits(tmp_path, install_server):
    """Non-TTY stdin with no LISSOM_YES declines overwrite."""
    work = tmp_path / "work"
    work.mkdir()
    _, port = install_server

    (work / ".claude" / "agents").mkdir(parents=True)
    old_agent = work / ".claude" / "agents" / "lissom-researcher.md"
    old_agent.write_text("---\nname: old\n---\nold\n")

    result = subprocess.run(
        ["bash", str(INSTALL_SH)],
        cwd=str(work),
        env={
            **os.environ,
            "LISSOM_REPO": f"http://127.0.0.1:{port}",
            "LISSOM_TARGET": ".claude",
        },
        capture_output=True, text=True, timeout=30,
        start_new_session=True,  # detach from controlling TTY → simulates CI / no-tty
    )

    assert result.returncode == 0
    assert old_agent.read_text() == "---\nname: old\n---\nold\n"
    assert "Installation cancelled." in result.stdout


def test_install_samples_specs(tmp_path, install_server):
    """.lissom/tasks/T1/Specs.md created from template."""
    work = tmp_path / "work"
    work.mkdir()
    _, port = install_server

    subprocess.run(
        ["bash", str(INSTALL_SH)],
        cwd=str(work),
        env={
            **os.environ,
            "LISSOM_REPO": f"http://127.0.0.1:{port}",
            "LISSOM_TARGET": ".claude",
            "LISSOM_YES": "1",
        },
        check=True, capture_output=True, text=True, timeout=30,
    )

    specs = work / ".lissom" / "tasks" / "T1" / "Specs.md"
    assert specs.is_file()
    assert "Sample Specs" in specs.read_text()


def test_install_adds_gitignore(tmp_path, install_server):
    """.gitignore updated with .lissom/ entry."""
    work = tmp_path / "work"
    work.mkdir()
    _, port = install_server

    (work / ".gitignore").write_text("__pycache__/\n")

    subprocess.run(
        ["bash", str(INSTALL_SH)],
        cwd=str(work),
        env={
            **os.environ,
            "LISSOM_REPO": f"http://127.0.0.1:{port}",
            "LISSOM_TARGET": ".claude",
            "LISSOM_YES": "1",
        },
        check=True, capture_output=True, text=True, timeout=30,
    )

    gitignore_content = (work / ".gitignore").read_text()
    assert ".lissom/" in gitignore_content


def test_install_cleans_up_zip(tmp_path, install_server):
    """Temporary zip file removed after unzip."""
    work = tmp_path / "work"
    work.mkdir()
    _, port = install_server

    subprocess.run(
        ["bash", str(INSTALL_SH)],
        cwd=str(work),
        env={
            **os.environ,
            "LISSOM_REPO": f"http://127.0.0.1:{port}",
            "LISSOM_TARGET": ".claude",
            "LISSOM_YES": "1",
        },
        check=True, capture_output=True, text=True, timeout=30,
    )

    assert not any(work.glob("lissom-skills-tmp.zip"))
    assert not any(work.glob("*.zip"))


@pytest.mark.parametrize("target", [".claude", ".opencode", ".qwen", ".gemini"])
def test_install_target(tmp_path, install_server, target):
    """LISSOM_TARGET=<target> creates correct directory with agents."""
    work = tmp_path / "work"
    work.mkdir()
    _, port = install_server

    result = subprocess.run(
        ["bash", str(INSTALL_SH)],
        cwd=str(work),
        env={
            **os.environ,
            "LISSOM_REPO": f"http://127.0.0.1:{port}",
            "LISSOM_TARGET": target,
            "LISSOM_YES": "1",
        },
        capture_output=True, text=True, timeout=30,
    )

    assert result.returncode == 0
    assert (work / target / "agents" / "lissom-researcher.md").is_file()


def test_empty_target_dir_preserved(tmp_path, install_server):
    """Empty target dir does not trigger overwrite prompt."""
    work = tmp_path / "work"
    work.mkdir()
    _, port = install_server

    (work / ".claude").mkdir()

    result = subprocess.run(
        ["bash", str(INSTALL_SH)],
        cwd=str(work),
        env={
            **os.environ,
            "LISSOM_REPO": f"http://127.0.0.1:{port}",
            "LISSOM_TARGET": ".claude",
            "LISSOM_YES": "1",
        },
        capture_output=True, text=True, timeout=30,
    )

    assert result.returncode == 0
    assert (work / ".claude" / "agents" / "lissom-researcher.md").is_file()


def test_print_agent_models_shows_models_on_fresh_install(tmp_path, install_server):
    """print_agent_models reads model values from files on first install (SAVED_FIELDS empty)."""
    work = tmp_path / "work"
    work.mkdir()
    _, port = install_server

    result = subprocess.run(
        ["bash", str(INSTALL_SH)],
        cwd=str(work),
        env={
            **os.environ,
            "LISSOM_REPO": f"http://127.0.0.1:{port}",
            "LISSOM_TARGET": ".claude",
            "LISSOM_YES": "1",
        },
        capture_output=True, text=True, timeout=30,
    )

    assert result.returncode == 0, (
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    # On fresh install, models should be read from the extracted files, not "empty (inherit)"
    assert "sonnet" in result.stdout
    assert "lissom-researcher" in result.stdout
    # Should NOT show "empty (inherit)" when files have model values
    assert "empty (inherit)" not in result.stdout


def test_frontmatter_fields_preserved_on_overwrite(tmp_path, install_server):
    """Custom model/temperature fields in existing files survive overwrite."""
    work = tmp_path / "work"
    work.mkdir()
    _, port = install_server

    target = work / ".claude"
    (target / "agents").mkdir(parents=True)
    custom = (
        "---\nname: lissom-researcher\ndescription: custom\ntools: Bash, Read\n"
        "model: my-custom-model\ntemperature: 0.5\n---\nCustom body.\n"
    )
    (target / "agents" / "lissom-researcher.md").write_text(custom)

    result = subprocess.run(
        ["bash", str(INSTALL_SH)],
        cwd=str(work),
        env={
            **os.environ,
            "LISSOM_REPO": f"http://127.0.0.1:{port}",
            "LISSOM_TARGET": ".claude",
            "LISSOM_YES": "1",
        },
        capture_output=True, text=True, timeout=30,
    )

    assert result.returncode == 0
    content = (target / "agents" / "lissom-researcher.md").read_text()
    assert "model: my-custom-model" in content
    assert "temperature: 0.5" in content
    assert "my-custom-model" in result.stdout
    assert "lissom-researcher" in result.stdout
    assert "sonnet" in result.stdout
    assert "(edit in" in result.stdout


def test_remote_install_via_curl(tmp_path, install_server):
    """Simulate curl | bash flow with HTTP server serving zips."""
    work = tmp_path / "work"
    work.mkdir()
    _, port = install_server

    result = subprocess.run(
        ["bash", "-c",
         f"curl -fsSL http://127.0.0.1:{port}/scripts/install.sh | bash"],
        cwd=str(work),
        env={
            **os.environ,
            "LISSOM_REPO": f"http://127.0.0.1:{port}",
            "LISSOM_TARGET": ".claude",
            "LISSOM_YES": "1",
        },
        capture_output=True, text=True, timeout=60,
    )

    assert result.returncode == 0, (
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert (work / ".claude" / "agents" / "lissom-researcher.md").is_file()
    assert (work / ".claude" / "skills" / "lissom-auto" / "SKILL.md").is_file()
    assert (work / ".lissom" / "tasks" / "T1" / "Specs.md").is_file()
