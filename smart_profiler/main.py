import argparse
import sys

from smart_profiler import profiler


def main() -> None:
    args = _parse_args()
    try:
        profiler.run(args.input, output_format=args.format, output_path=args.output)
    except FileNotFoundError as e:
        _exit(str(e))
    except PermissionError as e:
        _exit(str(e))
    except ValueError as e:
        _exit(str(e))
    except OSError as e:
        _exit(str(e))
    else:
        if args.output:
            print(f"Report saved to {args.output}", file=sys.stderr)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="smart-profiler",
        description="Analyze a CSV dataset and generate data quality insights.",
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        metavar="FILE",
        help="Path to the CSV file to profile.",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["console", "json"],
        default="console",
        help="Output format: 'console' (default) or 'json'.",
    )
    parser.add_argument(
        "--output", "-o",
        metavar="FILE",
        default=None,
        help="Write the report to FILE instead of printing to the terminal.",
    )
    return parser.parse_args()


def _exit(message: str) -> None:
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
