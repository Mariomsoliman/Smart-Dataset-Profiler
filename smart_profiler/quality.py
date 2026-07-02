import pandas as pd


def check(df: pd.DataFrame) -> dict:
    """Return dataset-level quality facts that require cross-column inspection."""
    duplicate_rows, duplicate_row_pct = _duplicate_info(df)
    missing_cells, total_cells, overall_missing_pct = _missing_info(df)

    return {
        "duplicate_rows": duplicate_rows,
        "duplicate_row_pct": duplicate_row_pct,
        "missing_cells": missing_cells,
        "total_cells": total_cells,
        "overall_missing_pct": overall_missing_pct,
    }


def _duplicate_info(df: pd.DataFrame) -> tuple[int, float]:
    if df.empty:
        return 0, 0.0
    duplicate_rows = int(df.duplicated().sum())
    duplicate_row_pct = (duplicate_rows / len(df) * 100)
    return duplicate_rows, duplicate_row_pct


def _missing_info(df: pd.DataFrame) -> tuple[int, int, float]:
    total_cells = df.size
    if total_cells == 0:
        return 0, 0, 0.0
    missing_cells = int(df.isna().sum().sum())
    overall_missing_pct = (missing_cells / total_cells * 100)
    return missing_cells, total_cells, overall_missing_pct
