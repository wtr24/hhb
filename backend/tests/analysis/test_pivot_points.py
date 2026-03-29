"""TA-07 pivot point method tests."""
import pytest
from analysis.pivot_points import (
    compute_standard, compute_woodie, compute_camarilla,
    compute_fibonacci, compute_demark, compute_all_methods,
)


PREV_BAR = {"high": 115.0, "low": 108.0, "close": 112.5, "open": 109.0}


def test_standard_pivots():
    result = compute_standard(115.0, 108.0, 112.5)
    assert result["method"] == "standard"
    pp = result["pp"]
    # PP = (115 + 108 + 112.5) / 3 = 111.8333...
    assert abs(pp - 111.8333) < 0.001
    assert result["r1"] > pp > result["s1"]


def test_woodie_pivots():
    result = compute_woodie(115.0, 108.0, 112.5, 109.0)
    assert result["method"] == "woodie"
    pp = result["pp"]
    assert result["r1"] > pp > result["s1"]


def test_camarilla_pivots():
    result = compute_camarilla(115.0, 108.0, 112.5)
    assert result["method"] == "camarilla"
    assert "r4" in result
    assert "s4" in result
    assert result["r4"] > result["r3"] > result["r2"] > result["r1"]
    assert result["s4"] < result["s3"] < result["s2"] < result["s1"]


def test_fibonacci_pivots():
    result = compute_fibonacci(115.0, 108.0, 112.5)
    assert result["method"] == "fibonacci"
    r3, r2, r1, pp, s1, s2, s3 = (
        result["r3"], result["r2"], result["r1"], result["pp"],
        result["s1"], result["s2"], result["s3"],
    )
    assert r3 > r2 > r1 > pp > s1 > s2 > s3


def test_demark_pivots():
    result = compute_demark(115.0, 108.0, 112.5, 109.0)
    assert result["method"] == "demark"
    assert "pp" in result
    assert "r1" in result
    assert "s1" in result
    assert result["r2"] is None
    assert result["r3"] is None


def test_all_methods_return_pp_s1_r1():
    results = compute_all_methods(115.0, 108.0, 112.5, 109.0)
    assert len(results) == 5
    for m in results:
        assert "pp" in m
        assert "r1" in m
        assert "s1" in m
