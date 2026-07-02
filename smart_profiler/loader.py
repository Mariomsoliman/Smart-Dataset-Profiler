import csv
import pandas as pd
from pathlib import Path


_SUPPORTED_EXTENSIONS = {".csv"}
_ENCODINGS_TO_TRY = ["utf-8-sig", "utf-8", "latin-1"]
_DATETIME_PARSE_THRESHOLD = 0.8


def load(path: str) -> tuple[pd.DataFrame, dict[str, str]]:
    """Load a CSV file and return the DataFrame alongside an inferred column type map."""
    file_path = _validate_path(path)
    encoding = _detect_encoding(file_path)
    delimiter = _detect_delimiter(file_path, encoding)
    df = _read_csv(file_path, encoding, delimiter)
    column_types = {col: _infer_type(df[col]) for col in df.columns}
    return df, column_types


def _read_csv(path: Path, encoding: str, delimiter: str) -> pd.DataFrame:
    try:
        return pd.read_csv(path, encoding=encoding, sep=delimiter)
    except pd.errors.EmptyDataError:
        raise ValueError(f"'{path.name}' is empty.")
    except pd.errors.ParserError:
        raise ValueError(f"Could not parse '{path.name}' as a valid CSV file.")


# --- Path validation ---

def _validate_path(path: str) -> Path:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {path}")
    if file_path.suffix.lower() not in _SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{file_path.suffix}'. Expected a .csv file."
        )
    return file_path


# --- Encoding detection ---

def _detect_encoding(path: Path) -> str:
    for encoding in _ENCODINGS_TO_TRY:
        if _can_read_with_encoding(path, encoding):
            return encoding
    raise ValueError(
        f"Could not decode '{path.name}' using any of: {_ENCODINGS_TO_TRY}"
    )


def _can_read_with_encoding(path: Path, encoding: str) -> bool:
    try:
        with open(path, encoding=encoding) as f:
            f.read()
        return True
    except PermissionError as e:
        raise PermissionError(f"Permission denied: cannot read '{path}'.") from e
    except UnicodeDecodeError:
        return False


# --- Delimiter detection ---

def _detect_delimiter(path: Path, encoding: str) -> str:
    sample = _read_sample(path, encoding)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        return dialect.delimiter
    except csv.Error:
        return ","


def _read_sample(path: Path, encoding: str, num_bytes: int = 4096) -> str:
    with open(path, encoding=encoding, newline="") as f:
        return f.read(num_bytes)


# --- Column type inference ---

def _infer_type(series: pd.Series) -> str:
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    if _looks_like_datetime(series):
        return "datetime"
    return "categorical"


def _looks_like_datetime(series: pd.Series) -> bool:
    """Check if an object-typed column contains parseable datetime strings."""
    sample = series.dropna().head(100)
    if sample.empty:
        return False
    parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
    return parsed.notna().mean() >= _DATETIME_PARSE_THRESHOLD
