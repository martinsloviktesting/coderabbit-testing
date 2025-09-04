# ruff: noqa: S101
# ---------------------------------------------------------------------------
# Additional unit tests for apply_strategy
# Test framework: pytest
# These tests cover happy paths, edge cases, unexpected inputs, and failures.
# ---------------------------------------------------------------------------
import pytest
from strategy import apply_strategy

def test_apply_strategy_add_basic_cases():
    cases = [
        (2, 3, 5),
        (-1, 5, 4),
        (0, 0, 0),
        (123456789123456789, 1, 123456789123456790),
    ]
    for x, y, expected in cases:
        assert apply_strategy("add", x, y) == expected

def test_apply_strategy_mul_basic_cases():
    cases = [
        (2, 3, 6),
        (-4, 2, -8),
        (0, 9999, 0),
        (7, -6, -42),
    ]
    for x, y, expected in cases:
        assert apply_strategy("mul", x, y) == expected

def test_apply_strategy_pow_basic_and_edges():
    # Basic powers
    assert apply_strategy("pow", 2, 3) == 8
    assert apply_strategy("pow", 5, 0) == 1
    assert apply_strategy("pow", 0, 5) == 0
    # 0 ** 0 edge case
    assert apply_strategy("pow", 0, 0) == 1
    # Negative base behavior
    assert apply_strategy("pow", -2, 3) == -8
    assert apply_strategy("pow", -2, 2) == 4

def test_apply_strategy_pow_negative_exponent_returns_float():
    result = apply_strategy("pow", 2, -1)
    assert result == pytest.approx(0.5)

def test_unknown_kind_returns_x_unmodified():
    # Unknown, empty, and case-mismatched kinds should fall back to returning x
    for kind in ("div", "", "ADD"):
        assert apply_strategy(kind, 7, 3) == 7

def test_non_string_kind_gracefully_returns_x():
    for kind in (None, 0, ["add"], {"kind": "add"}):
        assert apply_strategy(kind, 42, 99) == 42

def test_add_with_strings_concatenates_when_given_strings():
    assert apply_strategy("add", "a", "b") == "ab"

def test_mul_with_string_and_int_repeats_string():
    assert apply_strategy("mul", "hi", 3) == "hihihi"

def test_mul_with_two_strings_raises_typeerror():
    with pytest.raises(TypeError):
        apply_strategy("mul", "a", "b")

def test_pow_with_invalid_operand_types_raises_typeerror():
    with pytest.raises(TypeError):
        apply_strategy("pow", "a", 2)
    with pytest.raises(TypeError):
        apply_strategy("pow", 2, "b")