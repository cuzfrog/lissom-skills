"""
Integration tests for the new simplified install.sh.

The new install flow: prompt target → download zip → unzip → cleanup.
Tests use a local HTTP server to simulate GitHub releases.
"""

import os
import shutil
import subprocess
import threading
import zipfile
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from conftest import AGENTS, SKILLS

REPO_ROOT = Path(__file__).resolve().parent.parent
INSTALL_SH = REPO_ROOT / "scripts" / "install.sh"


def make_install_zip(root: Path, target: str = ".claude") -> Path:
    """Create a pre-built zip file for install testing. Returns zip path."""
    dist_dir = root / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)

    # Map target to shortname
    target_map = {
        ".claude": "claude",
        ".opencode": "opencode",
        ".qwen": "qwen",
        ".gemini": "gemini",
    }
    shortname = target_map[target]
    zip_path = dist_dir / f"lissom-skills-{shortname}.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add agent files
        for agent in AGENTS:
            content = (
                f"---\nname: {agent}\ndescription: fixture\ntools: Bash, Read\n"
                f"model: sonnet\n---\nBody for {agent}.\n"
            )
            zf.writestr(f"{target}/agents/{agent}.md", content)

        # Add skill files
        for skill in SKILLS:
            content = (
                f"---\nname: {skill}\ndescription: fixture\n---\nBody for {skill}.\n"
            )
            zf.writestr(f"{target}/skills/{skill}/SKILL.md", content)

        # Add templates
        zf.writestr(f"{target}/templates/Specs.md", "# Sample Specs\n")

    return zip_path


def _start_server(root: Path = REPO_ROOT):
    """Start an HTTP server that routes /releases/latest/download/ to root/dist/."""
    class _Handler(SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(root), **kw)
        def log_message(self, *a): pass

        def do_GET(self):
            # Route /releases/latest/download/<zip> to <root>/dist/<zip>
            if self.path.startswith("/releases/latest/download/"):
                zip_name = self.path.split("/")[-1]
                self.path = f"/dist/{zip_name}"
            super().do_GET()

    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, port


def test_fresh_install_creates_target_tree(tmp_path):
    """Fresh install downloads zip and extracts all agents, skills, templates."""
    work = tmp_path / "work"
    work.mkdir()

    dist_dir = REPO_ROOT / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    zip_path = make_install_zip(REPO_ROOT)
    (REPO_ROOT / "dist" / zip_path.name).write_bytes(zip_path.read_bytes())

    server, port = _start_server()

    try:
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

        # Verify target tree
        assert (work / ".claude" / "agents" / "lissom-researcher.md").is_file()
        assert (work / ".claude" / "skills" / "lissom-auto" / "SKILL.md").is_file()
        assert (work / ".lissom" / "tasks" / "T1" / "Specs.md").is_file()
    finally:
        server.shutdown()
        # Clean up dist
        for f in dist_dir.glob("*.zip"):
            f.unlink()


def test_overwrite_confirmation_accepted(tmp_path):
    """LISSOM_YES=1 overwrites existing target directory."""
    work = tmp_path / "work"
    work.mkdir()

    # Seed an existing file
    (work / ".claude" / "agents").mkdir(parents=True)
    (work / ".claude" / "agents" / "old.md").write_text("old content")

    dist_dir = REPO_ROOT / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    zip_path = make_install_zip(REPO_ROOT)
    (REPO_ROOT / "dist" / zip_path.name).write_bytes(zip_path.read_bytes())

    server, port = _start_server()

    try:
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
        # New files should exist
        assert (work / ".claude" / "agents" / "lissom-researcher.md").is_file()
    finally:
        server.shutdown()
        for f in dist_dir.glob("*.zip"):
            f.unlink()


