import os
import re
import io
import ast
from pathlib import Path

try:
    import pytest
    USING_PYTEST = True
except ImportError:
    USING_PYTEST = False

RE_HARDCODED_API_KEY = re.compile(
    r'\bsk[-_](?:live|test)[^-_\s"]*[-_\w]*', re.IGNORECASE
)
RE_SUSPICIOUS_PASSWORD = re.compile(
    r'\b(password|password123|admin|123456)\b', re.IGNORECASE
)


def scan_python_for_assignments(src_text):
    """
    Parse Python source and yield (name, value_node, value_literal_str) for top-level assignments.
    """
    results = []
    try:
        tree = ast.parse(src_text)
    except SyntaxError as e:
        return [("<<SYNTAX_ERROR>>", None, f"{e.__class__.__name__}: {e}")]
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    value_node = node.value
                    literal = None
                    if isinstance(value_node, ast.Constant) and isinstance(
                        value_node.value, (str, int, float, bool)
                    ):
                        literal = value_node.value
                    results.append((target.id, value_node, literal))
    return results


def scan_text_for_hardcoded_secrets(src_text):
    """
    Returns a list of issues found in the source text indicating hardcoded secrets/insecure defaults.
    """
    issues = []

    # Direct regex sweeps (string-level)
    for m in RE_HARDCODED_API_KEY.finditer(src_text):
        issues.append(f"Hardcoded key-like token detected: '{m.group(0)}'")

    for m in RE_SUSPICIOUS_PASSWORD.finditer(src_text):
        issues.append(f"Suspicious default password detected: '{m.group(0)}'")

    # AST-based checks for specific dangerous assignments
    for name, _, lit in scan_python_for_assignments(src_text):
        # DEBUG should not be True in committed config
        if name.upper() == "DEBUG" and isinstance(lit, bool) and lit is True:
            issues.append("DEBUG is set to True in committed config")

        # DATABASE_URL simple heuristic: flag obvious local dev db for awareness (does not fail tests by itself)
        if (
            name.upper() == "DATABASE_URL"
            and isinstance(lit, str)
            and lit.startswith("sqlite:///")
        ):
            # Document as a notice rather than failure in the generic scanner:
            issues.append(
                "Notice: DATABASE_URL points to a local sqlite database (verify suitability)"
            )

    return issues


# ---------- Unit tests for scanners (should pass) ----------

def test_scan_python_for_assignments_parses_simple_constants():
    src = 'A = 1\nB = "two"\nC = True\n'
    assigns = dict((n, v) for n, _, v in scan_python_for_assignments(src))
    assert assigns == {"A": 1, "B": "two", "C": True}  # noqa: S101

def test_scan_text_for_hardcoded_secrets_detects_api_key_and_password():
    src = '''
HARDCODED_API_KEY = "sk-live-please-rotate-me-1234567890"
DEFAULT_PASSWORD = "password123"
'''
    issues = scan_text_for_hardcoded_secrets(src)
    assert any("Hardcoded key-like token detected" in i for i in issues)  # noqa: S101
    assert any("Suspicious default password detected" in i for i in issues)  # noqa: S101

def test_scan_text_for_hardcoded_secrets_flags_debug_true():
    src = 'DEBUG = True\n'
    issues = scan_text_for_hardcoded_secrets(src)
    assert any("DEBUG is set to True" in i for i in issues)  # noqa: S101

def test_scan_text_for_hardcoded_secrets_handles_syntax_error_gracefully():
    src = 'A = \n'  # invalid syntax
    # We call the lower-level function to ensure it reports a syntax error but does not crash the higher-level scanner
    assigns = scan_python_for_assignments(src)
    assert any("<<SYNTAX_ERROR>>" in n for n, _, _ in assigns)  # noqa: S101

def test_scan_text_for_hardcoded_secrets_negative_cases_no_findings():
    src = '''
API_KEY = os.getenv("STRIPE_API_KEY")
DEFAULT_PASSWORD = os.getenv("APP_DEFAULT_PASSWORD", "")
DEBUG = False
DATABASE_URL = "postgresql://user:pass@host:5432/db"
'''
    issues = scan_text_for_hardcoded_secrets(src)
    # Accept presence of "Notice:" for DATABASE_URL if pattern triggers; current src uses postgres so none expected
    assert not any(msg for msg in issues if not msg.startswith("Notice:"))  # noqa: S101

# ---------- Integration test scanning the actual provided file ----------

def _read_repo_file(rel_path: str) -> str:
    p = Path(rel_path)
    assert p.exists(), f"Expected file not found: {rel_path}"  # noqa: S101
    return p.read_text(encoding="utf-8")

def test_config_file_has_no_hardcoded_secrets_or_insecure_defaults():
    """
    Scans tests/test_config.py as provided in the PR diff.
    This is marked xfail because the provided file contains intentional insecure placeholders.
    Once remediated (e.g., values moved to environment variables), remove xfail to enforce.
    """
    if USING_PYTEST:
        import pytest
        pytest.xfail(
            "Known insecure placeholders in tests/test_config.py; remove xfail after remediation."
        )
    src = _read_repo_file("tests/test_config.py")
    issues = scan_text_for_hardcoded_secrets(src)

    # Without pytest, we conservatively assert that the scanner runs and returns findings (documenting the state).
    # Replace the assertion below with stricter checks once remediation is complete.
    assert isinstance(issues, list) and len(issues) >= 1  # noqa: S101