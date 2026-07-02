import json
import textwrap

import pytest

from smart_profiler import profiler


def _write_csv(tmp_path, content: str) -> str:
    path = tmp_path / "data.csv"
    path.write_text(textwrap.dedent(content).strip())
    return str(path)


# --- Problematic dataset ---

@pytest.fixture
def problematic_csv(tmp_path):
    return _write_csv(tmp_path, """
        id,age,status,score
        1,25,active,8.0
        2,,active,7.5
        3,,active,
        4,30,active,9.0
        1,25,active,8.0
    """)


def test_profile_has_required_top_level_keys(problematic_csv):
    result = profiler.profile(problematic_csv)
    assert set(result.keys()) == {"row_count", "column_count", "columns", "quality", "recommendations"}


def test_row_and_column_counts_are_correct(problematic_csv):
    result = profiler.profile(problematic_csv)
    assert result["row_count"] == 5
    assert result["column_count"] == 4


def test_duplicate_rows_detected(problematic_csv):
    result = profiler.profile(problematic_csv)
    assert result["quality"]["duplicate_rows"] == 1


def test_high_missing_column_produces_recommendation(problematic_csv):
    result = profiler.profile(problematic_csv)
    types = [r["type"] for r in result["recommendations"]]
    assert "high_missing" in types


def test_high_missing_recommendation_names_affected_column(problematic_csv):
    result = profiler.profile(problematic_csv)
    affected = [r["column"] for r in result["recommendations"] if r["type"] == "high_missing"]
    assert "age" in affected


def test_high_cardinality_column_produces_recommendation(tmp_path):
    path = _write_csv(tmp_path, """
        user_token,score
        tok_001,8.0
        tok_002,7.5
        tok_003,9.0
        tok_004,6.5
        tok_005,8.5
        tok_006,7.0
        tok_007,9.5
        tok_008,6.0
        tok_009,8.2
        tok_010,7.8
    """)
    result = profiler.profile(path)
    types = [r["type"] for r in result["recommendations"]]
    assert "high_cardinality" in types


def test_duplicate_rows_produce_recommendation(problematic_csv):
    result = profiler.profile(problematic_csv)
    types = [r["type"] for r in result["recommendations"]]
    assert "duplicate_rows" in types


def test_recommendation_schema_has_required_fields(problematic_csv):
    result = profiler.profile(problematic_csv)
    required_keys = {"type", "severity", "column", "triggering_value", "message"}
    for rec in result["recommendations"]:
        assert set(rec.keys()) == required_keys


def test_dataset_level_recommendation_has_null_column(problematic_csv):
    result = profiler.profile(problematic_csv)
    duplicate_rec = next(r for r in result["recommendations"] if r["type"] == "duplicate_rows")
    assert duplicate_rec["column"] is None


def test_recommendation_severity_is_valid_value(problematic_csv):
    result = profiler.profile(problematic_csv)
    valid_severities = {"high", "medium", "low"}
    for rec in result["recommendations"]:
        assert rec["severity"] in valid_severities


# --- Clean dataset ---

@pytest.fixture
def clean_csv(tmp_path):
    return _write_csv(tmp_path, """
        age,score,category
        30,8.5,A
        25,7.0,B
        35,9.0,A
        28,6.5,B
        32,8.0,A
    """)


def test_clean_dataset_produces_no_recommendations(clean_csv):
    result = profiler.profile(clean_csv)
    assert result["recommendations"] == []


def test_clean_dataset_has_no_duplicates(clean_csv):
    result = profiler.profile(clean_csv)
    assert result["quality"]["duplicate_rows"] == 0


def test_clean_dataset_has_no_missing_cells(clean_csv):
    result = profiler.profile(clean_csv)
    assert result["quality"]["missing_cells"] == 0


# --- JSON serialization ---

def test_json_written_to_file_is_valid_and_complete(problematic_csv, tmp_path):
    out = tmp_path / "report.json"
    profiler.run(problematic_csv, output_format="json", output_path=str(out))
    assert out.exists()
    parsed = json.loads(out.read_text())
    assert "columns" in parsed
    assert "quality" in parsed
    assert "recommendations" in parsed


def test_json_output_with_integer_columns_does_not_crash(tmp_path):
    path = _write_csv(tmp_path, """
        count,label
        1,a
        2,b
        3,c
    """)
    out = tmp_path / "report.json"
    profiler.run(path, output_format="json", output_path=str(out))
    assert json.loads(out.read_text())  # no TypeError


def test_console_written_to_file_contains_section_headers(clean_csv, tmp_path):
    out = tmp_path / "report.txt"
    profiler.run(clean_csv, output_format="console", output_path=str(out))
    assert out.exists()
    content = out.read_text()
    assert "Dataset Overview" in content
    assert "Recommendations" in content


# --- Error handling ---

def test_missing_file_raises_file_not_found():
    with pytest.raises(FileNotFoundError):
        profiler.profile("/nonexistent/path/data.csv")


def test_wrong_extension_raises_value_error(tmp_path):
    bad_file = tmp_path / "data.txt"
    bad_file.write_text("col1,col2\n1,2")
    with pytest.raises(ValueError):
        profiler.profile(str(bad_file))


def test_empty_file_raises_value_error(tmp_path):
    empty = tmp_path / "empty.csv"
    empty.write_text("")
    with pytest.raises(ValueError, match="empty"):
        profiler.profile(str(empty))


def test_no_datetime_warnings_during_profiling(tmp_path, recwarn):
    path = _write_csv(tmp_path, """
        name,joined,score
        Alice,2023-01-15,8.5
        Bob,2022-06-30,7.0
        Carol,2024-03-01,9.0
    """)
    profiler.profile(path)
    datetime_warnings = [
        w for w in recwarn.list
        if "dateutil" in str(w.message).lower() or "infer format" in str(w.message).lower()
    ]
    assert datetime_warnings == [], f"Unexpected datetime warnings: {datetime_warnings}"
