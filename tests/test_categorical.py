import pandas as pd
import pytest

from smart_profiler.analysis.categorical import analyze


# --- Data contract ---

def test_result_has_required_keys():
    result = analyze(pd.Series(["a", "b", "c"]), "col")
    assert set(result.keys()) == {"column", "type", "count", "missing", "missing_pct", "stats", "flags"}


def test_stats_has_required_keys():
    result = analyze(pd.Series(["a", "b"]), "col")
    assert set(result["stats"].keys()) == {"unique_count", "top_values"}


def test_type_field_is_categorical():
    result = analyze(pd.Series(["x", "y"]), "col")
    assert result["type"] == "categorical"


# --- Stat correctness ---

def test_unique_count_is_correct():
    result = analyze(pd.Series(["a", "b", "a", "c"]), "col")
    assert result["stats"]["unique_count"] == 3


def test_top_values_are_ordered_by_frequency():
    result = analyze(pd.Series(["a", "a", "a", "b", "b", "c"]), "col")
    top = result["stats"]["top_values"]
    assert top[0]["value"] == "a"
    assert top[1]["value"] == "b"
    assert top[2]["value"] == "c"


def test_top_values_pct_uses_non_null_count_as_denominator():
    # 2 out of 4 non-null values are "a" → 50%, not 40% of total 5 rows
    result = analyze(pd.Series(["a", "a", "b", "b", None]), "col")
    top = result["stats"]["top_values"]
    a_entry = next(t for t in top if t["value"] == "a")
    assert a_entry["pct"] == pytest.approx(50.0)


def test_top_values_capped_at_five():
    result = analyze(pd.Series(["a", "b", "c", "d", "e", "f", "g"]), "col")
    assert len(result["stats"]["top_values"]) == 5


def test_top_values_fewer_than_five_when_column_has_fewer_unique():
    result = analyze(pd.Series(["a", "b", "c"]), "col")
    assert len(result["stats"]["top_values"]) == 3


def test_missing_count_excludes_nulls_from_top_values():
    result = analyze(pd.Series(["a", None, None]), "col")
    all_values = [t["value"] for t in result["stats"]["top_values"]]
    assert None not in all_values


def test_missing_count_and_pct_are_correct():
    result = analyze(pd.Series(["a", "b", None, None]), "col")
    assert result["missing"] == 2
    assert result["missing_pct"] == pytest.approx(50.0)


# --- Edge cases ---

def test_all_null_column_returns_empty_stats():
    result = analyze(pd.Series([None, None, None]), "col")
    assert result["stats"]["unique_count"] == 0
    assert result["stats"]["top_values"] == []


def test_all_null_column_raises_all_missing_flag():
    result = analyze(pd.Series([None, None]), "col")
    flag_names = [f["name"] for f in result["flags"]]
    assert "all_missing" in flag_names


def test_single_value_column_raises_constant_flag():
    result = analyze(pd.Series(["x", "x", "x"]), "col")
    flag_names = [f["name"] for f in result["flags"]]
    assert "constant" in flag_names


def test_high_cardinality_flag_raised_when_nearly_all_unique():
    series = pd.Series([f"id_{i}" for i in range(100)])
    result = analyze(series, "col")
    flag_names = [f["name"] for f in result["flags"]]
    assert "high_cardinality" in flag_names


def test_high_cardinality_flag_not_raised_for_low_cardinality():
    result = analyze(pd.Series(["a", "b", "a", "b", "a"]), "col")
    flag_names = [f["name"] for f in result["flags"]]
    assert "high_cardinality" not in flag_names


def test_constant_and_high_cardinality_are_mutually_exclusive():
    result = analyze(pd.Series(["x", "x", "x"]), "col")
    flag_names = [f["name"] for f in result["flags"]]
    assert not ("constant" in flag_names and "high_cardinality" in flag_names)


def test_clean_column_has_no_flags():
    result = analyze(pd.Series(["a", "b", "c", "a", "b"]), "col")
    assert result["flags"] == []


def test_high_missing_flag_raised_above_threshold():
    series = pd.Series(["a"] + [None] * 9)  # 90% missing
    result = analyze(series, "col")
    flag_names = [f["name"] for f in result["flags"]]
    assert "high_missing" in flag_names
