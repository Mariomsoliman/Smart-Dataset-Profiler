import pandas as pd

from smart_profiler.analysis._shared import HIGH_MISSING_THRESHOLD, compute_missing

_HIGH_CARDINALITY_THRESHOLD = 0.9
_TOP_N = 5


def analyze(series: pd.Series, column_name: str) -> dict:
    """Return a profiling result dict for a categorical column."""
    missing_count, missing_pct = compute_missing(series)
    clean = series.dropna()
    stats = _compute_stats(clean)
    flags = _build_flags(missing_pct, unique_count=stats["unique_count"], non_null_count=len(clean))

    return {
        "column": column_name,
        "type": "categorical",
        "count": len(series),
        "missing": missing_count,
        "missing_pct": missing_pct,
        "stats": stats,
        "flags": flags,
    }


def _compute_stats(clean: pd.Series) -> dict:
    """Compute categorical statistics on an already-cleaned (dropna) series."""
    if clean.empty:
        return {"unique_count": 0, "top_values": []}

    value_counts = clean.value_counts()
    non_null_count = len(clean)

    return {
        "unique_count": int(value_counts.size),
        "top_values": [
            {
                "value": value,
                "count": int(count),
                "pct": (count / non_null_count * 100),
            }
            for value, count in value_counts.head(_TOP_N).items()
        ],
    }


def _build_flags(missing_pct: float, unique_count: int, non_null_count: int) -> list[dict]:
    flags = []

    if missing_pct == 100.0:
        flags.append({"name": "all_missing", "value": missing_pct})
    elif missing_pct > HIGH_MISSING_THRESHOLD:
        flags.append({"name": "high_missing", "value": missing_pct})

    if unique_count == 1:
        flags.append({"name": "constant", "value": unique_count})
    elif non_null_count > 0 and (unique_count / non_null_count) > _HIGH_CARDINALITY_THRESHOLD:
        flags.append({"name": "high_cardinality", "value": unique_count})

    return flags
