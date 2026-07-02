# Smart Dataset Profiler

**Understand any CSV dataset in seconds.** Smart Profiler analyzes your data and returns statistics, data quality insights, and preprocessing recommendations — all from a single command.

[![Tests](https://github.com/Mariomsoliman/smart-profiler/actions/workflows/tests.yml/badge.svg)](https://github.com/Mariomsoliman/smart-profiler/actions/workflows/tests.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Why this exists

Before building a model or cleaning a dataset, you need to know what you're working with. How much data is missing? Are there duplicate rows? Which columns have enough variance to be useful? Answering these questions manually is tedious and error-prone.

Smart Profiler does it in one command and tells you exactly what to fix.

---

## Quick start

```bash
pip install git+https://github.com/Mariomsoliman/smart-profiler.git
smart-profiler --input your_data.csv
```

---

## Installation

### From source

```bash
git clone https://github.com/Mariomsoliman/smart-profiler.git
cd smart-profiler
pip install .
```

### For development

```bash
git clone https://github.com/Mariomsoliman/smart-profiler.git
cd smart-profiler
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

**Requirements:** Python 3.10 or later.

---

## Usage

```
smart-profiler --input FILE [--format FORMAT] [--output FILE]
```

| Flag | Short | Default | Description |
|---|---|---|---|
| `--input FILE` | `-i` | — | Path to the CSV file to profile *(required)* |
| `--format FORMAT` | `-f` | `console` | Output format: `console` or `json` |
| `--output FILE` | `-o` | — | Write the report to a file instead of the terminal |

### Examples

```bash
# Profile a dataset and print to the terminal
smart-profiler --input data.csv

# Export a machine-readable JSON report
smart-profiler --input data.csv --format json --output report.json

# Save the console report to a text file
smart-profiler --input data.csv --output report.txt
```

---

## Sample output

### Console

```
──────────────────────────── Dataset Overview ────────────────────────────
  Rows              1,000
  Columns           8
  Missing cells     432 / 8,000  (5.4%)
  Duplicate rows    3  (0.3%)

──────────────────────────── Numeric Columns ─────────────────────────────
 Column    Missing %      Mean       Std      Min        Max
 age           0.0%     34.71     12.30    18.00      89.00
 income       38.1%  52,400.00  8,200.00     0.00  200,000.00   ← flagged
 score         2.1%      7.84      1.22     1.00      10.00

──────────────────────────── Categorical Columns ─────────────────────────
 Column    Missing %   Unique   Top Value
 country       1.5%        4   USA (44.2%)
 status        0.0%        1   active (100%)                     ← flagged
 user_id       0.0%      997   usr_001 (0.1%)                    ← flagged

──────────────────────────── Recommendations ─────────────────────────────
  • Column 'income' has 38.1% missing values — consider imputation
    or dropping it before modeling.
  • Column 'status' has only one unique value — it carries no
    information and can be dropped.
  • Column 'user_id' has 997 unique values (high cardinality) — it
    may be an ID or free-text field. Consider excluding it from analysis.
  • Found 3 duplicate rows (0.3%) — consider deduplication before modeling.
```

Rows with at least one quality flag are highlighted in yellow in the terminal.

### JSON

When `--format json` is used, every recommendation is a structured object — no text parsing required:

```json
{
  "row_count": 1000,
  "column_count": 8,
  "columns": [ ... ],
  "quality": {
    "duplicate_rows": 3,
    "duplicate_row_pct": 0.3,
    "missing_cells": 432,
    "total_cells": 8000,
    "overall_missing_pct": 5.4
  },
  "recommendations": [
    {
      "type": "high_missing",
      "severity": "medium",
      "column": "income",
      "triggering_value": 38.1,
      "message": "Column 'income' has 38.1% missing values — consider imputation or dropping it before modeling."
    },
    {
      "type": "duplicate_rows",
      "severity": "medium",
      "column": null,
      "triggering_value": 3,
      "message": "Found 3 duplicate rows (0.3%) — consider deduplication before modeling."
    }
  ]
}
```

---

## JSON schema reference

### Top-level profile

| Field | Type | Description |
|---|---|---|
| `row_count` | `int` | Total number of rows in the dataset |
| `column_count` | `int` | Total number of columns, including skipped types |
| `columns` | `list[ColumnResult]` | One entry per analyzed column |
| `quality` | `QualityResult` | Dataset-level quality facts |
| `recommendations` | `list[Recommendation]` | Ordered list of actionable findings |

### ColumnResult

| Field | Type | Description |
|---|---|---|
| `column` | `str` | Column name |
| `type` | `"numeric" \| "categorical"` | Inferred column type |
| `count` | `int` | Total rows including nulls |
| `missing` | `int` | Number of null values |
| `missing_pct` | `float` | Percentage of null values |
| `stats` | `NumericStats \| CategoricalStats` | Type-specific statistics |
| `flags` | `list[Flag]` | Quality flags that triggered recommendations |

**NumericStats** — `mean`, `median`, `std`, `min`, `max`, `q25`, `q75` (all `float | null`)

**CategoricalStats** — `unique_count` (`int`), `top_values` (list of `{value, count, pct}`)

**Flag** — `{name: str, value: float}` — the name and the value that triggered it

### QualityResult

| Field | Type | Description |
|---|---|---|
| `duplicate_rows` | `int` | Number of rows that are exact duplicates |
| `duplicate_row_pct` | `float` | Percentage of rows that are duplicates |
| `missing_cells` | `int` | Total null cells across the entire dataset |
| `total_cells` | `int` | Total cells (`row_count × column_count`) |
| `overall_missing_pct` | `float` | Percentage of all cells that are null |

### Recommendation

| Field | Type | Description |
|---|---|---|
| `type` | `str` | Stable identifier (see table below) |
| `severity` | `"high" \| "medium" \| "low"` | How urgently to address this |
| `column` | `str \| null` | Affected column, or `null` for dataset-level findings |
| `triggering_value` | `float \| int` | The value that caused this recommendation |
| `message` | `str` | Human-readable description |

### Recommendation types

| Type | Severity | Default threshold | Triggered when |
|---|---|---|---|
| `all_missing` | `high` | 100% | Column has no values at all |
| `high_missing` | `medium` | > 30% | Column has too many null values |
| `constant` | `medium` | 1 unique value | Column carries no information |
| `high_cardinality` | `low` | > 90% unique | Column is likely an ID or free-text field |
| `duplicate_rows` | `medium` | ≥ 1 | Dataset contains exact duplicate rows |

---

## What gets analyzed

Smart Profiler automatically infers column types from the data:

- **Numeric** columns (integers and floats) → descriptive statistics + missing/constant flags
- **Categorical** columns (strings and mixed types) → cardinality, top values + all flags
- **Datetime** columns → detected and tagged, not yet analyzed *(v2 roadmap)*

---

## Project structure

```
smart_profiler/
├── main.py            # CLI entry point — argument parsing and error display
├── profiler.py        # Orchestrator — wires the pipeline together
├── loader.py          # CSV loading, encoding detection, type inference
├── quality.py         # Dataset-level checks (duplicates, overall missing rate)
├── recommender.py     # Maps quality flags to structured recommendation objects
├── reporter.py        # Console (rich) and JSON output renderers
└── analysis/
    ├── _shared.py     # Shared threshold and missing-value helper
    ├── numeric.py     # Statistics and flags for numeric columns
    └── categorical.py # Statistics and flags for categorical columns

tests/
├── test_numeric.py       # Unit tests for the numeric analyzer
├── test_categorical.py   # Unit tests for the categorical analyzer
├── test_quality.py       # Unit tests for the quality module
└── test_integration.py   # End-to-end pipeline tests
```

The pipeline flows in one direction: `load → analyze → quality → recommend → render`. Each stage is independent — you can call `profiler.profile(path)` to get the raw profile dict without rendering anything.

---

## Development

### Running the tests

```bash
pytest
```

All 60 tests should pass with no warnings across Python 3.10–3.13.

### Adding a new recommendation

1. Add a flag in the relevant analyzer (`analysis/numeric.py` or `analysis/categorical.py`)
2. Add a handler function in `recommender.py`
3. Register it in `_COLUMN_FLAG_HANDLERS` or `_QUALITY_CHECKS`
4. Add tests

No other files need to change.

### Adding a new column type

1. Create `analysis/your_type.py` with an `analyze(series, column_name) -> dict` function
2. Register it in `profiler._ANALYZERS`
3. Add tests

---

## Known limitations

- **Encoding support** — UTF-8 (with and without BOM) and Latin-1 only. Files in Windows-1252, UTF-16, or other encodings will fail with a clear error.
- **Datetime analysis** — datetime columns are detected and tagged but not yet analyzed. Statistics and recommendations for date/time data are planned for v2.
- **Large files** — encoding detection reads the full file before parsing begins. Files larger than a few hundred MB may profile slowly.
- **Delimiter detection** — uses a 4 KB sample. Files with very long rows may be misdetected; standard comma-delimited format is most reliable.
- **Type inference** — columns containing year strings (e.g. `"2019"`, `"2020"`) may be tagged as datetime instead of categorical.

---

## License

MIT. See [LICENSE](LICENSE) for details.
