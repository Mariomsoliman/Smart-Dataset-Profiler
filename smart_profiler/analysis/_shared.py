import pandas as pd


HIGH_MISSING_THRESHOLD = 30.0


def compute_missing(series: pd.Series) -> tuple[int, float]:
    missing_count = int(series.isna().sum())
    missing_pct = (missing_count / len(series) * 100) if len(series) > 0 else 0.0
    return missing_count, missing_pct
