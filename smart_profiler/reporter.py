import json
from pathlib import Path

import numpy as np
from rich.console import Console
from rich.rule import Rule
from rich.table import Table

_console = Console()

_NO_ISSUES_MESSAGE = (
    "No issues detected. Checked for: missing values, duplicate rows, "
    "constant columns, and high-cardinality columns."
)


def render_console(profile: dict, output_path: str | None = None) -> None:
    if output_path:
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                _render_all(profile, Console(file=f, no_color=True))
        except OSError as e:
            raise OSError(f"Could not write report to '{output_path}': {e.strerror}.") from e
    else:
        _render_all(profile, _console)


def render_json(profile: dict, output_path: str | None = None) -> None:
    content = json.dumps(profile, indent=2, cls=_NumpyEncoder)
    if output_path:
        try:
            Path(output_path).write_text(content, encoding="utf-8")
        except OSError as e:
            raise OSError(f"Could not write report to '{output_path}': {e.strerror}.") from e
    else:
        print(content)


class _NumpyEncoder(json.JSONEncoder):
    """Converts numpy scalar types to native Python types for JSON serialization."""
    def default(self, obj: object) -> int | float:
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        return super().default(obj)


def _render_all(profile: dict, console: Console) -> None:
    _render_overview(profile, console)
    _render_numeric_columns(profile["columns"], console)
    _render_categorical_columns(profile["columns"], console)
    _render_recommendations(profile["recommendations"], console)


# --- Sections ---

def _render_overview(profile: dict, console: Console) -> None:
    console.print(Rule("[bold]Dataset Overview[/bold]"))

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="dim")
    table.add_column()

    quality = profile["quality"]
    table.add_row("Rows",           f"{profile['row_count']:,}")
    table.add_row("Columns",        f"{profile['column_count']:,}")
    table.add_row("Missing cells",  f"{quality['missing_cells']:,} / {quality['total_cells']:,}  ({quality['overall_missing_pct']:.1f}%)")
    table.add_row("Duplicate rows", f"{quality['duplicate_rows']:,}  ({quality['duplicate_row_pct']:.1f}%)")

    console.print(table)
    console.print()


def _render_numeric_columns(columns: list[dict], console: Console) -> None:
    numeric = [col for col in columns if col["type"] == "numeric"]
    if not numeric:
        return

    console.print(Rule("[bold]Numeric Columns[/bold]"))

    table = Table(show_header=True, header_style="bold")
    table.add_column("Column")
    table.add_column("Missing %", justify="right")
    table.add_column("Mean",      justify="right")
    table.add_column("Std",       justify="right")
    table.add_column("Min",       justify="right")
    table.add_column("Max",       justify="right")

    for col in numeric:
        s = col["stats"]
        row_style = "yellow" if col["flags"] else ""
        table.add_row(
            col["column"],
            _fmt_pct(col["missing_pct"]),
            _fmt_num(s["mean"]),
            _fmt_num(s["std"]),
            _fmt_num(s["min"]),
            _fmt_num(s["max"]),
            style=row_style,
        )

    console.print(table)
    console.print()


def _render_categorical_columns(columns: list[dict], console: Console) -> None:
    categorical = [col for col in columns if col["type"] == "categorical"]
    if not categorical:
        return

    console.print(Rule("[bold]Categorical Columns[/bold]"))

    table = Table(show_header=True, header_style="bold")
    table.add_column("Column")
    table.add_column("Missing %", justify="right")
    table.add_column("Unique",    justify="right")
    table.add_column("Top Value")

    for col in categorical:
        s = col["stats"]
        top = s["top_values"][0] if s["top_values"] else None
        top_str = f"{top['value']}  ({top['pct']:.1f}%)" if top else "—"
        row_style = "yellow" if col["flags"] else ""
        table.add_row(
            col["column"],
            _fmt_pct(col["missing_pct"]),
            str(s["unique_count"]),
            top_str,
            style=row_style,
        )

    console.print(table)
    console.print()


def _render_recommendations(recommendations: list[dict], console: Console) -> None:
    console.print(Rule("[bold]Recommendations[/bold]"))
    if recommendations:
        for rec in recommendations:
            console.print(f"  • {rec['message']}")
    else:
        console.print(f"  {_NO_ISSUES_MESSAGE}")
    console.print()


# --- Formatting helpers ---

def _fmt_pct(value: float | None) -> str:
    return f"{value:.1f}%" if value is not None else "—"


def _fmt_num(value: float | None) -> str:
    return f"{value:,.2f}" if value is not None else "—"
