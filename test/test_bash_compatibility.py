"""
Test that install.sh and uninstall.sh use only bash 3.2 compatible syntax and
do not rely on non-portable command-line tool flags.

WHY THIS TEST EXISTS:
macOS ships with bash 3.2 as the default shell (due to the GPLv3 licensing change
in bash 4.0). Many developers rely on the system bash, so our install/uninstall
scripts must not use any features introduced in bash 4.0+. If we accidentally use
bash 4+ syntax, the scripts will fail silently or with cryptic errors on a large
portion of macOS machines.

Furthermore, many command-line tools (sed, sort, head, etc.) have different
flags on BSD/macOS vs GNU/Linux. A script that works on Linux may fail on macOS
due to these differences.

This test acts as a guardrail: any PR that introduces bash 4+ syntax or
non-portable command usage will fail CI before it reaches users.

Bash 4+ features checked:
- Associative arrays (declare -A, local -A)
- Case modification (${var,,}, ${var^^}, ${var,}, ${var^})
- mapfile / readarray builtins
- Globstar (shopt -s globstar)
- Lastpipe (shopt -s lastpipe)
- Nameref (declare -n, local -n)
- ${var@Q} quoting (bash 4.4+)
- ${!prefix@} / ${!prefix*} name matching (bash 4.0+)
- coproc keyword
- $BASHPID variable
- &>> redirect (stdout+stderr append)
- ;;& and ;& case fallthrough
- [[ -v var ]] variable is set check (bash 4.2+)
- read -t with fractional timeout (bash 4.0+)
- $EPOCHSECONDS, $EPOCHREALTIME (bash 5.0+)
- $BASH_ARGV0 (bash 5.0+)

Cross-platform command compatibility checked:
- sed -i without portable backup extension
- sed -r (GNU-only flag)
- sort -V (GNU-only flag)
- head -c (not available on BSD)
- realpath (not available on macOS by default)
- timeout (not available on macOS by default)
- readlink -f (differs on BSD)
- uname -o (not available on BSD)
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"

# Match lines that are pure comments (so we don't flag explanatory text)
COMMENT_LINE_RE = re.compile(r"^\s*#")

# ---------------------------------------------------------------------------
# Patterns: bash 4+ syntax (not compatible with bash 3.2)
# ---------------------------------------------------------------------------
BASH4_PATTERNS = [
    # Associative arrays — bash 4.0
    (
        re.compile(r"\bdeclare\s+(-[A-Za-z]*A[A-Za-z]*|-A)\b"),
        "associative array (declare -A)",
    ),
    (
        re.compile(r"\blocal\s+(-[A-Za-z]*A[A-Za-z]*|-A)\b"),
        "associative array (local -A)",
    ),
    # Case modification operators — bash 4.0
    (re.compile(r"\$\{[^}]*,,\}"), "lowercase expansion (${var,,})"),
    (re.compile(r"\$\{[^}]*\^\^\}"), "uppercase expansion (${var^^})"),
    (re.compile(r"\$\{[^}]*[^,],\}"), "lowercase first char (${var,})"),
    (re.compile(r"\$\{[^}]*[^\\^]\^\}"), "uppercase first char (${var^})"),
    # mapfile / readarray — bash 4.0
    (re.compile(r"\bmapfile\b"), "mapfile builtin"),
    (re.compile(r"\breadarray\b"), "readarray builtin"),
    # Globstar — bash 4.0
    (re.compile(r"shopt\s+-s\s+globstar"), "globstar (shopt -s globstar)"),
    # Lastpipe — bash 4.0
    (re.compile(r"shopt\s+-s\s+lastpipe"), "lastpipe (shopt -s lastpipe)"),
    # Nameref — bash 4.3
    (
        re.compile(r"\bdeclare\s+(-[A-Za-z]*n[A-Za-z]*|-n)\b"),
        "nameref (declare -n)",
    ),
    (
        re.compile(r"\blocal\s+(-[A-Za-z]*n[A-Za-z]*|-n)\b"),
        "nameref (local -n)",
    ),
    # ${var@Q} quoting — bash 4.4
    (re.compile(r"\$\{[^}]*@Q\}"), "${var@Q} quoting"),
    # ${!prefix@} / ${!prefix*} name matching — bash 4.0
    (
        re.compile(r"\$\{![A-Za-z_][A-Za-z_0-9]*[@*]\}"),
        "${!prefix@/prefix*} name matching",
    ),
    # coproc — bash 4.0
    (re.compile(r"\bcoproc\b"), "coproc keyword"),
    # $BASHPID — bash 4.0
    (re.compile(r"\$BASHPID\b"), "$BASHPID variable"),
    (re.compile(r"\$\{BASHPID\b"), "${BASHPID} variable"),
    # &>> redirect — bash 4.0
    (re.compile(r"&>>"), "&>> redirect (stdout+stderr append)"),
    # ;;& case fallthrough — bash 4.0
    (re.compile(r";;&"), ";;& case fallthrough"),
    # ;& case fallthrough — bash 4.0
    (re.compile(r";&(?:[\s\)]|$)"), ";& case fallthrough"),
    # [[ -v var ]] — bash 4.2
    (re.compile(r"\[\[\s+-v\s+"), "[[ -v var ]] (bash 4.2+)"),
    # read -t with fractional timeout — bash 4.0
    (
        re.compile(r"\bread\b[^;]*?-t\s+\d+\.\d+"),
        "read -t with fractional timeout (bash 4.0+)",
    ),
    # $EPOCHSECONDS / $EPOCHREALTIME — bash 5.0
    (re.compile(r"\$EPOCHSECONDS\b"), "$EPOCHSECONDS variable (bash 5.0+)"),
    (re.compile(r"\$EPOCHREALTIME\b"), "$EPOCHREALTIME variable (bash 5.0+)"),
    # $BASH_ARGV0 — bash 5.0
    (re.compile(r"\$BASH_ARGV0\b"), "$BASH_ARGV0 variable (bash 5.0+)"),
]

# ---------------------------------------------------------------------------
# Patterns: cross-platform command compatibility (GNU vs BSD)
# ---------------------------------------------------------------------------
CROSS_PLATFORM_PATTERNS = [
    # sed -i without a backup extension attached.  BSD sed on macOS requires
    # an explicit backup extension argument; bare `sed -i` is not portable.
    # The truly portable approach is to avoid -i entirely:
    #   sed 's/.../.../' file > tmp && mv tmp file
    #
    # Note: `sed -i ''` (empty extension) IS portable, so we exclude it
    # via negative lookaheads.  The pattern is assembled from multiple
    # string pieces to avoid Python deprecation warnings about invalid
    # escape sequences.
    (
        re.compile(
            r"\bsed\b[^;]*?\s-i(?=\s)"
            + r"(?!\s*'')(?!\s*"
            + '""'
            + r")(?=\s|$)"
        ),
        "sed -i without backup extension "
        "(BSD sed requires extension; use tempfile approach instead)",
    ),
    # sed -r — GNU-only flag for extended regex. BSD/macOS sed uses -E instead.
    (re.compile(r"\bsed\b[^;]*?\s-[a-zA-Z]*r[a-zA-Z]*\b"), "sed -r (GNU only; use -E on macOS)"),
    # sort -V (version sort) — GNU-only, not available on macOS.
    (re.compile(r"\bsort\b[^;]*?\s-V\b"), "sort -V (GNU only; not available on macOS)"),
    # head -c — not supported on BSD/macOS.
    (re.compile(r"\bhead\b[^;]*?\s-c\b"), "head -c (not available on BSD/macOS)"),
    # realpath — not installed on macOS by default (install coreutils for grealpath).
    (re.compile(r"\brealpath\b"), "realpath (not available on macOS by default)"),
    # timeout — not installed on macOS by default (install coreutils for gtimeout).
    (re.compile(r"\btimeout\b"), "timeout (not available on macOS by default)"),
    # readlink -f — flag differs between GNU and BSD.
    (re.compile(r"\breadlink\b[^;]*?\s-f\b"), "readlink -f (not available on BSD/macOS)"),
    # uname -o — BSD uname does not support -o.
    (re.compile(r"\buname\b[^;]*?\s-o\b"), "uname -o (not available on BSD/macOS)"),
]


def _scan_file(
    filepath: Path,
    patterns: list[tuple[re.Pattern, str]],
) -> list[tuple[int, str, str]]:
    """Scan a bash script for the given patterns.

    Skips pure-comment lines.

    Returns list of (line_number, matched_pattern_description, line_content).
    """
    violations = []
    content = filepath.read_text()

    for line_num, line in enumerate(content.splitlines(), start=1):
        if COMMENT_LINE_RE.match(line):
            continue

        for pattern, description in patterns:
            if pattern.search(line):
                violations.append((line_num, description, line.strip()))

    return violations


def _assert_no_violations(script: Path, category: str, violations: list) -> None:
    """Assert no violations, with a formatted error message on failure."""
    assert not violations, (
        f"{script.name} has {category} violations "
        f"(incompatible with macOS bash 3.2):\n"
        + "\n".join(
            f"  Line {ln}: {desc} — {content}" for ln, desc, content in violations
        )
    )


# ---------------------------------------------------------------------------
# Tests: bash 4+ syntax (bash version compatibility)
# ---------------------------------------------------------------------------


def test_install_sh_bash32_compatibility():
    """install.sh must not use any bash 4+ syntax."""
    script = SCRIPTS_DIR / "install.sh"
    assert script.exists(), f"{script} not found"
    violations = _scan_file(script, BASH4_PATTERNS)
    _assert_no_violations(script, "bash 4+ syntax", violations)


def test_uninstall_sh_bash32_compatibility():
    """uninstall.sh must not use any bash 4+ syntax."""
    script = SCRIPTS_DIR / "uninstall.sh"
    assert script.exists(), f"{script} not found"
    violations = _scan_file(script, BASH4_PATTERNS)
    _assert_no_violations(script, "bash 4+ syntax", violations)


# ---------------------------------------------------------------------------
# Tests: cross-platform command compatibility (GNU vs BSD)
# ---------------------------------------------------------------------------


def test_install_sh_cross_platform_compatibility():
    """install.sh must not use GNU-only command flags."""
    script = SCRIPTS_DIR / "install.sh"
    assert script.exists(), f"{script} not found"
    violations = _scan_file(script, CROSS_PLATFORM_PATTERNS)
    _assert_no_violations(script, "cross-platform command", violations)


def test_uninstall_sh_cross_platform_compatibility():
    """uninstall.sh must not use GNU-only command flags."""
    script = SCRIPTS_DIR / "uninstall.sh"
    assert script.exists(), f"{script} not found"
    violations = _scan_file(script, CROSS_PLATFORM_PATTERNS)
    _assert_no_violations(script, "cross-platform command", violations)