def test_overwrite_declined_exits(tmp_path):
    """User declines overwrite, directory unchanged."""
    work = tmp_path / "work"
    work.mkdir()

    # Seed an existing file
    (work / ".claude" / "agents").mkdir(parents=True)
    old_agent = work / ".claude" / "agents" / "lissom-researcher.md"
    old_agent.write_text("---\nname: old\n---\nold\n")

    dist_dir = REPO_ROOT / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    zip_path = make_install_zip(REPO_ROOT)
    (REPO_ROOT / "dist" / zip_path.name).write_bytes(zip_path.read_bytes())

    server, port = _start_server()

    try:
        result = subprocess.run(
            ["bash", str(INSTALL_SH)],
            cwd=str(work),
            env={
                **os.environ,
                "LISSOM_REPO": f"http://127.0.0.1:{port}",
                "LISSOM_TARGET": ".claude",
            },
            capture_output=True, text=True, timeout=30,
            input="n\n",  # Decline overwrite
        )

        assert result.returncode == 0
        # Old file should remain unchanged
        assert old_agent.read_text() == "---\nname: old\n---\nold\n"
        assert "Installation cancelled." in result.stdout
    finally:
        server.shutdown()
        for f in dist_dir.glob("*.zip"):
            f.unlink()


def test_install_samples_specs(tmp_path):
    """.lissom/tasks/T1/Specs.md created from template."""
    work = tmp_path / "work"
    work.mkdir()

    dist_dir = REPO_ROOT / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    zip_path = make_install_zip(REPO_ROOT)
    (REPO_ROOT / "dist" / zip_path.name).write_bytes(zip_path.read_bytes())

    server, port = _start_server()

    try:
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
    finally:
        server.shutdown()
        for f in dist_dir.glob("*.zip"):
            f.unlink()


def test_install_adds_gitignore(tmp_path):
    """.gitignore updated with .lissom/ entry."""
    work = tmp_path / "work"
    work.mkdir()

    # Create an existing .gitignore without .lissom/
    (work / ".gitignore").write_text("__pycache__/\n")

    dist_dir = REPO_ROOT / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    zip_path = make_install_zip(REPO_ROOT)
    (REPO_ROOT / "dist" / zip_path.name).write_bytes(zip_path.read_bytes())

    server, port = _start_server()

    try:
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
    finally:
        server.shutdown()
        for f in dist_dir.glob("*.zip"):
            f.unlink()


def test_install_cleans_up_zip(tmp_path):
    """Temporary zip file removed after unzip."""
    work = tmp_path / "work"
    work.mkdir()

    dist_dir = REPO_ROOT / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    zip_path = make_install_zip(REPO_ROOT)
    (REPO_ROOT / "dist" / zip_path.name).write_bytes(zip_path.read_bytes())

    server, port = _start_server()

    try:
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

        # No temporary zip should remain
        assert not any(work.glob("lissom-skills-tmp.zip"))
        assert not any(work.glob("*.zip"))
    finally:
        server.shutdown()
        for f in dist_dir.glob("*.zip"):
            f.unlink()


def test_install_target_claude(tmp_path):
    """LISSOM_TARGET=.claude creates .claude/ with agents and skills."""
    work = tmp_path / "work"
    work.mkdir()

    dist_dir = REPO_ROOT / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    zip_path = make_install_zip(REPO_ROOT, ".claude")
    (REPO_ROOT / "dist" / zip_path.name).write_bytes(zip_path.read_bytes())

    server, port = _start_server()

    try:
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
        assert (work / ".claude" / "skills" / "lissom-auto" / "SKILL.md").is_file()
        assert (work / ".claude" / "templates" / "Specs.md").is_file()
    finally:
        server.shutdown()
        for f in dist_dir.glob("*.zip"):
            f.unlink()


def test_install_target_opencode(tmp_path):
    """LISSOM_TARGET=.opencode creates .opencode/ directory."""
    work = tmp_path / "work"
    work.mkdir()

    dist_dir = REPO_ROOT / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    zip_path = make_install_zip(REPO_ROOT, ".opencode")
    (REPO_ROOT / "dist" / zip_path.name).write_bytes(zip_path.read_bytes())

    server, port = _start_server()

    try:
        result = subprocess.run(
            ["bash", str(INSTALL_SH)],
            cwd=str(work),
            env={
                **os.environ,
                "LISSOM_REPO": f"http://127.0.0.1:{port}",
                "LISSOM_TARGET": ".opencode",
                "LISSOM_YES": "1",
            },
            capture_output=True, text=True, timeout=30,
        )

        assert result.returncode == 0
        assert (work / ".opencode" / "agents" / "lissom-researcher.md").is_file()
    finally:
        server.shutdown()
        for f in dist_dir.glob("*.zip"):
            f.unlink()


