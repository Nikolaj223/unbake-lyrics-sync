from __future__ import annotations

import argparse
import json

from .metrics import aggregate, evaluate_record, load_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate lyrics recognition quality and timestamp alignment.")
    parser.add_argument("--manifest", required=True, help="Path to JSONL manifest with reference/prediction pairs")
    args = parser.parse_args()

    manifest = load_manifest(args.manifest)
    rows = [evaluate_record(record) for record in manifest]
    print(json.dumps({"summary": aggregate(rows), "rows": rows}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
