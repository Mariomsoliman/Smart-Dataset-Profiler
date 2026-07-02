import pandas as pd

from smart_profiler import loader, quality, recommender, reporter
from smart_profiler.analysis import categorical, numeric


_ANALYZERS = {
    "numeric":     numeric.analyze,
    "categorical": categorical.analyze,
}


def profile(path: str) -> dict:
    """Build and return the full profile dict without rendering it."""
    df, column_types = loader.load(path)
    column_results  = _analyze_columns(df, column_types)
    quality_results = quality.check(df)
    recommendations = recommender.recommend({
        "columns": column_results,
        "quality": quality_results,
    })
    return {
        "row_count":       len(df),
        "column_count":    len(df.columns),
        "columns":         column_results,
        "quality":         quality_results,
        "recommendations": recommendations,
    }


def run(path: str, output_format: str = "console", output_path: str | None = None) -> None:
    _render(profile(path), output_format, output_path)


def _analyze_columns(df: pd.DataFrame, column_types: dict[str, str]) -> list[dict]:
    results = []
    for col_name, col_type in column_types.items():
        analyze = _ANALYZERS.get(col_type)
        if analyze:
            results.append(analyze(df[col_name], col_name))
    return results


def _render(profile: dict, output_format: str, output_path: str | None = None) -> None:
    if output_format == "json":
        reporter.render_json(profile, output_path=output_path)
    else:
        reporter.render_console(profile, output_path=output_path)
