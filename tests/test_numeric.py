import pandas as pd
import pytest

from smart_profiler.analysis.numeric import analyze


# --- Data contract ---

def test_result_has_required_keys():
    result = analyze(pd.Series([1.0, 2.0, 3.0]), "col")
    assert set(result.keys()) == {"column", "type", "count", "missing", "missing_pct", "stats", "flags"}


def test_stats_has_required_keys():
    result = analyze(pd.Series([1.0, 2.0, 3.0]), "col")
    assert set(result["stats"].keys()) == {"mean", "median", "std", "min", "max", "q25", "q75"}


def test_type_field_is_numeric():
    result = analyze(pd.Series([1.0, 2.0]), "col")
    assert result["type"] == "numeric"


# --- Stat correctness ---

def test_basic_stats_are_correct():
    result = analyze(pd.Series([1.0, 2.0, 3.0, 4.0, 5.0]), "col")
    s = result["stats"]
    assert s["mean"] == pytest.approx(3.0)
    assert s["median"] == pytest.approx(3.0)
    assert s["min"] == pytest.approx(1.0)
    assert s["max"] == pytest.approx(5.0)
    assert s["q25"] == pytest.approx(2.0)
    assert s["q75"] == pytest.approx(4.0)


def test_missing_count_and_pct_are_correct():
    result = analyze(pd.Series([1.0, None, 3.0, None]), "col")
    assert result["missing"] == 2
    assert result["missing_pct"] == pytest.approx(50.0)


def test_stats_exclude_null_values():
    result = analyze(pd.Series([10.0, None, None]), "col")
    assert result["stats"]["mean"] == pytest.approx(10.0)
    assert result["stats"]["min"] == pytest.approx(10.0)
    assert result["stats"]["max"] == pytest.approx(10.0)


# --- Edge cases ---

def test_all_null_column_returns_none_stats():
    result = analyze(pd.Series([None, None, None], dtype=float), "col")
    for value in result["stats"].values():
        assert value is None


def test_all_null_column_raises_all_missing_flag():
    result = analyze(pd.Series([None, None], dtype=float), "col")
    flag_names = [f["name"] for f in result["flags"]]
    assert "all_missing" in flag_names


def test_single_value_column_raises_constant_flag():
    result = analyze(pd.Series([7.0, 7.0, 7.0]), "col")
    flag_names = [f["name"] for f in result["flags"]]
    assert "constant" in flag_names


def test_high_missing_flag_raised_above_threshold():
    series = pd.Series([1.0] + [None] * 9)  # 90% missing
    result = analyze(series, "col")
    flag_names = [f["name"] for f in result["flags"]]
    assert "high_missing" in flag_names


def test_high_missing_flag_not_raised_below_threshold():
    series = pd.Series([1.0, 2.0, 3.0, 4.0, None])  # 20% missing
    result = analyze(series, "col")
    flag_names = [f["name"] for f in result["flags"]]
    assert "high_missing" not in flag_names


def test_clean_column_has_no_flags():
    result = analyze(pd.Series([1.0, 2.0, 3.0, 4.0, 5.0]), "col")
    assert result["flags"] == []


def test_all_missing_and_high_missing_are_mutually_exclusive():
    result = analyze(pd.Series([None, None], dtype=float), "col")
    flag_names = [f["name"] for f in result["flags"]]
    assert not ("all_missing" in flag_names and "high_missing" in flag_names)


def test_flag_carries_triggering_value():
    series = pd.Series([1.0] + [None] * 9)
    result = analyze(series, "col")
    high_missing_flag = next(f for f in result["flags"] if f["name"] == "high_missing")
    assert high_missing_flag["value"] == pytest.approx(result["missing_pct"])
