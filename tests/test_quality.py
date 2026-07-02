import pandas as pd
import pytest

from smart_profiler.quality import check


def test_result_has_required_keys():
    result = check(pd.DataFrame({"a": [1, 2, 3]}))
    assert set(result.keys()) == {
        "duplicate_rows", "duplicate_row_pct",
        "missing_cells", "total_cells", "overall_missing_pct",
    }


def test_no_duplicates_in_clean_dataframe():
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    result = check(df)
    assert result["duplicate_rows"] == 0
    assert result["duplicate_row_pct"] == pytest.approx(0.0)


def test_duplicate_rows_are_counted_correctly():
    df = pd.DataFrame({"a": [1, 2, 1], "b": ["x", "y", "x"]})
    result = check(df)
    assert result["duplicate_rows"] == 1


def test_duplicate_row_pct_is_correct():
    df = pd.DataFrame({"a": [1, 1, 1, 1]})  # 3 duplicates out of 4 rows
    result = check(df)
    assert result["duplicate_rows"] == 3
    assert result["duplicate_row_pct"] == pytest.approx(75.0)


def test_total_cells_is_correct():
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4], "c": [5, 6]})
    result = check(df)
    assert result["total_cells"] == 6


def test_missing_cells_counted_correctly():
    df = pd.DataFrame({"a": [1, None, 3], "b": [None, None, 6]})
    result = check(df)
    assert result["missing_cells"] == 3


def test_overall_missing_pct_is_correct():
    df = pd.DataFrame({"a": [1, None], "b": [None, None]})  # 3 of 4 cells missing
    result = check(df)
    assert result["overall_missing_pct"] == pytest.approx(75.0)


def test_empty_dataframe_returns_zeros():
    result = check(pd.DataFrame())
    assert result["duplicate_rows"] == 0
    assert result["missing_cells"] == 0
    assert result["overall_missing_pct"] == pytest.approx(0.0)
