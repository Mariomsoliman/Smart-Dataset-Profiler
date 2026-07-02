def recommend(profile: dict) -> list[dict]:
    """Translate profiling results into structured recommendation objects."""
    recommendations = []

    for col in profile["columns"]:
        for flag in col["flags"]:
            handler = _COLUMN_FLAG_HANDLERS.get(flag["name"])
            if handler:
                recommendations.append(handler(col, flag))

    for check in _QUALITY_CHECKS:
        result = check(profile["quality"])
        if result:
            recommendations.append(result)

    return recommendations


def _rec(rec_type: str, severity: str, column: str | None, triggering_value: float | int, message: str) -> dict:
    return {
        "type":             rec_type,
        "severity":         severity,
        "column":           column,
        "triggering_value": triggering_value,
        "message":          message,
    }


# --- Column-level flag handlers ---

def _handle_high_missing(col: dict, flag: dict) -> dict:
    column = col["column"]
    return _rec(
        rec_type="high_missing",
        severity="medium",
        column=column,
        triggering_value=flag["value"],
        message=(
            f"Column '{column}' has {flag['value']:.1f}% missing values — "
            "consider imputation or dropping it before modeling."
        ),
    )


def _handle_all_missing(col: dict, flag: dict) -> dict:
    column = col["column"]
    return _rec(
        rec_type="all_missing",
        severity="high",
        column=column,
        triggering_value=flag["value"],
        message=f"Column '{column}' has no values at all — drop it.",
    )


def _handle_constant(col: dict, flag: dict) -> dict:
    column = col["column"]
    return _rec(
        rec_type="constant",
        severity="medium",
        column=column,
        triggering_value=flag["value"],
        message=(
            f"Column '{column}' has only one unique value — "
            "it carries no information and can be dropped."
        ),
    )


def _handle_high_cardinality(col: dict, flag: dict) -> dict:
    column = col["column"]
    return _rec(
        rec_type="high_cardinality",
        severity="low",
        column=column,
        triggering_value=flag["value"],
        message=(
            f"Column '{column}' has {flag['value']} unique values (high cardinality) — "
            "it may be an ID or free-text field. Consider excluding it from analysis."
        ),
    )


_COLUMN_FLAG_HANDLERS = {
    "high_missing":     _handle_high_missing,
    "all_missing":      _handle_all_missing,
    "constant":         _handle_constant,
    "high_cardinality": _handle_high_cardinality,
}


# --- Dataset-level quality checks ---

def _check_duplicates(quality: dict) -> dict | None:
    count = quality["duplicate_rows"]
    if count > 0:
        return _rec(
            rec_type="duplicate_rows",
            severity="medium",
            column=None,
            triggering_value=count,
            message=(
                f"Found {count} duplicate rows "
                f"({quality['duplicate_row_pct']:.1f}%) — consider deduplication before modeling."
            ),
        )
    return None


_QUALITY_CHECKS = [
    _check_duplicates,
]
