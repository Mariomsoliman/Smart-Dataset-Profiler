import pandas as pd

from smart_profiler.analysis._shared import HIGH_MISSING_THRESHOLD, compute_missing


def analyze(series: pd.Series, column_name: str) -> dict:
    """Return a profiling result dict for a numeric column."""
    missing_count, missing_pct = compute_missing(series)
    clean = series.dropna()
    stats = _compute_stats(clean)
    flags = _build_flags(missing_pct, unique_count=clean.nunique())

    return {
        "column": column_name,
        "type": "numeric",
        "count": len(series),
        "missing": missing_count,
        "missing_pct": missing_pct,
        "stats": stats,
        "flags": flags,
    }


def _compute_stats(clean: pd.Series) -> dict:
    """Compute descriptive statistics on an already-cleaned (dropna) series."""
    if clean.empty:
        return {key: None for key in ["mean", "median", "std", "min", "max", "q25", "q75"]}

    return {
        "mean":   clean.mean(),
        "median": clean.median(),
        "std":    clean.std(),
        "min":    clean.min(),
        "max":    clean.max(),
        "q25":    clean.quantile(0.25),
        "q75":    clean.quantile(0.75),
    }


def _build_flags(missing_pct: float, unique_count: int) -> list[dict]:
    flags = []
    if missing_pct == 100.0:
        flags.append({"name": "all_missing", "value": missing_pct})
    elif missing_pct > HIGH_MISSING_THRESHOLD:
        flags.append({"name": "high_missing", "value": missing_pct})
    if unique_count == 1:
        flags.append({"name": "constant", "value": unique_count})
    return flags
