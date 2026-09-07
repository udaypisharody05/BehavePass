from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.data.synthetic import generate_rows, read_csv, summary, validate_rows, write_csv


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic BehavePass sessions")
    parser.add_argument("--samples", type=int, default=15000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/synthetic/behavepass_synthetic.csv"),
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="validate an existing --output file without generating data",
    )
    args = parser.parse_args()
    if args.validate_only:
        rows = read_csv(args.output)
        validate_rows(rows, args.samples)
    else:
        rows = generate_rows(args.samples, args.seed)
        validate_rows(rows, args.samples)
        write_csv(rows, args.output)
    print(json.dumps(summary(rows), indent=2, sort_keys=True))
    print(f"Validated synthetic dataset: {args.output.resolve()}")


if __name__ == "__main__":
    main()
