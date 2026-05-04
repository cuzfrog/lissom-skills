"""
Test that install.sh and uninstall.sh use only bash 3.2 compatible syntax.

WHY THIS TEST EXISTS:
macOS ships with bash 3.2 as the default shell (due to the GPLv3 licensing change
in bash 4.0). Many developers rely on the system bash, so our install/uninstall
scripts must not use any features introduced in bash 4.0+. If we accidentally use
bash 4+ syntax, the scripts will fail silently or with cryptic errors on a large
portion of macOS machines.

This test acts as a guardrail: any PR that introduces bash 4+ syntax will fail CI
before it reaches users.

Bash 4+ features checked:
- Associative arrays (declare -A)
- Case modification (${var,,}, ${var^^}, ${var,}, ${var^})
- mapfile / readarray builtins
- Globstar (shopt -s globstar)
- Nameref (declare -n)
- ${var@Q} quoting (bash 4.4+)
- ${!prefix@} name matching (bash 4.0+)
- coproc keyword
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"

# Patterns that indicate bash 4+ syntax (not compatible with bash 3.2)
BASH4_PATTERNS = [
    # Associative arrays — introduced in bash 4.0
    (re.compile(r'\bdeclare\s+(-[A-Za-z]*A[A-Za-z]*|-A)\b'), "associative array (declare -A)"),
    (re.compile(r'\bdeclare\s+-gA\b'), "global associative array (declare -gA)"),

    # Case modification operators — introduced in bash 4.0
    (re.compile(r'\$\{[^}]*,,\}'), "lowercase expansion (${var,,})"),
    (re.compile(r'\$\{[^}]*\^\^\}'), "uppercase expansion (${var^^})"),
    (re.compile(r'\$\{[^}]*[^,],\}'), "lowercase first char (${var,})"),
    (re.compile(r'\$\{[^}]*[^\\^]\^\}'), "uppercase first char (${var^})"),

    # mapfile / readarray — introduced in bash 4.0
    (re.compile(r'\bmapfile\b'), "mapfile builtin"),
    (re.compile(r'\breadarray\b'), "readarray builtin"),

    # Globstar — introduced in bash 4.0
    (re.compile(r'shopt\s+-s\s+globstar'), "globstar (shopt -s globstar)"),

    # Nameref — introduced in bash 4.3
    (re.compile(r'\bdeclare\s+(-[A-Za-z]*n[A-Za-z]*|-n)\b'), "nameref (declare -n)"),

    # ${var@Q} quoting — introduced in bash 4.4
    (re.compile(r'\$\{[^}]*@Q\}'), "${var@Q} quoting"),

    # ${!prefix@} name matching — introduced in bash 4.0
    (re.compile(r'\$\{![A-Za-z_][A-Za-z_0-9]*@\}'), "${!prefix@} name matching"),

    # coproc — introduced in bash 4.0
    (re.compile(r'\bcoproc\b'), "coproc keyword"),
]

# Match lines that are pure comments (so we don't flag explanatory text)
COMMENT_LINE_RE = re.compile(r'^\s*#')


def _scan_file(filepath: Path) -> list[tuple[int, str, str]]:
    """Scan a bash script for bash 4+ syntax.

    Returns list of (line_number, matched_pattern_description, line_content).
    """
    violations = []
    content = filepath.read_text()

    for line_num, line in enumerate(content.splitlines(), start=1):
        # Skip comment lines — they are documentation, not executed code
        if COMMENT_LINE_RE.match(line):
            continue

        for pattern, description in BASH4_PATTERNS:
            if pattern.search(line):
                violations.append((line_num, description, line.strip()))

    return violations


def test_install_sh_bash32_compatibility():
    """install.sh must not use any bash 4+ syntax."""
    script = SCRIPTS_DIR / "install.sh"
    assert script.exists(), f"{script} not found"

    violations = _scan_file(script)
    assert not violations, (
        f"install.sh uses bash 4+ syntax (incompatible with macOS bash 3.2):\n"
        + "\n".join(
            f"  Line {ln}: {desc} — {content}"
            for ln, desc, content in violations
        )
    )


def test_uninstall_sh_bash32_compatibility():
    """uninstall.sh must not use any bash 4+ syntax."""
    script = SCRIPTS_DIR / "uninstall.sh"
    assert script.exists(), f"{script} not found"

    violations = _scan_file(script)
    assert not violations, (
        f"uninstall.sh uses bash 4+ syntax (incompatible with macOS bash 3.2):\n"
        + "\n".join(
            f"  Line {ln}: {desc} — {content}"
            for ln, desc, content in violations
        )
    )