def test_install_target_qwen(tmp_path):
    """LISSOM_TARGET=.qwen creates .qwen/ directory."""
    work = tmp_path / "work"
    work.mkdir()

    dist_dir = REPO_ROOT / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    zip_path = make_install_zip(REPO_ROOT, ".qwen")
    (REPO_ROOT / "dist" / zip_path.name).write_bytes(zip_path.read_bytes())

    server, port = _start_server()

    try:
        result = subprocess.run(
            ["bash", str(INSTALL_SH)],
            cwd=str(work),
            env={
                **os.environ,
                "LISSOM_REPO": f"http://127.0.0.1:{port}",
                "LISSOM_TARGET": ".qwen",
                "LISSOM_YES": "1",
            },
            capture_output=True, text=True, timeout=30,
        )

        assert result.returncode == 0
        assert (work / ".qwen" / "agents" / "lissom-researcher.md").is_file()
    finally:
        server.shutdown()
        for f in dist_dir.glob("*.zip"):
            f.unlink()


def test_install_target_gemini(tmp_path):
    """LISSOM_TARGET=.gemini creates .gemini/ directory."""
    work = tmp_path / "work"
    work.mkdir()

    dist_dir = REPO_ROOT / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    zip_path = make_install_zip(REPO_ROOT, ".gemini")
    (REPO_ROOT / "dist" / zip_path.name).write_bytes(zip_path.read_bytes())

    server, port = _start_server()

    try:
        result = subprocess.run(
            ["bash", str(INSTALL_SH)],
            cwd=str(work),
            env={
                **os.environ,
                "LISSOM_REPO": f"http://127.0.0.1:{port}",
                "LISSOM_TARGET": ".gemini",
                "LISSOM_YES": "1",
            },
            capture_output=True, text=True, timeout=30,
        )

        assert result.returncode == 0
        assert (work / ".gemini" / "agents" / "lissom-researcher.md").is_file()
    finally:
        server.shutdown()
        for f in dist_dir.glob("*.zip"):
            f.unlink()


def test_empty_target_dir_preserved(tmp_path):
    """Empty target dir does not trigger overwrite prompt."""
    work = tmp_path / "work"
    work.mkdir()
    (work / ".claude").mkdir()  # Empty dir

    dist_dir = REPO_ROOT / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    zip_path = make_install_zip(REPO_ROOT)
    (REPO_ROOT / "dist" / zip_path.name).write_bytes(zip_path.read_bytes())

    server, port = _start_server()

    try:
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
    finally:
        server.shutdown()
        for f in dist_dir.glob("*.zip"):
            f.unlink()


# ── Remote install test ──────────────────────────────────────────────

def test_remote_install_via_curl(tmp_path):
    """Simulate curl | bash flow with HTTP server serving zips."""
    work = tmp_path / "work"
    work.mkdir()

    # Pre-build zips in the repo root for the server to serve
    dist_dir = REPO_ROOT / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    zip_path = make_install_zip(REPO_ROOT)
    (REPO_ROOT / "dist" / zip_path.name).write_bytes(zip_path.read_bytes())

    server, port = _start_server()

    try:
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
    finally:
        server.shutdown()
        for f in dist_dir.glob("*.zip"):
            f.unlink()


# ── Regression tests: ui.sh prompt functions ────────────────────────

def test_prompt_target_directory_stdout_clean(tmp_path):
    """Regression: prompt_target_directory outputs only the target name to stdout."""
    for target in (".claude", ".opencode", ".qwen", ".gemini"):
        result = subprocess.run(
            ["bash", "-c", f"""
                source scripts/lib/ui.sh
                LISSOM_TARGET={target} prompt_target_directory
            """],
            capture_output=True, text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0
        lines = result.stdout.strip().splitlines()
        assert len(lines) == 1, (
            f"Expected 1 line of stdout (the target name), got {len(lines)}: {lines}\n"
            f"stderr: {result.stderr}"
        )
        assert lines[0] == target, f"stdout should be '{target}', got: {lines[0]!r}"
