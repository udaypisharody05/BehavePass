from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.data.synthetic import (
    assert_aggregate_alignment,
    generate_rows_and_sequences,
    read_csv,
    validate_sequence_alignment,
    write_sequences_jsonl,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create sequence data aligned to an existing synthetic aggregate CSV"
    )
    parser.add_argument("--aggregate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    existing = read_csv(args.aggregate)
    regenerated, sequences = generate_rows_and_sequences(len(existing), args.seed)
    assert_aggregate_alignment(existing, regenerated)
    validate_sequence_alignment(regenerated, sequences)
    write_sequences_jsonl(sequences, args.output)
    lengths = [int(record["sequence_length"]) for record in sequences]
    print(json.dumps({
        "sessions": len(sequences),
        "average_sequence_length": sum(lengths) / len(lengths),
        "minimum_sequence_length": min(lengths),
        "maximum_sequence_length": max(lengths),
        "aggregate_alignment": "passed",
        "output": str(args.output.resolve()),
    }, indent=2))


if __name__ == "__main__":
    main()
