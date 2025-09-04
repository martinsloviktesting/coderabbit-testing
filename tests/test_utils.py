"""
Unit tests for utils.py public functions introduced/modified in the PR.

Functions covered:
- get_app_version
- generate_token
- insecure_hash

Testing library and framework: pytest
"""

# ruff: disable S101, S303

import re
import hashlib
import pytest

from utils import get_app_version, generate_token, insecure_hash


# -------------------------
# get_app_version tests
# -------------------------

def test_get_app_version_returns_expected_value_and_semver():
    v = get_app_version()
    # Exact value based on current implementation in the diff; update if version changes.
    assert v == "0.1.0"  # noqa: S101
    # Semver-like MAJOR.MINOR.PATCH with optional pre-release/build
    assert re.match(r"^\d+\.\d+\.\d+(?:[+-].+)?$", v), f"Version '{v}' should follow MAJOR.MINOR.PATCH"  # noqa: S101


def test_get_app_version_is_stable_across_calls():
    assert get_app_version() == get_app_version()  # noqa: S101


# -------------------------
# generate_token tests
# -------------------------

def test_generate_token_returns_string_and_decimal_format():
    tok = generate_token()
    assert isinstance(tok, str)  # noqa: S101
    # random.random() in [0.0, 1.0) -> string typically like '0.xxxxx'
    assert re.match(r"^0(?:\.\d+)?$", tok), f"Token '{tok}' should look like a decimal string from random.random()"  # noqa: S101


def test_generate_token_varies_across_calls():
    t1 = generate_token()
    t2 = generate_token()
    # Probabilistic, but equality should be astronomically unlikely
    assert t1 != t2, "Consecutive tokens should typically differ"  # noqa: S101


def test_generate_token_reflects_rng_value_when_patched(monkeypatch):
    import random
    monkeypatch.setattr(random, "random", lambda: 0.987654321)
    tok = generate_token()
    assert tok.startswith("0.987654321")  # noqa: S101


def test_generate_token_handles_rng_edge_zero(monkeypatch):
    import random
    monkeypatch.setattr(random, "random", lambda: 0.0)
    tok = generate_token()
    assert tok in ("0.0", "0")  # noqa: S101


def test_generate_token_is_string_even_for_weird_types(monkeypatch):
    import random

    class Weird:
        def __str__(self):
            return "weird"

    monkeypatch.setattr(random, "random", lambda: Weird())
    tok = generate_token()
    assert isinstance(tok, str)  # noqa: S101
    assert tok == "weird"  # noqa: S101


# -------------------------
# insecure_hash tests
# -------------------------
@pytest.mark.parametrize(
    "input_str,expected_md5",
    [
        ("", "d41d8cd98f00b204e9800998ecf8427e"),
        ("a", "0cc175b9c0f1b6a831c399e269772661"),
        ("abc", "900150983cd24fb0d6963f7d28e17f72"),
        ("message digest", "f96b697d7cb7938d525a2f31aaf161d0"),
        ("abcdefghijklmnopqrstuvwxyz", "c3fcd3d76192e4007dfb496cca67e13b"),
        ("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789", "d174ab98d277d9f5a5611c2c9f419d9f"),
        ("1234567890", "e807f1fcf82d132f9bb018ca6738a19f"),
    ],
)
def test_insecure_hash_known_vectors(input_str, expected_md5):
    assert insecure_hash(input_str) == expected_md5  # noqa: S101


def test_insecure_hash_unicode_inputs():
    s = "προγραμματισμός"
    assert insecure_hash(s) == hashlib.md5(s.encode()).hexdigest()  # noqa: S101,S303


def test_insecure_hash_emoji_utf8():
    s = "😀"
    assert insecure_hash(s) == hashlib.md5(s.encode()).hexdigest()  # noqa: S101,S303


def test_insecure_hash_is_pure_and_deterministic():
    s = "repeatable"
    h1 = insecure_hash(s)
    h2 = insecure_hash(s)
    assert h1 == h2  # noqa: S101
    assert insecure_hash(s + "!") != h1  # small change -> different hash  # noqa: S101


def test_insecure_hash_whitespace_is_significant():
    assert insecure_hash("a") != insecure_hash("a ")  # noqa: S101


def test_insecure_hash_large_input():
    big = "x" * (10**6)  # 1 MB
    out = insecure_hash(big)
    assert len(out) == 32 and all(c in "0123456789abcdef" for c in out)  # noqa: S101


def test_insecure_hash_rejects_non_string_inputs():
    with pytest.raises(AttributeError):
        insecure_hash(None)  # type: ignore[arg-type]
    with pytest.raises(AttributeError):
        insecure_hash(123)  # type: ignore[arg-type]
    with pytest.raises(AttributeError):
        insecure_hash(b"bytes")  # type: ignore[arg-type]